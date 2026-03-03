"""
Content Curation Models
Caches curated learning resources and quality scores from YouTube/Reddit
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.database import Base


class CuratedResource(Base):
    """
    Curated Resource - Cached learning resource with quality scores
    Stores YouTube videos and Reddit recommendations to avoid repeated API calls
    """
    __tablename__ = "curated_resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Topic/search query
    topic = Column(String(500), nullable=False, index=True)  # e.g., "binary search trees"
    learning_style = Column(String(50), nullable=True, index=True)  # visual, audio, reading, kinesthetic, balanced

    # Resource identification
    resource_type = Column(String(50), nullable=False)  # 'youtube', 'reddit'
    resource_id = Column(String(255), nullable=False)  # YouTube video ID or Reddit post ID
    url = Column(Text, nullable=False)

    # Content metadata
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)  # Channel name or Reddit author

    # Quality scores
    quality_score = Column(Numeric(5, 2), nullable=False)  # 0-100 overall quality score
    platform_scores = Column(JSONB, nullable=True)  # {'youtube': 85.5, 'reddit': 72.3}
    cross_referenced = Column(String(10), nullable=False, default='false')  # 'true' or 'false' as string

    # Engagement metrics (stored as JSONB for flexibility)
    engagement_metrics = Column(JSONB, nullable=True)
    # For YouTube: {views, likes, comments, like_view_ratio, etc.}
    # For Reddit: {score, upvote_ratio, num_comments, subreddit}

    # Additional metadata
    resource_metadata = Column(JSONB, nullable=True)  # Flexible field for platform-specific data

    # Transcript/content availability
    has_transcript = Column(String(10), nullable=True)  # 'true', 'false', 'unknown'
    transcript_quality = Column(Numeric(5, 2), nullable=True)  # If analyzed

    # Caching metadata
    cache_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)  # When to refresh
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Composite indexes for efficient querying
    __table_args__ = (
        Index('idx_topic_learning_style', 'topic', 'learning_style'),
        Index('idx_topic_quality', 'topic', 'quality_score'),
        Index('idx_resource_type_quality', 'resource_type', 'quality_score'),
    )

    def __repr__(self):
        return f"<CuratedResource(topic={self.topic}, type={self.resource_type}, quality={self.quality_score})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "topic": self.topic,
            "learning_style": self.learning_style,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "quality_score": float(self.quality_score) if self.quality_score else 0,
            "platform_scores": self.platform_scores,
            "cross_referenced": self.cross_referenced == 'true',
            "engagement_metrics": self.engagement_metrics,
            "resource_metadata": self.resource_metadata,
            "has_transcript": self.has_transcript == 'true' if self.has_transcript else None,
            "transcript_quality": float(self.transcript_quality) if self.transcript_quality else None,
            "cache_expires_at": self.cache_expires_at.isoformat() if self.cache_expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ContentCurationQuery(Base):
    """
    Content Curation Query - Tracks what topics have been curated
    Helps with cache management and analytics
    """
    __tablename__ = "content_curation_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Query details
    topic = Column(String(500), nullable=False, index=True)
    learning_style = Column(String(50), nullable=True)

    # Results summary
    total_resources_found = Column(Integer, default=0)
    youtube_count = Column(Integer, default=0)
    reddit_count = Column(Integer, default=0)
    cross_referenced_count = Column(Integer, default=0)

    # Quality metrics
    avg_quality_score = Column(Numeric(5, 2), nullable=True)
    top_resource_score = Column(Numeric(5, 2), nullable=True)

    # Query metadata
    query_duration_ms = Column(Integer, nullable=True)  # How long the query took
    cache_hit = Column(String(10), nullable=False, default='false')  # Was it served from cache?

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<ContentCurationQuery(topic={self.topic}, resources={self.total_resources_found})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "topic": self.topic,
            "learning_style": self.learning_style,
            "total_resources_found": self.total_resources_found,
            "youtube_count": self.youtube_count,
            "reddit_count": self.reddit_count,
            "cross_referenced_count": self.cross_referenced_count,
            "avg_quality_score": float(self.avg_quality_score) if self.avg_quality_score else 0,
            "top_resource_score": float(self.top_resource_score) if self.top_resource_score else 0,
            "query_duration_ms": self.query_duration_ms,
            "cache_hit": self.cache_hit == 'true',
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
