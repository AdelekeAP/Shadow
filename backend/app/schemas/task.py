"""
Task Schemas - Pydantic Models for Request/Response
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    """Base schema for task data"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: str = Field(..., max_length=50)
    weight: float = Field(..., gt=0, le=100, description="Task weight in marks (CA max 30, EXAM max 65)")
    max_marks: Optional[float] = Field(None, gt=0, le=100)
    category: str = Field(default="CA", max_length=10)
    due_date: Optional[datetime] = None
    effort_estimate: Optional[int] = Field(None, ge=0, description="Estimated effort in minutes")

    @validator('task_type')
    def validate_task_type(cls, v):
        valid_types = ['test', 'project', 'assignment', 'participation', 'exam', 'quiz', 'presentation', 'other']
        if v.lower() not in valid_types:
            raise ValueError(f'task_type must be one of {valid_types}')
        return v.lower()

    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['CA', 'EXAM']
        if v.upper() not in valid_categories:
            raise ValueError(f'category must be one of {valid_categories}')
        return v.upper()

    @validator('max_marks', always=True)
    def set_max_marks(cls, v, values):
        """If max_marks not provided, use weight"""
        if v is None and 'weight' in values:
            return values['weight']
        return v


class TaskCreate(TaskBase):
    """Schema for creating a new task"""
    user_course_id: str = Field(..., description="UUID of the enrolled course")
    is_completed: bool = Field(default=False, description="Mark task as already completed")
    earned_marks: Optional[float] = Field(None, ge=0, le=100, description="Marks earned if already completed")

    @validator('weight')
    def validate_weight_by_category(cls, v, values):
        """Ensure tasks don't exceed category limits (CA: 30, EXAM: 65)"""
        if 'category' in values:
            if values['category'] == 'CA' and v > 30:
                raise ValueError('CA tasks cannot exceed 30 marks (5 marks reserved for participation)')
            elif values['category'] == 'EXAM' and v > 65:
                raise ValueError('EXAM tasks cannot exceed 65 marks')
        return v

    @validator('earned_marks')
    def validate_earned_marks_on_create(cls, v, values):
        """Validate earned marks if provided"""
        if v is not None:
            # Must be marked as completed to have earned marks
            if not values.get('is_completed', False):
                raise ValueError('Task must be marked as completed to have earned marks')
            # Cannot exceed weight
            if 'weight' in values and v > values['weight']:
                raise ValueError('Earned marks cannot exceed task weight')
        return v


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    task_type: Optional[str] = Field(None, max_length=50)
    weight: Optional[float] = Field(None, gt=0, le=100)
    max_marks: Optional[float] = Field(None, gt=0, le=100)
    earned_marks: Optional[float] = Field(None, ge=0, le=100, description="Marks earned on task")
    category: Optional[str] = Field(None, max_length=10)
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None
    completed_at: Optional[datetime] = None
    is_late: Optional[bool] = None
    effort_estimate: Optional[int] = Field(None, ge=0)
    actual_effort: Optional[int] = Field(None, ge=0, description="Actual effort in minutes")

    @validator('earned_marks')
    def validate_earned_marks(cls, v, values):
        """Ensure earned marks don't exceed max marks"""
        if v is not None and 'max_marks' in values and values['max_marks'] is not None:
            if v > values['max_marks']:
                raise ValueError('earned_marks cannot exceed max_marks')
        return v


class TaskComplete(BaseModel):
    """Schema for marking a task as complete"""
    earned_marks: Optional[float] = Field(None, ge=0, le=100, description="Marks earned (if graded)")
    actual_effort: Optional[int] = Field(None, ge=0, description="Time spent in minutes")


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: str
    user_id: str
    user_course_id: str
    title: str
    description: Optional[str]
    task_type: str
    weight: float
    max_marks: float
    earned_marks: Optional[float]
    category: str
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    is_completed: bool
    is_late: bool
    effort_estimate: Optional[int]
    actual_effort: Optional[int]
    priority_score: Optional[float]
    is_urgent: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TaskWithCourse(TaskResponse):
    """Extended task schema with course details"""
    course_code: Optional[str] = None
    course_title: Optional[str] = None


class TaskStats(BaseModel):
    """Schema for task statistics"""
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    total_ca_available: float
    total_ca_earned: float
    completion_rate: float
    average_score: Optional[float]


class CourseTaskSummary(BaseModel):
    """Schema for summarizing tasks by course"""
    course_id: str
    course_code: str
    course_title: str
    total_ca_marks: float
    earned_ca_marks: float
    remaining_ca_marks: float
    ca_percentage: float
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    tasks: list[TaskResponse]

    class Config:
        from_attributes = True
