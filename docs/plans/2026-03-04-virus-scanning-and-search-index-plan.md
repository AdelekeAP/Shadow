# Virus Scanning & Full-Text Search Index Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add ClamAV virus scanning with quarantine model to library uploads, and GIN trigram indexes for fast full-text search.

**Architecture:** ClamAV daemon integration via `pyclamd` with graceful degradation — files are quarantined (not rejected) when ClamAV is unavailable, keeping SmartStudy uploads functional. PostgreSQL `pg_trgm` extension with GIN indexes accelerates existing ILIKE queries without code changes.

**Tech Stack:** pyclamd, ClamAV daemon, PostgreSQL pg_trgm, Alembic migrations

---

### Task 1: Virus Scan Service — Tests

**Files:**
- Create: `backend/tests/test_services/test_virus_scan_service.py`

**Step 1: Write the failing tests**

```python
"""
Tests for Virus Scan Service
backend/app/services/virus_scan_service.py

Tests cover: scan_bytes (with ClamAV available, unavailable, infected file),
get_scanner_status, scan_pending_documents.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.services.virus_scan_service import scan_bytes, get_scanner_status


class TestScanBytes:

    @patch("app.services.virus_scan_service._get_clamd")
    def test_clean_file_returns_clean(self, mock_get_clamd):
        mock_cd = MagicMock()
        mock_cd.scan_stream.return_value = None  # ClamAV returns None for clean
        mock_get_clamd.return_value = mock_cd

        result = scan_bytes(b"%PDF-1.4 some content")
        assert result["status"] == "clean"
        assert result["threat"] is None

    @patch("app.services.virus_scan_service._get_clamd")
    def test_infected_file_returns_infected(self, mock_get_clamd):
        mock_cd = MagicMock()
        mock_cd.scan_stream.return_value = {"stream": ("FOUND", "Win.Test.EICAR_HDB-1")}
        mock_get_clamd.return_value = mock_cd

        result = scan_bytes(b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR")
        assert result["status"] == "infected"
        assert "EICAR" in result["threat"]

    @patch("app.services.virus_scan_service._get_clamd")
    def test_clamd_unavailable_returns_pending(self, mock_get_clamd):
        mock_get_clamd.return_value = None

        result = scan_bytes(b"%PDF-1.4 content")
        assert result["status"] == "pending"
        assert result["threat"] is None

    @patch("app.services.virus_scan_service._get_clamd")
    def test_scan_error_returns_error(self, mock_get_clamd):
        mock_cd = MagicMock()
        mock_cd.scan_stream.side_effect = Exception("Connection reset")
        mock_get_clamd.return_value = mock_cd

        result = scan_bytes(b"%PDF-1.4 content")
        assert result["status"] == "error"


class TestGetScannerStatus:

    @patch("app.services.virus_scan_service._get_clamd")
    def test_available(self, mock_get_clamd):
        mock_cd = MagicMock()
        mock_cd.version.return_value = "ClamAV 1.0.0"
        mock_get_clamd.return_value = mock_cd

        result = get_scanner_status()
        assert result["available"] is True
        assert "1.0.0" in result["version"]

    @patch("app.services.virus_scan_service._get_clamd")
    def test_unavailable(self, mock_get_clamd):
        mock_get_clamd.return_value = None

        result = get_scanner_status()
        assert result["available"] is False
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_services/test_virus_scan_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.virus_scan_service'`

---

### Task 2: Virus Scan Service — Implementation

**Files:**
- Create: `backend/app/services/virus_scan_service.py`
- Modify: `backend/requirements.txt` — add `pyclamd==0.4.0`

**Step 1: Add pyclamd to requirements.txt**

Append after the `# Error tracking` section:

```
# Virus scanning
pyclamd==0.4.0
```

**Step 2: Create the virus scan service**

