"""The toolkit's identity: one module, matching CITATION.cff, used by every page renderer."""

import json
import os
import re
import shutil
import subprocess  # nosec B404 - runs node on the repository's own bundle.js
import unittest
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src" / "ai_anthro_toolkit"

# The settled text of the author description (specs/ratification-desk/requirements.md).
DESCRIPTION = (
    "Matt Artz is an AI anthropologist, designer, and technologist who works with AI to study, use,"
    " and contribute to the development and governance of AI, establishing AI anthropology as a field."
)

# The page renderers. Each takes the identity from brand and spells none of it out.
RENDERERS = [SRC / "network" / "viewer" / "__init__.py"]


def _citation_cff() -> dict[str, str]:
    """The fields of CITATION.cff the identity must match (a flat read; no YAML library)."""
    text = (REPO / "CITATION.cff").read_text(encoding="utf-8")

    def field(name: str) -> str:
        m = re.search(rf"^\s*-?\s*{name}:\s*\"?([^\"\n]+)\"?\s*$", text, re.M)
        if m is None:
            raise AssertionError(f"CITATION.cff has no {name}")
        return m.group(1).strip()

    return {
        "doi": field("doi"),
        "url": field("url"),
        "orcid": field("orcid"),
        "given": field("given-names"),
        "family": field("family-names"),
    }


class TestIdentityModule(unittest.TestCase):
    def test_r8_2_identity_matches_citation_cff(self):
        """R8.2: the DOI, ORCID and repository in brand match CITATION.cff."""
        from ai_anthro_toolkit import brand

        cff = _citation_cff()
        self.assertEqual(brand.DOI_URL, f"https://doi.org/{cff['doi']}")
        self.assertEqual(brand.ORCID_URL, cff["orcid"])
        self.assertEqual(brand.REPOSITORY, cff["url"])
        self.assertEqual(brand.AUTHOR, f"{cff['given']} {cff['family']}")

    def test_r8_1_identity_fields_are_present(self):
        """R8.1: the credit, the author, a one-sentence description, and the links."""
        from ai_anthro_toolkit import brand

        self.assertEqual(brand.CREDIT, f"AI Anthropology Toolkit by {brand.AUTHOR}")
        self.assertTrue(brand.AUTHOR_DESCRIPTION.startswith(f"{brand.AUTHOR} is "))
        self.assertEqual(brand.AUTHOR_DESCRIPTION.count(". "), 0, "one sentence")
        self.assertTrue(brand.AUTHOR_DESCRIPTION.endswith("."))
        self.assertEqual(brand.AUTHOR_DESCRIPTION, DESCRIPTION)
        for url in (brand.WEBSITE, brand.REPOSITORY, brand.DOI_URL, brand.ORCID_URL):
            self.assertRegex(url, r"^https://[^\s\"'<>]+$")


