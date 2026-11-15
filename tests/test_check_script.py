"""scripts/check.sh finds its tools when run from a linked worktree.

The global pre-push hook runs the gate on each pushed commit in a throwaway
worktree, which has no .venv of its own; the gate then uses the main
checkout's. Each test builds a scratch repository holding only check.sh and
a stand-in python that answers the gate's tool check.
"""

import os
import shutil
import subprocess  # nosec B404 - runs git and the repository's own check.sh
import tempfile
import unittest
from pathlib import Path

CHECK_SH = Path(__file__).resolve().parents[1] / "scripts" / "check.sh"
GIT = shutil.which("git") or ""
# The scratch repositories ignore the user's and the system's git config, and so their hooks.
_ISOLATED = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def _env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return {**env, **_ISOLATED}


def _git(cwd: Path, *args: str) -> None:
    subprocess.run([GIT, *args], cwd=cwd, env=_env(), check=True, capture_output=True)  # nosec B603


@unittest.skipUnless(GIT, "git is not installed")
class TestGateFromLinkedWorktree(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.main = self.tmp / "main"
        (self.main / "scripts").mkdir(parents=True)
        shutil.copy(CHECK_SH, self.main / "scripts" / "check.sh")
        _git(self.main, "init", "-q")
        _git(self.main, "add", "scripts/check.sh")
        _git(self.main, "-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-qm", "gate")
        self.linked = self.tmp / "linked"
        _git(self.main, "worktree", "add", "--detach", "-q", str(self.linked), "HEAD")

    def _stub_python(self) -> Path:
        """A .venv/bin/python in the main checkout that accepts any command."""
        python = self.main / ".venv" / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.write_text("#!/bin/sh\nexit 0\n")
        python.chmod(0o755)
        return python

    def _gate_python(self, where: Path) -> subprocess.CompletedProcess:
        env = {**_env(), "CHECK_SH_PRINT_PYTHON": "1"}
        return subprocess.run(  # nosec B603
            [str(where / "scripts" / "check.sh")], cwd=where, env=env, capture_output=True, text=True
        )

    def test_linked_worktree_uses_the_main_checkouts_venv(self):
        python = self._stub_python()
        result = self._gate_python(self.linked)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), python.resolve())

    def test_main_checkout_uses_its_own_venv(self):
        self._stub_python()
        result = self._gate_python(self.main)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), ".venv/bin/python")

    def test_no_venv_anywhere_stops_the_gate(self):
        result = self._gate_python(self.linked)
        self.assertEqual(result.returncode, 2)
        self.assertIn("lacks a gate tool", result.stderr)


if __name__ == "__main__":
    unittest.main()
