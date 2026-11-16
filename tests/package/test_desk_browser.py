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
                for width in (240, 320, 1100):
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


# A host for the desk's own view: it delivers the build tool's result, then answers
# the view's tools/call requests by calling the server's tool in Python (see DeskView).
DESK_HOST = """<!doctype html>
<meta charset="utf-8">
<iframe id="view" style="width:900px;height:1600px;border:0"></iframe>
<script>
const RESULT = __RESULT__;
const frame = document.getElementById("view");
window.hostLog = [];
window.calls = [];
window.addEventListener("message", async (ev) => {
  const m = ev.data;
  if (!m || m.jsonrpc !== "2.0") return;
  window.hostLog.push(m.method || "response");
  const reply = (msg) => frame.contentWindow.postMessage(Object.assign({ jsonrpc: "2.0" }, msg), "*");
  if (m.method === "ui/initialize") {
    reply({ id: m.id, result: { protocolVersion: "2026-01-26", hostContext: { theme: "light" } } });
  } else if (m.method === "ui/notifications/initialized") {
    reply({ method: "ui/notifications/tool-result", params: RESULT });
  } else if (m.method === "tools/call") {
    window.calls.push(m.params);
    if (window.silent) return;  // a host that never answers
    if (window.rpcError) return reply({ id: m.id, error: { code: -32603, message: window.rpcError } });
    reply({ id: m.id, result: await window.callTool(m.params.name, m.params.arguments || {}) });
  }
});
frame.srcdoc = __SHELL__;
</script>
"""

APP_ONLY = ("desk_sync", "desk_finish")


def mcp_result(server, name, args):
    """A tools/call result as a host receives it: through server.mcp.call_tool, serialised
    the way it goes over the wire, a refusal as the isError result the SDK sends.

    Runs in a thread of its own, since Playwright's sync API holds this one's event loop.
    """
    from concurrent.futures import ThreadPoolExecutor

    import anyio
    from mcp.server.mcpserver.exceptions import ToolError

    def call():
        try:
            res = anyio.run(server.mcp.call_tool, name, args)
        except ToolError as exc:
            return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        return res.model_dump(by_alias=True, exclude_none=True, mode="json")

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(call).result()


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class DeskView(unittest.TestCase):
    """The desk in its MCP App shell, with a job store behind its app-only tools."""

    def setUp(self):
        import tempfile
        from unittest import mock

        from ai_anthro_toolkit.jobs import JobStore
        from ai_anthro_toolkit.mcp import server
        from tests.package.desk_helpers import load

        self.server, self.load = server, load
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.store = JobStore(Path(self._dir.name))
        patcher = mock.patch.object(server, "_jobs", self.store)
        patcher.start()
        self.addCleanup(patcher.stop)
        assert sync_playwright is not None  # the class is skipped otherwise
        self._pw = sync_playwright().start()
        self.addCleanup(self._pw.stop)
        self.browser = self._pw.chromium.launch()
        self.addCleanup(self.browser.close)

    def call_tool(self, name, args):
        """What the host returns for the view's tools/call: only app-only tools are offered,
        and each answers as the MCP layer answers a host, not as the Python function returns."""
        if name not in APP_ONLY:
            return {"content": [{"type": "text", "text": f"{name} is not offered to the view."}], "isError": True}
        return mcp_result(self.server, name, args)

    def build(self, **kw):
        result = self.server.build_ratification_desk(**kw)
        self.desk_id = result.structured_content["desk_id"]
        return {"content": [{"type": "text", "text": result.content[0].text}], "structuredContent": result.structured_content}

    def open_view(self, result, host=DESK_HOST):
        from ai_anthro_toolkit.desk import page as desk_page

        page = self.browser.new_page(viewport={"width": 1000, "height": 1700})
        self.errors = _watch(page)
        page.expose_function("callTool", self.call_tool)
        page.set_content(host.replace("__RESULT__", _js(result)).replace("__SHELL__", _js(desk_page.app_shell())))
        view = page.frame_locator("#view")
        view.locator("aat-decision-card article").first.wait_for(timeout=5000)
        page.wait_for_function("window.calls.length >= 1")
        self.wait_idle(page)
        return page, view

    def wait_idle(self, page):
        page.wait_for_function("document.getElementById('view').contentDocument.body.dataset.busy !== 'true'")

    def open_card(self, view):
        return view.locator("article.aat-card:not(.aat-card--done)").first

    def save(self, page, view, label="Save decision"):
        before = page.evaluate("window.calls.length")
        self.open_card(view).get_by_role("button", name=label).click()
        page.wait_for_function(f"window.calls.length > {before}")
        self.wait_idle(page)
        return page.evaluate("window.calls[window.calls.length - 1]")

    def saved(self):
        return json.loads(self.store.load_artifact(self.desk_id, "saved.json"))

    def codebook_view(self):
        return self.open_view(self.build(stage="codebook", codebook=self.load("codebook"), cases=self.load("cases")))

    def rulings_view(self, rid=None, **kw):
        rid = rid or self.server.ratify_codebook(codebook=self.load("codebook"))["ratification_id"]
        jobs = []
        for name in ("coding_a", "coding_b"):
            job = self.store.create("coding", {"ratification_id": rid, "mode": "delegated"})
            self.store.save_artifact(job, "result.json", json.dumps(self.load(name)))
            self.store.complete(job)
            jobs.append(job)
        result = self.build(stage="rulings", coding_job_ids=jobs, proposals=self.load("proposals"), **kw)
        self.cards = self.store.read(self.desk_id)["payload"]["cards"]
        return self.open_view(result)


