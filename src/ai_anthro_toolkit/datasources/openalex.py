"""OpenAlex scholarly-works search (mirrors the Academic Literature Explorer notebook)."""

import requests

API = "https://api.openalex.org/works"


def search_openalex(query: str, limit: int = 10, mailto: str | None = None) -> list[dict]:
    """Search OpenAlex works.

    Returns a list of records with: title, authors, year, venue, doi,
    cited_by_count, is_open_access, openalex_id, abstract_available.
    """
    limit = max(1, min(int(limit), 100))
    params = {
        "search": query,
        "per-page": limit,
        "select": "id,display_name,publication_year,doi,cited_by_count,"
                  "open_access,authorships,primary_location,abstract_inverted_index",
    }
    if mailto:
        params["mailto"] = mailto
    r = requests.get(API, params=params, timeout=30)
    r.raise_for_status()
    results = []
    for w in r.json().get("results", []):
        venue = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        results.append({
            "title": w.get("display_name"),
            "authors": [a["author"]["display_name"]
                        for a in w.get("authorships", []) if a.get("author")],
            "year": w.get("publication_year"),
            "venue": venue,
            "doi": w.get("doi"),
            "cited_by_count": w.get("cited_by_count", 0),
            "is_open_access": (w.get("open_access") or {}).get("is_oa", False),
            "openalex_id": w.get("id"),
            "abstract_available": bool(w.get("abstract_inverted_index")),
        })
    return results
