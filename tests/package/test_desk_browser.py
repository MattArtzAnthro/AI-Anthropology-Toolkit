"""The ratification desk's bundled A2UI renderer, driven in a real browser.

These tests need Playwright and a Chromium build. Without either they are
skipped with the reason printed. With AAT_REQUIRE_BROWSER=1 (set in CI, which
installs both) a missing browser fails the run instead of skipping it.
"""

import json
import os
import unittest
from pathlib import Path

from ai_anthro_toolkit import design

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "src" / "ai_anthro_toolkit" / "desk" / "app" / "dist" / "desk-app.js"

# The catalog identifiers the desk uses.
CATALOG_ID = "https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/catalogs/desk/v1"
BASIC_CATALOG_ID = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - depends on the environment
    sync_playwright = None


def _chromium_reason() -> str | None:
    """Why the browser tests cannot run here, or None when they can."""
    if sync_playwright is None:
        return "Playwright is not installed (pip install playwright)"
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
    except Exception as exc:  # noqa: BLE001 - any launch failure means skip
        return f"Chromium did not launch ({type(exc).__name__}); run: playwright install chromium"
    return None


def browser_gate(reason: str | None, required: bool) -> str | None:
    """The failure to report when the browser tests cannot run but must, else None."""
    if reason and required:
        return f"AAT_REQUIRE_BROWSER is set and the browser tests cannot run: {reason}"
    return None


SKIP_REASON = _chromium_reason()
REQUIRED = os.environ.get("AAT_REQUIRE_BROWSER") == "1"
if SKIP_REASON:
    print(f"\n[test_desk_browser] {'FAILING' if REQUIRED else 'skipped'}: {SKIP_REASON}")


class TestBrowserRequirement(unittest.TestCase):
    """A required browser that is missing fails the run; it never skips quietly."""

    def test_a_missing_browser_fails_when_required(self):
        self.assertIn("cannot run: no Chromium", browser_gate("no Chromium", required=True) or "")

    def test_a_missing_browser_only_skips_when_not_required(self):
        self.assertIsNone(browser_gate("no Chromium", required=False))
        self.assertIsNone(browser_gate(None, required=True))

    def test_this_run_meets_the_requirement(self):
        failure = browser_gate(SKIP_REASON, REQUIRED)
        if failure:
            self.fail(failure)


# A stubbed MCP Apps host. It answers ui/initialize with a host theme, then
# delivers a tool result whose structuredContent carries A2UI messages, the way
# a host delivers the result of the tool the view is linked to.
HOST_PAGE = """<!doctype html>
<meta charset="utf-8">
<iframe id="view" style="width:800px;height:600px;border:0"></iframe>
<script>
const MESSAGES = __MESSAGES__;
const frame = document.getElementById("view");
window.hostLog = [];
window.addEventListener("message", (ev) => {
  const m = ev.data;
  if (!m || m.jsonrpc !== "2.0") return;
  window.hostLog.push(m.method || "response");
  const reply = (msg) => frame.contentWindow.postMessage(Object.assign({ jsonrpc: "2.0" }, msg), "*");
  if (m.method === "ui/initialize") {
    reply({ id: m.id, result: { protocolVersion: "2026-01-26", hostContext: { theme: "dark" } } });
  } else if (m.method === "ui/notifications/initialized") {
    reply({ method: "ui/notifications/tool-result",
            params: { content: [], structuredContent: { a2ui: MESSAGES } } });
  }
});
frame.srcdoc = __SHELL__;
</script>
"""


def _shell(bundle_js: str) -> str:
    """The smallest view page: a mount point and the inlined bundle."""
    script = bundle_js.replace("</", "<\\/")
    return f'<!doctype html><meta charset="utf-8"><main id="desk"></main><script>{script}</script>'


def _js(value) -> str:
    """A JSON literal safe inside an inline <script>: no `</` can close it."""
    return json.dumps(value).replace("</", "<\\/")


