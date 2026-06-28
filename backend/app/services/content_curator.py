"""
Content Curator Service
Combines YouTube and Reddit to find and rank the best learning resources
Adapts recommendations based on learning styles
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone

from app.services.youtube_service import get_youtube_service

try:
    from app.services.reddit_service import get_reddit_service
except ImportError:
    get_reddit_service = lambda: None  # praw not installed

logger = logging.getLogger(__name__)


class ContentCurator:
    """
    Main service for curating high-quality learning resources
    Combines YouTube videos and Reddit recommendations
    """

    def __init__(self):
        self.youtube = get_youtube_service()
        self.reddit = get_reddit_service()

    def curate_resources(
        self,
        topic: str,
        learning_style: str = "balanced",
        max_results: int = 10,
        min_quality_score: float = 60.0,
        subtopics: Optional[List[str]] = None
    ) -> Dict:
        """
        Curate high-quality learning resources for a topic

        Args:
            topic: Study topic (e.g., "binary search trees")
            learning_style: visual, audio, reading, kinesthetic, or balanced
            max_results: Maximum number of resources to return per type
            min_quality_score: Minimum quality threshold (0-100)

        Returns:
            Dictionary with curated resources categorized by type
        """
        logger.info(f"Curating resources for topic: {topic} (style: {learning_style})")

        results = {
            'topic': topic,
            'learning_style': learning_style,
            'curated_at': datetime.now(timezone.utc).isoformat(),
            'videos': [],
            'reddit_resources': [],
            'combined_recommendations': []
        }

        # Get YouTube videos (pass subtopics for more specific searches)
        # Use full quality mode (transcripts + comments) for better curation
        def _fetch_videos(fast: bool):
            return self.youtube.get_curated_videos(
                topic=topic,
                max_results=max_results * 2,  # Get extra for filtering
                min_quality_score=min_quality_score,
                fast_mode=fast,
                subtopics=subtopics or []
            )

        try:
            videos = _fetch_videos(fast=False)  # Full quality: transcripts + comment analysis
            # Graceful fallback: full mode depends on transcripts/comments which are
            # frequently unavailable on cloud hosts (e.g. Railway). When that enrichment
            # fails, quality scores collapse below threshold and every video is filtered
            # out, leaving plans with no videos. Fast mode scores on view/like/comment
            # metadata only, so retry there so videos still attach.
            if not videos:
                logger.warning(
                    f"Full-mode YouTube curation returned 0 videos for '{topic}'; "
                    "falling back to fast mode (metadata-only scoring)"
                )
                videos = _fetch_videos(fast=True)
            results['videos'] = videos[:max_results]
            logger.info(f"Found {len(results['videos'])} high-quality YouTube videos")
        except Exception as e:
            logger.error(f"Error fetching YouTube videos: {e}")
            # Last-resort fallback after an exception in full mode
            try:
                videos = _fetch_videos(fast=True)
                results['videos'] = videos[:max_results]
                logger.info(f"Fast-mode fallback recovered {len(results['videos'])} YouTube videos")
            except Exception as e2:
                logger.error(f"Fast-mode YouTube fallback also failed: {e2}")

        # Get Reddit resources (gracefully handle if not configured)
        try:
            if self.reddit.reddit is not None:
                reddit_resources = self.reddit.find_learning_resources(
                    topic=topic,
                    max_results=max_results,
                    min_quality_score=min_quality_score
                )
                results['reddit_resources'] = reddit_resources
                logger.info(f"Found {len(reddit_resources)} Reddit resources")
            else:
                logger.info("Reddit service not configured - skipping Reddit resources")
                results['reddit_resources'] = []
        except Exception as e:
            logger.error(f"Error fetching Reddit resources: {e}")
            results['reddit_resources'] = []

        # Combine and cross-reference
        combined = self._combine_and_cross_reference(
            results['videos'],
            results['reddit_resources']
        )

        # Adapt to learning style
        adapted = self._adapt_to_learning_style(
            combined,
            learning_style,
            max_results
        )

        results['combined_recommendations'] = adapted

        return results

    def _combine_and_cross_reference(
        self,
        videos: List[Dict],
        reddit_resources: List[Dict]
    ) -> List[Dict]:
        """
        Combine YouTube and Reddit resources, boosting cross-referenced items

        Args:
            videos: YouTube video list
            reddit_resources: Reddit resource list

        Returns:
            Combined and scored resource list
        """
        combined = []

        # Add YouTube videos
        for video in videos:
            resource = {
                'type': 'youtube_video',  # Match frontend expectation
                'title': video['title'],
                'url': video['url'],
                'description': video.get('description', ''),
                'quality_score': video['quality_score'],
                'platform_scores': {
                    'youtube': video['quality_score']
                },
                'cross_referenced': False,
                'metadata': {
                    'channel': video.get('channel_title', ''),
                    'views': video.get('view_count', 0),
                    'likes': video.get('like_count', 0),
                    'has_transcript': video.get('has_transcript', False)
                }
            }
            combined.append(resource)

        # Add Reddit resources
        for reddit_res in reddit_resources:
            # Check if it's a YouTube link mentioned on Reddit
            is_youtube = 'youtube.com' in reddit_res['url'] or 'youtu.be' in reddit_res['url']

            if is_youtube:
                # Find matching YouTube video and boost its score
                for resource in combined:
                    if resource['type'] == 'youtube_video' and reddit_res['url'] in resource['url']:
                        # Cross-referenced! Boost quality score
                        resource['cross_referenced'] = True
                        resource['platform_scores']['reddit'] = reddit_res['quality_score']

                        # Calculate boosted score
                        youtube_score = resource['platform_scores']['youtube']
                        reddit_score = reddit_res['quality_score']
                        boosted_score = (youtube_score * 0.6) + (reddit_score * 0.4) + 15  # +15 bonus for cross-reference

                        resource['quality_score'] = min(boosted_score, 100)
                        logger.info(f"Cross-referenced resource: {resource['title']} (boosted to {resource['quality_score']})")
                        break
            else:
                # Add as separate Reddit resource
                resource = {
                    'type': 'reddit_post',  # Match frontend expectation
                    'title': reddit_res['title'],
                    'url': reddit_res['url'],
                    'description': reddit_res.get('description', ''),
                    'quality_score': reddit_res['quality_score'],
                    'platform_scores': {
                        'reddit': reddit_res['quality_score']
                    },
                    'cross_referenced': False,
                    'metadata': {
                        'subreddit': reddit_res.get('subreddit', ''),
                        'score': reddit_res.get('score', 0),
                        'upvote_ratio': reddit_res.get('upvote_ratio', 0),
                        'num_comments': reddit_res.get('num_comments', 0)
                    }
                }
                combined.append(resource)

        # Sort by quality score
        combined.sort(key=lambda x: x['quality_score'], reverse=True)

        return combined

    def _adapt_to_learning_style(
        self,
        resources: List[Dict],
        learning_style: str,
        max_results: int
    ) -> List[Dict]:
        """
        Adapt resource recommendations based on learning style

        Learning Styles:
        - visual: Prefer YouTube videos, diagrams, visual content
        - audio: Prefer videos with good audio explanations, podcasts
        - reading: Prefer articles, documentation, written guides
        - kinesthetic: Prefer interactive tutorials, hands-on projects
        - balanced: Mix of all types

        Args:
            resources: Combined resource list
            learning_style: User's preferred learning style
            max_results: Maximum results to return

        Returns:
            Adapted and filtered resource list
        """
        if learning_style == "balanced":
            # Return top resources regardless of type
            return resources[:max_results]

        # Apply style-specific filtering and boosting
        for resource in resources:
            style_boost = self._calculate_style_boost(resource, learning_style)
            resource['quality_score'] = min(resource['quality_score'] + style_boost, 100)
            resource['style_match'] = style_boost > 0

        # Sort again after style boosting
        resources.sort(key=lambda x: x['quality_score'], reverse=True)

        # Filter to ensure style diversity
        adapted = []
        style_preferences = self._get_style_preferences(learning_style)

        # For visual learners, prioritize getting ALL available videos first
        if learning_style == "visual":
            # First, add all YouTube videos
            for resource in resources:
                if resource['type'] == 'youtube_video':
                    adapted.append(resource)

            # Then add other resources up to max_results
            for resource in resources:
                if resource['type'] != 'youtube_video' and len(adapted) < max_results:
                    adapted.append(resource)

            return adapted[:max_results]

        # For kinesthetic learners, prioritize style-matched content first
        if learning_style == "kinesthetic":
            # First, add resources with style_match (hands-on keywords detected)
            for resource in resources:
                if resource.get('style_match'):
                    adapted.append(resource)

            # Then fill with remaining resources up to max_results
            for resource in resources:
                if not resource.get('style_match') and len(adapted) < max_results:
                    adapted.append(resource)

            return adapted[:max_results]

        # Standard behavior for other learning styles
        for resource in resources:
            # Check if resource matches preferred types
            if resource['type'] in style_preferences['preferred_types']:
                adapted.append(resource)
            elif len(adapted) < max_results // 2:
                # Include some diverse content even if not preferred
                adapted.append(resource)

            if len(adapted) >= max_results:
                break

        return adapted

    def _calculate_style_boost(self, resource: Dict, learning_style: str) -> float:
        """
        Calculate quality score boost based on learning style match

        Args:
            resource: Resource dictionary
            learning_style: User's learning style

        Returns:
            Boost amount (0-20 points)
        """
        boost = 0.0

        if learning_style == "visual":
            if resource['type'] == 'youtube_video':
                boost += 15
                # Extra boost for videos with transcripts (likely well-structured)
                if resource['metadata'].get('has_transcript'):
                    boost += 5

        elif learning_style == "audio":
            if resource['type'] == 'youtube_video':
                boost += 15
                # Extra boost for lecture-style content
                title_lower = resource['title'].lower()
                if any(kw in title_lower for kw in ['lecture', 'explanation', 'podcast', 'talk']):
                    boost += 5

        elif learning_style == "reading":
            if resource['type'] == 'reddit_post':
                boost += 15
            # YouTube videos with transcripts can be "read"
            elif resource['type'] == 'youtube_video' and resource['metadata'].get('has_transcript'):
                boost += 8

        elif learning_style == "kinesthetic":
            # Boost hands-on and interactive content
            title_lower = resource['title'].lower()
            if any(keyword in title_lower for keyword in ['hands-on', 'build', 'project', 'practice', 'interactive', 'exercise', 'lab', 'workshop']):
                boost += 15
                # Extra boost for coding-specific content
                if any(kw in title_lower for kw in ['code', 'coding', 'implement', 'tutorial', 'step-by-step']):
                    boost += 5

        return boost

    def _get_style_preferences(self, learning_style: str) -> Dict:
        """
        Get content type preferences for a learning style

        Args:
            learning_style: User's learning style

        Returns:
            Dictionary with preferred types and characteristics
        """
        preferences = {
            'visual': {
                'preferred_types': ['youtube_video'],
                'keywords': ['diagram', 'visualization', 'animated', 'visual']
            },
            'audio': {
                'preferred_types': ['youtube_video'],
                'keywords': ['explanation', 'lecture', 'talk', 'podcast']
            },
            'reading': {
                'preferred_types': ['reddit_post', 'youtube_video'],  # Include YouTube for transcripts
                'keywords': ['article', 'documentation', 'guide', 'written', 'text']
            },
            'kinesthetic': {
                'preferred_types': ['youtube_video', 'reddit_post'],
                'keywords': ['hands-on', 'build', 'project', 'practice', 'exercise', 'interactive']
            },
            'balanced': {
                'preferred_types': ['youtube_video', 'reddit_post'],
                'keywords': []
            }
        }

        return preferences.get(learning_style, preferences['balanced'])

    def get_resource_summary(self, topic: str) -> Dict:
        """
        Get a quick summary of available resources for a topic

        Args:
            topic: Study topic

        Returns:
            Summary dictionary with counts and top recommendations
        """
        try:
            # Quick search with lower limits
            videos = self.youtube.search_videos(topic, max_results=5)
            reddit_consensus = self.reddit.get_community_consensus(topic)

            return {
                'topic': topic,
                'video_count': len(videos),
                'reddit_resource_count': reddit_consensus['total_resources'],
                'top_video': videos[0] if videos else None,
                'common_recommendations': reddit_consensus['common_recommendations']
            }

        except Exception as e:
            logger.error(f"Error getting resource summary: {e}")
            return {
                'topic': topic,
                'error': str(e)
            }

    def search_specific_resource(self, query: str, resource_type: str = "all") -> List[Dict]:
        """
        Search for specific resources across platforms

        Args:
            query: Search query
            resource_type: "youtube", "reddit", or "all"

        Returns:
            List of matching resources
        """
        results = []

        if resource_type in ["youtube", "all"]:
            try:
                videos = self.youtube.search_videos(query, max_results=10)
                for video in videos:
                    results.append({
                        'type': 'youtube_video',
                        'title': video['title'],
                        'url': video['url'],
                        'metadata': video
                    })
            except Exception as e:
                logger.error(f"Error searching YouTube: {e}")

        if resource_type in ["reddit", "all"]:
            try:
                reddit_posts = self.reddit.search_posts(query, limit=10)
                for post in reddit_posts:
                    results.append({
                        'type': 'reddit',
                        'title': post['title'],
                        'url': post['permalink'],
                        'metadata': post
                    })
            except Exception as e:
                logger.error(f"Error searching Reddit: {e}")

        return results


# Singleton instance
_content_curator = None

def get_content_curator() -> ContentCurator:
    """Get or create ContentCurator singleton"""
    global _content_curator
    if _content_curator is None:
        _content_curator = ContentCurator()
    return _content_curator
