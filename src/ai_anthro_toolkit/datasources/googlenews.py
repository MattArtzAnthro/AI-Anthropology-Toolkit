"""Google News search via the gnews scraper (mirrors the Google News Explorer notebook)."""

import unicodedata
from email.utils import parsedate_to_datetime

_INSTALL_MSG = 'Install the data extra: pip install "ai-anthropology-toolkit[data]"'

_BLOCK_GUIDANCE = (
    "This usually means Google News is rate-limiting or blocking requests, "
    "which is common on datacenter/cloud IPs (Colab, CI runners, VPNs). "
    "Wait a few minutes and retry, narrow the query, or run from a "
    "residential connection."
)

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


def _iso_date(raw: str) -> str:
    """Convert gnews's RFC 2822 'published date' to ISO 8601, keeping the raw
    string when it cannot be parsed."""
    try:
        return parsedate_to_datetime(raw).isoformat()
    except Exception:
        return raw


def search_google_news(query: str, limit: int = 10, period: str = "7d",
                       country: str = "US", language: str = "en") -> list[dict]:
    """Search Google News and return article records (quick-search mode).

    Google News has no official API; the gnews library scrapes the public
    news feeds, so requests can be rate-limited or blocked upstream. Blocks
    and empty responses raise RuntimeError with guidance instead of being
    returned as an empty success.

    Args:
        query: Search keywords.
        limit: Maximum articles (1-100).
        period: Lookback window: "1h", "1d", "7d", "30d", or "1y".
        country: Two-letter country code (e.g. "US", "GB").
        language: Two-letter language code (e.g. "en", "es").

    Returns records with: title, publisher, published (ISO 8601 when
    parseable), url, description.
    """
    try:
        from gnews import GNews
    except ImportError:
        raise RuntimeError(_INSTALL_MSG) from None

    limit = max(1, min(int(limit), 100))
    gn = GNews(language=language, country=country, period=period,
               max_results=limit)
    try:
        results = gn.get_news(query)
    except Exception as e:
        raise RuntimeError(
            f"Google News request failed ({type(e).__name__}: {e}). "
            + _BLOCK_GUIDANCE) from e

    if not results:
        raise RuntimeError(
            "Google News returned no results. This can mean no matching "
            "articles for the query and period, but an empty result often "
            "means rate limiting or IP blocking. " + _BLOCK_GUIDANCE)

    records = []
    for r in results:
        pub = r.get("publisher", {})
        records.append({
            "title": _normalize_text(r.get("title", "")),
            "publisher": _normalize_text(
                pub.get("title", "") if isinstance(pub, dict) else str(pub)),
            "published": _iso_date(r.get("published date", "")),
            "url": r.get("url", ""),
            "description": _normalize_text(r.get("description", "")),
        })
    return records
