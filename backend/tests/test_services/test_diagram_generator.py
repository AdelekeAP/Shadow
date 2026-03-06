"""
Tests for diagram_generator service
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.services.diagram_generator import (
    resolve_department,
    parse_diagram_json,
    generate_diagram,
    DEPARTMENT_PREFIXES,
)


# ============================================================================
# resolve_department
# ============================================================================

class TestResolveDepartment:
    """Tests for department resolution from course codes."""

    def test_known_codes(self):
        assert resolve_department("CSC401") == "Computer Science"
        assert resolve_department("LAW301") == "Law"
        assert resolve_department("MED200") == "Medicine"
        assert resolve_department("BUS100") == "Business Administration"
        assert resolve_department("ECO201") == "Economics"
        assert resolve_department("PHY301") == "Physics"
        assert resolve_department("MTH401") == "Mathematics"

    def test_case_insensitive(self):
        assert resolve_department("csc401") == "Computer Science"
        assert resolve_department("Law301") == "Law"

    def test_unknown_prefix_no_db(self):
        assert resolve_department("XYZ999") == "General"

    def test_none_course_code(self):
        assert resolve_department(None) == "General"

    def test_empty_course_code(self):
        assert resolve_department("") == "General"

    def test_unknown_fallback_with_db(self):
        """DB query fallback when prefix is unknown."""
        mock_db = MagicMock()
        mock_course = MagicMock()
        mock_course.department = "Fine Arts"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_course

        result = resolve_department("ART101", mock_db)
        assert result == "Fine Arts"

    def test_db_fallback_no_match(self):
        """DB query returns nothing — falls back to General."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = resolve_department("ZZZ999", mock_db)
        assert result == "General"

    def test_db_fallback_exception(self):
        """DB query raises — falls back to General gracefully."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("DB down")

        result = resolve_department("ZZZ999", mock_db)
        assert result == "General"


# ============================================================================
# parse_diagram_json
# ============================================================================

VALID_DIAGRAM_JSON = json.dumps({
    "title": "Test Diagram",
    "diagram_type": "tree",
    "summary": "A test diagram",
    "nodes": [
        {"id": "n1", "label": "Root Node", "detail": "This is the root.", "type": "concept", "level": 0},
        {"id": "n2", "label": "Child Node", "detail": "This is a child.", "type": "process", "level": 1},
    ],
    "edges": [
        {"from": "n1", "to": "n2", "label": "connects to", "style": "solid"},
    ],
})


class TestParseDiagramJson:
    """Tests for GPT response parsing and validation."""

    def test_valid_json(self):
        result = parse_diagram_json(VALID_DIAGRAM_JSON)
        assert result["title"] == "Test Diagram"
        assert result["diagram_type"] == "tree"
        assert len(result["nodes"]) == 2
        assert len(result["edges"]) == 1

    def test_strips_markdown_fences(self):
        wrapped = f"```json\n{VALID_DIAGRAM_JSON}\n```"
        result = parse_diagram_json(wrapped)
        assert result["title"] == "Test Diagram"

    def test_strips_plain_fences(self):
        wrapped = f"```\n{VALID_DIAGRAM_JSON}\n```"
        result = parse_diagram_json(wrapped)
        assert result["title"] == "Test Diagram"

    def test_too_many_nodes_rejected(self):
        data = {
            "title": "Big",
            "diagram_type": "tree",
            "summary": "Too many nodes",
            "nodes": [
                {"id": f"n{i}", "label": f"Node {i}", "detail": "Detail", "type": "concept", "level": 0}
                for i in range(13)
            ],
            "edges": [],
        }
        with pytest.raises(ValueError, match="Maximum 12 nodes"):
            parse_diagram_json(json.dumps(data))

    def test_too_few_nodes_rejected(self):
        data = {
            "title": "Small",
            "diagram_type": "tree",
            "summary": "Too few",
            "nodes": [
                {"id": "n1", "label": "Only", "detail": "One node", "type": "concept", "level": 0},
            ],
            "edges": [],
        }
        with pytest.raises(ValueError, match="at least 2 nodes"):
            parse_diagram_json(json.dumps(data))

    def test_invalid_edge_refs_rejected(self):
        data = {
            "title": "Bad Edges",
            "diagram_type": "flow",
            "summary": "Invalid edge references",
            "nodes": [
                {"id": "n1", "label": "Node A", "detail": "Detail", "type": "concept", "level": 0},
                {"id": "n2", "label": "Node B", "detail": "Detail", "type": "concept", "level": 1},
            ],
            "edges": [
                {"from": "n1", "to": "n99", "style": "solid"},
            ],
        }
        with pytest.raises(ValueError, match="unknown node"):
            parse_diagram_json(json.dumps(data))

    def test_coerces_missing_style(self):
        data = {
            "title": "Coerce",
            "diagram_type": "tree",
            "summary": "Missing styles",
            "nodes": [
                {"id": "n1", "label": "A", "detail": "D", "type": "concept", "level": 0},
                {"id": "n2", "label": "B", "detail": "D", "type": "concept", "level": 1},
            ],
            "edges": [
                {"from": "n1", "to": "n2"},
            ],
        }
        result = parse_diagram_json(json.dumps(data))
        assert result["edges"][0]["style"] == "solid"

    def test_coerces_unknown_node_type(self):
        data = {
            "title": "Coerce",
            "diagram_type": "tree",
            "summary": "Unknown type",
            "nodes": [
                {"id": "n1", "label": "A", "detail": "D", "type": "unknown_type", "level": 0},
                {"id": "n2", "label": "B", "detail": "D", "type": "concept", "level": 1},
            ],
            "edges": [],
        }
        result = parse_diagram_json(json.dumps(data))
        assert result["nodes"][0]["type"] == "concept"

    def test_missing_title_rejected(self):
        data = {
            "diagram_type": "tree",
            "summary": "No title",
            "nodes": [
                {"id": "n1", "label": "A", "detail": "D", "type": "concept", "level": 0},
                {"id": "n2", "label": "B", "detail": "D", "type": "concept", "level": 1},
            ],
            "edges": [],
        }
        with pytest.raises(ValueError, match="title"):
            parse_diagram_json(json.dumps(data))

    def test_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            parse_diagram_json("not json at all")

    def test_invalid_diagram_type(self):
        data = {
            "title": "Bad type",
            "diagram_type": "hexagonal",
            "summary": "Invalid",
            "nodes": [
                {"id": "n1", "label": "A", "detail": "D", "type": "concept", "level": 0},
                {"id": "n2", "label": "B", "detail": "D", "type": "concept", "level": 1},
            ],
            "edges": [],
        }
        with pytest.raises(ValueError, match="Invalid diagram_type"):
            parse_diagram_json(json.dumps(data))


# ============================================================================
# generate_diagram (integration-level with mocks)
# ============================================================================

class TestGenerateDiagram:
    """Tests for the main generate_diagram function."""

    @patch("app.services.diagram_generator.cache_get")
    def test_cached_hit(self, mock_cache_get):
        """Cache hit returns cached data with cached=True."""
        cached_data = {
            "title": "Cached",
            "diagram_type": "tree",
            "summary": "From cache",
            "nodes": [{"id": "n1"}, {"id": "n2"}],
            "edges": [],
        }
        mock_cache_get.return_value = cached_data

        result = generate_diagram(
            db=MagicMock(),
            user_id="user-123",
            topic="Test Topic",
        )
        assert result["cached"] is True
        assert result["title"] == "Cached"
        mock_cache_get.assert_called_once()

    @patch("app.services.diagram_generator.cache_set")
    @patch("app.services.diagram_generator.cache_get", return_value=None)
    @patch("app.services.diagram_generator.call_with_retry")
    def test_fresh_generation(self, mock_call, mock_cache_get, mock_cache_set):
        """Cache miss triggers GPT call, caches result."""
        gpt_response = MagicMock()
        gpt_response.choices = [MagicMock()]
        gpt_response.choices[0].message.content = VALID_DIAGRAM_JSON
        mock_call.return_value = gpt_response

        result = generate_diagram(
            db=MagicMock(),
            user_id="user-456",
            topic="Binary Trees",
            course_code="CSC401",
            diagram_type="tree",
        )

        assert result["cached"] is False
        assert result["title"] == "Test Diagram"
        assert len(result["nodes"]) == 2
        mock_call.assert_called_once()
        mock_cache_set.assert_called_once()

    @patch("app.services.diagram_generator.cache_get", return_value=None)
    @patch("app.services.diagram_generator.call_with_retry")
    def test_gpt_invalid_json_raises(self, mock_call, mock_cache_get):
        """GPT returns invalid JSON — ValueError propagates."""
        gpt_response = MagicMock()
        gpt_response.choices = [MagicMock()]
        gpt_response.choices[0].message.content = "not valid json"
        mock_call.return_value = gpt_response

        with pytest.raises(Exception):
            generate_diagram(
                db=MagicMock(),
                user_id="user-789",
                topic="Bad Response",
            )
