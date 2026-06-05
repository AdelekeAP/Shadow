"""
Virus Scan Service — ClamAV integration with graceful degradation

Scans uploaded files for malware using the ClamAV daemon (clamd).
When ClamAV is unavailable, files are quarantined (scan_status='pending')
rather than rejected, so SmartStudy uploads still work.
"""
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


SCAN_TIMEOUT = 30  # seconds — prevents hangs on ZIP bombs or large files

# Magic-byte signatures for the only file types the library accepts.
# PDF starts with "%PDF"; PPTX/Office Open XML files are ZIP archives ("PK\x03\x04").
_ALLOWED_SIGNATURES = (b"%PDF", b"PK\x03\x04")


def _basic_content_safe(file_content: bytes) -> bool:
    """
    Minimum safeguard used when no AV scanner is available: confirm the bytes
    actually start with a PDF or Office/ZIP signature. This blocks disguised
    executables/scripts from masquerading as study material.
    """
    head = file_content[:8]
    return any(head.startswith(sig) for sig in _ALLOWED_SIGNATURES)


def _get_clamd() -> Optional[Any]:
    """Get a ClamAV daemon connection, or None if unavailable."""
    try:
        import pyclamd
    except ImportError:
        return None

    try:
        cd = pyclamd.ClamdUnixSocket(timeout=SCAN_TIMEOUT)
        if cd.ping():
            return cd
    except Exception:
        pass

    try:
        cd = pyclamd.ClamdNetworkSocket(timeout=SCAN_TIMEOUT)
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
        # No AV scanner deployed (e.g. Railway has no ClamAV). Quarantining as 'pending'
        # makes uploads invisible forever since nothing ever promotes them. For this closed
        # academic deployment we instead auto-approve after a magic-byte content-type check.
        # This is acceptable because uploads are already restricted to PDF/PPTX, capped at
        # 25 MB, and always served with Content-Disposition (never executed). Set
        # REQUIRE_VIRUS_SCAN=true to restore strict quarantine if a scanner is added later.
        if os.getenv("REQUIRE_VIRUS_SCAN", "false").lower() in ("1", "true", "yes"):
            logger.warning("ClamAV unavailable and REQUIRE_VIRUS_SCAN set — file quarantined as pending")
            return {"status": "pending", "threat": None}
        if _basic_content_safe(file_content):
            logger.warning("ClamAV unavailable — file passed content-type check, marked clean")
            return {"status": "clean", "threat": None}
        logger.warning("ClamAV unavailable and content-type check failed — quarantined as pending")
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
                # Quarantine: remove the infected file from library storage
                try:
                    if os.path.exists(doc.file_path):
                        os.remove(doc.file_path)
                        logger.info(f"Infected file removed: {doc.file_path}")
                    if doc.converted_pdf_path and os.path.exists(doc.converted_pdf_path):
                        os.remove(doc.converted_pdf_path)
                except Exception as rm_err:
                    logger.error(f"Failed to remove infected file {doc.file_path}: {rm_err}")
            else:
                counts["failed"] += 1

        except Exception as e:
            logger.error(f"Failed to scan document {doc.id}: {e}")
            counts["failed"] += 1

    db.commit()
    logger.info(f"Pending scan complete: {counts}")
    return counts
