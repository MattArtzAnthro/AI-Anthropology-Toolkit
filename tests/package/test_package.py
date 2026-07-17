"""Package tests: lens parity with the notebooks, live datasource micro-queries,
and the MCP tool registry.

    python3.12 -m unittest tests.package.test_package -v
"""

import json
import re
import unittest
from pathlib import Path

from ai_anthro_toolkit import lenses
from ai_anthro_toolkit.datasources import search_openalex, search_pubmed
from ai_anthro_toolkit.mcp import server

REPO = Path(__file__).resolve().parents[2]


class TestLensRegistry(unittest.TestCase):
    def test_42_lenses(self):
        self.assertEqual(len(lenses.STANCE_DEFINITIONS), 42)
        for key, entry in lenses.STANCE_DEFINITIONS.items():
            self.assertTrue(entry.get("name"), key)
            self.assertTrue(entry.get("prompt_modifier"), key)

    def test_find_lens_by_key_and_name(self):
        self.assertEqual(lenses.find_lens("critical_race")[0], "critical_race")
        self.assertEqual(lenses.find_lens("Critical Race")[0], "critical_race")
        self.assertEqual(lenses.find_lens("sts / actor-network")[0], "sts_actor_network")
        self.assertIsNone(lenses.find_lens("not a lens"))

    def test_parity_with_published_codebook_notebook(self):
        """Drift tripwire: package registry must match the notebook's."""
        nb_path = REPO / "notebooks" / "Qualitative_Codebook_Builder.ipynb"
        if not nb_path.exists():
            self.skipTest("published notebook not present")
        nb = json.loads(nb_path.read_text(encoding="utf-8"))
        code = "\n".join("".join(c["source"]) for c in nb["cells"]
                         if c["cell_type"] == "code")
        keys = set(re.findall(r'"(\w+)":\s*\{\s*\n\s*"name":', code))
        self.assertEqual(keys, set(lenses.STANCE_DEFINITIONS.keys()),
                         "lens registry drifted from the published notebook")


class TestDataSourcesLive(unittest.TestCase):
    """Tiny real queries against the public APIs."""

    def test_openalex(self):
        works = search_openalex("digital ethnography", limit=3)
        self.assertGreaterEqual(len(works), 1)
        first = works[0]
        for field in ("title", "authors", "year", "cited_by_count"):
            self.assertIn(field, first)

    def test_pubmed(self):
        records = search_pubmed("medical anthropology", limit=3)
        self.assertGreaterEqual(len(records), 1)
        first = records[0]
        for field in ("pmid", "title", "journal"):
            self.assertIn(field, first)


class TestMcpServer(unittest.TestCase):
    def test_expected_tools_registered(self):
        import asyncio
        tools = {t.name for t in asyncio.run(server.mcp.list_tools())}
        self.assertEqual(tools, {
            "search_openalex", "search_pubmed", "list_lenses", "get_lens",
            "toolkit_info", "chunk_transcript", "start_codebook_job",
            "start_coding_job", "get_next_batch", "submit_batch",
            "get_job_status", "get_job_result", "build_themes",
            "compare_lenses"})

    def test_lens_tools(self):
        hits = server.list_lenses("decolonial")
        self.assertEqual(hits[0]["key"], "decolonial")
        full = server.get_lens("Decolonial")
        self.assertIn("prompt_modifier", full)
        with self.assertRaises(ValueError):
            server.get_lens("nonsense")


if __name__ == "__main__":
    unittest.main()
