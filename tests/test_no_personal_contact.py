"""No code, notebook or skill may send a personal email address to a service.

User-Agent strings and ``mailto=`` parameters carry a contact address. The
datasource clients take ``mailto`` from the caller and default to none;
notebooks that set one use ``noreply@example.org``. Stdlib only — run with:

    python3 -m unittest tests/test_no_personal_contact.py -v
"""

import re
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Assembled so this file does not match its own scan.
PERSONAL = re.compile(r"[A-Za-z0-9._%+-]+@" + "mattartz" + r"\.me", re.IGNORECASE)
SUFFIXES = {".py", ".ipynb", ".sh", ".md", ".toml"}
SKIP_DIRS = {".git", ".venv", "__pycache__", "build", "dist"}


def scanned_files(root: Path = REPO) -> list[Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix in SUFFIXES and not SKIP_DIRS & set(p.parts)
    )


def personal_hits(paths, root: Path = REPO) -> list[str]:
    hits = []
    for p in paths:
        for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            if PERSONAL.search(line):
                hits.append(f"{p.relative_to(root)}:{n}")
    return hits


class NoPersonalContact(unittest.TestCase):
    def test_no_personal_address_in_code_notebooks_or_skills(self):
        self.assertEqual(personal_hits(scanned_files()), [])

    def test_the_scan_reaches_notebooks_source_and_skills(self):
        tops = {p.relative_to(REPO).parts[0] for p in scanned_files()}
        self.assertTrue({"notebooks", "src", "skills"} <= tops, tops)

    def test_the_scan_catches_a_planted_address(self):
        with tempfile.TemporaryDirectory() as d:
            nb = Path(d) / "notebooks" / "planted.ipynb"
            nb.parent.mkdir()
            nb.write_text('"mailto": "someone@' + "mattartz" + '.me"\n')
            self.assertEqual(personal_hits(scanned_files(Path(d)), Path(d)),
                             ["notebooks/planted.ipynb:1"])

    def test_the_contact_address_and_the_website_are_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            ok = Path(d) / "ok.py"
            ok.write_text("MAILTO = 'noreply@example.org'  # https://www.mattartz.me/\n")
            self.assertEqual(personal_hits([ok], Path(d)), [])


if __name__ == "__main__":
    unittest.main()
