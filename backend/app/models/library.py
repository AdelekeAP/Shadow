"""
Library Models - Student-Powered Learning Library
Stores course materials uploaded by students for shared learning
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, ARRAY, Index, UniqueConstraint, LargeBinary
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, deferred
from datetime import datetime, timezone
import uuid

from app.database import Base


class LibraryDocument(Base):
    """
    Library Document - Represents a course material uploaded to the learning library

    Students can upload slides/PDFs which are stored and organized by:
    - Course (CSC401, MTH201, etc.)
    - Week number (1-15 for semester)
    - Topic (Binary Trees, React Hooks, etc.)

    Features duplicate detection to avoid storing same content twice.
    """
    __tablename__ = "library_documents"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Organization
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    week_number = Column(Integer, nullable=True)  # 1-15, optional
    topic = Column(String(255), nullable=False)  # "Binary Search Trees"

    # File storage
    file_name = Column(String(255), nullable=False)  # "CSC401_Week5_BST.pdf"
    file_path = Column(Text, nullable=False)  # Local or S3 path
    file_type = Column(String(10), nullable=False)  # 'pdf', 'pptx'
    file_size = Column(Integer, nullable=False)  # Bytes
    converted_pdf_path = Column(Text, nullable=True)  # Path to converted PDF (for PPTX viewing)

    # Persistent file bytes stored directly in Postgres. Railway's filesystem is ephemeral
    # (wiped on every redeploy), so file_path alone is unreliable in production. These columns
    # are the durable source of truth; file_path is kept as a fallback for local dev.
    # deferred() => the blob is NOT loaded by browse/list queries, only when a file is served.
    file_data = deferred(Column(LargeBinary, nullable=True))  # Raw uploaded file bytes
    converted_pdf_data = deferred(Column(LargeBinary, nullable=True))  # Converted PDF bytes (PPTX viewing)

    # Duplicate detection
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    extracted_text = Column(Text, nullable=True)  # Full text for search
    scan_status = Column(String(10), nullable=False, server_default="clean", default="clean")  # clean, infected, pending, error
    key_topics = Column(JSONB, nullable=True)  # ["BST", "Insertion", "Deletion"]

    # Metadata
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=True)  # Public or private
    is_verified = Column(Boolean, default=False)  # Admin/peer verified

    # Engagement metrics
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)  # Net upvotes (upvotes - downvotes)

    # Timestamps
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_accessed = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Performance indexes
    __table_args__ = (
        Index('ix_library_documents_uploaded_by', 'uploaded_by'),
        Index('ix_library_documents_is_public_votes', 'is_public', 'helpful_votes'),
        Index('ix_library_documents_course_week', 'course_id', 'week_number'),
    )

    # Relationships
    course = relationship("Course", back_populates="library_documents")
    uploader = relationship("User", back_populates="library_contributions")
    votes = relationship("LibraryVote", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "course_id": str(self.course_id),
            "course_code": self.course.code if self.course else None,
            "course_title": self.course.title if self.course else None,
            "week_number": self.week_number,
            "topic": self.topic,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "key_topics": self.key_topics,
            "uploaded_by": str(self.uploaded_by),
            "uploader_name": self.uploader.full_name if self.uploader else "Unknown",
            "is_public": self.is_public,
            "is_verified": self.is_verified,
            "scan_status": self.scan_status,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "helpful_votes": self.helpful_votes,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }


class LibraryVote(Base):
    """
    Library Vote - Tracks upvotes/downvotes on library documents

    Students can vote on document quality/helpfulness.
    One vote per student per document.
    """
    __tablename__ = "library_votes"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    document_id = Column(UUID(as_uuid=True), ForeignKey("library_documents.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Vote value
    vote_value = Column(Integer, nullable=False)  # +1 for upvote, -1 for downvote

    # Timestamp
    voted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # One vote per user per document — enforced at DB level
    __table_args__ = (
        UniqueConstraint('document_id', 'user_id', name='uq_library_votes_document_user'),
    )

    # Relationships
    document = relationship("LibraryDocument", back_populates="votes")
    user = relationship("User")

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "user_id": str(self.user_id),
            "vote_value": self.vote_value,
            "voted_at": self.voted_at.isoformat() if self.voted_at else None
        }
