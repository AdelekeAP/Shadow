"""
Tests for Library Service
backend/app/services/library_service.py

Tests cover: calculate_file_hash (pure), browse_library, vote_on_document,
increment_view_count, increment_download_count, get_user_contributions,
check_duplicate_document (all DB-backed).

NOTE: Because the test suite uses SQLite (not PostgreSQL), UUID columns require
actual uuid.UUID objects rather than plain strings. We pass UUID objects for all
function arguments that feed into SQLAlchemy filter clauses.
"""
import uuid
import pytest

from app.models.library import LibraryDocument, LibraryVote
from app.services.library_service import (
    calculate_file_hash,
    check_duplicate_document,
    check_content_course_relevance,
    sanitize_filename,
    validate_file_magic_bytes,
    browse_library,
    vote_on_document,
    increment_view_count,
    increment_download_count,
    get_user_contributions,
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
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def library_doc(db_session, test_user, test_course):
    """Create a single public library document for tests."""
    doc = LibraryDocument(
        course_id=test_course.id,
        topic="Binary Search Trees",
        file_name="bst_lecture.pdf",
        file_path="library/CSC401/bst_lecture.pdf",
        file_type="pdf",
        file_size=2048,
        content_hash="a" * 64,
        uploaded_by=test_user.id,
        is_public=True,
        view_count=5,
        download_count=2,
        helpful_votes=3,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


@pytest.fixture
def second_library_doc(db_session, test_user, test_course):
    """A second document for filtering/counting tests."""
    doc = LibraryDocument(
        course_id=test_course.id,
        topic="Sorting Algorithms",
        file_name="sorting_notes.pdf",
        file_path="library/CSC401/sorting_notes.pdf",
        file_type="pdf",
        file_size=4096,
        content_hash="b" * 64,
        uploaded_by=test_user.id,
        is_public=True,
        view_count=10,
        download_count=7,
        helpful_votes=1,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)
    return doc


# ---------------------------------------------------------------------------
# calculate_file_hash  (pure function)
# ---------------------------------------------------------------------------

class TestCalculateFileHash:

    def test_returns_64_char_hex_string(self):
        h = calculate_file_hash(b"hello world")
        assert isinstance(h, str)
        assert len(h) == 64
        # Should be valid hex
        int(h, 16)

    def test_different_content_different_hashes(self):
        h1 = calculate_file_hash(b"content A")
        h2 = calculate_file_hash(b"content B")
        assert h1 != h2

    def test_same_content_same_hash(self):
        content = b"exact same bytes"
        assert calculate_file_hash(content) == calculate_file_hash(content)


# ---------------------------------------------------------------------------
# browse_library  (DB tests)
# ---------------------------------------------------------------------------

class TestBrowseLibrary:

    def test_empty_db_returns_empty_list(self, db_session):
        result = browse_library(db_session)
        assert isinstance(result, dict)
        assert result["documents"] == []
        assert result["total"] == 0
        assert result["has_more"] is False

    def test_returns_documents(self, db_session, library_doc):
        result = browse_library(db_session)
        assert len(result["documents"]) == 1
        assert result["documents"][0]["topic"] == "Binary Search Trees"

    def test_filter_by_course_id(self, db_session, library_doc, test_course):
        # Matching course -- pass UUID object for SQLite compatibility
        result = browse_library(db_session, course_id=test_course.id)
        assert len(result["documents"]) == 1

        # Non-matching course
        result = browse_library(db_session, course_id=uuid.uuid4())
        assert len(result["documents"]) == 0

    def test_search_query_filter(self, db_session, library_doc, second_library_doc):
        result = browse_library(db_session, search_query="Binary")
        assert len(result["documents"]) == 1
        assert result["documents"][0]["topic"] == "Binary Search Trees"

    def test_search_query_by_filename(self, db_session, library_doc, second_library_doc):
        result = browse_library(db_session, search_query="sorting")
        assert len(result["documents"]) == 1
        assert result["documents"][0]["file_name"] == "sorting_notes.pdf"


# ---------------------------------------------------------------------------
# vote_on_document
# ---------------------------------------------------------------------------

class TestVoteOnDocument:

    def test_nonexistent_document_returns_false(self, db_session, test_user):
        result = vote_on_document(db_session, test_user.id, uuid.uuid4(), 1)
        assert result is False

    def test_new_upvote(self, db_session, test_user, library_doc):
        initial_votes = library_doc.helpful_votes
        result = vote_on_document(db_session, test_user.id, library_doc.id, 1)
        assert result is True
        db_session.refresh(library_doc)
        assert library_doc.helpful_votes == initial_votes + 1

    def test_update_existing_vote(self, db_session, test_user, library_doc):
        # First vote: upvote (+1)
        vote_on_document(db_session, test_user.id, library_doc.id, 1)
        db_session.refresh(library_doc)
        after_upvote = library_doc.helpful_votes

        # Change to downvote (-1)
        vote_on_document(db_session, test_user.id, library_doc.id, -1)
        db_session.refresh(library_doc)
        # Should decrease by 2: remove +1 and apply -1
        assert library_doc.helpful_votes == after_upvote - 2


# ---------------------------------------------------------------------------
# increment_view_count
# ---------------------------------------------------------------------------

class TestIncrementViewCount:

    def test_increments(self, db_session, library_doc):
        old = library_doc.view_count
        result = increment_view_count(db_session, library_doc.id)
        assert result is True
        db_session.refresh(library_doc)
        assert library_doc.view_count == old + 1

    def test_nonexistent_doc_returns_false(self, db_session):
        result = increment_view_count(db_session, uuid.uuid4())
        assert result is False


# ---------------------------------------------------------------------------
# increment_download_count
# ---------------------------------------------------------------------------

class TestIncrementDownloadCount:

    def test_increments(self, db_session, library_doc):
        old = library_doc.download_count
        result = increment_download_count(db_session, library_doc.id)
        assert result is True
        db_session.refresh(library_doc)
        assert library_doc.download_count == old + 1

    def test_nonexistent_doc_returns_false(self, db_session):
        result = increment_download_count(db_session, uuid.uuid4())
        assert result is False


# ---------------------------------------------------------------------------
# get_user_contributions
# ---------------------------------------------------------------------------

class TestGetUserContributions:

    def test_no_documents_returns_zeros(self, db_session, test_user):
        result = get_user_contributions(db_session, test_user.id)
        assert result["total_documents"] == 0
        assert result["total_views"] == 0
        assert result["total_downloads"] == 0
        assert result["total_helpful_votes"] == 0

    def test_with_documents(self, db_session, test_user, library_doc, second_library_doc):
        result = get_user_contributions(db_session, test_user.id)
        assert result["total_documents"] == 2
        assert result["total_views"] == 5 + 10
        assert result["total_downloads"] == 2 + 7
        assert result["total_helpful_votes"] == 3 + 1


# ---------------------------------------------------------------------------
# check_duplicate_document
# ---------------------------------------------------------------------------

class TestCheckDuplicateDocument:

    def test_no_match_returns_none(self, db_session, test_course):
        result = check_duplicate_document(db_session, "x" * 64, test_course.id)
        assert result is None

    def test_matching_hash_returns_document(self, db_session, test_course, library_doc):
        result = check_duplicate_document(
            db_session, "a" * 64, test_course.id
        )
        assert result is not None
        assert str(result.id) == str(library_doc.id)


# ---------------------------------------------------------------------------
# sanitize_filename  (pure function — path traversal prevention)
# ---------------------------------------------------------------------------

class TestSanitizeFilename:

    def test_strips_directory_components(self):
        # os.path.basename strips directory traversal, leaving just "passwd"
        assert sanitize_filename("../../etc/passwd") == "passwd"

    def test_strips_windows_traversal(self):
        result = sanitize_filename("..\\..\\windows\\system32\\cmd.exe")
        assert ".." not in result
        assert "\\" not in result

    def test_removes_dangerous_characters(self):
        result = sanitize_filename("file<script>.pdf")
        assert "<" not in result
        assert ">" not in result

    def test_preserves_safe_names(self):
        assert sanitize_filename("CSC401_Week5_BST.pdf") == "CSC401_Week5_BST.pdf"

    def test_empty_input_returns_unnamed(self):
        assert sanitize_filename("") == "unnamed_document"

    def test_only_dots_returns_unnamed(self):
        assert sanitize_filename("....") == "unnamed_document"

    def test_collapses_multiple_underscores(self):
        result = sanitize_filename("a___b___c.pdf")
        assert "___" not in result


# ---------------------------------------------------------------------------
# validate_file_magic_bytes  (pure function)
# ---------------------------------------------------------------------------

class TestValidateFileMagicBytes:

    def test_valid_pdf(self):
        assert validate_file_magic_bytes(b"%PDF-1.4 rest of file", "pdf") is True

    def test_valid_pptx(self):
        assert validate_file_magic_bytes(b"PK\x03\x04 rest of zip", "pptx") is True

    def test_valid_ppt(self):
        assert validate_file_magic_bytes(b"\xd0\xcf\x11\xe0 rest of OLE", "ppt") is True

    def test_rejects_fake_pdf(self):
        assert validate_file_magic_bytes(b"Not a PDF at all", "pdf") is False

    def test_rejects_exe_as_pdf(self):
        assert validate_file_magic_bytes(b"MZ\x90\x00", "pdf") is False

    def test_rejects_unknown_type(self):
        assert validate_file_magic_bytes(b"%PDF-1.4", "exe") is False

    def test_empty_content(self):
        assert validate_file_magic_bytes(b"", "pdf") is False


# ---------------------------------------------------------------------------
# check_content_course_relevance  (pure function)
# ---------------------------------------------------------------------------

class TestCheckContentCourseRelevance:

    def test_matching_content_returns_none(self):
        text = "This lecture covers binary search trees in computer science algorithms"
        result = check_content_course_relevance(text, "CSC401", "Computer Science Algorithms")
        assert result is None

    def test_unrelated_content_returns_warning(self):
        text = "Marketing strategy and brand management for consumer products in the retail sector"
        result = check_content_course_relevance(text, "CSC401", "Computer Architecture")
        assert result is not None
        assert "CSC401" in result

    def test_short_text_returns_none(self):
        """Text too short to judge should not produce a warning."""
        result = check_content_course_relevance("short", "CSC401", "Computer Science")
        assert result is None

    def test_empty_text_returns_none(self):
        result = check_content_course_relevance("", "CSC401", "Computer Science")
        assert result is None

    def test_course_code_in_text_matches(self):
        text = "CSC401 lecture notes on operating systems and process scheduling"
        result = check_content_course_relevance(text, "CSC401", "Operating Systems")
        assert result is None

    def test_partial_title_match_returns_none(self):
        """Even one keyword match should avoid warning."""
        text = "This document discusses various algorithms and data structures"
        result = check_content_course_relevance(text, "CSC401", "Algorithms and Data Structures")
        assert result is None


# ---------------------------------------------------------------------------
# vote_on_document — invalid vote value
# ---------------------------------------------------------------------------

class TestVoteOnDocumentValidation:

    def test_invalid_vote_value_returns_false(self, db_session, test_user, library_doc):
        assert vote_on_document(db_session, test_user.id, library_doc.id, 0) is False
        assert vote_on_document(db_session, test_user.id, library_doc.id, 2) is False
        assert vote_on_document(db_session, test_user.id, library_doc.id, -5) is False


# ---------------------------------------------------------------------------
# browse_library — pagination
# ---------------------------------------------------------------------------

class TestBrowseLibraryPagination:

    def test_pagination_limit_and_offset(self, db_session, library_doc, second_library_doc):
        result = browse_library(db_session, limit=1, offset=0)
        assert len(result["documents"]) == 1
        assert result["total"] == 2
        assert result["has_more"] is True

        result2 = browse_library(db_session, limit=1, offset=1)
        assert len(result2["documents"]) == 1
        assert result2["has_more"] is False

    def test_sort_by_newest(self, db_session, library_doc, second_library_doc):
        result = browse_library(db_session, sort_by="newest")
        assert len(result["documents"]) == 2
        # Second doc was created after first, so should appear first
        assert result["documents"][0]["topic"] == "Sorting Algorithms"

    def test_sort_by_name(self, db_session, library_doc, second_library_doc):
        result = browse_library(db_session, sort_by="name")
        # Alphabetically: "Binary Search Trees" before "Sorting Algorithms"
        assert result["documents"][0]["topic"] == "Binary Search Trees"


# ---------------------------------------------------------------------------
# scan_status column
# ---------------------------------------------------------------------------

class TestScanStatusColumn:

    def test_default_scan_status_is_clean(self, db_session, test_user, test_course):
        doc = LibraryDocument(
            course_id=test_course.id,
            topic="Test Doc",
            file_name="test.pdf",
            file_path="library/test.pdf",
            file_type="pdf",
            file_size=1024,
            content_hash="c" * 64,
            uploaded_by=test_user.id,
            is_public=True,
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)
        assert doc.scan_status == "clean"

    def test_scan_status_in_to_dict(self, db_session, library_doc):
        d = library_doc.to_dict()
        assert "scan_status" in d
