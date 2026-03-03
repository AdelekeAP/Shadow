"""
Reddit API Service for Content Curation
Handles subreddit searching, resource recommendations, and community quality signals
"""
import os
import logging
from typing import List, Dict, Optional
import praw
from praw.exceptions import PRAWException

logger = logging.getLogger(__name__)


class RedditService:
    """Service for interacting with Reddit API via PRAW"""

    # Learning-focused subreddits to search
    LEARNING_SUBREDDITS = [
        'learnprogramming',
        'compsci',
        'computerscience',
        'algorithms',
        'datastructures',
        'AskComputerScience',
        'CSEducation',
        'programming',
        'learnpython',
        'learnjava',
        'learnjavascript',
        'webdev',
        'coding',
        'CodingHelp'
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Initialize Reddit service with API credentials

        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
        """
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent or os.getenv(
            "REDDIT_USER_AGENT",
            "Shadow Academic Platform v1.0"
        )

        if not self.client_id or not self.client_secret:
            logger.warning("Reddit API credentials not configured - service will be disabled")
            self.reddit = None
        else:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                logger.info("Reddit service initialized successfully")
            except PRAWException as e:
                logger.error(f"Failed to initialize Reddit service: {e}")
                self.reddit = None

    def search_posts(
        self,
        query: str,
        subreddits: Optional[List[str]] = None,
        limit: int = 50,
        time_filter: str = "all"  # hour, day, week, month, year, all
    ) -> List[Dict]:
        """
        Search for posts across learning subreddits

        Args:
            query: Search query (e.g., "best resources for data structures")
            subreddits: List of subreddit names (defaults to LEARNING_SUBREDDITS)
            limit: Maximum number of posts to retrieve
            time_filter: Time period to search

        Returns:
            List of post dictionaries
        """
        if not self.reddit:
            logger.error("Reddit service not initialized")
            return []

        subreddits = subreddits or self.LEARNING_SUBREDDITS
        all_posts = []

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                # Search within subreddit
                posts = subreddit.search(
                    query,
                    sort='relevance',
                    time_filter=time_filter,
                    limit=limit
                )

                for post in posts:
                    post_data = self._parse_post_data(post)
                    all_posts.append(post_data)

            except Exception as e:
                logger.error(f"Error searching r/{subreddit_name}: {e}")
                continue

        # Sort by quality score (upvote ratio * score)
        all_posts.sort(
            key=lambda x: x['upvote_ratio'] * x['score'],
            reverse=True
        )

        logger.info(f"Found {len(all_posts)} posts for query: {query}")
        return all_posts[:limit]

    def _parse_post_data(self, post) -> Dict:
        """
        Parse raw post data from Reddit API

        Args:
            post: PRAW Submission object

        Returns:
            Cleaned post metadata dictionary
        """
        return {
            'post_id': post.id,
            'title': post.title,
            'selftext': post.selftext,
            'author': str(post.author) if post.author else '[deleted]',
            'subreddit': str(post.subreddit),
            'score': post.score,
            'upvote_ratio': post.upvote_ratio,
            'num_comments': post.num_comments,
            'created_utc': post.created_utc,
            'url': post.url,
            'permalink': f"https://reddit.com{post.permalink}",
            'is_self': post.is_self
        }

    def get_top_comments(self, post_id: str, limit: int = 50) -> List[Dict]:
        """
        Get top-level comments for a post

        Args:
            post_id: Reddit post ID
            limit: Maximum number of comments to retrieve

        Returns:
            List of comment dictionaries
        """
        if not self.reddit:
            logger.error("Reddit service not initialized")
            return []

        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Remove "More Comments" objects

            comments = []
            for comment in submission.comments.list()[:limit]:
                if hasattr(comment, 'body'):
                    comments.append({
                        'comment_id': comment.id,
                        'body': comment.body,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'score': comment.score,
                        'created_utc': comment.created_utc
                    })

            return comments

        except Exception as e:
            logger.error(f"Error getting comments for post {post_id}: {e}")
            return []

    def extract_resource_urls(self, posts: List[Dict]) -> List[Dict]:
        """
        Extract URLs and resource recommendations from posts

        Args:
            posts: List of post dictionaries

        Returns:
            List of resource dictionaries with URLs and quality signals
        """
        resources = []

        for post in posts:
            # Check if post contains URL recommendations
            text = f"{post['title']} {post['selftext']}"

            # Common patterns for resource recommendations
            resource_indicators = [
                'recommend', 'suggestion', 'resource', 'tutorial',
                'course', 'book', 'video', 'guide', 'learn',
                'best', 'top', 'favorite', 'helpful'
            ]

            is_resource_post = any(
                indicator in text.lower()
                for indicator in resource_indicators
            )

            if is_resource_post or not post['is_self']:
                resource = {
                    'title': post['title'],
                    'url': post['url'] if not post['is_self'] else post['permalink'],
                    'source': 'reddit',
                    'subreddit': post['subreddit'],
                    'score': post['score'],
                    'upvote_ratio': post['upvote_ratio'],
                    'num_comments': post['num_comments'],
                    'quality_score': self._calculate_post_quality_score(post),
                    'description': post['selftext'][:500] if post['selftext'] else '',
                    'reddit_url': post['permalink']
                }
                resources.append(resource)

        # Sort by quality score
        resources.sort(key=lambda x: x['quality_score'], reverse=True)

        return resources

    def _calculate_post_quality_score(self, post: Dict) -> float:
        """
        Calculate quality score for a Reddit post

        Factors:
        - Upvote ratio (40%)
        - Post score/karma (30%)
        - Number of comments (20%)
        - Subreddit reputation (10%)

        Args:
            post: Post metadata dictionary

        Returns:
            Quality score (0-100)
        """
        score = 0.0

        # Upvote ratio (40%)
        # 0.8+ is generally considered high quality on Reddit
        upvote_score = (post['upvote_ratio'] - 0.5) / 0.5 * 100
        upvote_score = max(0, min(upvote_score, 100))  # Clamp 0-100
        score += upvote_score * 0.40

        # Post score (30%)
        # Logarithmic scaling: 10 upvotes = 30, 100 = 60, 1000+ = 100
        import math
        post_score = post['score']
        if post_score > 0:
            karma_score = min(math.log10(post_score + 1) / 3 * 100, 100)
            score += karma_score * 0.30

        # Comment engagement (20%)
        # More comments generally indicate valuable discussion
        num_comments = post['num_comments']
        if num_comments > 0:
            comment_score = min(math.log10(num_comments + 1) / 2 * 100, 100)
            score += comment_score * 0.20

        # Subreddit reputation (10%)
        # Premium subreddits get bonus points
        premium_subreddits = [
            'compsci', 'computerscience', 'CSEducation',
            'AskComputerScience', 'algorithms'
        ]
        if post['subreddit'] in premium_subreddits:
            score += 80 * 0.10
        else:
            score += 50 * 0.10

        return round(score, 2)

    def find_learning_resources(
        self,
        topic: str,
        max_results: int = 10,
        min_quality_score: float = 50.0
    ) -> List[Dict]:
        """
        Find high-quality learning resources for a topic from Reddit

        Args:
            topic: Study topic (e.g., "binary search algorithms")
            max_results: Maximum number of resources to return
            min_quality_score: Minimum quality threshold

        Returns:
            List of curated resource dictionaries
        """
        # Search for resource recommendation posts
        search_queries = [
            f"{topic} tutorial",
            f"{topic} resources",
            f"{topic} course",
            f"learn {topic}",
            f"best way to learn {topic}"
        ]

        all_resources = []

        for query in search_queries:
            posts = self.search_posts(query, limit=20)
            resources = self.extract_resource_urls(posts)

            for resource in resources:
                if resource['quality_score'] >= min_quality_score:
                    all_resources.append(resource)

        # Remove duplicates based on URL
        seen_urls = set()
        unique_resources = []

        for resource in all_resources:
            if resource['url'] not in seen_urls:
                seen_urls.add(resource['url'])
                unique_resources.append(resource)

        # Sort by quality score
        unique_resources.sort(key=lambda x: x['quality_score'], reverse=True)

        logger.info(f"Found {len(unique_resources)} high-quality resources for topic: {topic}")
        return unique_resources[:max_results]

    def get_community_consensus(self, topic: str) -> Dict:
        """
        Get community consensus on best resources for a topic

        Args:
            topic: Study topic

        Returns:
            Dictionary with consensus data
        """
        resources = self.find_learning_resources(topic, max_results=50)

        if not resources:
            return {
                'topic': topic,
                'total_resources': 0,
                'top_resources': [],
                'common_recommendations': []
            }

        # Find most commonly mentioned domains
        domain_counts = {}
        for resource in resources:
            url = resource['url']
            # Extract domain
            if 'youtube.com' in url or 'youtu.be' in url:
                domain = 'YouTube'
            elif 'reddit.com' in url:
                domain = 'Reddit Discussion'
            else:
                domain = url.split('/')[2] if '/' in url else url

            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Get top recommended domains
        common_recommendations = sorted(
            domain_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'topic': topic,
            'total_resources': len(resources),
            'top_resources': resources[:10],
            'common_recommendations': [
                {'domain': domain, 'count': count}
                for domain, count in common_recommendations
            ]
        }


# Singleton instance
_reddit_service = None

def get_reddit_service() -> RedditService:
    """Get or create Reddit service singleton"""
    global _reddit_service
    if _reddit_service is None:
        _reddit_service = RedditService()
    return _reddit_service
