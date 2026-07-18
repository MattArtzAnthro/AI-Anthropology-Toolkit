"""Google Books Ngram frequencies (mirrors the Google Books Ngram Explorer notebook)."""

import requests

API = "https://books.google.com/ngrams/json"

# Short corpus codes mapped to Google's 2019 corpus IDs (from the notebook).
_CORPORA = {
    "en": 26,
    "en-fiction": 27,
    "en-us": 28,
    "en-gb": 29,
    "fr": 30,
    "de": 31,
    "es": 32,
    "it": 33,
    "zh": 34,
    "he": 35,
    "ru": 36,
}

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.6000.100 Safari/537.36")


def get_ngram_frequencies(terms: str | list[str], year_from: int = 1900,
                          year_to: int = 2022, corpus: str = "en",
                          case_insensitive: bool = False,
                          smoothing: int = 0) -> list[dict]:
    """Fetch word/phrase frequencies from the Google Books Ngram Viewer.

    Args:
        terms: A phrase, comma-separated phrases, or a list of phrases.
            Supports the Ngram Viewer's wildcard, POS-tag, and arithmetic syntax.
        year_from / year_to: Year range (inclusive), 1800-2022.
        corpus: Corpus code — "en" (default), "en-fiction", "en-us", "en-gb",
            "fr", "de", "es", "it", "zh", "he", or "ru" (2019 corpora).
        case_insensitive: Aggregate across capitalizations; the response then
            includes an "(All)" series plus each case variant.
        smoothing: Moving-average window in years (0 = raw yearly values).

    Returns long-format records with: term, year, frequency (relative
    frequency of the term among all tokens published that year).
    """
    content = ", ".join(terms) if isinstance(terms, list) else terms
    corpus_id = _CORPORA.get(str(corpus).lower())
    if corpus_id is None:
        raise ValueError(f"Unknown corpus {corpus!r}; expected one of "
                         f"{sorted(_CORPORA)}")
    params = {
        "content": content.strip(),
        "year_start": int(year_from),
        "year_end": int(year_to),
        "corpus": corpus_id,
        "smoothing": int(smoothing),
        # The endpoint requires lowercase string booleans; Python's True/False
        # serialize as "True"/"False" and are silently ignored.
        "case_insensitive": "true" if case_insensitive else "false",
    }
    r = requests.get(API, params=params, headers={"User-Agent": _UA}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise ValueError("Unexpected response structure (expected a JSON list)")
    years = range(int(year_from), int(year_to) + 1)
    rows = []
    for entry in data:
        term = entry.get("ngram")
        series = entry.get("timeseries") or []
        if not term:
            continue
        for year, freq in zip(years, series):
            rows.append({"term": term, "year": year, "frequency": float(freq)})
    return rows
