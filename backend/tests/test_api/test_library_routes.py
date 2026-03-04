"""
Integration tests for Library API routes
backend/app/routes/library.py

Tests library browsing, document retrieval, voting, contributions, and stats.
"""
import pytest


# ---------------------------------------------------------------------------
# Second-user fixtures for cross-user tests (e.g. voting on another user's doc)
# ---------------------------------------------------------------------------

@pytest.fixture
def second_registered_user(client):
    """Register a second test user"""
    user_data = {
        "email": "student2@pau.edu.ng",
        "password": "SecurePass456!",
        "full_name": "Second Student",
        "university_id": "PAU/2022/099",
        "entry_level": "400L",
        "target_cgpa": 4.0,
        "current_cgpa": 3.5,
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201, f"Registration failed: {response.text}"
    return response.json()


@pytest.fixture
def second_auth_headers(second_registered_user):
    """Auth headers for the second user"""
    token = second_registered_user["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ===================================================================
# GET /api/v1/library/browse
# ===================================================================

class TestBrowseLibrary:

    def test_browse_library_empty(self, client, auth_headers):
        """Browse library with no documents returns an empty list"""
        response = client.get("/api/v1/library/browse", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data["documents"], list)
        assert len(data["documents"]) == 0
        assert data["total"] == 0
        assert data["has_more"] is False

    def test_browse_library_with_documents(self, client, auth_headers, library_document_in_db):
        """Browse library returns existing documents"""
        response = client.get("/api/v1/library/browse", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert isinstance(data["documents"], list)
        assert len(data["documents"]) == 1
        doc = data["documents"][0]
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
        assert len(data["documents"]) == 1
        assert "Binary" in data["documents"][0]["topic"]

    def test_browse_library_search_no_match(self, client, auth_headers, library_document_in_db):
        """Search filter that matches nothing returns empty list"""
        response = client.get(
            "/api/v1/library/browse?search=QuantumPhysics",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 0

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

    def test_vote_on_document_success(self, client, second_auth_headers, library_document_in_db):
        """A different user can upvote a document"""
        doc_id = library_document_in_db["document_id"]
        response = client.post(
            f"/api/v1/library/documents/{doc_id}/vote",
            json={"vote_value": 1},
            headers=second_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_vote_on_document_downvote(self, client, second_auth_headers, library_document_in_db):
        """A different user can downvote a document"""
        doc_id = library_document_in_db["document_id"]
        response = client.post(
            f"/api/v1/library/documents/{doc_id}/vote",
            json={"vote_value": -1},
            headers=second_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_vote_on_document_change_vote(self, client, second_auth_headers, library_document_in_db):
        """User can change their vote from upvote to downvote"""
        doc_id = library_document_in_db["document_id"]
        # First: upvote
        client.post(
            f"/api/v1/library/documents/{doc_id}/vote",
            json={"vote_value": 1},
            headers=second_auth_headers,
        )
        # Then: change to downvote
        response = client.post(
            f"/api/v1/library/documents/{doc_id}/vote",
            json={"vote_value": -1},
            headers=second_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_vote_on_nonexistent_document(self, client, second_auth_headers):
        """Voting on a non-existent document returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.post(
            f"/api/v1/library/documents/{fake_id}/vote",
            json={"vote_value": 1},
            headers=second_auth_headers,
        )
        assert response.status_code == 404

    def test_vote_invalid_value(self, client, second_auth_headers, library_document_in_db):
        """Invalid vote values are rejected (400 from route or 422 from schema)"""
        doc_id = library_document_in_db["document_id"]
        response = client.post(
            f"/api/v1/library/documents/{doc_id}/vote",
            json={"vote_value": 5},
            headers=second_auth_headers,
        )
        assert response.status_code in [400, 422]


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


# ===================================================================
# Access Control tests
# ===================================================================

class TestAccessControl:

    def test_private_document_visible_to_owner_in_browse(self, db_session, client, auth_headers, registered_user, course_in_db):
        """Uploaders should see their own private documents in browse results"""
        from app.models.library import LibraryDocument
        import uuid as _uuid
        import hashlib

        # Create a private document uploaded by the authenticated user
        doc = LibraryDocument(
            course_id=course_in_db["course"].id,
            topic="Private Notes",
            file_name="private.pdf",
            file_path="/tmp/fake/private.pdf",
            file_type="pdf",
            file_size=512,
            content_hash=hashlib.sha256(b"private content").hexdigest(),
            uploaded_by=_uuid.UUID(registered_user["user"]["id"]),
            is_public=False,
        )
        db_session.add(doc)
        db_session.commit()

        response = client.get("/api/v1/library/browse", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Owner should see their own private document
        topics = [d["topic"] for d in data["documents"]]
        assert "Private Notes" in topics

    def test_private_document_hidden_from_other_users(self, db_session, client, auth_headers, course_in_db):
        """Private documents should not appear in browse results for other users"""
        from app.models.library import LibraryDocument
        from app.models.user import User
        from passlib.context import CryptContext
        import uuid as _uuid
        import hashlib

        # Create a different user who owns the private document
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        other_user = User(
            id=_uuid.uuid4(),
            email="otheruser@pau.edu.ng",
            password_hash=pwd_context.hash("TestPass123!"),
            full_name="Other User",
            entry_level="400L",
        )
        db_session.add(other_user)
        db_session.commit()

        # Create a private document uploaded by the other user
        doc = LibraryDocument(
            course_id=course_in_db["course"].id,
            topic="Someone Elses Private Notes",
            file_name="other_private.pdf",
            file_path="/tmp/fake/other_private.pdf",
            file_type="pdf",
            file_size=512,
            content_hash=hashlib.sha256(b"other private content").hexdigest(),
            uploaded_by=other_user.id,
            is_public=False,
        )
        db_session.add(doc)
        db_session.commit()

        response = client.get("/api/v1/library/browse", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Other user's private doc should not appear
        topics = [d["topic"] for d in data["documents"]]
        assert "Someone Elses Private Notes" not in topics

    def test_browse_with_invalid_sort_falls_back_to_helpful(self, client, auth_headers):
        """Invalid sort_by value should fall back to 'helpful' without error"""
        response = client.get("/api/v1/library/browse?sort_by=invalid_sort", headers=auth_headers)
        assert response.status_code == 200

    def test_browse_with_invalid_file_type_rejected(self, client, auth_headers):
        """Invalid file_type is rejected with 400"""
        response = client.get("/api/v1/library/browse?file_type=exe", headers=auth_headers)
        assert response.status_code == 400
