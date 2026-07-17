"""PubMed search via NCBI E-utilities (mirrors the PubMed Literature Harvester notebook)."""

import requests

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def search_pubmed(query: str, limit: int = 10, api_key: str | None = None,
                  year_from: int | None = None, year_to: int | None = None,
                  journal: str | None = None) -> list[dict]:
    """Search PubMed and return record summaries.

    Works without an API key (NCBI allows small keyless request volumes);
    pass api_key for higher rate limits. Supports full PubMed query syntax
    in `query`, plus convenience filters: year_from/year_to (publication
    date) and journal (title abbreviation or full name). Returns records
    with: pmid, title, authors, journal, pubdate, doi.
    """
    limit = max(1, min(int(limit), 100))
    base = {"api_key": api_key} if api_key else {}
    term = query
    if journal:
        term += f' AND "{journal}"[ta]'
    date_params = {}
    if year_from or year_to:
        date_params = {"datetype": "pdat",
                       "mindate": f"{int(year_from or 1800)}/01/01",
                       "maxdate": f"{int(year_to or 2100)}/12/31"}
    r = requests.get(ESEARCH, params={**base, **date_params, "db": "pubmed",
                                      "term": term,
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
