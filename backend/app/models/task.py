"""
Task Model - SQLAlchemy ORM
Tracks assignments, tests, projects, and other academic tasks
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Task(Base):
    """
    Task Model - Represents an academic task (assignment, test, project, etc.)
    Linked to a specific course enrollment and tracks CA/Exam scores
    """
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user_course_id = Column(UUID(as_uuid=True), ForeignKey('user_courses.id', ondelete='CASCADE'), nullable=False)

    # Task details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)  # 'test', 'project', 'participation', 'exam', 'assignment'

    # PAU-specific grading (35/65 split)
    weight = Column(Numeric(5, 2), nullable=False)  # Marks (e.g., 15 for Test 1)
    max_marks = Column(Numeric(5, 2), nullable=True)  # Usually same as weight
    earned_marks = Column(Numeric(5, 2), nullable=True)  # Actual score received
    category = Column(String(10), nullable=False, default='CA')  # 'CA' or 'EXAM'

    # Timing
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False)
    is_late = Column(Boolean, default=False)

    # Effort tracking
    effort_estimate = Column(Integer, nullable=True)  # Minutes
    actual_effort = Column(Integer, nullable=True)  # Minutes (user feedback)

    # Priority
    priority_score = Column(Numeric(5, 2), nullable=True)  # Calculated by system
    is_urgent = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user_course = relationship("UserCourse", backref="tasks")

    def __repr__(self):
        return f"<Task(title={self.title}, type={self.task_type}, weight={self.weight})>"

    def to_dict(self):
        """Convert task to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "user_course_id": str(self.user_course_id),
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "weight": float(self.weight) if self.weight else 0.0,
            "max_marks": float(self.max_marks) if self.max_marks else float(self.weight) if self.weight else 0.0,
            "earned_marks": float(self.earned_marks) if self.earned_marks else None,
            "category": self.category,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_completed": self.is_completed,
            "is_late": self.is_late,
            "effort_estimate": self.effort_estimate,
            "actual_effort": self.actual_effort,
            "priority_score": float(self.priority_score) if self.priority_score else None,
            "is_urgent": self.is_urgent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def calculate_priority(self, current_cgpa: float = None, target_cgpa: float = None):
        """
        Calculate task priority score based on multiple factors
        Returns a score from 0-100 (higher = more urgent)

        Factors:
        1. Due date urgency (30 points)
        2. Task weight/importance (25 points)
        3. Completion status (20 points)
        4. CGPA impact (15 points)
        5. Course priority (10 points)
        """
        from datetime import datetime, timezone

        score = 0.0

        # 1. Due date urgency (0-30 points)
        if self.due_date and not self.is_completed:
            # Make due_date timezone-aware if it isn't already
            due_date_aware = self.due_date
            if due_date_aware.tzinfo is None:
                due_date_aware = due_date_aware.replace(tzinfo=timezone.utc)
            days_until_due = (due_date_aware - datetime.now(timezone.utc)).days
            if days_until_due < 0:
                score += 30  # Overdue
            elif days_until_due == 0:
                score += 28  # Due today
            elif days_until_due == 1:
                score += 25  # Due tomorrow
            elif days_until_due <= 3:
                score += 20  # Due this week
            elif days_until_due <= 7:
                score += 15  # Due next week
            elif days_until_due <= 14:
                score += 10  # Due in 2 weeks
            else:
                score += 5   # Due later

        # 2. Task weight/importance (0-25 points)
        if self.weight:
            weight_float = float(self.weight)
            # Normalize to 0-25 scale (assuming max weight is 35)
            score += min(25, (weight_float / 35) * 25)

        # 3. Completion status (0-20 points)
        if not self.is_completed:
            score += 20

        # 4. CGPA impact (0-15 points)
        if target_cgpa and current_cgpa:
            gap = target_cgpa - current_cgpa
            if gap > 0:
                # Behind target - prioritize more
                score += min(15, gap * 30)
            elif gap < 0:
                # Ahead of target - still important but less urgent
                score += 5

        # 5. Course priority (0-10 points)
        if hasattr(self, 'user_course') and self.user_course:
            if self.user_course.is_priority:
                score += 10
            if self.user_course.is_carryover:
                score += 5

        self.priority_score = round(score, 2)
        self.is_urgent = score >= 70  # Mark as urgent if score is high

        return self.priority_score
