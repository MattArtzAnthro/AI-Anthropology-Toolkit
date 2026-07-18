"""Diagnose which toolkit data sources are reachable from this environment.

Coding-agent sandboxes (Claude Cowork, Codex CLI, Gemini CLI) typically sit
behind network policies that allow scholarly APIs (OpenAlex, CrossRef,
PubMed) but block Google and YouTube endpoints. Run this first, collect from
what is reachable, and route blocked sources to local execution or their
Colab notebook instead of retrying against a firewall:

    python -m ai_anthro_toolkit.doctor
"""

from importlib.util import find_spec

from ai_anthro_toolkit import catalog

_INSTALL = 'pip install "ai-anthropology-toolkit[data]"'
_API_NOTE = "Official public API; works from most networks."
_SCRAPER_NOTE = ("Endpoints commonly block cloud and sandbox IPs; a "
                 "reachable homepage can still block queries with 403/429.")
_FEED_NOTE = "Fetches the feed URL you provide; depends on the feed host."


def _colab_fallback(filename: str) -> str:
    for nb in catalog.NOTEBOOKS:
        if nb["github_url"].endswith(filename) and nb.get("colab_url"):
            return (f"Run locally ({_INSTALL}) or in Colab: "
                    f"{nb['colab_url']}")
    return f"Run locally: {_INSTALL}"


SOURCES = [
    ("OpenAlex", "https://api.openalex.org/works?per-page=1",
     _API_NOTE, ""),
    ("CrossRef", "https://api.crossref.org/works?rows=1",
     _API_NOTE, ""),
    ("PubMed", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi",
     _API_NOTE, ""),
    ("Books Ngram",
     "https://books.google.com/ngrams/json?content=culture"
     "&year_start=2000&year_end=2001",
     _SCRAPER_NOTE, _colab_fallback("Google_Books_Ngram_Explorer.ipynb")),
    ("Google Trends", "https://trends.google.com/",
     _SCRAPER_NOTE, _colab_fallback("Google_Trends_Explorer.ipynb")),
    ("Google News", "https://news.google.com/rss",
     _SCRAPER_NOTE, _colab_fallback("Google_News_Explorer.ipynb")),
    ("Google Scholar", "https://scholar.google.com/",
     _SCRAPER_NOTE, _colab_fallback("Google_Scholar_Explorer.ipynb")),
    ("Google Patents", "https://patents.google.com/",
     _SCRAPER_NOTE, _colab_fallback("Google_Patents_Explorer.ipynb")),
    ("YouTube search", "https://www.youtube.com/",
     _SCRAPER_NOTE, _colab_fallback("YouTube_Video_Search.ipynb")),
    ("YouTube transcripts", "https://www.youtube.com/watch?v=jNQXAC9IVRw",
     _SCRAPER_NOTE, _colab_fallback("YouTube_Transcript_Fetcher.ipynb")),
    ("Podcast RSS", "https://feeds.npr.org/510289/podcast.xml",
     _FEED_NOTE, _colab_fallback("Podcast_RSS_Explorer.ipynb")),
]


def _default_fetch(url: str, timeout: float) -> int:
    import requests
    return requests.get(url, timeout=timeout, headers={
        "User-Agent": "Mozilla/5.0 (ai-anthro-doctor)"}).status_code


def environment_report(fetch=None) -> dict:
    """Probe every data source; never raises on network failure.

    fetch(url, timeout) -> HTTP status code; injectable for tests.
    """
    fetch = fetch or _default_fetch
    sources = []
    for name, url, note, fallback in SOURCES:
        try:
            reachable = fetch(url, 6) < 400
        except Exception:
            reachable = False
        sources.append({"name": name, "url": url, "reachable": reachable,
                        "note": note, "fallback": fallback})
    extras = {
        "data": all(find_spec(m) for m in ("feedparser", "pytrends",
                                           "gnews", "scholarly")),
        "chunking": find_spec("sentence_transformers") is not None,
    }
    return {"sources": sources, "extras": extras}


def main(fetch=None) -> None:
    report = environment_report(fetch=fetch)
    print("ai-anthropology-toolkit environment report")
    for s in report["sources"]:
        state = "reachable" if s["reachable"] else "UNREACHABLE"
        print(f"  [{state}] {s['name']} — {s['note']}")
        if not s["reachable"] and s["fallback"]:
            print(f"      fallback: {s['fallback']}")
    for extra, installed in report["extras"].items():
        state = "installed" if installed else "missing"
        print(f"  [extra:{extra}] {state}")
    print(f'Scraper dependencies install with: {_INSTALL}')
    print("Collect from reachable sources here; route unreachable ones to "
          "local execution or their Colab notebook.")


if __name__ == "__main__":
    main()
