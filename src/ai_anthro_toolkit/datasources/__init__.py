"""Data-collection clients mirroring the toolkit's Colab notebooks."""

from .crossref import search_crossref
from .openalex import search_openalex
from .pubmed import search_pubmed

__all__ = ["search_crossref", "search_openalex", "search_pubmed"]