def sizing_host(height):
    """DESK_HOST as Claude Desktop sizes an inline view: the frame starts at `height` and
    takes whatever height the view reports in ui/notifications/size-changed."""
    return (
        DESK_HOST.replace("height:1600px", f"height:{height}px")
        .replace("window.calls = [];", "window.calls = []; window.sizes = [];")
        .replace(
            '  if (m.method === "ui/initialize") {',
            '  if (m.method === "ui/notifications/size-changed") {\n'
            '    window.sizes.push(m.params); frame.style.height = m.params.height + "px"; return;\n'
            "  }\n"
            '  if (m.method === "ui/initialize") {',
        )
    )


# The frame's height, the view's full content height, and how far the view has scrolled.
FRAME = """() => { const f = document.getElementById('view'); const d = f.contentDocument;
  return { frame: f.clientHeight, content: d.documentElement.scrollHeight, scrolled: f.contentWindow.scrollY,
           sizes: window.sizes.length }; }"""


class TestFrameSize(DeskView):
    """In the MCP App the view reports its height, so the host shows the whole desk
    instead of a short default frame the researcher has to scroll inside."""

    def settled(self, page):
        """Wait until the frame has taken the last height the view reported."""
        page.wait_for_function(
            "window.sizes.length > 0 && document.getElementById('view').clientHeight"
            " === window.sizes[window.sizes.length - 1].height",
            timeout=5000,
        )
        page.wait_for_timeout(200)  # let any report the new frame size causes arrive
        return page.evaluate(FRAME)

    def test_a_short_frame_grows_to_hold_the_whole_desk(self):
        page, _view = self.open_view(
            self.build(stage="codebook", codebook=self.load("codebook"), cases=self.load("cases")),
            host=sizing_host(300),
        )
        size = self.settled(page)
        self.assertGreater(size["frame"], 300)
        self.assertLessEqual(size["content"], size["frame"], "the view still scrolls inside its frame")
        self.assertEqual(size["scrolled"], 0)
        self.assertEqual(self.errors, [])

    def test_a_tall_frame_shrinks_to_the_desk(self):
        page, _view = self.open_view(
            self.build(stage="codebook", codebook=self.load("codebook"), cases=self.load("cases")),
            host=sizing_host(6000),
        )
        size = self.settled(page)
        self.assertLess(size["frame"], 6000, "the view reported the frame's height, not its own")
        self.assertLessEqual(size["content"], size["frame"])

    def test_the_frame_follows_the_desk_as_it_changes(self):
        page, view = self.open_view(
            self.build(stage="codebook", codebook=self.load("codebook"), cases=self.load("cases")),
            host=sizing_host(300),
        )
        before = self.settled(page)
        self.save(page, view)
        page.wait_for_function(f"window.sizes.length > {before['sizes']}", timeout=5000)
        after = self.settled(page)
        self.assertNotEqual(after["frame"], before["frame"])
        self.assertLessEqual(after["content"], after["frame"])


