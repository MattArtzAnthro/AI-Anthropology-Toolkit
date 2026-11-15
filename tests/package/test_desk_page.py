"""The desk page shell: one self-contained file for a standalone desk, and the empty
shell an MCP App loads."""

import json
import re
import tempfile
import unittest
from importlib import resources
from pathlib import Path, PurePosixPath
from unittest import mock

from ai_anthro_toolkit import __version__, brand, design
from ai_anthro_toolkit.desk import a2ui, page
from tests.package.desk_helpers import codebook_desk, rulings_desk

BUNDLE = Path(page.__file__).parent / "app" / "dist" / "desk-app.js"
HOSTILE = "</script><script>alert(1)</script><!-- & -->"


def data_block(html):
    found = re.findall(r'<script type="application/json" id="desk-data">(.*?)</script>', html, re.S)
    return found


def styles(html):
    return "\n".join(re.findall(r"<style>(.*?)</style>", html, re.S))


def without_footer(html):
    return re.sub(r'<footer class="aat-byline">.*?</footer>', "", html, flags=re.S)


class TestSelfContained(unittest.TestCase):
    def setUp(self):
        desk = codebook_desk()
        desk["cards"][0] = dict(desk["cards"][0], definition=HOSTILE)
        self.desk = desk
        self.html = page.render_page(desk)

    def test_r1_5_page_has_no_external_script(self):
        self.assertNotRegex(self.html, r"(?i)<script[^>]*\ssrc\s*=")
        self.assertNotRegex(self.html, r"(?i)<link[^>]*rel=\"?(?:modulepreload|preload)")
        bundle = BUNDLE.read_text(encoding="utf-8")
        self.assertIn(bundle.replace("</", "<\\/"), self.html)
        # Two scripts, each closed once: nothing in the data can close one early.
        self.assertEqual(len(re.findall(r"(?i)</script", self.html)), 2)
        self.assertNotIn("<!--", self.html)
        [block] = data_block(self.html)
        self.assertEqual(json.loads(block), {"desk_id": self.desk["desk_id"], "stage": "codebook", "messages": a2ui.surface(self.desk)})
        self.assertIn(HOSTILE, json.dumps(json.loads(block)))
        self.assertEqual([c for c in "<>&" if c in block], [])

    def test_a_bundle_that_could_break_out_of_its_script_is_refused(self):
        for bad in ("x<!--y", "a<script>b", "a<SCRIPT b"):
            with self.subTest(bad), mock.patch.object(page, "_bundle", return_value=bad), \
                    self.assertRaisesRegex(RuntimeError, "cannot be inlined"):
                page.render_page(self.desk)

    def test_r1_6_page_has_no_build_machine_path(self):
        with tempfile.TemporaryDirectory() as root:
            desk = rulings_desk(desk_id="desk-9f8e7d6c")
            html = page.render_page(desk)
            for path in (str(Path.home()), root, str(Path(page.__file__).parent), str(Path(__file__).parents[2])):
                self.assertNotIn(path, html)
        self.assertNotRegex(self.html, r"/Users/[A-Za-z]|/home/[A-Za-z]|[A-Z]:\\\\Users|file://")

    def test_r8_6_every_colour_comes_from_tokens(self):
        css = styles(self.html)
        palette = {
            value.lower()
            for token in design.tokens()["color"]["tokens"] if isinstance(token["value"], dict)
            for value in token["value"].values()
        }
        hexes = {h.lower() for h in re.findall(r"#[0-9a-fA-F]{3,8}\b", css)}
        self.assertTrue(hexes)
        self.assertLessEqual(hexes, palette)
        # A shadow may write a token colour as rgb() with alpha, as bundle.css does.
        for r, g, b in re.findall(r"rgba?\(\s*(\d+)[ ,]+(\d+)[ ,]+(\d+)", css):
            self.assertIn(f"#{int(r):02x}{int(g):02x}{int(b):02x}", palette)
        self.assertNotRegex(css, r"(?i)\b(?:hsla?|hwb|lab|lch|oklab|oklch)\(")
        for part in (design.tokens_css(), design.a2ui_css(), design.stylesheet(fonts=False)):
            self.assertIn(part.strip(), css)
        self.assertIn('[data-theme="dark"]', css)
        self.assertIn("--a2ui-color-primary: var(--action);", css)

    def test_the_fonts_import_opens_the_stylesheet(self):
        """An @import after any other rule is ignored, and the page falls back to system fonts."""
        first = re.search(r"<style>(.*?)</style>", self.html, re.S).group(1)
        self.assertTrue(first.startswith(f'@import url("{design.FONTS_URL}");'))
        self.assertEqual(styles(self.html).count("@import"), 1)

    def test_r8_7_title_in_header_author_only_in_colophon(self):
        desk = codebook_desk(title="Garden <cooperative> study")
        html = page.render_page(desk)
        header = re.search(r"<header.*?</header>", html, re.S).group(0)
        self.assertIn('<p class="aat-desk__kind" id="desk-kind">Codebook desk</p>', header)
        self.assertIn('<h1 id="desk-title">Garden &lt;cooperative&gt; study</h1>', header)
        self.assertIn("<title>Garden &lt;cooperative&gt; study · Codebook desk</title>", html)
        self.assertNotIn(brand.AUTHOR, without_footer(html))
        self.assertEqual(html.count(brand.byline_html(__version__, full=True)), 1)

    def test_an_untitled_desk_is_headed_by_its_kind(self):
        self.assertIn("<title>Rulings desk</title>", page.render_page(rulings_desk(title="")))
        header = re.search(r"<header.*?</header>", page.render_page(rulings_desk(title="")), re.S).group(0)
        self.assertIn('<p class="aat-desk__kind" id="desk-kind"></p>\n<h1 id="desk-title">Rulings desk</h1>', header)

    def test_r8_3_the_page_ends_with_the_colophon_naming_the_version(self):
        visible = self.html.split("<body>", 1)[1].split("<script", 1)[0]
        before, after = visible.split(brand.byline_html(__version__, full=True))
        self.assertEqual(after.strip(), "</div>")  # nothing follows it on the page
        self.assertIn('<main id="desk"></main>', before)
        self.assertIn(f"v{__version__}", brand.byline_html(__version__, full=True))


