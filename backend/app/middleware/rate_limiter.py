"""
API rate limiting configuration using slowapi.
Protects expensive endpoints (auth, AI calls) from abuse.
"""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.getenv("TESTING") != "true",
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )
