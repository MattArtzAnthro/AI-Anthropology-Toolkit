"""Podcast episode metadata from RSS feeds (mirrors the Podcast RSS Explorer notebook)."""

import re
import unicodedata
from email.utils import parsedate_to_datetime

_REPLACEMENTS = [("‑", "-"), ("–", "-"), ("—", "-"),
                 ("‘", "'"), ("’", "'"), ("“", '"'),
                 ("”", '"'), ("…", "..."), ("&amp;", "&"),
                 ("&lt;", "<"), ("&gt;", ">")]


def _plain_text(text: str) -> str:
    """Strip HTML tags and normalize unicode punctuation."""
    if not isinstance(text, str):
        return text
    text = re.sub(r"<[^>]+>", "", text)
    text = unicodedata.normalize("NFKC", text)
    for old, new in _REPLACEMENTS:
        text = text.replace(old, new)
    return text.strip()


def _duration(dur) -> str:
    """Normalize an itunes duration to H:MM:SS."""
    if not dur:
        return ""
    dur = str(dur).strip()
    if re.match(r"^\d+:\d{2}:\d{2}$", dur):
        return dur
    if re.match(r"^\d+:\d{2}$", dur):
        return f"0:{dur}"
    try:
        secs = int(dur)
    except ValueError:
        return dur
    return f"{secs // 3600}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"


def get_podcast_episodes(feed_url: str, limit: int = 50) -> list[dict]:
    """Fetch episode metadata from a podcast RSS feed.

    Args:
        feed_url: URL of the podcast's RSS/Atom feed.
        limit: Maximum episodes to return (newest first, as ordered in the feed).

    Returns records with: title, published (ISO date, or the feed's raw date
    string if unparseable), duration (H:MM:SS), audio_url, description
    (plain text, truncated to 500 characters), link.
    """
    try:
        import feedparser
    except ImportError:
        raise RuntimeError(
            'Install the data extra: pip install "ai-anthropology-toolkit[data]"'
        ) from None
    feed = feedparser.parse(feed_url)
    episodes = []
    for e in feed.entries[:max(1, int(limit))]:
        enclosures = e.get("enclosures") or [{}]
        published = e.get("published", "")
        try:
            published = parsedate_to_datetime(published).strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            pass
        episodes.append({
            "title": _plain_text(e.get("title", "")),
            "published": published,
            "duration": _duration(e.get("itunes_duration", "")),
            "audio_url": enclosures[0].get("href", ""),
            "description": _plain_text(e.get("subtitle", "") or e.get("summary", ""))[:500],
            "link": e.get("link", ""),
        })
    return episodes
