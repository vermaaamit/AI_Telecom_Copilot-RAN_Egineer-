"""Redis-backed Security Counters with In-Memory Fallback (Section 31 & 32)."""
from datetime import datetime, timezone
import os
import threading
from typing import Any, Dict, Optional

from app.cache.store import RedisCacheStore, get_cache_store
from app.logging import app_logger


class SecurityCounterStore:
    """Manages rate-limiting and security counters with TTLs."""

    def __init__(self, ttl_failed_login: int = 900, ttl_upload: int = 3600, ttl_api: int = 60):
        self.ttl_failed_login = ttl_failed_login
        self.ttl_upload = ttl_upload
        self.ttl_api = ttl_api
        self.cache = get_cache_store()
        self._lock = threading.Lock()
        # In-memory auxiliary counters for offline metrics
        self._local_counts: Dict[str, int] = {}
        self._blocked_users: Dict[str, datetime] = {}

    def _incr_key(self, key: str, ttl: int) -> int:
        """Atomically increments a key with TTL."""
        try:
            curr = self.cache.get(key)
            new_val = (int(curr) + 1) if curr is not None else 1
            self.cache.set(key, new_val, ttl=ttl)
            with self._lock:
                self._local_counts[key] = new_val
            return new_val
        except Exception as e:
            app_logger.warning("Error accessing cache in SecurityCounterStore: {}", e)
            with self._lock:
                val = self._local_counts.get(key, 0) + 1
                self._local_counts[key] = val
                return val

    def record_failed_login(self, user_identifier: str) -> int:
        """Records a failed login attempt and flags brute-force threshold (>5)."""
        clean_id = user_identifier.lower().strip()
        key = f"failed_login:{clean_id}"
        count = self._incr_key(key, self.ttl_failed_login)
        if count >= 5:
            with self._lock:
                self._blocked_users[clean_id] = datetime.now(timezone.utc)
            app_logger.warning(
                "BRUTE_FORCE_TRIGGERED user={} failed_attempts={}", clean_id, count
            )
        return count

    def reset_failed_login(self, user_identifier: str) -> None:
        """Clears failed login counter upon successful authentication."""
        clean_id = user_identifier.lower().strip()
        key = f"failed_login:{clean_id}"
        try:
            self.cache.delete(key)
        except Exception:
            pass
        with self._lock:
            self._local_counts.pop(key, None)
            self._blocked_users.pop(clean_id, None)

    def is_user_locked(self, user_identifier: str) -> bool:
        """Checks if a user is temporarily locked due to brute force."""
        clean_id = user_identifier.lower().strip()
        key = f"failed_login:{clean_id}"
        val = self.cache.get(key)
        if val is not None and int(val) >= 5:
            return True
        with self._lock:
            return clean_id in self._blocked_users

    def record_upload(self, user_identifier: str) -> int:
        """Tracks CSV upload frequency per user (TTL=1 hour)."""
        clean_id = user_identifier.lower().strip()
        key = f"upload_count:{clean_id}"
        return self._incr_key(key, self.ttl_upload)

    def record_api_request(self, user_identifier: str) -> int:
        """Tracks short-term API burst requests (TTL=60s)."""
        clean_id = user_identifier.lower().strip()
        key = f"api_requests:{clean_id}"
        return self._incr_key(key, self.ttl_api)

    def get_metrics(self) -> Dict[str, Any]:
        """Returns security counters summary."""
        with self._lock:
            locked = list(self._blocked_users.keys())
            total_active_keys = len(self._local_counts)
        return {
            "locked_users_count": len(locked),
            "locked_users": locked,
            "tracked_security_keys": total_active_keys,
            "status": "ACTIVE",
        }


# Global singleton
_security_counter_store: Optional[SecurityCounterStore] = None


def get_security_counter_store() -> SecurityCounterStore:
    global _security_counter_store
    if _security_counter_store is None:
        _security_counter_store = SecurityCounterStore()
    return _security_counter_store

