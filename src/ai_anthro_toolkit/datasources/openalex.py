"""OpenAlex scholarly-works search (mirrors the Academic Literature Explorer notebook)."""

import requests

API = "https://api.openalex.org/works"
SOURCES_API = "https://api.openalex.org/sources"

_SORTS = {
    "relevance": None,  # OpenAlex default when `search` is used
    "recent": "publication_date:desc",
    "cited": "cited_by_count:desc",
}


def _resolve_source_ids(venue: str, mailto: str | None = None) -> str:
    """Resolve a journal/venue name to OpenAlex source IDs (pipe-joined)."""
    params = {"search": venue, "per-page": 3, "select": "id,display_name"}
    if mailto:
        params["mailto"] = mailto
    r = requests.get(SOURCES_API, params=params, timeout=30)
    r.raise_for_status()
    ids = [s["id"].rsplit("/", 1)[-1] for s in r.json().get("results", [])]
    return "|".join(ids)


def search_openalex(query: str, limit: int = 10, mailto: str | None = None,
                    year_from: int | None = None, year_to: int | None = None,
                    venue: str | None = None,
                    sort: str = "relevance",
                    open_access_only: bool = False) -> list[dict]:
    """Search OpenAlex works with optional year, venue, and sort controls.

    Args:
        query: Full-text search terms.
        limit: Maximum records (1-100).
        mailto: Optional contact email for OpenAlex's polite pool.
        year_from / year_to: Restrict by publication year (inclusive).
        venue: Journal or source name (e.g. "Anthropological Forum");
            resolved to OpenAlex source IDs and applied as a filter.
        sort: "relevance" (default), "recent", or "cited".
        open_access_only: Restrict to open-access works.

    Returns records with: title, authors, year, venue, doi, cited_by_count,
    is_open_access, openalex_id, abstract_available.
    """
    limit = max(1, min(int(limit), 100))
    filters = []
    if year_from:
        filters.append(f"from_publication_date:{int(year_from)}-01-01")
    if year_to:
        filters.append(f"to_publication_date:{int(year_to)}-12-31")
    if open_access_only:
        filters.append("open_access.is_oa:true")
    if venue:
        source_ids = _resolve_source_ids(venue, mailto)
        if not source_ids:
            return []
        filters.append(f"primary_location.source.id:{source_ids}")

    params = {
        "search": query,
        "per-page": limit,
        "select": "id,display_name,publication_year,doi,cited_by_count,"
                  "open_access,authorships,primary_location,abstract_inverted_index",
    }
    if filters:
        params["filter"] = ",".join(filters)
    sort_value = _SORTS.get(sort, None)
    if sort_value:
        params["sort"] = sort_value
    if mailto:
        params["mailto"] = mailto

    r = requests.get(API, params=params, timeout=30)
    r.raise_for_status()
    results = []
    for w in r.json().get("results", []):
        source = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        results.append({
            "title": w.get("display_name"),
            "authors": [a["author"]["display_name"]
                        for a in w.get("authorships", []) if a.get("author")],
            "year": w.get("publication_year"),
            "venue": source,
            "doi": w.get("doi"),
            "cited_by_count": w.get("cited_by_count", 0),
            "is_open_access": (w.get("open_access") or {}).get("is_oa", False),
            "openalex_id": w.get("id"),
            "abstract_available": bool(w.get("abstract_inverted_index")),
        })
    return results
