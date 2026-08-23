"""DOI Citation Formatter — a formatted citation from a bare DOI.

Wraps the DOI Foundation's citation formatter (https://citation.doi.org),
which renders registrar metadata through the Citation Style Language. It
covers Crossref, DataCite, and mEDRA DOIs, and ships every CSL style,
including the ones anthropology submits to: american-anthropological-
association, chicago-notes-bibliography-17th-edition, chicago-author-date-
17th-edition, journal-of-the-royal-anthropological-institute, and
social-anthropology.

This formats; it does not verify. The output is only as good as the
metadata the registrar holds, and registrar metadata is routinely wrong:
titles arrive mangled from PDF extraction, chapter records inherit their
book's title, some styles emit the deprecated dx.doi.org form, and bibtex
abstracts can carry raw JATS markup through from the registrar. Treat a
returned citation as a draft to check against the source, never as evidence
that the source says what a draft claims.
"""

import html
import re

import requests

FORMAT_API = "https://citation.doi.org/format"
STYLES_API = "https://citation.doi.org/styles"
LOCALES_API = "https://citation.doi.org/locales"

_UA = "ai-anthropology-toolkit (https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit)"

# Prefixes a DOI arrives wearing when it is copied out of a browser, a
# reference list, or a Zotero field. Longest first so the https forms are
# stripped before the bare "doi:" pattern is considered.
_DOI_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
    "doi.org/",
    "dx.doi.org/",
    "doi:",
)

class UnknownStyleError(ValueError):
    """The formatter does not ship the requested style.

    A distinct type because it is the one refusal that is not a fact about
    the DOI: it will fail every entry in a batch identically, so the batch
    stops on it rather than recording it N times. Batch control flow used to
    match on the message text and broke silently the first time the wording
    changed.
    """


def _clean(text: str) -> str:
    """Undo the transport artifacts, and only those.

    Two of them reach the rendered citation and would otherwise be pasted
    into a manuscript. The formatter HTML-escapes, so a journal title such
    as "Science, Technology, & Human Values" arrives carrying "&amp;". And
    registrar metadata routinely holds the newlines and indentation of the
    XML it was pretty-printed into, which survive as literal line breaks
    mid-title. No CSL style emits an internal newline of its own — checked
    across the styles this toolkit names, annotated bibliographies included
    — so collapsing whitespace cannot destroy a rendering the formatter
    meant. Nothing beyond these two is touched.
    """
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _raise_for_refusal(r, doi: str, style: str) -> None:
    """Fail with the formatter's own reason, not a guessed one.

    The formatter returns 400 and 404 for several distinct causes and does
    not evaluate DOI and style in a fixed order, so the status code alone
    does not identify what went wrong: the same unsupported format name
    comes back as "Unknown style ris" for one DOI and as a metadata error
    for another. Its message body does identify it, so that is what gets
    raised, with guidance attached only where the cause is recognized.

    The distinction that matters most is between a DOI that is not
    registered and one that is registered but whose metadata could not be
    retrieved. Reporting the second as the first tells a researcher a real
    reference is fake.
    """
    if r.status_code == 200:
        return
    body = _clean(r.text)
    if r.status_code in (429, 500, 502, 503, 504):
        raise RuntimeError(
            f"citation.doi.org returned {r.status_code}: {body or 'no detail'}. "
            "The formatter is rate-limiting or briefly unavailable; this is "
            "not a problem with the DOI. Wait and retry, and space out large "
            "batches.")
    if body.lower().startswith("unknown style"):
        raise UnknownStyleError(
            f"{body}. Call list_citation_styles for exact names — they are "
            "not guessable, and \"ris\" and \"csl\" are not styles here "
            "even though \"bibtex\" is.")
    if "metadata could not be retrieved" in body.lower():
        raise ValueError(
            f"DOI {doi!r} is registered, but citation.doi.org could not "
            f"retrieve metadata to format it ({body}). The DOI is not wrong. "
            "This can be transient, so retry before concluding the record is "
            "unformattable.")
    if body.lower().startswith("doi not found"):
        raise ValueError(
            f"DOI {doi!r} is not registered at citation.doi.org ({body}). "
            "Check for a typo or a truncated suffix.")
    if r.status_code in (400, 404):
        raise ValueError(
            f"citation.doi.org refused DOI {doi!r} in style {style!r} "
            f"({r.status_code}): {body or 'no detail given'}")
    r.raise_for_status()


_styles_cache: list[str] | None = None
_locales_cache: list[str] | None = None


def normalize_doi(doi: str) -> str:
    """Strip URL and `doi:` wrappers, leaving the bare 10.x/suffix form.

    Case is preserved. DOI resolution is case-insensitive, but registrar
    metadata is not always, and lowercasing a suffix has no upside here.
    """
    cleaned = (doi or "").strip()
    lowered = cleaned.lower()
    for prefix in _DOI_PREFIXES:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break
    if not cleaned:
        raise ValueError("No DOI given")
    if not cleaned.startswith("10."):
        raise ValueError(
            f"{doi!r} does not look like a DOI; expected the 10.<prefix>/"
            "<suffix> form, optionally wrapped in a doi.org URL")
    return cleaned


