"""Data-collection clients mirroring the toolkit's Colab notebooks."""

from .openalex import search_openalex
from .pubmed import search_pubmed

__all__ = ["search_openalex", "search_pubmed"]
