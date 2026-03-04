"""
Library Service - Manages the student-powered learning library
Handles duplicate detection, file storage, and library operations
"""
import os
import re
import hashlib
import logging
from uuid import UUID
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, func

from app.models.library import LibraryDocument, LibraryVote
from app.models.course import Course
from app.models.user import User
from app.services.document_converter import convert_pptx_to_pdf
from app.services.virus_scan_service import scan_bytes

logger = logging.getLogger(__name__)


def _validate_uuid(value) -> bool:
    """Return True if *value* is a valid UUID (string or UUID object)."""
    if isinstance(value, UUID):
        return True
    try:
        UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False


# Magic byte signatures for file type validation
FILE_SIGNATURES = {
    "pdf": b"%PDF",
    "pptx": b"PK\x03\x04",  # ZIP-based (OOXML)
    "ppt": b"\xd0\xcf\x11\xe0",  # OLE2 compound document
}


def sanitize_filename(filename: str) -> str:
    """
    Remove path traversal sequences and dangerous characters from a filename.

    Args:
        filename: Raw filename from user input

    Returns:
        Sanitized filename safe for filesystem use
    """
    # Take only the basename (strip any directory components)
    filename = os.path.basename(filename)
    # Replace path traversal sequences
    filename = filename.replace("..", "_")
    # Keep only safe characters: alphanumeric, dots, hyphens, underscores, spaces
    filename = re.sub(r"[^\w\s.\-]", "_", filename)
    # Collapse multiple underscores/spaces
    filename = re.sub(r"[_\s]+", "_", filename).strip("_")
    # Ensure non-empty
    return filename or "unnamed_document"