class TestDeskViewActions(DeskView):
    def test_r7_11_actions_become_app_only_tool_calls(self):
        """R7.11: in the MCP App the desk opens through desk_sync, each Save goes to
        desk_sync as the renderer sends it, and Ratify goes to desk_finish; nothing else."""
        page, view = self.codebook_view()
        self.assertEqual(page.evaluate("window.calls[0]"), {"name": "desk_sync", "arguments": {"desk_id": self.desk_id}})
        self.assertEqual(self.saved(), {"decisions": {}, "exclusive": None})
        n = len(self.load("codebook")) + 1  # every code, and the exclusivity question
        self.assertEqual(view.locator(".aat-tally__text").inner_text(), f"{n} of {n} decisions need you")
        self.open_card(view).locator("input[value=adopt]").check()
        call = self.save(page, view)
        self.assertEqual(view.locator(".aat-tally__text").inner_text(), f"{n - 1} of {n} decisions need you")
        self.assertRegex(view.locator("ol.aat-progress").get_attribute("aria-label"), rf"^.+: 1 of {n} decided$")
        self.assertEqual(call["name"], "desk_sync")
        self.assertEqual(call["arguments"]["action"]["name"], "save_decision")
        self.assertEqual(call["arguments"]["action"]["context"]["card_id"], "code-01")
        self.assertEqual(call["arguments"]["action"]["context"]["decision"]["action"], ["adopt"])
        self.assertEqual(self.saved()["decisions"], {"code-01": {"action": "adopt"}})
        done = view.locator("article.aat-card--done")
        self.assertEqual(done.count(), 1)
        self.assertIn("Adopted", done.inner_text())
        codebook = self.load("codebook")
        self.assertEqual(self.open_card(view).locator(".aat-card__title").inner_text(), codebook[1]["code_label"])
        for _ in codebook[1:]:
            self.open_card(view).locator("input[value=adopt]").check()
            self.save(page, view)
        self.open_card(view).locator("input[value=no]").check()
        call = self.save(page, view, "Save answer")
        self.assertEqual(call["arguments"]["action"], {"name": "answer_exclusive", "context": {"exclusive": ["no"]}})
        self.assertEqual(view.locator(".aat-tally__text").inner_text(), "Every decision is made. Ratify when you are ready.")
        before = page.evaluate("window.calls.length")
        view.get_by_role("button", name="Ratify the codebook").click()
        page.wait_for_function(f"window.calls.length > {before}")
        self.wait_idle(page)
        self.assertEqual(page.evaluate("window.calls[window.calls.length - 1]"),
                         {"name": "desk_finish", "arguments": {"desk_id": self.desk_id}})
        finished = json.loads(self.store.load_artifact(self.desk_id, "finished.json"))["outcome"]
        notice = view.locator(".aat-notice--done")
        self.assertIn(finished["ratification_id"], notice.inner_text())
        self.assertEqual({c["name"] for c in page.evaluate("window.calls")}, set(APP_ONLY))
        self.assertEqual(self.errors, [])

    def test_a_refused_save_shows_a_notice_and_saves_nothing(self):
        page, view = self.codebook_view()
        self.save(page, view)  # nothing chosen
        refusal = view.locator(".aat-notice--refusal")
        self.assertIn("Choose what to do with code-01 before saving.", refusal.inner_text())
        self.assertEqual(self.saved()["decisions"], {})
        self.open_card(view).locator("input[value=adopt]").check()
        self.save(page, view)
        self.assertEqual(view.locator(".aat-notice--refusal").count(), 0)

    def test_change_reopens_a_done_card(self):
        page, view = self.codebook_view()
        self.open_card(view).locator("input[value=adopt]").check()
        self.save(page, view)
        view.locator("article.aat-card--done").get_by_role("button", name="Change").click()
        self.assertEqual(view.locator("article.aat-card:not(.aat-card--done)").count(), 1)  # the card it closed
        self.assertEqual(self.open_card(view).locator(".aat-card__title").inner_text(), self.load("codebook")[0]["code_label"])
        self.assertEqual(view.locator("article.aat-card--done").count(), 0)
        self.open_card(view).locator("input[value=delete]").check()
        self.save(page, view)
        self.assertEqual(self.saved()["decisions"], {"code-01": {"action": "delete"}})

    def decide_all(self, page, view, exclusive="no"):
        for _ in self.load("codebook"):
            self.open_card(view).locator("input[value=adopt]").check()
            self.save(page, view)
        self.open_card(view).locator(f"input[value={exclusive}]").check()
        self.save(page, view, "Save answer")

    def test_change_reopens_the_exclusivity_question(self):
        page, view = self.codebook_view()
        self.decide_all(page, view, "no")
        done = view.locator("article.aat-card--done").filter(has_text="mutually exclusive")
        done.get_by_role("button", name="Change").click()
        self.assertEqual(view.locator("article.aat-card:not(.aat-card--done)").count(), 1)
        self.open_card(view).locator("input[value=yes]").check()
        self.save(page, view, "Save answer")
        self.assertIs(self.saved()["exclusive"], True)

    def test_a_second_click_while_saving_sends_nothing(self):
        page, view = self.codebook_view()
        self.open_card(view).locator("input[value=adopt]").check()
        before = page.evaluate("window.calls.length")
        page.evaluate("window.silent = true")
        button = self.open_card(view).get_by_role("button", name="Save decision")
        button.click()
        button.click()
        page.wait_for_function(f"window.calls.length > {before}")
        page.wait_for_timeout(300)
        self.assertEqual(page.evaluate("window.calls.length"), before + 1)

    def test_a_finished_desk_keeps_saying_where_it_was_recorded(self):
        """Reopened after Ratify, the view shows the ratification, and Change reopens nothing."""
        page, view = self.codebook_view()
        self.decide_all(page, view)
        view.get_by_role("button", name="Ratify the codebook").click()
        view.locator(".aat-notice--done").wait_for(timeout=5000)
        rid = json.loads(self.store.load_artifact(self.desk_id, "finished.json"))["outcome"]["ratification_id"]
        page.close()
        page, again = self.open_view(self.build_result())
        notice = again.locator(".aat-notice--done")
        self.assertIn(rid, notice.inner_text())
        calls = page.evaluate("window.calls.length")
        again.locator("article.aat-card--done").first.get_by_role("button", name="Change").click()
        self.assertEqual(again.locator("article.aat-card:not(.aat-card--done)").count(), 0)
        self.assertIn(rid, again.locator(".aat-notice--done").inner_text())
        self.assertEqual(again.locator(".aat-notice--refusal").count(), 0)
        self.assertEqual(page.evaluate("window.calls.length"), calls)

    def test_a_host_that_passes_on_only_text_still_saves(self):
        """The view reads the same JSON from the text when a host drops structuredContent."""
        def text_only(name, args):
            out = mcp_result(self.server, name, args)
            out.pop("structuredContent", None)
            return out

        self.call_tool = text_only
        page, view = self.codebook_view()
        self.open_card(view).locator("input[value=adopt]").check()
        self.save(page, view)
        self.assertEqual(self.saved()["decisions"], {"code-01": {"action": "adopt"}})
        self.assertEqual(view.locator("article.aat-card--done").count(), 1)
        self.assertEqual(view.locator(".aat-notice--refusal").count(), 0)

    def build_result(self):
        """The build result for this desk, as a host delivers it to a new view."""
        from ai_anthro_toolkit.desk import a2ui, gate

        result = {"content": [], "structuredContent": {**self.store.read(self.desk_id)["payload"], "desk_id": self.desk_id}}
        result["structuredContent"]["a2ui"] = a2ui.surface(gate.load_desk(self.store, self.desk_id))
        return result

    def test_r7_9_reopen_restores_saved_decisions(self):
        """R7.9: a desk reopened in a new view shows the decisions saved in the last one."""
        page, view = self.codebook_view()
        self.open_card(view).locator("input[value=adopt]").check()
        self.save(page, view)
        page.close()
        _, again = self.open_view(self.build_result())
        done = again.locator("article.aat-card--done")
        self.assertEqual(done.count(), 1)
        self.assertIn("Adopted", done.inner_text())
        self.assertEqual(self.open_card(again).locator(".aat-card__title").inner_text(), self.load("codebook")[1]["code_label"])

    def test_r7_9_reopen_restores_every_decision_and_the_answer(self):
        page, view = self.codebook_view()
        self.decide_all(page, view, "yes")
        page.close()
        _, again = self.open_view(self.build_result())
        n = len(self.load("codebook")) + 1
        self.assertEqual(again.locator("article.aat-card--done").count(), n)
        self.assertEqual(again.locator("article.aat-card:not(.aat-card--done)").count(), 0)
        self.assertEqual(again.locator(".aat-tally__text").inner_text(), "Every decision is made. Ratify when you are ready.")


