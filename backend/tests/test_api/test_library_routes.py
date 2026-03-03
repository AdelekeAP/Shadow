"""
Integration tests for Library API routes
backend/app/routes/library.py

Tests library browsing, document retrieval, voting, contributions, and stats.
"""
import pytest


# ===================================================================
# GET /api/v1/library/browse
# ===================================================================

class TestBrowseLibrary:

    def test_browse_library_empty(self, client, auth_headers):
        """Browse library with no documents returns an empty list"""
        response = client.get("/api/v1/library/browse", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_browse_library_with_documents(self, client, auth_headers, library_document_in_db):
        """Browse library returns existing documents"""
        response = client.get("/api/v1/library/browse", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        doc = data[0]
        assert doc["topic"] == "Binary Search Trees"
        assert doc["file_name"] == "BST_lecture.pdf"
        assert doc["file_type"] == "pdf"
        assert doc["is_public"] is True
        assert doc["helpful_votes"] == 5
        assert doc["view_count"] == 10
        assert doc["download_count"] == 3
        assert doc["course_code"] == "CSC401"
        assert doc["uploader_name"] == "Test Student"

    def test_browse_library_with_search(self, client, auth_headers, library_document_in_db):
        """Search filter matches documents by topic"""
        response = client.get(
            "/api/v1/library/browse?search=Binary",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Binary" in data[0]["topic"]

    def test_browse_library_search_no_match(self, client, auth_headers, library_document_in_db):
        """Search filter that matches nothing returns empty list"""
        response = client.get(
            "/api/v1/library/browse?search=QuantumPhysics",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_browse_library_unauthenticated(self, client):
        """Browsing without auth token is rejected"""
        response = client.get("/api/v1/library/browse")
        assert response.status_code in [401, 403]


# ===================================================================
# GET /api/v1/library/documents/{document_id}
# ===================================================================

class TestGetDocument:

    def test_get_document(self, client, auth_headers, library_document_in_db):
        """Retrieve a single document by ID"""
        doc_id = library_document_in_db["document_id"]
        response = client.get(
            f"/api/v1/library/documents/{doc_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert data["topic"] == "Binary Search Trees"
        assert data["course_code"] == "CSC401"
        assert data["uploader_name"] == "Test Student"
        # View count should have been incremented
        assert data["view_count"] >= 10

    def test_get_document_not_found(self, client, auth_headers):
        """Request for non-existent document returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/api/v1/library/documents/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ===================================================================
# POST /api/v1/library/documents/{document_id}/vote
# ===================================================================

class TestVoteOnDocument:

    def test_vote_on_document_self_vote_rejected(self, client, auth_headers, library_document_in_db):
        """Users cannot vote on their own documents"""
        doc_id = library_document_in_db["document_id"]
        response = client.post(
            f"/api/v1/library/documents/{doc_id}/vote",
            json={"vote_value": 1},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "cannot vote on your own documents" in response.json()["detail"].lower()


# ===================================================================
# GET /api/v1/library/my-contributions
# ===================================================================

class TestMyContributions:

    def test_get_my_contributions_empty(self, client, auth_headers):
        """Contributions stats with no uploads"""
        response = client.get("/api/v1/library/my-contributions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 0
        assert data["total_views"] == 0
        assert data["total_downloads"] == 0
        assert data["total_helpful_votes"] == 0
        assert data["documents"] == []

    def test_get_my_contributions_with_upload(self, client, auth_headers, library_document_in_db):
        """Contributions stats reflect the uploaded document"""
        response = client.get("/api/v1/library/my-contributions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 1
        assert data["total_views"] == 10
        assert data["total_downloads"] == 3
        assert data["total_helpful_votes"] == 5
        assert len(data["documents"]) == 1


# ===================================================================
# GET /api/v1/library/stats
# ===================================================================

class TestLibraryStats:

    def test_get_library_stats(self, client, auth_headers):
        """Stats endpoint returns expected shape when library is empty"""
        response = client.get("/api/v1/library/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "total_contributors" in data
        assert "popular_courses" in data
        assert "most_helpful_documents" in data
        assert data["total_documents"] == 0
        assert data["total_contributors"] == 0

    def test_get_library_stats_with_data(self, client, auth_headers, library_document_in_db):
        """Stats endpoint reflects existing documents"""
        response = client.get("/api/v1/library/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 1
        assert data["total_contributors"] == 1
        assert len(data["most_helpful_documents"]) == 1

    def test_get_library_stats_unauthenticated(self, client):
        """Stats without auth is rejected"""
        response = client.get("/api/v1/library/stats")
        assert response.status_code in [401, 403]
