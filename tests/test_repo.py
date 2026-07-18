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


def notebook_files():
    return sorted(NOTEBOOKS_DIR.glob("*.ipynb"))


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


if __name__ == "__main__":
    unittest.main()
