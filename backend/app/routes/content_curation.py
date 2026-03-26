"""
Content Curation API Routes
Endpoints for accessing YouTube and Reddit curated learning resources
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.content_curator import get_content_curator
from app.middleware.rate_limiter import limiter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/content", tags=["Content Curation"])


class CurateResourcesRequest(BaseModel):
    """Request body for curating resources"""
    topic: str
    learning_style: Optional[str] = "balanced"  # visual, audio, reading, kinesthetic, balanced
    max_results: Optional[int] = 10
    min_quality_score: Optional[float] = 60.0


@router.post(
    "/curate",
    operation_id="curate_resources",
    summary="Curate learning resources for a topic",
)
@limiter.limit("10/minute")
async def curate_resources(
    request: Request,
    body: CurateResourcesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Curate high-quality learning resources for a topic
    Combines YouTube videos and Reddit recommendations

    Args:
        body: Curation request with topic and preferences
        current_user: Authenticated user
        db: Database session

    Returns:
        Curated resources categorized by type and adapted to learning style
    """
    try:
        logger.info(f"User {current_user.id} requesting curation for: {body.topic}")

        curator = get_content_curator()

        # Curate resources
        results = curator.curate_resources(
            topic=body.topic,
            learning_style=body.learning_style,
            max_results=body.max_results,
            min_quality_score=body.min_quality_score
        )

        return {
            "success": True,
            "data": results
        }

    except Exception as e:
        logger.error(f"Error curating resources: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to curate resources"
        )


@router.get(
    "/search",
    operation_id="search_resources",
    summary="Search resources across platforms",
)
@limiter.limit("20/minute")
async def search_resources(
    request: Request,
    query: str = Query(..., description="Search query"),
    resource_type: str = Query("all", description="youtube, reddit, or all"),
    current_user: User = Depends(get_current_user)
):
    """
    Search for specific resources across platforms

    Args:
        query: Search query string
        resource_type: Type of resources to search (youtube, reddit, or all)
        current_user: Authenticated user

    Returns:
        List of matching resources
    """
    try:
        logger.info(f"User {current_user.id} searching for: {query} (type: {resource_type})")

        curator = get_content_curator()

        # Search for resources
        results = curator.search_specific_resource(
            query=query,
            resource_type=resource_type
        )

        return {
            "success": True,
            "query": query,
            "resource_type": resource_type,
            "total_results": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Error searching resources: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to search resources"
        )