class _Byline(HTMLParser):
    """The colophon's links in order, as (href, text, target, rel), and where the description sits."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str, str, str]] = []
        self.order: list[str] = []  # "link:<text>" and "about" in document order
        self.tags: list[tuple[str, str, str]] = []  # (tag, class, aria-hidden) of every element
        self.about = ""
        self.text = ""  # every piece of visible text, in order
        self._href: dict[str, str] | None = None
        self._text = ""
        self._in_about = False

    def handle_starttag(self, tag, attrs):
        a = {k: v or "" for k, v in attrs}
        self.tags.append((tag, a.get("class", ""), a.get("aria-hidden", "")))
        if tag == "a":
            self._href, self._text = a, ""
        if tag == "p" and "aat-byline__about" in a.get("class", ""):
            self._in_about = True

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            text = " ".join(self._text.split())
            self.links.append((self._href.get("href", ""), text, self._href.get("target", ""), self._href.get("rel", "")))
            self.order.append(f"link:{text}")
            self._href = None
        if tag == "p" and self._in_about:
            self._in_about = False
            self.order.append("about")

    def handle_data(self, data):
        self.text += " " + data
        if self._href is not None:
            self._text += data
        if self._in_about:
            self.about += data


def _parse(html: str) -> _Byline:
    parser = _Byline()
    parser.feed(html)
    return parser


def _expected_links():
    from ai_anthro_toolkit import brand

    return [
        (brand.WEBSITE, brand.CREDIT),
        (brand.WEBSITE, "Website"),
        (brand.REPOSITORY, "Toolkit on GitHub"),
        (brand.DOI_URL, "Cite (DOI)"),
        (brand.ORCID_URL, "ORCID"),
    ]


class TestColophon(unittest.TestCase):
    def test_r8_3_colophon_links_in_order(self):
        """R8.3: the credit linked to the website, the author description, then
        links to the website, the repository, the citation DOI and ORCID."""
        from ai_anthro_toolkit import brand

        html = brand.byline_html("3.10.0", full=True)
        self.assertTrue(html.startswith('<footer class="aat-byline">'), html[:60])
        parsed = _parse(html)
        self.assertEqual([(h, t) for h, t, _, _ in parsed.links], _expected_links())
        self.assertEqual(parsed.order, ["link:" + brand.CREDIT, "about"] + [f"link:{t}" for _, t in _expected_links()[1:]])
        self.assertEqual(" ".join(parsed.about.split()), brand.AUTHOR_DESCRIPTION)
        for href, text, target, rel in parsed.links:
            self.assertEqual((target, rel), ("_blank", "noopener"), text)
        self.assertTrue(html.endswith("</footer>"), html[-60:])

    def test_r8_3_colophon_carries_no_other_text(self):
        """R8.3: the colophon reads exactly credit, version, description, links."""
        from ai_anthro_toolkit import brand

        parsed = _parse(brand.byline_html("3.10.0", full=True))
        expected = [brand.CREDIT, "·", "v3.10.0", DESCRIPTION] + [t for _, t in _expected_links()[1:]]
        self.assertEqual(" ".join(parsed.text.split()), " ".join(expected))

    def test_r8_3_short_byline_drops_only_the_description(self):
        from ai_anthro_toolkit import brand

        parsed = _parse(brand.byline_html("3.10.0", full=False))
        self.assertEqual([(h, t) for h, t, _, _ in parsed.links], _expected_links())
        self.assertNotIn("about", parsed.order)
        self.assertEqual(parsed.about, "")

    def test_r8_4_colophon_names_package_version(self):
        """R8.4: the colophon names the toolkit version that built the page."""
        import ai_anthro_toolkit
        from ai_anthro_toolkit import brand

        html = brand.byline_html(ai_anthro_toolkit.__version__, full=True)
        self.assertIn(f'<span class="aat-id">v{ai_anthro_toolkit.__version__}</span>', html)

    def test_r8_4_version_is_escaped(self):
        from ai_anthro_toolkit import brand

        html = brand.byline_html('1.0"><script>x</script>', full=False)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_r8_4_no_version_no_version_mark(self):
        """R8.4: without a version the colophon shows neither the separator nor a bare "v"."""
        from ai_anthro_toolkit import brand

        parsed = _parse(brand.byline_html("", full=False))
        self.assertNotIn("aat-id", [c for _, c, _ in parsed.tags])
        self.assertNotIn("·", parsed.text)
        self.assertEqual(" ".join(parsed.text.split()), " ".join([brand.CREDIT] + [t for _, t in _expected_links()[1:]]))

    def test_r8_3_design_system_byline_matches(self):
        """R8.3: the design system's Byline component (published to claude.ai), run
        under node, renders the same elements, classes, links, order and text as
        byline_html, with and without the description and the version."""
        from ai_anthro_toolkit import brand

        node = shutil.which("node")
        if node is None:
            if os.environ.get("AAT_REQUIRE_BROWSER") == "1":
                self.fail("AAT_REQUIRE_BROWSER is set and node is not installed")
            self.skipTest("node is not installed")
        cases = [{"version": "3.10.0", "full": True}, {"version": "3.10.0", "full": False},
                 {"version": "", "full": True}, {"version": "", "full": False}]
        bundle = REPO / "design" / "system" / "components" / "bundle.js"
        out = subprocess.run(  # nosec B603 - fixed arguments, no shell
            [node, "-e", _RENDER_BYLINE, str(bundle), json.dumps(cases)],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout
        for case, js_html in zip(cases, json.loads(out), strict=True):
            with self.subTest(**case):
                js, py = _parse(js_html), _parse(brand.byline_html(case["version"], full=case["full"]))
                self.assertEqual(js.tags, py.tags)
                self.assertEqual(js.links, py.links)
                self.assertEqual(js.order, py.order)
                self.assertEqual(" ".join(js.text.split()), " ".join(py.text.split()))


# Runs bundle.js with a createElement that builds HTML, and prints the Byline for each case.
_RENDER_BYLINE = r"""
const [bundlePath, casesJson] = process.argv.slice(1);
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
const h = (type, props, ...children) => ({ type, props: props || {}, children: children.flat() });
const html = (n) => {
  if (n === null || n === undefined || n === false) return "";
  if (typeof n !== "object") return esc(n);
  const attrs = Object.entries(n.props)
    .filter(([, v]) => v !== null && v !== undefined)
    .map(([k, v]) => ` ${k === "className" ? "class" : k}="${esc(v)}"`).join("");
  return `<${n.type}${attrs}>${n.children.map(html).join("")}</${n.type}>`;
};
globalThis.window = { React: { createElement: h, useState: (v) => [v, () => {}], useId: () => "id" } };
new Function(require("fs").readFileSync(bundlePath, "utf8"))();
console.log(JSON.stringify(JSON.parse(casesJson).map((c) => html(window.AAT.Byline(c)))));
"""


class TestRenderersTakeTheIdentity(unittest.TestCase):
    def test_r8_1_viewer_credit_comes_from_brand(self):
        """R8.1: no page renderer spells out the credit or a link of its own;
        the rendered viewer carries brand's values."""
        from ai_anthro_toolkit import brand
        from ai_anthro_toolkit.network.viewer import build_app_html

        literals = (brand.CREDIT, brand.WEBSITE, brand.REPOSITORY, brand.DOI_URL, brand.ORCID_URL,
                    brand.AUTHOR_DESCRIPTION)
        for path in RENDERERS:
            source = path.read_text(encoding="utf-8")
            for literal in literals:
                self.assertNotIn(literal, source, f"{path.relative_to(REPO)} spells out {literal!r}")
        html = build_app_html()
        self.assertIn(brand.CREDIT, html)
        self.assertIn(brand.WEBSITE, html)

    def test_r8_5_viewer_credit_text_and_link_unchanged(self):
        """R8.5: the viewer's credit keeps its text, its link and its open-link call."""
        from ai_anthro_toolkit.network.viewer import build_app_html

        html = build_app_html()
        self.assertIn(
            '<div id="credit"><a id="credit-link" href="https://www.mattartz.me" target="_blank" '
            'rel="noopener">AI Anthropology Toolkit by Matt Artz</a></div>',
            html,
        )
        self.assertIn('request("ui/open-link", { url: "https://www.mattartz.me" })', html)


if __name__ == "__main__":
    unittest.main()