class TestRulingsView(DeskView):
    def depart(self, view):
        """Rule the open card with a code its proposal does not name; returns the card."""
        card = self.cards[0]
        other = next(code for code in self.store.read(self.desk_id)["payload"]["codes"] if code not in card["proposal"]["codes"])
        self.open_card(view).locator(f'input[value="{other}"]').check()
        return card, other

    def test_r3_2_proposal_appears_after_ruling(self):
        """R3.2: under blind-first no proposal is on screen until the ruling on its card is saved."""
        page, view = self.rulings_view()
        rationale = self.cards[0]["proposal"]["rationale"]
        self.assertNotIn(rationale, view.locator("main").inner_text())
        self.assertEqual(view.locator(".aat-prov--model").count(), 0)
        self.depart(view)
        self.save(page, view, "Save ruling")
        self.assertIn(rationale, view.locator(".aat-prov--model").inner_text())
        self.assertNotIn(self.cards[1]["proposal"]["rationale"], view.locator("main").inner_text())

    def test_r3_6_differing_ruling_shows_rule_question(self):
        """R3.6: a ruling that departs from its proposal keeps the card open with the rule
        question, and a ruling that states a rule is recorded as one."""
        page, view = self.rulings_view()
        card, other = self.depart(view)
        self.save(page, view, "Save ruling")
        open_card = self.open_card(view)
        self.assertEqual(open_card.locator(".aat-id").inner_text(), card["card_id"])
        self.assertIn("Does this ruling state a rule?", open_card.inner_text())
        open_card.locator("input[value=yes]").check()
        open_card.locator("textarea").first.fill("Selling below cost counts as food access.")
        self.save(page, view, "Save ruling")
        decision = self.saved()["decisions"][card["card_id"]]
        self.assertEqual((decision["codes"], decision["is_rule"]), ([other], True))
        self.assertEqual(decision["rule_text"], "Selling below cost counts as food access.")
        self.assertIn("states a rule", view.locator("article.aat-card--done").first.inner_text())

    def test_r3_3_exclusive_desk_allows_one_code(self):
        """R3.3: on a desk whose codes are mutually exclusive the ruling takes one code,
        and No code applies is not offered."""
        codebook_desk = self.server.build_ratification_desk(stage="codebook", codebook=self.load("codebook"), cases=self.load("cases"))
        stored = self.store.read(codebook_desk.structured_content["desk_id"])["payload"]
        doc = {"schema": "aat/desk-decisions@1", "desk_id": codebook_desk.structured_content["desk_id"],
               "card_checksum": stored["card_checksum"], "exclusive": True,
               "decisions": {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}}
        rid = self.server.record_desk_decisions(doc["desk_id"], doc, "page")["ratification_id"]
        page, view = self.rulings_view(rid)
        inputs = self.ruling(view).locator("input")
        self.assertEqual(set(inputs.evaluate_all("els => els.map(e => e.type)")), {"radio"})
        self.assertNotIn("(no code applies)", inputs.evaluate_all("els => els.map(e => e.value)"))
        inputs.nth(0).check()
        inputs.nth(1).check()
        self.assertEqual(inputs.evaluate_all("els => els.filter(e => e.checked).length"), 1)
        chosen = inputs.nth(1).get_attribute("value")
        self.save(page, view, "Save ruling")
        self.assertEqual(self.saved()["decisions"][self.cards[0]["card_id"]]["codes"], [chosen])

    def ruling(self, view):
        return self.open_card(view).locator("fieldset").filter(has=view.locator("legend", has_text="Your ruling"))

    def test_r3_3_a_desk_not_exclusive_takes_several_codes(self):
        """The contrast: where codes may overlap the ruling takes several, and No code applies is offered."""
        page, view = self.rulings_view()
        inputs = self.ruling(view).locator("input")
        self.assertEqual(set(inputs.evaluate_all("els => els.map(e => e.type)")), {"checkbox"})
        self.assertIn("(no code applies)", inputs.evaluate_all("els => els.map(e => e.value)"))

    def test_r7_9_a_ruling_awaiting_its_rule_answer_reopens_on_the_question(self):
        page, view = self.rulings_view()
        card, _ = self.depart(view)
        self.save(page, view, "Save ruling")
        page.close()
        from ai_anthro_toolkit.desk import a2ui, gate

        result = {"content": [], "structuredContent": {**self.store.read(self.desk_id)["payload"], "desk_id": self.desk_id}}
        result["structuredContent"]["a2ui"] = a2ui.surface(gate.load_desk(self.store, self.desk_id))
        _, again = self.open_view(result)
        open_card = self.open_card(again)
        self.assertEqual(open_card.locator(".aat-id").inner_text(), card["card_id"])
        self.assertIn("Does this ruling state a rule?", open_card.inner_text())


