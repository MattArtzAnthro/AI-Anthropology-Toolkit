"""Validation suite for the AI Anthropology Toolkit repository.

Checks structural conventions across the Claude Code plugin (skills, agents,
commands), the Jupyter notebooks, and repo-level documentation. Stdlib only —
run with:

    python3 -m unittest tests/test_repo.py -v
"""

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills"
AGENTS_DIR = REPO / "agents"
COMMANDS_DIR = REPO / "commands"
NOTEBOOKS_DIR = REPO / "notebooks"

# Current Anthropic model aliases. Dateless aliases only, so notebooks track
# model updates without breaking when dated snapshots retire.
ALLOWED_MODEL_IDS = {
    "claude-sonnet-5",
    "claude-haiku-4-5",
    "claude-opus-4-8",
}

VALID_AGENT_COLORS = {"blue", "cyan", "green", "yellow", "magenta", "red"}

# Tool names that may appear in an agent's `tools` or a command's
# `allowed-tools`. A typo silently disables the capability rather than
# erroring, so the vocabulary is closed on purpose.
KNOWN_TOOLS = {
    "Skill", "Read", "Write", "Edit", "Grep", "Glob", "Bash",
    "WebFetch", "WebSearch", "AskUserQuestion", "TodoWrite", "NotebookEdit",
}

SECRET_PATTERNS = [
    r"sk-ant-[A-Za-z0-9_-]{10,}",
    r"sk-[A-Za-z0-9]{40,}",
    r"AIza[0-9A-Za-z_-]{30,}",
    r"hf_[A-Za-z0-9]{30,}",
    r"ghp_[A-Za-z0-9]{30,}",
]


