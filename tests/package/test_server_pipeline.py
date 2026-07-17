"""End-to-end tests for the MCP server's analysis pipeline tools.

Covers the delegated batch loop (scripted orchestrator responses) and, when
the Claude CLI is available, a live api-mode coding job with completions
routed through `claude -p`.

    python3.12 -m unittest tests.package.test_server_pipeline -v
"""

import asyncio
import json
import shutil
import subprocess
import tempfile
import time
import unittest

import numpy as np

from ai_anthro_toolkit import chunking as chunking_mod
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.mcp import server

CHUNKS = [
    {"chunk_id": 1, "text": "We pool money every month so school fees are possible.", "speaker": "AMARA"},
    {"chunk_id": 2, "text": "The clinic closed; the government forgot us, we rely on each other.", "speaker": "AMARA"},
    {"chunk_id": 3, "text": "I trade vegetables for fish with the same women weekly.", "speaker": "AMARA"},
]

CODEBOOK = [
    {"code_label": "mutual_aid", "definition": "Pooling resources or labor to support one another"},
    {"code_label": "state_absence", "definition": "Perceived withdrawal of government services"},
    {"code_label": "reciprocal_exchange", "definition": "Recurring non-monetary exchange based on trust"},
]


class ServerTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old_jobs = server._jobs
        server._jobs = JobStore(self._tmp)

    def tearDown(self):
        server._jobs = self._old_jobs
        shutil.rmtree(self._tmp, ignore_errors=True)


class TestToolRegistry(ServerTestBase):
    def test_pipeline_tools_registered(self):
        tools = {t.name for t in asyncio.run(server.mcp.list_tools())}
        expected = {"toolkit_info", "search_openalex", "search_pubmed",
                    "list_lenses", "get_lens", "chunk_transcript",
                    "start_codebook_job", "start_coding_job", "get_next_batch",
                    "submit_batch", "get_job_status", "get_job_result",
                    "build_themes", "compare_lenses"}
        self.assertEqual(tools, expected)


class TestChunkTool(ServerTestBase):
    def test_chunk_transcript_with_stub_embedder(self):
        class Stub:
            def encode(self, sentences, **k):
                return np.ones((len(sentences), 8))

        old = getattr(chunking_mod, "_default_embedder", None)
        try:
            chunking_mod._default_embedder = Stub()
            out = server.chunk_transcript(
                text="AMARA: One sentence here. Another sentence follows. A third one.",
                max_sentences=2)
            self.assertGreaterEqual(out["total_chunks"], 1)
            self.assertIn("coherence_score", out["chunks"][0])
        finally:
            chunking_mod._default_embedder = old


class TestDelegatedCoding(ServerTestBase):
    def test_full_delegated_loop_with_validation(self):
        start = server.start_coding_job(CHUNKS, CODEBOOK, lens_key="interpretive",
                                        llm_mode="delegated")
        job_id = start["job_id"]
        self.assertEqual(start["mode"], "delegated")
        self.assertEqual(start["packets"], 3)

        batch = server.get_next_batch(job_id, batch_size=10)
        self.assertEqual(len(batch["packets"]), 3)
        self.assertIn("mutual_aid", batch["packets"][0]["prompt"])

        # scripted orchestrator: one valid, one with a hallucinated code, one empty
        # (response format per the notebook contract: bare comma-separated codes)
        results = [
            {"id": batch["packets"][0]["id"], "response": "mutual_aid"},
            {"id": batch["packets"][1]["id"],
             "response": "state_absence, community_resilience"},
            {"id": batch["packets"][2]["id"], "response": "NO_CODES"},
        ]
        out = server.submit_batch(job_id, results)
        self.assertEqual(out["remaining"], 0)
        self.assertTrue(any(r["invalid_codes"] == ["community_resilience"]
                            for r in out["rejected"]),
                        "hallucinated code was not rejected")

        status = server.get_job_status(job_id)
        self.assertEqual(status["status"], "complete")

        result = server.get_job_result(job_id)
        self.assertTrue(result["ready"])
        records = result["records"]
        self.assertEqual(records[0]["Deductive_Codes"], "mutual_aid")
        self.assertEqual(records[1]["Deductive_Codes"], "state_absence")
        self.assertEqual(records[2]["Coding_Status"], "No_Codes")


