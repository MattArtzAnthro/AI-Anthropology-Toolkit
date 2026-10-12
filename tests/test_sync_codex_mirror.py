"""Tests for the Codex mirror generator.

The generator's whole value is that the mirror stops being hand-maintained, so
the tests that matter are the ones proving it is safe to run unattended: it
must never touch the Codex-only router skill, and it must propagate deletions
rather than only additions. A generator that silently keeps a removed skill
alive would reintroduce the stale copy the mirror tests exist to catch.

`test_the_committed_mirror_is_current` is the one that runs in CI against real
content: it says the generator was run before the commit.
"""

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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


class CommandLine(unittest.TestCase):
    """`main()` against a throwaway repository, so nothing real is rewritten."""

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, ignore_errors=True)
        self.source = self.repo / "skills"
        self.plugin = self.repo / "plugins" / "ai-anthropology"
        (self.source / "alpha").mkdir(parents=True)
        (self.source / "alpha" / "SKILL.md").write_text("alpha\n", encoding="utf-8")
        (self.plugin / "skills").mkdir(parents=True)
        (self.repo / ".mcp.json").write_text('{"pin": "1.0.0"}\n', encoding="utf-8")
        for name, value in (("REPO", self.repo), ("SOURCE_SKILLS", self.source),
                            ("PLUGIN", self.plugin),
                            ("PLUGIN_SKILLS", self.plugin / "skills")):
            patcher = mock.patch.object(mirror, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = mirror.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_check_fails_on_drift_and_writes_nothing(self):
        code, _, err = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn("missing from the plugin: skills/alpha", err)
        self.assertIn("missing from the plugin: .mcp.json", err)
        self.assertFalse((self.plugin / "skills" / "alpha").exists())

    def test_sync_then_check_passes(self):
        code, out, _ = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("wrote skills/alpha", out)
        self.assertIn("wrote .mcp.json", out)
        self.assertEqual(self.run_main("--check")[0], 0)
        code, out, _ = self.run_main()
        self.assertIn("nothing written", out)

    def test_a_changed_pin_is_drift(self):
        self.run_main()
        (self.repo / ".mcp.json").write_text('{"pin": "1.0.1"}\n', encoding="utf-8")
        code, _, err = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn("content differs: .mcp.json", err)

    def test_a_missing_source_file_is_reported(self):
        self.run_main()
        (self.repo / ".mcp.json").unlink()
        code, _, err = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn("source file is missing: .mcp.json", err)

    def test_no_source_skills_is_an_error(self):
        shutil.rmtree(self.source)
        code, _, err = self.run_main("--check")
        self.assertEqual(code, 2)
        self.assertIn("no source skills", err)

    def test_unchanged_skills_are_not_rewritten(self):
        self.run_main()
        (self.source / "beta").mkdir()
        (self.source / "beta" / "SKILL.md").write_text("beta\n", encoding="utf-8")
        code, out, _ = self.run_main()
        self.assertIn("wrote skills/beta", out)
        self.assertNotIn("wrote skills/alpha", out)


if __name__ == "__main__":
    unittest.main()
