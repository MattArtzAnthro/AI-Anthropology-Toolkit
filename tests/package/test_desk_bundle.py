"""The desk's bundled renderer: what it is built from, and its size (R7.11)."""

import json
import re
import unittest

from tests.package.test_desk_a2ui import APP, DESK, _node, _node_or_skip

BUNDLE = APP / "dist" / "desk-app.js"
LOCK = APP / "package-lock.json"
VENDORED = DESK / "VENDORED.md"
BUDGET = 500_000  # bytes, minified (design.md: the budget catches a jump, not the runtime's floor)


def vendored_bundle() -> dict[str, tuple[str, str]]:
    """The bundle's packages as VENDORED.md lists them: {name: (version, licence)}."""
    text = VENDORED.read_text(encoding="utf-8")
    section = text.split("## The bundle", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\| `([^`]+)` \| ([^|]+?) \| ([^|]+?) \|", section, re.M)
    return {name: (version, licence) for name, version, licence in rows}


def locked() -> dict[str, tuple[str, str]]:
    """The packages the lockfile installs for the bundle (not the build's own tools)."""
    packages = json.loads(LOCK.read_text(encoding="utf-8"))["packages"]
    return {path.split("node_modules/")[-1]: (info["version"], info.get("license", ""))
            for path, info in packages.items() if path and not info.get("dev")}


class TestBundle(unittest.TestCase):
    def test_r7_11_bundle_versions_match_vendored_md(self):
        """Each package VENDORED.md lists is the version and licence the lockfile installs."""
        listed, installed = vendored_bundle(), locked()
        self.assertTrue(listed)
        for name, entry in listed.items():
            with self.subTest(name):
                self.assertEqual(entry, installed.get(name))

    def test_r7_11_vendored_md_lists_every_package_in_the_bundle(self):
        """What esbuild puts in the bundle is exactly what VENDORED.md lists."""
        node = _node_or_skip(self)
        built = json.loads(_node(node, ["scripts/bundle-check.mjs"]))
        self.assertEqual(set(built["packages"]), set(vendored_bundle()))

    def test_r7_11_the_committed_bundle_is_built_from_its_sources(self):
        node = _node_or_skip(self)
        built = json.loads(_node(node, ["scripts/bundle-check.mjs"]))
        self.assertTrue(built["matches"], "dist/desk-app.js differs from a build of src/: run npm run build in desk/app")

    def test_r7_11_the_bundle_fits_its_budget(self):
        size = BUNDLE.stat().st_size
        self.assertLessEqual(size, BUDGET, f"the bundle is {size} bytes, over its {BUDGET}-byte budget")

    def test_vendored_md_names_the_accepted_zod_advisory(self):
        text = VENDORED.read_text(encoding="utf-8")
        self.assertIn("GHSA-mrhx-c7xc-m3w5", text)
        self.assertRegex(text, r"zod` \| 3\.25\.76")


if __name__ == "__main__":
    unittest.main()
