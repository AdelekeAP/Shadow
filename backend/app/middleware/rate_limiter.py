"""
API rate limiting configuration using slowapi.
Protects expensive endpoints (auth, AI calls) from abuse.

Uses user-based keying for authenticated endpoints so students on shared
campus WiFi don't exhaust each other's limits. Falls back to IP for
unauthenticated requests (login, register, etc.).
"""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


def _get_user_or_ip(request: Request) -> str:
    """
    Extract user_id from JWT Bearer token if present, otherwise fall back
    to the remote IP address.  This keeps per-user rate limits isolated so
    students on the same campus network don't share a bucket.
    """
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from app.utils.auth import decode_access_token

            payload = decode_access_token(token)
            if payload and payload.get("user_id"):
                return f"user:{payload['user_id']}"
        except Exception:
            pass  # token invalid / expired — fall back to IP
    return get_remote_address(request)


limiter = Limiter(
    key_func=_get_user_or_ip,
    storage_uri=os.getenv("REDIS_URL", "memory://"),
    enabled=os.getenv("TESTING") != "true",
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    retry_after = getattr(exc, "retry_after", None)
    detail = "Rate limit exceeded. Please try again later."
    if retry_after:
        detail = f"Rate limit exceeded. Please try again in {retry_after} seconds."
    return JSONResponse(
        status_code=429,
        content={"detail": detail},
        headers={"Retry-After": str(retry_after)} if retry_after else {},
    )