def _watch(page) -> list[str]:
    """Collect uncaught errors and console.error output from the page and its frames."""
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    page.on("console", lambda m: errors.append(f"console.error: {m.text}") if m.type == "error" else None)
    return errors


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class TestBundledRendererInAppShell(unittest.TestCase):
    def test_r7_11_custom_component_renders_in_app_shell(self):
        """R7.11, rendering: the bundled A2UI renderer draws a basic Text and a
        toolkit Passage, delivered as a tool result to a view inside an MCP Apps
        host, and takes the host's theme. (Actions are covered with task 20.)"""
        self.assertTrue(BUNDLE.is_file(), f"no bundle at {BUNDLE}; run npm run build in desk/app")
        messages = [
            {
                "version": "v1.0",
                "createSurface": {"surfaceId": "desk", "catalogId": CATALOG_ID},
            },
            {
                "version": "v1.0",
                "updateComponents": {
                    "surfaceId": "desk",
                    "components": [
                        {
                            "id": "root",
                            "component": "Column",
                            "catalogId": BASIC_CATALOG_ID,
                            "children": ["heading", "passage"],
                        },
                        {
                            "id": "heading",
                            "component": "Text",
                            "catalogId": BASIC_CATALOG_ID,
                            "text": "Chunk 4 of 12",
                        },
                        {
                            "id": "passage",
                            "component": "Passage",
                            "text": "We kept the seed in the rafters, out of the damp.",
                            "source": "Interview 3, lines 40-41",
                        },
                    ],
                },
            },
        ]
        page_html = HOST_PAGE.replace("__MESSAGES__", _js(messages)).replace(
            "__SHELL__", _js(_shell(BUNDLE.read_text(encoding="utf-8")))
        )
        assert sync_playwright is not None  # the class is skipped otherwise
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page()
                errors = _watch(page)
                page.set_content(page_html)
                view = page.frame_locator("#view")
                passage = view.locator("aat-passage")
                passage.wait_for(timeout=5000)
                self.assertIn("We kept the seed in the rafters", passage.inner_text())
                self.assertIn("Interview 3, lines 40-41", passage.inner_text())
                self.assertIn("Chunk 4 of 12", view.locator("main").inner_text())
                self.assertEqual(view.locator("html").get_attribute("data-theme"), "dark")
                self.assertEqual(errors, [])
                log = page.evaluate("window.hostLog")
                self.assertEqual(log[:2], ["ui/initialize", "ui/notifications/initialized"])
            finally:
                browser.close()


def _themed_page(bundle_js: str, data_theme: str | None) -> str:
    """A standalone page carrying the design system's CSS, optionally forced to a theme."""
    css = design.tokens_css() + design.a2ui_css() + design.stylesheet(fonts=False)
    script = bundle_js.replace("</", "<\\/")
    attr = f' data-theme="{data_theme}"' if data_theme else ""
    return (
        f'<!doctype html><html{attr}><meta charset="utf-8"><style>{css}</style>'
        f'<main id="desk"></main><script>{script}</script></html>'
    )


THEMED_MESSAGES = [
    {"version": "v1.0", "createSurface": {"surfaceId": "s", "catalogId": BASIC_CATALOG_ID}},
    {
        "version": "v1.0",
        "updateComponents": {
            "surfaceId": "s",
            "components": [
                {"id": "root", "component": "Column", "children": ["t", "c", "b", "card", "field", "b2"]},
                {"id": "t", "component": "Text", "text": "Plain text"},
                {"id": "c", "component": "Text", "text": "A caption", "variant": "caption"},
                {"id": "bl", "component": "Text", "text": "Go"},
                {
                    "id": "b",
                    "component": "Button",
                    "child": "bl",
                    "variant": "primary",
                    "action": {"event": {"name": "go"}},
                },
                {"id": "card", "component": "Card", "child": "ct"},
                {"id": "ct", "component": "Text", "text": "Inside a card"},
                {"id": "field", "component": "TextField", "label": "A note", "value": {"@path": "/note"}},
                {"id": "b2l", "component": "Text", "text": "Later"},
                {"id": "b2", "component": "Button", "child": "b2l", "action": {"event": {"name": "later"}}},
            ],
        },
    },
]

# (data-theme attribute, the browser's colour-scheme preference, the theme expected)
THEME_CASES = [
    ("light", "light", "light"),
    ("dark", "light", "dark"),
    (None, "dark", "dark"),  # dark through prefers-color-scheme alone
    ("light", "dark", "light"),  # forced light under a dark preference
]

SWEEP = """() => {
  const out = [];
  for (const el of [document.querySelector('main'), ...document.querySelectorAll('main *')]) {
    const s = getComputedStyle(el);
    const where = el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ')[0] : '');
    for (const prop of ['color', 'backgroundColor', 'borderTopColor', 'borderRightColor',
                        'borderBottomColor', 'borderLeftColor']) {
      out.push([where, prop, s[prop]]);
    }
  }
  return out;
}"""


def _rgb(hex_colour: str) -> str:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgb({r}, {g}, {b})"


