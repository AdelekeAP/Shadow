# Virus Scanning & Full-Text Search Index Design

**Date:** 2026-03-04
**Status:** Approved

## Problem

1. **No virus scanning**: Malicious PDFs can be uploaded and served to other students via the library
2. **No search index on extracted_text**: ILIKE search does full table scan, will degrade at 100+ documents

## Solution

### 1. Virus Scanning — ClamAV with Quarantine Model

**Approach:** ClamAV daemon (`clamd`) via `pyclamd` Python library, with quarantine-based fallback when ClamAV is unavailable.

**New database column:** `scan_status` on `library_documents` — values: `clean`, `infected`, `pending`, `error`

**New service:** `VirusScanService` in `backend/app/services/virus_scan_service.py`

#### Upload Flow (modified)

1. File uploaded → existing validation (magic bytes, size, type)
2. Attempt ClamAV scan via `pyclamd`:
   - **Clean** → `scan_status = 'clean'`, proceed normally
   - **Infected** → reject upload immediately, return 400 error, log file details
   - **ClamAV unavailable** → `scan_status = 'pending'`, file saved but quarantined from public browse
   - **Scan error** → `scan_status = 'error'`, treat as pending (quarantined)
3. SmartStudy text extraction proceeds regardless of scan status (uploader's own file)
4. Study plan generation works normally — scan status doesn't block text extraction

#### Public Library Browse (modified)

- `browse_library()` adds filter: `scan_status == 'clean'` for public results
- Uploader can always see their own documents regardless of scan status
- Document detail/view/download endpoints: public access requires `scan_status == 'clean'`

#### Background Recovery

- `scan_pending_documents()` utility function scans all `pending`/`error` documents
- Can be called via admin endpoint or scheduled task
- On scan completion: updates `scan_status` to `clean` or `infected`
- Infected files: kept on disk but permanently hidden from browse (for audit trail)

### 2. Full-Text Search Index — GIN Trigram

**Approach:** PostgreSQL `pg_trgm` extension with GIN indexes on searched columns.

**Changes:**
- Enable `pg_trgm` extension via migration
- Add GIN trigram index on `extracted_text` column
- Add GIN trigram index on `topic` column
- Add GIN trigram index on `file_name` column

**No code changes needed** — existing ILIKE queries automatically use GIN trigram indexes.

### Migration

Single Alembic migration covering:
1. `scan_status` column (String, default `'clean'` for existing documents)
2. `pg_trgm` extension
3. GIN trigram indexes on `extracted_text`, `topic`, `file_name`

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/services/virus_scan_service.py` | Create | ClamAV integration service |
| `backend/app/services/library_service.py` | Modify | Add scan call in upload, filter browse by scan_status |
| `backend/app/models/library.py` | Modify | Add scan_status column |
| `backend/app/routes/library.py` | Modify | Filter public access by scan_status |
| `backend/app/routes/smartstudy/study_plans.py` | Modify | Integrate scan into upload endpoints |
| `backend/alembic/versions/xxx_add_scan_status_and_gin_indexes.py` | Create | Migration |
| `backend/requirements.txt` | Modify | Add pyclamd |
| `backend/tests/test_services/test_virus_scan_service.py` | Create | Unit tests |

## Dependencies

- `pyclamd` Python package
- ClamAV daemon installed on server (optional — system degrades gracefully)
- PostgreSQL `pg_trgm` extension (built-in, just needs enabling)