@router.get(
    "/summary/{topic}",
    operation_id="get_resource_summary",
    summary="Get resource summary for a topic",
)
async def get_resource_summary(
    topic: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a quick summary of available resources for a topic

    Args:
        topic: Study topic
        current_user: Authenticated user

    Returns:
        Summary with counts and top recommendations
    """
    try:
        logger.info(f"User {current_user.id} requesting summary for: {topic}")

        curator = get_content_curator()

        # Get summary
        summary = curator.get_resource_summary(topic)

        return {
            "success": True,
            "data": summary
        }

    except Exception as e:
        logger.error(f"Error getting resource summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get resource summary"
        )


@router.get(
    "/youtube/videos",
    operation_id="search_youtube_videos",
    summary="Search YouTube for educational videos",
)
async def search_youtube_videos(
    topic: str = Query(..., description="Topic to search for"),
    max_results: int = Query(10, description="Maximum number of results"),
    duration: str = Query("medium", description="Video duration: short, medium, or long"),
    current_user: User = Depends(get_current_user)
):
    """
    Search YouTube for educational videos

    Args:
        topic: Topic to search for
        max_results: Maximum number of results
        duration: Video duration filter
        current_user: Authenticated user

    Returns:
        List of YouTube video metadata
    """
    try:
        logger.info(f"User {current_user.id} searching YouTube for: {topic}")

        curator = get_content_curator()

        # Search YouTube
        videos = curator.youtube.search_videos(
            query=topic,
            max_results=max_results,
            duration=duration
        )

        return {
            "success": True,
            "topic": topic,
            "total_videos": len(videos),
            "videos": videos
        }

    except Exception as e:
        logger.error(f"Error searching YouTube: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to search YouTube"
        )


@router.get(
    "/youtube/curated",
    operation_id="get_curated_youtube",
    summary="Get curated YouTube videos with quality scores",
)
async def get_curated_youtube_videos(
    topic: str = Query(..., description="Topic to search for"),
    max_results: int = Query(5, description="Maximum number of results"),
    min_quality_score: float = Query(50.0, description="Minimum quality threshold"),
    current_user: User = Depends(get_current_user)
):
    """
    Get curated, high-quality YouTube videos with transcripts and comment analysis

    Args:
        topic: Topic to search for
        max_results: Maximum number of results
        min_quality_score: Minimum quality threshold (0-100)
        current_user: Authenticated user

    Returns:
        List of curated YouTube videos with quality scores
    """
    try:
        logger.info(f"User {current_user.id} requesting curated YouTube videos for: {topic}")

        curator = get_content_curator()

        # Get curated videos
        videos = curator.youtube.get_curated_videos(
            topic=topic,
            max_results=max_results,
            min_quality_score=min_quality_score
        )

        return {
            "success": True,
            "topic": topic,
            "total_videos": len(videos),
            "videos": videos
        }

    except Exception as e:
        logger.error(f"Error getting curated YouTube videos: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get curated videos"
        )


@router.get(
    "/reddit/resources",
    operation_id="get_reddit_resources",
    summary="Find learning resources from Reddit",
)
async def get_reddit_resources(
    topic: str = Query(..., description="Topic to search for"),
    max_results: int = Query(10, description="Maximum number of results"),
    min_quality_score: float = Query(50.0, description="Minimum quality threshold"),
    current_user: User = Depends(get_current_user)
):
    """
    Find high-quality learning resources from Reddit

    Args:
        topic: Topic to search for
        max_results: Maximum number of results
        min_quality_score: Minimum quality threshold (0-100)
        current_user: Authenticated user

    Returns:
        List of Reddit-recommended resources
    """
    try:
        logger.info(f"User {current_user.id} requesting Reddit resources for: {topic}")

        curator = get_content_curator()

        # Get Reddit resources
        resources = curator.reddit.find_learning_resources(
            topic=topic,
            max_results=max_results,
            min_quality_score=min_quality_score
        )

        return {
            "success": True,
            "topic": topic,
            "total_resources": len(resources),
            "resources": resources
        }

    except Exception as e:
        logger.error(f"Error getting Reddit resources: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get Reddit resources"
        )


@router.get(
    "/reddit/consensus/{topic}",
    operation_id="get_community_consensus",
    summary="Get community consensus on best resources",
)
async def get_community_consensus(
    topic: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get community consensus on best resources for a topic

    Args:
        topic: Topic to analyze
        current_user: Authenticated user

    Returns:
        Community consensus data with top recommendations
    """
    try:
        logger.info(f"User {current_user.id} requesting community consensus for: {topic}")

        curator = get_content_curator()

        # Get consensus
        consensus = curator.reddit.get_community_consensus(topic)

        return {
            "success": True,
            "data": consensus
        }

    except Exception as e:
        logger.error(f"Error getting community consensus: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get community consensus"
        )


@router.get(
    "/health",
    operation_id="check_content_health",
    summary="Check content curation service health",
)
async def check_health():
    """
    Check if content curation services are available

    Returns:
        Status of YouTube and Reddit services
    """
    try:
        curator = get_content_curator()

        youtube_available = curator.youtube.youtube is not None
        reddit_available = curator.reddit.reddit is not None

        return {
            "success": True,
            "services": {
                "youtube": {
                    "available": youtube_available,
                    "status": "configured" if youtube_available else "missing_api_key"
                },
                "reddit": {
                    "available": reddit_available,
                    "status": "configured" if reddit_available else "missing_credentials"
                }
            }
        }

    except Exception as e:
        logger.error(f"Error checking service health: {e}", exc_info=True)
        return {
            "success": False,
            "error": "Service health check failed"
        }
