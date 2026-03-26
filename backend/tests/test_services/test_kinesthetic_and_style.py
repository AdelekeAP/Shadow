"""
Tests for PracticeExerciseService, analyze_content_type, and the
practice-exercises endpoint.

Covers:
  - GPT-based exercise generation with call_with_retry
  - Fallback exercises on GPT failure / unparseable JSON
  - Field validation and sanitization (minutes clamping, missing fields)
  - Content-type analysis (math, code, visual, conceptual)
  - Learning-style recommendations and warnings
  - POST /exercises endpoint auth, ownership, 404, and success paths
"""
import json
import uuid
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from app.services.practice_exercise_service import (
    PracticeExerciseService,
    get_practice_exercise_service,
)
from app.services.document_processor import analyze_content_type


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_openai_response(content: str) -> MagicMock:
    """Create a mock OpenAI ChatCompletion response."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    resp.model = "gpt-4o-mini"
    return resp


VALID_EXERCISES_JSON = json.dumps([
    {
        "title": "Implement a Stack",
        "instructions": "Build a stack data structure from scratch.",
        "steps": ["Open editor", "Create class", "Add push/pop", "Test it"],
        "difficulty": "medium",
        "estimated_minutes": 20,
        "exercise_type": "code_challenge",
        "success_criteria": "All operations work correctly",
    },
    {
        "title": "Draw a Linked List",
        "instructions": "Diagram a singly linked list on paper.",
        "steps": ["Draw nodes", "Add pointers", "Trace traversal"],
        "difficulty": "easy",
        "estimated_minutes": 10,
        "exercise_type": "diagram_drawing",
        "success_criteria": "Diagram matches the expected structure",
    },
])


# ===================================================================
# TestPracticeExerciseService  (unit tests)
# ===================================================================

class TestPracticeExerciseService:

    @pytest.fixture(autouse=True)
    def service(self):
        self.svc = PracticeExerciseService()

    # 1. Success path
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_exercises_success(self, mock_retry):
        """Valid JSON array from GPT -> list of exercise dicts with correct fields."""
        mock_retry.return_value = _mock_openai_response(VALID_EXERCISES_JSON)

        result = await self.svc.generate_exercises(
            topic="Data Structures",
            activity_title="Learn Stacks",
            activity_description="Understand LIFO",
        )

        assert isinstance(result, list)
        assert len(result) == 2
        for ex in result:
            assert "title" in ex
            assert "instructions" in ex
            assert "steps" in ex
            assert isinstance(ex["steps"], list)
            assert "difficulty" in ex
            assert "estimated_minutes" in ex
            assert "exercise_type" in ex
            assert "success_criteria" in ex

    # 2. Slide content included in prompt
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_exercises_with_slide_content(self, mock_retry):
        """When slide_content is provided, the prompt should contain 'ACTUAL SLIDE/LECTURE CONTENT'."""
        mock_retry.return_value = _mock_openai_response(VALID_EXERCISES_JSON)

        await self.svc.generate_exercises(
            topic="Binary Trees",
            activity_title="BST Intro",
            activity_description="Learn BST properties",
            slide_content="Slide 1: Binary tree definition\nSlide 2: Traversal",
        )

        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "ACTUAL SLIDE/LECTURE CONTENT" in user_msg["content"]
        assert "Slide 1: Binary tree definition" in user_msg["content"]

    # 3. No slide content -> no-slides path
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_exercises_without_slides(self, mock_retry):
        """Without slide_content, the prompt should use the no-slides fallback."""
        mock_retry.return_value = _mock_openai_response(VALID_EXERCISES_JSON)

        await self.svc.generate_exercises(
            topic="Sorting Algorithms",
            activity_title="Learn QuickSort",
            activity_description="Understand divide-and-conquer",
        )

        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "ACTUAL SLIDE/LECTURE CONTENT" not in user_msg["content"]
        assert "No slides were uploaded" in user_msg["content"]

    # 4. Invalid JSON -> fallback
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_exercises_invalid_json_fallback(self, mock_retry):
        """GPT returns garbage -> fallback exercises (2 exercises with known titles)."""
        mock_retry.return_value = _mock_openai_response("This is not valid JSON at all!")

        result = await self.svc.generate_exercises(
            topic="Recursion",
            activity_title="Learn Recursion",
            activity_description="Base case + recursive case",
        )

        assert isinstance(result, list)
        assert len(result) == 2
        assert "Explain Recursion in Your Own Words" in result[0]["title"]
        assert "Apply Recursion to a Real Problem" in result[1]["title"]

    # 5. Non-list (dict) -> fallback
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_exercises_non_list_fallback(self, mock_retry):
        """GPT returns a dict instead of a list -> fallback exercises."""
        mock_retry.return_value = _mock_openai_response(json.dumps({"title": "oops"}))

        result = await self.svc.generate_exercises(
            topic="Graphs",
            activity_title="Learn BFS",
            activity_description="Breadth-first search",
        )

        assert isinstance(result, list)
        assert len(result) == 2
        assert "Graphs" in result[0]["title"]

    # 6. Missing fields -> sanitized defaults
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_exercises_validates_fields(self, mock_retry):
        """Exercises with missing fields get sanitized defaults."""
        partial = json.dumps([
            {"title": "Minimal Exercise"},  # All other fields missing
            {"no_title": "should be skipped"},  # Missing title -> skipped
        ])
        mock_retry.return_value = _mock_openai_response(partial)

        result = await self.svc.generate_exercises(
            topic="Testing",
            activity_title="Write Tests",
            activity_description="Unit testing basics",
            difficulty="hard",
        )

        assert len(result) == 1
        ex = result[0]
        assert ex["title"] == "Minimal Exercise"
        assert ex["instructions"] == ""
        assert ex["steps"] == []
        # Missing difficulty falls back to the passed-in difficulty param
        assert ex["difficulty"] == "hard"
        assert ex["estimated_minutes"] == 15  # default
        assert ex["exercise_type"] == "worked_example"  # default
        assert ex["success_criteria"] == ""

    # 7. estimated_minutes clamped to 5-60
    @patch("app.services.openai_client.call_with_retry")
    async def test_generate_exercises_clamps_minutes(self, mock_retry):
        """estimated_minutes outside 5-60 range gets clamped."""
        exercises_json = json.dumps([
            {
                "title": "Too Short",
                "instructions": "Quick exercise",
                "steps": ["Do it"],
                "difficulty": "easy",
                "estimated_minutes": 1,  # Below minimum (5)
                "exercise_type": "worked_example",
                "success_criteria": "Done",
            },
            {
                "title": "Too Long",
                "instructions": "Marathon exercise",
                "steps": ["Start", "Continue", "Finish"],
                "difficulty": "hard",
                "estimated_minutes": 120,  # Above maximum (60)
                "exercise_type": "build_project",
                "success_criteria": "Completed",
            },
        ])
        mock_retry.return_value = _mock_openai_response(exercises_json)

        result = await self.svc.generate_exercises(
            topic="Clamping",
            activity_title="Test Clamp",
            activity_description="Verify clamp behavior",
        )

        assert result[0]["estimated_minutes"] == 5   # clamped up from 1
        assert result[1]["estimated_minutes"] == 60   # clamped down from 120

    # 8. Direct test of _fallback_exercises
    def test_fallback_exercises_content(self):
        """_fallback_exercises returns 2 exercises with topic in their titles."""
        result = self.svc._fallback_exercises("Machine Learning", "Intro to ML", "medium")

        assert isinstance(result, list)
        assert len(result) == 2
        assert "Machine Learning" in result[0]["title"]
        assert "Machine Learning" in result[1]["title"]
        assert result[0]["exercise_type"] == "explain_aloud"
        assert result[1]["exercise_type"] == "worked_example"
        assert result[1]["difficulty"] == "medium"
        # Verify structure completeness
        for ex in result:
            assert "steps" in ex
            assert isinstance(ex["steps"], list)
            assert len(ex["steps"]) >= 3


# ===================================================================
# TestContentAnalysis  (unit tests)
# ===================================================================

class TestContentAnalysis:

    # 9. Empty text
    def test_analyze_empty_text(self):
        """Empty string -> general content type, all styles recommended, no warnings."""
        result = analyze_content_type("")

        assert result["content_type"] == "general"
        assert result["math_density"] == 0.0
        assert result["code_density"] == 0.0
        assert result["visual_mentions"] == 0.0
        assert set(result["recommended_styles"]) == {"visual", "audio", "reading", "kinesthetic"}
        assert result["style_warnings"] == {}

    # 10. Mathematical content
    def test_analyze_mathematical_content(self):
        """Text with math terms, symbols, Greek letters -> mathematical, audio warning."""
        math_text = """
        Theorem 1: The integral of a polynomial function can be computed using
        the power rule. Consider the equation f(x) = x^2 + 3x + 5.
        The derivative is given by f'(x) = 2x + 3.
        Proof: By the fundamental theorem of calculus, the integral from a to b
        equals F(b) - F(a). Using the formula for eigenvalue decomposition,
        we can express the matrix as A = PDP^(-1).
        The determinant of the matrix is given by det(A) = ad - bc.
        Consider the polynomial equation with logarithm and exponential terms.
        The vector space has dimension n and the proof follows from the lemma.
        """ * 3  # Repeat to ensure enough density

        result = analyze_content_type(math_text)

        assert result["content_type"] == "mathematical"
        assert result["math_density"] > 0.0
        assert "audio" in result["style_warnings"]

    # 11. Programming content
    def test_analyze_programming_content(self):
        """Text with code keywords -> programming, audio and reading warnings."""
        code_text = """
        def binary_search(arr, target):
            left = 0
            right = len(arr) - 1
            while left <= right:
                mid = (left + right) // 2
                if arr[mid] == target:
                    return mid
                elif arr[mid] < target:
                    left = mid + 1
                else:
                    right = mid - 1
            return -1

        class TreeNode:
            def __init__(self, val):
                self.val = val
                self.left = None
                self.right = None

        def inorder_traversal(root):
            if root is None:
                return []
            return inorder_traversal(root.left) + [root.val] + inorder_traversal(root.right)

        for i in range(10):
            print(binary_search([1,2,3,4,5,6,7,8,9,10], i))

        import collections
        from typing import List

        class Solution:
            def solve(self, nums: List[int]) -> bool:
                return True
        """ * 3

        result = analyze_content_type(code_text)

        assert result["content_type"] == "programming"
        assert result["code_density"] > 0.0
        assert "audio" in result["style_warnings"]
        assert "reading" in result["style_warnings"]

    # 12. Visual-heavy content
    def test_analyze_visual_heavy_content(self):
        """Text referencing diagrams, figures, charts -> visual_heavy, audio warning."""
        visual_text = """
        As shown in the diagram below, the system architecture follows a layered pattern.
        Refer to Figure 1 for the complete flowchart of the authentication process.
        The chart in Fig. 2 illustrates the performance comparison between algorithms.
        Students should draw a network topology diagram showing all connected nodes.
        The illustration on page 5 demonstrates the concept clearly.
        See the graph for quarterly revenue trends and the table of results.
        The mindmap captures all related concepts and their relationships.
        Please sketch the flowchart before implementing the solution.
        Visualize the data flow using a diagram similar to Fig. 3.
        The tree structure is shown in the figure at the end of this section.
        """ * 3

        result = analyze_content_type(visual_text)

        assert result["content_type"] == "visual_heavy"
        assert result["visual_mentions"] > 0.0
        assert "audio" in result["style_warnings"]

    # 13. Conceptual content
    def test_analyze_conceptual_content(self):
        """Plain English text about history -> conceptual, no warnings."""
        conceptual_text = """
        The Renaissance was a period of cultural rebirth that began in Italy
        during the fourteenth century and spread throughout Europe over the next
        several hundred years. It was characterized by a renewed interest in
        classical Greek and Roman culture, philosophy, art, and literature.
        The movement had profound effects on European intellectual life, leading
        to advances in science, politics, and the arts. Key figures of the
        Renaissance include Leonardo da Vinci, Michelangelo, and Galileo Galilei.
        The invention of the printing press by Johannes Gutenberg around the year
        fourteen fifty also played a crucial role in spreading new ideas across
        the continent. The political landscape of Renaissance Europe was shaped
        by powerful city-states in Italy and the rise of nation-states elsewhere.
        """ * 3

        result = analyze_content_type(conceptual_text)

        assert result["content_type"] == "conceptual"
        assert result["style_warnings"] == {}
        assert set(result["recommended_styles"]) == {"visual", "audio", "reading", "kinesthetic"}

    # 14. Math recommended styles
    def test_analyze_math_recommended_styles(self):
        """Mathematical content recommends visual, kinesthetic, reading (NOT audio)."""
        math_text = """
        Theorem: Every continuous function on a closed interval is bounded.
        Proof follows from the lemma on compactness. The integral of the
        derivative equals the original function by the fundamental theorem.
        Consider the equation f(x) = x^2 where the eigenvalue is lambda.
        The matrix determinant and polynomial roots are related through the
        formula. Apply the logarithm to simplify the exponential expression.
        """ * 5

        result = analyze_content_type(math_text)

        assert result["content_type"] == "mathematical"
        assert "visual" in result["recommended_styles"]
        assert "kinesthetic" in result["recommended_styles"]
        assert "reading" in result["recommended_styles"]
        assert "audio" not in result["recommended_styles"]

    # 15. Code recommended styles
    def test_analyze_code_recommended_styles(self):
        """Code content recommends kinesthetic, visual."""
        code_text = """
        def merge_sort(arr):
            if len(arr) <= 1:
                return arr
            mid = len(arr) // 2
            left = merge_sort(arr[:mid])
            right = merge_sort(arr[mid:])
            return merge(left, right)

        class Graph:
            def __init__(self):
                self.adjacency_list = {}

            def add_edge(self, u, v):
                if u not in self.adjacency_list:
                    self.adjacency_list[u] = []
                self.adjacency_list[u].append(v)

        for node in graph.adjacency_list:
            print(node)

        while queue:
            current = queue.pop(0)
            if current == target:
                return True

        import heapq
        from collections import defaultdict
        """ * 5

        result = analyze_content_type(code_text)

        assert result["content_type"] == "programming"
        assert "kinesthetic" in result["recommended_styles"]
        assert "visual" in result["recommended_styles"]


# ===================================================================
# TestPracticeExerciseEndpoint  (integration tests)
# ===================================================================

class TestPracticeExerciseEndpoint:
    """Integration tests for POST .../resources/{resource_id}/exercises."""

    @pytest.fixture
    def integration_client(self):
        """TestClient + DB session sharing the SAME in-memory engine."""
        from tests.conftest import _engine, _TestingSessionLocal, _override_get_db
        from app.database import Base, get_db
        from app.main import app as fastapi_app
        import app.models  # noqa: F401 — register all models with Base

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
        """Create user + study plan + resource in the shared DB."""
        from app.models.user import User
        from app.models.smartstudy import StudyPlan, StudyPlanResource
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = User(
            id=uuid.uuid4(),
            email=f"kinesthetic_{uuid.uuid4().hex[:6]}@pau.edu.ng",
            password_hash=pwd_context.hash("TestPass123!"),
            full_name="Kinesthetic Test User",
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
                "days": [
                    {
                        "day_number": 1,
                        "activities": [{"difficulty": "medium"}],
                    }
                ],
                "_slide_content": "Slide content about stacks and queues",
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
            resource_type="ai_generated",
            resource_title="Learn Stacks",
            resource_description="Introduction to stack data structure",
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

    # 16. Success
    @patch("app.services.openai_client.call_with_retry")
    def test_exercises_endpoint_success(self, mock_retry, integration_client):
        """Authenticated user with valid plan+resource -> 200 with exercises."""
        mock_retry.return_value = _mock_openai_response(VALID_EXERCISES_JSON)

        # Reset singleton so it picks up fresh state
        import app.services.practice_exercise_service as pe_mod
        pe_mod._practice_exercise_service = None

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/exercises",
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert "exercises" in body
        assert isinstance(body["exercises"], list)
        assert body["count"] == len(body["exercises"])
        assert body["plan_id"] == str(data["plan"].id)
        assert body["resource_id"] == str(data["resource"].id)

        pe_mod._practice_exercise_service = None

    # 17. Unauthenticated
    def test_exercises_endpoint_unauthenticated(self, integration_client):
        """No auth token -> 401."""
        c = integration_client["client"]
        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/exercises"
        )
        assert resp.status_code == 401

    # 18. Plan not found
    def test_exercises_endpoint_plan_not_found(self, integration_client):
        """Valid auth, non-existent plan_id -> 404."""
        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/exercises",
            headers=headers,
        )
        assert resp.status_code == 404

    # 19. Resource not found
    def test_exercises_endpoint_resource_not_found(self, integration_client):
        """Valid auth + plan, non-existent resource_id -> 404."""
        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{uuid.uuid4()}/exercises",
            headers=headers,
        )
        assert resp.status_code == 404
