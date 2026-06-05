"""
Library API Routes - Learning Library Endpoints
Student-powered resource sharing system
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging
import os

from app.database import get_db
from app.models.user import User
from app.models.library import LibraryDocument
from app.schemas.library import (
    LibraryDocumentResponse,
    LibraryBrowseResponse,
    VoteRequest,
    LibraryBrowseRequest,
    UserContributionsResponse
)
from app.services.library_service import (
    browse_library,
    vote_on_document,
    increment_view_count,
    increment_download_count,
    get_user_contributions
)
from app.utils.auth import get_current_user
from app.services.cache_service import cache_get, cache_set, cache_delete_pattern
from app.middleware.rate_limiter import limiter

router = APIRouter(prefix="/library", tags=["library"])
logger = logging.getLogger(__name__)


def _validate_uuid(value: str, name: str = "ID") -> str:
    """Validate that a string is a valid UUID format."""
    try:
        UUID(value)
        return value
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {name} format"
        )


def _check_document_access(document: LibraryDocument, user: User) -> None:
    """
    Validate that a user can access a document.

    Raises HTTPException if access is denied (private doc, infected doc,
    or unscanned doc that doesn't belong to the requesting user).
    """
    is_owner = str(document.uploaded_by) == str(user.id)

    # Block infected files for everyone, including owners
    if document.scan_status == "infected":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This document has been flagged by our security scan and cannot be downloaded"
        )

    if not document.is_public and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this document"
        )

    if document.scan_status != "clean" and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This document is pending security review"
        )


def _serve_bytes(db: Session, document_id: str, data: bytes, content_type: str,
                 file_name: str, inline: bool) -> Response:
    """Serve file bytes stored in the DB, incrementing the appropriate counter."""
    if inline:
        increment_view_count(db, document_id)
    else:
        increment_download_count(db, document_id)
    disposition = "inline" if inline else "attachment"
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'{disposition}; filename="{file_name}"'}
    )


@router.get(
    "/browse",
    response_model=LibraryBrowseResponse,
    operation_id="browse_library",
    summary="Browse library documents with optional filters",
)
@limiter.limit("60/minute")
async def browse_library_documents(
    request: Request,
    course_id: Optional[str] = Query(None, description="Filter by course UUID"),
    week_number: Optional[int] = Query(None, ge=1, le=15, description="Filter by week (1-15)"),
    file_type: Optional[str] = Query(None, description="Filter by file type (pdf, pptx, ppt)"),
    search: Optional[str] = Query(None, description="Search in topic, filename, or content"),
    sort_by: Optional[str] = Query("helpful", description="Sort order: helpful, newest, oldest, name, size_asc, size_desc"),
    limit: int = Query(50, ge=1, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Browse library documents with optional filters

    **Filters:**
    - `course_id`: Filter by specific course
    - `week_number`: Filter by week (1-15)
    - `file_type`: Filter by file type (pdf, pptx, ppt)
    - `search`: Search in topic, filename, or document content
    - `sort_by`: Sort order (helpful, newest, oldest, name, size_asc, size_desc)
    - `limit`: Max results (default 50, max 100)
    - `offset`: Pagination offset

    **Returns:** Paginated library documents sorted by chosen order
    """
    try:
        if course_id:
            _validate_uuid(course_id, "course_id")

        # Validate file_type if provided
        if file_type and file_type.lower() not in ('pdf', 'pptx', 'ppt'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file_type. Must be one of: pdf, pptx, ppt"
            )

        # Validate sort_by if provided
        valid_sorts = ('helpful', 'newest', 'oldest', 'name', 'size_asc', 'size_desc')
        if sort_by and sort_by.lower() not in valid_sorts:
            sort_by = 'helpful'

        # Check cache first
        cache_key = f"library:browse:{course_id}:{week_number}:{file_type}:{search}:{sort_by}:{limit}:{offset}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        result = browse_library(
            db=db,
            course_id=course_id,
            week_number=week_number,
            file_type=file_type,
            search_query=search,
            sort_by=sort_by or 'helpful',
            limit=limit,
            offset=offset,
            user_id=str(current_user.id)
        )

        cache_set(cache_key, result, ttl=300)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error browsing library: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to browse library"
        )