def validate_file_magic_bytes(file_content: bytes, expected_type: str) -> bool:
    """
    Validate that file content matches the expected type by checking magic bytes.

    Args:
        file_content: Raw file bytes
        expected_type: Expected file extension (pdf, pptx, ppt)

    Returns:
        True if magic bytes match expected type
    """
    sig = FILE_SIGNATURES.get(expected_type.lower())
    if sig is None:
        return False
    return file_content[:len(sig)] == sig


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate SHA-256 hash of file content for duplicate detection

    Args:
        file_content: Binary file content

    Returns:
        SHA-256 hash string (64 characters)
    """
    return hashlib.sha256(file_content).hexdigest()


def check_duplicate_document(
    db: Session,
    content_hash: str,
    course_id: str,
    week_number: Optional[int] = None
) -> Optional[LibraryDocument]:
    """
    Check if document already exists in library

    Args:
        db: Database session
        content_hash: SHA-256 hash of file content
        course_id: Course UUID
        week_number: Optional week number

    Returns:
        Existing LibraryDocument if found, None otherwise
    """
    try:
        query = db.query(LibraryDocument).filter(
            and_(
                LibraryDocument.content_hash == content_hash,
                LibraryDocument.course_id == course_id
            )
        )

        # If week specified, also match week
        if week_number:
            query = query.filter(LibraryDocument.week_number == week_number)

        existing = query.first()

        if existing:
            logger.info(f"📋 Duplicate detected: {existing.file_name} (uploaded by {existing.uploader.full_name})")

        return existing

    except Exception as e:
        logger.error(f"❌ Error checking for duplicates: {e}")
        return None


def save_file_to_library(
    file_content: bytes,
    file_name: str,
    course_code: str
) -> str:
    """
    Save file to library storage (local for now, can be S3 later)

    Args:
        file_content: Binary file content
        file_name: Original filename
        course_code: Course code for organization

    Returns:
        Relative file path

    File structure:
        library/
        ├── CSC401/
        │   ├── Week1_Introduction.pdf
        │   └── Week5_BinaryTrees.pptx
        └── MTH201/
            └── Week3_Integration.pdf
    """
    try:
        # Create library directory structure
        base_dir = "library"
        # Sanitize course_code as well (defense in depth)
        safe_course = re.sub(r"[^\w\-]", "_", course_code)
        course_dir = os.path.join(base_dir, safe_course)

        # Create directories if they don't exist
        os.makedirs(course_dir, exist_ok=True)

        # Sanitize the user-supplied filename to prevent path traversal
        safe_name = sanitize_filename(file_name)

        # Generate unique filename (add hash prefix to avoid collisions)
        content_hash = calculate_file_hash(file_content)[:8]  # First 8 chars of hash
        unique_filename = f"{content_hash}_{safe_name}"

        # Full path
        file_path = os.path.join(course_dir, unique_filename)

        # Final safety check: ensure resolved path is under base_dir
        resolved = os.path.realpath(file_path)
        expected_base = os.path.realpath(base_dir)
        if not resolved.startswith(expected_base + os.sep):
            raise ValueError("Attempted path traversal blocked")

        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"💾 File saved to library: {file_path}")

        return file_path

    except Exception as e:
        logger.error(f"❌ Error saving file to library: {e}")
        raise Exception(f"Failed to save file: {str(e)}")


def check_content_course_relevance(
    extracted_text: str,
    course_code: str,
    course_title: str,
) -> Optional[str]:
    """
    Lightweight check that document content is relevant to the selected course.

    Compares keywords from the course code and title against the extracted text.
    Returns a warning message if the content appears unrelated, or None if OK.

    This is a soft guardrail — it never blocks the upload.
    """
    if not extracted_text or len(extracted_text.strip()) < 50:
        # Too little text to judge
        return None

    text_lower = extracted_text.lower()

    # Build keyword set from course code + title
    # e.g. "CSC401" -> ["csc", "csc401"], "Computer Architecture" -> ["computer", "architecture"]
    keywords: List[str] = []

    # Course code tokens (e.g. "CSC401" -> "csc401", "csc")
    code_clean = course_code.strip().lower()
    keywords.append(code_clean)
    # Extract the alphabetic prefix (e.g. "csc" from "csc401")
    alpha_prefix = re.sub(r"[^a-z]", "", code_clean)
    if alpha_prefix and len(alpha_prefix) >= 2:
        keywords.append(alpha_prefix)

    # Title words (skip short/common words)
    stop_words = {"and", "the", "of", "in", "to", "for", "a", "an", "on", "at", "is", "it", "its"}
    title_words = [
        w.lower() for w in re.findall(r"[A-Za-z]+", course_title)
        if len(w) >= 3 and w.lower() not in stop_words
    ]
    keywords.extend(title_words)

    # Common academic abbreviations (both directions)
    _abbreviations = {
        "computer": "cs", "science": "sci", "mathematics": "math",
        "engineering": "eng", "statistics": "stat", "economics": "econ",
        "biology": "bio", "chemistry": "chem", "physics": "phys",
        "information": "info", "technology": "tech", "management": "mgmt",
        "accounting": "acct", "psychology": "psych", "philosophy": "phil",
    }
    for tw in list(title_words):
        abbr = _abbreviations.get(tw)
        if abbr:
            keywords.append(abbr)
    # Also map abbreviations back to full words
    _reverse = {v: k for k, v in _abbreviations.items()}
    for tw in list(title_words):
        full = _reverse.get(tw)
        if full:
            keywords.append(full)

    if not keywords:
        return None

    # Check how many keywords appear in the document text
    matched = [kw for kw in keywords if kw in text_lower]
    match_ratio = len(matched) / len(keywords) if keywords else 0

    if match_ratio == 0 and len(keywords) >= 2:
        return (
            f"The uploaded document doesn't appear to mention anything related to "
            f"{course_code} ({course_title}). Please double-check you selected the correct course."
        )

    return None


def contribute_to_library(
    db: Session,
    user_id: str,
    course_id: str,
    topic: str,
    file_content: bytes,
    file_name: str,
    file_type: str,
    extracted_text: str,
    week_number: Optional[int] = None,
    key_topics: Optional[List[str]] = None,
    is_public: bool = True
) -> Dict[str, Any]:
    """
    Contribute a document to the learning library

    Args:
        db: Database session
        user_id: Uploader's UUID
        course_id: Course UUID
        topic: Document topic
        file_content: Binary file content
        file_name: Original filename
        file_type: File extension (pdf, pptx)
        extracted_text: Extracted text content
        week_number: Optional week (1-15)
        key_topics: Optional list of key topics/keywords
        is_public: Whether to make document public (default True)

    Returns:
        Dict with status and library document info
    """
    try:
        # Validate file magic bytes match claimed type
        if not validate_file_magic_bytes(file_content, file_type):
            return {
                "success": False,
                "error": f"File content does not match the expected {file_type.upper()} format. The file may be corrupted or mislabeled."
            }

        # Virus scan
        scan_result = scan_bytes(file_content)
        if scan_result["status"] == "infected":
            logger.warning(f"BLOCKED: Infected file upload attempt by user {user_id}: {scan_result['threat']}")
            return {
                "success": False,
                "error": f"File rejected: malware detected ({scan_result['threat']}). Please scan your device."
            }
        scan_status = scan_result["status"]  # 'clean', 'pending', or 'error'

        # Calculate hash
        content_hash = calculate_file_hash(file_content)

        # Check for duplicates
        existing = check_duplicate_document(db, content_hash, course_id, week_number)

        if existing:
            return {
                "success": False,
                "is_duplicate": True,
                "existing_document_id": str(existing.id),
                "message": f"This document already exists in the library (uploaded by {existing.uploader.full_name})",
                "existing_document": existing.to_dict()
            }

        # Get course info for file storage
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return {
                "success": False,
                "error": "Course not found"
            }

        # Check content-course relevance (soft warning, never blocks)
        relevance_warning = check_content_course_relevance(
            extracted_text or "",
            course.code,
            course.title,
        )
        if relevance_warning:
            logger.warning(f"⚠️ Relevance mismatch: {relevance_warning}")

        # Save file to library storage
        file_path = save_file_to_library(file_content, file_name, course.code)

        # Convert PPTX to PDF for in-browser viewing
        converted_pdf_path = None
        if file_type.lower() in ['pptx', 'ppt']:
            try:
                logger.info(f"🔄 Converting {file_type.upper()} to PDF for viewing...")
                converted_pdf_path = convert_pptx_to_pdf(file_path)
                logger.info(f"✅ Converted PDF saved: {converted_pdf_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to convert PPTX to PDF: {e}")
                logger.warning("   Document will be available for download only")

        # Create library document entry
        library_doc = LibraryDocument(
            course_id=course_id,
            week_number=week_number,
            topic=topic,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_size=len(file_content),
            content_hash=content_hash,
            extracted_text=extracted_text,
            key_topics=key_topics or [],
            uploaded_by=user_id,
            is_public=is_public,
            is_verified=False,
            view_count=0,
            download_count=0,
            helpful_votes=0,
            converted_pdf_path=converted_pdf_path,
            scan_status=scan_status,
        )

        db.add(library_doc)
        db.commit()
        db.refresh(library_doc)

        logger.info(f"✅ Document added to library: {library_doc.id} - {file_name}")

        result = {
            "success": True,
            "is_duplicate": False,
            "library_document_id": str(library_doc.id),
            "message": "Document successfully added to learning library!",
            "document": library_doc.to_dict()
        }
        if relevance_warning:
            result["relevance_warning"] = relevance_warning
        return result

    except Exception as e:
        logger.error(f"❌ Error contributing to library: {e}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }


def browse_library(
    db: Session,
    course_id: Optional[str] = None,
    week_number: Optional[int] = None,
    file_type: Optional[str] = None,
    search_query: Optional[str] = None,
    sort_by: str = "helpful",
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Browse library documents with optional filters.

    Args:
        db: Database session
        course_id: Optional course filter (UUID string)
        week_number: Optional week filter (1-15)
        file_type: Optional file type filter (pdf, pptx, ppt)
        search_query: Optional text search in topic/filename/content
        sort_by: Sort order (helpful, newest, oldest, name, size_asc, size_desc)
        limit: Max results per page (default 50, max 100)
        offset: Pagination offset (0-based)

    Returns:
        Paginated result dict::

            {
                "documents": List[Dict],  # Serialized LibraryDocument dicts
                "total": int,             # Total matching documents (before pagination)
                "has_more": bool,         # True if more pages exist after this one
            }

    Note:
        This returns a paginated dict (not a flat list). The corresponding
        route schema is ``LibraryBrowseResponse``.
    """
    try:
        # Show public+clean docs to everyone, but also show the uploader
        # their own documents regardless of scan_status or visibility.
        if user_id:
            query = db.query(LibraryDocument).options(
                joinedload(LibraryDocument.course),
                joinedload(LibraryDocument.uploader)
            ).filter(
                or_(
                    and_(
                        LibraryDocument.is_public == True,
                        LibraryDocument.scan_status == "clean"
                    ),
                    LibraryDocument.uploaded_by == user_id
                )
            )
        else:
            query = db.query(LibraryDocument).options(
                joinedload(LibraryDocument.course),
                joinedload(LibraryDocument.uploader)
            ).filter(
                LibraryDocument.is_public == True,
                LibraryDocument.scan_status == "clean"
            )

        # Filter by course
        if course_id:
            query = query.filter(LibraryDocument.course_id == course_id)

        # Filter by week
        if week_number:
            query = query.filter(LibraryDocument.week_number == week_number)

        # Filter by file type
        if file_type:
            query = query.filter(
                func.lower(LibraryDocument.file_type) == file_type.lower()
            )

        # Search in topic, filename, or extracted text
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                or_(
                    LibraryDocument.topic.ilike(search_term),
                    LibraryDocument.file_name.ilike(search_term),
                    LibraryDocument.extracted_text.ilike(search_term)
                )
            )

        # Get total count before pagination
        total = query.count()

        # Apply sort order
        if sort_by == "newest":
            query = query.order_by(LibraryDocument.uploaded_at.desc())
        elif sort_by == "oldest":
            query = query.order_by(LibraryDocument.uploaded_at.asc())
        elif sort_by == "name":
            query = query.order_by(LibraryDocument.topic.asc())
        elif sort_by == "size_asc":
            query = query.order_by(LibraryDocument.file_size.asc())
        elif sort_by == "size_desc":
            query = query.order_by(LibraryDocument.file_size.desc())
        else:
            # Default: most helpful first, then most viewed
            query = query.order_by(
                LibraryDocument.helpful_votes.desc(),
                LibraryDocument.view_count.desc()
            )

        # Pagination
        documents = query.limit(limit).offset(offset).all()

        return {
            "documents": [doc.to_dict() for doc in documents],
            "total": total,
            "has_more": (offset + limit) < total
        }

    except Exception as e:
        logger.error(f"❌ Error browsing library: {e}")
        return {"documents": [], "total": 0, "has_more": False}