def parse_frontmatter(path):
    """Parse simple YAML frontmatter without pyyaml.

    Supports plain scalars, folded blocks (>), and one-level lists. Returns
    (dict, body_text).
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.index("\n---", 3)
    raw = text[3:end].strip("\n")
    body = text[end + 4:]
    fields = {}
    key = None
    folded = False
    for line in raw.splitlines():
        if line and not line[0].isspace() and ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            folded = value in (">", ">-", "|", "|-")
            fields[key] = "" if folded else value
        elif key is not None and line.strip():
            stripped = line.strip()
            # "- item" lines start a list only for plain (non-folded) fields;
            # inside a folded scalar they are literal text and must count
            # toward the field's length.
            if stripped.startswith("- ") and not folded:
                if not isinstance(fields[key], list):
                    fields[key] = []
                fields[key].append(stripped[2:].strip().strip('"'))
            elif folded or line[0].isspace():
                fields[key] = (fields[key] + " " + stripped).strip()
    return fields, body


def parse_tools_field(value):
    """Normalize a tools/allowed-tools field to a list of tool names."""
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.startswith("["):
        return [t.strip().strip('"').strip("'") for t in value[1:-1].split(",")]
    return [value] if value else []


def skill_dirs():
    return sorted(d for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").is_file())


def skill_names():
    return {d.name for d in skill_dirs()}


def agent_files():
    return sorted(AGENTS_DIR.glob("*.md"))


def command_files():
    return sorted(COMMANDS_DIR.glob("*.md"))


def notebook_files():
    return sorted(NOTEBOOKS_DIR.glob("*.ipynb"))



def _flat(path):
    """Skill text with line wrapping normalised away.

    A phrase that spans a line break is still present in the skill; an
    assertion that cannot see it is testing the wrapping, not the rule.
    """
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))

class TestSkills(unittest.TestCase):
    def test_skills_present(self):
        self.assertGreaterEqual(len(skill_dirs()), 16)
        self.assertIn("qualitative-analysis", skill_names())

    def test_frontmatter_name_matches_directory(self):
        for d in skill_dirs():
            fields, _ = parse_frontmatter(d / "SKILL.md")
            self.assertEqual(fields.get("name"), d.name, f"{d.name}/SKILL.md name mismatch")

    def test_description_within_spec_limit(self):
        for d in skill_dirs():
            fields, _ = parse_frontmatter(d / "SKILL.md")
            desc = fields.get("description", "")
            self.assertTrue(desc, f"{d.name}: missing description")
            self.assertLessEqual(
                len(desc), 1024,
                f"{d.name}: description is {len(desc)} chars (limit 1024)",
            )

    def test_skills_readme_lists_every_skill(self):
        """The catalog in skills/README.md had no enforcement and drifted.

        `rival-interpretations` was missing from it while every other
        catalog in the repo (commands/skills.md, README.md, CLAUDE.md) was
        current, because those three are checked and this one was not. A
        catalog nobody verifies is worse than no catalog: it reads as
        complete.
        """
        text = (SKILLS_DIR / "README.md").read_text(encoding="utf-8")
        missing = [s for s in sorted(skill_names())
                   if f"{s}/" not in text]
        self.assertFalse(
            missing, f"skills/README.md catalog missing: {missing}")

    def test_no_references_to_nonexistent_skills(self):
        """Any '<kebab-name> skill' mention must name a real skill."""
        known = skill_names()
        pattern = re.compile(r"`?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`?\s+skills?\b")
        for d in skill_dirs():
            text = (d / "SKILL.md").read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                name = match.group(1)
                self.assertIn(
                    name, known,
                    f"{d.name}/SKILL.md references nonexistent skill '{name}'",
                )

    def test_routing_clauses_name_real_skills(self):
        """A "Do NOT use ... (use other-skill)" clause must name a real skill.

        test_no_references_to_nonexistent_skills only sees the phrasing
        "`x-y` skill", so it cannot see the routing clauses, which say
        "(use x-y)" instead. That left 19 sibling references across 6
        descriptions unguarded: a rename or a typo would silently point a user
        at nothing, and the routing clause is where a wrong name does the most
        damage, because it is the instruction that sends them elsewhere.

        The "use" anchor is required rather than checking every kebab-case
        token: 28 tokens in these descriptions are hyphenated words rather than
        skill names, so a blanket check would report de-identification and
        co-occurrence as missing skills.
        """
        known = skill_names()
        pattern = re.compile(
            r"\buse\s+(?:the\s+)?`?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`?")
        for d in skill_dirs():
            fields, _ = parse_frontmatter(d / "SKILL.md")
            for name in pattern.findall(fields.get("description", "")):
                self.assertIn(
                    name, known,
                    f"{d.name}: routing clause sends the user to '{name}', "
                    f"which is not a skill in this library")

    def test_reference_files_all_mentioned(self):
        for d in skill_dirs():
            refs = d / "references"
            if not refs.is_dir():
                continue
            text = (d / "SKILL.md").read_text(encoding="utf-8")
            for ref in refs.glob("*.md"):
                self.assertIn(
                    ref.name, text,
                    f"{d.name}: references/{ref.name} never mentioned in SKILL.md",
                )

    def test_mentioned_reference_files_exist(self):
        for d in skill_dirs():
            text = (d / "SKILL.md").read_text(encoding="utf-8")
            for name in re.findall(r"references/([\w.-]+\.md)", text):
                self.assertTrue(
                    (d / "references" / name).is_file(),
                    f"{d.name}: SKILL.md mentions missing references/{name}",
                )

    def test_relative_markdown_links_resolve(self):
        md_files = [REPO / "README.md", REPO / "CLAUDE.md", SKILLS_DIR / "README.md"]
        md_files += list(SKILLS_DIR.glob("*/SKILL.md"))
        md_files += list(SKILLS_DIR.glob("*/references/*.md"))
        link = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        fence = re.compile(r"^```.*?^```", re.M | re.S)
        for f in md_files:
            prose = fence.sub("", f.read_text(encoding="utf-8"))
            for target in link.findall(prose):
                target = target.split("#")[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:")):
                    continue
                resolved = (f.parent / target).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"{f.relative_to(REPO)}: broken relative link -> {target}",
                )

    def test_design_md_exists_with_lens_registry(self):
        design = SKILLS_DIR / "DESIGN.md"
        self.assertTrue(design.is_file(), "skills/DESIGN.md is missing")
        text = design.read_text(encoding="utf-8")
        self.assertRegex(text, re.compile(r"analytical lens", re.I))
        # Must match the notebooks' actual label (STANCE_DEFINITIONS entry).
        self.assertIn("STS / Actor-Network", text)

    def test_no_stale_research_design_planning_references(self):
        for f in SKILLS_DIR.rglob("*.md"):
            self.assertNotIn(
                "research-design-planning",
                f.read_text(encoding="utf-8"),
                f"{f.relative_to(REPO)}: stale 'research-design-planning' reference",
            )

    def test_funder_references_carry_currency_disclaimer(self):
        for name in ("nsf-cultural-anthro.md", "wenner-gren.md", "fulbright.md"):
            f = SKILLS_DIR / "grant-proposal" / "references" / name
            text = f.read_text(encoding="utf-8").lower()
            self.assertTrue(
                "verify" in text and "current" in text,
                f"{name}: missing verify-against-current-guidelines disclaimer",
            )

    def test_grant_proposal_hard_requirements_hedged(self):
        text = (SKILLS_DIR / "grant-proposal" / "SKILL.md").read_text(encoding="utf-8")
        if "hard requirements" in text:
            self.assertRegex(
                text, re.compile(r"(verify|confirm)", re.I),
                "grant-proposal: 'hard requirements' claim lacks a verify/confirm hedge",
            )


FRICTION_DECLARATION_RE = re.compile(
    r"This skill adopts the Friction by Design conventions at Tier ([123])"
)
FRICTION_WILL_HEADING = "## What This Skill Will and Will Not Do"
FRICTION_WILL_NOT_LEAD = "**Will not do, under any setting.**"
FRICTION_WILL_DO_LEAD = "**Will do, on request.**"
FRICTION_DEPTH_HEADING = "## Calibrating the Depth"


def friction_tier_table():
    """Parse the Friction by Design adoption table in skills/DESIGN.md.

    Returns {skill_name: (tier, reason_cell)}.
    """
    text = (SKILLS_DIR / "DESIGN.md").read_text(encoding="utf-8")
    section = text.split("### Adoption tiers", 1)[1].split("\n## ", 1)[0]
    tiers = {}
    for line in section.splitlines():
        m = re.match(r"\|\s*([a-z][a-z0-9-]+)\s*\|\s*([123])\s*\|(.*)\|", line)
        if m:
            tiers[m.group(1)] = (int(m.group(2)), m.group(3).strip())
    return tiers


class TestFrictionConvention(unittest.TestCase):
    """The Friction by Design conventions (skills/DESIGN.md).

    These checks verify structural presence only. Whether a will-not list is
    specific to its skill or generic, whether friction sits where the risk
    is, and whether any of it is questioning rather than a form are
    judgments no check here touches — the same limit class as the
    specificity bar.
    """

    def test_working_principle_core_sentences_carried_verbatim(self):
        """The working principle's core sentences must not drift apart.

        Verbatim containment after whitespace normalization (the carriers
        wrap prose at different columns; DESIGN.md wraps them in its own
        convention framing, which is allowed — the sentences are not)."""
        core = ("Be adversarial toward your own output. Trust what survives "
                "an attempt to break it, and be most suspicious of what "
                "arrived easily.")
        carriers = [REPO / "CLAUDE.md", REPO / "AGENTS.md",
                    REPO / "GEMINI.md", SKILLS_DIR / "DESIGN.md"]
        def norm(s):
            # strip blockquote markers so DESIGN.md's quoted form counts,
            # then collapse all whitespace
            lines = [ln.lstrip().lstrip(">").lstrip() for ln in s.splitlines()]
            return " ".join(" ".join(lines).split())
        missing = [p.name for p in carriers
                   if norm(core) not in norm(p.read_text(encoding="utf-8"))]
        self.assertFalse(
            missing,
            "working principle core sentences missing or drifted in: "
            + ", ".join(missing),
        )

    def test_adoption_table_covers_every_skill_exactly(self):
        table = friction_tier_table()
        self.assertEqual(
            set(table), skill_names(),
            "DESIGN.md adoption table and skills/ directory disagree",
        )

    def test_declarations_match_the_table(self):
        table = friction_tier_table()
        for d in skill_dirs():
            body = (d / "SKILL.md").read_text(encoding="utf-8")
            m = FRICTION_DECLARATION_RE.search(body)
            if m:
                declared = int(m.group(1))
                self.assertIn(
                    declared, (1, 2),
                    f"{d.name}: Tier 3 is non-adoption and takes no declaration",
                )
                self.assertEqual(
                    declared, table[d.name][0],
                    f"{d.name}: declares Tier {declared} but DESIGN.md "
                    f"assigns Tier {table[d.name][0]}",
                )

    def test_declared_adopters_carry_required_sections(self):
        table = friction_tier_table()
        for d in skill_dirs():
            body = (d / "SKILL.md").read_text(encoding="utf-8")
            m = FRICTION_DECLARATION_RE.search(body)
            if not m:
                continue
            tier = int(m.group(1))
            for required in (
                FRICTION_WILL_HEADING,
                FRICTION_WILL_NOT_LEAD,
                FRICTION_WILL_DO_LEAD,
            ):
                self.assertIn(
                    required, body,
                    f"{d.name}: Tier {tier} adopter missing '{required}'",
                )
            if tier == 1 and "Variance:" not in table[d.name][1]:
                for required in (
                    FRICTION_DEPTH_HEADING,
                    "**Full pass.**",
                    "**Advisory pass.**",
                    # Canonical shared sentences: the trailing noun varies by
                    # audience (someone/the author), the rule may not.
                    "Default to asking. Do not infer the setting from how confident",
                    "use it and do not re-ask",
                ):
                    self.assertIn(
                        required, body,
                        f"{d.name}: Tier 1 adopter missing '{required}'",
                    )

    def test_tier_three_skills_do_not_carry_the_ceremony(self):
        table = friction_tier_table()
        for d in skill_dirs():
            if table[d.name][0] != 3:
                continue
            body = (d / "SKILL.md").read_text(encoding="utf-8")
            self.assertIsNone(
                FRICTION_DECLARATION_RE.search(body),
                f"{d.name}: Tier 3 must not carry an adoption declaration",
            )
            self.assertNotIn(
                FRICTION_DEPTH_HEADING, body,
                f"{d.name}: Tier 3 must not carry the depth ceremony",
            )

    def test_advisors_owning_tier_one_skills_carry_the_depth_setting(self):
        # The "once per engagement" rule needs a carrier: an agent whose
        # draw-on list includes a Tier 1 skill must say it carries the
        # depth setting, or three skills in one session each re-ask.
        table = friction_tier_table()
        tier_one = {n for n, (t, _r) in table.items() if t == 1}
        for f in agent_files():
            body = f.read_text(encoding="utf-8")
            m = re.search(
                r"\*\*Skills You Draw On:\*\*(.*?)(?:\n\*\*|\Z)", body, re.S
            )
            if not m:
                continue
            claimed = {n for n in tier_one if n in m.group(1)}
            if claimed:
                self.assertIn(
                    "depth setting", body,
                    f"{f.stem}: draws on Tier 1 skill(s) {sorted(claimed)} "
                    "but never mentions carrying the depth setting",
                )

    def test_agents_carry_the_session_parameters_convention(self):
        """Shared parameters need a carrier or they are shared on paper only.

        DESIGN.md declares six parameters so a project can move through the
        lifecycle without re-specifying its identity at each phase. Only the
        depth setting ever had a carrier; the rest were re-elicited by each
        skill in turn. An agent that orchestrates skills is the carrier, so
        an agent missing the convention silently reintroduces the re-asking
        this framework exists to stop.
        """
        for f in agent_files():
            body = f.read_text(encoding="utf-8")
            if "Skills You Draw On" not in body:
                continue
            self.assertIn(
                "Session Parameters", body,
                f"{f.stem}: orchestrates skills but carries no session-"
                "parameters convention, so every skill it invokes re-asks")
            self.assertIn(
                "Carrying the parameters", body,
                f"{f.stem}: session-parameters block does not point at the "
                "canonical convention in DESIGN.md")

    def test_design_md_defines_the_parameter_carrier(self):
        """The convention the agents point at has to exist and be specific."""
        text = (SKILLS_DIR / "DESIGN.md").read_text(encoding="utf-8")
        self.assertIn("### Carrying the parameters", text,
                      "DESIGN.md: parameter-carrier convention missing")
        section = text.split("### Carrying the parameters", 1)[1].split(
            "\n## ", 1)[0].lower()
        for required in ("questionnaire", "career stage", "depth setting"):
            self.assertIn(
                required, section,
                f"DESIGN.md carrier convention does not address '{required}'")

    def test_every_assigned_adopter_declares(self):
        # The reverse direction of test_declarations_match_the_table: a
        # Tier 1/2 assignment in DESIGN.md that no SKILL.md declares is a
        # convention nobody adopted.
        table = friction_tier_table()
        for name, (tier, _reason) in table.items():
            if tier == 3:
                continue
            body = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIsNotNone(
                FRICTION_DECLARATION_RE.search(body),
                f"{name}: assigned Tier {tier} in DESIGN.md but SKILL.md "
                "carries no adoption declaration",
            )

    def test_carriers_declare_tier_one(self):
        for name in ("tool-building", "paper-planning"):
            body = (SKILLS_DIR / name / "SKILL.md").read_text(encoding="utf-8")
            m = FRICTION_DECLARATION_RE.search(body)
            self.assertIsNotNone(m, f"{name}: missing adoption declaration")
            self.assertEqual("1", m.group(1), f"{name}: carrier must be Tier 1")

    # Stage 6 of tool-building writes the acceptance checks and asks the
    # researcher nothing. Surfacing the behaviors a specification left open
    # therefore belongs at Stage 4, before ratification: a commitment settled
    # after ratification is a change to a frozen specification. The three
    # tests below hold that placement, because it is the kind of ruling a
    # later edit undoes by accident.

    def _tool_building_stages(self):
        body = (SKILLS_DIR / "tool-building" / "SKILL.md").read_text(
            encoding="utf-8")
        marks = [(n, body.index(f"**Stage {n}.")) for n in ("4", "5", "6", "7")]
        return body, dict(marks)

    def test_unstated_commitments_surfaced_at_stage_four(self):
        body, at = self._tool_building_stages()
        where = body.index("references/unstated-commitments.md",
                           at["4"])
        self.assertLess(
            where, at["5"],
            "unstated-commitments must be read at Stage 4, before "
            "ratification — a commitment settled after ratification is a "
            "change to a frozen specification",
        )

    def test_stage_six_asks_the_researcher_nothing(self):
        body, at = self._tool_building_stages()
        stage_six = body[at["6"]:at["7"]]
        self.assertIn(
            "ask nothing of them", stage_six,
            "Stage 6 runs the check-writing mechanics without the "
            "researcher; losing this sentence loses the rule",
        )
        self.assertNotIn(
            "unstated-commitments", stage_six,
            "surfacing open commitments at Stage 6 would put a decision "
            "gate in the one stage built to have none",
        )

    def test_unstated_commitments_states_rather_than_asks(self):
        ref = (SKILLS_DIR / "tool-building" / "references"
               / "unstated-commitments.md").read_text(encoding="utf-8")
        self.assertIn(
            "State the commitment, not the question", ref,
            "the reference must keep the rule that a reconstruction can be "
            "wrong and a question cannot",
        )
        for mark in ("mirror", "surprise-capable"):
            self.assertIn(mark, ref, f"reference drops the {mark} mark")


class TestAgents(unittest.TestCase):
    def test_agents_present(self):
        names = {f.stem for f in agent_files()}
        self.assertGreaterEqual(len(names), 8)
        self.assertIn("analysis-advisor", names)

    def test_frontmatter_complete_and_valid(self):
        for f in agent_files():
            fields, _ = parse_frontmatter(f)
            self.assertEqual(fields.get("name"), f.stem, f"{f.name}: name/filename mismatch")
            self.assertTrue(fields.get("description"), f"{f.name}: missing description")
            self.assertEqual(fields.get("model"), "inherit", f"{f.name}: model must be inherit")
            self.assertIn(fields.get("color"), VALID_AGENT_COLORS, f"{f.name}: invalid color")

    def test_description_has_examples(self):
        for f in agent_files():
            fields, _ = parse_frontmatter(f)
            self.assertIn("<example>", fields.get("description", ""), f"{f.name}: no <example> blocks")

    def test_agent_tool_names_are_real(self):
        for f in agent_files():
            fields, _ = parse_frontmatter(f)
            for tool in parse_tools_field(fields.get("tools")):
                self.assertIn(tool, KNOWN_TOOLS,
                              f"{f.stem}: '{tool}' is not a known tool name")

    def test_write_capable_agents_can_also_read_and_run(self):
        """An agent that writes files but cannot read them is broken.

        tool-builder is the first agent here that produces files. Write
        without Read means it cannot inspect what it is editing, and without
        Bash it cannot run the gates it exists to run.
        """
        for f in agent_files():
            fields, _ = parse_frontmatter(f)
            tools = set(parse_tools_field(fields.get("tools")))
            if {"Write", "Edit"} & tools:
                self.assertIn("Read", tools,
                              f"{f.stem}: writes files but cannot Read them")
                self.assertIn("Bash", tools,
                              f"{f.stem}: writes files but cannot run checks")

    def test_agents_carry_skill_tool(self):
        """Agents orchestrate skills, so each must be able to invoke them."""
        for f in agent_files():
            fields, _ = parse_frontmatter(f)
            tools = parse_tools_field(fields.get("tools"))
            self.assertIn("Skill", tools, f"{f.name}: 'Skill' missing from tools")

    def test_agent_bodies_instruct_skill_invocation(self):
        for f in agent_files():
            _, body = parse_frontmatter(f)
            self.assertIn(
                "Skill tool", body,
                f"{f.name}: body never tells the agent to invoke skills via the Skill tool",
            )

    def test_agents_reference_real_skills(self):
        known = skill_names()
        pattern = re.compile(r"`?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`?\s+skills?\b")
        for f in agent_files():
            text = f.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                self.assertIn(
                    match.group(1), known,
                    f"{f.name}: references nonexistent skill '{match.group(1)}'",
                )

    def test_agent_boundary_cross_pointers(self):
        """Fuzzy-boundary agents must route their sibling's cases explicitly."""
        pairs = [
            ("research-design", "proposal-advisor"),
            ("proposal-advisor", "research-design"),
            ("writing-advisor", "dissemination-advisor"),
            ("dissemination-advisor", "writing-advisor"),
        ]
        for agent, sibling in pairs:
            fields, _ = parse_frontmatter(AGENTS_DIR / f"{agent}.md")
            self.assertIn(
                sibling, fields.get("description", ""),
                f"{agent}: description should route boundary cases to {sibling}",
            )

    def test_every_skill_owned_by_an_agent(self):
        owned = set()
        pattern = re.compile(r"\*\*`?([a-z0-9-]+)`?\*\*|`([a-z0-9-]+)`")
        for f in agent_files():
            text = f.read_text(encoding="utf-8")
            for a, b in pattern.findall(text):
                owned.add(a or b)
        missing = skill_names() - owned
        self.assertFalse(missing, f"skills not claimed by any agent: {sorted(missing)}")


