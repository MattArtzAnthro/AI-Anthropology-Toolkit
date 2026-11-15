"""The toolkit's identity: the credit and links every page it renders carries.

Page renderers take these values from here and never spell them out. The DOI,
ORCID and repository match CITATION.cff. The design system's Byline component
(design/system/components) renders the same colophon as byline_html().
"""

from html import escape

TOOLKIT = "AI Anthropology Toolkit"
AUTHOR = "Matt Artz"
CREDIT = f"{TOOLKIT} by {AUTHOR}"
AUTHOR_DESCRIPTION = (
    f"{AUTHOR} is an AI anthropologist, designer, and technologist who works with AI to study, use,"
    " and contribute to the development and governance of AI, establishing AI anthropology as a field."
)
WEBSITE = "https://www.mattartz.me"
REPOSITORY = "https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit"
DOI_URL = "https://doi.org/10.5281/zenodo.16728812"
ORCID_URL = "https://orcid.org/0000-0002-3822-1429"

# The colophon's links after the credit, in order.
LINKS = (
    (WEBSITE, "Website"),
    (REPOSITORY, "Toolkit on GitHub"),
    (DOI_URL, "Cite (DOI)"),
    (ORCID_URL, "ORCID"),
)


def _link(href: str, inner: str) -> str:
    return f'<a href="{escape(href)}" target="_blank" rel="noopener">{inner}</a>'


def byline_html(version: str, *, full: bool) -> str:
    """The colophon a page ends with (R8.3, R8.4).

    The credit linked to the website, then "· v{version}" naming the version that
    built the page (left out when ``version`` is empty), then (with ``full``) the
    author's one-sentence description, then the links to the website, the
    repository, the citation DOI and ORCID. Styled by the design system's
    ``.aat-byline`` rules.
    """
    parts = [_link(WEBSITE, f"<b>{escape(TOOLKIT)}</b> by {escape(AUTHOR)}")]
    if version:
        parts.append('<span class="aat-byline__sep" aria-hidden="true">·</span>')
        parts.append(f'<span class="aat-id">v{escape(version)}</span>')
    if full:
        parts.append(f'<p class="aat-byline__about">{escape(AUTHOR_DESCRIPTION)}</p>')
    parts.extend(_link(href, escape(text)) for href, text in LINKS)
    return '<footer class="aat-byline">' + "\n  ".join(parts) + "</footer>"
