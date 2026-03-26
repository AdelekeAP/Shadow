"""
Tests for StudyCardsService, the study-cards endpoint, and the validate-step endpoint.

Covers:
  - GPT-based study card generation (flashcards, key concepts, comprehension)
  - Fallback on GPT failure / unparseable JSON
  - Field validation and sanitization
  - POST /study-cards endpoint auth, ownership, 404, and success paths
  - POST /exercises/validate-step correct, incorrect, GPT failure, auth
"""
import json
import uuid
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from app.services.study_cards_service import (
    StudyCardsService,
    get_study_cards_service,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_openai_response(content: str) -> MagicMock:
    """Create a mock OpenAI ChatCompletion response."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    resp.model = "gpt-5.4"
    return resp


VALID_STUDY_CARDS_JSON = json.dumps({
    "flashcards": [
        {"front": "What is a stack?", "back": "LIFO data structure", "category": "definition"},
        {"front": "Push operation", "back": "Adds element to top", "category": "concept"},
    ],
    "key_concepts": [
        {"concept": "LIFO Principle", "explanation": "Last in, first out ordering.", "importance": "critical"},
        {"concept": "Stack Overflow", "explanation": "When stack exceeds capacity.", "importance": "important"},
    ],
    "comprehension_questions": [
        {"question": "Why use a stack for undo operations?", "hint": "Think about ordering.", "sample_answer": "Because undo reverses the most recent action first."},
    ],
})


# ===================================================================
# TestStudyCardsService  (unit tests)
# ===================================================================

class TestStudyCardsService:

    @pytest.fixture(autouse=True)
    def service(self):
        self.svc = StudyCardsService()

    # 1. Success path
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_success(self, mock_retry):
        """Valid JSON from GPT -> dict with all three sections."""
        mock_retry.return_value = _mock_openai_response(VALID_STUDY_CARDS_JSON)

        result = await self.svc.generate(
            topic="Data Structures",
            activity_title="Learn Stacks",
            activity_description="Understand LIFO",
        )

        assert "flashcards" in result
        assert "key_concepts" in result
        assert "comprehension_questions" in result
        assert len(result["flashcards"]) == 2
        assert len(result["key_concepts"]) == 2
        assert len(result["comprehension_questions"]) == 1
        assert result["flashcards"][0]["category"] == "definition"
        assert result["key_concepts"][0]["importance"] == "critical"

    # 2. Slide content in prompt
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_with_slide_content(self, mock_retry):
        """When slide_content is provided, prompt includes it."""
        mock_retry.return_value = _mock_openai_response(VALID_STUDY_CARDS_JSON)

        await self.svc.generate(
            topic="BST",
            activity_title="BST Intro",
            activity_description="Learn BST",
            slide_content="Slide 1: Binary tree definition",
        )

        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "ACTUAL SLIDE/LECTURE CONTENT" in user_msg["content"]

    # 3. No slide content
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_without_slides(self, mock_retry):
        """Without slide_content, uses the no-slides fallback path."""
        mock_retry.return_value = _mock_openai_response(VALID_STUDY_CARDS_JSON)

        await self.svc.generate(
            topic="Sorting",
            activity_title="QuickSort",
            activity_description="Divide and conquer",
        )

        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "No slides were uploaded" in user_msg["content"]

    # 4. Invalid JSON -> fallback
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_invalid_json_fallback(self, mock_retry):
        """GPT returns garbage -> fallback study cards."""
        mock_retry.return_value = _mock_openai_response("Not JSON at all!")

        result = await self.svc.generate(
            topic="Recursion",
            activity_title="Learn Recursion",
            activity_description="Base case",
        )

        assert len(result["flashcards"]) == 3  # fallback has 3
        assert "Recursion" in result["flashcards"][0]["front"]

    # 5. Non-dict -> fallback
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_non_dict_fallback(self, mock_retry):
        """GPT returns a list instead of dict -> fallback."""
        mock_retry.return_value = _mock_openai_response(json.dumps([1, 2, 3]))

        result = await self.svc.generate(
            topic="Graphs",
            activity_title="BFS",
            activity_description="Breadth-first",
        )

        assert "flashcards" in result
        assert len(result["flashcards"]) == 3  # fallback

    # 6. Invalid category -> defaults to "concept"
    @patch("app.services.openai_client.call_with_retry")
    async def test_validate_flashcard_invalid_category(self, mock_retry):
        """Flashcard with invalid category gets defaulted to 'concept'."""
        bad_cards = json.dumps({
            "flashcards": [
                {"front": "Q1", "back": "A1", "category": "invalid_cat"},
            ],
            "key_concepts": [],
            "comprehension_questions": [],
        })
        mock_retry.return_value = _mock_openai_response(bad_cards)

        result = await self.svc.generate(topic="Test", activity_title="T", activity_description="D")

        assert result["flashcards"][0]["category"] == "concept"

    # 7. Direct fallback test
    def test_fallback_content(self):
        """_fallback returns 3 flashcards, 1 concept, 1 question with topic in them."""
        result = self.svc._fallback("Machine Learning")

        assert len(result["flashcards"]) == 3
        assert len(result["key_concepts"]) == 1
        assert len(result["comprehension_questions"]) == 1
        assert "Machine Learning" in result["flashcards"][0]["front"]
        assert result["key_concepts"][0]["importance"] == "critical"


# ===================================================================
# TestStudyCardsEndpoint  (integration tests)
# ===================================================================

class TestStudyCardsEndpoint:

    @pytest.fixture
    def integration_client(self):
        from tests.conftest import _engine, _TestingSessionLocal, _override_get_db
        from app.database import Base, get_db
        from app.main import app as fastapi_app
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=_engine)
        session = _TestingSessionLocal()

        fastapi_app.dependency_overrides[get_db] = _override_get_db
        from fastapi.testclient import TestClient
        with TestClient(fastapi_app) as c:
            yield {"client": c, "db": session}

        session.close()
        fastapi_app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=_engine)

    def _create_test_data(self, session):
        from app.models.user import User
        from app.models.smartstudy import StudyPlan, StudyPlanResource
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = User(
            id=uuid.uuid4(),
            email=f"reading_{uuid.uuid4().hex[:6]}@pau.edu.ng",
            password_hash=pwd_context.hash("TestPass123!"),
            full_name="Reading Test User",
            university_id=f"PAU/2022/{uuid.uuid4().hex[:3]}",
            entry_level="400L",
            target_cgpa=4.5,
            current_cgpa=3.5,
        )
        session.add(user)
        session.flush()

        plan = StudyPlan(
            id=uuid.uuid4(),
            user_id=user.id,
            topic="Data Structures",
            plan_data={
                "title": "Master Data Structures",
                "days": [{"day_number": 1, "activities": [{"difficulty": "medium"}]}],
                "_slide_content": "Slide content about stacks",
            },
            duration_days=7,
            start_date=date.today(),
            is_active=True,
            completion_percentage=0,
            completed_days=[],
        )
        session.add(plan)
        session.flush()

        resource = StudyPlanResource(
            id=uuid.uuid4(),
            study_plan_id=plan.id,
            resource_type="article",
            resource_title="Stacks Article",
            resource_description="Introduction to stacks",
            day_number=1,
            order_in_day=0,
            clicked=False,
            completed=False,
        )
        session.add(resource)
        session.commit()

        return {"user": user, "plan": plan, "resource": resource}

    def _auth_header(self, user):
        from app.utils.auth import create_access_token
        token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    # 8. Study cards endpoint success
    @patch("app.services.openai_client.call_with_retry")
    def test_study_cards_endpoint_success(self, mock_retry, integration_client):
        mock_retry.return_value = _mock_openai_response(VALID_STUDY_CARDS_JSON)

        import app.services.study_cards_service as sc_mod
        sc_mod._study_cards_service = None

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/study-cards",
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert "flashcards" in body
        assert "key_concepts" in body
        assert "comprehension_questions" in body
        assert body["plan_id"] == str(data["plan"].id)

        sc_mod._study_cards_service = None

    # 9. Unauthenticated
    def test_study_cards_unauthenticated(self, integration_client):
        c = integration_client["client"]
        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/study-cards"
        )
        assert resp.status_code == 401

    # 10. Plan not found
    def test_study_cards_plan_not_found(self, integration_client):
        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/study-cards",
            headers=headers,
        )
        assert resp.status_code == 404


# ===================================================================
# TestValidateStep  (unit + integration tests)
# ===================================================================

class TestValidateStep:

    @pytest.fixture
    def integration_client(self):
        from tests.conftest import _engine, _TestingSessionLocal, _override_get_db
        from app.database import Base, get_db
        from app.main import app as fastapi_app
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=_engine)
        session = _TestingSessionLocal()

        fastapi_app.dependency_overrides[get_db] = _override_get_db
        from fastapi.testclient import TestClient
        with TestClient(fastapi_app) as c:
            yield {"client": c, "db": session}

        session.close()
        fastapi_app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=_engine)

    def _create_test_data(self, session):
        from app.models.user import User
        from app.models.smartstudy import StudyPlan, StudyPlanResource
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = User(
            id=uuid.uuid4(),
            email=f"guided_{uuid.uuid4().hex[:6]}@pau.edu.ng",
            password_hash=pwd_context.hash("TestPass123!"),
            full_name="Guided Solver User",
            university_id=f"PAU/2022/{uuid.uuid4().hex[:3]}",
            entry_level="400L",
            target_cgpa=4.5,
            current_cgpa=3.5,
        )
        session.add(user)
        session.flush()

        plan = StudyPlan(
            id=uuid.uuid4(),
            user_id=user.id,
            topic="Algorithms",
            plan_data={"title": "Algo Plan", "days": [{"day_number": 1, "activities": []}]},
            duration_days=7,
            start_date=date.today(),
            is_active=True,
            completion_percentage=0,
            completed_days=[],
        )
        session.add(plan)
        session.flush()

        resource = StudyPlanResource(
            id=uuid.uuid4(),
            study_plan_id=plan.id,
            resource_type="practice",
            resource_title="Binary Search Practice",
            day_number=1,
            order_in_day=0,
            clicked=False,
            completed=False,
        )
        session.add(resource)
        session.commit()

        return {"user": user, "plan": plan, "resource": resource}

    def _auth_header(self, user):
        from app.utils.auth import create_access_token
        token = create_access_token(data={"sub": user.email, "user_id": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    # 11. Correct answer
    @patch("app.services.openai_client.call_with_retry")
    def test_validate_step_correct(self, mock_retry, integration_client):
        mock_retry.return_value = _mock_openai_response(json.dumps({
            "correct": True,
            "feedback": "Great work! Your implementation is correct.",
            "hint": None,
        }))

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/exercises/validate-step",
            headers=headers,
            json={
                "exercise_title": "Implement Binary Search",
                "step_text": "Write a function that takes a sorted array",
                "student_answer": "def binary_search(arr, target): ...",
                "topic": "Binary Search",
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["correct"] is True
        assert "feedback" in body

    # 12. Incorrect answer with hint
    @patch("app.services.openai_client.call_with_retry")
    def test_validate_step_incorrect(self, mock_retry, integration_client):
        mock_retry.return_value = _mock_openai_response(json.dumps({
            "correct": False,
            "feedback": "Not quite — you're using linear search instead.",
            "hint": "Try dividing the array in half each time.",
        }))

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/exercises/validate-step",
            headers=headers,
            json={
                "exercise_title": "Implement Binary Search",
                "step_text": "Implement the comparison logic",
                "student_answer": "for i in range(len(arr)): if arr[i] == target: return i",
                "topic": "Binary Search",
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["correct"] is False
        assert body["hint"] is not None

    # 13. GPT failure -> graceful fallback
    @patch("app.services.openai_client.call_with_retry")
    def test_validate_step_gpt_failure(self, mock_retry, integration_client):
        mock_retry.side_effect = Exception("OpenAI timeout")

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/exercises/validate-step",
            headers=headers,
            json={
                "exercise_title": "Test",
                "step_text": "Do something",
                "student_answer": "my answer",
                "topic": "Test",
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["correct"] is None
        assert "mark this step yourself" in body["feedback"].lower()

    # 14. Unauthenticated
    def test_validate_step_unauthenticated(self, integration_client):
        c = integration_client["client"]
        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/exercises/validate-step",
            json={"student_answer": "test"},
        )
        assert resp.status_code == 401
