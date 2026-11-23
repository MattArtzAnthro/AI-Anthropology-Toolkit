"""The gate's `formal` stage can fail: formal/stamp.py --check refuses a model, script or
vectors.json that changed since the provers last passed on it, and passes on the committed copy."""

import shutil
import subprocess  # nosec B404 - runs the repository's own stamp script
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "formal"


def _check(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(root / "formal" / "stamp.py"), "--check", "--root", str(root)],
                          capture_output=True, text=True, check=False)  # nosec B603


class TestFormalStamp(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        shutil.copytree(FORMAL, self.root / "formal", ignore=shutil.ignore_patterns(".lake"))
        for line in (FORMAL / "modeled.txt").read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                target = self.root / line.strip()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("", encoding="utf-8")

    def test_the_committed_models_carry_a_current_stamp(self):
        self.assertEqual(_check(ROOT).returncode, 0, _check(ROOT).stdout + _check(ROOT).stderr)

    def test_a_changed_model_fails_the_stamp(self):
        model = self.root / "formal" / "AatModel" / "Submit.lean"
        model.write_text(model.read_text(encoding="utf-8") + "\n-- edited\n", encoding="utf-8")
        self.assertEqual(_check(self.root).returncode, 1)

    def test_changed_vectors_fail_the_stamp(self):
        vectors = self.root / "formal" / "vectors.json"
        vectors.write_text(vectors.read_text(encoding="utf-8").replace('"refused": true', '"refused": false', 1),
                           encoding="utf-8")
        self.assertEqual(_check(self.root).returncode, 1)

    def test_a_modeled_file_that_is_gone_fails_the_stamp(self):
        (self.root / "src" / "ai_anthro_toolkit" / "jobs.py").unlink()
        self.assertEqual(_check(self.root).returncode, 1)


if __name__ == "__main__":
    unittest.main()