class TestAllCommands(unittest.TestCase):
    """Structural checks every command must pass.

    TestCommand below is specific to new-project. These apply to all of them,
    because a command added without them is unvalidated: build-tool shipped
    with no structural coverage at all until this class existed.
    """

    def test_frontmatter_complete(self):
        for f in command_files():
            fields, body = parse_frontmatter(f)
            self.assertEqual(fields.get("name"), f.stem,
                             f"{f.name}: name/filename mismatch")
            self.assertTrue(fields.get("description"),
                            f"{f.name}: missing description")
            self.assertTrue(body.strip(), f"{f.name}: empty body")

    def test_declared_tools_include_skill(self):
        """A command that declares tools is dispatching work, so it needs Skill.

        Commands that declare no tools are display-only; `skills` prints a
        catalog from its own body and correctly asks for nothing. Whether a
        given command ought to declare tools at all is a judgment about what it
        is for, and no rule here can settle it, so the check applies only to
        commands that have already declared.
        """
        for f in command_files():
            fields, _ = parse_frontmatter(f)
            declared = parse_tools_field(fields.get("allowed-tools"))
            if not declared:
                continue
            self.assertIn("Skill", declared,
                          f"{f.stem}: declares tools but not Skill")

    def test_tool_names_are_real(self):
        for f in command_files():
            fields, _ = parse_frontmatter(f)
            for tool in parse_tools_field(fields.get("allowed-tools")):
                self.assertIn(tool, KNOWN_TOOLS,
                              f"{f.stem}: '{tool}' is not a known tool name")

    def test_references_real_skills(self):
        known = skill_names()
        pattern = re.compile(r"`?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`?\s+skills?\b")
        for f in command_files():
            _, body = parse_frontmatter(f)
            for match in pattern.finditer(body):
                self.assertIn(
                    match.group(1), known,
                    f"{f.stem} references nonexistent skill "
                    f"'{match.group(1)}'")


