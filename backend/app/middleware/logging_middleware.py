"""
Request correlation ID middleware for structured logging.
Logs method, path, status code, and duration for every request.
Also persists usage logs to the database for /api/ paths.

In production (ENVIRONMENT=production), request logs are emitted as structured
JSON objects.  In development, a compact human-readable format is used instead.
"""
import json as _json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_var: ContextVar[str] = ContextVar('request_id', default='')

logger = logging.getLogger("shadow.requests")

_IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"


def _extract_user_id_from_request(request: Request) -> str:
    """Best-effort user_id extraction from JWT in the Authorization header.

    Returns the user_id string or ``"anonymous"`` when the token is absent,
    invalid, or does not contain a user_id claim.
    """
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt as _jwt
            token = auth_header.split(" ", 1)[1]
            payload = _jwt.decode(
                token,
                os.environ.get("SECRET_KEY", ""),
                algorithms=["HS256"],
            )
            uid = payload.get("user_id")
            if uid:
                return str(uid)
        except Exception:
            pass
    return "anonymous"


class RequestIDFilter(logging.Filter):
    """Logging filter that injects the current request_id into every log record."""

    def filter(self, record):
        record.request_id = request_id_var.get('')
        return True


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a correlation ID to every request.

    Accepts an incoming ``X-Request-ID`` header or generates a new UUID.
    The ID is stored in a ``ContextVar`` so that all log records emitted
    during the request automatically include it (via ``RequestIDFilter``).
    The ID is returned to the client in the ``X-Request-ID`` response header.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request_id_var.set(request_id)

        # Also attach to request.state for downstream route handlers
        request.state.request_id = request_id

        start_time = time.perf_counter()

        # Extract user_id once for logging
        user_id = _extract_user_id_from_request(request)
        ip = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            if _IS_PRODUCTION:
                logger.error(
                    _json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "method": request.method,
                        "path": request.url.path,
                        "status": 500,
                        "duration_ms": round(duration_ms, 2),
                        "user_id": user_id,
                        "ip": ip,
                    }),
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": round(duration_ms, 2),
                    },
                )
            else:
                logger.error(
                    "Request failed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": round(duration_ms, 2),
                    },
                )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        if _IS_PRODUCTION:
            # Structured JSON log line for production
            logger.info(
                _json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "user_id": user_id,
                    "ip": ip,
                }),
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
        else:
            # Human-readable log line for development
            logger.info(
                f"{request.method} {request.url.path} {response.status_code} {duration_ms / 1000:.3f}s",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

        response.headers["X-Request-ID"] = request_id

        # Best-effort UsageLog insertion for API paths
        if request.url.path.startswith("/api/"):
            try:
                from app.database import SessionLocal
                from app.models.usage_log import UsageLog

                import uuid as _uuid
                db_user_id = None
                if user_id != "anonymous":
                    try:
                        db_user_id = _uuid.UUID(user_id)
                    except Exception:
                        pass

                log_session = SessionLocal()
                try:
                    log_entry = UsageLog(
                        user_id=db_user_id,
                        endpoint_path=request.url.path,
                        http_method=request.method,
                        status_code=response.status_code,
                        response_time_ms=round(duration_ms, 2),
                    )
                    log_session.add(log_entry)
                    log_session.commit()
                finally:
                    log_session.close()
            except Exception:
                pass  # Never let logging break the request

        return response
