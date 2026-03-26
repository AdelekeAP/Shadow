"""
Admin Routes — Feature flag management and AI usage monitoring.
Protected by admin email check.
"""
import os
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.utils.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

_ADMIN_EMAILS = set(
    e.strip().lower()
    for e in os.getenv("ADMIN_EMAILS", "").split(",")
    if e.strip()
)


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email.lower() not in _ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/features", operation_id="list_features", summary="List all feature flag states")
async def list_features(admin: User = Depends(_require_admin)):
    from app.services.feature_flags import get_all_features
    return get_all_features()


@router.post("/features/{name}/disable", operation_id="disable_feature", summary="Globally disable a feature")
async def disable_feature(name: str, admin: User = Depends(_require_admin)):
    from app.services.feature_flags import set_feature
    set_feature(name, enabled=False)
    logger.warning(f"Admin {admin.email} disabled feature: {name}")
    return {"feature": name, "status": "disabled"}


@router.post("/features/{name}/enable", operation_id="enable_feature", summary="Globally enable a feature")
async def enable_feature(name: str, admin: User = Depends(_require_admin)):
    from app.services.feature_flags import set_feature
    set_feature(name, enabled=True)
    logger.info(f"Admin {admin.email} enabled feature: {name}")
    return {"feature": name, "status": "enabled"}


@router.post(
    "/features/{name}/users/{user_id}/disable",
    operation_id="disable_feature_for_user",
    summary="Disable a feature for a specific user",
)
async def disable_feature_for_user(name: str, user_id: str, admin: User = Depends(_require_admin)):
    from app.services.feature_flags import set_feature
    set_feature(name, enabled=False, user_id=user_id)
    logger.warning(f"Admin {admin.email} disabled feature {name} for user {user_id}")
    return {"feature": name, "user_id": user_id, "status": "disabled"}


@router.post(
    "/features/{name}/users/{user_id}/enable",
    operation_id="enable_feature_for_user",
    summary="Enable a feature for a specific user",
)
async def enable_feature_for_user(name: str, user_id: str, admin: User = Depends(_require_admin)):
    from app.services.feature_flags import set_feature
    set_feature(name, enabled=True, user_id=user_id)
    logger.info(f"Admin {admin.email} enabled feature {name} for user {user_id}")
    return {"feature": name, "user_id": user_id, "status": "enabled"}


@router.get(
    "/ai-usage/{user_id}",
    operation_id="get_user_ai_usage",
    summary="View a user's daily AI usage",
)
async def get_user_ai_usage(user_id: str, admin: User = Depends(_require_admin)):
    from app.services.ai_usage_tracker import get_daily_usage
    return get_daily_usage(user_id)
