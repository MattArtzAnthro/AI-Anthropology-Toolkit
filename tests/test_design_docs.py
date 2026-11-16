"""The design system's derived files stay in step with its tokens.

src/ai_anthro_toolkit/design/tokens.json is the source; design/brand-spec.json
and design/brand-guide.html are built from it by scripts/build_design_docs.py.
"""

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

import tomllib

from scripts import build_design_docs as build

REPO = Path(__file__).resolve().parent.parent


def load_tokens() -> dict:
    return json.loads(build.TOKENS.read_text(encoding="utf-8"))


class TestContrastGate(unittest.TestCase):
    def test_contrast_matches_known_wcag_values(self):
        self.assertAlmostEqual(build.contrast("#000000", "#ffffff"), 21.0, places=2)
        self.assertAlmostEqual(build.contrast("#767676", "#ffffff"), 4.54, places=2)
        self.assertAlmostEqual(build.contrast("#ffffff", "#ffffff"), 1.0, places=2)

    def test_every_pairing_passes_in_both_themes(self):
        rows = build.check_contrast(load_tokens())
        self.assertEqual(len(rows), 2 * len(build.PAIRINGS))
        self.assertEqual({r["theme"] for r in rows}, {"light", "dark"})

    def test_gate_refuses_a_failing_text_pair(self):
        tokens = copy.deepcopy(load_tokens())
        for tok in tokens["color"]["tokens"]:
            if tok["name"] == "ink-muted":
                tok["value"]["dark"] = "#3a4452"  # too dark on the dark surface
        with self.assertRaisesRegex(ValueError, r"ink-muted on surface \(dark\)"):
            build.check_contrast(tokens)

    def test_gate_refuses_a_failing_control_border(self):
        tokens = copy.deepcopy(load_tokens())
        for tok in tokens["color"]["tokens"]:
            if tok["name"] == "line-strong":
                tok["value"]["light"] = "#8090a3"  # the value Harbor started with: 2.8:1 on paper
        with self.assertRaisesRegex(ValueError, r"line-strong on paper \(light\) is 2\.\d\d:1, needs 3\.0:1"):
            build.check_contrast(tokens)

    def test_alias_resolves_to_its_target(self):
        pal = build.palettes(load_tokens())
        for theme in ("light", "dark"):
            self.assertEqual(pal[theme]["focus"], pal[theme]["action"])


class TestCommittedFilesAreCurrent(unittest.TestCase):
    def test_brand_spec_matches_tokens(self):
        self.assertEqual(build.SPEC.read_text(encoding="utf-8"), build.spec_text(load_tokens()),
                         "design/brand-spec.json is stale; run scripts/build_design_docs.py")

    def test_check_flag_reports_staleness(self):
        self.assertEqual(build.main(["--check"]), 0)

    def test_spec_carries_every_token_in_both_themes(self):
        spec = json.loads(build.SPEC.read_text(encoding="utf-8"))
        pal = build.palettes(load_tokens())
        self.assertEqual(set(spec["colors"]["tokens"]), set(pal["light"]))
        for name, entry in spec["colors"]["tokens"].items():
            self.assertEqual(entry["hex"], pal["light"][name])
            self.assertEqual(entry["dark"]["hex"], pal["dark"][name])

    def test_brand_guide_shows_every_colour_and_has_no_placeholders(self):
        guide = build.GUIDE.read_text(encoding="utf-8")
        self.assertNotIn("{{", guide)
        pal = build.palettes(load_tokens())
        for theme in ("light", "dark"):
            for name, value in pal[theme].items():
                self.assertIn(value, guide, f"{name} ({theme}) {value} missing from brand-guide.html")
        self.assertIn(f"Version {build.SPEC_VERSION}", guide)


class TestRenderGuide(unittest.TestCase):
    def test_fills_placeholders(self):
        self.assertEqual(build.render_guide("<p>{{a}}</p>", {"a": "x"}), "<p>x</p>")

    def test_refuses_a_placeholder_with_no_value(self):
        with self.assertRaisesRegex(ValueError, "brand_name"):
            build.render_guide("<h1>{{brand_name}}</h1>", {})

    def test_every_guide_table_scrolls_inside_its_own_box(self):
        # The six-column button table is wider than a phone; unwrapped, it
        # widens the whole page.
        guide = build.GUIDE.read_text(encoding="utf-8")
        tables = guide.count('<table class="usage-table">')
        self.assertGreater(tables, 0)
        self.assertEqual(guide.count('<div class="table-scroll"><table class="usage-table">'), tables)
        self.assertRegex(guide, r"\.table-scroll\s*{\s*overflow-x:\s*auto")

    def test_fonts_href_requires_the_import_line(self):
        with self.assertRaisesRegex(ValueError, "@import"):
            build._fonts_href("body { color: red; }")


def _in_a_venv(path: Path, root: Path) -> bool:
    """Whether ``path`` sits inside a virtual environment (a folder holding pyvenv.cfg)."""
    return any((parent / "pyvenv.cfg").is_file() for parent in path.parents if parent != root and root in parent.parents)


def _stylesheets(root: Path) -> list[Path]:
    """Every bundle.css under ``root`` except installed copies and build output."""
    return [p for p in root.rglob("bundle.css")
            if not _in_a_venv(p, root) and "build" not in p.relative_to(root).parts]


class TestPackaging(unittest.TestCase):
    def test_tokens_and_stylesheet_ship_as_package_data(self):
        data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        shipped = data["tool"]["setuptools"]["package-data"]["ai_anthro_toolkit.design"]
        self.assertEqual(sorted(shipped), ["bundle.css", "tokens.json"])
        for name in shipped:
            self.assertTrue((build.TOKENS.parent / name).is_file(), name)

    def test_design_folder_stays_out_of_the_sdist(self):
        self.assertIn("prune design", (REPO / "MANIFEST.in").read_text(encoding="utf-8").splitlines())

    def test_stylesheet_exists_once(self):
        self.assertEqual(_stylesheets(REPO), [build.BUNDLE], "bundle.css must live only in the package")

    def test_a_stray_stylesheet_is_found_and_an_installed_one_is_not(self):
        """The release script installs the package into a venv inside the repository; its
        copy is an install, not a second source. A copy anywhere else is found."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in ("src/pkg/bundle.css", "docs/bundle.css", ".release-venv/lib/site-packages/pkg/bundle.css",
                        "build/lib/pkg/bundle.css"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text("", encoding="utf-8")
            (root / ".release-venv" / "pyvenv.cfg").write_text("", encoding="utf-8")
            self.assertEqual(sorted(_stylesheets(root)), [root / "docs/bundle.css", root / "src/pkg/bundle.css"])

    def test_no_local_paths_in_design_files(self):
        for path in [*(REPO / "design").rglob("*"), build.TOKENS, build.BUNDLE]:
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"/Users/|/private/tmp|/home/\w", text), path)


if __name__ == "__main__":
    unittest.main()