def vote_on_document(
    db: Session,
    user_id: str,
    document_id: str,
    vote_value: int  # +1 for upvote, -1 for downvote
) -> bool:
    """
    Vote on a library document

    Args:
        db: Database session
        user_id: Voter's UUID
        document_id: Document UUID
        vote_value: +1 or -1

    Returns:
        True if successful
    """
    # Defense-in-depth: validate inputs even if route already checked
    if not _validate_uuid(document_id) or not _validate_uuid(user_id):
        logger.warning(f"⚠️ Invalid UUID in vote_on_document: doc={document_id}, user={user_id}")
        return False
    if vote_value not in (-1, 1):
        logger.warning(f"⚠️ Invalid vote value: {vote_value}")
        return False

    try:
        document = db.query(LibraryDocument).filter(
            LibraryDocument.id == document_id
        ).first()

        if not document:
            logger.warning(f"⚠️ Document not found: {document_id}")
            return False

        # Check if user already voted
        existing_vote = db.query(LibraryVote).filter(
            and_(
                LibraryVote.document_id == document_id,
                LibraryVote.user_id == user_id
            )
        ).first()

        if existing_vote:
            # Update existing vote
            old_value = existing_vote.vote_value
            # Validate stored value before delta calculation
            if old_value not in (-1, 1):
                logger.warning(f"⚠️ Corrupt vote value {old_value} for vote {existing_vote.id}, resetting")
                old_value = 0
            existing_vote.vote_value = vote_value
            existing_vote.voted_at = datetime.now(timezone.utc)

            # Adjust document's helpful_votes
            document.helpful_votes = document.helpful_votes - old_value + vote_value

        else:
            # Create new vote
            vote = LibraryVote(
                document_id=document_id,
                user_id=user_id,
                vote_value=vote_value
            )
            db.add(vote)

            # Update document's helpful_votes
            document.helpful_votes = document.helpful_votes + vote_value

        db.commit()
        logger.info(f"✅ Vote recorded: Document {document_id} by User {user_id} ({vote_value:+d})")

        return True

    except IntegrityError:
        # Race condition: concurrent insert hit the unique constraint.
        # Roll back and retry as an update.
        db.rollback()
        logger.info(f"🔄 Concurrent vote detected, retrying as update")
        try:
            existing_vote = db.query(LibraryVote).filter(
                and_(
                    LibraryVote.document_id == document_id,
                    LibraryVote.user_id == user_id
                )
            ).first()
            document = db.query(LibraryDocument).filter(
                LibraryDocument.id == document_id
            ).first()
            if existing_vote and document:
                old_value = existing_vote.vote_value
                existing_vote.vote_value = vote_value
                existing_vote.voted_at = datetime.now(timezone.utc)
                document.helpful_votes = document.helpful_votes - old_value + vote_value
                db.commit()
                return True
            return False
        except Exception as retry_exc:
            logger.error(f"❌ Failed to retry vote after race condition: {retry_exc}")
            db.rollback()
            return False

    except Exception as e:
        logger.error(f"❌ Error voting on document: {e}")
        db.rollback()
        return False


