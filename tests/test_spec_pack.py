"""Gate integrity: a spec pack must be complete, and it must have been read.

The tool-building skill refuses to write code before a specification is
ratified. That refusal is only as good as the definition of "ratifiable", so
both conditions are mechanical here rather than left to good intentions.

Completeness catches an underspecified pack. The reading check catches a pack
that could have been written without opening the repository, which is recitation
rather than reading, and which the skill's own text concedes it can only
partly detect.

    python3 -m unittest tests.test_spec_pack -v
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "spec_packs"
TEMPLATE = (REPO / "skills" / "tool-building" / "references"
            / "spec-pack-template.md")

# The order matters and is asserted: a researcher reads these top to bottom,
# and the load-bearing items come first on purpose.
REQUIRED_HEADINGS = [
    "Outcome",
    "Scope in",
    "Scope out",
    "Constraints",
    "Prior decisions",
    "Likely files and interfaces",
    "Verification mode",
    "Verification",
    "Acceptance examples",
    "Open questions",
]

VALID_MODES = {"record-checkable", "interpretation-dependent"}


def _sections(text):
    """Split a SPEC.md into {heading: body} for level-2 headings."""
    parts = re.split(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1]
            for i in range(1, len(parts) - 1, 2)}


def check_spec_pack(text):
    """Return the reasons this pack is not ready for implementation."""
    problems = []
    sections = _sections(text)

    for heading in REQUIRED_HEADINGS:
        if heading not in sections:
            problems.append(f"missing section: {heading}")

    def body(name):
        return sections.get(name, "").strip()

    for name in ("Scope out", "Verification"):
        if name in sections and not body(name):
            problems.append(f"section is empty: {name}")

    mode = body("Verification mode").lower()
    declared = {m for m in VALID_MODES if m in mode}
    if len(declared) != 1:
        problems.append(
            f"verification mode must declare exactly one of {sorted(VALID_MODES)}")
    elif declared == {"interpretation-dependent"}:
        if re.search(r"pass/fail|passes or fails|must pass",
                     body("Acceptance examples"), re.IGNORECASE):
            problems.append(
                "interpretation-dependent artifacts may not claim pass/fail")

    if re.search(r"^\s*[-*]\s*critical", body("Open questions"),
                 re.IGNORECASE | re.MULTILINE):
        problems.append("unresolved critical open question")

    return problems


def check_reading(text, project_root):
    """Return signs this pack was recited rather than read.

    Recitation leaves fingerprints: paths that do not exist, no runnable
    verification, and a set of conventions referred to but never quoted. This
    catches the lazy case only. A specification that reads enough of the project
    to satisfy these three and recites the rest is not detectable here, and the
    skill's own text says so rather than implying the problem is solved.
    """
    problems = []
    sections = _sections(text)
    root = Path(project_root)

    paths = re.findall(r"`([^`\s]+\.[A-Za-z0-9_]+)`",
                       sections.get("Likely files and interfaces", ""))
    if not paths:
        problems.append("no file paths named in Likely files and interfaces")
    for path in paths:
        if not (root / path).exists():
            problems.append(f"named path does not exist: {path}")

    commands = re.findall(r"^\s*[-*]\s*`([^`]+)`",
                          sections.get("Verification", ""), re.MULTILINE)
    if not commands:
        problems.append("no verification commands named in backticks")

    if not re.search(r"[\"“][^\"”]{12,}[\"”]",
                     sections.get("Prior decisions", "")):
        problems.append(
            "Prior decisions quotes no specific convention from the constitution")

    return problems


class _Fixtures(unittest.TestCase):
    def load(self, name):
        return (FIXTURES / name / "SPEC.md").read_text(encoding="utf-8")


class TestCompleteness(_Fixtures):
    """Each fixture differs from `complete` in exactly one respect, so a
    failure here names one rule rather than a general malaise."""

    def test_complete_pack_is_ready(self):
        self.assertEqual([], check_spec_pack(self.load("complete")))

    def test_empty_scope_out_is_rejected(self):
        self.assertIn("section is empty: Scope out",
                      check_spec_pack(self.load("missing_scope_out")))

    def test_empty_verification_is_rejected(self):
        self.assertIn("section is empty: Verification",
                      check_spec_pack(self.load("missing_verification")))

    def test_undeclared_mode_is_rejected(self):
        problems = check_spec_pack(self.load("no_mode"))
        self.assertTrue(any("verification mode" in p for p in problems),
                        f"expected a mode complaint, got {problems}")

    def test_critical_open_question_blocks_ratification(self):
        self.assertIn("unresolved critical open question",
                      check_spec_pack(self.load("critical_open_question")))

    def test_interpretive_pack_may_not_claim_pass_fail(self):
        self.assertIn(
            "interpretation-dependent artifacts may not claim pass/fail",
            check_spec_pack(self.load("interpretive_claims_pass_fail")))


class TestReadingCheck(_Fixtures):
    """A pack can be well-formed and never have touched the project.

    The `recited` fixture is the whole point of this class: it passes every
    completeness rule and fails on reading, which is why the reading check is a
    separate precondition rather than another completeness item.
    """

    def test_a_pack_written_against_the_project_passes(self):
        self.assertEqual([], check_reading(self.load("complete"), REPO))

    def test_recited_pack_is_structurally_complete(self):
        self.assertEqual([], check_spec_pack(self.load("recited")),
                         "the recited fixture must pass completeness, or it is "
                         "not testing what it exists to test")

    def test_recited_pack_fails_on_reading(self):
        problems = check_reading(self.load("recited"), REPO)
        self.assertTrue(any("does not exist" in p for p in problems),
                        f"expected a nonexistent-path complaint, got {problems}")
        self.assertIn(
            "Prior decisions quotes no specific convention from the constitution",
            problems)

    def test_the_complete_fixture_names_paths_that_really_exist(self):
        """Guards the fixture itself. If someone moves one of these files, the
        reading check starts reporting a defect that is not in the pack.

        Scoped to the one section that holds paths. A first version scanned every
        backticked line in the file and flagged a Verification command, because
        `wc -w skills/.../SKILL.md` contains a path without being one.
        """
        listed = _sections(self.load("complete")).get(
            "Likely files and interfaces", "")
        paths = re.findall(r"^\s*[-*]\s*`([^`]+)`\s*$", listed, re.MULTILINE)
        self.assertTrue(paths, "fixture lists no paths, so it cannot pass the "
                               "reading check for the right reason")
        for path in paths:
            self.assertTrue((REPO / path).exists(),
                            f"fixture names {path}, which is gone")


class TestTemplateMatchesTheChecks(unittest.TestCase):
    """The template is what a researcher sees; the checks follow it, not the
    reverse. If these disagree, fix the template only when the check is right."""

    def test_template_exists(self):
        self.assertTrue(TEMPLATE.is_file(),
                        f"missing {TEMPLATE.relative_to(REPO)}")

    def test_template_carries_every_required_heading(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        for heading in REQUIRED_HEADINGS:
            self.assertIn(f"## {heading}", text,
                          f"spec-pack-template.md lacks '## {heading}'")

    def test_template_headings_are_in_order(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        positions = [text.index(f"## {h}") for h in REQUIRED_HEADINGS]
        self.assertEqual(positions, sorted(positions),
                         "template headings are out of order; a researcher "
                         "reads these top to bottom and the load-bearing "
                         "items come first on purpose")

    def test_template_requires_the_red_run(self):
        # The decision record must carry the red run: checks listed with
        # their observed first failure, before implementation. Without this
        # section the checks-before-code order is unrecorded and therefore
        # unenforceable after the fact.
        text = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("## The red run", text,
                      "spec-pack-template.md lacks the red-run section")
        self.assertIn("first failure", text,
                      "red-run section does not require the observed "
                      "first failure")

    def test_template_names_both_verification_modes(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        for mode in sorted(VALID_MODES):
            self.assertIn(mode, text,
                          f"template never names the '{mode}' mode, so a "
                          f"researcher cannot declare it")


if __name__ == "__main__":
    unittest.main()
