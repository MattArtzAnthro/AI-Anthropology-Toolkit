"""Google Scholar search via the scholarly scraper (mirrors the Google Scholar Explorer notebook)."""

import unicodedata

_INSTALL_MSG = 'Install the data extra: pip install "ai-anthropology-toolkit[data]"'

_BLOCK_GUIDANCE = (
    "Google Scholar is rate-limiting or blocking requests from this IP, "
    "which is common on datacenter/cloud IPs (Colab, CI runners, VPNs) and "
    "after many rapid queries. Wait a few minutes and retry, reduce the "
    "result count, or run from a residential connection."
)

_BLOCK_MARKERS = ("maxtries", "cannot fetch", "captcha", "blocked", "429")

_CHAR_MAP = {
    "‑": "-", "–": "-", "—": "-",
    "‘": "'", "’": "'",
    "“": '"', "”": '"',
    "…": "...",
}


def _normalize_text(text: str) -> str:
    """Normalize unicode characters to ASCII-friendly equivalents."""
    if not isinstance(text, str):
        return text
    text = unicodedata.normalize("NFKC", text)
    for src, dst in _CHAR_MAP.items():
        text = text.replace(src, dst)
    return text


def _is_block(e: Exception) -> bool:
    """Detect scholarly's block signatures (MaxTriesExceededException,
    "Cannot Fetch", CAPTCHA, HTTP 429)."""
    text = f"{type(e).__name__} {e}".lower()
    return any(marker in text for marker in _BLOCK_MARKERS)


def search_google_scholar(query: str, limit: int = 5,
                          year_from: int | None = None,
                          year_to: int | None = None) -> list[dict]:
    """Search Google Scholar and return publication records.

    Google Scholar has no official API; the scholarly library scrapes result
    pages one publication at a time and gets blocked quickly, so `limit` is
    capped at 20. Blocks (MaxTriesExceededException, "Cannot Fetch", CAPTCHA,
    HTTP 429) and empty responses raise RuntimeError with guidance instead of
    being returned as an empty success.

    Args:
        query: Search keywords.
        limit: Maximum publications (1-20).
        year_from / year_to: Restrict by publication year (inclusive;
            Scholar's year filtering is approximate).

    Returns records with: title, authors, year, venue, cited_by_count, url.
    """
    try:
        from scholarly import scholarly
    except ImportError:
        raise RuntimeError(_INSTALL_MSG) from None

    limit = max(1, min(int(limit), 20))
    search_kwargs = {}
    if year_from:
        search_kwargs["year_low"] = int(year_from)
    if year_to:
        search_kwargs["year_high"] = int(year_to)

    try:
        results_iter = scholarly.search_pubs(query, **search_kwargs)
    except Exception as e:
        raise RuntimeError(
            f"Google Scholar search failed ({type(e).__name__}: {e}). "
            + _BLOCK_GUIDANCE) from e

    records = []
    for _ in range(limit):
        try:
            r = next(results_iter)
        except StopIteration:
            break
        except Exception as e:
            if _is_block(e) or not records:
                raise RuntimeError(
                    f"Google Scholar stopped responding "
                    f"({type(e).__name__}: {e}). " + _BLOCK_GUIDANCE) from e
            break  # keep the partial results already fetched

        bib = r.get("bib", {})
        authors = bib.get("author", [])
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(" and ") if a.strip()]
        try:
            year = int(bib.get("pub_year"))
        except (TypeError, ValueError):
            year = None
        records.append({
            "title": _normalize_text(bib.get("title", "")),
            "authors": [_normalize_text(a) for a in authors],
            "year": year,
            "venue": _normalize_text(bib.get("venue", "")),
            "cited_by_count": r.get("num_citations", 0),
            "url": r.get("pub_url") or r.get("eprint_url") or "",
        })

    if not records:
        raise RuntimeError(
            "Google Scholar returned no results. This can mean no matching "
            "publications, but an empty result often means rate limiting or "
            "IP blocking. " + _BLOCK_GUIDANCE)
    return records