def _palette(theme: str) -> dict[str, str]:
    """Colour token name -> computed rgb() for one theme, aliases resolved."""
    raw = {t["name"]: t["value"] for t in design.tokens()["color"]["tokens"]}
    out = {}
    for name, value in raw.items():
        while isinstance(value, str) and value.startswith("{"):
            value = raw[value.strip("{}")]
        out[name] = _rgb(value if isinstance(value, str) else value[theme])
    return out


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class TestBasicComponentsTakeTheTokens(unittest.TestCase):
    def test_r8_6_basic_components_draw_in_token_colours(self):
        """R8.6: every colour the renderer's own basic components draw (text,
        background and borders) is a toolkit token, in each way a theme is chosen."""
        self.assertTrue(BUNDLE.is_file(), f"no bundle at {BUNDLE}")
        bundle_js = BUNDLE.read_text(encoding="utf-8")
        assert sync_playwright is not None  # the class is skipped otherwise
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                for data_theme, scheme, theme in THEME_CASES:
                    with self.subTest(data_theme=data_theme, scheme=scheme):
                        palette = _palette(theme)
                        allowed = set(palette.values()) | {"rgba(0, 0, 0, 0)"}
                        page = browser.new_page(color_scheme=scheme)
                        errors = _watch(page)
                        page.set_content(_themed_page(bundle_js, data_theme))
                        page.evaluate("m => window.DeskApp.render(m)", THEMED_MESSAGES)
                        button = page.locator("main button").first
                        button.wait_for(timeout=5000)
                        self.assertEqual(
                            page.locator("main .a2ui-text").first.evaluate("el => getComputedStyle(el).color"),
                            palette["ink"],
                        )
                        self.assertEqual(button.evaluate("el => getComputedStyle(el).backgroundColor"), palette["action"])
                        self.assertEqual(button.evaluate("el => getComputedStyle(el).color"), palette["on-action"])
                        off = [(w, prop, v) for w, prop, v in page.evaluate(SWEEP) if v not in allowed]
                        self.assertEqual(off, [], f"colours outside the {theme} tokens")
                        self.assertEqual(errors, [])
                        page.close()
            finally:
                browser.close()


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class TestColophonLayout(unittest.TestCase):
    def test_r8_3_description_sits_on_its_own_row(self):
        """R8.3: in the full colophon the author description stands on its own row,
        nothing beside it, set with text-wrap: balance; the colophon fits the width,
        narrow and wide, with and without the description."""
        from ai_anthro_toolkit import brand

        css = design.tokens_css() + design.stylesheet(fonts=False)
        assert sync_playwright is not None  # the class is skipped otherwise
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                for full in (True, False):
                    page_html = (
                        f'<!doctype html><meta charset="utf-8"><style>{css}</style>'
                        f"<main>{brand.byline_html('3.10.0', full=full)}</main>"
                    )
                    for width in (320, 400, 1100, 1600):
                        with self.subTest(full=full, width=width):
                            page = browser.new_page(viewport={"width": width, "height": 600})
                            page.set_content(page_html)
                            overflow = page.evaluate(
                                "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                            )
                            self.assertEqual(overflow, 0)
                            if full:
                                self.assertEqual(page.evaluate(_BESIDE_ABOUT), [], "beside the description")
                                self.assertEqual(
                                    page.locator(".aat-byline__about").evaluate("e => getComputedStyle(e).textWrap"),
                                    "balance",
                                )
                            page.close()
            finally:
                browser.close()


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class TestStandalonePage(unittest.TestCase):
    def test_r1_5_the_page_runs_its_inlined_bundle_offline(self):
        """R1.5: opened as a file with the network refused, the standalone page parses its
        escaped inline bundle and its data block, falls back to system fonts, and fits a
        narrow and a wide window."""
        from ai_anthro_toolkit.desk import page as desk_page
        from tests.package.desk_helpers import codebook_desk

        html = desk_page.render_page(codebook_desk(title="Garden cooperative study"))
        assert sync_playwright is not None  # the class is skipped otherwise
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                for width in (320, 1100):
                    with self.subTest(width=width):
                        tab = browser.new_page(viewport={"width": width, "height": 700})
                        tab.route("**/*", lambda route: route.fulfill(status=200, content_type="text/css", body=""))
                        errors = _watch(tab)
                        tab.set_content(html)
                        self.assertTrue(tab.evaluate("typeof window.DeskApp.render === 'function'"))
                        data = tab.evaluate("JSON.parse(document.getElementById('desk-data').textContent)")
                        self.assertEqual(data["desk_id"], "desk-0a1b2c3d")
                        self.assertEqual(tab.locator("h1").inner_text(), "Garden cooperative study")
                        self.assertTrue(tab.locator("footer.aat-byline").is_visible())
                        self.assertEqual(tab.evaluate(
                            "document.documentElement.scrollWidth - document.documentElement.clientWidth"), 0)
                        self.assertEqual(errors, [])
                        tab.close()
            finally:
                browser.close()


# The colophon's other children that share a row with the description.
_BESIDE_ABOUT = """() => {
  const about = document.querySelector('.aat-byline__about').getBoundingClientRect();
  return [...document.querySelector('.aat-byline').children]
    .filter(el => !el.classList.contains('aat-byline__about'))
    .filter(el => { const r = el.getBoundingClientRect(); return r.top < about.bottom && r.bottom > about.top; })
    .map(el => el.textContent);
}"""


if __name__ == "__main__":
    unittest.main()
