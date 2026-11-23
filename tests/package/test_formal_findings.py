"""The defects the formal models in formal/ found, one test each, on the real server code.

Each test names the theorem (formal/AatModel/*.lean) or the TLC row (formal/tla/check.sh) that
covers its rule for every input or every order of steps; the test holds the code to it on one.

    python3 -m unittest tests.package.test_formal_findings -v
"""

import json
import multiprocessing
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.mcp import server

sys.path.insert(0, str(Path(__file__).resolve().parent))
import desk_helpers  # noqa: E402

CODEBOOK = [{"code_label": "trust", "definition": "Relying on others."},
            {"code_label": "risk", "definition": "Exposure to harm."}]
CHUNKS = [{"chunk_id": f"c{i}", "text": f"Chunk {i}."} for i in range(4)]


def _code(label):
    return json.dumps([{"label": label, "definition": f"{label} defined", "extraction_type": "emergent",
                        "example": "an example"}])


class StoreBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old = server._jobs
        server._jobs = JobStore(self._tmp)

    def tearDown(self):
        server._jobs = self._old
        shutil.rmtree(self._tmp, ignore_errors=True)

    def coding_job(self, chunks=CHUNKS):
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        return server.start_coding_job(chunks, ratification_id=rid, llm_mode="delegated")["job_id"]

    def codebook_job(self, docs=None):
        docs = docs or {"d1": "alpha " * 40, "d2": "beta " * 40}
        return server.start_codebook_job(docs, "interpretive", llm_mode="delegated", min_frequency=2)["job_id"]


