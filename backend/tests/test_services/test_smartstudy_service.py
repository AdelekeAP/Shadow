"""
Tests for SmartStudy Service
backend/app/services/smartstudy_service.py

Tests cover: build_system_prompt (pure), load_student_context (DB),
check_smartstudy_triggers (mock context), get_suggested_prompts (mock context),
chat_with_smartstudy (mock OpenAI).

NOTE: Because the test suite uses SQLite (not PostgreSQL), UUID columns require
actual uuid.UUID objects rather than plain strings. We pass UUID objects for all
function arguments that reach the DB layer.
"""
import uuid
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.services.smartstudy_service import (
    build_system_prompt,
    load_student_context,
    check_smartstudy_triggers,
    get_suggested_prompts,
    chat_with_smartstudy,
)


# ---------------------------------------------------------------------------
# Override test_course from conftest (the shared one passes an invalid
# ``semester`` keyword argument to Course).
# ---------------------------------------------------------------------------

@pytest.fixture
def test_course(db_session):
    """Create a test course without the invalid 'semester' kwarg."""
    from app.models.course import Course
    course = Course(code="CSC401", title="Software Engineering", credits=3, level="400L")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


# ---------------------------------------------------------------------------
# build_system_prompt  (pure function -- no DB required)
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:

    def test_basic_context_contains_name(self):
        context = {
            "student_info": {
                "name": "Alice",
                "current_cgpa": 3.8,
                "target_cgpa": 4.5,
                "learning_style": "visual",
                "entry_level": "400L",
            },
            "courses": [],
            "recent_moods": [],
            "cgpa_gap": 0.7,
        }
        prompt = build_system_prompt(context)
        assert "Alice" in prompt
        assert "3.8" in prompt

    def test_basic_context_contains_cgpa_info(self):
        context = {
            "student_info": {
                "name": "Bob",
                "current_cgpa": 4.0,
                "target_cgpa": 4.5,
                "learning_style": None,
                "entry_level": "300L",
            },
            "courses": [],
            "recent_moods": [],
            "cgpa_gap": 0.5,
        }
        prompt = build_system_prompt(context)
        assert "4.0" in prompt
        assert "4.5" in prompt

    def test_context_with_courses_contains_codes(self):
        context = {
            "student_info": {"name": "Student"},
            "courses": [
                {
                    "code": "CSC401",
                    "title": "Software Engineering",
                    "ca_score": 28,
                    "predicted_grade": "A",
                },
                {
                    "code": "MTH201",
                    "title": "Calculus II",
                    "ca_score": 20,
                    "predicted_grade": "B",
                },
            ],
            "recent_moods": [],
            "cgpa_gap": None,
        }
        prompt = build_system_prompt(context)
        assert "CSC401" in prompt
        assert "MTH201" in prompt

    def test_context_with_moods_contains_mood_info(self):
        context = {
            "student_info": {"name": "Student"},
            "courses": [],
            "recent_moods": [
                {
                    "mood_type": "stressed",
                    "energy_level": 2,
                    "primary_emotion": "anxiety",
                    "note": None,
                    "logged_at": datetime.now().isoformat(),
                }
            ],
            "cgpa_gap": None,
        }
        prompt = build_system_prompt(context)
        assert "stressed" in prompt
        assert "anxiety" in prompt

    def test_empty_context_returns_valid_string(self):
        prompt = build_system_prompt({})
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should contain the default role description even without student data
        assert "SmartStudy" in prompt

    def test_context_with_cgpa_gap_contains_gap(self):
        context = {
            "student_info": {
                "name": "Test",
                "current_cgpa": 3.0,
                "target_cgpa": 4.5,
            },
            "courses": [],
            "recent_moods": [],
            "cgpa_gap": 1.5,
        }
        prompt = build_system_prompt(context)
        assert "1.5" in prompt


# ---------------------------------------------------------------------------
# load_student_context  (needs DB fixtures)
# ---------------------------------------------------------------------------

