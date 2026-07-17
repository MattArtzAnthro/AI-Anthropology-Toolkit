"""CrossRef works search — canonical DOI metadata, no API key required."""

import requests

API = "https://api.crossref.org/works"


def search_crossref(query: str, limit: int = 10,
                    year_from: int | None = None, year_to: int | None = None,
                    journal: str | None = None,
                    journal_articles_only: bool = True,
                    mailto: str | None = None) -> list[dict]:
    """Search CrossRef for published works.

    Args:
        query: Search terms (matched against titles, authors, and metadata).
        limit: Maximum records (1-100).
        year_from / year_to: Restrict by publication year (inclusive).
        journal: Container title to search within (e.g. "American Ethnologist").
        journal_articles_only: Restrict to type journal-article (default True).
        mailto: Optional contact email for CrossRef's polite pool.

    Returns records with: title, authors, journal, year, doi, type,
    cited_by_count, publisher.
    """
    limit = max(1, min(int(limit), 100))
    filters = []
    if year_from:
        filters.append(f"from-pub-date:{int(year_from)}-01-01")
    if year_to:
        filters.append(f"until-pub-date:{int(year_to)}-12-31")
    if journal_articles_only:
        filters.append("type:journal-article")

    params = {
        "query": query,
        "rows": limit,
        "select": "title,author,container-title,published,DOI,type,"
                  "is-referenced-by-count,publisher",
    }
    if filters:
        params["filter"] = ",".join(filters)
    if journal:
        params["query.container-title"] = journal
    if mailto:
        params["mailto"] = mailto

    r = requests.get(API, params=params, timeout=30)
    r.raise_for_status()
    results = []
    for item in r.json().get("message", {}).get("items", []):
        date_parts = (item.get("published", {}) or {}).get("date-parts") or [[None]]
        authors = []
        for a in item.get("author", []) or []:
            name = " ".join(x for x in (a.get("given"), a.get("family")) if x)
            if name:
                authors.append(name)
        results.append({
            "title": (item.get("title") or [None])[0],
            "authors": authors,
            "journal": (item.get("container-title") or [None])[0],
            "year": date_parts[0][0],
            "doi": item.get("DOI"),
            "type": item.get("type"),
            "cited_by_count": item.get("is-referenced-by-count", 0),
            "publisher": item.get("publisher"),
        })
    return results
