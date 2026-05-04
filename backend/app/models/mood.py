"""
Mood Log Model - Track student mood and energy levels
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.database import Base


class MoodLog(Base):
    """
    MoodLog Model - Student mood tracking for better task recommendations
    """
    __tablename__ = "mood_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Mood details — user self-reported via UI buttons
    mood_type = Column(String(50), nullable=False)  # 'focused', 'motivated', 'calm', 'confident', 'tired', 'stressed', 'anxious', 'overwhelmed'
    energy_level = Column(Integer, nullable=False)  # 1-5 scale
    note = Column(Text, nullable=True)  # Optional text note

    # Optional linkage to course/task
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='SET NULL'), nullable=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)

    # ML-detected emotion from `note` text — j-hartmann/emotion-english-distilroberta-base (7 classes)
    sentiment_score = Column(Integer, nullable=True)  # -1 / 0 / 1 polarity derived from primary_emotion (legacy)
    primary_emotion = Column(String(50), nullable=True)  # 'anger', 'disgust', 'fear', 'joy', 'neutral', 'sadness', 'surprise'
    emotion_confidence = Column(Numeric(3, 3), nullable=True)  # 0.000-1.000
    emotion_scores = Column(JSONB, nullable=True)  # All 7 scores: {"joy": 0.892, "neutral": 0.045, ...}

    logged_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<MoodLog(user_id={self.user_id}, mood={self.mood_type}, energy={self.energy_level})>"

    def to_dict(self):
        """Convert mood log to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "mood_type": self.mood_type,
            "energy_level": self.energy_level,
            "note": self.note,
            "course_id": str(self.course_id) if self.course_id else None,
            "task_id": str(self.task_id) if self.task_id else None,
            "sentiment_score": self.sentiment_score,
            "primary_emotion": self.primary_emotion,
            "emotion_confidence": float(self.emotion_confidence) if self.emotion_confidence else None,
            "emotion_scores": self.emotion_scores,
            "logged_at": self.logged_at.isoformat() if self.logged_at else None
        }
