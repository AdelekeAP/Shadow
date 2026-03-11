"""
Shadow - Main FastAPI Application
Goal-Driven Academic Achievement System for PAU
"""
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Initialize Sentry for error tracking (only if DSN is configured)
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "development"),
        send_default_pii=False,
    )

# Configure structured JSON logging
from app.logging_config import setup_logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events"""
    # Startup
    logger.info("Starting Shadow API...")

    # === Environment validation ===
    _env = os.getenv("ENVIRONMENT", "development")
    _db_url = os.getenv("DATABASE_URL", "")

    if _env == "production":
        if not os.getenv("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY must be set in production")
        if not _db_url or _db_url == "postgresql://localhost:5432/shadow_db":
            raise RuntimeError("DATABASE_URL must be explicitly set in production")

    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY not set — SmartStudy AI features will be unavailable")

    # Log optional service status
    for svc, var in [("Redis", "REDIS_URL"), ("ClamAV", "CLAMAV_HOST"), ("SMTP", "SMTP_HOST"), ("Sentry", "SENTRY_DSN")]:
        if os.getenv(var):
            logger.info(f"  {svc}: configured")
        else:
            logger.info(f"  {svc}: not configured")

    # Start notification scheduler
    try:
        from app.services.notification_scheduler import start_scheduler
        start_scheduler()
        logger.info("Notification scheduler started")
    except Exception as e:
        logger.error(f"Failed to start notification scheduler: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Shadow API...")

    # Stop notification scheduler
    try:
        from app.services.notification_scheduler import stop_scheduler
        stop_scheduler()
        logger.info("Notification scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping notification scheduler: {e}")


# Tag metadata for OpenAPI documentation
tags_metadata = [
    {
        "name": "Authentication",
        "description": "User registration, login, and profile management. "
                       "JWT tokens are issued on login/register and must be included as a Bearer token in subsequent requests.",
    },
    {
        "name": "Courses",
        "description": "Course enrollment and management. Students can add courses for a semester, "
                       "track assessment components (CA and Exam), and view course-level analytics.",
    },
    {
        "name": "Tasks",
        "description": "Academic task management with intelligent prioritization. Tasks are ranked by "
                       "deadline proximity, grade impact, and course weight using a proprietary scoring algorithm.",
    },
    {
        "name": "CGPA",
        "description": "CGPA calculation and prediction engine using the PAU 5.0 grading scale. "
                       "Includes what-if scenario analysis and semester-by-semester breakdown.",
    },
    {
        "name": "Recommendations",
        "description": "AI-generated academic recommendations based on current performance, "
                       "task completion patterns, and target CGPA gap analysis.",
    },
    {
        "name": "Mood Tracking",
        "description": "Wellness monitoring with a 7-emotion classification model. Tracks mood type, "
                       "energy level, and optional free-text notes. Sentiment analysis is performed "
                       "automatically on text entries.",
    },
    {
        "name": "SmartStudy",
        "description": "The core AI-powered learning intervention system. Provides GPT-4 chat assistance, "
                       "generates personalized study plans with curated YouTube videos and articles, "
                       "and tracks before/after performance for effectiveness measurement.",
    },
    {
        "name": "Library",
        "description": "Peer-to-peer academic resource sharing. Students can upload PDFs and PPTX files, "
                       "which are processed and converted for easy viewing. Resources are searchable by "
                       "course and topic.",
    },
    {
        "name": "Content Curation",
        "description": "Automated content discovery and curation from YouTube, Reddit, and academic sources. "
                       "Resources are matched to study plan topics and ranked by relevance.",
    },
    {
        "name": "Notifications",
        "description": "Push and in-app notification system for task deadlines, study plan reminders, "
                       "and academic milestones. Includes user-configurable notification preferences.",
    },
    {
        "name": "Analytics",
        "description": "Effectiveness analytics dashboard for SmartStudy interventions. Provides summary metrics, "
                       "learning style breakdowns, temporal trends, mood-effectiveness correlation, "
                       "and per-topic performance analysis.",
    },
]

# Disable OpenAPI docs in production
_is_production = os.getenv("ENVIRONMENT") == "production"

# Create FastAPI app
app = FastAPI(
    title="Shadow API",
    docs_url=None if _is_production else "/api/docs",
    redoc_url=None if _is_production else "/api/redoc",
    description="""
## Shadow -- Goal-Driven Academic Achievement System

Shadow is an AI-powered academic achievement system designed for **Pan-Atlantic University (PAU)** students.
It combines intelligent task prioritization, CGPA prediction, and the **SmartStudy** AI learning
intervention system to help students achieve their target academic goals.

### Key Features

- **SmartStudy AI** -- GPT-4 powered learning assistant with personalized study plan generation
- **CGPA Analytics** -- PAU-specific grading engine on the 5.0 scale with what-if predictions
- **Task Management** -- Smart prioritization based on deadline proximity, grade impact, and course weight
- **Mood Tracking** -- Wellness monitoring with a 7-emotion NLP classification model
- **Learning Library** -- Peer-to-peer academic resource sharing with document processing
- **Content Curation** -- Automated discovery of YouTube, Reddit, and academic resources
- **Effectiveness Analytics** -- Before/after intervention tracking with statistical analysis

### PAU Grading Scale

| Grade | Points | Mark Range |
|-------|--------|------------|
| A     | 5.0    | 70 -- 100  |
| B     | 4.0    | 60 -- 69   |
| C     | 3.0    | 50 -- 59   |
| D     | 2.0    | 45 -- 49   |
| E     | 1.0    | 40 -- 44   |
| F     | 0.0    | 0 -- 39    |

