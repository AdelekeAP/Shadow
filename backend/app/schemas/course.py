"""
Course Schemas - Pydantic Models for Request/Response
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class CourseBase(BaseModel):
    """Base schema for course data"""
    code: str = Field(..., min_length=3, max_length=20)
    title: str = Field(..., min_length=3, max_length=255)
    credits: int = Field(..., ge=1, le=6)
    level: Optional[str] = Field("400", max_length=10)
    status: Optional[str] = Field("C", max_length=20)
    department: Optional[str] = Field("Computer Science", max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['C', 'E', 'R']  # Compulsory, Elective, Required
        if v and v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v


class CourseCreate(CourseBase):
    """Schema for creating a new course (admin or user)"""
    pass


class CourseResponse(CourseBase):
    """Schema for course response"""
    id: str
    created_by: str
    is_approved: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserCourseCreate(BaseModel):
    """Schema for enrolling in a course"""
    course_id: str
    semester_id: Optional[str] = None
    is_carryover: Optional[bool] = False
    is_priority: Optional[bool] = False


class UserCourseUpdate(BaseModel):
    """Schema for updating enrollment details"""
    is_carryover: Optional[bool] = None
    is_priority: Optional[bool] = None
    ca_score: Optional[float] = Field(None, ge=0, le=35)
    participation_score: Optional[float] = Field(None, ge=0, le=5)
    exam_score: Optional[float] = Field(None, ge=0, le=65)


class UserCourseResponse(BaseModel):
    """Schema for user course enrollment response"""
    id: str
    user_id: str
    semester_id: Optional[str]
    course_id: str
    is_carryover: bool
    is_priority: bool

    # PAU-specific fields
    ca_score: float
    participation_score: Optional[float]
    exam_score: Optional[float]
    predicted_exam_score: Optional[float]

    # Grades
    current_score: Optional[float]
    predicted_score: Optional[float]
    current_grade_point: Optional[float]
    predicted_grade_point: Optional[float]
    letter_grade: Optional[str]
    predicted_letter_grade: Optional[str]

    completion_rate: float
    enrolled_at: Optional[datetime]
    updated_at: Optional[datetime]

    # Include course details
    course: Optional[CourseResponse]

    class Config:
        from_attributes = True


class UserCourseWithDetails(UserCourseResponse):
    """Extended schema with additional computed fields"""
    pass


class SemesterCreate(BaseModel):
    """Schema for creating a semester"""
    name: str = Field(..., min_length=3, max_length=50)
    academic_year: Optional[str] = Field(None, max_length=20)
    semester_number: Optional[int] = Field(None, ge=1, le=2)
    start_date: datetime
    end_date: datetime
    target_gpa: Optional[float] = Field(None, ge=0.0, le=5.0)

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class SemesterUpdate(BaseModel):
    """Schema for updating a semester"""
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    target_gpa: Optional[float] = Field(None, ge=0.0, le=5.0)
    actual_gpa: Optional[float] = Field(None, ge=0.0, le=5.0)
    is_active: Optional[bool] = None


class SemesterResponse(BaseModel):
    """Schema for semester response"""
    id: str
    user_id: str
    name: str
    academic_year: Optional[str]
    semester_number: Optional[int]
    start_date: datetime
    end_date: datetime
    target_gpa: Optional[float]
    actual_gpa: Optional[float]
    is_active: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
