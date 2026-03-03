"""
Quiz Models - AI-Powered Knowledge Testing
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    study_plan_id = Column(UUID(as_uuid=True), ForeignKey('study_plans.id', ondelete='SET NULL'), nullable=True)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id', ondelete='SET NULL'), nullable=True)

    title = Column(String(255), nullable=False)
    topic = Column(String(255), nullable=False, index=True)
    quiz_type = Column(String(50), nullable=False)  # 'quick_quiz', 'exam_style', 'topic_review'

    questions = Column(JSONB, nullable=False)
    # Structure: [{ "id": 1, "type": "multiple_choice"|"true_false"|"short_answer",
    #               "question": "...", "options": [...], "correct_answer": "...",
    #               "explanation": "...", "topic_tag": "...", "difficulty": "easy"|"medium"|"hard" }]

    question_count = Column(Integer, nullable=False)
    time_limit_minutes = Column(Integer, nullable=True)  # null = untimed
    difficulty_level = Column(String(50), nullable=True)
    source_type = Column(String(50), nullable=False)  # 'document', 'topic', 'study_plan'
    slide_content = Column(Text, nullable=True)  # Preserved document text for study plan generation

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    attempts = relationship("QuizAttempt", backref="quiz", cascade="all, delete-orphan")

    def to_dict(self, include_answers=False):
        questions = self.questions or []
        if not include_answers:
            questions = [{k: v for k, v in q.items() if k not in ('correct_answer', 'explanation')} for q in questions]
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "study_plan_id": str(self.study_plan_id) if self.study_plan_id else None,
            "course_id": str(self.course_id) if self.course_id else None,
            "title": self.title,
            "topic": self.topic,
            "quiz_type": self.quiz_type,
            "questions": questions,
            "question_count": self.question_count,
            "time_limit_minutes": self.time_limit_minutes,
            "difficulty_level": self.difficulty_level,
            "source_type": self.source_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    answers = Column(JSONB, nullable=False)
    score = Column(Numeric(5, 2), nullable=False)
    correct_count = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)

    time_taken_seconds = Column(Integer, nullable=True)
    was_timed = Column(Boolean, default=False)
    timed_out = Column(Boolean, default=False)

    knowledge_gaps = Column(JSONB, nullable=True)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "quiz_id": str(self.quiz_id),
            "user_id": str(self.user_id),
            "answers": self.answers,
            "score": float(self.score) if self.score else 0,
            "correct_count": self.correct_count,
            "total_questions": self.total_questions,
            "time_taken_seconds": self.time_taken_seconds,
            "was_timed": self.was_timed,
            "timed_out": self.timed_out,
            "knowledge_gaps": self.knowledge_gaps,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
