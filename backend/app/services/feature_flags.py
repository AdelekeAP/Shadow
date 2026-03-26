"""
Feature Flag Service — Redis-backed with in-memory fallback.
Allows global and per-user feature toggling (e.g. AI kill switch).
"""
import logging
import os

logger = logging.getLogger(__name__)

# In-memory fallback when Redis is unavailable
_memory_store: dict[str, str] = {}


def _get_redis():
    """Get Redis connection, or None if unavailable."""
    try:
        from app.services.cache_service import _get_redis as cache_redis
        return cache_redis()
    except Exception:
        return None


def is_feature_enabled(feature_name: str, user_id: str | None = None) -> bool:
    """Check if a feature is enabled.

    Resolution order:
    1. Per-user override (if user_id provided)
    2. Global flag
    3. Default: enabled
    """
    r = _get_redis()

    # Check per-user override first
    if user_id:
        user_key = f"feature:{feature_name}:user:{user_id}"
        val = _get(r, user_key)
        if val is not None:
            return val != "disabled"

    # Check global flag
    global_key = f"feature:{feature_name}"
    val = _get(r, global_key)
    if val is not None:
        return val != "disabled"

    # Default: enabled
    return True


def set_feature(feature_name: str, enabled: bool, user_id: str | None = None) -> None:
    """Set a feature flag globally or per-user."""
    if user_id:
        key = f"feature:{feature_name}:user:{user_id}"
    else:
        key = f"feature:{feature_name}"

    value = "enabled" if enabled else "disabled"
    _set(key, value)


def get_all_features() -> dict:
    """Return all known feature states."""
    features = [
        "ai_chat", "ai_study_plans", "ai_quizzes",
        "ai_audio", "ai_exercises", "ai_diagrams",
    ]
    result = {}
    for f in features:
        result[f] = "enabled" if is_feature_enabled(f) else "disabled"
    return result


# ---- internal helpers ----

def _get(r, key: str) -> str | None:
    if r is not None:
        try:
            val = r.get(key)
            if val is not None:
                return val.decode() if isinstance(val, bytes) else val
        except Exception:
            pass
    return _memory_store.get(key)


def _set(key: str, value: str) -> None:
    r = _get_redis()
    if r is not None:
        try:
            r.set(key, value)
            return
        except Exception:
            pass
    _memory_store[key] = value