class TestCommand(unittest.TestCase):
    def setUp(self):
        self.path = COMMANDS_DIR / "new-project.md"
        self.fields, self.body = parse_frontmatter(self.path)

    def test_allowed_tools_include_skill(self):
        tools = parse_tools_field(self.fields.get("allowed-tools"))
        self.assertIn("Skill", tools, "new-project: Skill missing from allowed-tools")

    def test_asks_for_save_location(self):
        self.assertRegex(
            self.body, re.compile(r"(where|location|parent director)", re.I),
            "new-project: never asks where to save the project",
        )

    def test_handles_existing_directory(self):
        self.assertRegex(
            self.body, re.compile(r"already exists", re.I),
            "new-project: no handling for an existing project directory",
        )

    def test_references_real_skills(self):
        known = skill_names()
        pattern = re.compile(r"`?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`?\s+skills?\b")
        for match in pattern.finditer(self.body):
            self.assertIn(match.group(1), known)


class TestCommandCatalog(unittest.TestCase):
    def test_every_skill_reachable_from_commands(self):
        combined = "".join(
            f.read_text(encoding="utf-8") for f in COMMANDS_DIR.glob("*.md")
        )
        missing = [s for s in sorted(skill_names()) if s not in combined]
        self.assertFalse(missing, f"skills unreachable from any command: {missing}")

    def test_skills_command_lists_full_catalog(self):
        f = COMMANDS_DIR / "skills.md"
        self.assertTrue(f.is_file(), "commands/skills.md is missing")
        text = f.read_text(encoding="utf-8")
        for s in sorted(skill_names()):
            self.assertIn(s, text, f"skills.md catalog missing skill '{s}'")
        for a in agent_files():
            self.assertIn(a.stem, text, f"skills.md catalog missing agent '{a.stem}'")


