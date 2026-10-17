"""Cache store abstraction for AI Telecom Copilot – RAN Engineer.

Implementations:
  InMemoryCacheStore  – Phase 1 / development / tests
  RedisCacheStore     – Production (future)

Never scatter Redis calls through business logic.
Always depend on the CacheStore interface.
"""
from __future__ import annotations

import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheStore(ABC):
    """Abstract cache store interface."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Return the cached value or None if missing/expired."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Store a value with an optional TTL in seconds."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a key from the cache."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if the key exists and has not expired."""


class InMemoryCacheStore(CacheStore):
    """Thread-safe in-memory cache. Suitable for Phase 1 and unit tests."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}  # value, expires_at
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at and time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        expires_at = time.monotonic() + ttl if ttl > 0 else 0.0
        with self._lock:
            self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None


class RedisCacheStore(CacheStore):
    """Redis-backed cache store (future integration).

    Requires redis-py: pip install redis
    REDIS_URL environment variable must be set.

    Example:
        REDIS_URL=redis://localhost:6379/0
    """

    def __init__(self, url: str | None = None) -> None:
        self._fallback = InMemoryCacheStore()
        self._client = None
        try:
            import redis  # type: ignore
            redis_url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self._client = redis.from_url(redis_url, decode_responses=False)
        except Exception:
            self._client = None

    def get(self, key: str) -> Optional[Any]:
        if self._client is None:
            return self._fallback.get(key)
        import pickle
        try:
            raw = self._client.get(key)
            return pickle.loads(raw) if raw is not None else None  # noqa: S301
        except Exception:
            return self._fallback.get(key)

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if self._client is None:
            self._fallback.set(key, value, ttl)
            return
        import pickle
        try:
            self._client.set(key, pickle.dumps(value), ex=ttl if ttl > 0 else None)
        except Exception:
            self._fallback.set(key, value, ttl)

    def delete(self, key: str) -> None:
        if self._client is None:
            self._fallback.delete(key)
            return
        try:
            self._client.delete(key)
        except Exception:
            self._fallback.delete(key)

    def exists(self, key: str) -> bool:
        if self._client is None:
            return self._fallback.exists(key)
        try:
            return bool(self._client.exists(key))
        except Exception:
            return self._fallback.exists(key)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
_cache_store: CacheStore | None = None


def get_cache_store() -> CacheStore:
    """Return the appropriate cache store based on RANENGINEER_CACHE env var.

    RANENGINEER_CACHE=redis   → RedisCacheStore (requires REDIS_URL)
    default                   → InMemoryCacheStore
    """
    global _cache_store
    if _cache_store is None:
        cache_type = os.getenv("RANENGINEER_CACHE", "memory").lower()
        _cache_store = RedisCacheStore() if cache_type == "redis" else InMemoryCacheStore()
    return _cache_store


__all__ = ["CacheStore", "InMemoryCacheStore", "RedisCacheStore", "get_cache_store"]

