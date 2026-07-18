"""Google Trends retrieval via pytrends (mirrors the Google Trends Explorer notebook)."""

import json

_INSTALL_MSG = 'Install the data extra: pip install "ai-anthropology-toolkit[data]"'

_BLOCK_GUIDANCE = (
    "Google Trends rate-limits automated queries aggressively (HTTP 429), "
    "especially from datacenter/cloud IPs (Colab, CI runners, VPNs). "
    "Wait a few minutes and retry, use fewer terms, or run from a "
    "residential connection."
)


def _records(df) -> list[dict]:
    """Convert a DataFrame (index included) to a JSON-friendly list of row dicts."""
    return json.loads(df.reset_index().to_json(orient="records", date_format="iso"))


def get_google_trends(terms: str | list[str], timeframe: str = "today 12-m",
                      geo: str = "") -> dict:
    """Retrieve Google Trends interest data for up to 5 terms.

    Google Trends has no official API; pytrends scrapes the public endpoints,
    which rate-limit automated queries aggressively. When Trends returns no
    data at all (the signature of rate limiting or IP blocking, not a true
    absence of data), this raises RuntimeError with guidance instead of
    returning an empty success. Regional data is intermittently unavailable
    upstream, so "interest_by_region" may be an empty list even on success.

    Args:
        terms: One search term, a comma-separated string, or a list of terms.
            Google Trends compares at most 5 terms; extras are dropped.
        timeframe: Trends timeframe string (e.g. "today 12-m", "today 3-m",
            "now 7-d", "all").
        geo: ISO 3166-1 alpha-2 country ("US") or ISO 3166-2 subregion
            ("US-CA"); empty string for worldwide.

    Returns a dict with:
        interest_over_time: [{"date": iso, <term>: value, ...}, ...] on the
            0-100 relative-interest scale.
        interest_by_region: [{"geoName": ..., "geoCode": ..., <term>: value},
            ...] (may be empty).
        related_queries: {term: {"top": [...], "rising": [...]}}.
    """
    try:
        from pytrends.request import TrendReq
    except ImportError:
        raise RuntimeError(_INSTALL_MSG) from None

    if isinstance(terms, str):
        terms = [t.strip() for t in terms.split(",") if t.strip()]
    terms = [t for t in terms if t][:5]
    if not terms:
        raise ValueError("Provide at least one search term.")

    pytrends = TrendReq(hl="en-US", tz=0)
    try:
        pytrends.build_payload(kw_list=terms, geo=geo, timeframe=timeframe, cat=0)
    except Exception as e:
        raise RuntimeError(
            f"Could not reach Google Trends ({type(e).__name__}: {e}). "
            + _BLOCK_GUIDANCE) from e

    try:
        iot = pytrends.interest_over_time()
        if not iot.empty and "isPartial" in iot.columns:
            iot = iot.drop(columns=["isPartial"])
    except Exception:
        iot = None

    try:
        ibr = pytrends.interest_by_region(resolution="COUNTRY",
                                          inc_low_vol=True, inc_geo_code=True)
        ibr = ibr[ibr.select_dtypes(include="number").sum(axis=1) > 0]
    except Exception:
        ibr = None

    related = {term: {"top": [], "rising": []} for term in terms}
    try:
        rq = pytrends.related_queries()
        for term in terms:
            data = rq.get(term) or {}
            for kind in ("top", "rising"):
                df = data.get(kind)
                if df is not None and not df.empty:
                    related[term][kind] = json.loads(df.to_json(orient="records"))
    except Exception:
        pass  # related queries are frequently unavailable upstream

    if (iot is None or iot.empty) and (ibr is None or ibr.empty):
        raise RuntimeError(
            "Google Trends returned no data for this query. This is almost "
            "always rate limiting or IP blocking, not a true absence of "
            "data. " + _BLOCK_GUIDANCE)

    return {
        "interest_over_time": _records(iot) if iot is not None and not iot.empty else [],
        "interest_by_region": _records(ibr) if ibr is not None and not ibr.empty else [],
        "related_queries": related,
    }