@router.get(
    "/documents/{document_id}",
    response_model=LibraryDocumentResponse,
    operation_id="get_library_document",
    summary="Get details of a specific library document",
)
async def get_library_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific library document

    Returns document metadata. View count is tracked via the /view endpoint.
    """
    try:
        _validate_uuid(document_id, "document_id")

        document = db.query(LibraryDocument).filter(
            LibraryDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        _check_document_access(document, current_user)

        return document.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document"
        )


@router.post(
    "/documents/{document_id}/vote",
    operation_id="vote_on_library_document",
    summary="Vote on a library document",
)
@limiter.limit("30/minute")
async def vote_on_library_document(
    request: Request,
    document_id: str,
    vote_data: VoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Vote on a library document

    **Vote values:**
    - `+1`: Upvote (helpful)
    - `-1`: Downvote (not helpful)

    **Note:** One vote per user per document. Updates existing vote if already voted.
    """
    try:
        _validate_uuid(document_id, "document_id")

        # Check if document exists
        document = db.query(LibraryDocument).filter(
            LibraryDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Access check: can't vote on private/unscanned docs you don't own
        _check_document_access(document, current_user)

        # Can't vote on own documents
        if str(document.uploaded_by) == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot vote on your own documents"
            )

        # Validate vote value
        if vote_data.vote_value not in [-1, 1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vote value must be +1 (upvote) or -1 (downvote)"
            )

        # Record vote
        success = vote_on_document(
            db=db,
            user_id=str(current_user.id),
            document_id=document_id,
            vote_value=vote_data.vote_value
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record vote"
            )

        # Invalidate caches affected by votes
        cache_delete_pattern("library:browse:*")
        cache_delete_pattern("library:stats*")
        cache_delete_pattern(f"library:contributions:{document.uploaded_by}")

        return {
            "success": True,
            "message": f"Vote recorded: {'👍 Helpful' if vote_data.vote_value == 1 else '👎 Not helpful'}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error voting on document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record vote"
        )


