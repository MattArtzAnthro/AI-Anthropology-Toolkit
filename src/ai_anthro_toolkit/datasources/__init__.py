"""Data-collection clients mirroring the toolkit's Colab notebooks."""

from .crossref import search_crossref
from .googlenews import search_google_news
from .ngram import get_ngram_frequencies
from .openalex import search_openalex
from .patents import search_google_patents
from .podcast import get_podcast_episodes
from .pubmed import search_pubmed
from .scholar import search_google_scholar
from .trends import get_google_trends
from .youtube import get_youtube_transcript, search_youtube

__all__ = [
    "get_google_trends",
    "get_ngram_frequencies",
    "get_podcast_episodes",
    "get_youtube_transcript",
    "search_crossref",
    "search_google_news",
    "search_google_patents",
    "search_google_scholar",
    "search_openalex",
    "search_pubmed",
    "search_youtube",
]
