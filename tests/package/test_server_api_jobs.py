"""API-mode job workers in the MCP server, offline.

The model is replaced where the server obtains it (`server._api_llm`), and
the sentence embedder where the codebook refiner obtains it, so the real
job thread, job store, and result handling all run. Nothing here calls the
Anthropic API or spends tokens.

    python3.12 -m unittest tests.package.test_server_api_jobs -v
"""

import json
import os
import shutil
import tempfile
import time
import unittest
from unittest import mock

import numpy as np

from ai_anthro_toolkit import codebook as codebook_mod
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.mcp import server

CHUNKS = [
    {"chunk_id": 1, "text": "We pool money every month so school fees are possible.",
     "speaker": "WÓJCIK"},
    {"chunk_id": 2, "text": "The clinic closed; the government forgot us.",
     "speaker": "WÓJCIK"},
    {"chunk_id": 3, "text": "I trade vegetables for fish with the same women weekly.",
     "speaker": "KOWALSKI"},
]

CODEBOOK = [
    {"code_label": "mutual_aid", "definition": "Pooling resources or labor to support one another"},
    {"code_label": "state_absence", "definition": "Perceived withdrawal of government services"},
    {"code_label": "reciprocal_exchange", "definition": "Recurring non-monetary exchange based on trust"},
]

EXTRACTION = json.dumps([
    {"label": "rotating savings", "definition": "Member-run rotating credit groups "
     "that pool household funds.", "extraction_type": "emergent",
     "example": "we pool money every month", "code_group": "Economy"},
    {"label": "state_absence", "definition": "Withdrawal of public services felt "
     "in everyday life.", "extraction_type": "theoretical",
     "example": "the clinic closed", "code_group": "Politics"},
])


def one_hot_embedder(texts):
    """Every distinct text gets its own axis, so nothing is a duplicate."""
    vocab = {}
    rows = []
    for t in texts:
        vocab.setdefault(t, len(vocab))
    for t in texts:
        v = np.zeros(max(1, len(vocab)))
        v[vocab[t]] = 1.0
        rows.append(v)
    return np.array(rows)


def scripted_llm(route):
    """An llm callable answering each prompt through `route(prompt, system)`."""
    calls = []

    def llm(prompt, *, system=None, temperature=0.3, max_tokens=4096):
        calls.append((prompt, system))
        return route(prompt, system)

    llm.calls = calls
    return llm


class ApiJobBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old_jobs = server._jobs
        server._jobs = JobStore(self._tmp)

    def tearDown(self):
        server._jobs = self._old_jobs
        shutil.rmtree(self._tmp, ignore_errors=True)

    def wait(self, job_id, timeout=15.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = server.get_job_status(job_id)
            if status["status"] in ("complete", "failed"):
                return status
            time.sleep(0.02)
        self.fail(f"job {job_id} did not finish: {server.get_job_status(job_id)}")

    def ratified(self, codebook=CODEBOOK):
        return server.ratify_codebook(codebook=codebook)["ratification_id"]


class TestApiCodebookJob(ApiJobBase):
    def test_codebook_job_extracts_refines_and_records_provenance(self):
        def route(prompt, system):
            if "Extract codes from the text below" in prompt:
                return EXTRACTION
            return "[]"  # synthesis: nothing to change

        llm = scripted_llm(route)
        docs = {"fieldnote_a.txt": "Members pool money each month. " * 5,
                "fieldnote_b.txt": "The clinic closed and nobody came. " * 5}
        with mock.patch.object(server, "_api_llm", lambda model=None: llm), \
                mock.patch.object(codebook_mod, "_default_embedder", one_hot_embedder):
            start = server.start_codebook_job(docs, "interpretive", llm_mode="api")
            self.assertEqual(start["mode"], "api")
            status = self.wait(start["job_id"])

        self.assertEqual(status["status"], "complete", status)
        self.assertGreater(status["processed"], 0)
        result = server.get_job_result(start["job_id"])
        self.assertTrue(result["ready"])
        labels = {r["code_label"] for r in result["records"]}
        self.assertEqual(labels, {"ROTATING_SAVINGS", "STATE_ABSENCE"})
        self.assertEqual(result["quality_report"]["validation"]["stance"], "interpretive")
        sidecar = server._jobs.load_artifact(start["job_id"], server._checks.PROVENANCE_SIDECAR)
        self.assertIn("ROTATING_SAVINGS", sidecar)
        # The finished api-mode codebook can be ratified and governs coding.
        rat = server.ratify_codebook(codebook_job_id=start["job_id"])
        self.assertEqual(rat["codes"], 2)

    def test_model_failure_marks_the_job_failed_with_the_reason(self):
        def route(prompt, system):
            raise RuntimeError("overloaded_error: upstream at capacity")

        with mock.patch.object(server, "_api_llm", lambda model=None: scripted_llm(route)):
            start = server.start_codebook_job({"a.txt": "Some text here."},
                                              "interpretive", llm_mode="api")
            status = self.wait(start["job_id"])
        self.assertEqual(status["status"], "failed")
        self.assertIn("overloaded_error", status["error"])
        result = server.get_job_result(start["job_id"])
        self.assertFalse(result["ready"])
        self.assertIn("overloaded_error", result["error"])

    def test_unknown_lens_is_refused_before_a_job_exists(self):
        with self.assertRaises(ValueError):
            server.start_codebook_job({"a.txt": "x"}, "no-such-lens", llm_mode="api")
        self.assertEqual(os.listdir(self._tmp), [])


class TestApiModeWithoutKey(ApiJobBase):
    def test_missing_key_fails_the_job_with_actionable_guidance(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            start = server.start_coding_job(CHUNKS, CODEBOOK,
                                            ratification_id=self.ratified(),
                                            llm_mode="api")
            status = self.wait(start["job_id"])
        self.assertEqual(status["status"], "failed")
        # Before the fix the error was the bare KeyError text "'ANTHROPIC_API_KEY'".
        self.assertIn("delegated", status["error"])

    def test_default_mode_follows_the_environment(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}):
            self.assertEqual(server._mode(""), "api")
            self.assertEqual(server.toolkit_info()["llm_mode_default"], "api")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            self.assertEqual(server._mode(None), "delegated")
            self.assertEqual(server._mode("api"), "api")


class TestApiCodingJob(ApiJobBase):
    @staticmethod
    def _deductive(prompt, system):
        if "pool money" in prompt:
            return "mutual_aid"
        if "clinic closed" in prompt:
            return "state_absence, invented_code"
        if "NOT in the valid codebook" in prompt:
            return "state_absence"
        return "NO_CODES"

    def test_deductive_job_codes_every_chunk_against_the_codebook(self):
        llm = scripted_llm(self._deductive)
        with mock.patch.object(server, "_api_llm", lambda model=None: llm):
            start = server.start_coding_job(CHUNKS, CODEBOOK,
                                            ratification_id=self.ratified(),
                                            lens_key="interpretive", llm_mode="api")
            status = self.wait(start["job_id"])
        self.assertEqual(status["status"], "complete", status)
        self.assertEqual(status["processed"], 3)
        records = server.get_job_result(start["job_id"])["records"]
        by_id = {r["chunk_id"]: r for r in records}
        self.assertEqual(by_id[1]["Deductive_Codes"], "mutual_aid")
        self.assertEqual(by_id[2]["Deductive_Codes"], "state_absence")
        self.assertEqual(by_id[3]["Coding_Status"], "No_Codes")
        sidecar = json.loads(server._jobs.load_artifact(
            start["job_id"], server._checks.PROVENANCE_SIDECAR))
        self.assertEqual(sidecar["ratification_id"],
                         server._jobs.read(start["job_id"])["payload"]["ratification_id"])

    def test_hybrid_job_adds_inductive_codes(self):
        def route(prompt, system):
            if "INDUCTIVE CODING" in prompt:
                return ("**INDUCTIVE CODE: INFORMAL_CREDIT**\n"
                        "Definition: Lending outside formal institutions\n"
                        "Rationale: Recurs across speakers\n"
                        'Example: "we pool money"\n'
                        "When to Apply: When money moves through personal ties\n")
            if system and "INDUCTIVE CODES" in system:
                return "INFORMAL_CREDIT" if "pool money" in prompt else "NONE"
            return self._deductive(prompt, system)

        with mock.patch.object(server, "_api_llm", lambda model=None: scripted_llm(route)):
            start = server.start_coding_job(CHUNKS, CODEBOOK,
                                            ratification_id=self.ratified(),
                                            approach="hybrid", llm_mode="api")
            status = self.wait(start["job_id"])
        self.assertEqual(status["status"], "complete", status)
        first = server.get_job_result(start["job_id"])["records"][0]
        self.assertEqual(first["Coding_Status"], "Both_Deductive_Inductive")
        self.assertIn("INFORMAL_CREDIT_IND", first["All_Codes"])

    def test_failure_after_a_checkpoint_is_not_served_as_a_result(self):
        many = [{"chunk_id": i, "text": f"We pool money, round {i}."} for i in range(20)]
        calls = {"n": 0}

        def route(prompt, system):
            calls["n"] += 1
            if calls["n"] > 16:  # after the checkpoint at chunk 15 is written
                raise ConnectionError("connection reset by peer")
            return "mutual_aid"

        with mock.patch.object(server, "_api_llm", lambda model=None: scripted_llm(route)):
            start = server.start_coding_job(many, CODEBOOK,
                                            ratification_id=self.ratified(),
                                            llm_mode="api")
            status = self.wait(start["job_id"])
        self.assertEqual(status["status"], "failed")
        # A checkpoint exists on disk...
        self.assertIsNotNone(server._jobs.load_artifact(start["job_id"], "result.json"))
        # ...but the result tool must not present it as the job's output.
        result = server.get_job_result(start["job_id"])
        self.assertFalse(result["ready"])
        self.assertNotIn("records", result)
        self.assertIn("connection reset", result["error"])

    def test_bad_approach_is_refused(self):
        with self.assertRaises(ValueError):
            server.start_coding_job(CHUNKS, CODEBOOK, ratification_id=self.ratified(),
                                    approach="grounded", llm_mode="api")

    def test_hybrid_falls_back_to_deductive_in_delegated_mode(self):
        start = server.start_coding_job(CHUNKS, CODEBOOK,
                                        ratification_id=self.ratified(),
                                        approach="hybrid", llm_mode="delegated")
        state = server._jobs.read(start["job_id"])
        self.assertEqual(state["payload"]["approach"], "deductive")


class TestApiThemes(ApiJobBase):
    CODED = [
        {"chunk_id": 1, "text": "t1", "Deductive_Codes": "MUTUAL_AID",
         "Inductive_Codes": "", "All_Codes": "MUTUAL_AID",
         "Coding_Status": "Deductive_Only"},
        {"chunk_id": 2, "text": "t2", "Deductive_Codes": "MUTUAL_AID, STATE_ABSENCE",
         "Inductive_Codes": "", "All_Codes": "MUTUAL_AID, STATE_ABSENCE",
         "Coding_Status": "Deductive_Only"},
    ]

    def test_api_mode_returns_parsed_themes(self):
        completion = ("Theme 1: Collective provisioning\n"
                      "Description: Households compensate for state absence by "
                      "pooling resources.\n"
                      "Supporting Codes: MUTUAL_AID, STATE_ABSENCE\n")
        llm = scripted_llm(lambda p, s: completion)
        with mock.patch.object(server, "_api_llm", lambda model=None: llm):
            out = server.build_themes(coded=self.CODED, lens_key="interpretive",
                                      llm_mode="api")
        self.assertEqual(len(llm.calls), 1)
        self.assertGreaterEqual(len(out["themes"]), 1)
        self.assertIn("MUTUAL_AID", out["themes"][0]["codes"])
        self.assertIn("patterns", out)

    def test_themes_from_a_job_id_and_refusal_without_input(self):
        rat = self.ratified()
        start = server.start_coding_job(CHUNKS, CODEBOOK, ratification_id=rat,
                                        llm_mode="delegated")
        batch = server.get_next_batch(start["job_id"], batch_size=10)
        server.submit_batch(start["job_id"], [
            {"id": p["id"], "response": "mutual_aid"} for p in batch["packets"]])
        out = server.build_themes(job_id=start["job_id"], llm_mode="delegated")
        self.assertIn("delegated_prompt", out)
        with self.assertRaises(ValueError):
            server.build_themes(llm_mode="delegated")


class TestJobStoreConcurrency(unittest.TestCase):
    def test_readers_never_see_a_half_written_state(self):
        # An api-mode worker updates job.json while the server answers
        # get_job_status from another thread. Before writes were atomic, a
        # reader could catch the file truncated and fail with JSONDecodeError.
        import threading

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        store = JobStore(tmp)
        job_id = store.create("coding", {"blob": "x" * 200_000})
        stop = threading.Event()

        def writer():
            n = 0
            while not stop.is_set():
                n += 1
                store.update(job_id, processed=n)

        t = threading.Thread(target=writer)
        t.start()
        try:
            for _ in range(400):
                store.status(job_id)  # raises if it reads a partial file
        finally:
            stop.set()
            t.join()
        self.assertEqual([p for p in os.listdir(os.path.join(tmp, job_id))
                          if p.endswith(".tmp")], [])


class TestDelegatedProvenance(ApiJobBase):
    def test_delegated_coding_records_its_ratification(self):
        rat = self.ratified()
        start = server.start_coding_job(CHUNKS, CODEBOOK, ratification_id=rat,
                                        llm_mode="delegated")
        batch = server.get_next_batch(start["job_id"], batch_size=10)
        server.submit_batch(start["job_id"], [
            {"id": p["id"], "response": "mutual_aid"} for p in batch["packets"]])
        sidecar = json.loads(server._jobs.load_artifact(
            start["job_id"], server._checks.PROVENANCE_SIDECAR))
        self.assertEqual(sidecar["ratification_id"], rat)


class TestJobResultReadiness(ApiJobBase):
    def test_delegated_coding_is_not_ready_until_every_packet_is_in(self):
        start = server.start_coding_job(CHUNKS, CODEBOOK,
                                        ratification_id=self.ratified(),
                                        llm_mode="delegated")
        job_id = start["job_id"]
        first = server.get_next_batch(job_id, batch_size=1)["packets"]
        server.submit_batch(job_id, [{"id": first[0]["id"], "response": "mutual_aid"}])
        partial = server.get_job_result(job_id)
        self.assertFalse(partial["ready"])
        self.assertEqual(partial["status"]["processed"], 1)
        rest = server.get_next_batch(job_id, batch_size=10)["packets"]
        server.submit_batch(job_id, [{"id": p["id"], "response": "NO_CODES"} for p in rest])
        self.assertTrue(server.get_job_result(job_id)["ready"])

    def test_unknown_job_kind_is_refused_on_submit(self):
        rid = self.ratified()  # a ratification job, which takes no batches
        with self.assertRaises(ValueError):
            server.submit_batch(rid, [{"id": "0", "response": "x"}])


class TestCompareLensesFromJobs(ApiJobBase):
    def _coded_job(self, response):
        start = server.start_coding_job(CHUNKS, CODEBOOK,
                                        ratification_id=self.ratified(),
                                        lens_key="interpretive", llm_mode="delegated")
        batch = server.get_next_batch(start["job_id"], batch_size=10)
        server.submit_batch(start["job_id"], [
            {"id": p["id"], "response": response} for p in batch["packets"]])
        return start["job_id"]

    def test_job_ids_carry_codebooks_and_ratifications(self):
        a = self._coded_job("mutual_aid")
        b = self._coded_job("mutual_aid, state_absence")
        out = server.compare_lenses(job_ids={"interpretive": a, "critical": b})
        self.assertIn("agreement_matrix", out)
        rids = out["vocabulary"]["ratification_ids"]
        self.assertEqual(set(rids), {"interpretive", "critical"})
        self.assertTrue(all(rids.values()))

    def test_missing_job_is_tolerated_and_one_lens_is_refused(self):
        a = self._coded_job("mutual_aid")
        out = server.compare_lenses(job_ids={"interpretive": a, "critical": "coding-gone"})
        self.assertEqual(out["vocabulary"]["ratification_ids"]["critical"], "")
        with self.assertRaises(ValueError):
            server.compare_lenses(results_by_lens={"only": []})


if __name__ == "__main__":
    unittest.main()
