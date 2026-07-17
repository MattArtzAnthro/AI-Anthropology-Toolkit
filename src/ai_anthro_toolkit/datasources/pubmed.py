"""PubMed search via NCBI E-utilities (mirrors the PubMed Literature Harvester notebook)."""

import requests

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def search_pubmed(query: str, limit: int = 10, api_key: str | None = None) -> list[dict]:
    """Search PubMed and return record summaries.

    Works without an API key (NCBI allows small keyless request volumes);
    pass api_key for higher rate limits. Returns records with: pmid, title,
    authors, journal, pubdate, doi.
    """
    limit = max(1, min(int(limit), 100))
    base = {"api_key": api_key} if api_key else {}
    r = requests.get(ESEARCH, params={**base, "db": "pubmed", "term": query,
                                      "retmax": limit, "retmode": "json"}, timeout=30)
    r.raise_for_status()
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    r = requests.get(ESUMMARY, params={**base, "db": "pubmed", "id": ",".join(ids),
                                       "retmode": "json"}, timeout=30)
    r.raise_for_status()
    summary = r.json().get("result", {})
    results = []
    for pmid in ids:
        rec = summary.get(pmid)
        if not rec:
            continue
        doi = next((aid["value"] for aid in rec.get("articleids", [])
                    if aid.get("idtype") == "doi"), None)
        results.append({
            "pmid": pmid,
            "title": rec.get("title"),
            "authors": [a.get("name") for a in rec.get("authors", [])],
            "journal": rec.get("fulljournalname"),
            "pubdate": rec.get("pubdate"),
            "doi": doi,
        })
    return results