class TestViewNotices(DeskView):
    def test_a_message_the_renderer_rejects_shows_a_notice(self):
        bad = [{"version": "v1.0", "createSurface": {"surfaceId": "s", "catalogId": CATALOG_ID}},
               {"version": "v1.0", "updateComponents": {"surfaceId": "s", "components": [
                   {"id": "root", "component": "Gauge"}]}}]
        from ai_anthro_toolkit.desk import page as desk_page

        page = self.browser.new_page()
        page.expose_function("callTool", self.call_tool)
        page.set_content(DESK_HOST.replace("__RESULT__", _js({"content": [], "structuredContent": {"a2ui": bad}}))
                         .replace("__SHELL__", _js(desk_page.app_shell())))
        refusal = page.frame_locator("#view").locator(".aat-notice--refusal")
        refusal.wait_for(timeout=5000)
        self.assertIn("Gauge", refusal.inner_text())

    def test_the_view_shows_the_desk_title(self):
        page, view = self.open_view(self.build(stage="codebook", codebook=self.load("codebook"), cases=self.load("cases"),
                                               title="Garden study"))
        self.assertEqual(view.locator("#desk-title").inner_text(), "Garden study")
        self.assertEqual(view.locator("#desk-kind").text_content(), "Codebook desk")

    def test_the_view_has_one_colophon(self):
        page, view = self.codebook_view()
        self.assertEqual(view.locator("footer.aat-byline").count(), 1)

    def test_a_refused_open_draws_the_desk_and_says_it_cannot_save(self):
        def refuse_open(name, args):
            if name == "desk_sync" and "action" not in args:
                return {"content": [{"type": "text", "text": "Saving is turned off here."}], "isError": True}
            return mcp_result(self.server, name, args)

        self.call_tool = refuse_open
        page, view = self.codebook_view()
        self.assertEqual(self.open_card(view).locator(".aat-card__title").inner_text(), self.load("codebook")[0]["code_label"])
        refusal = view.locator(".aat-notice--refusal")
        self.assertIn("Decisions cannot be saved in this view.", refusal.inner_text())
        self.assertIn("Saving is turned off here.", refusal.inner_text())

    def test_a_host_error_shows_its_message(self):
        page, view = self.codebook_view()
        page.evaluate("window.rpcError = 'The host refused the call.'")
        self.open_card(view).locator("input[value=adopt]").check()
        self.save(page, view)
        self.assertIn("The host refused the call.", view.locator(".aat-notice--refusal").inner_text())
        self.assertEqual(self.saved()["decisions"], {})

    def test_a_host_that_never_answers_frees_the_view(self):
        """The view gives up on a silent host, says so, and takes the next decision."""
        page, view = self.codebook_view()
        view.locator("body").evaluate("() => { window.DeskApp.settings.timeoutMs = 300; }")
        page.evaluate("window.silent = true")
        self.open_card(view).locator("input[value=adopt]").check()
        self.save(page, view)
        self.assertIn("The host did not answer.", view.locator(".aat-notice--refusal").inner_text())
        page.evaluate("window.silent = false")
        self.save(page, view)
        self.assertEqual(self.saved()["decisions"], {"code-01": {"action": "adopt"}})
        self.assertEqual(view.locator(".aat-notice--refusal").count(), 0)


