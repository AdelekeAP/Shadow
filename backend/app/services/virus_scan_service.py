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


def _get_clamd() -> Optional[Any]:
    """Get a ClamAV daemon connection, or None if unavailable."""
    try:
        import pyclamd
    except ImportError:
        return None

    try:
        cd = pyclamd.ClamdUnixSocket()
        if cd.ping():
            return cd
    except Exception:
        pass

    try:
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
