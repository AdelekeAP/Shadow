"""
Tests for diagram API routes
"""
import pytest
from unittest.mock import patch, MagicMock


# ============================================================================
# POST /api/v1/smartstudy/diagrams/
# ============================================================================

class TestCreateDiagramRoute:
    """Tests for the diagram generation endpoint."""

    @patch("app.services.diagram_generator.generate_diagram")
    def test_create_diagram_success(self, mock_generate, client, auth_headers):
        """Authenticated request with valid data returns 200."""
        mock_generate.return_value = {
            "title": "Test Diagram",
            "diagram_type": "tree",
            "summary": "A test diagram",
            "nodes": [
                {"id": "n1", "label": "Root", "detail": "Root node", "type": "concept", "level": 0},
                {"id": "n2", "label": "Child", "detail": "Child node", "type": "process", "level": 1},
            ],
            "edges": [
                {"from": "n1", "to": "n2", "label": None, "style": "solid"},
            ],
            "cached": False,
        }

        response = client.post(
            "/api/v1/smartstudy/diagrams/",
            json={"topic": "Binary Search Trees"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Diagram"
        assert data["diagram_type"] == "tree"
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        assert data["cached"] is False

    def test_create_diagram_unauthenticated(self, client):
        """Request without auth token returns 401 or 422."""
        response = client.post(
            "/api/v1/smartstudy/diagrams/",
            json={"topic": "Test"},
        )
        # FastAPI returns 422 when required Header is missing
        assert response.status_code in (401, 422)

    def test_create_diagram_invalid_type(self, client, auth_headers):
        """Invalid diagram_type returns 422."""
        response = client.post(
            "/api/v1/smartstudy/diagrams/",
            json={"topic": "Test", "diagram_type": "hexagonal"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_diagram_empty_topic(self, client, auth_headers):
        """Empty topic returns 422."""
        response = client.post(
            "/api/v1/smartstudy/diagrams/",
            json={"topic": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_diagram_missing_topic(self, client, auth_headers):
        """Missing topic field returns 422."""
        response = client.post(
            "/api/v1/smartstudy/diagrams/",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @patch("app.services.diagram_generator.generate_diagram")
    def test_create_diagram_with_all_fields(self, mock_generate, client, auth_headers):
        """Request with all optional fields works."""
        mock_generate.return_value = {
            "title": "Full Request",
            "diagram_type": "flow",
            "summary": "All fields provided",
            "nodes": [
                {"id": "n1", "label": "Start", "detail": "Begin here", "type": "process", "level": 0},
                {"id": "n2", "label": "End", "detail": "Finish here", "type": "outcome", "level": 1},
            ],
            "edges": [{"from": "n1", "to": "n2", "label": "leads to", "style": "bold"}],
            "cached": False,
        }

        response = client.post(
            "/api/v1/smartstudy/diagrams/",
            json={
                "topic": "Negligence in Tort Law",
                "course_code": "LAW301",
                "diagram_type": "flow",
                "context_hint": "Focus on Nigerian case law",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["diagram_type"] == "flow"

    @patch("app.services.diagram_generator.generate_diagram")
    def test_create_diagram_service_error(self, mock_generate, client, auth_headers):
        """Service exception returns 500."""
        mock_generate.side_effect = Exception("OpenAI down")

        response = client.post(
            "/api/v1/smartstudy/diagrams/",
            json={"topic": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 500