class TestStandaloneDecisions(DeskView):
    """The standalone page, opened in a browser with no server behind it (R7.2, R7.3)."""

    ORIGIN = "http://localhost:8765/"  # a secure context, as a file is, so the clipboard is there

    def open_page(self, context=None, built=None):
        """The page build_ratification_desk wrote, served from an origin so that it has storage."""
        built = built or self.build(stage="codebook", codebook=self.load("codebook"), cases=self.load("cases"))
        html = Path(built["structuredContent"]["page"]).read_text(encoding="utf-8")
        context = context or self.browser.new_context(viewport={"width": 1000, "height": 1600})
        tab = context.new_page()
        self.errors = _watch(tab)
        tab.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=html)
                  if route.request.url == self.ORIGIN else route.fulfill(status=200, content_type="text/css", body=""))
        tab.goto(self.ORIGIN)
        tab.locator("aat-decision-card article").first.wait_for(timeout=5000)
        return tab

    def key(self):
        return f"aat-desk:{self.desk_id}:{self.store.read(self.desk_id)['payload']['card_checksum']}"

    def decide_all(self, tab, exclusive="no"):
        for _ in self.load("codebook"):
            self.open_card(tab).locator("input[value=adopt]").check()
            self.open_card(tab).get_by_role("button", name="Save decision").click()
        self.open_card(tab).locator(f"input[value={exclusive}]").check()
        self.open_card(tab).get_by_role("button", name="Save answer").click()

    def copied(self, tab):
        box = tab.locator("#desk-notices textarea")
        box.wait_for(timeout=5000)
        return json.loads(box.input_value())

    def test_r7_2_decision_survives_reload_outside_app(self):
        """R7.2: with no host, each decision saves in the browser and a reload restores it."""
        tab = self.open_page()
        self.open_card(tab).locator("input[value=adopt]").check()
        self.open_card(tab).get_by_role("button", name="Save decision").click()
        self.assertEqual(tab.locator("article.aat-card--done").count(), 1)
        stored = json.loads(tab.evaluate("k => localStorage.getItem(k)", self.key()))
        self.assertEqual(stored, {"decisions": {"code-01": {"action": "adopt"}}, "exclusive": None})
        tab.reload()
        tab.locator("article.aat-card--done").wait_for(timeout=5000)
        self.assertIn("Adopted", tab.locator("article.aat-card--done").inner_text())
        self.assertEqual(self.open_card(tab).locator(".aat-card__title").inner_text(), self.load("codebook")[1]["code_label"])
        self.assertEqual(self.store.load_artifact(self.desk_id, "saved.json"), None)  # nothing reached the server
        self.assertEqual(self.errors, [])

    def test_r7_2_a_refused_decision_saves_nothing(self):
        tab = self.open_page()
        self.open_card(tab).get_by_role("button", name="Save decision").click()
        self.assertIn("Choose what to do with code-01 before saving.", tab.locator(".aat-notice--refusal").inner_text())
        self.assertIsNone(tab.evaluate("k => localStorage.getItem(k)", self.key()))

    def test_r7_2_blocked_storage_keeps_decisions_in_memory_with_a_notice(self):
        """R7.2: where the browser refuses storage the decisions stay on the page, and it says so."""
        context = self.browser.new_context()
        context.add_init_script("Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('blocked', 'SecurityError'); } });")
        tab = self.open_page(context)
        notice = tab.locator(".aat-notice", has_text="This browser is not keeping the decisions.")
        self.assertIn("Copy them as JSON", notice.inner_text())
        self.open_card(tab).locator("input[value=adopt]").check()
        self.open_card(tab).get_by_role("button", name="Save decision").click()
        self.assertEqual(tab.locator("article.aat-card--done").count(), 1)
        self.assertEqual(notice.count(), 1)
        tab.get_by_role("button", name="Copy decisions as JSON").click()
        self.assertEqual(self.copied(tab)["decisions"], {"code-01": {"action": "adopt"}})

    def test_r7_2_a_ruling_releases_its_proposal_on_the_page(self):
        """R3.2 on the standalone page: the proposal shows only after its ruling is saved."""
        rid = self.server.ratify_codebook(codebook=self.load("codebook"))["ratification_id"]
        jobs = []
        for name in ("coding_a", "coding_b"):
            job = self.store.create("coding", {"ratification_id": rid, "mode": "delegated"})
            self.store.save_artifact(job, "result.json", json.dumps(self.load(name)))
            self.store.complete(job)
            jobs.append(job)
        tab = self.open_page(built=self.build(stage="rulings", coding_job_ids=jobs, proposals=self.load("proposals")))
        cards = self.store.read(self.desk_id)["payload"]["cards"]
        self.assertEqual(tab.locator(".aat-prov--model").count(), 0)
        other = next(c for c in self.store.read(self.desk_id)["payload"]["codes"] if c not in cards[0]["proposal"]["codes"])
        self.open_card(tab).locator(f'input[value="{other}"]').check()
        self.open_card(tab).get_by_role("button", name="Save ruling").click()
        self.assertIn(cards[0]["proposal"]["rationale"], tab.locator(".aat-prov--model").inner_text())
        self.assertIn("Does this ruling state a rule?", self.open_card(tab).inner_text())
        self.assertNotIn(cards[1]["proposal"]["rationale"], tab.locator("main").inner_text())

    def test_r7_3_copied_json_accepted_by_record_desk_decisions(self):
        """R7.3: the document the page copies is one record_desk_decisions ratifies."""
        context = self.browser.new_context()
        context.grant_permissions(["clipboard-read", "clipboard-write"], origin=self.ORIGIN)
        tab = self.open_page(context)
        tab.get_by_role("button", name="Ratify the codebook").click()
        self.assertIn(f"{len(self.load('codebook')) + 1} decisions are still open.", tab.locator(".aat-notice--refusal").inner_text())
        self.decide_all(tab)
        tab.get_by_role("button", name="Copy decisions as JSON").click()
        doc = self.copied(tab)
        self.assertEqual(json.loads(tab.evaluate("navigator.clipboard.readText()")), doc)
        self.assertEqual(tab.locator("#desk-notices .aat-notice__title").inner_text(), "The decisions are copied as JSON.")
        outcome = self.server.record_desk_decisions(self.desk_id, doc, "page")
        self.assertRegex(outcome["ratification_id"], r"^ratification-[0-9a-f]{8}$")
        self.assertEqual(self.errors, [])

    def test_r7_3_ratify_on_the_page_gives_the_decisions_to_record(self):
        tab = self.open_page()
        self.decide_all(tab)
        tab.get_by_role("button", name="Ratify the codebook").click()
        doc = self.copied(tab)
        self.assertIn("record_desk_decisions", tab.locator("#desk-notices").inner_text())
        self.assertEqual(set(doc["decisions"]), {c["card_id"] for c in self.store.read(self.desk_id)["payload"]["cards"]})
        self.assertIs(doc["exclusive"], False)

    def test_r7_3_where_the_clipboard_is_refused_the_json_is_there_to_copy(self):
        context = self.browser.new_context()
        context.add_init_script("navigator.clipboard.writeText = () => Promise.reject(new Error('denied'));")
        tab = self.open_page(context)
        tab.get_by_role("button", name="Copy decisions as JSON").click()
        self.assertEqual(self.copied(tab)["desk_id"], self.desk_id)
        self.assertEqual(tab.locator("#desk-notices .aat-notice__title").inner_text(), "Copy the decisions below.")

    def rulings_page(self):
        rid = self.server.ratify_codebook(codebook=self.load("codebook"))["ratification_id"]
        jobs = []
        for name in ("coding_a", "coding_b"):
            job = self.store.create("coding", {"ratification_id": rid, "mode": "delegated"})
            self.store.save_artifact(job, "result.json", json.dumps(self.load(name)))
            self.store.complete(job)
            jobs.append(job)
        tab = self.open_page(built=self.build(stage="rulings", coding_job_ids=jobs, proposals=self.load("proposals")))
        return tab, self.store.read(self.desk_id)["payload"]

    def stored(self, tab):
        return tab.evaluate("k => localStorage.getItem(k)", self.key())

    def reopened(self, tab, kept, key=None):
        """The page reloaded with ``kept`` as what this browser holds for it."""
        tab.evaluate("([k, v]) => localStorage.setItem(k, v)", [key or self.key(), kept])
        tab.reload()
        tab.locator("aat-decision-card article").first.wait_for(timeout=5000)
        return tab

    def test_r7_2_the_page_refuses_what_the_server_would_refuse(self):
        """R7.2: a save the server would refuse is refused on the page, in its words, and kept nowhere."""
        tab = self.open_page()
        label = self.load("codebook")[0]["code_label"]
        self.open_card(tab).locator("input[value=merge]").check()
        self.open_card(tab).get_by_role("button", name="Save decision").click()
        refusal = tab.locator(".aat-notice--refusal")
        self.assertIn("This decision was not saved.", refusal.inner_text())
        self.assertIn(f"code-01: {label} is merged into '', which is not a code in this codebook.", refusal.inner_text())
        self.open_card(tab).locator("input[value=reword]").check()
        self.open_card(tab).get_by_role("button", name="Save decision").click()
        self.assertIn(f"code-01: The reword of {label} has an empty definition.", refusal.inner_text())
        self.assertEqual(tab.locator("article.aat-card--done").count(), 0)
        self.assertIsNone(self.stored(tab))
        self.assertEqual(self.errors, [])

    def test_r7_2_an_exclusion_without_a_reason_is_refused_on_the_page(self):
        tab, desk = self.rulings_page()
        self.open_card(tab).get_by_role("button", name="Exclude this chunk").click()
        self.assertIn(f"{desk['cards'][0]['card_id']}: An exclusion needs a reason.", tab.locator(".aat-notice--refusal").inner_text())
        self.assertIsNone(self.stored(tab))
        self.open_card(tab).get_by_label("Reason for excluding").fill("Interviewer talking.")
        self.open_card(tab).get_by_role("button", name="Exclude this chunk").click()
        self.assertEqual(tab.locator("article.aat-card--done").count(), 1)
        self.assertEqual(tab.locator(".aat-notice--refusal").count(), 0)

    def test_r7_2_a_changed_decision_is_the_one_a_reload_restores(self):
        tab = self.open_page()
        self.open_card(tab).locator("input[value=adopt]").check()
        self.open_card(tab).get_by_role("button", name="Save decision").click()
        tab.locator("article.aat-card--done").get_by_role("button", name="Change").click()
        self.open_card(tab).locator("input[value=delete]").check()
        self.open_card(tab).get_by_role("button", name="Save decision").click()
        tab.reload()
        tab.locator("article.aat-card--done").wait_for(timeout=5000)
        self.assertIn("Deleted", tab.locator("article.aat-card--done").inner_text())
        self.assertEqual(json.loads(self.stored(tab))["decisions"], {"code-01": {"action": "delete"}})

    def test_r7_2_a_reloaded_rulings_page_shows_its_released_proposal(self):
        """A departing ruling's card stays open with its proposal and the rule question,
        and a reload brings both back."""
        tab, desk = self.rulings_page()
        first = desk["cards"][0]
        other = next(c for c in desk["codes"] if c not in first["proposal"]["codes"])
        self.open_card(tab).locator(f'input[value="{other}"]').check()
        self.open_card(tab).get_by_role("button", name="Save ruling").click()
        self.assertIn("Does this ruling state a rule?", self.open_card(tab).inner_text())
        tab.reload()
        tab.locator(".aat-prov--model").wait_for(timeout=5000)
        self.assertIn(first["proposal"]["rationale"], tab.locator(".aat-prov--model").inner_text())
        self.assertIn("Does this ruling state a rule?", self.open_card(tab).inner_text())
        self.assertNotIn(desk["cards"][1]["proposal"]["rationale"], tab.locator("main").inner_text())

    def test_r7_2_what_the_browser_kept_is_checked_before_it_is_restored(self):
        """Damaged storage, and decisions the server would refuse, restore nothing and say so."""
        tab = self.open_page()
        for kept, says in (("not json", ""), ("[1]", "not a set of decisions"),
                           ('{"decisions": []}', "not a set of decisions"),
                           ('{"decisions": {"code-01": "adopt"}}', "not a set of decisions"),
                           ('{"decisions": {}, "exclusive": "yes"}', "not a set of decisions"),
                           ('{"decisions": {"code-01": {"action": "merge", "target": "Shared labour"}}}', "cannot be merged into itself"),
                           ('{"decisions": {"code-99": {"action": "adopt"}}}', "code-99 is not a card on this desk.")):
            with self.subTest(kept=kept):
                self.reopened(tab, kept)
                notice = tab.locator(".aat-notice--refusal")
                self.assertIn("The decisions this browser kept could not be restored.", notice.inner_text())
                self.assertIn(says, notice.inner_text())
                self.assertEqual(tab.locator("article.aat-card--done").count(), 0)

    def test_r7_2_decisions_kept_for_other_cards_are_not_restored(self):
        """What the browser kept for this desk with other cards (another checksum) stays unused."""
        tab = self.open_page()
        self.reopened(tab, '{"decisions": {"code-01": {"action": "adopt"}}, "exclusive": null}',
                      key=f"aat-desk:{self.desk_id}:{'0' * 64}")
        self.assertEqual(tab.locator("article.aat-card--done").count(), 0)
        self.assertEqual(tab.locator(".aat-notice").count(), 0)

    def test_r7_2_storage_that_refuses_writes_keeps_decisions_in_memory(self):
        context = self.browser.new_context()
        context.add_init_script("Storage.prototype.setItem = function () { throw new DOMException('full', 'QuotaExceededError'); };")
        tab = self.open_page(context)
        self.assertEqual(tab.locator(".aat-notice").count(), 0)
        self.open_card(tab).locator("input[value=adopt]").check()
        self.open_card(tab).get_by_role("button", name="Save decision").click()
        self.assertEqual(tab.locator("article.aat-card--done").count(), 1)
        self.assertEqual(tab.locator(".aat-notice", has_text="This browser is not keeping the decisions.").count(), 1)

    def test_r7_2_the_storage_notice_outlasts_other_notices(self):
        context = self.browser.new_context()
        context.add_init_script("Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('blocked', 'SecurityError'); } });")
        tab = self.open_page(context)
        self.open_card(tab).get_by_role("button", name="Save decision").click()  # refused
        self.assertEqual(tab.locator(".aat-notice--refusal").count(), 1)
        self.open_card(tab).locator("input[value=adopt]").check()
        self.open_card(tab).get_by_role("button", name="Save decision").click()
        self.assertEqual(tab.locator(".aat-notice--refusal").count(), 0)
        self.assertEqual(tab.locator(".aat-notice", has_text="This browser is not keeping the decisions.").count(), 1)

    def test_r7_3_copy_with_nothing_decided_gives_an_empty_document(self):
        tab = self.open_page()
        tab.get_by_role("button", name="Copy decisions as JSON").click()
        doc = self.copied(tab)
        self.assertEqual(doc["decisions"], {})
        self.assertIsNone(doc["exclusive"])

    def test_r7_3_ratify_counts_one_open_decision_in_the_singular(self):
        tab = self.open_page()
        for _ in self.load("codebook"):
            self.open_card(tab).locator("input[value=adopt]").check()
            self.open_card(tab).get_by_role("button", name="Save decision").click()
        tab.get_by_role("button", name="Ratify the codebook").click()
        self.assertIn("1 decision is still open.", tab.locator(".aat-notice--refusal").inner_text())

    def test_r7_2_the_page_framed_by_another_page_still_decides_on_its_own(self):
        """A page with its decisions in it decides standalone even inside a frame, where
        window.parent is not itself: no host message is sent or awaited."""
        built = self.build(stage="codebook", codebook=self.load("codebook"), cases=self.load("cases"))
        html = Path(built["structuredContent"]["page"]).read_text(encoding="utf-8")
        tab = self.browser.new_context(viewport={"width": 1000, "height": 1600}).new_page()
        tab.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html", body=(
            html if route.request.url == self.ORIGIN + "desk.html" else '<iframe src="desk.html" style="width:1000px;height:1500px"></iframe>'))
            if route.request.url.startswith(self.ORIGIN) else route.fulfill(status=200, content_type="text/css", body=""))
        tab.goto(self.ORIGIN)
        frame = tab.frame_locator("iframe")
        frame.locator("aat-decision-card article").first.wait_for(timeout=5000)
        self.open_card(frame).locator("input[value=adopt]").check()
        self.open_card(frame).get_by_role("button", name="Save decision").click()
        self.assertEqual(frame.locator("article.aat-card--done").count(), 1)
        stored = tab.frames[1].evaluate("k => localStorage.getItem(k)", self.key())
        self.assertEqual(json.loads(stored)["decisions"], {"code-01": {"action": "adopt"}})

    def test_r7_3_copy_in_the_app_when_the_desk_did_not_load_copies_nothing(self):
        """Where the host refused the view's load, there is no saved document to copy."""
        from ai_anthro_toolkit.desk import page as desk_page

        result = self.build(stage="codebook", codebook=self.load("codebook"), cases=self.load("cases"))
        page = self.browser.new_page(viewport={"width": 1000, "height": 1700})
        page.expose_function("callTool", self.call_tool)
        host = DESK_HOST.replace("window.calls = [];", "window.calls = []; window.rpcError = 'The server is down.';")
        page.set_content(host.replace("__RESULT__", _js(result)).replace("__SHELL__", _js(desk_page.app_shell())))
        view = page.frame_locator("#view")
        view.locator("aat-decision-card article").first.wait_for(timeout=5000)
        page.wait_for_function("window.calls.length >= 1")
        self.wait_idle(page)
        view.get_by_role("button", name="Copy decisions as JSON").click()
        self.assertIn("There are no decisions to copy.", view.locator(".aat-notice--refusal").last.inner_text())
        self.assertEqual(view.locator("#desk-notices textarea").count(), 0)

    def test_r7_3_copy_in_the_app_copies_what_the_server_saved(self):
        """R7.3 in the MCP App: Copy gives the decisions saved on the server, without a tool call."""
        page, view = self.codebook_view()
        self.open_card(view).locator("input[value=adopt]").check()
        self.save(page, view)
        calls = page.evaluate("window.calls.length")
        view.get_by_role("button", name="Copy decisions as JSON").click()
        box = view.locator("#desk-notices textarea")
        box.wait_for(timeout=5000)
        saved = self.saved()
        self.assertEqual(json.loads(box.input_value()), {
            "schema": "aat/desk-decisions@1", "desk_id": self.desk_id,
            "card_checksum": self.store.read(self.desk_id)["payload"]["card_checksum"],
            "exclusive": saved["exclusive"], "decisions": saved["decisions"]})
        self.assertEqual(page.evaluate("window.calls.length"), calls)


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class TestCatalogMarkup(unittest.TestCase):
    def test_r7_11_components_the_server_does_not_send_draw_their_markup(self):
        """Step, Status, Notice and Tally draw the design system's markup in the bundle."""
        from ai_anthro_toolkit.desk import page as desk_page
        from tests.package.test_desk_a2ui import CORPUS

        batch = dict(CORPUS)["the components the server does not send"]
        assert sync_playwright is not None
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                tab = browser.new_page()
                tab.set_content(desk_page.app_shell())
                self.assertTrue(tab.evaluate("b => window.DeskApp.render(b)", batch))
                self.assertEqual(tab.locator(".aat-step--done .aat-step__label").inner_text(), "Choose")
                self.assertEqual(tab.locator(".aat-step--done .aat-status--model").inner_text(), "Model draft")
                notice = tab.locator(".aat-notice--refusal[role=alert]")
                self.assertEqual(notice.locator(".aat-notice__title").inner_text(), "Can't ratify yet.")
                self.assertIn("2 codes have no decision.", notice.inner_text())
                self.assertEqual(notice.get_by_role("button").inner_text(), "Go")
                self.assertEqual(tab.locator(".aat-tally .aat-tally__text").inner_text(), "Done.")
                self.assertEqual(tab.locator(".aat-tally").get_by_role("button").count(), 0)  # nothing left to go to
            finally:
                browser.close()


