"""
Pydantic Schemas for SmartStudy v2.0
Handles chat conversations, study plans, and AI interactions
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


# ============================================================================
# Chat Schemas
# ============================================================================

class ChatMessageCreate(BaseModel):
    """Schema for creating a new chat message"""
    content: str = Field(..., min_length=1, max_length=5000, description="Message content")
    conversation_id: Optional[UUID] = Field(None, description="Existing conversation ID (if continuing chat)")


class ChatMessageResponse(BaseModel):
    """Schema for chat message response"""
    id: UUID
    conversation_id: UUID
    role: str  # 'user' or 'assistant'
    content: str
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatConversationResponse(BaseModel):
    """Schema for chat conversation response"""
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class ChatConversationList(BaseModel):
    """Schema for list of conversations"""
    id: UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


# ============================================================================
# Study Plan Schemas
# ============================================================================

class StudyPlanCreate(BaseModel):
    """Schema for creating a study plan"""
    course_id: Optional[UUID] = None
    topic: str = Field(..., min_length=1, max_length=255)
    trigger_type: Optional[str] = Field(None, description="reactive, proactive, preventive, exploratory")
    trigger_task_id: Optional[UUID] = None
    trigger_score: Optional[float] = None
    duration_days: Optional[int] = Field(None, ge=1, le=30)
    difficulty_level: Optional[str] = Field("auto", description="beginner, intermediate, advanced, or auto")
    learning_style: Optional[str] = Field(None, description="visual, audio, reading, kinesthetic, or auto")


class StudyPlanResourceResponse(BaseModel):
    """Schema for study plan resource response"""
    id: UUID
    study_plan_id: UUID
    resource_type: str  # 'youtube_video', 'reddit_post', 'ai_explanation', 'pauarchive_link'
    resource_url: Optional[str] = None
    resource_title: Optional[str] = None
    resource_description: Optional[str] = None
    quality_score: Optional[float] = None
    clicked: bool = False
    completed: bool = False
    helpful_rating: Optional[int] = None
    day_number: Optional[int] = None
    order_in_day: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StudyPlanResponse(BaseModel):
    """Schema for study plan response"""
    id: UUID
    user_id: UUID
    course_id: Optional[UUID] = None
    topic: str
    trigger_type: Optional[str] = None
    trigger_task_id: Optional[UUID] = None
    trigger_score: Optional[float] = None
    plan_data: Dict[str, Any]  # JSON structure from GPT-4
    duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    completion_percentage: float = 0.0
    is_active: bool = True
    before_score: Optional[float] = None
    after_score: Optional[float] = None
    effectiveness_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    resources: List[StudyPlanResourceResponse] = []

    class Config:
        from_attributes = True


class StudyPlanUpdate(BaseModel):
    """Schema for updating a study plan"""
    completion_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    is_active: Optional[bool] = None
    before_score: Optional[float] = None
    after_score: Optional[float] = None
    completed_days: Optional[List[int]] = None


class ResourceClickUpdate(BaseModel):
    """Schema for marking a resource as clicked"""
    clicked: bool = True


class ResourceCompletionUpdate(BaseModel):
    """Schema for marking a resource as completed"""
    completed: bool = True
    helpful_rating: Optional[int] = Field(None, ge=1, le=5)


class ResourceReportCreate(BaseModel):
    """Schema for reporting a broken/irrelevant resource"""
    reason: str = Field("broken_link", pattern="^(broken_link|irrelevant|outdated)$", description="broken_link, irrelevant, or outdated")


# ============================================================================
# Document Upload Schemas
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Schema for uploaded document response"""
    id: UUID
    user_id: UUID
    task_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    analyzed: bool = False
    analyzed_topics: Optional[Dict[str, Any]] = None
    analysis_confidence: Optional[str] = None
    uploaded_at: datetime
    analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Intervention Outcome Schemas
# ============================================================================

class InterventionOutcomeCreate(BaseModel):
    """Schema for creating an intervention outcome"""
    study_plan_id: Optional[UUID] = None
    before_score: Optional[float] = None
    after_score: Optional[float] = None
    grade_improvement: Optional[float] = None
    days_to_improvement: Optional[int] = None
    completion_rate: Optional[float] = None
    resource_engagement_rate: Optional[float] = None
    intervention_type: Optional[str] = None  # 'chat_only', 'study_plan', 'both'
    student_mood_during: Optional[str] = None


class InterventionOutcomeResponse(BaseModel):
    """Schema for intervention outcome response"""
    id: UUID
    user_id: UUID
    study_plan_id: Optional[UUID] = None
    before_score: Optional[float] = None
    after_score: Optional[float] = None
    grade_improvement: Optional[float] = None
    days_to_improvement: Optional[int] = None
    completion_rate: Optional[float] = None
    resource_engagement_rate: Optional[float] = None
    intervention_type: Optional[str] = None
    student_mood_during: Optional[str] = None
    measured_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SmartStudy Request/Response Schemas
# ============================================================================

class SmartStudyContextResponse(BaseModel):
    """Schema for SmartStudy student context"""
    student_info: Dict[str, Any]
    struggling_courses: List[Dict[str, Any]]
    recent_moods: List[Dict[str, Any]]
    at_risk_tasks: List[Dict[str, Any]]
    cgpa_status: Dict[str, Any]


class SmartStudySuggestedPrompt(BaseModel):
    """Schema for suggested chat prompts"""
    prompt: str
    category: str  # 'struggling', 'planning', 'motivation', 'clarification'
    icon: str  # Emoji


class SmartStudyDashboardTrigger(BaseModel):
    """Schema for dashboard trigger conditions"""
    show_trigger: bool
    trigger_type: str  # 'at_risk', 'struggling', 'behind_schedule'
    trigger_message: str
    suggested_action: str


# ============================================================================
# Video Notes Schemas
# ============================================================================

class VideoNoteCreate(BaseModel):
    """Schema for creating a video note"""
    resource_id: UUID
    content: str = Field(..., min_length=1, max_length=5000, description="Note content")
    timestamp_seconds: Optional[int] = Field(None, ge=0, description="Video timestamp in seconds")
    note_type: Optional[str] = Field("note", description="note, highlight, question, summary")
    color: Optional[str] = Field("yellow", description="Note color: yellow, green, blue, pink, orange")


class VideoNoteUpdate(BaseModel):
    """Schema for updating a video note"""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    timestamp_seconds: Optional[int] = Field(None, ge=0)
    note_type: Optional[str] = None
    color: Optional[str] = None


class VideoNoteResponse(BaseModel):
    """Schema for video note response"""
    id: UUID
    user_id: UUID
    resource_id: UUID
    content: str
    timestamp_seconds: Optional[int] = None
    formatted_timestamp: Optional[str] = None
    note_type: str = "note"
    color: str = "yellow"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoNotesListResponse(BaseModel):
    """Schema for listing video notes"""
    notes: List[VideoNoteResponse]
    total_count: int
    resource_id: UUID


# ============================================================================
# Quiz Schemas
# ============================================================================

class QuizCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=255)
    quiz_type: str = Field("quick_quiz")
    question_count: Optional[int] = Field(None, ge=5, le=50)
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=180)
    difficulty_level: Optional[str] = Field("mixed")
    study_plan_id: Optional[str] = None
    course_id: Optional[str] = None


class QuizAnswer(BaseModel):
    question_id: int
    user_answer: str = Field("", max_length=5000)


class QuizSubmission(BaseModel):
    answers: List[QuizAnswer] = Field(..., min_length=1, max_length=50)
    time_taken_seconds: Optional[int] = Field(None, ge=0)
    timed_out: bool = False
