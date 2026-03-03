"""
Integration tests for SmartStudy API routes
backend/app/routes/smartstudy/

Tests the full request/response cycle through FastAPI with a real
(in-memory SQLite) database. External service calls (OpenAI, etc.)
are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock

FAKE_UUID = "00000000-0000-0000-0000-000000000000"


# ===================================================================
# POST /api/v1/smartstudy/chat
# ===================================================================

class TestChat:

    @patch("app.routes.smartstudy.chat.chat_with_smartstudy")
    def test_chat_returns_response(self, mock_chat, client, auth_headers):
        mock_chat.return_value = {
            "response": "A BST is a data structure...",
            "conversation_id": "some-conv-id",
        }
        response = client.post(
            "/api/v1/smartstudy/chat",
            json={"content": "Explain BST"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "A BST is a data structure..."
        assert "conversation_id" in data
        mock_chat.assert_called_once()

    @patch("app.routes.smartstudy.chat.chat_with_smartstudy")
    def test_chat_with_conversation_id(self, mock_chat, client, auth_headers, conversation_in_db):
        conv_id = conversation_in_db["conversation_id"]
        mock_chat.return_value = {"response": "Sure, here's more info..."}
        response = client.post(
            "/api/v1/smartstudy/chat",
            json={"content": "Tell me more", "conversation_id": conv_id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        mock_chat.assert_called_once()

    @patch("app.routes.smartstudy.chat.chat_with_smartstudy")
    def test_chat_error_from_service(self, mock_chat, client, auth_headers):
        mock_chat.return_value = {"error": "OpenAI API failure"}
        response = client.post(
            "/api/v1/smartstudy/chat",
            json={"content": "Hello"},
            headers=auth_headers,
        )
        assert response.status_code == 500

    def test_chat_requires_auth(self, client):
        response = client.post(
            "/api/v1/smartstudy/chat",
            json={"content": "Hello"},
        )
        assert response.status_code == 401

    def test_chat_empty_content_rejected(self, client, auth_headers):
        response = client.post(
            "/api/v1/smartstudy/chat",
            json={"content": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422


# ===================================================================
# GET /api/v1/smartstudy/conversations
# ===================================================================

class TestConversations:

    def test_list_conversations_empty(self, client, auth_headers):
        response = client.get(
            "/api/v1/smartstudy/conversations",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_conversations_with_data(self, client, auth_headers, conversation_in_db):
        response = client.get(
            "/api/v1/smartstudy/conversations",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Help with BSTs"
        assert data[0]["message_count"] == 2

    def test_list_conversations_limit(self, client, auth_headers, conversation_in_db):
        response = client.get(
            "/api/v1/smartstudy/conversations?limit=1",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) <= 1

    def test_list_conversations_requires_auth(self, client):
        response = client.get("/api/v1/smartstudy/conversations")
        assert response.status_code == 401


# ===================================================================
# GET /api/v1/smartstudy/conversations/{conversation_id}
# ===================================================================

class TestGetConversation:

    def test_get_conversation(self, client, auth_headers, conversation_in_db):
        conv_id = conversation_in_db["conversation_id"]
        response = client.get(
            f"/api/v1/smartstudy/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Help with BSTs"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"

    def test_get_conversation_not_found(self, client, auth_headers):
        response = client.get(
            f"/api/v1/smartstudy/conversations/{FAKE_UUID}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_conversation_requires_auth(self, client, conversation_in_db):
        conv_id = conversation_in_db["conversation_id"]
        response = client.get(f"/api/v1/smartstudy/conversations/{conv_id}")
        assert response.status_code == 401


# ===================================================================
# DELETE /api/v1/smartstudy/conversations/{conversation_id}
# ===================================================================

class TestDeleteConversation:

    def test_delete_conversation(self, client, auth_headers, conversation_in_db):
        conv_id = conversation_in_db["conversation_id"]
        response = client.delete(
            f"/api/v1/smartstudy/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/smartstudy/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_conversation_not_found(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/smartstudy/conversations/{FAKE_UUID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# GET /api/v1/smartstudy/context
# ===================================================================

class TestContext:

    @patch("app.routes.smartstudy.context.load_student_context")
    def test_get_context(self, mock_ctx, client, auth_headers):
        mock_ctx.return_value = {
            "student_info": {"current_cgpa": 3.8, "target_cgpa": 4.5},
            "courses": [],
            "recent_moods": [],
            "recent_tasks": [],
            "cgpa_gap": 0.7,
        }
        response = client.get(
            "/api/v1/smartstudy/context",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "student_info" in data
        assert "cgpa_status" in data

    def test_context_requires_auth(self, client):
        response = client.get("/api/v1/smartstudy/context")
        assert response.status_code == 401


# ===================================================================
# GET /api/v1/smartstudy/suggested-prompts
# ===================================================================

class TestSuggestedPrompts:

    @patch("app.routes.smartstudy.context.get_suggested_prompts")
    def test_get_suggested_prompts(self, mock_prompts, client, auth_headers):
        mock_prompts.return_value = [
            {"prompt": "Help me study for CSC401", "category": "planning", "icon": "📚"},
            {"prompt": "I'm struggling with BSTs", "category": "struggling", "icon": "😟"},
        ]
        response = client.get(
            "/api/v1/smartstudy/suggested-prompts",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["category"] == "planning"

    def test_suggested_prompts_requires_auth(self, client):
        response = client.get("/api/v1/smartstudy/suggested-prompts")
        assert response.status_code == 401


# ===================================================================
# GET /api/v1/smartstudy/triggers
# ===================================================================

class TestTriggers:

    @patch("app.routes.smartstudy.context.check_smartstudy_triggers")
    def test_get_triggers(self, mock_triggers, client, auth_headers):
        mock_triggers.return_value = {
            "should_trigger": True,
            "primary_trigger": {
                "type": "at_risk",
                "title": "Low CA score",
                "message": "Your CSC401 CA is below average",
            },
            "all_triggers": [],
        }
        response = client.get(
            "/api/v1/smartstudy/triggers",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["should_trigger"] is True

    def test_triggers_requires_auth(self, client):
        response = client.get("/api/v1/smartstudy/triggers")
        assert response.status_code == 401


# ===================================================================
# GET /api/v1/smartstudy/dashboard-trigger
# ===================================================================

class TestDashboardTrigger:

    @patch("app.routes.smartstudy.context.check_smartstudy_triggers")
    def test_dashboard_trigger_active(self, mock_triggers, client, auth_headers):
        mock_triggers.return_value = {
            "should_trigger": True,
            "primary_trigger": {
                "type": "at_risk",
                "title": "Low CA score",
                "message": "Your CSC401 CA is below average",
            },
            "all_triggers": [],
        }
        response = client.get(
            "/api/v1/smartstudy/dashboard-trigger",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["show_trigger"] is True
        assert data["trigger_type"] == "at_risk"

    @patch("app.routes.smartstudy.context.check_smartstudy_triggers")
    def test_dashboard_trigger_inactive(self, mock_triggers, client, auth_headers):
        mock_triggers.return_value = {
            "should_trigger": False,
            "primary_trigger": None,
            "all_triggers": [],
        }
        response = client.get(
            "/api/v1/smartstudy/dashboard-trigger",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["show_trigger"] is False


# ===================================================================
# POST /api/v1/smartstudy/study-plans
# ===================================================================

class TestCreateStudyPlan:

    @patch("app.routes.smartstudy.study_plans.generate_study_plan")
    def test_create_study_plan(self, mock_gen, client, auth_headers):
        mock_gen.return_value = {
            "study_plan_id": "abc-123",
            "topic": "Binary Search Trees",
            "plan_data": {"days": [{"day": 1, "activities": ["Read chapter"]}]},
        }
        response = client.post(
            "/api/v1/smartstudy/study-plans",
            json={"topic": "Binary Search Trees"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Binary Search Trees"
        mock_gen.assert_called_once()

    @patch("app.routes.smartstudy.study_plans.generate_study_plan")
    def test_create_study_plan_error(self, mock_gen, client, auth_headers):
        mock_gen.return_value = {"error": "OpenAI API failed"}
        response = client.post(
            "/api/v1/smartstudy/study-plans",
            json={"topic": "Sorting"},
            headers=auth_headers,
        )
        assert response.status_code == 500

    def test_create_study_plan_requires_auth(self, client):
        response = client.post(
            "/api/v1/smartstudy/study-plans",
            json={"topic": "Trees"},
        )
        assert response.status_code == 401


# ===================================================================
# GET /api/v1/smartstudy/study-plans
# ===================================================================

class TestListStudyPlans:

    def test_list_study_plans_empty(self, client, auth_headers):
        response = client.get(
            "/api/v1/smartstudy/study-plans",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_study_plans_with_data(self, client, auth_headers, study_plan_in_db):
        response = client.get(
            "/api/v1/smartstudy/study-plans",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["topic"] == "Binary Search Trees"
        assert "resources" in data[0]
        assert len(data[0]["resources"]) == 1

    def test_list_study_plans_active_only(self, client, auth_headers, study_plan_in_db):
        response = client.get(
            "/api/v1/smartstudy/study-plans?active_only=true",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_study_plans_requires_auth(self, client):
        response = client.get("/api/v1/smartstudy/study-plans")
        assert response.status_code == 401


# ===================================================================
# GET /api/v1/smartstudy/study-plans/{plan_id}
# ===================================================================

class TestGetStudyPlan:

    @patch("app.routes.smartstudy.study_plans.get_study_plan")
    def test_get_study_plan(self, mock_get, client, auth_headers, study_plan_in_db):
        plan_id = study_plan_in_db["plan_id"]
        mock_get.return_value = {
            "id": plan_id,
            "topic": "Binary Search Trees",
            "plan_data": {"days": []},
            "resources": [],
        }
        response = client.get(
            f"/api/v1/smartstudy/study-plans/{plan_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["topic"] == "Binary Search Trees"

    @patch("app.routes.smartstudy.study_plans.get_study_plan")
    def test_get_study_plan_not_found(self, mock_get, client, auth_headers):
        mock_get.return_value = None
        response = client.get(
            f"/api/v1/smartstudy/study-plans/{FAKE_UUID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# PATCH /api/v1/smartstudy/study-plans/{plan_id}
# ===================================================================

class TestUpdateStudyPlan:

    def test_update_completion(self, client, auth_headers, study_plan_in_db):
        plan_id = study_plan_in_db["plan_id"]
        response = client.patch(
            f"/api/v1/smartstudy/study-plans/{plan_id}",
            json={"completion_percentage": 50},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completion_percentage"] == 50.0
        assert data["is_active"] is True

    def test_update_auto_complete_at_100(self, client, auth_headers, study_plan_in_db):
        plan_id = study_plan_in_db["plan_id"]
        response = client.patch(
            f"/api/v1/smartstudy/study-plans/{plan_id}",
            json={"completion_percentage": 100},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completion_percentage"] == 100.0
        assert data["is_active"] is False

    def test_update_plan_not_found(self, client, auth_headers):
        response = client.patch(
            f"/api/v1/smartstudy/study-plans/{FAKE_UUID}",
            json={"completion_percentage": 50},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_plan_requires_auth(self, client, study_plan_in_db):
        plan_id = study_plan_in_db["plan_id"]
        response = client.patch(
            f"/api/v1/smartstudy/study-plans/{plan_id}",
            json={"completion_percentage": 50},
        )
        assert response.status_code == 401


# ===================================================================
# POST /api/v1/smartstudy/study-plans/{plan_id}/resources/{resource_id}/click
# ===================================================================

class TestResourceClick:

    def test_track_resource_click(self, client, auth_headers, study_plan_in_db):
        plan_id = study_plan_in_db["plan_id"]
        resource_id = study_plan_in_db["resource_id"]
        response = client.post(
            f"/api/v1/smartstudy/study-plans/{plan_id}/resources/{resource_id}/click",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "click" in response.json()["message"].lower()

    def test_click_plan_not_found(self, client, auth_headers, study_plan_in_db):
        resource_id = study_plan_in_db["resource_id"]
        response = client.post(
            f"/api/v1/smartstudy/study-plans/{FAKE_UUID}/resources/{resource_id}/click",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_click_resource_not_found(self, client, auth_headers, study_plan_in_db):
        plan_id = study_plan_in_db["plan_id"]
        response = client.post(
            f"/api/v1/smartstudy/study-plans/{plan_id}/resources/{FAKE_UUID}/click",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# POST /api/v1/smartstudy/study-plans/{plan_id}/resources/{resource_id}/complete
# ===================================================================

class TestResourceComplete:

    def test_mark_resource_complete(self, client, auth_headers, study_plan_in_db):
        plan_id = study_plan_in_db["plan_id"]
        resource_id = study_plan_in_db["resource_id"]
        response = client.post(
            f"/api/v1/smartstudy/study-plans/{plan_id}/resources/{resource_id}/complete",
            json={"completed": True, "helpful_rating": 4},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "complete" in response.json()["message"].lower()

    def test_complete_plan_not_found(self, client, auth_headers, study_plan_in_db):
        resource_id = study_plan_in_db["resource_id"]
        response = client.post(
            f"/api/v1/smartstudy/study-plans/{FAKE_UUID}/resources/{resource_id}/complete",
            json={"completed": True},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_complete_resource_not_found(self, client, auth_headers, study_plan_in_db):
        plan_id = study_plan_in_db["plan_id"]
        response = client.post(
            f"/api/v1/smartstudy/study-plans/{plan_id}/resources/{FAKE_UUID}/complete",
            json={"completed": True},
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# POST /api/v1/smartstudy/video-notes
# ===================================================================

class TestCreateVideoNote:

    def test_create_video_note(self, client, auth_headers, study_plan_in_db):
        resource_id = study_plan_in_db["resource_id"]
        response = client.post(
            "/api/v1/smartstudy/video-notes",
            json={
                "resource_id": resource_id,
                "content": "Important concept at this point",
                "timestamp_seconds": 120,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Important concept at this point"
        assert data["timestamp_seconds"] == 120
        assert data["formatted_timestamp"] == "2:00"

    def test_create_note_resource_not_found(self, client, auth_headers):
        response = client.post(
            "/api/v1/smartstudy/video-notes",
            json={
                "resource_id": FAKE_UUID,
                "content": "Some note",
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_note_requires_auth(self, client, study_plan_in_db):
        resource_id = study_plan_in_db["resource_id"]
        response = client.post(
            "/api/v1/smartstudy/video-notes",
            json={"resource_id": resource_id, "content": "Note"},
        )
        assert response.status_code == 401


# ===================================================================
# GET /api/v1/smartstudy/video-notes/resource/{resource_id}
# ===================================================================

class TestGetVideoNotes:

    def test_get_notes_for_resource_empty(self, client, auth_headers, study_plan_in_db):
        resource_id = study_plan_in_db["resource_id"]
        response = client.get(
            f"/api/v1/smartstudy/video-notes/resource/{resource_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["notes"] == []

    def test_get_notes_after_creating(self, client, auth_headers, study_plan_in_db):
        resource_id = study_plan_in_db["resource_id"]
        # Create a note first
        client.post(
            "/api/v1/smartstudy/video-notes",
            json={
                "resource_id": resource_id,
                "content": "Test note",
                "timestamp_seconds": 60,
            },
            headers=auth_headers,
        )
        response = client.get(
            f"/api/v1/smartstudy/video-notes/resource/{resource_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1
        assert data["notes"][0]["content"] == "Test note"

    def test_get_notes_resource_not_found(self, client, auth_headers):
        response = client.get(
            f"/api/v1/smartstudy/video-notes/resource/{FAKE_UUID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# PUT /api/v1/smartstudy/video-notes/{note_id}
# ===================================================================

class TestUpdateVideoNote:

    def test_update_video_note(self, client, auth_headers, study_plan_in_db):
        resource_id = study_plan_in_db["resource_id"]
        # Create a note
        create_resp = client.post(
            "/api/v1/smartstudy/video-notes",
            json={
                "resource_id": resource_id,
                "content": "Original note",
                "timestamp_seconds": 30,
            },
            headers=auth_headers,
        )
        note_id = create_resp.json()["id"]

        # Update it
        response = client.put(
            f"/api/v1/smartstudy/video-notes/{note_id}",
            json={"content": "Updated note content"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated note content"

    def test_update_note_not_found(self, client, auth_headers):
        response = client.put(
            f"/api/v1/smartstudy/video-notes/{FAKE_UUID}",
            json={"content": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# DELETE /api/v1/smartstudy/video-notes/{note_id}
# ===================================================================

class TestDeleteVideoNote:

    def test_delete_video_note(self, client, auth_headers, study_plan_in_db):
        resource_id = study_plan_in_db["resource_id"]
        # Create a note
        create_resp = client.post(
            "/api/v1/smartstudy/video-notes",
            json={
                "resource_id": resource_id,
                "content": "Note to delete",
            },
            headers=auth_headers,
        )
        note_id = create_resp.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/v1/smartstudy/video-notes/{note_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_note_not_found(self, client, auth_headers):
        response = client.delete(
            f"/api/v1/smartstudy/video-notes/{FAKE_UUID}",
            headers=auth_headers,
        )
        assert response.status_code == 404


# ===================================================================
# PATCH /api/v1/smartstudy/study-plans/{plan_id} — before/after scores
# ===================================================================

class TestStudyPlanScoreUpdate:

    def test_patch_before_score(self, client, auth_headers, study_plan_in_db, db_session):
        plan_id = study_plan_in_db["plan_id"]
        response = client.patch(
            f"/api/v1/smartstudy/study-plans/{plan_id}",
            json={"before_score": 45.0},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["study_plan_id"] == plan_id

        # Expire cached objects so re-query sees the committed changes
        db_session.expire_all()
        from app.models.smartstudy import StudyPlan
        plan = db_session.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
        assert float(plan.before_score) == 45.0

    def test_patch_after_score_computes_effectiveness(self, client, auth_headers, study_plan_in_db, db_session):
        plan_id = study_plan_in_db["plan_id"]
        plan = study_plan_in_db["plan"]

        # Set before_score first
        plan.before_score = 40.0
        db_session.commit()

        # Now PATCH after_score
        response = client.patch(
            f"/api/v1/smartstudy/study-plans/{plan_id}",
            json={"after_score": 75.0},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Refresh and verify effectiveness_score = after - before = 35.0
        db_session.refresh(plan)
        assert float(plan.after_score) == 75.0
        assert float(plan.effectiveness_score) == 35.0

    def test_patch_both_scores(self, client, auth_headers, study_plan_in_db, db_session):
        plan_id = study_plan_in_db["plan_id"]
        plan = study_plan_in_db["plan"]

        response = client.patch(
            f"/api/v1/smartstudy/study-plans/{plan_id}",
            json={"before_score": 30.0, "after_score": 80.0},
            headers=auth_headers,
        )
        assert response.status_code == 200

        db_session.refresh(plan)
        assert float(plan.before_score) == 30.0
        assert float(plan.after_score) == 80.0
        assert float(plan.effectiveness_score) == 50.0

    @patch("app.routes.smartstudy.study_plans.get_study_plan")
    def test_before_score_in_get_response(self, mock_get, client, auth_headers, study_plan_in_db, db_session):
        plan_id = study_plan_in_db["plan_id"]
        plan = study_plan_in_db["plan"]

        # Set before_score via PATCH
        client.patch(
            f"/api/v1/smartstudy/study-plans/{plan_id}",
            json={"before_score": 55.0},
            headers=auth_headers,
        )

        db_session.refresh(plan)

        # Mock the GET endpoint to return the plan data
        mock_get.return_value = {
            "id": plan_id,
            "topic": plan.topic,
            "plan_data": plan.plan_data,
            "before_score": float(plan.before_score) if plan.before_score else None,
            "after_score": float(plan.after_score) if plan.after_score else None,
            "effectiveness_score": float(plan.effectiveness_score) if plan.effectiveness_score else None,
            "resources": [],
        }

        response = client.get(
            f"/api/v1/smartstudy/study-plans/{plan_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["before_score"] == 55.0