class TestNotebooks(unittest.TestCase):
    def test_notebooks_parse_as_nbformat4(self):
        for f in notebook_files():
            nb = json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual(nb.get("nbformat"), 4, f"{f.name}: not nbformat 4")

    def test_no_committed_outputs(self):
        for f in notebook_files():
            nb = json.loads(f.read_text(encoding="utf-8"))
            for i, cell in enumerate(nb["cells"]):
                if cell["cell_type"] != "code":
                    continue
                self.assertEqual(
                    cell.get("outputs", []), [],
                    f"{f.name} cell {i}: committed outputs present",
                )
                self.assertIsNone(
                    cell.get("execution_count"),
                    f"{f.name} cell {i}: execution_count not cleared",
                )

    def test_no_widget_state_metadata(self):
        for f in notebook_files():
            nb = json.loads(f.read_text(encoding="utf-8"))
            self.assertNotIn(
                "widgets", nb.get("metadata", {}),
                f"{f.name}: serialized widget state in notebook metadata",
            )

    def test_source_stored_as_line_arrays(self):
        for f in notebook_files():
            nb = json.loads(f.read_text(encoding="utf-8"))
            for i, cell in enumerate(nb["cells"]):
                self.assertIsInstance(
                    cell.get("source"), list,
                    f"{f.name} cell {i}: source stored as string, not line array",
                )

    def test_no_hardcoded_secrets(self):
        for f in notebook_files():
            text = f.read_text(encoding="utf-8")
            for pattern in SECRET_PATTERNS:
                self.assertIsNone(
                    re.search(pattern, text),
                    f"{f.name}: possible hardcoded credential matching {pattern}",
                )

    def test_model_ids_are_current_aliases(self):
        """Scan joined cell sources so IDs split across source lines are seen."""
        pattern = re.compile(r"claude-[a-z0-9][a-z0-9._-]*[a-z0-9]")
        for f in notebook_files():
            nb = json.loads(f.read_text(encoding="utf-8"))
            for cell in nb["cells"]:
                src = cell["source"]
                text = src if isinstance(src, str) else "".join(src)
                for model in set(pattern.findall(text)):
                    self.assertIn(
                        model, ALLOWED_MODEL_IDS,
                        f"{f.name}: model ID '{model}' not in current allowlist",
                    )


