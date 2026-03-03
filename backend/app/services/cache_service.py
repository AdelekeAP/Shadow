"""
Cache Service - Redis caching layer with graceful fallback.

Provides simple get/set/delete operations backed by Redis.
When Redis is unavailable or disabled, all operations silently return
None / False so the application continues to function without caching.
"""
import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() in ("true", "1", "yes")

# TTL presets (seconds)
TTL_CGPA: int = 600       # 10 minutes
TTL_ANALYTICS: int = 300   # 5 minutes
TTL_CONTEXT: int = 60      # 1 minute

# ---------------------------------------------------------------------------
# Lazy Redis connection
# ---------------------------------------------------------------------------
_redis_client = None


def _get_redis():
    """Return a Redis client, connecting lazily on first call.

    Returns ``None`` when Redis is disabled or the connection fails.
    """
    global _redis_client

    if not REDIS_ENABLED:
        return None

    if _redis_client is not None:
        return _redis_client

    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Verify connectivity with a lightweight ping
        _redis_client.ping()
        logger.info("Redis cache connected at %s", REDIS_URL)
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable, caching disabled: %s", exc)
        _redis_client = None
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def cache_get(key: str) -> Optional[Any]:
    """Retrieve a cached value by *key*.

    Returns the deserialised Python object, or ``None`` when the key is
    missing or Redis is unavailable.
    """
    try:
        client = _get_redis()
        if client is None:
            return None
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("cache_get(%s) failed: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl: int = TTL_ANALYTICS) -> bool:
    """Store *value* under *key* with the given *ttl* (seconds).

    Returns ``True`` on success, ``False`` on failure or when Redis is
    unavailable.
    """
    try:
        client = _get_redis()
        if client is None:
            return False
        serialized = json.dumps(value)
        client.setex(key, ttl, serialized)
        return True
    except Exception as exc:
        logger.warning("cache_set(%s) failed: %s", key, exc)
        return False


def cache_delete(key: str) -> bool:
    """Delete a single cached *key*.

    Returns ``True`` on success, ``False`` on failure or when Redis is
    unavailable.
    """
    try:
        client = _get_redis()
        if client is None:
            return False
        client.delete(key)
        return True
    except Exception as exc:
        logger.warning("cache_delete(%s) failed: %s", key, exc)
        return False


def cache_delete_pattern(pattern: str) -> bool:
    """Delete all keys matching *pattern* (e.g. ``"analytics:user123:*"``).

    Uses ``SCAN`` internally to avoid blocking Redis on large key-spaces.
    Returns ``True`` on success, ``False`` on failure or when Redis is
    unavailable.
    """
    try:
        client = _get_redis()
        if client is None:
            return False
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                client.delete(*keys)
            if cursor == 0:
                break
        return True
    except Exception as exc:
        logger.warning("cache_delete_pattern(%s) failed: %s", pattern, exc)
        return False
