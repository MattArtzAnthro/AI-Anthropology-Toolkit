"""The toolkit design system: tokens.json and bundle.css, shipped as package data.

Every page the toolkit renders takes its colours, type, spacing and components from here.
The brand book, components and previews live in design/system/ at the repository root.
"""

import json
import re
from functools import cache
from importlib import resources

__all__ = ["FONTS_URL", "FONT_DOMAINS", "a2ui_css", "stylesheet", "tokens", "tokens_css"]

FONT_DOMAINS: tuple[str, str] = ("https://fonts.googleapis.com", "https://fonts.gstatic.com")
"""The domains the fonts load from, declared in an MCP App's content security policy."""


def _read(name: str) -> str:
    return resources.files(__name__).joinpath(name).read_text(encoding="utf-8")


@cache
def _tokens_text() -> str:
    return _read("tokens.json")


@cache
def _bundle() -> str:
    return _read("bundle.css")


def _import_line(css: str) -> tuple[str, str]:
    """The stylesheet's first line, the fonts @import, and the URL it names."""
    first = css.split("\n", 1)[0]
    m = re.fullmatch(r'@import url\("([^"]+)"\);', first)
    if m is None:
        raise ValueError("bundle.css must open with the fonts @import line")
    return first, m.group(1)


FONTS_URL: str = _import_line(_bundle())[1]
"""The Google Fonts URL for Figtree, Source Serif 4 and Source Code Pro."""


def tokens() -> dict:
    """tokens.json, parsed. Each call returns a fresh copy."""
    return json.loads(_tokens_text())


def _value(raw: str) -> str:
    """A token value as CSS. An alias such as ``{action}`` becomes ``var(--action)``."""
    if raw.startswith("{") and raw.endswith("}"):
        return f"var(--{raw[1:-1]})"
    return raw


def _rule(selector: str, declarations: list[str], indent: str = "") -> str:
    body = "\n".join(f"{indent}  {d}" for d in declarations)
    return f"{indent}{selector} {{\n{body}\n{indent}}}"


def tokens_css() -> str:
    """The tokens as CSS custom properties.

    Light values sit on ``:root``. Dark values apply under ``prefers-color-scheme: dark``
    unless the page is forced light with ``data-theme="light"``, and whenever it is forced
    dark with ``data-theme="dark"``. An alias is declared once and follows its target.
    """
    t = tokens()
    light = ["color-scheme: light;"]
    dark = ["color-scheme: dark;"]
    for tok in t["color"]["tokens"]:
        value = tok["value"]
        if isinstance(value, str):  # an alias, the same in both themes
            light.append(f"--{tok['name']}: {_value(value)};")
            continue
        light.append(f"--{tok['name']}: {_value(value['light'])};")
        dark.append(f"--{tok['name']}: {_value(value['dark'])};")
    for family, stack in t["type"]["families"].items():
        light.append(f"--font-{family}: {stack};")
    for group in ("spacing", "radius", "size"):
        for tok in t[group]["tokens"]:
            light.append(f"--{tok['name']}: {tok['value']};")
    return "\n".join(
        [
            _rule(":root", light),
            "@media (prefers-color-scheme: dark) {\n"
            + _rule(':root:not([data-theme="light"])', dark, indent="  ")
            + "\n}",
            _rule(':root[data-theme="dark"]', dark),
        ]
    ) + "\n"


def stylesheet(fonts: bool) -> str:
    """bundle.css. With ``fonts=False`` the fonts @import line is dropped and the
    font stacks fall back to system fonts."""
    css = _bundle()
    if fonts:
        return css
    first, _ = _import_line(css)
    return css[len(first) :].lstrip("\n")


# The A2UI renderer's theme variables, each set from a toolkit token. The renderer
# declares its defaults with zero specificity, so these plain :root rules win, and
# the dark theme follows from tokens_css() because every value is a token variable.
_A2UI = {
    "--a2ui-color-background": "var(--paper)",
    "--a2ui-color-on-background": "var(--ink)",
    "--a2ui-color-surface": "var(--surface)",
    "--a2ui-color-on-surface": "var(--ink)",
    "--a2ui-color-primary": "var(--action)",
    "--a2ui-color-primary-hover": "var(--action-hover)",
    "--a2ui-color-on-primary": "var(--on-action)",
    "--a2ui-color-secondary": "var(--action-soft)",
    "--a2ui-color-on-secondary": "var(--ink)",
    "--a2ui-color-border": "var(--line-strong)",
    "--a2ui-color-input": "var(--surface)",
    "--a2ui-color-on-input": "var(--ink)",
    "--a2ui-text-color-text": "var(--ink)",
    "--a2ui-text-caption-color": "var(--ink-muted)",
    "--a2ui-textfield-color-border-focus": "var(--focus)",
    "--a2ui-textfield-color-error": "var(--refusal)",
    "--a2ui-checkbox-color-error": "var(--refusal)",
    "--a2ui-choicepicker-color-error": "var(--refusal)",
    "--a2ui-datetimeinput-color-error": "var(--refusal)",
    "--a2ui-slider-color-error": "var(--refusal)",
    "--a2ui-text-color": "var(--ink)",
    # Shadows and the backdrop are ink at low strength, as in bundle.css.
    "--a2ui-card-box-shadow": (
        "0 1px 2px color-mix(in srgb, var(--ink) 6%, transparent),"
        " 0 12px 32px color-mix(in srgb, var(--ink) 8%, transparent)"
    ),
    "--a2ui-modal-box-shadow": "0 6px 20px color-mix(in srgb, var(--ink) 10%, transparent)",
    "--a2ui-modal-backdrop-bg": "color-mix(in srgb, var(--ink) 50%, transparent)",
    "--a2ui-border-radius": "var(--radius-sm)",
    "--a2ui-font-family-title": "var(--font-sans)",
    "--a2ui-font-family-monospace": "var(--font-mono)",
    "--a2ui-spacing-m": "var(--space-2)",
}


def a2ui_css() -> str:
    """The A2UI renderer's theme variables set from the toolkit tokens (R8.6).

    Use it after tokens_css(); it names token variables and carries no colour of its own.
    """
    return _rule(":root", [f"{k}: {v};" for k, v in _A2UI.items()]) + "\n"