```python
"""
Virus Scan Service — ClamAV integration with graceful degradation

Scans uploaded files for malware using the ClamAV daemon (clamd).
When ClamAV is unavailable, files are quarantined (scan_status='pending')
rather than rejected, so SmartStudy uploads still work.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _get_clamd() -> Optional[Any]:
    """Get a ClamAV daemon connection, or None if unavailable."""
    try:
        import pyclamd
        cd = pyclamd.ClamdUnixSocket()
        if cd.ping():
            return cd
    except Exception:
        pass

    try:
        import pyclamd
        cd = pyclamd.ClamdNetworkSocket()
        if cd.ping():
            return cd
    except Exception:
        pass

    return None


def scan_bytes(file_content: bytes) -> Dict[str, Any]:
    """
    Scan file bytes for malware using ClamAV.

    Returns:
        Dict with keys:
        - status: 'clean' | 'infected' | 'pending' | 'error'
        - threat: threat name if infected, None otherwise
    """
    cd = _get_clamd()

    if cd is None:
        logger.warning("ClamAV daemon unavailable — file quarantined as pending")
        return {"status": "pending", "threat": None}

    try:
        result = cd.scan_stream(file_content)

        if result is None:
            return {"status": "clean", "threat": None}

        # result format: {'stream': ('FOUND', 'Win.Test.EICAR_HDB-1')}
        status_tuple = result.get("stream", ())
        if len(status_tuple) >= 2 and status_tuple[0] == "FOUND":
            threat_name = status_tuple[1]
            logger.warning(f"MALWARE DETECTED: {threat_name}")
            return {"status": "infected", "threat": threat_name}

        return {"status": "clean", "threat": None}

    except Exception as e:
        logger.error(f"ClamAV scan error: {e}")
        return {"status": "error", "threat": None}


def get_scanner_status() -> Dict[str, Any]:
    """Check if ClamAV is available and return version info."""
    cd = _get_clamd()
    if cd is None:
        return {"available": False, "version": None}

    try:
        version = cd.version()
        return {"available": True, "version": version}
    except Exception:
        return {"available": False, "version": None}


def scan_pending_documents(db) -> Dict[str, int]:
    """
    Scan all documents with scan_status 'pending' or 'error'.
    Call this when ClamAV comes back online.

    Returns:
        Dict with counts: cleaned, infected, failed
    """
    from app.models.library import LibraryDocument

    cd = _get_clamd()
    if cd is None:
        logger.warning("Cannot scan pending documents — ClamAV unavailable")
        return {"cleaned": 0, "infected": 0, "failed": 0}

    counts = {"cleaned": 0, "infected": 0, "failed": 0}

    pending_docs = db.query(LibraryDocument).filter(
        LibraryDocument.scan_status.in_(["pending", "error"])
    ).all()

    for doc in pending_docs:
        try:
            import os
            if not os.path.exists(doc.file_path):
                logger.warning(f"File missing for document {doc.id}: {doc.file_path}")
                counts["failed"] += 1
                continue

            with open(doc.file_path, "rb") as f:
                content = f.read()

            result = scan_bytes(content)

            if result["status"] == "clean":
                doc.scan_status = "clean"
                counts["cleaned"] += 1
            elif result["status"] == "infected":
                doc.scan_status = "infected"
                counts["infected"] += 1
                logger.warning(f"INFECTED document found: {doc.id} - {result['threat']}")
            else:
                counts["failed"] += 1

        except Exception as e:
            logger.error(f"Failed to scan document {doc.id}: {e}")
            counts["failed"] += 1

    db.commit()
    logger.info(f"Pending scan complete: {counts}")
    return counts
```

**Step 3: Run tests to verify they pass**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_services/test_virus_scan_service.py -v`
Expected: All 6 tests PASS

**Step 4: Commit**

```bash
git add backend/app/services/virus_scan_service.py backend/tests/test_services/test_virus_scan_service.py backend/requirements.txt
git commit -m "feat: add virus scan service with ClamAV integration and graceful degradation"
```

---

### Task 3: Add scan_status Column to Model

**Files:**
- Modify: `backend/app/models/library.py:46` — add scan_status column after extracted_text
- Modify: `backend/app/models/library.py:73-95` — add scan_status to to_dict()

**Step 1: Write failing test**

Add to `backend/tests/test_services/test_library_service.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_services/test_library_service.py::TestScanStatusColumn -v`
Expected: FAIL with `AttributeError: ... has no attribute 'scan_status'`

**Step 3: Add scan_status column to model**

In `backend/app/models/library.py`, after line 44 (`extracted_text` column), add:

```python
    scan_status = Column(String(10), nullable=False, server_default="clean", default="clean")  # clean, infected, pending, error
