"""
Tests for AudioSummaryService
backend/app/services/audio_summary_service.py

Covers: script generation via call_with_retry, slide content integration,
script truncation, TTS synthesis, caching, and availability checks.
"""
import os
import pytest
import uuid
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import date

from app.services.audio_summary_service import (
    AudioSummaryService,
    MAX_SCRIPT_CHARS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def audio_service(tmp_path, monkeypatch):
    """Create AudioSummaryService with a temp cache dir and fake ElevenLabs key."""
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key-123")
    monkeypatch.setattr(
        "app.services.audio_summary_service.AUDIO_CACHE_DIR",
        str(tmp_path),
    )
    svc = AudioSummaryService()
    return svc


@pytest.fixture
def audio_service_no_elevenlabs(tmp_path, monkeypatch):
    """AudioSummaryService with no ElevenLabs key."""
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.setattr(
        "app.services.audio_summary_service.AUDIO_CACHE_DIR",
        str(tmp_path),
    )
    svc = AudioSummaryService()
    return svc


def _mock_openai_response(content="This is a generated script about the topic."):
    """Create a mock OpenAI ChatCompletion response."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = content
    mock_resp.model = "gpt-5.4"
    return mock_resp


# ===================================================================
# generate_script tests
# ===================================================================

class TestGenerateScript:

    @patch("app.services.openai_client.call_with_retry")
    async def test_uses_call_with_retry(self, mock_retry, audio_service):
        """Verify call_with_retry is called (not direct openai_client)."""
        mock_retry.return_value = _mock_openai_response()

        await audio_service.generate_script("Binary Trees", "Learn basics", "Introduction to BSTs")

        mock_retry.assert_called_once()
        call_kwargs = mock_retry.call_args
        from app.services.openai_client import PLAN_MODELS
        assert call_kwargs.kwargs.get("models") == PLAN_MODELS

    @patch("app.services.openai_client.call_with_retry")
    async def test_includes_slide_content(self, mock_retry, audio_service):
        """When slide_content is provided, the prompt should contain it."""
        mock_retry.return_value = _mock_openai_response()
        slide_text = "Slide 1: Introduction to Binary Trees\nSlide 2: BST Properties"

        await audio_service.generate_script(
            "Binary Trees", "Learn basics", "Intro to BSTs",
            slide_content=slide_text,
        )

        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "ACTUAL SLIDE/LECTURE CONTENT" in user_msg["content"]
        assert "Slide 1: Introduction to Binary Trees" in user_msg["content"]

    @patch("app.services.openai_client.call_with_retry")
    async def test_without_slide_content(self, mock_retry, audio_service):
        """When no slide_content, the prompt works as a standalone lecture."""
        mock_retry.return_value = _mock_openai_response()

        await audio_service.generate_script("Binary Trees", "Learn basics", "Intro to BSTs")

        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "ACTUAL SLIDE/LECTURE CONTENT" not in user_msg["content"]
        assert "podcast-style audio lecture" in user_msg["content"]

    @patch("app.services.openai_client.call_with_retry")
    async def test_truncates_long_script(self, mock_retry, audio_service):
        """Script exceeding MAX_SCRIPT_CHARS gets truncated at sentence boundary."""
        long_script = "This is a sentence. " * 300  # ~6000 chars
        mock_retry.return_value = _mock_openai_response(long_script)

        result = await audio_service.generate_script("Topic", "Title", "Desc")

        assert len(result) <= MAX_SCRIPT_CHARS + 1
        assert result.endswith(".")

    @patch("app.services.openai_client.call_with_retry")
    async def test_slide_content_truncated_in_prompt(self, mock_retry, audio_service):
        """Very long slide_content is truncated to 6000 chars in the prompt."""
        mock_retry.return_value = _mock_openai_response()
        huge_slide = "A" * 10000

        await audio_service.generate_script("Topic", "Title", "Desc", slide_content=huge_slide)

        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "A" * 6000 in user_msg["content"]
        assert "A" * 6001 not in user_msg["content"]


# ===================================================================
# synthesize_audio tests
# ===================================================================

class TestSynthesizeAudio:

    @patch("app.services.audio_summary_service.httpx.Client")
    def test_success(self, mock_client_cls, audio_service):
        """Successful ElevenLabs TTS returns audio bytes and provider."""
        mock_response = MagicMock(status_code=200, content=b'ID3' + b'\x00' * 100)
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

        audio_bytes, provider = audio_service.synthesize_audio("Hello world")
        assert audio_bytes[:3] == b'ID3'
        assert provider == "elevenlabs"

    @patch("app.services.openai_client.get_openai_client", return_value=None)
    @patch("app.services.audio_summary_service.httpx.Client")
    def test_rate_limit_raises(self, mock_client_cls, mock_openai, audio_service):
        """429 from ElevenLabs + no OpenAI fallback raises RuntimeError."""
        mock_response = MagicMock(status_code=429)
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        with pytest.raises(RuntimeError, match="All TTS providers failed"):
            audio_service.synthesize_audio("Hello world")

    @patch("app.services.openai_client.get_openai_client", return_value=None)
    @patch("app.services.audio_summary_service.httpx.Client")
    def test_invalid_key_raises(self, mock_client_cls, mock_openai, audio_service):
        """401 from ElevenLabs + no OpenAI fallback raises RuntimeError."""
        mock_response = MagicMock(status_code=401)
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        with pytest.raises(RuntimeError, match="All TTS providers failed"):
            audio_service.synthesize_audio("Hello world")

    @patch("app.services.openai_client.get_openai_client", return_value=None)
    def test_no_elevenlabs_key_raises(self, mock_openai, audio_service_no_elevenlabs):
        """No ElevenLabs key + no OpenAI fallback raises RuntimeError."""
        with pytest.raises(RuntimeError, match="All TTS providers failed"):
            audio_service_no_elevenlabs.synthesize_audio("Hello world")

    @patch("app.services.openai_client.get_openai_client", return_value=None)
    @patch("app.services.audio_summary_service.httpx.Client")
    def test_invalid_audio_data_raises(self, mock_post, mock_openai, audio_service):
        """Non-MP3 response body from ElevenLabs + no OpenAI fallback raises RuntimeError."""
        _mock_resp = MagicMock(status_code=200, content=b'<html>Error</html>')
        _mock_resp.raise_for_status = MagicMock()
        _mock_cl = MagicMock()
        _mock_cl.post.return_value = _mock_resp
        mock_post.return_value.__enter__ = MagicMock(return_value=_mock_cl)
        mock_post.return_value.__exit__ = MagicMock(return_value=False)
        with pytest.raises(RuntimeError, match="All TTS providers failed"):
            audio_service.synthesize_audio("Hello world")


# ===================================================================
# get_or_generate tests
# ===================================================================

class TestGetOrGenerate:

    async def test_cached_file(self, audio_service, tmp_path):
        """When cached MP3 exists on disk, return it without generating."""
        resource_id = str(uuid.uuid4())
        cached_path = tmp_path / f"{resource_id}.mp3"
        cached_path.write_bytes(b'ID3cached')

        result = await audio_service.get_or_generate(resource_id, "Topic", "Title", "Desc")
        assert result["filepath"] == str(cached_path)
        assert result["script"] is None

    @patch("app.services.audio_summary_service.httpx.Client")
    @patch("app.services.openai_client.call_with_retry")
    async def test_fresh_generation(self, mock_retry, mock_tts_post, audio_service, tmp_path):
        """No cached file -> generates script + audio -> caches to disk."""
        mock_retry.return_value = _mock_openai_response("Generated script.")
        _mock_resp = MagicMock(status_code=200, content=b'ID3' + b'\x00' * 50)
        _mock_resp.raise_for_status = MagicMock()
        _mock_cl = MagicMock()
        _mock_cl.post.return_value = _mock_resp
        mock_tts_post.return_value.__enter__ = MagicMock(return_value=_mock_cl)
        mock_tts_post.return_value.__exit__ = MagicMock(return_value=False)

        resource_id = str(uuid.uuid4())
        result = await audio_service.get_or_generate(resource_id, "Topic", "Title", "Desc")
        assert result["filepath"] is not None
        assert result["script"] == "Generated script."
        assert os.path.isfile(result["filepath"])

    @patch("app.services.openai_client.get_openai_client", return_value=None)
    @patch("app.services.audio_summary_service.httpx.Client")
    @patch("app.services.openai_client.call_with_retry")
    async def test_tts_failure_returns_script(self, mock_retry, mock_tts_post, mock_openai_client, audio_service):
        """All TTS providers fail -> script returned, no audio, tts_failed=True."""
        mock_retry.return_value = _mock_openai_response("Script without audio.")
        _mock_cl = MagicMock()
        _mock_cl.post.side_effect = Exception("TTS service down")
        mock_tts_post.return_value.__enter__ = MagicMock(return_value=_mock_cl)
        mock_tts_post.return_value.__exit__ = MagicMock(return_value=False)

        resource_id = str(uuid.uuid4())
        result = await audio_service.get_or_generate(resource_id, "Topic", "Title", "Desc")
        assert result["filepath"] is None
        assert result["script"] == "Script without audio."
        assert result["tts_failed"] is True
        assert "tts_error" in result

    @patch("app.services.audio_summary_service.httpx.Client")
    @patch("app.services.openai_client.call_with_retry")
    async def test_slide_content_passed_through(self, mock_retry, mock_tts_post, audio_service):
        """slide_content is forwarded to generate_script."""
        mock_retry.return_value = _mock_openai_response("Script from slides.")
        _mock_resp = MagicMock(status_code=200, content=b'ID3' + b'\x00' * 50)
        _mock_resp.raise_for_status = MagicMock()
        _mock_cl = MagicMock()
        _mock_cl.post.return_value = _mock_resp
        mock_tts_post.return_value.__enter__ = MagicMock(return_value=_mock_cl)
        mock_tts_post.return_value.__exit__ = MagicMock(return_value=False)

        resource_id = str(uuid.uuid4())
        result = await audio_service.get_or_generate(
            resource_id, "Topic", "Title", "Desc",
            slide_content="Slide 1: Intro\nSlide 2: Details",
        )
        call_args = mock_retry.call_args
        messages = call_args.kwargs.get("messages", call_args.args[0] if call_args.args else [])
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "Slide 1: Intro" in user_msg["content"]


# ===================================================================
# is_available tests
# ===================================================================

class TestIsAvailable:

    @patch("app.services.openai_client.get_openai_client")
    async def test_both_keys_set(self, mock_client, audio_service):
        """Both OpenAI client and ElevenLabs key -> True."""
        mock_client.return_value = MagicMock()
        assert audio_service.is_available is True

    @patch("app.services.openai_client.get_openai_client")
    async def test_missing_elevenlabs_with_openai(self, mock_client, audio_service_no_elevenlabs):
        """No ElevenLabs but OpenAI available -> True (OpenAI provides TTS fallback)."""
        mock_client.return_value = MagicMock()
        assert audio_service_no_elevenlabs.is_available is True

    @patch("app.services.openai_client.get_openai_client", return_value=None)
    async def test_no_providers(self, mock_client, audio_service_no_elevenlabs):
        """No ElevenLabs and no OpenAI -> False."""
        assert audio_service_no_elevenlabs.is_available is False

    @patch("app.services.openai_client.get_openai_client")
    async def test_missing_openai(self, mock_client, audio_service):
        """No OpenAI client -> False."""
        mock_client.return_value = None
        assert audio_service.is_available is False


# ===================================================================
# Route integration tests (audio endpoint)
# Uses the root conftest's shared engine via _TestingSessionLocal
# so that TestClient and test data share the same in-memory DB.
# ===================================================================

class TestAudioEndpoint:
    """Integration tests for the generate_audio route handler."""

    @pytest.fixture
    def integration_client(self):
        """TestClient + DB session sharing the SAME in-memory engine."""
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
        """Create user + plan + resource in the shared DB."""
        from app.models.user import User
        from app.models.smartstudy import StudyPlan, StudyPlanResource
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        user = User(
            id=uuid.uuid4(),
            email=f"audio_{uuid.uuid4().hex[:6]}@pau.edu.ng",
            password_hash=pwd_context.hash("TestPass123!"),
            full_name="Audio Test User",
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
            topic="Binary Trees",
            plan_data={
                "title": "Master BSTs",
                "days": [{"day_number": 1, "activities": []}],
                "_slide_content": "Slide content here",
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
            resource_title="Learn BST basics",
            resource_description="Introduction to binary search trees",
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

    def test_unauthenticated(self, integration_client):
        """401 without auth token."""
        c = integration_client["client"]
        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/audio"
        )
        assert resp.status_code == 401

    def test_plan_not_found(self, integration_client):
        """404 for non-existent plan."""
        c = integration_client["client"]
        data = self._create_test_data(integration_client["db"])
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{uuid.uuid4()}/resources/{uuid.uuid4()}/audio",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_resource_not_found(self, integration_client):
        """404 for non-existent resource within a valid plan."""
        c = integration_client["client"]
        data = self._create_test_data(integration_client["db"])
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{uuid.uuid4()}/audio",
            headers=headers,
        )
        assert resp.status_code == 404

    def test_cached_audio(self, integration_client):
        """When resource already has audio_file_path, returns cached response."""
        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)

        resource = data["resource"]
        resource.audio_file_path = "cached_audio.mp3"
        resource.audio_script = "Cached script text"
        db.commit()

        headers = self._auth_header(data["user"])
        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{resource.id}/audio",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["cached"] is True
        assert "cached_audio.mp3" in body["audio_url"]

    @patch("app.services.openai_client.get_openai_client", return_value=None)
    def test_service_unavailable(self, mock_client, integration_client, monkeypatch):
        """503 when audio service is not configured."""
        monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        # Reset singleton so it picks up the missing keys
        import app.services.audio_summary_service as audio_mod
        audio_mod._audio_summary_service = None

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/audio",
            headers=headers,
        )
        assert resp.status_code == 503
        audio_mod._audio_summary_service = None

    @patch("app.services.audio_summary_service.httpx.Client")
    @patch("app.services.openai_client.call_with_retry")
    @patch("app.services.openai_client.get_openai_client")
    def test_generate_audio_success(
        self, mock_client, mock_retry, mock_httpx_cls, integration_client, tmp_path, monkeypatch,
    ):
        """Full success path: generates script + audio, returns 200."""
        mock_client.return_value = MagicMock()
        mock_retry.return_value = _mock_openai_response("Generated audio script.")
        mock_response = MagicMock(status_code=200, content=b'ID3' + b'\x00' * 50)
        mock_response.raise_for_status = MagicMock()
        mock_httpx = MagicMock()
        mock_httpx.post.return_value = mock_response
        mock_httpx_cls.return_value.__enter__ = MagicMock(return_value=mock_httpx)
        mock_httpx_cls.return_value.__exit__ = MagicMock(return_value=False)

        monkeypatch.setattr(
            "app.services.audio_summary_service.AUDIO_CACHE_DIR",
            str(tmp_path),
        )
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")

        import app.services.audio_summary_service as audio_mod
        audio_mod._audio_summary_service = None

        db = integration_client["db"]
        c = integration_client["client"]
        data = self._create_test_data(db)
        headers = self._auth_header(data["user"])

        resp = c.post(
            f"/api/v1/smartstudy/study-plans/{data['plan'].id}/resources/{data['resource'].id}/audio",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["script"] == "Generated audio script."
        assert body["audio_url"] is not None
        assert body["cached"] is False

        audio_mod._audio_summary_service = None
