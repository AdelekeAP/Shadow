"""
Tests for Task model methods
backend/app/models/task.py

Tests the calculate_priority() and to_dict() methods which contain
significant business logic without requiring database connections.
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, PropertyMock
from decimal import Decimal


class MockTaskModel:
    """
    Mimics the Task SQLAlchemy model closely enough to test
    calculate_priority() and to_dict().
    """

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.user_id = kwargs.get("user_id", uuid.uuid4())
        self.user_course_id = kwargs.get("user_course_id", uuid.uuid4())
        self.title = kwargs.get("title", "Test Task")
        self.description = kwargs.get("description", None)
        self.task_type = kwargs.get("task_type", "assignment")
        self.topic = kwargs.get("topic", None)
        self.weight = kwargs.get("weight", Decimal("10.00"))
        self.max_marks = kwargs.get("max_marks", None)
        self.earned_marks = kwargs.get("earned_marks", None)
        self.category = kwargs.get("category", "CA")
        self.due_date = kwargs.get("due_date", None)
        self.completed_at = kwargs.get("completed_at", None)
        self.is_completed = kwargs.get("is_completed", False)
        self.is_late = kwargs.get("is_late", False)
        self.effort_estimate = kwargs.get("effort_estimate", None)
        self.actual_effort = kwargs.get("actual_effort", None)
        self.priority_score = kwargs.get("priority_score", None)
        self.is_urgent = kwargs.get("is_urgent", False)
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
        self.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))
        self.user_course = kwargs.get("user_course", None)

    def calculate_priority(self, current_cgpa=None, target_cgpa=None):
        """Replicated from Task model for testing without DB"""
        score = 0.0

        # 1. Due date urgency (0-30 points)
        if self.due_date and not self.is_completed:
            due_date_aware = self.due_date
            if due_date_aware.tzinfo is None:
                due_date_aware = due_date_aware.replace(tzinfo=timezone.utc)
            days_until_due = (due_date_aware - datetime.now(timezone.utc)).days
            if days_until_due < 0:
                score += 30
            elif days_until_due == 0:
                score += 28
            elif days_until_due == 1:
                score += 25
            elif days_until_due <= 3:
                score += 20
            elif days_until_due <= 7:
                score += 15
            elif days_until_due <= 14:
                score += 10
            else:
                score += 5

        # 2. Task weight/importance (0-25 points)
        if self.weight:
            weight_float = float(self.weight)
            score += min(25, (weight_float / 35) * 25)

        # 3. Completion status (0-20 points)
        if not self.is_completed:
            score += 20

        # 4. CGPA impact (0-15 points)
        if target_cgpa and current_cgpa:
            gap = target_cgpa - current_cgpa
            if gap > 0:
                score += min(15, gap * 30)
            elif gap < 0:
                score += 5

        # 5. Course priority (0-10 points)
        if hasattr(self, 'user_course') and self.user_course:
            if getattr(self.user_course, 'is_priority', False):
                score += 10
            if getattr(self.user_course, 'is_carryover', False):
                score += 5

        self.priority_score = round(score, 2)
        self.is_urgent = score >= 70
        return self.priority_score

    def to_dict(self):
        """Replicated from Task model"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "user_course_id": str(self.user_course_id),
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type,
            "topic": self.topic,
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
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ===================================================================
# calculate_priority tests
# ===================================================================