@unittest.skipIf(SKIP_REASON, SKIP_REASON or "")
class TestOneColophon(unittest.TestCase):
    def test_r8_4_each_page_shows_the_brand_colophon_once(self):
        """The desk's Byline draws nothing: the page around it carries the colophon from
        brand, once, on the standalone page and in the MCP App shell alike."""
        from ai_anthro_toolkit import __version__, brand
        from ai_anthro_toolkit.desk import page as desk_page
        from tests.package.desk_helpers import codebook_desk

        want = brand.byline_html(__version__, full=True)
        shape = """el => [...el.children].map(n => [n.tagName, n.className, n.getAttribute('href'), n.textContent.trim()])"""
        assert sync_playwright is not None
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                tab = browser.new_page()
                tab.set_content(desk_page.render_page(codebook_desk()) + f"<template id=want>{want}</template>")
                tab.locator("aat-byline").wait_for(state="attached", timeout=5000)
                self.assertEqual(tab.locator("footer.aat-byline").count(), 1)
                self.assertEqual(tab.locator("aat-byline").inner_html().replace("<!---->", "").strip(), "")
                expected = tab.evaluate(f"() => ({shape})(document.getElementById('want').content.querySelector('footer'))")
                self.assertEqual(tab.locator("footer.aat-byline").evaluate(shape), expected)
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
