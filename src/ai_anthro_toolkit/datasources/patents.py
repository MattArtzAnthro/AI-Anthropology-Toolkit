"""Google Patents search via the site's internal query endpoint (mirrors the Google Patents Explorer notebook)."""

import re
import unicodedata

import requests

API = "https://patents.google.com/xhr/query"

# Full browser headers — the endpoint rejects requests without them.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://patents.google.com/",
    "X-Requested-With": "XMLHttpRequest",
}

_BLOCK_MESSAGE = (
    "Google Patents is rate limiting / bot blocking automated queries from "
    "this IP address. Even a few rapid searches can trigger a temporary "
    "block, and blocks are more common on cloud IPs. Wait 10-15 minutes "
    "before retrying, or request fewer results."
)


def _clean(text) -> str:
    """Strip HTML tags and normalize unicode."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", str(text))
    return unicodedata.normalize("NFKC", text).strip()


def search_google_patents(query: str, limit: int = 10) -> list[dict]:
    """Search Google Patents by keyword.

    Queries the endpoint behind the Google Patents search page (no API key;
    results are fetched in pages of 10). Raises RuntimeError when Google
    rate-limits or bot-blocks the requesting IP (HTTP 503/429) — the block
    is temporary; wait 10-15 minutes and retry.

    Args:
        query: Keywords matched against patent titles, abstracts, and text.
        limit: Maximum records (1-100).

    Returns records with: title, patent_id, inventors, assignee,
    filing_date, publication_date, url.
    """
    limit = max(1, min(int(limit), 100))
    q = requests.utils.quote(query)
    results: list[dict] = []
    for page in range((limit + 9) // 10):
        url = f"{API}?url=q%3D{q}%26num%3D10%26page%3D{page}"
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code in (503, 429):
            raise RuntimeError(_BLOCK_MESSAGE)
        r.raise_for_status()
        clusters = r.json().get("results", {}).get("cluster", [])
        patents = clusters[0].get("result", []) if clusters else []
        if not patents:
            break
        for p in patents:
            pat = p.get("patent", {})
            number = pat.get("publication_number", "")
            results.append({
                "title": _clean(pat.get("title", "")),
                "patent_id": number,
                "inventors": _clean(pat.get("inventor", "")),
                "assignee": _clean(pat.get("assignee", "")),
                "filing_date": pat.get("filing_date", ""),
                "publication_date": pat.get("publication_date", ""),
                "url": f"https://patents.google.com/patent/{number}" if number else "",
            })
            if len(results) >= limit:
                return results
    return results
