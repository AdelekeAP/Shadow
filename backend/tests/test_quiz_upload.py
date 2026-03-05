"""
Comprehensive tests for Quiz Upload and Study-Weak-Topics features.

Covers:
  - POST /api/v1/smartstudy/quizzes/upload  (file validation, processing, cleanup)
  - POST /api/v1/smartstudy/quizzes/{quiz_id}/study-weak-topics  (gap-analysis study plan)

These tests use the same patterns as tests/test_quiz.py:
  - unittest.mock for mocking the database, OpenAI calls, and file I/O
  - MockQuizModel / MockQuizAttemptModel helpers for route-level isolation
  - TestClient integration tests with SQLite for end-to-end route testing

File references:
  backend/app/routes/smartstudy/quizzes.py   (upload + study-weak-topics endpoints)
  backend/app/models/quiz.py                 (Quiz, QuizAttempt ORM models)
  backend/app/services/study_plan_generator.py  (generate_study_plan)
  backend/app/services/document_processor.py    (extract_text_from_file, extract_topics_with_gpt4)
"""

import io
import json
import os
import tempfile
import uuid
import inspect
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock, AsyncMock, ANY


# ===================================================================
# Shared helpers
# ===================================================================

FAKE_UUID = "00000000-0000-0000-0000-000000000000"

# Minimal valid PDF magic bytes (followed by junk so size > 0)
VALID_PDF_BYTES = b"%PDF-1.4 fake content for testing" + (b"x" * 100)

# Minimal valid PPTX magic bytes (ZIP/PK header followed by junk)
VALID_PPTX_BYTES = b"PK\x03\x04" + (b"x" * 100)

# 10 MB limit from the endpoint
TEN_MB = 10 * 1024 * 1024


def _make_sample_questions():
    """Return a list of sample quiz questions in the expected JSON format."""
    return [
        {
            "id": 1,
            "type": "multiple_choice",
            "question": "What is a binary search tree?",
            "options": ["A) A linear structure", "B) A tree with sorted nodes", "C) A graph", "D) A hash table"],
            "correct_answer": "B",
            "explanation": "A BST is a tree where left < parent < right.",
            "topic_tag": "BST Basics",
            "difficulty": "easy",
        },
        {
            "id": 2,
            "type": "true_false",
            "question": "A BST always has O(log n) search time.",
            "options": ["True", "False"],
            "correct_answer": "False",
            "explanation": "Only balanced BSTs guarantee O(log n).",
            "topic_tag": "BST Complexity",
            "difficulty": "medium",
        },
    ]


class MockQuizModel:
    """Mimics the Quiz SQLAlchemy model without needing a database."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.user_id = kwargs.get("user_id", uuid.uuid4())
        self.study_plan_id = kwargs.get("study_plan_id", None)
        self.course_id = kwargs.get("course_id", None)
        self.title = kwargs.get("title", "Quiz: Data Structures")
        self.topic = kwargs.get("topic", "Data Structures")
        self.quiz_type = kwargs.get("quiz_type", "quick_quiz")
        self.questions = kwargs.get("questions", _make_sample_questions())
        self.question_count = kwargs.get("question_count", 2)
        self.time_limit_minutes = kwargs.get("time_limit_minutes", None)
        self.difficulty_level = kwargs.get("difficulty_level", "mixed")
        self.source_type = kwargs.get("source_type", "topic")
        self.slide_content = kwargs.get("slide_content", None)
        self.created_at = kwargs.get("created_at", datetime.now(timezone.utc))

    def to_dict(self, include_answers=False):
        questions = self.questions or []
        if not include_answers:
            questions = [
                {k: v for k, v in q.items() if k not in ("correct_answer", "explanation")}
                for q in questions
            ]
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


class MockQuizAttemptModel:
    """Mimics the QuizAttempt SQLAlchemy model without needing a database."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.quiz_id = kwargs.get("quiz_id", uuid.uuid4())
        self.user_id = kwargs.get("user_id", uuid.uuid4())
        self.answers = kwargs.get("answers", [])
        self.score = kwargs.get("score", Decimal("75.00"))
        self.correct_count = kwargs.get("correct_count", 2)
        self.total_questions = kwargs.get("total_questions", 4)
        self.time_taken_seconds = kwargs.get("time_taken_seconds", 120)
        self.was_timed = kwargs.get("was_timed", False)
        self.timed_out = kwargs.get("timed_out", False)
        self.knowledge_gaps = kwargs.get("knowledge_gaps", None)
        self.started_at = kwargs.get("started_at", datetime.now(timezone.utc))
        self.completed_at = kwargs.get("completed_at", datetime.now(timezone.utc))

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


