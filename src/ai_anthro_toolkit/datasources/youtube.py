"""YouTube search and transcript fetching (mirrors the YouTube Video Search
and YouTube Transcript Fetcher notebooks)."""

import re

WATCH_URL = "https://www.youtube.com/watch?v="

_INSTALL_HINT = 'Install the data extra: pip install "ai-anthropology-toolkit[data]"'

_YOUTUBE_URL = re.compile(
    r"(?:https?://)?(?:www\.|m\.)?youtube\.com/watch\?v=([\w-]{11})"
    r"|(?:https?://)?youtu\.be/([\w-]{11})"
)


def _parse_video_id(url_or_id: str) -> str:
    """Extract an 11-character YouTube video ID from a URL or raw ID."""
    url_or_id = url_or_id.strip()
    m = _YOUTUBE_URL.search(url_or_id)
    if m:
        return m.group(1) or m.group(2)
    if re.fullmatch(r"[\w-]{11}", url_or_id):
        return url_or_id
    raise ValueError(f"Could not parse a YouTube video ID from {url_or_id!r}.")


def _runs_text(node) -> str:
    """Pull the first text run from a YouTube renderer node ({"runs": [...]})."""
    if isinstance(node, dict):
        runs = node.get("runs") or []
        return runs[0].get("text", "") if runs else ""
    return ""


def _simple_text(node) -> str:
    """Pull the simpleText value from a YouTube renderer node."""
    if isinstance(node, dict):
        return node.get("simpleText", "")
    return ""


def search_youtube(query: str, limit: int = 10) -> list[dict]:
    """Search YouTube videos via scrapetube (no API key required).

    Args:
        query: Search terms.
        limit: Maximum videos to return.

    Returns records with: video_id, title, channel, views, duration, url.

    Raises:
        RuntimeError: If scrapetube is not installed, if YouTube changed its
            internal page structure (which breaks the scrapetube library), or
            if YouTube is blocking/rate-limiting this IP address.
    """
    try:
        import scrapetube
    except ImportError:
        raise RuntimeError(_INSTALL_HINT) from None

    limit = max(1, int(limit))
    try:
        raw = list(scrapetube.get_search(query, limit=limit))
    except Exception as exc:
        raise RuntimeError(
            f"YouTube search failed ({type(exc).__name__}: {exc}). This usually "
            "means YouTube changed its internal page structure (which breaks the "
            "scrapetube library) or is rate-limiting this IP address. Wait a few "
            "minutes and retry, run from a residential connection, or check for "
            "a scrapetube update."
        ) from exc

    if not raw:
        raise RuntimeError(
            f"YouTube returned no results for {query!r}. An empty result usually "
            "means YouTube is blocking automated requests from this IP address "
            "(common on cloud/datacenter IPs). Wait a few minutes and retry, or "
            "run from a residential connection."
        )

    results = []
    for r in raw:
        vid = r.get("videoId", "")
        results.append({
            "video_id": vid,
            "title": _runs_text(r.get("title")),
            "channel": _runs_text(r.get("ownerText")),
            "views": _simple_text(r.get("viewCountText")),
            "duration": _simple_text(r.get("lengthText")),
            "url": f"{WATCH_URL}{vid}" if vid else "",
        })
    return results


def get_youtube_transcript(video_id: str, languages: list[str] | None = None,
                           join_segments: bool = True) -> dict:
    """Fetch a YouTube video transcript, preferring human-created captions.

    Human-created captions in a preferred language are tried first, then any
    human-created caption, then auto-generated captions in a preferred
    language, then any auto-generated caption.

    Args:
        video_id: An 11-character video ID or a full YouTube URL
            (youtube.com/watch?v=... and youtu.be/... forms are parsed).
        languages: Preferred language codes in priority order (default ["en"]).
        join_segments: Also return the transcript joined into a single string.

    Returns a dict with: video_id, language, auto_generated (bool), segments
    (each with start, duration, text), and text (the joined transcript, or
    None when join_segments is False).

    Raises:
        RuntimeError: If youtube-transcript-api is not installed, no
            transcript is available for the video, or YouTube blocks the
            request (YouTube blocks datacenter/cloud IPs frequently).
        ValueError: If a video ID cannot be parsed from the input.
    """
    try:
        from youtube_transcript_api import (
            CouldNotRetrieveTranscript,
            NoTranscriptFound,
            RequestBlocked,
            TranscriptsDisabled,
            YouTubeTranscriptApi,
        )
    except ImportError:
        raise RuntimeError(_INSTALL_HINT) from None

    vid = _parse_video_id(video_id)
    langs = list(languages) if languages else ["en"]

    api = YouTubeTranscriptApi()
    try:
        transcript_list = api.list(vid)
        chosen = None
        for matches in (
            lambda t: not t.is_generated and t.language_code in langs,
            lambda t: not t.is_generated,
            lambda t: t.is_generated and t.language_code in langs,
            lambda t: t.is_generated,
        ):
            chosen = next((t for t in transcript_list if matches(t)), None)
            if chosen is not None:
                break
        if chosen is None:
            raise RuntimeError(
                f"No transcript available for video {vid} "
                f"(languages tried: {', '.join(langs)})."
            )
        snippets = chosen.fetch()
    except RequestBlocked as exc:
        raise RuntimeError(
            f"YouTube blocked the transcript request for video {vid} "
            f"({type(exc).__name__}). YouTube blocks datacenter/cloud IPs "
            "frequently; wait a few minutes and retry, or run from a "
            "residential connection."
        ) from exc
    except (TranscriptsDisabled, NoTranscriptFound) as exc:
        raise RuntimeError(
            f"No transcript available for video {vid} "
            f"(languages tried: {', '.join(langs)}): {type(exc).__name__}."
        ) from exc
    except CouldNotRetrieveTranscript as exc:
        raise RuntimeError(
            f"Could not retrieve a transcript for video {vid} "
            f"(languages tried: {', '.join(langs)}): {type(exc).__name__}."
        ) from exc

    segments = [
        {
            "start": s.start,
            "duration": s.duration,
            "text": re.sub(r"\s+", " ", s.text).strip(),
        }
        for s in snippets
    ]
    text = " ".join(seg["text"] for seg in segments) if join_segments else None
    return {
        "video_id": vid,
        "language": chosen.language_code,
        "auto_generated": bool(chosen.is_generated),
        "segments": segments,
        "text": text,
    }
