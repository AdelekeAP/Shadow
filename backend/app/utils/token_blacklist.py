"""
Token blacklist with Redis + in-memory fallback.
Tokens are stored as SHA-256 hashes with TTL matching token expiry.
Redis is tried first; if unavailable, falls back to in-memory dict.
"""
import hashlib
import logging
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_blacklist: dict[str, datetime] = {}
_lock = threading.Lock()


def _get_redis():
    """Try to get a Redis client from the cache service."""
    try:
        from app.services.cache_service import _get_redis as cache_redis
        return cache_redis()
    except Exception:
        return None


def blacklist_token(token: str, expires_at: datetime) -> None:
    """Add a token to the blacklist until its natural expiry."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Calculate TTL in seconds
    ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    if ttl <= 0:
        return  # Already expired, no need to blacklist

    # Try Redis first
    redis_client = _get_redis()
    if redis_client is not None:
        try:
            redis_client.setex(f"blacklist:{token_hash}", ttl, "1")
            return
        except Exception as exc:
            logger.warning("Redis blacklist_token failed, using memory fallback: %s", exc)

    # Fall back to in-memory
    with _lock:
        _blacklist[token_hash] = expires_at
        _cleanup()


def is_blacklisted(token: str) -> bool:
    """Return True if the token has been revoked."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Try Redis first
    redis_client = _get_redis()
    if redis_client is not None:
        try:
            if redis_client.exists(f"blacklist:{token_hash}"):
                return True
            # Also check in-memory in case it was added before Redis came up
        except Exception as exc:
            logger.warning("Redis is_blacklisted failed, checking memory fallback: %s", exc)

    # Check in-memory fallback
    with _lock:
        exp = _blacklist.get(token_hash)
        if exp and exp > datetime.now(timezone.utc):
            return True
        return False


def _cleanup() -> None:
    """Remove expired entries to prevent unbounded growth."""
    now = datetime.now(timezone.utc)
    expired = [k for k, v in _blacklist.items() if v <= now]
    for k in expired:
        del _blacklist[k]
