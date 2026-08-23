"""Consistency tripwires: server metadata, catalog, and notebook-prompt parity.

These tests exist so documentation and metadata cannot drift silently from
the code: tool families must match the registry, every tool must describe
itself, the notebook catalog must mirror notebooks/, and the package's
prompt templates must remain verbatim ports of the published notebooks.

    python3.12 -m unittest tests.package.test_consistency -v
"""

import asyncio
import json
import re
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


class TestNotebookParityClaim(unittest.TestCase):
    def test_notebooks_claim_does_not_promise_universal_coverage(self):
        """The claim read "Every capability also exists as a hands-on Colab
        notebook" while four tool families had none — methodology, documents,
        checks, and citations. A researcher choosing this toolkit because
        every capability is inspectable in Colab would have been choosing on
        a false premise, and nothing here could catch it."""
        claim = server.toolkit_info()["notebooks"].lower()
        for absolute in ("every capability", "all capabilities",
                         "every tool", "each capability"):
            self.assertNotIn(absolute, claim,
                             f"notebooks claim promises {absolute!r}; "
                             "verify it against catalog.NOTEBOOKS first")

    def test_families_without_notebooks_are_still_without_notebooks(self):
        """If a notebook is ever added for one of these, the claim above
        should be revisited rather than left understating the coverage."""
        families = server.toolkit_info()["tool_families"]
        for family in ("methodology", "documents", "checks", "citations"):
            self.assertIn(family, families)
        names = " ".join(n["github_url"] for n in catalog.NOTEBOOKS).lower()
        for absent in ("citation", "lens", "markup"):
            self.assertNotIn(absent, names,
                             f"a {absent} notebook now exists; update the "
                             "server's notebooks claim to include it")


class TestNetworkHygiene(unittest.TestCase):
    def test_every_requests_call_has_a_timeout(self):
        import re
        src = REPO / "src" / "ai_anthro_toolkit"
        offenders = []
        for path in src.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"requests\.(?:get|post)\(", text):
                span = text[match.start():match.start() + 400]
                if "timeout" not in span:
                    line = text.count("\n", 0, match.start()) + 1
                    offenders.append(f"{path.relative_to(REPO)}:{line}")
        self.assertEqual(offenders, [],
                         "requests calls without a timeout can hang forever: "
                         + ", ".join(offenders))


class TestDependencyBounds(unittest.TestCase):
    """A major release of a dependency can remove what the server imports.

    mcp 2.0.0 dropped mcp.server.fastmcp. With an unbounded requirement, a
    fresh resolve picks it up and ai-anthro-mcp dies at import — while this
    suite stays green, because it runs against whatever mcp is already
    installed rather than against what a new install would choose. Nothing
    else here can see that, so the bound itself is the thing under test.
    """

    def _requirement(self, name: str) -> str:
        text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
        block = re.search(r"^dependencies\s*=\s*\[(.*?)^\]", text, re.S | re.M)
        self.assertIsNotNone(block, "no dependencies array in pyproject.toml")
        for spec in re.findall(r'"([^"]+)"', block.group(1)):
            if re.match(rf"{name}\b", spec):
                return spec
        self.fail(f"{name} is not declared in dependencies")

    def test_mcp_requirement_has_an_upper_bound(self):
        spec = self._requirement("mcp")
        self.assertTrue(
            "<" in spec,
            f"the mcp requirement is {spec!r}, with no upper bound. mcp 2.0.0 "
            "removed mcp.server.fastmcp, so an unbounded requirement resolves "
            "to a release the server cannot start under.",
        )

    def test_the_module_the_server_imports_still_exists(self):
        try:
            import mcp.server.fastmcp  # noqa: F401
        except ModuleNotFoundError as exc:
            self.fail(
                f"mcp.server.fastmcp is not importable ({exc}). The installed "
                "mcp is a release this server cannot run on; check the upper "
                "bound in pyproject.toml.",
            )


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