class TestLoadStudentContext:

    def test_user_not_found_returns_empty_dict(self, db_session):
        result = load_student_context(db_session, uuid.uuid4())
        assert result == {}

    def test_user_with_no_courses_tasks_moods(self, db_session, test_user):
        result = load_student_context(db_session, test_user.id)
        assert "student_info" in result
        assert result["student_info"]["name"] == "Test Service User"
        assert result["courses"] == []
        assert result["recent_tasks"] == []
        assert result["recent_moods"] == []

    def test_user_with_enrolled_course(self, db_session, test_user, test_course):
        from app.models.course import UserCourse

        uc = UserCourse(
            user_id=test_user.id,
            course_id=test_course.id,
            ca_score=25,
            predicted_letter_grade="A",
            predicted_score=85,
            completion_rate=70,
        )
        db_session.add(uc)
        db_session.commit()

        result = load_student_context(db_session, test_user.id)
        assert len(result["courses"]) == 1
        assert result["courses"][0]["code"] == "CSC401"
        assert result["courses"][0]["ca_score"] == 25.0


# ---------------------------------------------------------------------------
# check_smartstudy_triggers  (mock load_student_context)
#
# NOTE: check_smartstudy_triggers also does a raw DB query on
#       ChatConversation, so we pass the UUID object (not a string)
#       to keep SQLite happy.
# ---------------------------------------------------------------------------

class TestCheckSmartStudyTriggers:

    @patch("app.services.smartstudy_service.load_student_context")
    def test_no_triggers(self, mock_load, db_session, test_user):
        # cgpa_gap is 0 (falsy), so TRIGGER 8 (new_user) won't fire even
        # though there are 0 chat conversations.
        mock_load.return_value = {
            "student_info": {"name": "Test", "current_cgpa": 4.0, "target_cgpa": 4.5},
            "courses": [],
            "recent_tasks": [],
            "recent_moods": [],
            "cgpa_gap": 0,
        }
        result = check_smartstudy_triggers(db_session, test_user.id)
        assert result["should_trigger"] is False
        assert result["urgency"] == "none"

    @patch("app.services.smartstudy_service.load_student_context")
    def test_overdue_tasks_trigger(self, mock_load, db_session, test_user):
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        mock_load.return_value = {
            "student_info": {},
            "courses": [],
            "recent_tasks": [
                {"title": "T1", "due_date": yesterday, "is_completed": False, "is_late": False},
                {"title": "T2", "due_date": yesterday, "is_completed": False, "is_late": False},
            ],
            "recent_moods": [],
            "cgpa_gap": 0,
        }
        result = check_smartstudy_triggers(db_session, test_user.id)
        assert result["should_trigger"] is True
        assert any(t["type"] == "overdue_tasks" for t in result["triggers"])
        assert result["urgency"] == "high"

    @patch("app.services.smartstudy_service.load_student_context")
    def test_cgpa_gap_critical(self, mock_load, db_session, test_user):
        mock_load.return_value = {
            "student_info": {"target_cgpa": 4.5},
            "courses": [],
            "recent_tasks": [],
            "recent_moods": [],
            "cgpa_gap": 0.8,
        }
        result = check_smartstudy_triggers(db_session, test_user.id)
        assert result["should_trigger"] is True
        assert any(t["type"] == "cgpa_gap" for t in result["triggers"])
        assert result["urgency"] == "critical"

    @patch("app.services.smartstudy_service.load_student_context")
    def test_negative_mood_trigger(self, mock_load, db_session, test_user):
        mock_load.return_value = {
            "student_info": {},
            "courses": [],
            "recent_tasks": [],
            "recent_moods": [
                {"primary_emotion": "anxiety", "energy_level": 3},
                {"primary_emotion": "sadness", "energy_level": 2},
                {"primary_emotion": "fear", "energy_level": 1},
            ],
            "cgpa_gap": 0,
        }
        result = check_smartstudy_triggers(db_session, test_user.id)
        assert result["should_trigger"] is True
        assert any(t["type"] == "negative_mood" for t in result["triggers"])

    @patch("app.services.smartstudy_service.load_student_context")
    def test_low_energy_trigger(self, mock_load, db_session, test_user):
        mock_load.return_value = {
            "student_info": {},
            "courses": [],
            "recent_tasks": [],
            "recent_moods": [
                {"primary_emotion": "joy", "energy_level": 1},
                {"primary_emotion": "joy", "energy_level": 2},
                {"primary_emotion": "joy", "energy_level": 1},
            ],
            "cgpa_gap": 0,
        }
        result = check_smartstudy_triggers(db_session, test_user.id)
        assert result["should_trigger"] is True
        assert any(t["type"] == "low_energy" for t in result["triggers"])

    @patch("app.services.smartstudy_service.load_student_context")
    def test_task_overload_trigger(self, mock_load, db_session, test_user):
        incomplete_tasks = [
            {"title": f"Task{i}", "due_date": None, "is_completed": False, "is_late": False}
            for i in range(10)
        ]
        mock_load.return_value = {
            "student_info": {},
            "courses": [],
            "recent_tasks": incomplete_tasks,
            "recent_moods": [],
            "cgpa_gap": 0,
        }
        result = check_smartstudy_triggers(db_session, test_user.id)
        assert result["should_trigger"] is True
        assert any(t["type"] == "task_overload" for t in result["triggers"])


