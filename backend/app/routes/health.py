"""
Health check endpoint for load balancers and uptime monitors.

GET /api/v1/health returns status of database and Redis dependencies.
No authentication required.
"""
import logging

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    summary="Health Check",
    response_description="Returns health status of database and Redis.",
)
async def health_check(response: Response):
    """
    Public health-check endpoint that verifies database and Redis connectivity.

    - **database**: runs ``SELECT 1`` against PostgreSQL. Returns ``"degraded"``
      on failure (HTTP 503).
    - **redis**: calls ``cache_get("health_check")``. Returns ``"degraded"`` on
      failure but remains HTTP 200 (non-fatal).
    """
    checks = {
        "database": "ok",
        "redis": "ok",
    }

    # --- Database check ---
    db_healthy = True
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Health check: database unreachable: %s", exc)
        checks["database"] = "degraded"
        db_healthy = False

    # --- Redis check ---
    try:
        from app.services.cache_service import cache_get
        cache_get("health_check")  # None is fine; we just verify no exception
    except Exception as exc:
        logger.warning("Health check: Redis unreachable: %s", exc)
        checks["redis"] = "degraded"

    status = "healthy" if db_healthy else "degraded"
    if not db_healthy:
        response.status_code = 503

    return {
        "status": status,
        "checks": checks,
    }