class TestSubmitBatch(StoreBase):
    """Submit.lean: new_complete_is_honest, new_only_issued, new_counts_once,
    new_complete_is_final, new_refuses_api_jobs."""

    def test_an_id_the_job_never_issued_is_refused_and_does_not_complete_it(self):
        # old_completes_with_unanswered / new_refuses_unissued
        job = self.coding_job()
        with self.assertRaisesRegex(ValueError, "zz1, zz2"):
            server.submit_batch(job, [{"id": "c0", "response": "trust"},
                                      {"id": "zz1", "response": "x"}, {"id": "zz2", "response": "x"},
                                      {"id": "zz3", "response": "x"}])
        self.assertEqual(server.get_job_status(job)["processed"], 0)  # the refusal wrote nothing
        server.submit_batch(job, [{"id": "c0", "response": "trust"}])
        self.assertEqual(server.get_job_status(job)["status"], "in_progress")
        self.assertFalse(server.get_job_result(job)["ready"])

    def test_an_api_job_takes_no_batches(self):
        # old_completes_api_job / new_refuses_api_jobs
        gate = threading.Event()
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        with mock.patch.dict(os.environ, {"AAT_MODE": "api"}), \
                mock.patch.object(server, "_api_llm", lambda model=None: lambda *a, **k: (gate.wait(5), "trust")[1]):
            job = server.start_coding_job(CHUNKS, ratification_id=rid)["job_id"]
            try:
                with self.assertRaisesRegex(ValueError, "api mode"):
                    server.submit_batch(job, [{"id": "c0", "response": "risk"}])
                self.assertEqual(server.get_job_status(job)["status"], "in_progress")
            finally:
                gate.set()
                deadline = time.time() + 10  # let the worker finish before the store goes
                while server.get_job_status(job)["status"] == "in_progress" and time.time() < deadline:
                    time.sleep(0.02)

    def test_a_codebook_packet_sent_twice_is_counted_once(self):
        # old_counts_twice / new_counts_resend_once
        job = self.codebook_job()
        first = server.get_next_batch(job, 10)["packets"][0]["id"]
        server.submit_batch(job, [{"id": first, "response": _code("trust")}])
        out = server.submit_batch(job, [{"id": first, "response": _code("trust")}])
        self.assertEqual(out["already_submitted"], [first])
        self.assertEqual([(e["label"], e["frequency"]) for e in server._codebook_entries(job)], [("TRUST", 1)])

    def test_a_complete_job_takes_no_more_batches(self):
        # old_takes_after_complete / new_complete_is_final
        job = self.codebook_job()
        packets = server.get_next_batch(job, 10)["packets"]
        server.submit_batch(job, [{"id": p["id"], "response": _code("trust")} for p in packets])
        before = server._jobs.load_artifact(job, "result.json")
        with self.assertRaisesRegex(ValueError, "already complete"):
            server.submit_batch(job, [{"id": packets[0]["id"], "response": _code("risk")}])
        self.assertEqual(server._jobs.load_artifact(job, "result.json"), before)

    def test_interviews_chunked_separately_are_coded_chunk_by_chunk(self):
        # old_duplicate_ids_never_complete: chunk_transcript numbers each transcript's chunks
        # from 1, so two interviews share chunk IDs. Each chunk now gets a packet of its own.
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        chunks = [{"chunk_id": n, "text": f"{who} {n}", "source_file": who}
                  for who in ("ana.txt", "ben.txt") for n in (1, 2)]
        job = server.start_coding_job(chunks, ratification_id=rid, llm_mode="delegated")["job_id"]
        packets = server.get_next_batch(job, 10)["packets"]
        self.assertEqual(len({p["id"] for p in packets}), 4)
        answers = ["trust", "risk", "NO_CODES", "trust, risk"]
        server.submit_batch(job, [{"id": p["id"], "response": a} for p, a in zip(packets, answers)])
        result = server.get_job_result(job)
        self.assertTrue(result["ready"])
        self.assertEqual([(r["source_file"], r["chunk_id"], r["Deductive_Codes"]) for r in result["records"]],
                         [("ana.txt", 1, "trust"), ("ana.txt", 2, "risk"), ("ben.txt", 1, ""),
                          ("ben.txt", 2, "trust, risk")])
        with mock.patch.dict(os.environ, {"AAT_MODE": "api"}), \
                mock.patch.object(server, "_run_api_job", lambda job_id, worker: None):
            self.assertEqual(server.start_coding_job(chunks, ratification_id=rid)["mode"], "api")

    def test_a_batch_resent_after_a_failed_refinement_is_counted_once(self):
        # tla: Count no-ledger CountedOnce FAIL, current PASS. Refinement can fail (an
        # embedding model that cannot be downloaded raises OSError) after the merge is kept.
        job = self.codebook_job()
        packets = server.get_next_batch(job, 10)["packets"]
        batch = [{"id": p["id"], "response": _code("trust")} for p in packets]
        real = server._codebook.refine_codebook
        with mock.patch.object(server._codebook, "refine_codebook", side_effect=OSError("offline")):
            for _ in range(2):
                with self.assertRaises(OSError):
                    server.submit_batch(job, batch)
        with mock.patch.object(server._codebook, "refine_codebook", real):
            out = server.submit_batch(job, batch)
        self.assertEqual(out["remaining"], 0)
        self.assertEqual(server.get_job_status(job)["status"], "complete")
        self.assertEqual([(e["label"], e["frequency"]) for e in server._codebook_entries(job)], [("TRUST", 2)])

    def test_two_batches_at_once_keep_every_code(self):
        # tla: Submit unlocked DoneHasCodes FAIL, current PASS. Slow the store's writes so the
        # two calls overlap on every run, as they did in 30 of 200 unforced runs.
        real = JobStore.save_artifact

        def slow(store, job_id, name, content):
            time.sleep(0.01)
            return real(store, job_id, name, content)

        with mock.patch.object(JobStore, "save_artifact", slow):
            for _ in range(5):
                job = self.coding_job()
                calls = [threading.Thread(target=server.submit_batch, args=(job, [
                    {"id": f"c{k}", "response": "trust"} for k in ks])) for ks in ((0, 1), (2, 3))]
                for t in calls:
                    t.start()
                for t in calls:
                    t.join()
                coded = {r["chunk_id"]: r["Deductive_Codes"] for r in server.get_job_result(job)["records"]}
                self.assertEqual(coded, {f"c{i}": "trust" for i in range(4)})


