"""
Library Pydantic Schemas - Request/Response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class LibraryDocumentResponse(BaseModel):
    """Response schema for library document"""
    id: str
    course_id: str
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    week_number: Optional[int] = None
    topic: str
    file_name: str
    file_type: str
    file_size: int
    key_topics: Optional[List[str]] = []
    uploaded_by: str
    uploader_name: Optional[str] = None
    is_public: bool
    is_verified: bool
    scan_status: Optional[str] = "clean"
    view_count: int
    download_count: int
    helpful_votes: int
    uploaded_at: Optional[str] = None
    last_accessed: Optional[str] = None

    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    """Request schema for voting on a document"""
    vote_value: int = Field(..., ge=-1, le=1, description="Vote value: +1 for upvote, -1 for downvote")


class LibraryBrowseRequest(BaseModel):
    """Request schema for browsing library"""
    course_id: Optional[str] = None
    week_number: Optional[int] = Field(None, ge=1, le=15)
    search_query: Optional[str] = None
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class LibraryBrowseResponse(BaseModel):
    """Paginated response for library browse"""
    documents: List[LibraryDocumentResponse]
    total: int
    has_more: bool


class UserContributionsResponse(BaseModel):
    """Response schema for user's library contributions"""
    total_documents: int
    total_views: int
    total_downloads: int
    total_helpful_votes: int
    documents: List[LibraryDocumentResponse]
