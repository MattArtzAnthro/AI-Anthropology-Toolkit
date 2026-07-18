"""Consistency tripwires: server metadata, catalog, and notebook-prompt parity.

These tests exist so documentation and metadata cannot drift silently from
the code: tool families must match the registry, every tool must describe
itself, the notebook catalog must mirror notebooks/, and the package's
prompt templates must remain verbatim ports of the published notebooks.

    python3.12 -m unittest tests.package.test_consistency -v
"""

import asyncio
import json
import unittest
from pathlib import Path

from ai_anthro_toolkit import catalog, codebook, coding, themes
from ai_anthro_toolkit.mcp import server

REPO = Path(__file__).resolve().parents[2]
NOTEBOOKS = REPO / "notebooks"


def _notebook_code(name: str) -> str:
    nb = json.loads((NOTEBOOKS / name).read_text(encoding="utf-8"))
    return "\n".join("".join(c["source"]) for c in nb["cells"]
                     if c["cell_type"] == "code")


class TestServerMetadata(unittest.TestCase):
    def test_tool_families_match_registry_exactly(self):
        registered = {t.name for t in asyncio.run(server.mcp.list_tools())}
        families = server.toolkit_info()["tool_families"]
        declared = {name for tools in families.values() for name in tools}
        self.assertEqual(
            declared | {"toolkit_info"}, registered,
            "toolkit_info tool_families drifted from the registered tools",
        )

    def test_every_tool_has_a_description(self):
        for t in asyncio.run(server.mcp.list_tools()):
            self.assertTrue((t.description or "").strip(),
                            f"tool {t.name} has no description")

    def test_instructions_name_only_real_tools(self):
        registered = {t.name for t in asyncio.run(server.mcp.list_tools())}
        import re
        instructions = server.mcp.instructions or ""
        for name in re.findall(r"\b(?:get|search|list|start|submit|build|compare|chunk)_[a-z_]+\b",
                               instructions):
            self.assertIn(name, registered,
                          f"instructions mention unregistered tool '{name}'")


class TestNotebookCatalog(unittest.TestCase):
    def test_catalog_matches_notebooks_directory_bidirectionally(self):
        catalog_files = {n["github_url"].rsplit("/", 1)[-1]
                        for n in catalog.NOTEBOOKS}
        on_disk = {p.name for p in NOTEBOOKS.glob("*.ipynb")}
        self.assertEqual(catalog_files - on_disk, set(),
                         "catalog lists notebooks that do not exist")
        self.assertEqual(on_disk - catalog_files, set(),
                         "notebooks on disk missing from the catalog")


class TestPromptParity(unittest.TestCase):
    """The drift treaty: package prompts stay verbatim ports of the notebooks.

    Placeholder lines (containing '{') may differ in interpolation syntax, so
    parity is asserted over the literal lines: at least 90% of a template's
    non-placeholder lines must appear verbatim in the notebook source.
    """

    def assert_parity(self, template: str, notebook: str, label: str):
        source = _notebook_code(notebook)
        lines = [ln.strip() for ln in template.splitlines()
                 if ln.strip() and "{" not in ln]
        self.assertGreaterEqual(len(lines), 5, f"{label}: template too short to check")
        missing = [ln for ln in lines if ln not in source]
        ratio = 1 - len(missing) / len(lines)
        self.assertGreaterEqual(
            ratio, 0.9,
            f"{label}: prompt drifted from {notebook} — missing lines: {missing[:5]}",
        )

    def test_deductive_coding_prompt(self):
        self.assert_parity(coding.DEDUCTIVE_CODING_PROMPT,
                           "Coding_and_Thematic_Analysis.ipynb", "deductive")

    def test_inductive_prompts(self):
        self.assert_parity(coding.INDUCTIVE_GENERATION_PROMPT,
                           "Coding_and_Thematic_Analysis.ipynb", "inductive-gen")
        self.assert_parity(coding.INDUCTIVE_APPLICATION_PROMPT,
                           "Coding_and_Thematic_Analysis.ipynb", "inductive-apply")

    def test_theme_prompt(self):
        self.assert_parity(themes.THEME_BUILDING_PROMPT,
                           "Coding_and_Thematic_Analysis.ipynb", "themes")

    def test_codebook_prompts(self):
        self.assert_parity(codebook.EXTRACTION_PROMPT_TEMPLATE,
                           "Qualitative_Codebook_Builder.ipynb", "extraction")
        self.assert_parity(codebook.CONSOLIDATION_PROMPT,
                           "Qualitative_Codebook_Builder.ipynb", "consolidation")


if __name__ == "__main__":
    unittest.main()