class TestShipped(unittest.TestCase):
    def test_the_template_and_bundle_ship_as_package_data(self):
        root = resources.files("ai_anthro_toolkit.desk")
        for name in ("template.html", "app/dist/desk-app.js"):
            self.assertTrue(root.joinpath(name).is_file(), name)
        try:
            import tomllib
        except ImportError:  # pragma: no cover - Python 3.10
            self.skipTest("tomllib needs Python 3.11")
        repo = Path(__file__).parents[2]
        globs = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["setuptools"]["package-data"]["ai_anthro_toolkit.desk"]
        for name in ("template.html", "app/dist/desk-app.js"):
            with self.subTest(name):
                self.assertTrue(any(PurePosixPath(name).match(g) for g in globs), f"{name} is not package data")
        # Only the built bundle ships from app/, not its sources or node_modules.
        self.assertEqual([g for g in globs if g.startswith("app/")], ["app/dist/desk-app.js"])


class TestAppShell(unittest.TestCase):
    def test_the_shell_carries_the_page_but_no_desk(self):
        shell = page.app_shell()
        self.assertEqual(data_block(shell), [])
        self.assertIn(BUNDLE.read_text(encoding="utf-8").replace("</", "<\\/"), shell)
        self.assertNotRegex(shell, r"(?i)<script[^>]*\ssrc\s*=")
        self.assertIn(design.a2ui_css().strip(), styles(shell))
        self.assertEqual(shell.count(brand.byline_html(__version__, full=True)), 1)
        self.assertNotIn(brand.AUTHOR, without_footer(shell))
        self.assertIn('<header class="aat-desk__head">\n<p class="aat-desk__kind" id="desk-kind"></p>\n<h1 id="desk-title"></h1>\n</header>', shell)
        self.assertIn("<title>Ratification desk</title>", shell)
        self.assertIn("</footer>\n</div>\n<script>", shell)  # nothing between the page and its bundle
        self.assertNotIn(str(Path.home()), shell)

    def test_the_shell_does_not_change_between_desks(self):
        self.assertEqual(page.app_shell(), page.app_shell())


if __name__ == "__main__":
    unittest.main()