```

In `to_dict()` method, add after the `"is_verified"` line:

```python
            "scan_status": self.scan_status,
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_services/test_library_service.py::TestScanStatusColumn -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/library.py backend/tests/test_services/test_library_service.py
git commit -m "feat: add scan_status column to LibraryDocument model"
```

---

### Task 4: Integrate Virus Scanning into Upload Flow

**Files:**
- Modify: `backend/app/services/library_service.py:274-404` — add scan call in `contribute_to_library()`

**Step 1: Write failing test**

Add to `backend/tests/test_services/test_library_service.py`:

```python
from unittest.mock import patch


class TestContributeToLibraryWithScan:

    @patch("app.services.library_service.scan_bytes")
    def test_clean_file_gets_clean_status(self, mock_scan, db_session, test_user, test_course):
        mock_scan.return_value = {"status": "clean", "threat": None}
        result = contribute_to_library(
            db=db_session,
            user_id=str(test_user.id),
            course_id=str(test_course.id),
            topic="Clean Doc",
            file_content=b"%PDF-1.4 clean content",
            file_name="clean.pdf",
            file_type="pdf",
            extracted_text="some text",
        )
        assert result["success"] is True
        doc = db_session.query(LibraryDocument).filter(
            LibraryDocument.id == result["library_document_id"]
        ).first()
        assert doc.scan_status == "clean"

    @patch("app.services.library_service.scan_bytes")
    def test_infected_file_rejected(self, mock_scan, db_session, test_user, test_course):
        mock_scan.return_value = {"status": "infected", "threat": "Win.Test.EICAR"}
        result = contribute_to_library(
            db=db_session,
            user_id=str(test_user.id),
            course_id=str(test_course.id),
            topic="Bad Doc",
            file_content=b"%PDF-1.4 bad content",
            file_name="bad.pdf",
            file_type="pdf",
            extracted_text="bad text",
        )
        assert result["success"] is False
        assert "malware" in result["error"].lower() or "infected" in result["error"].lower()

    @patch("app.services.library_service.scan_bytes")
    def test_pending_scan_still_saves(self, mock_scan, db_session, test_user, test_course):
        mock_scan.return_value = {"status": "pending", "threat": None}
        result = contribute_to_library(
            db=db_session,
            user_id=str(test_user.id),
            course_id=str(test_course.id),
            topic="Pending Doc",
            file_content=b"%PDF-1.4 pending content",
            file_name="pending.pdf",
            file_type="pdf",
            extracted_text="some text",
        )
        assert result["success"] is True
        doc = db_session.query(LibraryDocument).filter(
            LibraryDocument.id == result["library_document_id"]
        ).first()
        assert doc.scan_status == "pending"
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_services/test_library_service.py::TestContributeToLibraryWithScan -v`
Expected: FAIL (scan_bytes not imported, scan_status not set)

**Step 3: Modify contribute_to_library() in library_service.py**

Add import at top of `library_service.py`:

```python
from app.services.virus_scan_service import scan_bytes
```

In `contribute_to_library()`, after the magic bytes validation block (line ~312) and before the hash calculation, add virus scan:

```python
        # Virus scan
        scan_result = scan_bytes(file_content)
        if scan_result["status"] == "infected":
            logger.warning(f"BLOCKED: Infected file upload attempt by user {user_id}: {scan_result['threat']}")
            return {
                "success": False,
                "error": f"File rejected: malware detected ({scan_result['threat']}). Please scan your device."
            }
        scan_status = scan_result["status"]  # 'clean', 'pending', or 'error'
