"""Tests for the Codex mirror generator.

The generator's whole value is that the mirror stops being hand-maintained, so
the tests that matter are the ones proving it is safe to run unattended: it
must never touch the Codex-only router skill, and it must propagate deletions
rather than only additions. A generator that silently keeps a removed skill
alive would reintroduce the stale copy the mirror tests exist to catch.

`test_the_committed_mirror_is_current` is the one that runs in CI against real
content: it says the generator was run before the commit.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import sync_codex_mirror as mirror


class CommittedTree(unittest.TestCase):
    def test_the_committed_mirror_is_current(self):
        """The mirror in the repository matches its source right now.

        Equivalent to test_codex_plugin's byte-identity checks, phrased as the
        actionable question: was the generator run? The failure message names
        the command instead of the diff.
        """
        drift = mirror.differences(mirror.SOURCE_SKILLS, mirror.PLUGIN_SKILLS)
        self.assertEqual(
            drift, [],
            "the Codex mirror is stale; run: python3 -m scripts.sync_codex_mirror",
        )


class Generator(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.source = self.tmp / "skills"
        self.plugin = self.tmp / "plugin" / "skills"
        self.plugin.mkdir(parents=True)
        self._write(self.source / "alpha", "alpha from source")

    def _write(self, directory: Path, text: str, name: str = "SKILL.md"):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / name).write_text(text + "\n", encoding="utf-8")

    def test_the_codex_only_entry_skill_is_never_touched(self):
        """It is authored, not mirrored, and has no source counterpart.

        Deleting it would break the plugin's router, and it is the one
        directory the inventory test expects the source not to have.
        """
        entry = self.plugin / mirror.ENTRY_SKILL
        self._write(entry, "router, authored not mirrored")
        mirror.sync(self.source, self.plugin)
        self.assertTrue((entry / "SKILL.md").is_file())
        self.assertEqual(
            (entry / "SKILL.md").read_text(encoding="utf-8").strip(),
            "router, authored not mirrored",
        )

    def test_a_skill_removed_from_the_source_is_removed_from_the_mirror(self):
        self._write(self.plugin / "stale", "no longer in the source")
        mirror.sync(self.source, self.plugin)
        self.assertFalse((self.plugin / "stale").exists())

    def test_a_file_deleted_from_a_skill_does_not_survive_in_the_mirror(self):
        self._write(self.source / "alpha", "extra", name="extra.md")
        mirror.sync(self.source, self.plugin)
        self.assertTrue((self.plugin / "alpha" / "extra.md").is_file())

        (self.source / "alpha" / "extra.md").unlink()
        mirror.sync(self.source, self.plugin)
        self.assertFalse((self.plugin / "alpha" / "extra.md").exists())

    def test_content_drift_is_reported_and_then_repaired(self):
        mirror.sync(self.source, self.plugin)
        self.assertEqual(mirror.differences(self.source, self.plugin), [])

        (self.plugin / "alpha" / "SKILL.md").write_text("edited\n", encoding="utf-8")
        drift = mirror.differences(self.source, self.plugin)
        self.assertIn("content differs: skills/alpha/SKILL.md", drift)

        mirror.sync(self.source, self.plugin)
        self.assertEqual(mirror.differences(self.source, self.plugin), [])

    def test_a_directory_without_a_skill_md_is_not_treated_as_a_skill(self):
        """Same rule as the mirror tests use, so the two cannot disagree."""
        (self.source / "references").mkdir()
        (self.source / "references" / "notes.md").write_text("x\n", encoding="utf-8")
        mirror.sync(self.source, self.plugin)
        self.assertFalse((self.plugin / "references").exists())


if __name__ == "__main__":
    unittest.main()
