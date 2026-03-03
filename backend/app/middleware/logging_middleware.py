"""
Request logging middleware with correlation IDs.
Logs method, path, status code, and duration for every request.
Also persists usage logs to the database for /api/ paths.
"""
import logging
import os
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("shadow.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every request with a unique correlation ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Attach request_id to request state for downstream use
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
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
        logger.info(
            "Request completed",
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

                # Best-effort user_id extraction from JWT
                user_id = None
                auth_header = request.headers.get("authorization", "")
                if auth_header.startswith("Bearer "):
                    try:
                        from jose import jwt
                        import uuid as _uuid

                        token = auth_header.split(" ")[1]
                        payload = jwt.decode(
                            token,
                            os.environ.get("SECRET_KEY", ""),
                            algorithms=["HS256"],
                        )
                        user_id_str = payload.get("user_id")
                        if user_id_str:
                            user_id = _uuid.UUID(user_id_str)
                    except Exception:
                        pass

                log_session = SessionLocal()
                try:
                    log_entry = UsageLog(
                        user_id=user_id,
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