class TestRatify(StoreBase):
    """Ratify.lean: new_ratifies_only_finished_codebooks, new_held_never_changes."""

    def test_only_a_finished_codebook_job_is_ratified(self):
        # old_ratifies_coding_job / new_refuses_coding_job
        job = self.coding_job()
        server.submit_batch(job, [{"id": "c0", "response": "trust"}])
        with self.assertRaisesRegex(ValueError, "not a codebook job"):
            server.ratify_codebook(codebook_job_id=job)
        unfinished = self.codebook_job()
        with self.assertRaisesRegex(ValueError, "no result yet"):
            server.ratify_codebook(codebook_job_id=unfinished)

    def test_a_ratification_id_names_one_codebook(self):
        # old_ratification_drifts / new_refuses_rebinding: a job finished and ratified under an
        # earlier version, whose result a late batch then rewrote
        job = self.codebook_job()
        packets = server.get_next_batch(job, 10)["packets"]
        server.submit_batch(job, [{"id": p["id"], "response": _code("trust")} for p in packets])
        first = server.ratify_codebook(codebook_job_id=job)
        self.assertEqual(server.ratify_codebook(codebook_job_id=job)["checksum"], first["checksum"])
        rewritten = json.loads(server._jobs.load_artifact(job, "result.json")) + [
            {"code_label": "RISK", "definition": "late"}]
        server._jobs.save_artifact(job, "result.json", json.dumps(rewritten))
        with self.assertRaisesRegex(ValueError, "already ratified"):
            server.ratify_codebook(codebook_job_id=job)
        held = json.loads(server._jobs.load_artifact(job, "ratification.json"))
        self.assertEqual(held["checksum"], first["checksum"])


class TestDeskLists(StoreBase):
    def test_rulings_desks_built_at_once_are_all_listed(self):
        # tla: DeskList unlocked DesksKept FAIL, current PASS
        job = self.codebook_job()
        packets = server.get_next_batch(job, 10)["packets"]
        server.submit_batch(job, [{"id": p["id"], "response": _code("trust")} for p in packets])
        rid = server.ratify_codebook(codebook_job_id=job)["ratification_id"]
        passes = []
        for answer in ("TRUST", "NO_CODES"):
            coding = server.start_coding_job(CHUNKS[:2], ratification_id=rid, llm_mode="delegated")["job_id"]
            server.submit_batch(coding, [{"id": c["chunk_id"], "response": answer} for c in CHUNKS[:2]])
            passes.append(coding)
        real = JobStore.save_artifact

        def slow(store, job_id, name, content):
            if name == "ratification.json":
                time.sleep(0.05)
            return real(store, job_id, name, content)

        with mock.patch.object(JobStore, "save_artifact", slow):
            built = []
            calls = [threading.Thread(target=lambda: built.append(server._build_desk(
                "rulings", "", "", None, None, passes, None, True).structured_content["desk_id"]))
                for _ in range(2)]
            calls.append(threading.Thread(target=server.ratify_codebook, kwargs={"codebook_job_id": job}))
            for t in calls:
                t.start()
            for t in calls:
                t.join()
        held = json.loads(server._jobs.load_artifact(rid, "ratification.json"))
        self.assertEqual(sorted(held["desks"]), sorted(built))