class TestRepoDocs(unittest.TestCase):
    def test_install_instructions_consistent(self):
        expected = "/plugin marketplace add MattArtzAnthro/AI-Anthropology-Toolkit"
        for f in (REPO / "README.md", SKILLS_DIR / "README.md"):
            self.assertIn(expected, f.read_text(encoding="utf-8"), f"{f.name}: wrong install instructions")
        self.assertNotIn(
            "claude plugin add /path/to",
            (REPO / "README.md").read_text(encoding="utf-8"),
            "README.md: stale 'claude plugin add' instruction",
        )

    def test_readme_lists_new_components(self):
        text = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("qualitative-analysis", text)
        self.assertIn("analysis-advisor", text)

    def test_claude_md_counts_match_filesystem(self):
        text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
        skills_claim = re.search(r"\*\*Skills \((\d+)\)", text)
        agents_claim = re.search(r"\*\*Agents \((\d+)\)", text)
        self.assertIsNotNone(skills_claim)
        self.assertIsNotNone(agents_claim)
        self.assertEqual(int(skills_claim.group(1)), len(skill_dirs()), "CLAUDE.md skill count stale")
        self.assertEqual(int(agents_claim.group(1)), len(agent_files()), "CLAUDE.md agent count stale")

    def test_claude_md_mcp_claim_accurate(self):
        text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertNotIn(
            "lives in a separate repository", text,
            "CLAUDE.md: MCP server does not live in a separate public repository",
        )

    def test_citation_cff_well_formed(self):
        text = (REPO / "CITATION.cff").read_text(encoding="utf-8")
        self.assertRegex(text, r"cff-version:\s*1\.2\.0", "CITATION.cff: cff-version should be 1.2.0")
        self.assertRegex(text, r'doi:\s*"?10\.', "CITATION.cff: doi should be the bare DOI, not a URL")
        self.assertRegex(text, r"type:\s*software", "CITATION.cff: missing 'type: software'")
        self.assertNotRegex(text, re.compile(r"[ \t]+$", re.M), "CITATION.cff: trailing whitespace")

    def test_plugin_manifests_valid_and_agree(self):
        plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "ai-anthropology")
        entry = marketplace["plugins"][0]
        self.assertEqual(plugin["version"], entry["version"], "plugin/marketplace version mismatch")

    def test_package_version_consistency(self):
        pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
        declared = re.search(r'version = "([\d.]+)"', pyproject).group(1)
        init = (REPO / "src/ai_anthro_toolkit/__init__.py").read_text(encoding="utf-8")
        dunder = re.search(r'__version__ = "([\w.]+)"', init).group(1)
        self.assertEqual(declared, dunder,
                         "pyproject version and module __version__ disagree")

    def test_readme_mcp_section_reflects_native_data_tools(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        section = readme.split("## MCP Server", 1)[1].split("\n## ", 1)[0]
        for phrase in ("Google Trends", "podcast", "data collection"):
            self.assertIn(phrase.lower(), section.lower(),
                          f"README MCP section no longer mentions {phrase}")
        self.assertNotIn("will expand to include MCP", readme,
                         "README still claims the MCP server is future work")

    def test_readme_registers_server_across_clis(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        for snippet in ("claude mcp add", "codex mcp add", "gemini mcp add"):
            self.assertIn(snippet, readme,
                          f"README lacks the {snippet.split()[0]} registration")

    def test_readme_skills_section_is_cross_agent(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        for marker in ("~/.codex/skills", "~/.cursor/skills", "DESIGN.md"):
            self.assertIn(marker, readme,
                          f"README skills install table lacks {marker}")

    def test_agent_instruction_files_include_registration(self):
        pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
        version = re.search(r'version = "([\d.]+)"', pyproject).group(1)
        pin = f"ai-anthropology-toolkit[data]=={version}"
        for name in ("AGENTS.md", "GEMINI.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            for snippet in ("codex mcp add", "gemini mcp add", pin):
                self.assertIn(snippet, text, f"{name} lacks {snippet}")

    def test_agent_instruction_files_carry_fallback_chain(self):
        install = 'pip install "ai-anthropology-toolkit[data]"'
        for name in ("AGENTS.md", "GEMINI.md"):
            path = REPO / name
            self.assertTrue(path.exists(), f"{name} missing from repo root")
            text = path.read_text(encoding="utf-8")
            self.assertIn(install, text, f"{name} lacks the install command")
            self.assertIn("doctor", text, f"{name} lacks the doctor step")
            self.assertIn("colab", text.lower(), f"{name} lacks the Colab fallback")

    def test_readme_documents_sandbox_fallback(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn('pip install "ai-anthropology-toolkit[data]"', readme)
        self.assertIn("ai_anthro_toolkit.doctor", readme)

    def test_tool_building_writes_standing_checks_not_only_tests(self):
        """The acceptance checks verify an instrument once, while it is being
        built. The commitments settled at Stage 4 are what the researcher
        wants held months later, over data collected after the build is
        forgotten, so Stage 6 persists them as their own file."""
        body = _flat(SKILLS_DIR / "tool-building" / "SKILL.md")
        self.assertIn("instrument-checks.json", body)
        self.assertIn("ai-anthro-check", body)
        self.assertIn("silence is not consent to a default", body)
        self.assertIn("unenforceable with its reason", body)

    def test_the_spec_pack_records_the_commitments(self):
        """Nothing can generate a check from an answer that was never
        written down."""
        body = _flat(SKILLS_DIR / "tool-building" / "references"
                     / "spec-pack-template.md")
        self.assertIn("## Commitments", body)
        for commitment in ("emptiness", "duplication", "partial-presence",
                           "unparseable", "ordering"):
            with self.subTest(commitment=commitment):
                self.assertIn(commitment, body)

    def test_assembly_skills_refuse_to_reopen_a_settled_judgment(self):
        """Measured 2026-08-06 under an isolated run: both assembly scenarios
        refuted, asking 8 and 9 questions after the researcher had already
        supplied the judgment. Ceremony, not caution — the gate becoming a
        form. These skills now carry the rule that says so."""
        for name in ("ethnographic-generalization", "qualitative-analysis"):
            body = _flat(SKILLS_DIR / name / "SKILL.md")
            with self.subTest(skill=name):
                self.assertIn(
                    "already supplied is not re-opened", body,
                    f"{name} lost the rule that assembly proceeds when the "
                    f"judgment is already made",
                )
                self.assertIn(
                    "ask them together", body,
                    f"{name} lost the instruction to batch the facts "
                    f"assembly needs rather than eliciting them one by one",
                )

    def test_the_sort_gate_says_a_proposal_is_not_an_answer(self):
        """Measured 2026-08-06: tool-building's sort gate confirmed with the
        repo reachable and refuted without it. The failure is not refusing to
        propose; it is proposing and then continuing as though the proposal
        had been answered."""
        body = _flat(SKILLS_DIR / "tool-building" / "SKILL.md")
        self.assertIn("proposed classification is not a settled one", body)
        self.assertIn("the last thing on the screen is the question", body)

    def test_releasing_doc_carries_the_ordering_rule(self):
        """The package version is pinned in files that ship in the same commit
        as the code, so pushing before uploading publishes a pin to a version
        that does not exist. Three releases have broken this way; the rule
        lives in RELEASING.md and this holds it there."""
        doc = REPO / "RELEASING.md"
        self.assertTrue(doc.is_file(), "RELEASING.md missing from repo root")
        text = doc.read_text(encoding="utf-8")
        self.assertIn(
            "before pushing", text,
            "RELEASING.md no longer states that the upload precedes the push",
        )
        for pin_site in (".mcp.json", "AGENTS.md", "GEMINI.md"):
            self.assertIn(
                pin_site, text,
                f"RELEASING.md does not name {pin_site} as carrying the pin",
            )
        self.assertIn(
            "[data]==", text,
            "RELEASING.md must require verifying the extras-qualified spec: "
            "a bare ==X resolves before [data]==X does, so checking the "
            "simplified form gives a false all-clear",
        )

    def test_releasing_doc_is_discoverable(self):
        for name in ("README.md", "CLAUDE.md"):
            text = (REPO / name).read_text(encoding="utf-8")
            self.assertIn(
                "RELEASING.md", text,
                f"{name} does not point at RELEASING.md",
            )

    def test_doctor_console_script_registered(self):
        pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('ai-anthro-doctor = "ai_anthro_toolkit.doctor:main"',
                      pyproject)

    def test_mcp_json_wiring(self):
        mcp_cfg = json.loads((REPO / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("ai-anthropology", mcp_cfg["mcpServers"])
        args = " ".join(mcp_cfg["mcpServers"]["ai-anthropology"]["args"])
        pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
        version = re.search(r'version = "([\d.]+)"', pyproject)
        pin = f"ai-anthropology-toolkit[data]=={version.group(1)}"
        self.assertIn(pin, args, ".mcp.json uvx pin does not match pyproject version")
        plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin.get("mcpServers"), "./.mcp.json")

    def test_precommit_config_present_with_nbstripout(self):
        f = REPO / ".pre-commit-config.yaml"
        self.assertTrue(f.is_file(), ".pre-commit-config.yaml missing")
        self.assertIn("nbstripout", f.read_text(encoding="utf-8"))

    def test_ci_workflow_present(self):
        workflows = list((REPO / ".github" / "workflows").glob("*.yml"))
        self.assertTrue(workflows, "no GitHub Actions workflow found")
        combined = "".join(w.read_text(encoding="utf-8") for w in workflows)
        self.assertIn("unittest", combined, "CI workflow does not run the validation suite")


class TestRivalInterpretations(unittest.TestCase):
    """The rules that make this skill a test rather than a critique.

    Every rule below was arrived at by running the instrument against real
    material and watching it go wrong, so each is the kind of thing a later
    edit smooths away without noticing what it cost.
    """

    def setUp(self):
        self.skill = SKILLS_DIR / "rival-interpretations"
        self.body = _flat(self.skill / "SKILL.md")
        self.brief = _flat(self.skill / "references" / "reading-brief.md")
        self.adjudication = _flat(
            self.skill / "references" / "adjudication.md")
        self.roster = _flat(self.skill / "references" / "roster-selection.md")
        self.command = _flat(COMMANDS_DIR / "test-claim.md")

    def test_no_reading_is_admitted_without_a_falsifier(self):
        """The load-bearing guardrail, and the only thing separating three
        positions from three paraphrases. It also does the work that would
        otherwise need an authored debate posture for each of the 42 lenses:
        a position with nothing at stake cannot produce a falsifier, so it
        drops out on its own. Losing this rule silently converts the skill
        into a machine for manufacturing disagreement."""
        for name, text in (("SKILL.md", self.body),
                           ("reading-brief.md", self.brief)):
            with self.subTest(file=name):
                self.assertIn(
                    "No reading is admitted without a falsifier", text)
        self.assertIn("drawn from the material", self.body)
        self.assertIn(
            "cannot produce", self.brief,
            "reading-brief no longer says what happens to a position that "
            "cannot falsify itself here")

    def test_a_falsifier_must_be_checkable_rather_than_theoretical(self):
        """A falsifier that names a theoretical caveat rather than something
        in the material passes the letter of the rule and defeats its point,
        so the brief carries the inadmissible forms explicitly."""
        self.assertIn("Not a theoretical objection", self.body)
        self.assertIn("Not a theoretical caveat", self.brief)
        self.assertIn("Do not substitute a theoretical objection", self.brief)
        self.assertIn("Not admissible", self.brief)

    def test_no_rebuttal_without_a_span(self):
        """Arguing about a paraphrase of the anchor wastes the one advantage
        this method has, and it is how a rebuttal round produces heat."""
        self.assertIn("No rebuttal without a span", self.body)
        self.assertIn("No rebuttal without a span", self.brief)

    def test_rebuttals_are_targeted_rather_than_all_pairs(self):
        """Firing every pair spends a full dispatch to produce one sentence
        of agreement. Measured in the trial run: one pair out of three
        actually collided."""
        for text in (self.body, self.brief):
            self.assertIn("same span", text)
        self.assertIn("incompatible", self.brief)

    def test_readers_never_see_each_other(self):
        """Isolation is the entire reason this dispatches subagents. Three
        positions argued in one context produce one context talking to
        itself in three registers."""
        self.assertIn("None sees the others' readings", self.brief)
        self.assertRegex(
            self.body,
            r"[Nn]one sees the others' readings|never sees the others",
            "SKILL.md no longer states that readers are isolated")

    def test_the_home_position_is_asked_for_singly_not_ranked(self):
        """A full ranking was the original request and is deliberately not
        built: under a rule that filters nothing, only the first position is
        ever used. This is exactly the kind of departure a later edit
        'restores' without re-deriving why it was dropped."""
        self.assertIn("Not a ranking", self.body)
        self.assertIn(
            "cannot be discounted by discounting its source", self.body,
            "SKILL.md lost the reason the home position is asked for at all")

    def test_the_claim_is_ratified_and_outranks_the_roster(self):
        """Testing the wrong claim well is worse than declining, because it
        arrives looking like a result. Mirrors tool-building's sort gate."""
        self.assertIn("A proposed claim is not a settled one", self.body)
        self.assertIn("the last thing on the screen is the question",
                      self.body)
        self.assertIn("outranks confirming the roster", self.body)

    def test_declining_is_a_reported_outcome(self):
        """A skill that always finds something worth three readers is
        selling rather than testing, and the command must not promise a test
        before the gate has run."""
        self.assertIn("Declining is the common outcome", self.body)
        self.assertIn("declines more often than it runs", self.body)
        self.assertIn(
            "A declined gate is a result", self.command,
            "test-claim no longer reports a declined gate as a result")

    def test_the_worklist_keeps_defects_and_decisions_apart(self):
        """The failure mode is writing a decision as an instruction, because
        the imperative mood is shorter and reads as more useful. The trial
        run did it three times out of five."""
        self.assertIn("Never convert a decision into a defect", self.body)
        self.assertIn(
            "may never convert one into the other", self.adjudication)
        for required in ("## Defects", "## Decisions"):
            with self.subTest(section=required):
                self.assertIn(required, self.adjudication)

    def test_what_stays_open_is_never_resolved_for_the_researcher(self):
        """Naming a genuine conflict and then recommending a side converts
        the researcher's decision into the machine's."""
        self.assertIn("never dissolved", self.body)
        self.assertIn("no recommended resolution", self.body)
        self.assertIn("never recommend a side", self.adjudication)

    def test_convergence_is_never_reported_as_proof(self):
        """Three positions agreeing is evidence about the roster as much as
        about the claim, and a roster built on one axis converges by
        construction."""
        self.assertIn("Convergence is never reported as proof",
                      self.adjudication)
        self.assertIn("Never present convergence as proof", self.body)
        self.assertIn(
            "Name the roster", self.adjudication,
            "a convergence claim is uninterpretable without knowing what "
            "agreed")

    def test_the_record_closes_on_the_researcher(self):
        """The record is what makes this a research artifact rather than a
        critique, and an empty Resolution section presented as a completed
        test reads as though the instrument settled something."""
        self.assertIn("## Resolution", self.adjudication)
        self.assertIn("Carried forward unresolved", self.adjudication)
        self.assertIn("## Unresolved", self.adjudication)
        self.assertIn(
            "has usually been tidied rather than finished", self.body)

    def test_the_record_discloses_that_the_readings_were_machine_argued(self):
        """A reader who assumes three colleagues read the chapter has been
        misled by omission, and the methods-section claim is the whole
        reason the record exists."""
        self.assertIn("machine-argued", self.adjudication)

    def test_registry_entries_that_cannot_argue_are_named(self):
        """Four registry entries are methodological or scope framings rather
        than positions. Silently substituting something adjacent hides a true
        thing about the researcher's own request."""
        for entry in ("evaluation", "mixed_methods", "multi_sited",
                      "historical_archival"):
            with self.subTest(entry=entry):
                self.assertIn(entry, self.roster)
        self.assertIn("rather than silently substituting", self.roster)

    def test_the_roster_is_bounded_by_the_registry(self):
        """A position improvised outside the registry argues from a
        literature nobody can check."""
        self.assertIn("42-lens registry", self.roster)
        self.assertIn("not a hole for this skill to patch", self.roster)

    def test_the_coding_modifier_is_not_mistaken_for_a_debate_brief(self):
        """Every one of the 42 prompt modifiers ends in a coding
        instruction. Reusing one as an argumentative brief is the mistake
        that makes a thin position sound confident."""
        self.assertIn("Do not treat the coding modifier as a debate brief",
                      self.roster)

    def test_measured_divergence_outranks_predicted_divergence(self):
        """The gate's third condition is a prediction everywhere except
        where a cross-lens run has already measured it, and that is the
        strongest form it takes."""
        self.assertIn("evidence rather than prediction", self.body)
        for text in (self.body, self.roster):
            self.assertIn("friction points", text)


if __name__ == "__main__":
    unittest.main()
