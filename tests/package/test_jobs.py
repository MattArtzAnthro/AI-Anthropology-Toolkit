"""The job store refuses IDs it did not issue, and says what a real one looks like.

A job ID reaches the store from the orchestrating model, which can mistype
it or invent one. Reading an unknown job must not create anything, must not
reach outside the store's root, and must not answer as if the job existed:
get_next_batch once returned done=true for a typo, which reads as "finished".

    python3.12 -m unittest tests.package.test_jobs -v
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ai_anthro_toolkit import jobs
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.mcp import server


class TestJobStoreIds(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())
        self.root = self._tmp / "jobs"
        self.store = JobStore(self.root)

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_created_ids_round_trip(self):
        job_id = self.store.create("coding", {"total": 2})
        self.assertRegex(job_id, r"^coding-[0-9a-f]{8}$")
        self.assertEqual(self.store.status(job_id)["total"], 2)
        self.store.save_artifact(job_id, "result.json", "[]")
        self.assertEqual(self.store.load_artifact(job_id, "result.json"), "[]")
        self.assertIsNone(self.store.load_artifact(job_id, "missing.json"))

    def test_unknown_id_raises_and_creates_nothing(self):
        for call in (self.store.read, self.store.status,
                     lambda j: self.store.load_artifact(j, "result.json"),
                     lambda j: self.store.save_artifact(j, "x.json", "{}")):
            with self.assertRaises(ValueError) as ctx:
                call("coding-0badc0de")
            self.assertIn("coding-0badc0de", str(ctx.exception))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_malformed_id_is_refused_before_touching_disk(self):
        for bad in ("../escaped", "coding-typo123", "", "coding-1234567", "/etc/x",
                    "coding-0badc0de/../../x", "coding-0BADC0DE", "coding-0badc0de0",
                    "Coding-0badc0de", "_x-0badc0de", "coding-0badc0de\n", None, 123):
            with self.subTest(job_id=bad):
                with self.assertRaises(ValueError) as ctx:
                    self.store.status(bad)
                self.assertIn("coding-1a2b3c4d", str(ctx.exception))
        self.assertEqual(sorted(p.name for p in self._tmp.iterdir()), ["jobs"])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_unknown_and_malformed_ids_raise_different_errors(self):
        with self.assertRaises(jobs.UnknownJobError):
            self.store.status("coding-0badc0de")
        with self.assertRaises(ValueError) as ctx:
            self.store.status("../escaped")
        self.assertNotIsInstance(ctx.exception, jobs.UnknownJobError)

    def test_a_directory_without_job_json_is_not_a_job(self):
        (self.root / "coding-0badc0de").mkdir()
        with self.assertRaises(jobs.UnknownJobError):
            self.store.status("coding-0badc0de")

    def test_unknown_job_error_is_a_value_error(self):
        # FastMCP reports ValueError text to the caller; keep it in that family.
        # (Asserted as ValueError throughout so the old code fails by assertion.)
        self.assertTrue(issubclass(getattr(jobs, "UnknownJobError", type), ValueError))


class TestServerUnknownJob(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old_jobs = server._jobs
        server._jobs = JobStore(self._tmp)

    def tearDown(self):
        server._jobs = self._old_jobs
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_next_batch_for_unknown_job_is_an_error_not_done(self):
        with self.assertRaises(ValueError):
            server.get_next_batch("coding-0badc0de")

    def test_status_and_result_for_unknown_job_raise(self):
        for tool in (server.get_job_status, server.get_job_result):
            with self.subTest(tool=tool.__name__):
                with self.assertRaises(ValueError):
                    tool("coding-0badc0de")
        self.assertEqual(list(Path(self._tmp).iterdir()), [])


class TestServerJobResults(unittest.TestCase):
    CODEBOOK = [{"code_label": "mutual_aid", "definition": "Pooling resources"},
                {"code_label": "state_absence", "definition": "Withdrawn services"}]
    CHUNKS = [{"chunk_id": 1, "text": "We pool money."},
              {"chunk_id": 2, "text": "The clinic closed."}]

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old_jobs = server._jobs
        server._jobs = JobStore(self._tmp)

    def tearDown(self):
        server._jobs = self._old_jobs
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _completed_job(self, n):
        job_id = server._jobs.create("coding", {})
        server._jobs.save_artifact(job_id, "result.json",
                                   json.dumps([{"chunk_id": i} for i in range(n)]))
        server._jobs.complete(job_id)
        return job_id

    def test_result_pages_and_says_where_the_next_page_starts(self):
        job_id = self._completed_job(250)
        first = server.get_job_result(job_id)
        self.assertEqual((first["total"], first["returned"], first["next_offset"]), (250, 100, 100))
        self.assertEqual(first["records"][0]["chunk_id"], 0)
        last = server.get_job_result(job_id, offset=200)
        self.assertEqual(last["returned"], 50)
        self.assertEqual(last["records"][-1]["chunk_id"], 249)
        self.assertNotIn("next_offset", last)
        self.assertNotIn("note", last)

    def test_include_text_false_keeps_codes_and_drops_text(self):
        job_id = server._jobs.create("coding", {})
        server._jobs.save_artifact(job_id, "result.json", json.dumps(
            [{"chunk_id": 1, "text": "long passage", "All_Codes": "a, b"}]))
        server._jobs.complete(job_id)
        rec = server.get_job_result(job_id, include_text=False)["records"][0]
        self.assertEqual(rec, {"chunk_id": 1, "All_Codes": "a, b"})
        self.assertEqual(server.get_job_result(job_id)["records"][0]["text"], "long passage")

    def test_status_counts_cover_every_record_not_just_the_page(self):
        job_id = server._jobs.create("coding", {})
        recs = [{"chunk_id": i, "Coding_Status": "No_Codes" if i % 5 == 0 else "Deductive_Only"}
                for i in range(250)]
        server._jobs.save_artifact(job_id, "result.json", json.dumps(recs))
        server._jobs.complete(job_id)
        out = server.get_job_result(job_id, limit=10)
        self.assertEqual(out["coding_status_counts"], {"No_Codes": 50, "Deductive_Only": 200})
        self.assertNotIn("coding_status_counts", server.get_job_result(self._completed_job(3)))

    def test_offset_and_limit_are_clamped(self):
        job_id = self._completed_job(250)
        self.assertEqual(server.get_job_result(job_id, limit=0)["returned"], 1)
        self.assertEqual(server.get_job_result(job_id, limit=10_000)["returned"], 250)
        self.assertEqual(server.get_job_result(job_id, offset=-5)["offset"], 0)
        self.assertEqual(server.get_job_result(job_id, offset=999)["returned"], 0)

    def test_paging_every_page_recovers_every_record(self):
        job_id = self._completed_job(250)
        seen, offset = [], 0
        while True:
            page = server.get_job_result(job_id, offset=offset, limit=70)
            seen += [r["chunk_id"] for r in page["records"]]
            if "next_offset" not in page:
                break
            offset = page["next_offset"]
        self.assertEqual(seen, list(range(250)))

    def test_coding_reads_the_ratified_codebook_itself(self):
        rid = server.ratify_codebook(codebook=self.CODEBOOK)["ratification_id"]
        out = server.start_coding_job(self.CHUNKS, ratification_id=rid, llm_mode="delegated")
        state = server._jobs.read(out["job_id"])
        self.assertEqual(state["payload"]["valid_codes"], ["mutual_aid", "state_absence"])
        self.assertEqual(out["packets"], 2)

    def test_coding_with_a_ratification_that_holds_no_records_is_refused(self):
        rid = server.ratify_codebook(codebook=self.CODEBOOK)["ratification_id"]
        (Path(self._tmp) / rid / "result.json").unlink()
        with self.assertRaises(ValueError) as ctx:
            server.start_coding_job(self.CHUNKS, ratification_id=rid, llm_mode="delegated")
        self.assertIn("holds no codebook records", str(ctx.exception))

    def test_missing_transcript_file_is_an_actionable_error(self):
        with self.assertRaises(ValueError) as ctx:
            server.chunk_transcript(path=str(Path(self._tmp) / "nope.txt"))
        self.assertIn("No transcript file", str(ctx.exception))


class TestErrorsReachTheModel(unittest.TestCase):
    """mcp 2.x forwards an exception's text only when it is a ToolError; the
    server relays its anticipated errors so the model reads them, not just
    "Error executing tool <name>"."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old_jobs = server._jobs
        server._jobs = JobStore(self._tmp)

    def tearDown(self):
        server._jobs = self._old_jobs
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _call(self, name, args):
        import asyncio

        from mcp.server.mcpserver.exceptions import ToolError
        with self.assertRaises(ToolError) as ctx:
            asyncio.run(server.mcp.call_tool(name, args))
        return str(ctx.exception)

    def test_unknown_job_text_is_relayed(self):
        self.assertIn("No job 'coding-1a2b3c4e'", self._call(
            "get_next_batch", {"job_id": "coding-1a2b3c4e"}))

    def test_runtime_error_text_is_relayed(self):
        from unittest import mock
        with mock.patch.object(server._data, "search_youtube",
                               side_effect=RuntimeError("YouTube blocked this IP; retry later.")):
            self.assertIn("retry later", self._call("search_youtube", {"query": "x"}))

    def test_direct_callers_still_get_the_original_type(self):
        with self.assertRaises(ValueError):
            server.get_lens("no-such-lens")


if __name__ == "__main__":
    unittest.main()
