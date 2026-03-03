"""
Article Search Service
Finds real, validated article URLs using the Serper.dev Google Search API.
Free tier: 2,500 queries.
"""
import os
import logging
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

# Domain whitelist with quality boosts
HIGH_QUALITY_DOMAINS = {
    "developer.mozilla.org": 90,
    "mdn.dev": 90,
    "freecodecamp.org": 88,
    "www.freecodecamp.org": 88,
    "geeksforgeeks.org": 85,
    "www.geeksforgeeks.org": 85,
    "realpython.com": 88,
    "javascript.info": 87,
    "css-tricks.com": 85,
    "web.dev": 88,
    "docs.python.org": 90,
    "react.dev": 90,
    "www.programiz.com": 83,
    "stackoverflow.com": 82,
    "baeldung.com": 85,
    "digitalocean.com": 84,
    "www.digitalocean.com": 84,
    "tutorialspoint.com": 80,
    "www.tutorialspoint.com": 80,
    "hackernoon.com": 80,
    "dev.to": 80,
    "medium.com": 78,
}

# Domains to exclude (already covered by other curators)
EXCLUDED_DOMAINS = {
    "youtube.com", "www.youtube.com", "youtu.be",
    "reddit.com", "www.reddit.com", "old.reddit.com",
}

SERPER_SEARCH_URL = "https://google.serper.dev/search"


