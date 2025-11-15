"""
Pydantic Schemas for Request/Response Validation
"""
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData
)
from app.schemas.course import (
    CourseBase,
    CourseCreate,
    CourseResponse,
    UserCourseCreate,
    UserCourseUpdate,
    UserCourseResponse,
    SemesterCreate,
    SemesterUpdate,
    SemesterResponse
)
from app.schemas.task import (
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskComplete,
    TaskResponse,
    TaskWithCourse,
    TaskStats,
    CourseTaskSummary
)

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    "CourseBase",
    "CourseCreate",
    "CourseResponse",
    "UserCourseCreate",
    "UserCourseUpdate",
    "UserCourseResponse",
    "SemesterCreate",
    "SemesterUpdate",
    "SemesterResponse",
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskComplete",
    "TaskResponse",
    "TaskWithCourse",
    "TaskStats",
    "CourseTaskSummary"
]
