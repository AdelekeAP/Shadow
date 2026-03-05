"""
Resource Finder Service
Finds documentation, articles, practice exercises, and learning resources for study plans
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ResourceFinder:
    """
    Service for finding various learning resources:
    - Documentation (official docs, MDN, etc.)
    - Articles (via Serper search API)
    - Practice platforms (LeetCode, HackerRank, etc. — matched by topic category)
    - Interactive tutorials (Codecademy, freeCodeCamp)
    - GitHub repositories
    """

    def __init__(self):
        # Curated documentation sources by technology
        self.documentation_sources = {
            # JavaScript/Web
            'javascript': {
                'official': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
                'tutorial': 'https://javascript.info/',
                'reference': 'https://devdocs.io/javascript/'
            },
            'react': {
                'official': 'https://react.dev/',
                'tutorial': 'https://react.dev/learn',
                'hooks': 'https://react.dev/reference/react/hooks',
                'reference': 'https://devdocs.io/react/'
            },
            'react hooks': {
                'official': 'https://react.dev/reference/react/hooks',
                'usestate': 'https://react.dev/reference/react/useState',
                'useeffect': 'https://react.dev/reference/react/useEffect',
                'tutorial': 'https://react.dev/learn/state-a-components-memory'
            },
            'typescript': {
                'official': 'https://www.typescriptlang.org/docs/',
                'handbook': 'https://www.typescriptlang.org/docs/handbook/intro.html',
                'reference': 'https://devdocs.io/typescript/'
            },
            'nodejs': {
                'official': 'https://nodejs.org/docs/latest/api/',
                'tutorial': 'https://nodejs.dev/learn',
                'reference': 'https://devdocs.io/node/'
            },
            'html': {
                'official': 'https://developer.mozilla.org/en-US/docs/Web/HTML',
                'tutorial': 'https://developer.mozilla.org/en-US/docs/Learn/HTML',
                'reference': 'https://devdocs.io/html/'
            },
            'css': {
                'official': 'https://developer.mozilla.org/en-US/docs/Web/CSS',
                'tutorial': 'https://developer.mozilla.org/en-US/docs/Learn/CSS',
                'reference': 'https://devdocs.io/css/'
            },
            # Python
            'python': {
                'official': 'https://docs.python.org/3/',
                'tutorial': 'https://docs.python.org/3/tutorial/',
                'reference': 'https://devdocs.io/python/'
            },
            'django': {
                'official': 'https://docs.djangoproject.com/',
                'tutorial': 'https://docs.djangoproject.com/en/stable/intro/tutorial01/',
                'reference': 'https://devdocs.io/django/'
            },
            'flask': {
                'official': 'https://flask.palletsprojects.com/',
                'tutorial': 'https://flask.palletsprojects.com/tutorial/',
                'reference': 'https://devdocs.io/flask/'
            },
            'fastapi': {
                'official': 'https://fastapi.tiangolo.com/',
                'tutorial': 'https://fastapi.tiangolo.com/tutorial/',
                'reference': 'https://fastapi.tiangolo.com/reference/'
            },
            # Data Science
            'pandas': {
                'official': 'https://pandas.pydata.org/docs/',
                'tutorial': 'https://pandas.pydata.org/docs/getting_started/intro_tutorials/',
                'reference': 'https://devdocs.io/pandas/'
            },
            'numpy': {
                'official': 'https://numpy.org/doc/stable/',
                'tutorial': 'https://numpy.org/doc/stable/user/quickstart.html',
                'reference': 'https://devdocs.io/numpy/'
            },
            'machine learning': {
                'sklearn': 'https://scikit-learn.org/stable/user_guide.html',
                'tensorflow': 'https://www.tensorflow.org/tutorials',
                'pytorch': 'https://pytorch.org/tutorials/'
            },
            # Databases
            'sql': {
                'tutorial': 'https://www.w3schools.com/sql/',
                'postgres': 'https://www.postgresql.org/docs/current/tutorial.html',
                'reference': 'https://devdocs.io/postgresql/'
            },
            'mongodb': {
                'official': 'https://www.mongodb.com/docs/',
                'tutorial': 'https://www.mongodb.com/docs/manual/tutorial/',
                'university': 'https://university.mongodb.com/'
            },
            # DevOps
            'docker': {
                'official': 'https://docs.docker.com/',
                'tutorial': 'https://docs.docker.com/get-started/',
                'reference': 'https://devdocs.io/docker/'
            },
            'git': {
                'official': 'https://git-scm.com/doc',
                'tutorial': 'https://git-scm.com/book/en/v2',
                'reference': 'https://devdocs.io/git/'
            },
            # General CS
            'data structures': {
                'visualgo': 'https://visualgo.net/',
                'geeksforgeeks': 'https://www.geeksforgeeks.org/data-structures/',
                'tutorial': 'https://www.programiz.com/dsa'
            },
            'algorithms': {
                'visualgo': 'https://visualgo.net/',
                'geeksforgeeks': 'https://www.geeksforgeeks.org/fundamentals-of-algorithms/',
                'tutorial': 'https://www.programiz.com/dsa'
            }
        }

        # Practice platforms by category
        self.practice_platforms = {
            'coding': [
                {
                    'name': 'LeetCode',
                    'url': 'https://leetcode.com/problemset/',
                    'search_url': 'https://leetcode.com/problemset/all/?search=',
                    'description': 'Practice coding problems and prepare for interviews',
                    'type': 'practice'
                },
                {
                    'name': 'HackerRank',
                    'url': 'https://www.hackerrank.com/domains',
                    'description': 'Coding challenges and skill certification',
                    'type': 'practice'
                },
                {
                    'name': 'Codewars',
                    'url': 'https://www.codewars.com/',
                    'description': 'Code challenges (kata) to improve skills',
                    'type': 'practice'
                },
                {
                    'name': 'Exercism',
                    'url': 'https://exercism.org/',
                    'description': 'Free coding practice with mentorship',
                    'type': 'practice'
                }
            ],
            'web': [
                {
                    'name': 'CodePen',
                    'url': 'https://codepen.io/',
                    'search_url': 'https://codepen.io/search/pens?q=',
                    'description': 'Online code editor for HTML/CSS/JS',
                    'type': 'sandbox'
                },
                {
                    'name': 'CodeSandbox',
                    'url': 'https://codesandbox.io/',
                    'search_url': 'https://codesandbox.io/search?query=',
                    'description': 'Online IDE for web development',
                    'type': 'sandbox'
                },
                {
                    'name': 'StackBlitz',
                    'url': 'https://stackblitz.com/',
                    'description': 'Online VS Code for web projects',
                    'type': 'sandbox'
                },
                {
                    'name': 'JSFiddle',
                    'url': 'https://jsfiddle.net/',
                    'description': 'Test HTML/CSS/JS code snippets',
                    'type': 'sandbox'
                }
            ],
            'algorithms': [
                {
                    'name': 'VisuAlgo',
                    'url': 'https://visualgo.net/',
                    'description': 'Visualize algorithms and data structures',
                    'type': 'interactive'
                },
                {
                    'name': 'Algorithm Visualizer',
                    'url': 'https://algorithm-visualizer.org/',
                    'description': 'Interactive algorithm visualization',
                    'type': 'interactive'
                }
            ],
            'database': [
                {
                    'name': 'SQLZoo',
                    'url': 'https://sqlzoo.net/',
                    'description': 'Interactive SQL tutorial and exercises',
                    'type': 'interactive'
                },
                {
                    'name': 'SQL Fiddle',
                    'url': 'http://sqlfiddle.com/',
                    'description': 'Online SQL testing environment',
                    'type': 'sandbox'
                }
            ],
            'math': [
                {
                    'name': 'Khan Academy - Math',
                    'url': 'https://www.khanacademy.org/math',
                    'description': 'Free math courses from arithmetic to calculus',
                    'type': 'interactive'
                },
                {
                    'name': 'Wolfram Alpha',
                    'url': 'https://www.wolframalpha.com/',
                    'search_url': 'https://www.wolframalpha.com/input?i=',
                    'description': 'Computational knowledge engine for math problems',
                    'type': 'sandbox'
                },
                {
                    'name': 'Symbolab',
                    'url': 'https://www.symbolab.com/',
                    'description': 'Step-by-step math solver and practice',
                    'type': 'practice'
                }
            ],
            'science': [
                {
                    'name': 'Khan Academy - Science',
                    'url': 'https://www.khanacademy.org/science',
                    'description': 'Free science courses covering physics, chemistry, biology',
                    'type': 'interactive'
                },
                {
                    'name': 'PhET Simulations',
                    'url': 'https://phet.colorado.edu/',
                    'description': 'Interactive science and math simulations',
                    'type': 'interactive'
                }
            ],
            'business': [
                {
                    'name': 'Investopedia',
                    'url': 'https://www.investopedia.com/',
                    'search_url': 'https://www.investopedia.com/search?q=',
                    'description': 'Financial education and business concepts',
                    'type': 'interactive'
                },
                {
                    'name': 'Khan Academy - Economics',
                    'url': 'https://www.khanacademy.org/economics-finance-domain',
                    'description': 'Free economics and finance courses',
                    'type': 'interactive'
                }
            ],
            'humanities': [
                {
                    'name': 'Stanford Encyclopedia of Philosophy',
                    'url': 'https://plato.stanford.edu/',
                    'search_url': 'https://plato.stanford.edu/search/searcher.py?query=',
                    'description': 'Authoritative philosophy reference',
                    'type': 'interactive'
                },
                {
                    'name': 'JSTOR',
                    'url': 'https://www.jstor.org/',
                    'search_url': 'https://www.jstor.org/action/doBasicSearch?Query=',
                    'description': 'Digital library for academic journals and books',
                    'type': 'practice'
                }
            ]
        }

        # Interactive learning platforms
        self.learning_platforms = [
            {
                'name': 'freeCodeCamp',
                'url': 'https://www.freecodecamp.org/learn',
                'description': 'Free coding bootcamp with certifications',
                'topics': ['web', 'javascript', 'python', 'data science']
            },
            {
                'name': 'Codecademy',
                'url': 'https://www.codecademy.com/catalog',
                'description': 'Interactive coding courses',
                'topics': ['web', 'python', 'javascript', 'sql', 'data science']
            },
            {
                'name': 'Khan Academy',
                'url': 'https://www.khanacademy.org/computing',
                'description': 'Free courses on computing and programming',
                'topics': ['algorithms', 'computer science', 'web']
            },
            {
                'name': 'The Odin Project',
                'url': 'https://www.theodinproject.com/',
                'description': 'Full stack web development curriculum',
                'topics': ['web', 'javascript', 'nodejs', 'react']
            },
            {
                'name': 'Scrimba',
                'url': 'https://scrimba.com/',
                'description': 'Interactive video courses for coding',
                'topics': ['web', 'react', 'javascript', 'css']
            }
        ]

    def find_documentation(self, topic: str) -> List[Dict]:
        """
        Find official documentation and reference materials for a topic

        Args:
            topic: Learning topic (e.g., "React Hooks", "Python")

        Returns:
            List of documentation resources with URLs
        """
        resources = []
        topic_lower = topic.lower()

        # Check for exact or partial matches in documentation sources
        for key, docs in self.documentation_sources.items():
            if key in topic_lower or topic_lower in key:
                for doc_type, url in docs.items():
                    resources.append({
                        'type': 'documentation',
                        'title': f'{key.title()} - {doc_type.replace("_", " ").title()}',
                        'url': url,
                        'description': f'Official {doc_type} for {key.title()}',
                        'quality_score': 90 if doc_type == 'official' else 85,
                        'source': 'documentation'
                    })

        # No fallback — return empty rather than a useless search-page URL

        logger.info(f"Found {len(resources)} documentation resources for '{topic}'")
        return resources[:5]  # Limit to top 5

    def find_articles(self, topic: str, db=None) -> List[Dict]:
        """
        Find articles and tutorials via Serper Google Search.
        Returns empty list if Serper is unavailable or returns no results.

        Args:
            topic: Learning topic
            db: Optional database session for caching search results

        Returns:
            List of article resources with URLs (empty if no real results)
        """
        # 1. Try cache first
        from app.services.article_search_service import (
            get_article_search_service, get_cached_articles, cache_articles,
        )

        cached = get_cached_articles(topic, db=db)
        if cached:
            logger.info(f"Using {len(cached)} cached articles for '{topic}'")
            return cached[:5]

        # 2. Try Serper search for real URLs
        search_service = get_article_search_service()
        if search_service.is_available:
            articles = search_service.search_and_validate(topic, count=5)
            if articles:
                if db:
                    cache_articles(topic, articles, db=db)
                logger.info(f"Serper found {len(articles)} real articles for '{topic}'")
                return articles[:5]

        # 3. No Serper results — return empty rather than template search-page URLs
        logger.info(f"No real articles found for '{topic}' (Serper unavailable or returned nothing)")
        return []

    def find_practice_resources(self, topic: str, category: str = 'coding') -> List[Dict]:
        """
        Find practice platforms and coding exercises.
        Only returns resources for categories that genuinely match the topic.

        Args:
            topic: Learning topic
            category: Type of practice (coding, web, algorithms, database)

        Returns:
            List of practice resources (empty for unmatched categories)
        """
        resources = []
        topic_lower = topic.lower()
        encoded_topic = topic.replace(' ', '+')

        # Determine category based on topic keywords
        detected_category = None
        if any(word in topic_lower for word in ['html', 'css', 'web', 'react', 'frontend', 'ui']):
            detected_category = 'web'
        elif any(word in topic_lower for word in ['algorithm', 'data structure', 'sorting', 'search']):
            detected_category = 'algorithms'
        elif any(word in topic_lower for word in ['sql', 'database', 'query', 'postgres', 'mysql']):
            detected_category = 'database'
        elif any(word in topic_lower for word in ['python', 'java', 'javascript', 'coding', 'programming', 'code']):
            detected_category = 'coding'
        elif any(word in topic_lower for word in ['math', 'calculus', 'algebra', 'statistics', 'probability', 'linear algebra', 'differential']):
            detected_category = 'math'
        elif any(word in topic_lower for word in ['physics', 'chemistry', 'biology', 'science', 'engineering', 'circuit']):
            detected_category = 'science'
        elif any(word in topic_lower for word in ['business', 'management', 'economics', 'finance', 'accounting', 'marketing']):
            detected_category = 'business'
        elif any(word in topic_lower for word in ['history', 'philosophy', 'literature', 'sociology', 'psychology', 'political', 'law']):
            detected_category = 'humanities'

        # If no category matched, return empty — don't send students to CodePen for "NLP"
        if detected_category is None:
            logger.info(f"No matching practice category for '{topic}', returning empty")
            return []

        category = detected_category

        # Get platforms for the matched category
        platforms = self.practice_platforms.get(category, [])

        for platform in platforms:
            resource = {
                'type': 'practice',
                'title': f'Practice {topic} on {platform["name"]}',
                'url': platform.get('search_url', platform['url']),
                'description': platform['description'],
                'quality_score': 80,
                'source': platform['name'].lower(),
                'platform_type': platform.get('type', 'practice')
            }

            # Add topic to search URL if available
            if 'search_url' in platform:
                resource['url'] = f'{platform["search_url"]}{encoded_topic}'

            resources.append(resource)

        # Add LeetCode for specific algorithm topics
        if category == 'algorithms' or any(word in topic_lower for word in ['array', 'string', 'tree', 'graph', 'dynamic']):
            resources.insert(0, {
                'type': 'practice',
                'title': f'LeetCode - {topic} Problems',
                'url': f'https://leetcode.com/problemset/all/?search={encoded_topic}',
                'description': 'Practice coding problems on LeetCode',
                'quality_score': 88,
                'source': 'leetcode',
                'platform_type': 'practice'
            })

        logger.info(f"Found {len(resources)} practice resources for '{topic}'")
        return resources[:5]

    def find_interactive_tutorials(self, topic: str) -> List[Dict]:
        """
        Find interactive learning platforms and courses

        Args:
            topic: Learning topic

        Returns:
            List of interactive learning resources
        """
        resources = []
        topic_lower = topic.lower()

        for platform in self.learning_platforms:
            # Check if platform covers the topic
            topic_match = any(t in topic_lower for t in platform['topics']) or \
                         any(topic_lower in t for t in platform['topics'])

            if topic_match:
                resources.append({
                    'type': 'interactive',
                    'title': f'Learn {topic} on {platform["name"]}',
                    'url': platform['url'],
                    'description': platform['description'],
                    'quality_score': 82,
                    'source': platform['name'].lower(),
                    'platform_type': 'course'
                })

        # Add topic-specific interactive resources
        if 'react' in topic_lower:
            resources.insert(0, {
                'type': 'interactive',
                'title': 'React Tutorial - Tic-Tac-Toe',
                'url': 'https://react.dev/learn/tutorial-tic-tac-toe',
                'description': 'Official React interactive tutorial',
                'quality_score': 95,
                'source': 'official'
            })

        if any(word in topic_lower for word in ['algorithm', 'data structure']):
            resources.insert(0, {
                'type': 'interactive',
                'title': 'VisuAlgo - Algorithm Visualizations',
                'url': 'https://visualgo.net/',
                'description': 'Visualize data structures and algorithms',
                'quality_score': 90,
                'source': 'visualgo'
            })

        logger.info(f"Found {len(resources)} interactive resources for '{topic}'")
        return resources[:5]

    def find_github_resources(self, topic: str) -> List[Dict]:
        """
        Find GitHub repositories with tutorials and examples

        Args:
            topic: Learning topic

        Returns:
            List of GitHub resources
        """
        resources = []
        encoded_topic = topic.replace(' ', '+')

        # GitHub search for learning resources
        resources.append({
            'type': 'github',
            'title': f'GitHub - {topic} tutorials and examples',
            'url': f'https://github.com/search?q={encoded_topic}+tutorial&type=repositories&s=stars',
            'description': f'Find open-source {topic} tutorials and example code',
            'quality_score': 75,
            'source': 'github'
        })

        # Awesome lists
        resources.append({
            'type': 'github',
            'title': f'Awesome {topic} - Curated Resources',
            'url': f'https://github.com/search?q=awesome+{encoded_topic}&type=repositories&s=stars',
            'description': f'Curated list of {topic} resources',
            'quality_score': 80,
            'source': 'github-awesome'
        })

        # Topic-specific popular repos
        popular_repos = {
            'react': {
                'title': 'React - Official Repository',
                'url': 'https://github.com/facebook/react',
                'description': 'Official React source code and examples'
            },
            'javascript': {
                'title': 'JavaScript Algorithms & Data Structures',
                'url': 'https://github.com/trekhleb/javascript-algorithms',
                'description': 'Algorithms and data structures in JavaScript'
            },
            'python': {
                'title': 'The Algorithms - Python',
                'url': 'https://github.com/TheAlgorithms/Python',
                'description': 'All algorithms implemented in Python'
            },
            'machine learning': {
                'title': 'Machine Learning for Beginners',
                'url': 'https://github.com/microsoft/ML-For-Beginners',
                'description': 'Microsoft ML curriculum'
            }
        }

        for key, repo in popular_repos.items():
            if key in topic.lower():
                resources.insert(0, {
                    'type': 'github',
                    'title': repo['title'],
                    'url': repo['url'],
                    'description': repo['description'],
                    'quality_score': 88,
                    'source': 'github-popular'
                })

        logger.info(f"Found {len(resources)} GitHub resources for '{topic}'")
        return resources[:5]

    def find_all_resources(
        self,
        topic: str,
        resource_types: List[str] = None,
        max_per_type: int = 3,
        db=None
    ) -> Dict[str, List[Dict]]:
        """
        Find all types of resources for a topic

        Args:
            topic: Learning topic
            resource_types: List of types to include (documentation, articles, practice, interactive, github)
            max_per_type: Maximum resources per type
            db: Optional database session for article caching

        Returns:
            Dictionary with resources organized by type
        """
        if resource_types is None:
            resource_types = ['documentation', 'articles', 'practice', 'interactive', 'github']

        results = {
            'topic': topic,
            'found_at': datetime.now(timezone.utc).isoformat(),
            'resources': {}
        }

        if 'documentation' in resource_types:
            results['resources']['documentation'] = self.find_documentation(topic)[:max_per_type]

        if 'articles' in resource_types:
            results['resources']['articles'] = self.find_articles(topic, db=db)[:max_per_type]

        if 'practice' in resource_types:
            results['resources']['practice'] = self.find_practice_resources(topic)[:max_per_type]

        if 'interactive' in resource_types:
            results['resources']['interactive'] = self.find_interactive_tutorials(topic)[:max_per_type]

        if 'github' in resource_types:
            results['resources']['github'] = self.find_github_resources(topic)[:max_per_type]

        # Flatten all resources for easy access
        all_resources = []
        for resource_list in results['resources'].values():
            all_resources.extend(resource_list)

        results['all_resources'] = sorted(all_resources, key=lambda x: x.get('quality_score', 0), reverse=True)
        results['total_count'] = len(all_resources)

        logger.info(f"Found {results['total_count']} total resources for '{topic}'")
        return results


# Singleton instance
_resource_finder = None


def get_resource_finder() -> ResourceFinder:
    """Get or create ResourceFinder singleton"""
    global _resource_finder
    if _resource_finder is None:
        _resource_finder = ResourceFinder()
    return _resource_finder
