"""
YouTube API Service for Content Curation
Handles video search, transcript extraction, and quality metrics
"""
import os
import logging
import time
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# In-memory cache for YouTube API results (24-hour TTL)
_youtube_cache: Dict[str, dict] = {}
_CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours

# Quota tracking — YouTube Data API v3 gives 10,000 units/day
# search().list costs ~100 units, videos().list costs ~1 unit
_DAILY_QUOTA_LIMIT = 10_000
_QUOTA_WARNING_PCT = 0.80  # warn at 80%
_quota_tracker: Dict[str, int] = {"units": 0, "reset_day": 0}


def _track_quota(units: int) -> None:
    """Track daily YouTube API quota usage and warn when approaching limit."""
    import datetime
    today = datetime.date.today().toordinal()
    if _quota_tracker["reset_day"] != today:
        _quota_tracker["units"] = 0
        _quota_tracker["reset_day"] = today
        # Reset exhausted keys on new day — all quotas refresh at midnight PT
        if _youtube_service and hasattr(_youtube_service, '_exhausted_keys'):
            _youtube_service._exhausted_keys.clear()
    _quota_tracker["units"] += units
    used = _quota_tracker["units"]
    if used >= _DAILY_QUOTA_LIMIT:
        logger.error(f"YouTube API daily quota EXCEEDED ({used}/{_DAILY_QUOTA_LIMIT} units)", exc_info=True)
    elif used >= _DAILY_QUOTA_LIMIT * _QUOTA_WARNING_PCT:
        logger.warning(f"YouTube API quota at {used}/{_DAILY_QUOTA_LIMIT} units ({round(used/_DAILY_QUOTA_LIMIT*100)}%)")


def _cache_key(query: str, max_results: int, duration: str, order: str) -> str:
    """Generate a cache key from search parameters."""
    return f"{query}|{max_results}|{duration}|{order}"


