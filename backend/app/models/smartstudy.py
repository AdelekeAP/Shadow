"""
SmartStudy Models - AI Learning Intervention System
Includes chat conversations, study plans, resources, and effectiveness tracking
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class ChatConversation(Base):
    """
    Chat Conversation - Container for AI chat messages
    """
    __tablename__ = "chat_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    title = Column(String(255), nullable=True)  # Auto-generated from first message

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    messages = relationship("ChatMessage", backref="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatConversation(id={self.id}, title={self.title})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChatMessage(Base):
    """
    Chat Message - Individual message in a conversation
    """
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('chat_conversations.id', ondelete='CASCADE'), nullable=False, index=True)

    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)  # For cost tracking
    model_used = Column(String(50), nullable=True, default='gpt-4')

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role,
            "content": self.content,
            "tokens_used": self.tokens_used,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class StudyPlan(Base):
    """
    Study Plan - Personalized learning intervention plan
    """
    __tablename__ = "study_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='SET NULL'), nullable=True)

    topic = Column(String(255), nullable=False, index=True)

    # Trigger information
    trigger_type = Column(String(50), nullable=True)  # 'reactive', 'proactive', 'preventive', 'exploratory'
    trigger_task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    trigger_score = Column(Numeric(5, 2), nullable=True)  # Score that triggered intervention

    # Plan content (GPT-4 generated JSON structure)
    plan_data = Column(JSONB, nullable=False)

    duration_days = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Progress tracking
    completion_percentage = Column(Numeric(5, 2), nullable=True, default=0)
    is_active = Column(Boolean, default=True, index=True)

    # Effectiveness tracking
    before_score = Column(Numeric(5, 2), nullable=True)  # Baseline performance
    after_score = Column(Numeric(5, 2), nullable=True)  # Performance after intervention
    effectiveness_score = Column(Numeric(5, 2), nullable=True)  # Calculated improvement

    # Learning style tracking (Phase 2 Week 2)
    learning_style_used = Column(String(50), nullable=True)  # 'visual', 'audio', 'reading', 'kinesthetic'
    completed_days = Column(JSONB, nullable=True, default=[])  # Array of completed day numbers

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    resources = relationship("StudyPlanResource", backref="study_plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StudyPlan(id={self.id}, topic={self.topic}, active={self.is_active})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "course_id": str(self.course_id) if self.course_id else None,
            "topic": self.topic,
            "trigger_type": self.trigger_type,
            "trigger_task_id": str(self.trigger_task_id) if self.trigger_task_id else None,
            "trigger_score": float(self.trigger_score) if self.trigger_score else None,
            "plan_data": self.plan_data,
            "duration_days": self.duration_days,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "completion_percentage": float(self.completion_percentage) if self.completion_percentage else 0.0,
            "is_active": self.is_active,
            "before_score": float(self.before_score) if self.before_score else None,
            "after_score": float(self.after_score) if self.after_score else None,
            "effectiveness_score": float(self.effectiveness_score) if self.effectiveness_score else None,
            "learning_style_used": self.learning_style_used,
            "completed_days": self.completed_days if self.completed_days else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class StudyPlanResource(Base):
    """
    Study Plan Resource - Individual learning resource in a study plan
    """
    __tablename__ = "study_plan_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_plan_id = Column(UUID(as_uuid=True), ForeignKey('study_plans.id', ondelete='CASCADE'), nullable=False, index=True)

    resource_type = Column(String(50), nullable=False)  # 'youtube_video', 'reddit_post', 'ai_explanation', 'pauarchive_link'
    resource_url = Column(Text, nullable=True)
    resource_title = Column(Text, nullable=True)
    resource_description = Column(Text, nullable=True)
    quality_score = Column(Numeric(5, 2), nullable=True)  # CrowdCurate quality score (0-100)

    # Engagement tracking
    clicked = Column(Boolean, default=False)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    completed = Column(Boolean, default=False)
    helpful_rating = Column(Integer, nullable=True)  # 1-5 stars

    day_number = Column(Integer, nullable=True)  # Which day in the plan
    order_in_day = Column(Integer, nullable=True)  # Order within day

    # Report tracking (Phase A)
    report_reason = Column(String(50), nullable=True)  # broken_link, irrelevant, outdated
    reported_at = Column(DateTime(timezone=True), nullable=True)

    # Audio summary (Phase B)
    audio_file_path = Column(String(500), nullable=True)
    audio_script = Column(Text, nullable=True)
    audio_generated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<StudyPlanResource(id={self.id}, type={self.resource_type})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "study_plan_id": str(self.study_plan_id),
            "resource_type": self.resource_type,
            "resource_url": self.resource_url,
            "resource_title": self.resource_title,
            "resource_description": self.resource_description,
            "quality_score": float(self.quality_score) if self.quality_score else None,
            "clicked": self.clicked,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "completed": self.completed,
            "helpful_rating": self.helpful_rating,
            "day_number": self.day_number,
            "order_in_day": self.order_in_day,
            "report_reason": self.report_reason,
            "reported_at": self.reported_at.isoformat() if self.reported_at else None,
            "has_audio": self.audio_file_path is not None,
            "audio_url": f"/api/v1/smartstudy/audio/{self.audio_file_path}" if self.audio_file_path else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UploadedDocument(Base):
    """
    Uploaded Document - User-uploaded files for AI analysis (optional feature)
    """
    __tablename__ = "uploaded_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('chat_conversations.id', ondelete='SET NULL'), nullable=True)

    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)

    # AI Analysis (GPT-4 Vision)
    analyzed = Column(Boolean, default=False)
    analyzed_topics = Column(JSONB, nullable=True)  # Extracted topics
    analysis_confidence = Column(String(20), nullable=True)  # 'high', 'medium', 'low'

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<UploadedDocument(id={self.id}, file={self.file_name})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "task_id": str(self.task_id) if self.task_id else None,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "analyzed": self.analyzed,
            "analyzed_topics": self.analyzed_topics,
            "analysis_confidence": self.analysis_confidence,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }


class InterventionOutcome(Base):
    """
    Intervention Outcome - Tracks effectiveness of SmartStudy interventions
    """
    __tablename__ = "intervention_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    study_plan_id = Column(UUID(as_uuid=True), ForeignKey('study_plans.id', ondelete='SET NULL'), nullable=True)

    # Performance metrics
    before_score = Column(Numeric(5, 2), nullable=True)
    after_score = Column(Numeric(5, 2), nullable=True)
    grade_improvement = Column(Numeric(5, 2), nullable=True)

    # Learning metrics
    days_to_improvement = Column(Integer, nullable=True)
    completion_rate = Column(Numeric(5, 2), nullable=True)
    resource_engagement_rate = Column(Numeric(5, 2), nullable=True)

    # Context
    intervention_type = Column(String(50), nullable=True)  # 'chat_only', 'study_plan', 'both'
    student_mood_during = Column(String(50), nullable=True)

    measured_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<InterventionOutcome(id={self.id}, improvement={self.grade_improvement})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "study_plan_id": str(self.study_plan_id) if self.study_plan_id else None,
            "before_score": float(self.before_score) if self.before_score else None,
            "after_score": float(self.after_score) if self.after_score else None,
            "grade_improvement": float(self.grade_improvement) if self.grade_improvement else None,
            "days_to_improvement": self.days_to_improvement,
            "completion_rate": float(self.completion_rate) if self.completion_rate else None,
            "resource_engagement_rate": float(self.resource_engagement_rate) if self.resource_engagement_rate else None,
            "intervention_type": self.intervention_type,
            "student_mood_during": self.student_mood_during,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
        }


class ContentQualityScore(Base):
    """
    Content Quality Score - Cached quality scores for curated resources
    """
    __tablename__ = "content_quality_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    content_type = Column(String(50), nullable=True)  # 'youtube_video', 'reddit_post'
    content_id = Column(String(255), nullable=False, unique=True)  # External ID
    content_url = Column(Text, nullable=True)
    content_title = Column(Text, nullable=True)
    topic = Column(String(255), nullable=True, index=True)

    # Quality signals
    engagement_score = Column(Numeric(5, 2), nullable=True)  # Likes, views, comments
    sentiment_score = Column(Numeric(5, 2), nullable=True)  # Comment sentiment
    community_score = Column(Numeric(5, 2), nullable=True)  # Reddit upvotes
    student_rating = Column(Numeric(5, 2), nullable=True)  # Shadow user ratings

    # Composite score (0-100)
    quality_score = Column(Numeric(5, 2), nullable=True, index=True)

    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ContentQualityScore(id={self.content_id}, quality={self.quality_score})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "content_type": self.content_type,
            "content_id": self.content_id,
            "content_url": self.content_url,
            "content_title": self.content_title,
            "topic": self.topic,
            "engagement_score": float(self.engagement_score) if self.engagement_score else None,
            "sentiment_score": float(self.sentiment_score) if self.sentiment_score else None,
            "community_score": float(self.community_score) if self.community_score else None,
            "student_rating": float(self.student_rating) if self.student_rating else None,
            "quality_score": float(self.quality_score) if self.quality_score else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class VideoNote(Base):
    """
    Video Note - Notes taken while watching videos in study plans
    Supports timestamped notes and highlights for video learning
    """
    __tablename__ = "video_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), ForeignKey('study_plan_resources.id', ondelete='CASCADE'), nullable=False, index=True)

    # Note content
    content = Column(Text, nullable=False)

    # Video timestamp (in seconds) - optional
    timestamp_seconds = Column(Integer, nullable=True)

    # Note type for organization
    note_type = Column(String(50), default='note')  # 'note', 'highlight', 'question', 'summary'

    # Color coding for visual organization
    color = Column(String(20), default='yellow')  # 'yellow', 'green', 'blue', 'pink', 'orange'

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<VideoNote(id={self.id}, timestamp={self.timestamp_seconds})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "resource_id": str(self.resource_id),
            "content": self.content,
            "timestamp_seconds": self.timestamp_seconds,
            "note_type": self.note_type,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def format_timestamp(self):
        """Format timestamp as MM:SS or HH:MM:SS"""
        if self.timestamp_seconds is None:
            return None
        hours = self.timestamp_seconds // 3600
        minutes = (self.timestamp_seconds % 3600) // 60
        seconds = self.timestamp_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