Assessment split: **35% Continuous Assessment** (30% assessments + 5% participation) / **65% Exam**

### Authentication

All endpoints (except `/api/v1/auth/register` and `/api/v1/auth/login`) require a **JWT Bearer token**.
Include it in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

Tokens are returned upon successful registration or login.

### Rate Limiting

| Endpoint Group | Limit | Window |
|----------------|-------|--------|
| Authentication (`/auth/login`, `/auth/register`) | 5 requests | per minute |
| SmartStudy chat | 15 requests | per minute |
| Quiz creation | 10 requests | per minute |
| Audio generation | 6/min, 40/hr, 100/day | multi-window |
| Exercises & Study cards | 10/min, 60/hr | multi-window |
| Exercise validation | 20/min, 120/hr | multi-window |
| Library voting | 30 requests | per minute |
| All other endpoints | 60 requests | per minute |

Rate limits are enforced **per authenticated user** (via JWT). Unauthenticated endpoints fall back to IP-based limiting. Exceeding the limit returns `HTTP 429 Too Many Requests`.
""",
    version="2.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "Adeleke Paul Aladenusi",
        "url": "https://github.com/shadow-pau",
        "email": "shadow@pau.edu.ng",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Configure CORS - Environment-based origin restrictions
if os.getenv("ENVIRONMENT") == "production":
    origins = [
        os.getenv("PRODUCTION_FRONTEND_URL", "https://shadow.pau.edu.ng"),
    ]
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3004",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=3600
)

# Request correlation ID middleware (outermost — runs first, wraps everything)
from app.middleware.logging_middleware import RequestCorrelationMiddleware, RequestIDFilter
app.add_middleware(RequestCorrelationMiddleware)

# Attach RequestIDFilter to root logger so all log records include request_id
logging.getLogger().addFilter(RequestIDFilter())

# Security headers middleware
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Global exception handler — prevents stack traces from leaking to clients
from starlette.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = []
    for e in exc.errors():
        loc = " -> ".join(str(l) for l in e["loc"] if l != "body")
        errors.append(f"{loc}: {e['msg']}" if loc else e["msg"])
    return JSONResponse(
        status_code=422,
        content={"detail": "; ".join(errors)}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled error", extra={"path": request.url.path})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Auth dependency for protected endpoints
from app.utils.auth import get_current_user

# Root endpoint
@app.get(
    "/",
    summary="API Status Check",
    tags=["Health"],
    response_description="Returns API status, version, and documentation URL.",
)
async def root():
    """
    Root endpoint that confirms the Shadow API is running.

    Returns basic metadata including the API version and a link to the
    interactive documentation.
    """
    return {
        "message": "Welcome to Shadow API",
        "version": "2.0.0",
        "status": "active",
        "documentation": "/api/docs"
    }


# Health check endpoint
@app.get(
    "/health",
    summary="Health Check",
    tags=["Health"],
    response_description="Returns service health status and current environment.",
)
async def health_check():
    """
    Lightweight health-check endpoint for uptime monitors and load balancers.

    Returns the service status and the current deployment environment
    (e.g., `development`, `staging`, `production`).
    """
    return {
        "status": "healthy",
    }


@app.get(
    "/health/detailed",
    summary="Detailed Health Check",
    tags=["Health"],
    response_description="Returns health status of all service dependencies.",
)
async def detailed_health_check(current_user = Depends(get_current_user)):
    """
    Detailed health check that verifies connectivity to all external
    dependencies: PostgreSQL, Redis, and ClamAV.

    Requires authentication. Returns per-service status so operations teams
    can identify degraded states.
    """
    checks = {}

    # Database check
    try:
        from sqlalchemy import text
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = {"status": "healthy"}
    except Exception:
        checks["database"] = {"status": "unhealthy"}

    # Redis check
    try:
        from app.services.cache_service import _get_redis
        r = _get_redis()
        if r is not None:
            r.ping()
            checks["redis"] = {"status": "healthy"}
        else:
            checks["redis"] = {"status": "unavailable", "note": "Caching disabled"}
    except Exception:
        checks["redis"] = {"status": "unhealthy"}

    # ClamAV check
    try:
        from app.services.virus_scan_service import get_scanner_status
        scanner = get_scanner_status()
        if scanner["available"]:
            checks["clamav"] = {"status": "healthy"}
        else:
            checks["clamav"] = {"status": "unavailable", "note": "Files quarantined as pending"}
    except Exception:
        checks["clamav"] = {"status": "unhealthy"}

    overall = "healthy" if all(
        c.get("status") == "healthy" for c in checks.values()
    ) else "degraded"

    return {
        "status": overall,
        "services": checks
    }


# Import and include routers
from app.routes import auth, courses, tasks, cgpa, recommendations, mood, smartstudy, library, content_curation, notifications, analytics, semesters
from app.routes import admin

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["Courses"])
app.include_router(semesters.router, prefix="/api/v1", tags=["Semesters"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(cgpa.router, prefix="/api/v1", tags=["CGPA"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])
app.include_router(mood.router, prefix="/api/v1/mood", tags=["Mood Tracking"])
app.include_router(smartstudy.router, tags=["SmartStudy"])
app.include_router(library.router, prefix="/api/v1", tags=["Library"])
app.include_router(content_curation.router, tags=["Content Curation"])
app.include_router(notifications.router, prefix="/api/v1", tags=["Notifications"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
