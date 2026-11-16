"""The desk page shell (R1.5, R1.6, R8.3, R8.6, R8.7).

``render_page(desk)`` is the standalone desk: one file holding the design system's CSS,
the bundled A2UI renderer, and the desk's A2UI messages in a JSON block with what
``a2ui.local`` gives for deciding on the page with no server, so it opens offline with
nothing fetched but the fonts, which fall back to system faces.
``app_shell()`` is the same page without a desk, the MCP App resource; its desk arrives
in a tool result. Both end with the colophon from ``brand``.
"""

import json
import re
from collections.abc import Mapping
from functools import cache
from html import escape
from importlib import resources
from typing import Any

from ai_anthro_toolkit import __version__, brand, design
from ai_anthro_toolkit.desk import a2ui

__all__ = ["app_shell", "render_page"]

_PKG = "ai_anthro_toolkit.desk"
_KINDS = {"codebook": "Codebook desk", "rulings": "Rulings desk"}
# What would end an inline script early, or start the parser's double-escaped state.
_BREAKOUT = re.compile(r"<!--|<script", re.I)


@cache
def _template() -> str:
    return (resources.files(_PKG) / "template.html").read_text(encoding="utf-8")


@cache
def _bundle() -> str:
    return (resources.files(_PKG) / "app" / "dist" / "desk-app.js").read_text(encoding="utf-8")


def _script(js: str) -> str:
    """The bundle made safe to inline: ``</`` cannot close its script. A bundle holding
    ``<!--`` or ``<script`` is refused, since no escape is valid everywhere in code."""
    if _BREAKOUT.search(js):
        raise RuntimeError("The desk bundle holds '<!--' or '<script' and cannot be inlined; rebuild it.")
    return js.replace("</", "<\\/")


def _json(value: Any) -> str:
    """JSON for an inline block: no ``<``, ``>`` or ``&`` survives to the HTML parser."""
    return json.dumps(value).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _fill(**parts: str) -> str:
    """The template with each ``{{NAME}}`` replaced in one pass, so nothing inserted is
    read again as a placeholder."""
    return re.sub(r"\{\{([A-Z]+)\}\}", lambda m: parts[m.group(1)], _template())


def _page(*, title: str, kind: str, heading: str, data: str) -> str:
    # @import counts only before every other rule, so the fonts open the stylesheet.
    css = f'@import url("{design.FONTS_URL}");\n' + design.tokens_css() + design.a2ui_css() + design.stylesheet(fonts=False)
    return _fill(
        TITLE=escape(title), CSS=css, KIND=escape(kind), HEADING=heading,
        COLOPHON=brand.byline_html(__version__, full=True), DATA=data, BUNDLE=_script(_bundle()),
    )


def render_page(desk: Mapping[str, Any]) -> str:
    """The standalone page for ``desk`` (as ``a2ui.surface`` takes it). The header shows
    the desk's title, or its kind when it has none; the author is named only in the
    colophon (R8.7)."""
    kind = _KINDS[desk["stage"]]
    title = str(desk.get("title") or "").strip()
    data = {"desk_id": desk["desk_id"], "stage": desk["stage"], "messages": a2ui.surface(desk), "local": a2ui.local(desk)}
    return _page(
        title=f"{title} · {kind}" if title else kind,
        kind=kind if title else "",
        heading=f'<h1 id="desk-title">{escape(title or kind)}</h1>',
        data=f'<script type="application/json" id="desk-data">{_json(data)}</script>\n',
    )


def app_shell() -> str:
    """The MCP App resource: the page with no desk. The view fills the header from the
    desk's data model when the desk arrives."""
    return _page(title="Ratification desk", kind="", heading='<h1 id="desk-title"></h1>', data="")