```

Then in the `LibraryDocument(...)` constructor (around line 361-378), add:

```python
            scan_status=scan_status,
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_services/test_library_service.py::TestContributeToLibraryWithScan -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add backend/app/services/library_service.py backend/tests/test_services/test_library_service.py
git commit -m "feat: integrate virus scanning into library upload flow"
```

---

### Task 5: Filter Browse & Access by scan_status

**Files:**
- Modify: `backend/app/services/library_service.py:443-448` — add scan_status filter to browse_library()
- Modify: `backend/app/routes/library.py:145-176` — add scan_status check to document detail/view/download

**Step 1: Write failing tests**

Add to `backend/tests/test_services/test_library_service.py`:

```python
class TestBrowseLibraryWithScanStatus:

    def test_pending_docs_hidden_from_browse(self, db_session, test_user, test_course):
        doc = LibraryDocument(
            course_id=test_course.id,
            topic="Pending Scan Doc",
            file_name="pending.pdf",
            file_path="library/pending.pdf",
            file_type="pdf",
            file_size=1024,
            content_hash="d" * 64,
            uploaded_by=test_user.id,
            is_public=True,
            scan_status="pending",
        )
        db_session.add(doc)
        db_session.commit()

        result = browse_library(db_session)
        assert result["total"] == 0

    def test_clean_docs_visible_in_browse(self, db_session, test_user, test_course):
        doc = LibraryDocument(
            course_id=test_course.id,
            topic="Clean Doc",
            file_name="clean.pdf",
            file_path="library/clean.pdf",
            file_type="pdf",
            file_size=1024,
            content_hash="e" * 64,
            uploaded_by=test_user.id,
            is_public=True,
            scan_status="clean",
        )
        db_session.add(doc)
        db_session.commit()

        result = browse_library(db_session)
        assert result["total"] == 1

    def test_infected_docs_hidden_from_browse(self, db_session, test_user, test_course):
        doc = LibraryDocument(
            course_id=test_course.id,
            topic="Infected Doc",
            file_name="infected.pdf",
            file_path="library/infected.pdf",
            file_type="pdf",
            file_size=1024,
            content_hash="f" * 64,
            uploaded_by=test_user.id,
            is_public=True,
            scan_status="infected",
        )
        db_session.add(doc)
        db_session.commit()

        result = browse_library(db_session)
        assert result["total"] == 0
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_services/test_library_service.py::TestBrowseLibraryWithScanStatus -v`
Expected: FAIL (pending/infected docs still showing)

**Step 3: Add scan_status filter to browse_library()**

In `library_service.py`, `browse_library()` function, add after the `is_public == True` filter (line 448):

```python
            LibraryDocument.scan_status == "clean"
```

So the filter becomes:

```python
        query = db.query(LibraryDocument).options(
            joinedload(LibraryDocument.course),
            joinedload(LibraryDocument.uploader)
        ).filter(
            LibraryDocument.is_public == True,
            LibraryDocument.scan_status == "clean"
        )
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_services/test_library_service.py::TestBrowseLibraryWithScanStatus -v`
Expected: All 3 tests PASS

**Step 5: Add scan_status checks to routes**

In `backend/app/routes/library.py`, modify the access check in `get_library_document()`, `view_library_document()`, and `download_library_document()`. After the `is_public` / ownership check, add:

```python
        # Block public access to unscanned documents
        if document.scan_status != "clean" and str(document.uploaded_by) != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This document is pending security review"
            )
```

**Step 6: Run all library tests**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_services/test_library_service.py tests/test_api/test_library_routes.py -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add backend/app/services/library_service.py backend/app/routes/library.py backend/tests/test_services/test_library_service.py
git commit -m "feat: filter library browse and access by scan_status"
```

---

### Task 6: Alembic Migration — scan_status + GIN Indexes

**Files:**
- Create: `backend/alembic/versions/c4d5e6f7g8h9_add_scan_status_and_gin_indexes.py`

**Step 1: Create the migration file**

