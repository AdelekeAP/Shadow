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
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
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
from app.routes import auth, courses, tasks

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["Courses"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])

# TODO: Add other routers
# from app.routes import users, moods, gpa
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(moods.router, prefix="/api/v1/moods", tags=["Moods"])
# app.include_router(gpa.router, prefix="/api/v1/gpa", tags=["GPA"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