def format_citation(doi: str, style: str = "apa",
                    locale: str = "en-US") -> dict:
    """Render one DOI as a formatted citation in a named CSL style.

    Args:
        doi: A DOI, bare or wrapped in a doi.org URL or a `doi:` prefix.
        style: A CSL style name, exactly as `list_citation_styles` reports
            it. Guessing fails loudly: "chicago-note-bibliography" is not a
            style, "chicago-notes-bibliography" is. "bibtex" is also a style
            here and ignores `locale`; "ris" and "csl" are not.
        locale: A CSL locale such as "en-US", "en-GB", "de-DE", or "fr-FR".

    Returns a record with: doi, style, locale, citation, and source (the
    request URL, so a citation can be re-derived later). The citation is the
    formatter's own rendering, changed only by `_clean`: HTML entities are
    decoded and whitespace runs collapse to single spaces. Nothing else is
    rewritten, including the deprecated dx.doi.org URLs some styles emit.

    Raises ValueError when the formatter refuses the DOI or the style, with
    its own reason attached — in particular, a DOI that is registered but
    unformattable is reported as such rather than as a missing DOI.
    Raises RuntimeError when the formatter is rate-limiting or down.
    """
    cleaned = normalize_doi(doi)
    style = (style or "apa").strip()
    locale = (locale or "en-US").strip()
    params = {"doi": cleaned, "style": style, "lang": locale}
    r = requests.get(FORMAT_API, params=params,
                     headers={"User-Agent": _UA}, timeout=30)
    _raise_for_refusal(r, cleaned, style)
    return {
        "doi": cleaned,
        "style": style,
        "locale": locale,
        "citation": _clean(r.text),
        "source": r.url,
    }


def format_citation_batch(dois: list[str] | str, style: str = "apa",
                          locale: str = "en-US") -> dict:
    """Format many DOIs in one pass, in the order given.

    Deliberately not called a bibliography. The formatter renders one DOI per
    request, so this is that request repeated: it cannot sort entries the way
    a style's rules require, and it cannot disambiguate two works by the same
    author in the same year, both of which a real bibliography needs. Use it
    to render the entries, then order them yourself.

    Args:
        dois: DOIs in any accepted form, as a list or a comma- or
            newline-separated string.
        style / locale: As `format_citation`.

    Returns: style, locale, requested, formatted (records in input order),
    and failed (one record per DOI that could not be rendered, each with the
    reason). One bad DOI never discards the rest — a reference list is worth
    more with 29 of 30 entries and a named gap than it is as an exception.

    Raises ValueError if the style is unknown, since that fails every entry
    rather than one, and RuntimeError if the formatter starts refusing the
    batch for load.
    """
    if isinstance(dois, str):
        items = [d for d in re.split(r"[,\n]", dois) if d.strip()]
    else:
        items = [d for d in dois if str(d).strip()]
    formatted, failed = [], []
    for raw in items:
        try:
            formatted.append(format_citation(raw, style=style, locale=locale))
        except UnknownStyleError:
            # Not a fact about this DOI: it fails every remaining entry
            # identically, so stop rather than log one cause N times.
            raise
        except ValueError as e:
            failed.append({"doi": str(raw).strip(), "reason": str(e)})
    return {
        "style": style,
        "locale": locale,
        "requested": len(items),
        "formatted": formatted,
        "failed": failed,
    }


def list_citation_styles(contains: str = "", limit: int = 50) -> dict:
    """Find exact CSL style names the formatter accepts.

    The formatter ships thousands of styles and rejects anything that is not
    an exact name, so this is the lookup step before `format_citation`, not
    a catalog worth reading whole.

    Args:
        contains: Case-insensitive substring filter, e.g. "anthropolog",
            "chicago", "taylor-and-francis". Empty returns the first `limit`
            names alphabetically, which is rarely what anyone wants.
        limit: Maximum names returned (the count of matches is reported
            separately, so truncation is never silent).

    Returns: total (styles the formatter ships), matched (how many the
    filter hit), styles (up to `limit` names), and truncated.
    """
    global _styles_cache
    if _styles_cache is None:
        r = requests.get(STYLES_API, headers={"User-Agent": _UA}, timeout=30)
        r.raise_for_status()
        _styles_cache = sorted(str(s) for s in r.json())
    needle = (contains or "").strip().lower()
    matches = [s for s in _styles_cache if needle in s.lower()]
    limit = max(1, int(limit))
    return {
        "total": len(_styles_cache),
        "matched": len(matches),
        "styles": matches[:limit],
        "truncated": len(matches) > limit,
    }


def list_citation_locales() -> list[str]:
    """The CSL locale codes the formatter accepts (e.g. "en-US", "de-DE")."""
    global _locales_cache
    if _locales_cache is None:
        r = requests.get(LOCALES_API, headers={"User-Agent": _UA}, timeout=30)
        r.raise_for_status()
        _locales_cache = sorted(str(s) for s in r.json())
    return list(_locales_cache)