```python
"""Add scan_status column and GIN trigram indexes for full-text search

Revision ID: c4d5e6f7g8h9
Revises: 6211460164fa
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "c4d5e6f7g8h9"
down_revision = "6211460164fa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add scan_status column with default 'clean' for existing rows
    op.add_column(
        "library_documents",
        sa.Column("scan_status", sa.String(10), nullable=False, server_default="clean"),
    )

    # 2. Enable pg_trgm extension for trigram-based GIN indexes
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 3. Add GIN trigram indexes for fast ILIKE search
    op.execute(
        "CREATE INDEX ix_library_documents_topic_gin ON library_documents "
        "USING gin (topic gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_library_documents_file_name_gin ON library_documents "
        "USING gin (file_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_library_documents_extracted_text_gin ON library_documents "
        "USING gin (extracted_text gin_trgm_ops)"
    )

    # 4. Add index on scan_status for filtering
    op.create_index("ix_library_documents_scan_status", "library_documents", ["scan_status"])


def downgrade() -> None:
    op.drop_index("ix_library_documents_scan_status", table_name="library_documents")
    op.execute("DROP INDEX IF EXISTS ix_library_documents_extracted_text_gin")
    op.execute("DROP INDEX IF EXISTS ix_library_documents_file_name_gin")
    op.execute("DROP INDEX IF EXISTS ix_library_documents_topic_gin")
    op.drop_column("library_documents", "scan_status")
```

**Step 2: Verify migration syntax**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -c "from alembic.versions import *; print('Migration file parses OK')" 2>&1 || echo "Check syntax manually"`

**Step 3: Commit**

```bash
git add backend/alembic/versions/c4d5e6f7g8h9_add_scan_status_and_gin_indexes.py
git commit -m "feat: add migration for scan_status column and GIN trigram search indexes"
```

---

### Task 7: Update Schema Response + Add scan_status to LibraryDocumentResponse

**Files:**
- Modify: `backend/app/schemas/library.py` — add scan_status field to LibraryDocumentResponse

**Step 1: Write failing test**

Add to `backend/tests/test_api/test_schemas.py` (or create a new test if the test already exists):

```python
def test_library_document_response_includes_scan_status():
    from app.schemas.library import LibraryDocumentResponse
    fields = LibraryDocumentResponse.model_fields
    assert "scan_status" in fields
```

**Step 2: Run test**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_api/test_schemas.py::test_library_document_response_includes_scan_status -v`
Expected: FAIL

**Step 3: Add scan_status to schema**

In `backend/app/schemas/library.py`, add to `LibraryDocumentResponse` after `is_verified`:

```python
    scan_status: Optional[str] = "clean"
```

**Step 4: Run test to verify**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest tests/test_api/test_schemas.py::test_library_document_response_includes_scan_status -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/schemas/library.py backend/tests/test_api/test_schemas.py
git commit -m "feat: add scan_status to LibraryDocumentResponse schema"
```

---

### Task 8: Run Full Test Suite and Verify

**Step 1: Run all backend tests**

Run: `cd /Users/useruser/Documents/shadow-final-year/backend && python -m pytest -v`
Expected: All tests PASS

**Step 2: Fix any failures**

If any existing tests fail due to the new scan_status column (e.g., existing library_doc fixtures don't set scan_status), add `scan_status="clean"` to those fixtures.

**Step 3: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: ensure all existing tests pass with scan_status changes"
```

---

## Summary of Changes

| # | Task | Files | Test Count |
|---|------|-------|------------|
| 1 | Virus scan service tests | test_virus_scan_service.py | 6 |
| 2 | Virus scan service impl | virus_scan_service.py, requirements.txt | — |
| 3 | scan_status model column | library.py model | 2 |
| 4 | Scan in upload flow | library_service.py | 3 |
| 5 | Filter browse/access | library_service.py, library.py routes | 3 |
| 6 | Alembic migration | migration file | — |
| 7 | Schema update | library.py schema | 1 |
| 8 | Full test run | — | all |
