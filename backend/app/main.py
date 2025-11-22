"""
Shadow - Main FastAPI Application
Goal-Driven Academic Achievement System for PAU
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Shadow API",
    description="Goal-Driven Academic Achievement System for Pan-Atlantic University",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS - Allow frontend to make requests
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
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


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API status check
    """
    return {
        "message": "Welcome to Shadow API",
        "version": "1.0.0",
        "status": "active",
        "documentation": "/api/docs"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "production")
    }


# Import and include routers
from app.routes import auth, courses, tasks, cgpa, recommendations, mood

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["Courses"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(cgpa.router, prefix="/api/v1", tags=["CGPA"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])
app.include_router(mood.router, prefix="/api/v1/mood", tags=["Mood Tracking"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
