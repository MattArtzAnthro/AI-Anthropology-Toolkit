"""No code, notebook or skill may use a personal email address as an API contact.

User-Agent strings and ``mailto=`` parameters carry a contact address. The
datasource clients take ``mailto`` from the caller and default to none;
notebooks that set one use ``noreply@example.org``. Citing the address
in documentation or metadata is fine. Stdlib only — run with:

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

# A personal address is allowed as a citation (README, LICENSE, author metadata) and
# refused as an API contact: a request marker on the line or the two lines before it.
LINKS = re.compile(r"\]\(mailto:[^)\s]*\)|<mailto:[^>\s]*>|href=[\"']mailto:[^\"']*[\"']",
                   re.IGNORECASE)
MARK_ANYCASE = re.compile(r"mailto|user[-_ ]?agent|polite|contact_email|user_agent_contact"
                          r"|--contact|headers\s*=|params\s*=", re.IGNORECASE)
MARK_CONST = re.compile(r"\bUA\b|\b[A-Z_]*(?:EMAIL|MAILTO|CONTACT)[A-Z_]*\s*[:=]")


def contact_lines(lines):
    """1-based numbers of lines that use a personal address as a request contact."""
    hits = []
    for i, line in enumerate(lines):
        if PERSONAL.search(LINKS.sub("", line)):
            context = LINKS.sub("", "\n".join(lines[max(0, i - 2):i + 1]))
            if MARK_ANYCASE.search(context) or MARK_CONST.search(context):
                hits.append(i + 1)
    return hits


def scanned_files(root: Path = REPO) -> list[Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and p.suffix in SUFFIXES and not SKIP_DIRS & set(p.parts)
    )


def personal_hits(paths, root: Path = REPO) -> list[str]:
    hits = []
    for p in paths:
        lines = p.read_text(errors="ignore").splitlines()
        hits += [f"{p.relative_to(root)}:{n}" for n in contact_lines(lines)]
    return hits


class NoPersonalContact(unittest.TestCase):
    def test_no_personal_address_used_as_a_contact(self):
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

    def test_citing_the_address_is_allowed(self):
        domain = "mattartz" + ".me"
        with tempfile.TemporaryDirectory() as d:
            readme = Path(d) / "README.md"
            readme.write_text(
                f"Artz, Matt. 2025. Toolkit. Contact research@{domain}.\n"
                f"**Contact:** [research@{domain}](mailto:research@{domain})\n")
            self.assertEqual(personal_hits([readme], Path(d)), [])

    def test_a_contact_continued_onto_the_next_line_is_caught(self):
        domain = "mattartz" + ".me"
        lines = ['UA = ("tool/0.1 "', f'      "accounts@{domain})")']
        self.assertEqual(contact_lines(lines), [2])


if __name__ == "__main__":
    unittest.main()