class TestDeskResend(StoreBase):
    def test_resending_an_interrupted_finish_keeps_desks_built_on_its_ratification(self):
        # tla: DeskList resend-rewrites DesksKept FAIL, current PASS
        from ai_anthro_toolkit.desk import gate
        built = server._build_desk("codebook", "t", "", desk_helpers.load("codebook"),
                                   desk_helpers.load("cases"), None, None, True).structured_content
        desk_id = built["desk_id"]
        desk = server._jobs.read(desk_id)["payload"]
        doc = {"schema": "aat/desk-decisions@1", "desk_id": desk_id, "card_checksum": desk["card_checksum"],
               "exclusive": False, "decisions": {c["card_id"]: {"action": "adopt"} for c in desk["cards"]}}
        with mock.patch.object(gate.record, "append", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                server.record_desk_decisions(desk_id, doc, "chat")
        rid = json.loads(server._jobs.load_artifact(desk_id, "finishing.json") or "{}")["ratification_id"]
        codes = [r["code_label"] for r in json.loads(server._jobs.load_artifact(rid, "result.json") or "[]")]
        passes = []
        for answer in (codes[0], "NO_CODES"):
            coding = server.start_coding_job(CHUNKS[:2], ratification_id=rid, llm_mode="delegated")["job_id"]
            server.submit_batch(coding, [{"id": c["chunk_id"], "response": answer} for c in CHUNKS[:2]])
            passes.append(coding)
        rulings = server._build_desk("rulings", "", "", None, None, passes, None, True).structured_content["desk_id"]
        self.assertEqual(server.record_desk_decisions(desk_id, doc, "chat")["ratification_id"], rid)
        held = json.loads(server._jobs.load_artifact(rid, "ratification.json") or "{}")
        self.assertEqual(held["desks"], [rulings])


class TestJobLock(StoreBase):
    def test_one_folder_reached_by_two_spellings_is_one_lock(self):
        # On a case-insensitive disk two roots can name one folder; nesting their locks in one
        # thread must not wait on itself.
        job = self.coding_job()
        other = JobStore(self._tmp.upper() if Path(self._tmp.upper()).exists() else self._tmp + "/.")
        finished = threading.Event()

        def nested():
            with server._jobs.locked(job), other.locked(job):
                finished.set()

        worker = threading.Thread(target=nested, daemon=True)
        worker.start()
        worker.join(5)
        self.assertTrue(finished.is_set(), "the second spelling of the folder waited on the first")


def _finish_in_another_process(root, desk_id, doc, answers, both_decided):
    store = JobStore(root)
    real = store.create

    def slow(kind, payload):
        # Both callers have decided to mint before either writes: the overlap the TLC trace
        # needs. When the job lock keeps the other caller out, the wait times out and this
        # caller goes on alone.
        made = real(kind, payload)
        try:
            both_decided.wait(3)
        except threading.BrokenBarrierError:
            pass
        return made

    store.create = slow  # type: ignore[method-assign]
    server._jobs = store
    try:
        answers.put(server.record_desk_decisions(desk_id, doc, "chat")["ratification_id"])
    except ValueError as exc:
        answers.put(f"refused: {exc}")


class TestDeskAcrossProcesses(StoreBase):
    def test_two_server_processes_cannot_both_finish_a_desk(self):
        # tla: Desk two-processes RecordNamesFinished / ToldWhatHolds FAIL, current PASS
        built = server._build_desk("codebook", "t", "", desk_helpers.load("codebook"),
                                   desk_helpers.load("cases"), None, None, True).structured_content
        desk = server._jobs.read(built["desk_id"])["payload"]
        docs = [{"schema": "aat/desk-decisions@1", "desk_id": built["desk_id"],
                 "card_checksum": desk["card_checksum"], "exclusive": exclusive,
                 "decisions": {c["card_id"]: {"action": "adopt"} for c in desk["cards"]}}
                for exclusive in (True, False)]
        context = multiprocessing.get_context("spawn")
        answers = context.Queue()
        both_decided = context.Barrier(2)
        procs = [context.Process(target=_finish_in_another_process,
                                 args=(self._tmp, built["desk_id"], doc, answers, both_decided)) for doc in docs]
        for p in procs:
            p.start()
        for p in procs:
            p.join(60)
        told = [answers.get(timeout=5) for _ in procs]
        ratified = [t for t in told if not t.startswith("refused")]
        self.assertEqual(len(ratified), 1, told)
        finished = json.loads(server._jobs.load_artifact(built["desk_id"], "finished.json"))
        record = [e["detail"]["ratification_id"] for e in server._desk_record.read(server._jobs, built["desk_id"])
                  if e["action"] == "ratify"]
        self.assertEqual(record, [finished["outcome"]["ratification_id"]])
        self.assertEqual(ratified, record)


if __name__ == "__main__":
    unittest.main()