class ArticleSearchService:
    """Finds real article URLs via the Serper.dev Google Search API."""

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if self.api_key:
            logger.info("Serper.dev search service initialized")
        else:
            logger.warning("SERPER_API_KEY not set — article search disabled")

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def search_articles(self, topic: str, count: int = 5) -> List[Dict]:
        """
        Search Google via Serper for real article URLs about a topic.

        Returns list of dicts with: title, url, description, quality_score, source
        """
        if not self.is_available:
            return []

        try:
            query = f"{topic} tutorial guide"
            payload = {
                "q": query,
                "num": min(count * 2, 20),
            }
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            }

            resp = requests.post(SERPER_SEARCH_URL, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for idx, item in enumerate(data.get("organic", [])):
                url = item.get("link", "")
                domain = self._extract_domain(url)

                # Skip excluded domains
                if domain in EXCLUDED_DOMAINS:
                    continue

                quality = self._score_result(item, idx, domain)

                results.append({
                    "type": "article",
                    "title": item.get("title", f"{topic} article"),
                    "url": url,
                    "description": item.get("snippet", ""),
                    "quality_score": quality,
                    "source": domain,
                })

                if len(results) >= count:
                    break

            results.sort(key=lambda r: r["quality_score"], reverse=True)
            logger.info(f"Serper found {len(results)} articles for '{topic}'")
            return results

        except requests.RequestException as e:
            logger.error(f"Serper API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Serper unexpected error: {e}")
            return []

    def validate_url(self, url: str, timeout: int = 5) -> bool:
        """Quick HEAD check that the URL is reachable."""
        try:
            resp = requests.head(url, timeout=timeout, allow_redirects=True)
            return resp.status_code < 400
        except Exception:
            return False

    def search_and_validate(self, topic: str, count: int = 5) -> List[Dict]:
        """Search for articles, then validate top results."""
        articles = self.search_articles(topic, count=count + 2)

        validated = []
        for article in articles:
            if self.validate_url(article["url"]):
                validated.append(article)
                if len(validated) >= count:
                    break
            else:
                logger.debug(f"URL validation failed: {article['url']}")

        # If validation filtered too many, return unvalidated as fallback
        if len(validated) < count and len(articles) > len(validated):
            for article in articles:
                if article not in validated:
                    validated.append(article)
                    if len(validated) >= count:
                        break

        return validated[:count]

    def _score_result(self, item: Dict, position: int, domain: str) -> float:
        """
        Score a search result for quality.

        Factors:
        - Domain whitelist boost
        - Position bonus (top result +10, decaying)
        """
        # Base score
        score = HIGH_QUALITY_DOMAINS.get(domain, 70.0)

        # Position bonus: top result +10, second +7, third +5, etc.
        position_bonus = max(0, 10 - position * 3)
        score += position_bonus

        return min(100.0, max(0.0, score))

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except Exception:
            return ""


# Cache for article results keyed by topic
_article_cache: Dict[str, Dict] = {}
_CACHE_TTL = timedelta(days=7)


def get_cached_articles(topic: str, db=None) -> Optional[List[Dict]]:
    """Check in-memory cache and optionally CuratedResource table."""
    cache_key = hashlib.md5(topic.lower().encode()).hexdigest()

    # In-memory cache
    if cache_key in _article_cache:
        entry = _article_cache[cache_key]
        if datetime.utcnow() < entry["expires_at"]:
            logger.debug(f"Article cache hit for '{topic}'")
            return entry["articles"]
        else:
            del _article_cache[cache_key]

    # DB cache via CuratedResource
    if db:
        try:
            from app.models.content_curation import CuratedResource
            cached = db.query(CuratedResource).filter(
                CuratedResource.topic == topic.lower(),
                CuratedResource.resource_type == "article",
                CuratedResource.cache_expires_at > datetime.utcnow(),
            ).order_by(CuratedResource.quality_score.desc()).limit(5).all()

            if cached:
                articles = [{
                    "type": "article",
                    "title": r.title,
                    "url": r.url,
                    "description": r.description or "",
                    "quality_score": float(r.quality_score),
                    "source": r.author or "",
                } for r in cached]
                # Also populate in-memory cache
                _article_cache[cache_key] = {
                    "articles": articles,
                    "expires_at": datetime.utcnow() + _CACHE_TTL,
                }
                logger.debug(f"Article DB cache hit for '{topic}': {len(articles)} results")
                return articles
        except Exception as e:
            logger.warning(f"DB cache lookup failed: {e}")

    return None


def cache_articles(topic: str, articles: List[Dict], db=None):
    """Store articles in both in-memory and DB cache."""
    cache_key = hashlib.md5(topic.lower().encode()).hexdigest()
    expires_at = datetime.utcnow() + _CACHE_TTL

    # In-memory
    _article_cache[cache_key] = {
        "articles": articles,
        "expires_at": expires_at,
    }

    # DB cache
    if db:
        try:
            from app.models.content_curation import CuratedResource
            for article in articles:
                # Check if already cached
                existing = db.query(CuratedResource).filter(
                    CuratedResource.url == article["url"],
                    CuratedResource.resource_type == "article",
                ).first()

                if existing:
                    existing.quality_score = article["quality_score"]
                    existing.cache_expires_at = expires_at
                    existing.updated_at = datetime.utcnow()
                else:
                    resource = CuratedResource(
                        topic=topic.lower(),
                        learning_style="balanced",
                        resource_type="article",
                        resource_id=hashlib.md5(article["url"].encode()).hexdigest(),
                        url=article["url"],
                        title=article["title"],
                        description=article.get("description", ""),
                        author=article.get("source", ""),
                        quality_score=article["quality_score"],
                        cache_expires_at=expires_at,
                    )
                    db.add(resource)

            db.commit()
            logger.debug(f"Cached {len(articles)} articles for '{topic}' in DB")
        except Exception as e:
            logger.warning(f"DB cache write failed: {e}")
            try:
                db.rollback()
            except Exception:
                pass


def invalidate_article_cache(url: str, db=None):
    """Invalidate cache for a specific URL (e.g., when reported as broken)."""
    if db:
        try:
            from app.models.content_curation import CuratedResource
            db.query(CuratedResource).filter(
                CuratedResource.url == url,
                CuratedResource.resource_type == "article",
            ).delete()
            db.commit()
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
            try:
                db.rollback()
            except Exception:
                pass


# Singleton
_article_search_service = None


def get_article_search_service() -> ArticleSearchService:
    """Get or create ArticleSearchService singleton."""
    global _article_search_service
    if _article_search_service is None:
        _article_search_service = ArticleSearchService()
    return _article_search_service
