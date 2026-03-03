"""
Shadow - Main FastAPI Application
Goal-Driven Academic Achievement System for PAU
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Configure structured JSON logging
from app.logging_config import setup_logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events"""
    # Startup
    logger.info("Starting Shadow API...")

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

# Create FastAPI app
app = FastAPI(
    title="Shadow API",
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

Authentication endpoints are rate-limited to **5 requests per minute** per client IP to prevent abuse.
""",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "Shadow Development Team",
        "url": "https://github.com/shadow-pau",
        "email": "shadow@pau.edu.ng",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Configure CORS - Allow frontend to make requests
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
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Request logging middleware
from app.middleware.logging_middleware import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting
from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


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
        "environment": os.getenv("ENVIRONMENT", "production")
    }


# Import and include routers
from app.routes import auth, courses, tasks, cgpa, recommendations, mood, smartstudy, library, content_curation, notifications, analytics, semesters

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