# ---------------------------------------------------------------------------
# get_suggested_prompts  (mock load_student_context)
# ---------------------------------------------------------------------------

class TestGetSuggestedPrompts:

    @patch("app.services.smartstudy_service.load_student_context")
    def test_no_special_context_returns_general_prompts(self, mock_load, db_session, test_user):
        mock_load.return_value = {
            "student_info": {},
            "courses": [],
            "recent_tasks": [],
            "recent_moods": [],
            "cgpa_gap": 0,
        }
        prompts = get_suggested_prompts(db_session, str(test_user.id))
        assert isinstance(prompts, list)
        assert len(prompts) >= 1
        # Should have the general prompts
        categories = [p["category"] for p in prompts]
        assert "clarification" in categories or "planning" in categories

    @patch("app.services.smartstudy_service.load_student_context")
    def test_cgpa_gap_prompt(self, mock_load, db_session, test_user):
        mock_load.return_value = {
            "student_info": {},
            "courses": [],
            "recent_tasks": [],
            "recent_moods": [],
            "cgpa_gap": 0.5,
        }
        prompts = get_suggested_prompts(db_session, str(test_user.id))
        prompt_texts = [p["prompt"] for p in prompts]
        assert any("CGPA" in text or "catch up" in text for text in prompt_texts)

    @patch("app.services.smartstudy_service.load_student_context")
    def test_negative_mood_prompt(self, mock_load, db_session, test_user):
        mock_load.return_value = {
            "student_info": {},
            "courses": [],
            "recent_tasks": [],
            "recent_moods": [
                {"primary_emotion": "anxiety", "energy_level": 2},
            ],
            "cgpa_gap": None,
        }
        prompts = get_suggested_prompts(db_session, str(test_user.id))
        prompt_texts = [p["prompt"] for p in prompts]
        assert any("overwhelmed" in text.lower() for text in prompt_texts)

    @patch("app.services.smartstudy_service.load_student_context")
    def test_max_five_prompts(self, mock_load, db_session, test_user):
        # Craft context that would trigger extra prompts
        mock_load.return_value = {
            "student_info": {},
            "courses": [],
            "recent_tasks": [
                {"title": f"T{i}", "is_completed": False} for i in range(10)
            ],
            "recent_moods": [
                {"primary_emotion": "anxiety", "energy_level": 1},
            ],
            "cgpa_gap": 1.0,
        }
        prompts = get_suggested_prompts(db_session, str(test_user.id))
        assert len(prompts) <= 5


# ---------------------------------------------------------------------------
# chat_with_smartstudy  (mock OpenAI client)
# ---------------------------------------------------------------------------

class TestChatWithSmartStudy:

    @patch("app.services.smartstudy_service.call_with_retry")
    async def test_no_openai_client_returns_error(self, mock_call, db_session, test_user):
        from app.services.openai_client import OpenAIError, OpenAIErrorType
        mock_call.side_effect = OpenAIError(
            error_type=OpenAIErrorType.auth_error,
            user_message="OpenAI client not initialized. Please check OPENAI_API_KEY.",
        )
        result = await chat_with_smartstudy(db_session, test_user.id, "Hello")
        assert "error" in result
        assert "OpenAI" in result["error"]

    @patch("app.services.smartstudy_service.load_student_context")
    @patch("app.services.smartstudy_service.call_with_retry")
    async def test_successful_chat(self, mock_call, mock_load, db_session, test_user):
        mock_load.return_value = {
            "student_info": {"name": "Test"},
            "courses": [],
            "recent_tasks": [],
            "recent_moods": [],
            "cgpa_gap": None,
        }

        # Build the mock response (what call_with_retry returns)
        mock_message = MagicMock()
        mock_message.content = "Hello! How can I help you study today?"

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_usage = MagicMock()
        mock_usage.total_tokens = 150

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_call.return_value = mock_response

        result = await chat_with_smartstudy(db_session, test_user.id, "Hi there")

        assert "error" not in result
        assert "conversation_id" in result
        assert result["ai_response"] == "Hello! How can I help you study today?"
        assert result["tokens_used"] == 150