@router.get(
    "/documents/{document_id}/view",
    operation_id="view_library_document",
    summary="View a library document inline",
)
async def view_library_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    View a library document inline (for in-app viewing)

    Returns the file with proper content type for browser viewing.
    Increments view count.
    """
    try:
        _validate_uuid(document_id, "document_id")

        document = db.query(LibraryDocument).filter(
            LibraryDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        _check_document_access(document, current_user)

        serving_file_name = document.file_name
        content_type = 'application/pdf'
        is_pptx = document.file_type.lower() in ['pptx', 'ppt']

        if is_pptx:
            # PPTX is only viewable in-browser via its converted PDF (bytes preferred, disk fallback)
            serving_file_name = os.path.splitext(document.file_name)[0] + '.pdf'
            if document.converted_pdf_data:
                return _serve_bytes(db, document_id, document.converted_pdf_data,
                                    'application/pdf', serving_file_name, inline=True)
            if document.converted_pdf_path and os.path.exists(document.converted_pdf_path):
                increment_view_count(db, document_id)
                return FileResponse(
                    path=document.converted_pdf_path,
                    media_type='application/pdf',
                    headers={"Content-Disposition": f'inline; filename="{serving_file_name}"'}
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PowerPoint file cannot be viewed in-browser. Converted PDF not available. Please use the download option."
            )

        # PDF (and anything else): serve the durable DB bytes, falling back to local disk
        if document.file_data:
            return _serve_bytes(db, document_id, document.file_data,
                                content_type, serving_file_name, inline=True)
        if document.file_path and os.path.exists(document.file_path):
            increment_view_count(db, document_id)
            return FileResponse(
                path=document.file_path,
                media_type=content_type,
                headers={"Content-Disposition": f'inline; filename="{serving_file_name}"'}
            )

        logger.error(f"No file bytes or disk file for document {document_id} ({document.file_path})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to view document"
        )


@router.get(
    "/documents/{document_id}/download",
    operation_id="download_library_document",
    summary="Download a library document",
)
@limiter.limit("100/hour")
async def download_library_document(
    request: Request,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download a library document

    Increments download count and returns the file.
    """
    try:
        _validate_uuid(document_id, "document_id")

        document = db.query(LibraryDocument).filter(
            LibraryDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        _check_document_access(document, current_user)

        # Serve the durable DB bytes, falling back to local disk for legacy/local files
        if document.file_data:
            increment_download_count(db, document_id)
            return Response(
                content=document.file_data,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{document.file_name}"'}
            )
        if document.file_path and os.path.exists(document.file_path):
            increment_download_count(db, document_id)
            return FileResponse(
                path=document.file_path,
                filename=document.file_name,
                media_type="application/octet-stream"
            )

        logger.error(f"No file bytes or disk file for document {document_id} ({document.file_path})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )


@router.get(
    "/my-contributions",
    response_model=UserContributionsResponse,
    operation_id="get_my_library_contributions",
    summary="Get current user's library contributions and stats",
)
async def get_my_contributions(
    limit: int = Query(50, ge=1, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's library contributions and stats

    **Returns:**
    - Total documents uploaded
    - Total views across all documents
    - Total downloads across all documents
    - Total helpful votes received
    - Paginated list of uploaded documents with stats
    """
    try:
        # Check cache first
        cache_key = f"library:contributions:{current_user.id}:{limit}:{offset}"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        stats = get_user_contributions(db, str(current_user.id), limit=limit, offset=offset)

        cache_set(cache_key, stats, ttl=300)
        return stats

    except Exception as e:
        logger.error(f"Error getting user contributions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get contributions"
        )


@router.get(
    "/stats",
    operation_id="get_library_stats",
    summary="Get overall library statistics",
)
async def get_library_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get overall library statistics

    **Returns:**
    - Total documents in library
    - Total contributors
    - Most popular courses
    - Most helpful documents
    """
    try:
        # Check cache first
        cache_key = "library:stats"
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

        from sqlalchemy import func, desc
        from sqlalchemy.orm import joinedload

        # Total documents
        total_docs = db.query(func.count(LibraryDocument.id)).filter(
            LibraryDocument.is_public == True
        ).scalar()

        # Total contributors
        total_contributors = db.query(
            func.count(func.distinct(LibraryDocument.uploaded_by))
        ).filter(
            LibraryDocument.is_public == True
        ).scalar()

        # Most popular courses (by document count)
        popular_courses = db.query(
            LibraryDocument.course_id,
            func.count(LibraryDocument.id).label('doc_count')
        ).filter(
            LibraryDocument.is_public == True
        ).group_by(
            LibraryDocument.course_id
        ).order_by(
            desc('doc_count')
        ).limit(5).all()

        # Most helpful documents (eager-load relationships for to_dict)
        helpful_docs = db.query(LibraryDocument).options(
            joinedload(LibraryDocument.course),
            joinedload(LibraryDocument.uploader)
        ).filter(
            LibraryDocument.is_public == True
        ).order_by(
            desc(LibraryDocument.helpful_votes)
        ).limit(5).all()

        result = {
            "total_documents": total_docs,
            "total_contributors": total_contributors,
            "popular_courses": [
                {"course_id": str(course_id), "document_count": count}
                for course_id, count in popular_courses
            ],
            "most_helpful_documents": [doc.to_dict() for doc in helpful_docs]
        }

        cache_set(cache_key, result, ttl=600)
        return result

    except Exception as e:
        logger.error(f"Error getting library stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get library stats"
        )