def increment_view_count(db: Session, document_id: str) -> bool:
    """
    Increment view count for a document

    Args:
        db: Database session
        document_id: Document UUID

    Returns:
        True if successful
    """
    if not _validate_uuid(document_id):
        logger.warning(f"⚠️ Invalid UUID in increment_view_count: {document_id}")
        return False
    try:
        document = db.query(LibraryDocument).filter(
            LibraryDocument.id == document_id
        ).first()

        if document:
            document.view_count += 1
            document.last_accessed = datetime.now(timezone.utc)
            db.commit()
            return True

        return False

    except Exception as e:
        logger.error(f"❌ Error incrementing view count: {e}")
        db.rollback()
        return False


def increment_download_count(db: Session, document_id: str) -> bool:
    """
    Increment download count for a document

    Args:
        db: Database session
        document_id: Document UUID

    Returns:
        True if successful
    """
    if not _validate_uuid(document_id):
        logger.warning(f"⚠️ Invalid UUID in increment_download_count: {document_id}")
        return False
    try:
        document = db.query(LibraryDocument).filter(
            LibraryDocument.id == document_id
        ).first()

        if document:
            document.download_count += 1
            db.commit()
            return True

        return False

    except Exception as e:
        logger.error(f"❌ Error incrementing download count: {e}")
        db.rollback()
        return False


def get_user_contributions(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Get statistics about user's library contributions

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Dict with contribution stats
    """
    try:
        documents = db.query(LibraryDocument).filter(
            LibraryDocument.uploaded_by == user_id
        ).all()

        total_views = sum(doc.view_count for doc in documents)
        total_downloads = sum(doc.download_count for doc in documents)
        total_votes = sum(doc.helpful_votes for doc in documents)

        return {
            "total_documents": len(documents),
            "total_views": total_views,
            "total_downloads": total_downloads,
            "total_helpful_votes": total_votes,
            "documents": [doc.to_dict() for doc in documents]
        }

    except Exception as e:
        logger.error(f"❌ Error getting user contributions: {e}")
        return {
            "total_documents": 0,
            "total_views": 0,
            "total_downloads": 0,
            "total_helpful_votes": 0,
            "documents": []
        }