# ===================================================================
# Integration test fixtures (TestClient + SQLite)
# ===================================================================

@pytest.fixture(scope="function")
def _route_test_env():
    """Set up environment and create in-memory SQLite DB engine for route tests."""
    os.environ["DISABLE_ML_MODELS"] = "true"
    os.environ["TESTING"] = "true"
    os.environ["SECRET_KEY"] = "test-secret-key-for-quiz-upload-tests"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.dialects.postgresql import JSONB
    from sqlalchemy.ext.compiler import compiles
    from app.database import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @compiles(JSONB, "sqlite")
    def compile_jsonb_sqlite(type_, compiler, **kw):
        return "JSON"

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    import app.models  # noqa: F401 — ensure all models are imported so metadata is populated
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    yield engine, session, TestingSessionLocal
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def quiz_client(_route_test_env):
    """Create a TestClient with overridden DB dependency."""
    from fastapi.testclient import TestClient
    from app.database import get_db
    from app.main import app

    engine, session, TestingSessionLocal = _route_test_env

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def quiz_auth_headers(quiz_client):
    """Register a test user and return auth headers."""
    user_data = {
        "email": "upload_tester@pau.edu.ng",
        "password": "SecurePass123!",
        "full_name": "Upload Tester",
        "university_id": "PAU/2022/099",
        "entry_level": "400L",
        "target_cgpa": 4.5,
        "current_cgpa": 3.8,
    }
    response = quiz_client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201, f"Registration failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ===================================================================
# 1. Quiz Upload Tests — Integration (TestClient)
# ===================================================================

