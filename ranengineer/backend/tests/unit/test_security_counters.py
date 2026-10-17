"""Unit tests for Redis-backed Security Counters (Section 31)."""
import pytest

from app.security.counters import SecurityCounterStore


def test_failed_login_counter_increments_and_locks():
    store = SecurityCounterStore(ttl_failed_login=10)
    user = "test_locked_user@telecom.ai"
    store.reset_failed_login(user)

    assert store.is_user_locked(user) is False

    for attempt in range(1, 5):
        cnt = store.record_failed_login(user)
        assert cnt == attempt
        assert store.is_user_locked(user) is False

    # 5th attempt locks the account
    cnt5 = store.record_failed_login(user)
    assert cnt5 >= 5
    assert store.is_user_locked(user) is True

    # Reset clears lockout
    store.reset_failed_login(user)
    assert store.is_user_locked(user) is False


def test_upload_and_api_counters():
    store = SecurityCounterStore()
    user = "engineer@telecom.ai"

    u1 = store.record_upload(user)
    u2 = store.record_upload(user)
    assert u2 == u1 + 1

    a1 = store.record_api_request(user)
    a2 = store.record_api_request(user)
    assert a2 == a1 + 1

    metrics = store.get_metrics()
    assert "locked_users_count" in metrics
    assert "tracked_security_keys" in metrics

