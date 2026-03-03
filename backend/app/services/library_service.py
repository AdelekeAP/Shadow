"""
Library Service - Manages the student-powered learning library
Handles duplicate detection, file storage, and library operations
"""
import os
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.library import LibraryDocument, LibraryVote
from app.models.course import Course
from app.models.user import User
from app.services.document_converter import convert_pptx_to_pdf

logger = logging.getLogger(__name__)


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
        course_dir = os.path.join(base_dir, course_code)

        # Create directories if they don't exist
        os.makedirs(course_dir, exist_ok=True)

        # Generate unique filename (add hash prefix to avoid collisions)
        content_hash = calculate_file_hash(file_content)[:8]  # First 8 chars of hash
        file_extension = os.path.splitext(file_name)[1]
        unique_filename = f"{content_hash}_{file_name}"

        # Full path
        file_path = os.path.join(course_dir, unique_filename)

        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"💾 File saved to library: {file_path}")

        return file_path

    except Exception as e:
        logger.error(f"❌ Error saving file to library: {e}")
        raise Exception(f"Failed to save file: {str(e)}")


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
            converted_pdf_path=converted_pdf_path
        )

        db.add(library_doc)
        db.commit()
        db.refresh(library_doc)

        logger.info(f"✅ Document added to library: {library_doc.id} - {file_name}")

        return {
            "success": True,
            "is_duplicate": False,
            "library_document_id": str(library_doc.id),
            "message": "Document successfully added to learning library!",
            "document": library_doc.to_dict()
        }

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
    search_query: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """
    Browse library documents with optional filters

    Args:
        db: Database session
        course_id: Optional course filter
        week_number: Optional week filter
        search_query: Optional text search in topic/filename
        limit: Max results (default 50)
        offset: Pagination offset

    Returns:
        List of library documents
    """
    try:
        query = db.query(LibraryDocument).filter(
            LibraryDocument.is_public == True
        )

        # Filter by course
        if course_id:
            query = query.filter(LibraryDocument.course_id == course_id)

        # Filter by week
        if week_number:
            query = query.filter(LibraryDocument.week_number == week_number)

        # Search in topic or filename
        if search_query:
            search_term = f"%{search_query}%"
            query = query.filter(
                or_(
                    LibraryDocument.topic.ilike(search_term),
                    LibraryDocument.file_name.ilike(search_term)
                )
            )

        # Order by helpful votes (most helpful first), then views
        query = query.order_by(
            LibraryDocument.helpful_votes.desc(),
            LibraryDocument.view_count.desc()
        )

        # Pagination
        documents = query.limit(limit).offset(offset).all()

        return [doc.to_dict() for doc in documents]

    except Exception as e:
        logger.error(f"❌ Error browsing library: {e}")
        return []


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
    try:
        # Check if user already voted
        existing_vote = db.query(LibraryVote).filter(
            and_(
                LibraryVote.document_id == document_id,
                LibraryVote.user_id == user_id
            )
        ).first()

        document = db.query(LibraryDocument).filter(
            LibraryDocument.id == document_id
        ).first()

        if not document:
            logger.warning(f"⚠️ Document not found: {document_id}")
            return False

        if existing_vote:
            # Update existing vote
            old_value = existing_vote.vote_value
            existing_vote.vote_value = vote_value
            existing_vote.voted_at = datetime.utcnow()

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
    try:
        document = db.query(LibraryDocument).filter(
            LibraryDocument.id == document_id
        ).first()

        if document:
            document.view_count += 1
            document.last_accessed = datetime.utcnow()
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