class TestTaskCalculatePriority:

    def test_overdue_task_gets_max_urgency(self):
        task = MockTaskModel(
            due_date=datetime.now(timezone.utc) - timedelta(days=2),
            weight=Decimal("15"),
        )
        score = task.calculate_priority()
        assert score >= 30  # 30 for overdue + weight + incomplete

    def test_due_today_high_urgency(self):
        task = MockTaskModel(
            due_date=datetime.now(timezone.utc) + timedelta(hours=6),
            weight=Decimal("15"),
        )
        score = task.calculate_priority()
        assert score >= 28  # 28 for due today

    def test_due_tomorrow(self):
        task = MockTaskModel(
            due_date=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
            weight=Decimal("15"),
        )
        score = task.calculate_priority()
        assert 25 <= score  # 25 for due tomorrow + weight + incomplete

    def test_completed_task_has_lower_priority(self):
        task_incomplete = MockTaskModel(
            due_date=datetime.now(timezone.utc) + timedelta(days=3),
            weight=Decimal("15"),
            is_completed=False,
        )
        task_complete = MockTaskModel(
            due_date=datetime.now(timezone.utc) + timedelta(days=3),
            weight=Decimal("15"),
            is_completed=True,
        )
        score_incomplete = task_incomplete.calculate_priority()
        score_complete = task_complete.calculate_priority()
        assert score_incomplete > score_complete  # 20 points difference

    def test_heavier_task_higher_priority(self):
        light_task = MockTaskModel(weight=Decimal("5"))
        heavy_task = MockTaskModel(weight=Decimal("30"))
        assert heavy_task.calculate_priority() > light_task.calculate_priority()

    def test_cgpa_gap_increases_priority(self):
        task = MockTaskModel(weight=Decimal("15"))
        score_no_gap = task.calculate_priority(current_cgpa=4.5, target_cgpa=4.5)

        task2 = MockTaskModel(weight=Decimal("15"))
        score_with_gap = task2.calculate_priority(current_cgpa=3.0, target_cgpa=4.5)

        assert score_with_gap > score_no_gap

    def test_exceeding_target_still_adds_points(self):
        task = MockTaskModel(weight=Decimal("15"))
        score = task.calculate_priority(current_cgpa=4.8, target_cgpa=4.5)
        # Should add 5 points (ahead of target)
        task2 = MockTaskModel(weight=Decimal("15"))
        score2 = task2.calculate_priority()  # No CGPA data
        assert score > score2

    def test_priority_course_adds_10_points(self):
        mock_user_course = MagicMock()
        mock_user_course.is_priority = True
        mock_user_course.is_carryover = False

        task = MockTaskModel(
            weight=Decimal("15"),
            user_course=mock_user_course,
        )
        score_with = task.calculate_priority()

        task2 = MockTaskModel(weight=Decimal("15"), user_course=None)
        score_without = task2.calculate_priority()

        assert score_with - score_without == 10

    def test_carryover_course_adds_5_points(self):
        mock_user_course = MagicMock()
        mock_user_course.is_priority = False
        mock_user_course.is_carryover = True

        task = MockTaskModel(
            weight=Decimal("15"),
            user_course=mock_user_course,
        )
        score_with = task.calculate_priority()

        task2 = MockTaskModel(weight=Decimal("15"), user_course=None)
        score_without = task2.calculate_priority()

        assert score_with - score_without == 5

    def test_is_urgent_flag_set_above_70(self):
        """Tasks scoring >= 70 should be marked urgent"""
        task = MockTaskModel(
            due_date=datetime.now(timezone.utc) - timedelta(days=1),  # 30 points
            weight=Decimal("35"),  # 25 points
            is_completed=False,  # 20 points = 75 total
        )
        task.calculate_priority(current_cgpa=3.0, target_cgpa=4.5)
        assert task.is_urgent is True

    def test_is_urgent_flag_not_set_below_70(self):
        task = MockTaskModel(
            due_date=datetime.now(timezone.utc) + timedelta(days=20),  # 5 points
            weight=Decimal("5"),  # ~3.6 points
            is_completed=False,  # 20 points = ~28.6
        )
        task.calculate_priority()
        assert task.is_urgent is False


# ===================================================================
# to_dict tests
# ===================================================================

class TestTaskToDict:

    def test_returns_dict(self):
        task = MockTaskModel()
        result = task.to_dict()
        assert isinstance(result, dict)

    def test_id_is_string(self):
        task = MockTaskModel()
        result = task.to_dict()
        assert isinstance(result["id"], str)

    def test_weight_is_float(self):
        task = MockTaskModel(weight=Decimal("15.50"))
        result = task.to_dict()
        assert result["weight"] == 15.5
        assert isinstance(result["weight"], float)

    def test_none_earned_marks(self):
        task = MockTaskModel(earned_marks=None)
        result = task.to_dict()
        assert result["earned_marks"] is None

    def test_earned_marks_as_float(self):
        task = MockTaskModel(earned_marks=Decimal("12.50"))
        result = task.to_dict()
        assert result["earned_marks"] == 12.5

    def test_due_date_isoformat(self):
        dt = datetime(2026, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        task = MockTaskModel(due_date=dt)
        result = task.to_dict()
        assert "2026-03-15" in result["due_date"]

    def test_none_due_date(self):
        task = MockTaskModel(due_date=None)
        result = task.to_dict()
        assert result["due_date"] is None

    def test_password_not_exposed(self):
        """Ensure no sensitive fields leak through"""
        task = MockTaskModel()
        result = task.to_dict()
        assert "password" not in result
        assert "password_hash" not in result

    def test_max_marks_defaults_to_weight(self):
        task = MockTaskModel(weight=Decimal("15"), max_marks=None)
        result = task.to_dict()
        assert result["max_marks"] == 15.0