class YouTubeService:
    """Service for interacting with YouTube Data API v3.

    Supports multiple API keys for automatic rotation when quota is exhausted.
    Set YOUTUBE_API_KEY to a comma-separated list of keys in .env:
        YOUTUBE_API_KEY=key1,key2,key3
    When one key hits quota, the service automatically rotates to the next.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube service with one or more API keys.

        Args:
            api_key: Single key or comma-separated keys (defaults to env variable)
        """
        raw_keys = api_key or os.getenv("YOUTUBE_API_KEY", "")
        self._api_keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        self._current_key_index = 0
        self._exhausted_keys: set = set()  # Keys that hit quota today

        if not self._api_keys:
            logger.warning("YouTube API key not configured - service will be disabled")
            self.youtube = None
            self.api_key = None
        else:
            self.api_key = self._api_keys[0]
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            if len(self._api_keys) > 1:
                logger.info(f"YouTube service initialized with {len(self._api_keys)} API keys (rotation enabled)")

    def _rotate_key(self) -> bool:
        """Try rotating to the next available API key.

        Returns True if a fresh key was activated, False if all keys are exhausted.
        """
        self._exhausted_keys.add(self.api_key)
        for i in range(len(self._api_keys)):
            candidate = self._api_keys[(self._current_key_index + 1 + i) % len(self._api_keys)]
            if candidate not in self._exhausted_keys:
                self._current_key_index = self._api_keys.index(candidate)
                self.api_key = candidate
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
                logger.info(f"Rotated to YouTube API key #{self._current_key_index + 1}/{len(self._api_keys)}")
                return True
        logger.error("All YouTube API keys exhausted — no more keys to rotate to", exc_info=True)
        return False

    def search_videos(
        self,
        query: str,
        max_results: int = 10,
        duration: str = "medium",  # short (<4min), medium (4-20min), long (>20min)
        order: str = "relevance",  # relevance, viewCount, rating, date
        _retry_depth: int = 0
    ) -> List[Dict]:
        """
        Search for educational videos on YouTube

        Args:
            query: Search query (e.g., "python data structures tutorial")
            max_results: Maximum number of results to return
            duration: Video duration filter
            order: Sort order for results

        Returns:
            List of video metadata dictionaries
        """
        if not self.youtube:
            logger.error("YouTube service not initialized - missing API key", exc_info=True)
            return []

        # Check in-memory cache first
        key = _cache_key(query, max_results, duration, order)
        cached = _youtube_cache.get(key)
        if cached and (time.time() - cached["ts"]) < _CACHE_TTL_SECONDS:
            logger.info(f"YouTube cache hit for '{query}' ({len(cached['data'])} results)")
            return cached["data"]

        try:
            # Search for videos
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                maxResults=max_results,
                type='video',
                videoDuration=duration,
                order=order,
                relevanceLanguage='en',
                safeSearch='moderate'
            ).execute()

            _track_quota(100)  # search().list costs ~100 units

            # Extract video IDs
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

            if not video_ids:
                logger.info(f"No videos found for query: {query}")
                return []

            # Get detailed video statistics
            videos_response = self.youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            _track_quota(1)  # videos().list costs ~1 unit

            videos = []
            for item in videos_response.get('items', []):
                video_data = self._parse_video_data(item)
                videos.append(video_data)

            logger.info(f"Found {len(videos)} videos for query: {query}")

            # Store in cache
            _youtube_cache[key] = {"data": videos, "ts": time.time()}

            return videos

        except Exception as e:
            error_str = str(e).lower()
            # Detect quota exhaustion and try rotating to next key (with depth limit)
            if "quota" in error_str or "rateLimitExceeded" in str(e) or "403" in error_str:
                logger.warning(f"YouTube API quota exceeded for key #{self._current_key_index + 1}: {e}")
                if _retry_depth < len(self._api_keys) and self._rotate_key():
                    logger.info(f"Retrying search with rotated key (attempt {_retry_depth + 1})...")
                    return self.search_videos(query, max_results, duration, order, _retry_depth=_retry_depth + 1)
            logger.error(f"Error searching YouTube for query '{query}': {e}", exc_info=True)
            return []

    def _parse_video_data(self, item: Dict) -> Dict:
        """
        Parse raw video data from YouTube API response

        Args:
            item: Raw video item from API

        Returns:
            Cleaned video metadata dictionary
        """
        video_id = item['id']
        snippet = item['snippet']
        statistics = item.get('statistics', {})
        content_details = item.get('contentDetails', {})

        # Calculate engagement metrics
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))

        # Like-to-view ratio (quality signal)
        like_view_ratio = (like_count / view_count * 100) if view_count > 0 else 0

        # Comment-to-view ratio (engagement signal)
        comment_view_ratio = (comment_count / view_count * 100) if view_count > 0 else 0

        return {
            'video_id': video_id,
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'channel_title': snippet.get('channelTitle', ''),
            'published_at': snippet.get('publishedAt', ''),
            'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
            'duration': content_details.get('duration', ''),
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'like_view_ratio': round(like_view_ratio, 2),
            'comment_view_ratio': round(comment_view_ratio, 2),
            'url': f"https://www.youtube.com/watch?v={video_id}"
        }

    def get_video_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript/captions for a video

        Args:
            video_id: YouTube video ID

        Returns:
            Full transcript text or None if unavailable
        """
        try:
            # Import here to avoid issues
            from youtube_transcript_api import YouTubeTranscriptApi as TranscriptAPI
            from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

            # Try to get English transcript
            transcript_list = TranscriptAPI.get_transcript(
                video_id,
                languages=['en', 'en-US', 'en-GB']
            )

            # Combine all text segments
            full_transcript = ' '.join([entry['text'] for entry in transcript_list])

            logger.info(f"Retrieved transcript for video {video_id} ({len(full_transcript)} chars)")
            return full_transcript

        except Exception as e:
            # Handle all errors gracefully (transcripts may not be available)
            logger.debug(f"Transcript not available for {video_id}: {e}")
            return None

    def get_video_comments(
        self,
        video_id: str,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Get top comments for a video (for quality analysis)

        Args:
            video_id: YouTube video ID
            max_results: Maximum number of comments to retrieve

        Returns:
            List of comment dictionaries
        """
        if not self.youtube:
            logger.error("YouTube service not initialized", exc_info=True)
            return []

        try:
            # Get comment threads
            comments_response = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(max_results, 100),  # API limit
                order='relevance',  # Most relevant comments first
                textFormat='plainText'
            ).execute()

            _track_quota(1)  # commentThreads().list costs ~1 unit

            comments = []
            for item in comments_response.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']

                comments.append({
                    'text': snippet['textDisplay'],
                    'author': snippet['authorDisplayName'],
                    'like_count': snippet['likeCount'],
                    'published_at': snippet['publishedAt']
                })

            logger.info(f"Retrieved {len(comments)} comments for video {video_id}")
            return comments

        except Exception as e:
            logger.error(f"Error getting comments for video {video_id}: {e}", exc_info=True)
            return []

    def analyze_comment_sentiment(self, comments: List[Dict]) -> Dict:
        """
        Analyze sentiment of video comments (simple keyword-based)

        Args:
            comments: List of comment dictionaries

        Returns:
            Sentiment analysis results
        """
        if not comments:
            return {
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'positive_percentage': 0,
                'quality_score': 0
            }

        # Simple keyword-based sentiment analysis
        positive_keywords = [
            'great', 'excellent', 'amazing', 'helpful', 'clear', 'perfect',
            'best', 'awesome', 'fantastic', 'love', 'thank', 'understand',
            'easy', 'simple', 'good', 'well explained'
        ]

        negative_keywords = [
            'bad', 'terrible', 'confusing', 'unclear', 'waste', 'boring',
            'useless', 'wrong', 'difficult', 'hard', 'not helpful', 'poor'
        ]

        positive_count = 0
        negative_count = 0

        for comment in comments:
            text = comment['text'].lower()

            # Check for positive keywords
            if any(keyword in text for keyword in positive_keywords):
                positive_count += 1
            # Check for negative keywords
            elif any(keyword in text for keyword in negative_keywords):
                negative_count += 1

        neutral_count = len(comments) - positive_count - negative_count
        positive_percentage = (positive_count / len(comments) * 100) if comments else 0

        # Quality score based on sentiment (0-100)
        quality_score = positive_percentage * 0.7 + (1 - negative_count / len(comments)) * 30

        return {
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'positive_percentage': round(positive_percentage, 2),
            'quality_score': round(quality_score, 2)
        }

    def get_curated_videos(
        self,
        topic: str,
        max_results: int = 5,
        min_quality_score: float = 50.0,
        fast_mode: bool = True,
        subtopics: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Get curated, high-quality videos for a topic
        Combines search, transcripts, and comment analysis

        Args:
            topic: Study topic (e.g., "binary search trees")
            max_results: Maximum number of videos to return
            min_quality_score: Minimum quality threshold
            fast_mode: If True, skip transcript/comment analysis for speed

        Returns:
            List of curated video dictionaries with quality scores
        """
        # Search for videos (get more than needed for filtering)
        # Try multiple search queries for better coverage
        # Use subtopics (if provided) for more specific searches
        if subtopics:
            # Mix specific subtopic queries with a broad topic fallback
            search_queries = [
                f"{topic} tutorial",  # Always search the main topic first
                f"{topic} {subtopics[0]} explained" if len(subtopics) > 0 else f"{topic} explained",
                f"{topic} {subtopics[1] if len(subtopics) > 1 else ''} lecture".strip(),
            ]
        else:
            search_queries = [
                f"{topic} tutorial",
                f"{topic} explained",
                f"learn {topic}",
            ]

        all_videos = []
        seen_ids = set()

        for query in search_queries:
            videos = self.search_videos(
                query=query,
                max_results=max_results * 2,
                duration="medium"  # Prefer 4-20 minute tutorials
            )

            for video in videos:
                if video['video_id'] not in seen_ids:
                    all_videos.append(video)
                    seen_ids.add(video['video_id'])

            # Stop if we have enough candidates
            if len(all_videos) >= max_results * 4:
                break

        if not all_videos:
            logger.warning(f"No videos found for topic: {topic}")
            return []

        logger.info(f"Found {len(all_videos)} candidate videos for topic: {topic}")

        curated_videos = []

        for video in all_videos:
            try:
                if fast_mode:
                    # Fast mode: Use basic metrics only (no extra API calls)
                    # Calculate a simpler quality score based on available data
                    video['has_transcript'] = False
                    video['transcript'] = None
                    video['comment_sentiment'] = {'quality_score': 50}

                    # Simple quality score based on engagement
                    quality_score = self._calculate_fast_quality_score(video)
                else:
                    # Full mode: Get transcript and comments (slower, more accurate)
                    transcript = self.get_video_transcript(video['video_id'])
                    video['has_transcript'] = transcript is not None
                    video['transcript'] = transcript

                    comments = self.get_video_comments(video['video_id'], max_results=50)
                    sentiment = self.analyze_comment_sentiment(comments)
                    video['comment_sentiment'] = sentiment

                    quality_score = self._calculate_video_quality_score(video, sentiment)

                video['quality_score'] = quality_score

                # Only include videos above quality threshold
                if quality_score >= min_quality_score:
                    curated_videos.append(video)

            except Exception as e:
                logger.error(f"Error processing video {video['video_id']} for topic '{topic}': {e}", exc_info=True)
                # Still include the video with a base score on error
                video['quality_score'] = 45.0
                video['has_transcript'] = False
                if video['quality_score'] >= min_quality_score:
                    curated_videos.append(video)
                continue

        # Sort by quality score (highest first)
        curated_videos.sort(key=lambda x: x['quality_score'], reverse=True)

        logger.info(f"Curated {len(curated_videos)} high-quality videos for topic: {topic}")
        return curated_videos[:max_results]

    def _calculate_fast_quality_score(self, video: Dict) -> float:
        """
        Calculate a quick quality score based on basic metrics only
        Used in fast_mode to avoid extra API calls

        Args:
            video: Video metadata

        Returns:
            Quality score (0-100)
        """
        import math

        score = 0.0

        # Like-to-view ratio (40%) - most important signal
        like_ratio = video.get('like_view_ratio', 0)
        like_score = min(like_ratio / 8 * 100, 100)  # 8% ratio = perfect score
        score += like_score * 0.40

        # View count (30%) - normalized logarithmically
        view_count = video.get('view_count', 0)
        if view_count > 0:
            # 1000 views = 40, 10000 = 55, 100000 = 70, 1M = 85, 10M = 100
            view_score = min(math.log10(view_count) / 7 * 100, 100)
            score += view_score * 0.30

        # Comment engagement (20%)
        comment_ratio = video.get('comment_view_ratio', 0)
        comment_score = min(comment_ratio / 0.3 * 100, 100)  # 0.3% = perfect
        score += comment_score * 0.20

        # Base score for being from YouTube (10%)
        score += 10

        return round(score, 2)

    def _calculate_video_quality_score(self, video: Dict, sentiment: Dict) -> float:
        """
        Calculate overall quality score for a video

        Factors:
        - Like-to-view ratio (30%)
        - Comment sentiment (25%)
        - Transcript availability (20%)
        - View count (normalized, 15%)
        - Comment engagement (10%)

        Args:
            video: Video metadata
            sentiment: Comment sentiment analysis

        Returns:
            Quality score (0-100)
        """
        score = 0.0

        # Like-to-view ratio (30%)
        # Good videos typically have 2-10% like ratio
        like_ratio = video['like_view_ratio']
        like_score = min(like_ratio / 10 * 100, 100)  # Cap at 100
        score += like_score * 0.30

        # Comment sentiment (25%)
        score += sentiment['quality_score'] * 0.25

        # Transcript availability (20%)
        score += 100 * 0.20 if video['has_transcript'] else 0

        # View count (15%) - normalized logarithmically
        # 1000 views = 30, 10000 = 50, 100000 = 70, 1M+ = 100
        import math
        view_count = video['view_count']
        if view_count > 0:
            view_score = min(math.log10(view_count) / 6 * 100, 100)
            score += view_score * 0.15

        # Comment engagement (10%)
        comment_ratio = video['comment_view_ratio']
        comment_score = min(comment_ratio / 0.5 * 100, 100)  # Cap at 0.5% comment ratio
        score += comment_score * 0.10

        return round(score, 2)


# Singleton instance
_youtube_service = None

def get_youtube_service() -> YouTubeService:
    """Get or create YouTube service singleton"""
    global _youtube_service
    if _youtube_service is None:
        _youtube_service = YouTubeService()
    return _youtube_service
