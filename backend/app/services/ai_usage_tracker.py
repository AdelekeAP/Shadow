"""
AI Usage Tracker — Redis-backed daily counters with in-memory fallback.
Tracks per-user, per-feature AI usage with configurable daily limits.
"""
import logging
import os
from datetime import date

logger = logging.getLogger(__name__)

# In-memory fallback when Redis is unavailable
_memory_counters: dict[str, int] = {}

# Default daily limits (overridable via env vars)
_DAILY_LIMITS = {
    "ai_chat": int(os.getenv("AI_DAILY_LIMIT_CHAT", "100")),
    "ai_study_plans": int(os.getenv("AI_DAILY_LIMIT_PLANS", "20")),
    "ai_quizzes": int(os.getenv("AI_DAILY_LIMIT_QUIZZES", "30")),
    "ai_audio": int(os.getenv("AI_DAILY_LIMIT_AUDIO", "50")),
    "ai_exercises": int(os.getenv("AI_DAILY_LIMIT_EXERCISES", "30")),
    "ai_diagrams": int(os.getenv("AI_DAILY_LIMIT_DIAGRAMS", "20")),
}


def _get_redis():
    try:
        from app.services.cache_service import _get_redis as cache_redis
        return cache_redis()
    except Exception:
        return None


def _counter_key(user_id: str, feature: str) -> str:
    today = date.today().isoformat()
    return f"ai_usage:{user_id}:{today}:{feature}"


def track_usage(user_id: str, feature: str) -> int:
    """Increment and return the new count for today."""
    key = _counter_key(user_id, feature)
    r = _get_redis()
    if r is not None:
        try:
            count = r.incr(key)
            r.expire(key, 86400)  # TTL: 24 hours
            return count
        except Exception:
            pass
    # In-memory fallback
    _memory_counters[key] = _memory_counters.get(key, 0) + 1
    return _memory_counters[key]


def get_daily_usage(user_id: str, feature: str | None = None) -> dict:
    """Get today's usage counts. If feature is None, return all features."""
    features = [feature] if feature else list(_DAILY_LIMITS.keys())
    result = {}
    for f in features:
        key = _counter_key(user_id, f)
        r = _get_redis()
        count = 0
        if r is not None:
            try:
                val = r.get(key)
                count = int(val) if val else 0
            except Exception:
                count = _memory_counters.get(key, 0)
        else:
            count = _memory_counters.get(key, 0)
        result[f] = {"used": count, "limit": _DAILY_LIMITS.get(f, 100)}
    return result


def check_daily_limit(user_id: str, feature: str) -> bool:
    """Return True if user is under the daily limit for this feature."""
    key = _counter_key(user_id, feature)
    limit = _DAILY_LIMITS.get(feature, 100)
    r = _get_redis()
    count = 0
    if r is not None:
        try:
            val = r.get(key)
            count = int(val) if val else 0
        except Exception:
            count = _memory_counters.get(key, 0)
    else:
        count = _memory_counters.get(key, 0)
    return count < limit
