from app.cache.store import InMemoryCacheStore, RedisCacheStore, get_cache_store


def test_in_memory_cache_store():
    store = InMemoryCacheStore()
    store.set("test_key", {"score": 98}, ttl=10)
    assert store.exists("test_key") is True
    assert store.get("test_key") == {"score": 98}

    store.delete("test_key")
    assert store.exists("test_key") is False
    assert store.get("test_key") is None


def test_redis_cache_store_fallback():
    # If redis connection fails, it transparently falls back to in-memory store
    store = RedisCacheStore(url="redis://127.0.0.1:9999/0")
    store.set("fallback_key", "healthy_cell", ttl=10)
    val = store.get("fallback_key")
    assert val == "healthy_cell"
    assert store.exists("fallback_key") is True
    store.delete("fallback_key")
    assert store.get("fallback_key") is None


def test_get_cache_store_singleton():
    s1 = get_cache_store()
    s2 = get_cache_store()
    assert s1 is s2

