"""
In-memory token blacklist with TTL.
Tokens are stored as SHA-256 hashes and auto-cleaned on write.
For multi-server deployments, replace with Redis.
"""
import hashlib
import threading
from datetime import datetime, timezone

_blacklist: dict[str, datetime] = {}
_lock = threading.Lock()


def blacklist_token(token: str, expires_at: datetime) -> None:
    """Add a token to the blacklist until its natural expiry."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with _lock:
        _blacklist[token_hash] = expires_at
        _cleanup()


def is_blacklisted(token: str) -> bool:
    """Return True if the token has been revoked."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
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