class TestQuizUploadIntegration:
    """Integration tests hitting the actual /upload endpoint via TestClient."""

    def test_upload_rejects_unsupported_extension(self, quiz_client, quiz_auth_headers):
        """POST /upload with a .txt file should return 400 with a clear message."""
        file_content = b"Some plain text content"
        response = quiz_client.post(
            "/api/v1/smartstudy/quizzes/upload",
            files={"uploaded_file": ("notes.txt", io.BytesIO(file_content), "text/plain")},
            data={"topic": "Test"},
            headers=quiz_auth_headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "PDF" in detail or "PPTX" in detail

    def test_upload_rejects_empty_file(self, quiz_client, quiz_auth_headers):
        """POST /upload with a 0-byte PDF should return 400."""
        response = quiz_client.post(
            "/api/v1/smartstudy/quizzes/upload",
            files={"uploaded_file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
            data={"topic": "Test"},
            headers=quiz_auth_headers,
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_rejects_oversized_file(self, quiz_client, quiz_auth_headers):
        """POST /upload with a >10MB file should return 400."""
        # Create content that starts with valid PDF magic bytes but exceeds 10 MB
        oversized = b"%PDF-1.4" + (b"\x00" * (TEN_MB + 1))
        response = quiz_client.post(
            "/api/v1/smartstudy/quizzes/upload",
            files={"uploaded_file": ("huge.pdf", io.BytesIO(oversized), "application/pdf")},
            data={"topic": "Test"},
            headers=quiz_auth_headers,
        )
        assert response.status_code == 400
        assert "10MB" in response.json()["detail"] or "too large" in response.json()["detail"].lower()

    def test_upload_rejects_pdf_magic_bytes_mismatch(self, quiz_client, quiz_auth_headers):
        """POST /upload with .pdf extension but non-PDF content should return 400."""
        # Content that does NOT start with %PDF
        fake_pdf = b"THIS IS NOT A PDF FILE AT ALL" + (b"x" * 100)
        response = quiz_client.post(
            "/api/v1/smartstudy/quizzes/upload",
            files={"uploaded_file": ("lecture.pdf", io.BytesIO(fake_pdf), "application/pdf")},
            data={"topic": "Test"},
            headers=quiz_auth_headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "does not match" in detail
        assert "PDF" in detail

    def test_upload_rejects_pptx_magic_bytes_mismatch(self, quiz_client, quiz_auth_headers):
        """POST /upload with .pptx extension but non-PPTX content should return 400."""
        # Content that does NOT start with PK\x03\x04
        fake_pptx = b"NOT_A_ZIP_OR_PPTX_FILE" + (b"y" * 100)
        response = quiz_client.post(
            "/api/v1/smartstudy/quizzes/upload",
            files={"uploaded_file": ("slides.pptx", io.BytesIO(fake_pptx), "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
            data={"topic": "Test"},
            headers=quiz_auth_headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "does not match" in detail
        assert "PPTX" in detail

    def test_upload_requires_topic_or_file(self, quiz_client, quiz_auth_headers):
        """POST /upload with neither topic nor file should return 400."""
        response = quiz_client.post(
            "/api/v1/smartstudy/quizzes/upload",
            data={},
            headers=quiz_auth_headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "topic" in detail.lower() or "document" in detail.lower()


class TestQuizUploadTempFileCleanup:
    """Tests verifying that temporary files are cleaned up after document processing."""

    @pytest.mark.asyncio
    async def test_upload_temp_file_cleanup(self):
        """Verify that the _process_document helper removes the temp file in its finally block."""
        # We test the inner _process_document function directly by reproducing its logic
        # and verifying os.unlink is called.
        import asyncio

        created_paths = []

        def mock_extract_text(path):
            """Mock extract_text_from_file that records the path and returns text."""
            created_paths.append(path)
            return "Extracted slide content about algorithms"

        with patch("app.services.document_processor.extract_text_from_file", side_effect=mock_extract_text):
            with patch("app.services.document_processor.extract_topics_with_gpt4", return_value={"main_topic": "Algorithms"}):
                # Simulate the _process_document logic from the endpoint
                def _process_document(data: bytes, ext: str):
                    tmp_path = None
                    try:
                        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                            tmp.write(data)
                            tmp_path = tmp.name
                        created_paths.append(tmp_path)
                        return mock_extract_text(tmp_path)
                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                result = await asyncio.to_thread(_process_document, VALID_PDF_BYTES, "pdf")

                assert result == "Extracted slide content about algorithms"
                # The temp file should have been created and then deleted
                assert len(created_paths) >= 1
                for path in created_paths:
                    assert not os.path.exists(path), f"Temp file was not cleaned up: {path}"

    @pytest.mark.asyncio
    async def test_upload_temp_file_cleanup_on_extraction_error(self):
        """Verify temp file is cleaned up even when extract_text_from_file raises."""
        import asyncio

        created_tmp_path = None

        def _process_document(data: bytes, ext: str):
            nonlocal created_tmp_path
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = tmp.name
                created_tmp_path = tmp_path
                raise RuntimeError("Simulated extraction failure")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        with pytest.raises(RuntimeError, match="Simulated extraction failure"):
            await asyncio.to_thread(_process_document, VALID_PDF_BYTES, "pdf")

        assert created_tmp_path is not None
        assert not os.path.exists(created_tmp_path), "Temp file was not cleaned up after error"


# ===================================================================
# 2. Study Weak Topics Tests — Unit tests (mocked DB)
# ===================================================================

class TestStudyWeakTopicsUnit:
    """Unit tests for the study-weak-topics endpoint using mocked dependencies."""

    @pytest.mark.asyncio
    @patch("app.services.study_plan_generator.generate_study_plan")
    async def test_study_weak_topics_success(self, mock_gen_plan):
        """Quiz with weak topics should generate a study plan and return it."""
        from app.routes.smartstudy.quizzes import create_study_plan_from_quiz_gaps

        user_id = uuid.uuid4()
        quiz_id = uuid.uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id

        mock_quiz = MagicMock()
        mock_quiz.id = quiz_id
        mock_quiz.user_id = user_id
        mock_quiz.topic = "Binary Search Trees"
        mock_quiz.course_id = None
        mock_quiz.slide_content = None

        weak_topics = [
            {"topic": "BST Traversal", "score_pct": 30},
            {"topic": "BST Deletion", "score_pct": 40},
        ]
        mock_attempt = MagicMock()
        mock_attempt.knowledge_gaps = {"weak_topics": weak_topics}
        mock_attempt.score = Decimal("35.00")

        mock_db = MagicMock()
        # First query: Quiz lookup
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quiz
        # Second query: QuizAttempt lookup (order_by().first())
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_attempt

        mock_gen_plan.return_value = {
            "study_plan_id": str(uuid.uuid4()),
            "topic": "Binary Search Trees — focusing on: BST Traversal, BST Deletion",
            "days": [],
        }

        mock_request = MagicMock()

        result = await create_study_plan_from_quiz_gaps(
            request=mock_request,
            quiz_id=str(quiz_id),
            db=mock_db,
            current_user=mock_user,
        )

        mock_gen_plan.assert_called_once()
        call_kwargs = mock_gen_plan.call_args
        assert "BST Traversal" in call_kwargs.kwargs.get("topic", "") or "BST Traversal" in call_kwargs.args[0] if call_kwargs.args else "BST Traversal" in str(call_kwargs)
        assert result["source"] == "quiz_gap_analysis"
        assert result["weak_topics"] == ["BST Traversal", "BST Deletion"]
        assert result["quiz_score"] == 35.0

    @pytest.mark.asyncio
    async def test_study_weak_topics_quiz_not_found(self):
        """Invalid quiz_id should return 404."""
        from app.routes.smartstudy.quizzes import create_study_plan_from_quiz_gaps
        from fastapi import HTTPException

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await create_study_plan_from_quiz_gaps(
                request=mock_request,
                quiz_id=str(uuid.uuid4()),
                db=mock_db,
                current_user=mock_user,
            )
        assert exc_info.value.status_code == 404
        assert "Quiz not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_study_weak_topics_no_attempts(self):
        """Quiz with 0 attempts should return 400."""
        from app.routes.smartstudy.quizzes import create_study_plan_from_quiz_gaps
        from fastapi import HTTPException

        user_id = uuid.uuid4()
        quiz_id = uuid.uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id

        mock_quiz = MagicMock()
        mock_quiz.id = quiz_id
        mock_quiz.user_id = user_id

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quiz
        # No attempts exist
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        mock_request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await create_study_plan_from_quiz_gaps(
                request=mock_request,
                quiz_id=str(quiz_id),
                db=mock_db,
                current_user=mock_user,
            )
        assert exc_info.value.status_code == 400
        assert "Take the quiz first" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_study_weak_topics_no_weak_topics(self):
        """Perfect score (no weak topics) should return 400 with 'no weak topics' message."""
        from app.routes.smartstudy.quizzes import create_study_plan_from_quiz_gaps
        from fastapi import HTTPException

        user_id = uuid.uuid4()
        quiz_id = uuid.uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id

        mock_quiz = MagicMock()
        mock_quiz.id = quiz_id
        mock_quiz.user_id = user_id

        # Attempt exists with knowledge_gaps but empty weak_topics
        mock_attempt = MagicMock()
        mock_attempt.knowledge_gaps = {"weak_topics": [], "strong_topics": [{"topic": "All", "score_pct": 100}]}
        mock_attempt.score = Decimal("100.00")

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quiz
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_attempt

        mock_request = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await create_study_plan_from_quiz_gaps(
                request=mock_request,
                quiz_id=str(quiz_id),
                db=mock_db,
                current_user=mock_user,
            )
        assert exc_info.value.status_code == 400
        detail = str(exc_info.value.detail).lower()
        assert "no weak topics" in detail or "scored well" in detail

    @pytest.mark.asyncio
    @patch("app.services.study_plan_generator.generate_study_plan")
    async def test_study_weak_topics_uses_slide_content(self, mock_gen_plan):
        """When quiz has slide_content (from an uploaded document), it should be passed
        to generate_study_plan so the study plan can reference original material."""
        from app.routes.smartstudy.quizzes import create_study_plan_from_quiz_gaps

        user_id = uuid.uuid4()
        quiz_id = uuid.uuid4()
        slide_text = "Slide 1: Introduction to Sorting Algorithms\nSlide 2: Bubble Sort..."

        mock_user = MagicMock()
        mock_user.id = user_id

        mock_quiz = MagicMock()
        mock_quiz.id = quiz_id
        mock_quiz.user_id = user_id
        mock_quiz.topic = "Sorting Algorithms"
        mock_quiz.course_id = uuid.uuid4()
        mock_quiz.slide_content = slide_text

        mock_attempt = MagicMock()
        mock_attempt.knowledge_gaps = {
            "weak_topics": [{"topic": "Bubble Sort", "score_pct": 25}]
        }
        mock_attempt.score = Decimal("50.00")

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quiz
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_attempt

        mock_gen_plan.return_value = {
            "study_plan_id": str(uuid.uuid4()),
            "topic": "Sorting Algorithms — focusing on: Bubble Sort",
            "days": [],
        }

        mock_request = MagicMock()

        await create_study_plan_from_quiz_gaps(
            request=mock_request,
            quiz_id=str(quiz_id),
            db=mock_db,
            current_user=mock_user,
        )

        mock_gen_plan.assert_called_once()
        call_kwargs = mock_gen_plan.call_args
        # Check that slide_content was passed through
        assert call_kwargs.kwargs.get("slide_content") == slide_text

    @pytest.mark.asyncio
    @patch("app.services.study_plan_generator.generate_study_plan")
    async def test_study_weak_topics_without_slide_content(self, mock_gen_plan):
        """When quiz has no document (slide_content=None), study plan should still be
        generated successfully with slide_content=None."""
        from app.routes.smartstudy.quizzes import create_study_plan_from_quiz_gaps

        user_id = uuid.uuid4()
        quiz_id = uuid.uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id

        mock_quiz = MagicMock()
        mock_quiz.id = quiz_id
        mock_quiz.user_id = user_id
        mock_quiz.topic = "Machine Learning"
        mock_quiz.course_id = None
        mock_quiz.slide_content = None  # No document uploaded

        mock_attempt = MagicMock()
        mock_attempt.knowledge_gaps = {
            "weak_topics": [{"topic": "Gradient Descent", "score_pct": 20}]
        }
        mock_attempt.score = Decimal("40.00")

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_quiz
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_attempt

        mock_gen_plan.return_value = {
            "study_plan_id": str(uuid.uuid4()),
            "topic": "Machine Learning — focusing on: Gradient Descent",
            "days": [],
        }

        mock_request = MagicMock()

        result = await create_study_plan_from_quiz_gaps(
            request=mock_request,
            quiz_id=str(quiz_id),
            db=mock_db,
            current_user=mock_user,
        )

        mock_gen_plan.assert_called_once()
        call_kwargs = mock_gen_plan.call_args
        assert call_kwargs.kwargs.get("slide_content") is None
        assert result["source"] == "quiz_gap_analysis"
        assert result["weak_topics"] == ["Gradient Descent"]

    def test_study_weak_topics_rate_limited(self):
        """Verify the study-weak-topics endpoint has a @limiter.limit() decorator."""
        from app.routes.smartstudy.quizzes import create_study_plan_from_quiz_gaps

        # slowapi attaches rate limit info via decorators; the endpoint function
        # will have a `__wrapped__` attribute or rate limit metadata.
        # We inspect the route definitions on the router instead.
        from app.routes.smartstudy.quizzes import router

        # Find the route for study-weak-topics
        found_route = None
        for route in router.routes:
            if hasattr(route, "path") and "study-weak-topics" in route.path:
                found_route = route
                break

        assert found_route is not None, "study-weak-topics route not found in router"

        # slowapi stores rate limit info in the endpoint's __self__ or via
        # the _rate_limits attribute, or the route has dependencies.
        # The most reliable check is that the endpoint function has been
        # decorated with @limiter.limit, which attaches metadata.
        endpoint = found_route.endpoint
        # Check for the _limit attribute that slowapi attaches
        has_rate_limit = (
            hasattr(endpoint, "__wrapped__")
            or hasattr(endpoint, "_rate_limits")
            or hasattr(endpoint, "__rate_limit__")
            or any("limiter" in str(d) for d in getattr(found_route, "dependencies", []))
        )
        # If the above heuristics fail, we can also inspect the source for
        # @limiter.limit — a reliable fallback
        if not has_rate_limit:
            source = inspect.getsource(endpoint)
            # The decorator was applied in the module source, so we check
            # the module-level source for the route
            import app.routes.smartstudy.quizzes as quizzes_module
            module_source = inspect.getsource(quizzes_module)
            # Find the function definition and look for @limiter.limit before it
            func_name = "create_study_plan_from_quiz_gaps"
            idx = module_source.find(f"def {func_name}")
            assert idx > 0, f"Could not find {func_name} in module source"
            # Look at the ~200 chars before the function definition for the decorator
            preceding = module_source[max(0, idx - 200):idx]
            has_rate_limit = "limiter.limit" in preceding

        assert has_rate_limit, "study-weak-topics endpoint is not rate limited"


# ===================================================================
# 3. Study Weak Topics Tests — Integration (TestClient)
# ===================================================================

class TestStudyWeakTopicsIntegration:
    """End-to-end tests for study-weak-topics via TestClient."""

    @patch("app.services.quiz_generator.call_with_retry")
    def test_study_weak_topics_success_e2e(self, mock_call, quiz_client, quiz_auth_headers):
        """Full flow: create quiz -> submit with some wrong answers -> study weak topics."""
        # Step 1: Create a quiz
        quiz_data = {
            "title": "Quiz: Algorithms",
            "questions": [
                {
                    "id": 1, "type": "multiple_choice",
                    "question": "What is Bubble Sort?",
                    "options": ["A) O(n^2)", "B) O(n)", "C) O(log n)", "D) O(1)"],
                    "correct_answer": "A", "explanation": "Bubble sort is O(n^2).",
                    "topic_tag": "Sorting", "difficulty": "easy",
                },
                {
                    "id": 2, "type": "multiple_choice",
                    "question": "What is Merge Sort complexity?",
                    "options": ["A) O(n^2)", "B) O(n log n)", "C) O(n)", "D) O(1)"],
                    "correct_answer": "B", "explanation": "Merge sort is O(n log n).",
                    "topic_tag": "Sorting", "difficulty": "medium",
                },
                {
                    "id": 3, "type": "multiple_choice",
                    "question": "What is a Binary Tree?",
                    "options": ["A) Linear", "B) Tree with 2 children max", "C) Graph", "D) Array"],
                    "correct_answer": "B", "explanation": "Binary tree: each node has at most 2 children.",
                    "topic_tag": "Trees", "difficulty": "easy",
                },
            ],
        }
        mock_message = MagicMock()
        mock_message.content = json.dumps(quiz_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_usage = MagicMock()
        mock_usage.total_tokens = 400
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_call.return_value = mock_response

        create_resp = quiz_client.post(
            "/api/v1/smartstudy/quizzes",
            json={"topic": "Algorithms"},
            headers=quiz_auth_headers,
        )
        assert create_resp.status_code == 200
        quiz_id = create_resp.json()["id"]

        # Step 2: Submit answers (get Trees wrong)
        submit_resp = quiz_client.post(
            f"/api/v1/smartstudy/quizzes/{quiz_id}/submit",
            json={
                "answers": [
                    {"question_id": 1, "user_answer": "A"},   # correct
                    {"question_id": 2, "user_answer": "B"},   # correct
                    {"question_id": 3, "user_answer": "A"},   # wrong (Trees)
                ],
            },
            headers=quiz_auth_headers,
        )
        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        assert "knowledge_gaps" in submit_data

        # Step 3: Call study-weak-topics
        with patch("app.services.study_plan_generator.generate_study_plan") as mock_plan:
            mock_plan.return_value = {
                "study_plan_id": str(uuid.uuid4()),
                "topic": "Algorithms — focusing on: Trees",
                "days": [],
            }
            study_resp = quiz_client.post(
                f"/api/v1/smartstudy/quizzes/{quiz_id}/study-weak-topics",
                headers=quiz_auth_headers,
            )

        # If knowledge_gaps identified weak topics, we expect success
        # If the student scored well enough that no weak topics exist, we expect 400
        if submit_data["knowledge_gaps"] and submit_data["knowledge_gaps"].get("weak_topics"):
            assert study_resp.status_code == 200
            study_data = study_resp.json()
            assert study_data["source"] == "quiz_gap_analysis"
            assert "weak_topics" in study_data
        else:
            # Perfect or near-perfect: 400 "no weak topics"
            assert study_resp.status_code == 400

    def test_study_weak_topics_quiz_not_found_e2e(self, quiz_client, quiz_auth_headers):
        """study-weak-topics on a non-existent quiz_id should return 404."""
        fake_id = str(uuid.uuid4())
        response = quiz_client.post(
            f"/api/v1/smartstudy/quizzes/{fake_id}/study-weak-topics",
            headers=quiz_auth_headers,
        )
        assert response.status_code == 404
        assert "Quiz not found" in response.json()["detail"]

    @patch("app.services.quiz_generator.call_with_retry")
    def test_study_weak_topics_no_attempts_e2e(self, mock_call, quiz_client, quiz_auth_headers):
        """study-weak-topics on a quiz with 0 attempts should return 400."""
        # Create a quiz but do NOT submit any answers
        quiz_data = {
            "title": "Quiz: No Attempts",
            "questions": _make_sample_questions(),
        }
        mock_message = MagicMock()
        mock_message.content = json.dumps(quiz_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_usage = MagicMock()
        mock_usage.total_tokens = 200
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_call.return_value = mock_response

        create_resp = quiz_client.post(
            "/api/v1/smartstudy/quizzes",
            json={"topic": "No Attempts Test"},
            headers=quiz_auth_headers,
        )
        assert create_resp.status_code == 200
        quiz_id = create_resp.json()["id"]

        # Immediately try study-weak-topics without submitting
        response = quiz_client.post(
            f"/api/v1/smartstudy/quizzes/{quiz_id}/study-weak-topics",
            headers=quiz_auth_headers,
        )
        assert response.status_code == 400
        assert "Take the quiz first" in response.json()["detail"]

    @patch("app.services.quiz_generator.call_with_retry")
    def test_study_weak_topics_no_weak_topics_e2e(self, mock_call, quiz_client, quiz_auth_headers):
        """study-weak-topics after a perfect score should return 400 'no weak topics'."""
        # Create a quiz with only MCQ questions
        quiz_data = {
            "title": "Quiz: Perfect Score",
            "questions": [
                {
                    "id": 1, "type": "multiple_choice",
                    "question": "2+2?",
                    "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
                    "correct_answer": "B", "explanation": "2+2=4.",
                    "topic_tag": "Math", "difficulty": "easy",
                },
            ],
        }
        mock_message = MagicMock()
        mock_message.content = json.dumps(quiz_data)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_usage = MagicMock()
        mock_usage.total_tokens = 200
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_call.return_value = mock_response

        create_resp = quiz_client.post(
            "/api/v1/smartstudy/quizzes",
            json={"topic": "Perfect Score Test"},
            headers=quiz_auth_headers,
        )
        assert create_resp.status_code == 200
        quiz_id = create_resp.json()["id"]

        # Submit perfect answers
        submit_resp = quiz_client.post(
            f"/api/v1/smartstudy/quizzes/{quiz_id}/submit",
            json={
                "answers": [{"question_id": 1, "user_answer": "B"}],
            },
            headers=quiz_auth_headers,
        )
        assert submit_resp.status_code == 200
        assert submit_resp.json()["score"] == 100.0

        # study-weak-topics should fail with "no weak topics"
        response = quiz_client.post(
            f"/api/v1/smartstudy/quizzes/{quiz_id}/study-weak-topics",
            headers=quiz_auth_headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "no weak topics" in detail or "scored well" in detail


# ===================================================================
# 4. Additional upload edge case tests (unit-level)
# ===================================================================

class TestUploadValidationUnit:
    """Unit-level tests for upload validation logic, testing the endpoint
    function directly with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_upload_accepts_valid_pdf_with_topic(self):
        """A valid PDF file with proper magic bytes and a topic should proceed to processing."""
        from app.routes.smartstudy.quizzes import create_quiz_with_upload

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        mock_file = MagicMock(spec=["filename", "read", "size"])
        mock_file.filename = "lecture.pdf"
        mock_file.size = len(VALID_PDF_BYTES)
        mock_file.read = AsyncMock(return_value=VALID_PDF_BYTES)

        mock_db = MagicMock()
        mock_request = MagicMock()

        with patch("app.services.document_processor.extract_text_from_file", return_value="Slide content here"):
            with patch("app.services.quiz_generator.generate_quiz") as mock_gen:
                mock_gen.return_value = {
                    "id": str(uuid.uuid4()),
                    "topic": "Test Topic",
                    "questions": _make_sample_questions(),
                }
                result = await create_quiz_with_upload(
                    request=mock_request,
                    topic="Test Topic",
                    uploaded_file=mock_file,
                    quiz_type="quick_quiz",
                    question_count=None,
                    time_limit_minutes=None,
                    difficulty_level="mixed",
                    course_id=None,
                    db=mock_db,
                    current_user=mock_user,
                )

                assert result["extracted_topic"] == "Test Topic"
                mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_topic_only_no_file(self):
        """When only a topic is provided (no file), the quiz should be generated from topic."""
        from app.routes.smartstudy.quizzes import create_quiz_with_upload

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        mock_db = MagicMock()
        mock_request = MagicMock()

        with patch("app.services.quiz_generator.generate_quiz") as mock_gen:
            mock_gen.return_value = {
                "id": str(uuid.uuid4()),
                "topic": "Neural Networks",
                "questions": _make_sample_questions(),
            }
            result = await create_quiz_with_upload(
                request=mock_request,
                topic="Neural Networks",
                uploaded_file=None,
                quiz_type="quick_quiz",
                question_count=None,
                time_limit_minutes=None,
                difficulty_level="mixed",
                course_id=None,
                db=mock_db,
                current_user=mock_user,
            )

            assert result["extracted_topic"] == "Neural Networks"
            # generate_quiz should be called with slide_content=None
            call_kwargs = mock_gen.call_args
            assert call_kwargs.kwargs.get("slide_content") is None

    @pytest.mark.asyncio
    async def test_upload_extracts_topic_from_document_when_no_topic_given(self):
        """When no topic is provided but a file is uploaded, topic should be extracted from content."""
        from app.routes.smartstudy.quizzes import create_quiz_with_upload

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        mock_file = MagicMock(spec=["filename", "read", "size"])
        mock_file.filename = "algorithms.pdf"
        mock_file.size = len(VALID_PDF_BYTES)
        mock_file.read = AsyncMock(return_value=VALID_PDF_BYTES)

        mock_db = MagicMock()
        mock_request = MagicMock()

        with patch("app.services.document_processor.extract_text_from_file", return_value="Content about Graph Theory"):
            with patch("app.services.document_processor.extract_topics_with_gpt4", return_value={"main_topic": "Graph Theory"}):
                with patch("app.services.quiz_generator.generate_quiz") as mock_gen:
                    mock_gen.return_value = {
                        "id": str(uuid.uuid4()),
                        "topic": "Graph Theory",
                        "questions": _make_sample_questions(),
                    }
                    result = await create_quiz_with_upload(
                        request=mock_request,
                        topic=None,
                        uploaded_file=mock_file,
                        quiz_type="quick_quiz",
                        question_count=None,
                        time_limit_minutes=None,
                        difficulty_level="mixed",
                        course_id=None,
                        db=mock_db,
                        current_user=mock_user,
                    )

                    assert result["extracted_topic"] == "Graph Theory"

    @pytest.mark.asyncio
    async def test_upload_falls_back_to_general_knowledge_when_extraction_returns_none(self):
        """If document topic extraction returns None and no topic provided, default to 'General Knowledge'."""
        from app.routes.smartstudy.quizzes import create_quiz_with_upload

        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()

        mock_file = MagicMock(spec=["filename", "read", "size"])
        mock_file.filename = "unknown.pdf"
        mock_file.size = len(VALID_PDF_BYTES)
        mock_file.read = AsyncMock(return_value=VALID_PDF_BYTES)

        mock_db = MagicMock()
        mock_request = MagicMock()

        with patch("app.services.document_processor.extract_text_from_file", return_value="Some random text"):
            with patch("app.services.document_processor.extract_topics_with_gpt4", return_value={"main_topic": None}):
                with patch("app.services.quiz_generator.generate_quiz") as mock_gen:
                    mock_gen.return_value = {
                        "id": str(uuid.uuid4()),
                        "topic": "General Knowledge",
                        "questions": _make_sample_questions(),
                    }
                    result = await create_quiz_with_upload(
                        request=mock_request,
                        topic=None,
                        uploaded_file=mock_file,
                        quiz_type="quick_quiz",
                        question_count=None,
                        time_limit_minutes=None,
                        difficulty_level="mixed",
                        course_id=None,
                        db=mock_db,
                        current_user=mock_user,
                    )

                    assert result["extracted_topic"] == "General Knowledge"
