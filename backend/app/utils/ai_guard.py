"""
AI Guard — FastAPI dependency that enforces feature flags and daily usage limits
before any AI endpoint is called.
"""
from fastapi import Depends, HTTPException, status
from app.utils.auth import get_current_user
from app.models.user import User


def require_ai_feature(feature_name: str):
    """Return a FastAPI dependency that checks feature flag + daily limit."""

    async def _guard(current_user: User = Depends(get_current_user)):
        from app.services.feature_flags import is_feature_enabled
        from app.services.ai_usage_tracker import check_daily_limit, track_usage, get_daily_usage

        if not is_feature_enabled(feature_name, user_id=str(current_user.id)):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="This feature is temporarily unavailable",
            )

        if not check_daily_limit(str(current_user.id), feature_name):
            usage = get_daily_usage(str(current_user.id), feature_name)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily AI usage limit reached. Try again tomorrow.",
                headers={"X-AI-Usage": str(usage)},
            )

        # Track the usage
        track_usage(str(current_user.id), feature_name)

    return _guard