class TestDelegatedCodebook(ServerTestBase):
    def test_delegated_codebook_job(self):
        docs = {"fieldnote.txt": "Community members organise rotating savings groups. " * 30}
        start = server.start_codebook_job(docs, "interpretive",
                                          llm_mode="delegated", min_frequency=1)
        job_id = start["job_id"]
        self.assertGreaterEqual(start["packets"], 1)

        canned = json.dumps([{
            "label": "rotating_savings",
            "definition": "Member-run rotating credit groups pooling household funds",
            "extraction_type": "emergent",
            "example": "rotating savings groups",
        }])
        while True:
            batch = server.get_next_batch(job_id, batch_size=5)
            if batch["done"]:
                break
            server.submit_batch(job_id, [
                {"id": p["id"], "response": canned} for p in batch["packets"]])

        result = server.get_job_result(job_id)
        self.assertTrue(result["ready"])
        rec = result["records"][0]
        # sanitize_code_label uppercases (notebook convention)
        self.assertEqual(rec["code_label"], "ROTATING_SAVINGS")
        self.assertEqual(rec["stance_key"], "interpretive")
        self.assertEqual(rec["stance"], "Interpretive")
        self.assertIn("quality_report", result)


class TestThemesAndCrossLens(ServerTestBase):
    CODED = [
        {"chunk_id": 1, "text": "t1", "Deductive_Codes": "MUTUAL_AID",
         "Inductive_Codes": "", "All_Codes": "MUTUAL_AID",
         "Coding_Status": "Deductive_Only"},
        {"chunk_id": 2, "text": "t2", "Deductive_Codes": "STATE_ABSENCE",
         "Inductive_Codes": "", "All_Codes": "STATE_ABSENCE",
         "Coding_Status": "Deductive_Only"},
    ]

    def test_build_themes_delegated_two_step(self):
        first = server.build_themes(coded=self.CODED, lens_key="interpretive",
                                    llm_mode="delegated")
        self.assertIn("delegated_prompt", first)
        self.assertTrue(first["delegated_prompt"])

        completion = (
            "THEME 1: Solidarity Under Withdrawal\n"
            "Core Concept: Households substitute mutual support for services the "
            "state no longer provides. Care migrates from institutions to relations.\n"
            "Sub-themes:\n"
            "  a) Rotating support: Pooled resources cover recurring needs\n"
            "Key Finding: Mutual aid absorbs the functions of absent institutions, "
            "supported by MUTUAL_AID and STATE_ABSENCE.\n"
            "Supporting Codes: MUTUAL_AID, STATE_ABSENCE\n"
        )
        second = server.build_themes(coded=self.CODED, lens_key="interpretive",
                                     llm_mode="delegated", response=completion)
        self.assertGreaterEqual(len(second["themes"]), 1)
        self.assertIn("MUTUAL_AID", second["themes"][0]["codes"])
        self.assertIn("patterns", second)

    def test_compare_lenses_via_results(self):
        lens_a = self.CODED
        lens_b = [dict(r, All_Codes="MUTUAL_AID") for r in self.CODED]
        out = server.compare_lenses(results_by_lens={"interpretive": lens_a,
                                                     "critical": lens_b})
        self.assertIn("agreement_matrix", out)
        self.assertIn("mean_agreement", out)


def _claude_cli_available() -> bool:
    return shutil.which("claude") is not None


@unittest.skipUnless(_claude_cli_available(), "claude CLI not available")
class TestApiModeLiveViaCli(ServerTestBase):
    """Live api-mode job with completions routed through `claude -p`."""

    def test_api_mode_coding_job_live(self):
        def cli_llm(prompt, *, system=None, temperature=0.3, max_tokens=4096):
            full = (f"<system>\n{system}\n</system>\n\n{prompt}"
                    if system else prompt)
            r = subprocess.run(["claude", "-p", full, "--model", "claude-haiku-4-5"],
                               capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                raise RuntimeError(r.stderr[:200])
            return r.stdout.strip()

        old = server._api_llm
        server._api_llm = lambda model=None: cli_llm
        try:
            start = server.start_coding_job(CHUNKS[:2], CODEBOOK,
                                            lens_key="interpretive",
                                            llm_mode="api")
            job_id = start["job_id"]
            deadline = time.time() + 240
            while time.time() < deadline:
                status = server.get_job_status(job_id)
                if status["status"] in ("complete", "failed"):
                    break
                time.sleep(3)
            self.assertEqual(status["status"], "complete",
                             f"job did not complete: {status}")
            result = server.get_job_result(job_id)
            self.assertTrue(result["ready"])
            valid = {c["code_label"] for c in CODEBOOK} | {""}
            for rec in result["records"]:
                for code in rec["Deductive_Codes"].split(","):
                    self.assertIn(code.strip(), valid,
                                  f"invalid code survived: {code!r}")
        finally:
            server._api_llm = old


if __name__ == "__main__":
    unittest.main()
