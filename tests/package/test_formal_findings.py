"""The defects the formal models in formal/ found, one test each, on the real server code.

Each test names the theorem (formal/AatModel/*.lean) or the TLC row (formal/tla/check.sh) that
covers its rule for every input or every order of steps; the test holds the code to it on one.

    python3 -m unittest tests.package.test_formal_findings -v
"""

import errno
import json
import multiprocessing
import os
import shutil
import subprocess  # noqa: S404
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

    def test_two_updates_at_once_keep_both_fields(self):
        # job.json is read, changed and written; two calls at once lost one's field.
        from ai_anthro_toolkit import jobs
        job = self.coding_job()
        real = jobs._write_atomic

        def slow(path, content):
            time.sleep(0.05)
            return real(path, content)

        with mock.patch.object(jobs, "_write_atomic", slow):
            calls = [threading.Thread(target=server._jobs.update, args=(job,), kwargs={k: 1})
                     for k in ("first", "second")]
            for t in calls:
                t.start()
            for t in calls:
                t.join()
        state = server._jobs.read(job)
        self.assertEqual((state.get("first"), state.get("second")), (1, 1))

    def test_analyze_network_refuses_an_unknown_network_as_view_network_does(self):
        job = self.coding_job()
        for network_id in (job, "network-00000000"):
            with self.subTest(network_id):
                viewed = server.view_network(network_id=network_id)
                with self.assertRaises(ValueError) as analyzed:
                    server.analyze_network(network_id=network_id)
                self.assertEqual(str(analyzed.exception), viewed.content[0].text)

    def test_two_analyses_of_one_network_take_turns(self):
        # analyze_network reads a network's graph, lays it out and writes it back.
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        job = server.start_coding_job(CHUNKS, ratification_id=rid, llm_mode="delegated")["job_id"]
        server.submit_batch(job, [{"id": c["chunk_id"], "response": "trust, risk"} for c in CHUNKS])
        network_id = server.build_network(job_id=job)["network_id"]
        real, inside, most = server._network.analyze_network, [0], [0]
        guard = threading.Lock()

        def slow(*args, **kwargs):
            with guard:
                inside[0] += 1
                most[0] = max(most[0], inside[0])
            time.sleep(0.1)
            try:
                return real(*args, **kwargs)
            finally:
                with guard:
                    inside[0] -= 1

        with mock.patch.object(server._network, "analyze_network", slow):
            calls = [threading.Thread(target=server.analyze_network, kwargs={"network_id": network_id, "seed": s})
                     for s in (1, 2)]
            for t in calls:
                t.start()
            for t in calls:
                t.join()
        self.assertEqual(most[0], 1)

    def test_a_call_waits_for_the_lock_only_so_long(self):
        # A call held up behind a slow one (a refinement downloading an embedding model) is
        # refused after LOCK_TIMEOUT, with nothing recorded, rather than waiting for ever.
        from ai_anthro_toolkit import jobs
        job = self.coding_job()
        holding, release = threading.Event(), threading.Event()

        def hold():
            with server._jobs.locked(job):
                holding.set()
                release.wait(5)

        holder = threading.Thread(target=hold, daemon=True)
        holder.start()
        holding.wait(5)
        try:
            with mock.patch.object(jobs, "LOCK_TIMEOUT", 0.2):
                started = time.monotonic()
                with self.assertRaisesRegex(RuntimeError, "try again"):
                    server.submit_batch(job, [{"id": "c0", "response": "trust"}])
                self.assertLess(time.monotonic() - started, 2)
        finally:
            release.set()
            holder.join(5)
        self.assertIsNone(server._jobs.load_artifact(job, "done_ids.json"))

    @unittest.skipIf(sys.platform == "win32", "flock")
    def test_a_call_waits_for_another_process_only_so_long(self):
        from ai_anthro_toolkit import jobs
        job = self.coding_job()
        lock = Path(self._tmp) / job / ".lock"
        script = ("import fcntl, sys\n"
                  f"fh = open({str(lock)!r}, 'a')\n"
                  "fcntl.flock(fh, fcntl.LOCK_EX)\n"
                  "print('held', flush=True)\n"
                  "sys.stdin.read()\n")
        other = subprocess.Popen([sys.executable, "-c", script], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(other.stdout.readline().strip(), "held")
            with mock.patch.object(jobs, "LOCK_TIMEOUT", 0.3), self.assertRaisesRegex(RuntimeError, "try again"):
                with server._jobs.locked(job):
                    pass
        finally:
            other.stdin.close()
            other.wait(5)
            other.stdout.close()
        with server._jobs.locked(job):  # released with the other process
            pass

    def test_a_file_system_without_locks_is_named(self):
        # A network share mounted without lock support refuses flock (ENOLCK); the call says
        # where the job store is and what to do, rather than relaying the bare errno.
        from ai_anthro_toolkit import jobs
        if jobs.fcntl is None:
            self.skipTest("flock")
        job = self.coding_job()
        for code in (errno.ENOLCK, errno.ENOTSUP, errno.EOPNOTSUPP):
            with self.subTest(errno.errorcode[code]):
                with mock.patch.object(jobs.fcntl, "flock", side_effect=OSError(code, "no locks")):
                    with self.assertRaisesRegex(RuntimeError, "local disk") as caught:
                        with server._jobs.locked(job):
                            pass
                self.assertIn(str(self._tmp), str(caught.exception))
        # Any other failure is relayed as it is, not taken for a held lock or a lockless disk.
        with mock.patch.object(jobs.fcntl, "flock", side_effect=OSError(errno.EIO, "I/O error")):
            with self.assertRaises(OSError) as caught:
                with server._jobs.locked(job):
                    pass
        self.assertEqual(caught.exception.errno, errno.EIO)
        with server._jobs.locked(job):  # nothing was left held
            pass

    def test_windows_holds_against_other_processes(self):
        # Without fcntl the lock is msvcrt's byte-range lock on the job's .lock file, which
        # Windows enforces across processes (and over SMB, on the server).
        from ai_anthro_toolkit import jobs
        job = self.coding_job()
        calls = []

        class FakeMsvcrt:
            LK_NBLCK, LK_UNLCK = 2, 0
            busy = 2  # another process holds it for two tries

            @classmethod
            def locking(cls, fd, mode, nbytes):
                calls.append((mode, nbytes))
                if mode == cls.LK_NBLCK and cls.busy:
                    cls.busy -= 1
                    raise OSError(errno.EACCES, "locked")

        with mock.patch.object(jobs, "fcntl", None), mock.patch.object(jobs, "msvcrt", FakeMsvcrt):
            with server._jobs.locked(job):
                self.assertEqual(calls, [(2, 1)] * 3)
            self.assertEqual(calls[-1], (0, 1))
            FakeMsvcrt.busy = 10**6
            with mock.patch.object(jobs, "LOCK_TIMEOUT", 0.2), self.assertRaisesRegex(RuntimeError, "try again"):
                with server._jobs.locked(job):
                    pass

def _finish_in_another_process(root, desk_id, doc, answers, both_decided):
    store = JobStore(root)
    real = store.new_id

    def slow(kind):
        # Both callers have decided to mint before either writes: the overlap the TLC trace
        # needs. When the job lock keeps the other caller out, the wait times out and this
        # caller goes on alone.
        made = real(kind)
        try:
            both_decided.wait(3)
        except threading.BrokenBarrierError:
            pass
        return made

    store.new_id = slow  # type: ignore[method-assign]
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


def _earlier_release_submit(job, pid, label):
    """What submit_batch in 3.11.1 (before ledger.json) does with one codebook packet: merge
    its code into entries.json by label, adding one to the code's frequency (it does not ask
    whether the packet was merged before), and record the packet in done_ids.json."""
    entries = json.loads(server._jobs.load_artifact(job, "entries.json") or "[]")
    doc = pid.split("::")[0]
    same = next((e for e in entries if e["label"] == label), None)
    if same is None:
        entries.append({"label": label, "definition": "d", "extraction_type": "emergent", "frequency": 1,
                        "source_documents": [doc], "examples": []})
    else:
        same["frequency"] += 1
        same["source_documents"] = sorted(set(same["source_documents"]) | {doc})
    done = json.loads(server._jobs.load_artifact(job, "done_ids.json") or "[]")
    server._jobs.save_artifact(job, "entries.json", json.dumps(entries))
    server._jobs.save_artifact(job, "done_ids.json", json.dumps(sorted(set(done) | {pid})))


class TestEarlierReleases(StoreBase):
    """Jobs an earlier release wrote, or shares. Submit.lean: new_keeps_answered,
    new_refuses_repeated_queue, new_reopens_early_complete; tla: Count mixed-versions."""

    def test_a_codebook_job_shared_with_an_earlier_release_keeps_every_code(self):
        # fix1_loses_stale_ledger: an earlier release merges a packet into entries.json without
        # ledger.json; the next batch here started from the stale ledger and lost that code.
        job = self.codebook_job({"d1": "alpha " * 40, "d2": "beta " * 40, "d3": "gamma " * 40})
        ids = [p["id"] for p in server.get_next_batch(job, 10)["packets"]]
        self.assertEqual(len(ids), 3)
        server.submit_batch(job, [{"id": ids[0], "response": _code("alpha")}])
        _earlier_release_submit(job, ids[1], "ALPHA")
        out = server.submit_batch(job, [{"id": ids[2], "response": _code("gamma")}])
        self.assertEqual(out["remaining"], 0)
        self.assertEqual(sorted((e["label"], e["frequency"]) for e in server._codebook_entries(job)),
                         [("ALPHA", 2), ("GAMMA", 1)])

    def test_a_codebook_batch_that_died_between_its_two_writes_is_counted_once(self):
        # tla: Count current CountedOnce/Kept PASS. The call dies after ledger.json and before
        # entries.json; sent again, the batch is taken from ledger.json, which a server reading
        # entries.json instead would get wrong (it would lose ALPHA).
        job = self.codebook_job({"d1": "alpha " * 40, "d2": "beta " * 40})
        ids = [p["id"] for p in server.get_next_batch(job, 10)["packets"]]
        real = JobStore.save_artifact

        def dies_at_entries(store, job_id, name, content):
            if name == "entries.json":
                raise OSError("disk full")
            return real(store, job_id, name, content)

        with mock.patch.object(JobStore, "save_artifact", dies_at_entries):
            with self.assertRaises(OSError):
                server.submit_batch(job, [{"id": ids[0], "response": _code("alpha")}])
        server.submit_batch(job, [{"id": ids[0], "response": _code("alpha")}])
        server.submit_batch(job, [{"id": ids[1], "response": _code("beta")}])
        self.assertEqual(sorted((e["label"], e["frequency"]) for e in server._codebook_entries(job)),
                         [("ALPHA", 1), ("BETA", 1)])

    def test_a_batch_that_died_before_entries_keeps_its_codes_when_an_earlier_release_ran_since(self):
        # fix2_takes_unwritten_as_merged / new_merges_unwritten; tla: Count union Kept FAIL, current
        # Kept PASS. The call dies after ledger.json and before entries.json; an earlier release
        # then answers another packet; sent again, ALPHA was taken as merged and was in no file.
        job = self.codebook_job({"d1": "alpha " * 40, "d2": "beta " * 40, "d3": "gamma " * 40})
        ids = [p["id"] for p in server.get_next_batch(job, 10)["packets"]]
        real = JobStore.save_artifact

        def dies_at_entries(store, job_id, name, content):
            if name == "entries.json":
                raise OSError("disk full")
            return real(store, job_id, name, content)

        with mock.patch.object(JobStore, "save_artifact", dies_at_entries):
            with self.assertRaises(OSError):
                server.submit_batch(job, [{"id": ids[0], "response": _code("alpha")}])
        _earlier_release_submit(job, ids[1], "BETA")
        server.submit_batch(job, [{"id": ids[0], "response": _code("alpha")}])
        server.submit_batch(job, [{"id": ids[2], "response": _code("gamma")}])
        self.assertEqual(sorted((e["label"], e["frequency"]) for e in server._codebook_entries(job)),
                         [("ALPHA", 1), ("BETA", 1), ("GAMMA", 1)])

    def test_a_batch_whose_refinement_failed_is_not_served_to_an_earlier_release(self):
        # tla: Count union-resent CountedOnce FAIL, current PASS. Refinement raises on the last
        # batch (an embedding model that cannot be downloaded). Its packets are recorded as
        # answered before refinement, so an earlier release's get_next_batch, which serves the
        # packets done_ids.json lacks, does not serve them again to be merged twice.
        job = self.codebook_job()
        ids = [p["id"] for p in server.get_next_batch(job, 10)["packets"]]
        server.submit_batch(job, [{"id": ids[0], "response": _code("alpha")}])
        with mock.patch.object(server._codebook, "refine_codebook", side_effect=RuntimeError("no model")):
            with self.assertRaisesRegex(RuntimeError, "no model"):
                server.submit_batch(job, [{"id": ids[1], "response": _code("beta")}])
        done = set(json.loads(server._jobs.load_artifact(job, "done_ids.json")))
        queue = json.loads(server._jobs.load_artifact(job, "queue.json"))
        self.assertEqual([p["id"] for p in queue if p["id"] not in done], [])
        self.assertEqual(server.get_job_status(job)["status"], "in_progress")
        self.assertFalse(server.get_job_result(job)["ready"])

    def test_a_codebook_whose_refinement_failed_is_built_by_an_empty_batch(self):
        # Every packet answered, the codebook not built: get_next_batch says so, and
        # submit_batch with no results builds it without counting anything again.
        job = self.codebook_job()
        ids = [p["id"] for p in server.get_next_batch(job, 10)["packets"]]
        with mock.patch.object(server._codebook, "refine_codebook", side_effect=RuntimeError("no model")):
            with self.assertRaises(RuntimeError):
                server.submit_batch(job, [{"id": i, "response": _code("alpha")} for i in ids])
        nxt = server.get_next_batch(job, 10)
        self.assertEqual((nxt["packets"], nxt["done"]), ([], False))
        self.assertIn("submit_batch with an empty list", nxt["note"])
        out = server.submit_batch(job, [])
        self.assertEqual(out["remaining"], 0)
        self.assertEqual(server.get_job_status(job)["status"], "complete")
        self.assertTrue(server.get_job_result(job)["ready"])
        self.assertEqual([(e["label"], e["frequency"]) for e in server._codebook_entries(job)], [("ALPHA", 2)])
        self.assertTrue(server.get_next_batch(job, 10)["done"])

    def test_a_job_with_no_packets_gets_no_note_to_finish_it(self):
        # Nothing failed: a delegated job with nothing to answer, or before its packets are
        # queued, is not told its last batch failed.
        job = server._jobs.create("codebook", {"mode": "delegated"})
        nxt = server.get_next_batch(job)
        self.assertEqual((nxt["packets"], nxt["done"], "note" in nxt), ([], True, False))

    def test_a_coding_job_that_died_before_its_status_is_finished_by_an_empty_batch(self):
        job = self.coding_job()
        packets = server.get_next_batch(job, 10)["packets"]
        with mock.patch.object(server._jobs, "update", side_effect=OSError("the process died")):
            with self.assertRaises(OSError):
                server.submit_batch(job, [{"id": p["id"], "response": "trust"} for p in packets])
        nxt = server.get_next_batch(job, 10)
        self.assertEqual((nxt["packets"], nxt["done"]), ([], False))
        self.assertIn("submit_batch with an empty list", nxt["note"])
        self.assertEqual(server.submit_batch(job, [])["remaining"], 0)
        self.assertEqual(server.get_job_status(job)["status"], "complete")
        self.assertEqual([r["Deductive_Codes"] for r in server.get_job_result(job)["records"]],
                         ["trust"] * len(packets))

    def test_a_codebook_batch_that_failed_writing_done_ids_is_counted_once(self):
        # tla: Count one-release (CrashW2): entries.json written, done_ids.json not (disk full).
        job = self.codebook_job({"d1": "alpha " * 40, "d2": "beta " * 40})
        ids = [p["id"] for p in server.get_next_batch(job, 10)["packets"]]
        real = JobStore.save_artifact

        def fails_at_done(store, job_id, name, content):
            if name == "done_ids.json":
                raise OSError("disk full")
            return real(store, job_id, name, content)

        with mock.patch.object(JobStore, "save_artifact", fails_at_done), self.assertRaises(OSError):
            server.submit_batch(job, [{"id": ids[0], "response": _code("alpha")}])
        server.submit_batch(job, [{"id": ids[0], "response": _code("alpha")}])
        server.submit_batch(job, [{"id": ids[1], "response": _code("beta")}])
        self.assertEqual(sorted((e["label"], e["frequency"]) for e in server._codebook_entries(job)),
                         [("ALPHA", 1), ("BETA", 1)])

    def test_an_api_job_gets_no_note_to_finish_it(self):
        job = server._jobs.create("coding", {"mode": "api"})
        nxt = server.get_next_batch(job)
        self.assertEqual((nxt["packets"], nxt["done"], "note" in nxt), ([], True, False))

    def _repeated_ids_job(self):
        """A coding job an earlier release started on two interviews: one packet ID per chunk_id,
        so both chunks numbered 1 were issued as packet 1."""
        job = self.coding_job([{"chunk_id": "x", "text": "placeholder"}])
        chunks = [{"chunk_id": 1, "text": f"{who} one", "source_file": who} for who in ("ana.txt", "ben.txt")]
        server._jobs.save_artifact(job, "chunks.json", json.dumps(chunks))
        server._jobs.save_artifact(job, "queue.json", json.dumps([{"id": "1", "prompt": "p"}] * 2))
        return job

    def test_an_old_job_that_gave_two_chunks_one_packet_is_refused(self):
        # fix1_repeated_queue_completes / new_refuses_repeated_queue: the answer to packet 1
        # cannot be told apart, so it must not be written to both chunks.
        job = self._repeated_ids_job()
        with self.assertRaisesRegex(ValueError, "start the coding job again"):
            server.get_next_batch(job)
        with self.assertRaisesRegex(ValueError, "start the coding job again"):
            server.submit_batch(job, [{"id": "1", "response": "trust"}])
        self.assertIsNone(server._jobs.load_artifact(job, "result.json"))
        self.assertEqual(server.get_job_status(job)["status"], "in_progress")

    def test_an_old_job_marked_complete_too_early_can_be_finished(self):
        # fix1_stuck_on_unissued_done / new_drops_unissued_done: an earlier release counted
        # IDs it never issued as answered and marked the job complete with chunks uncoded.
        job = self.coding_job()
        server.submit_batch(job, [{"id": "c0", "response": "trust"}])
        server._jobs.save_artifact(job, "done_ids.json", json.dumps(["c0", "zz1", "zz2", "zz3"]))
        server._jobs.update(job, status="complete", processed=4)
        status = server.get_job_status(job)
        self.assertEqual((status["status"], status["processed"], status["total"]), ("in_progress", 1, 4))
        self.assertFalse(server.get_job_result(job)["ready"])
        packets = server.get_next_batch(job, 10)["packets"]
        self.assertEqual([p["id"] for p in packets], ["c1", "c2", "c3"])
        out = server.submit_batch(job, [{"id": p["id"], "response": "risk"} for p in packets])
        self.assertEqual(out["remaining"], 0)
        status = server.get_job_status(job)
        self.assertEqual((status["status"], status["processed"], status["pct"]), ("complete", 4, 100.0))
        coded = [r["Deductive_Codes"] for r in server.get_job_result(job)["records"]]
        self.assertEqual(coded, ["trust", "risk", "risk", "risk"])
        with self.assertRaisesRegex(ValueError, "already complete"):
            server.submit_batch(job, [{"id": "c0", "response": "risk"}])

    def test_a_codebook_job_completed_too_early_is_not_ratified(self):
        job = self.codebook_job()
        first = server.get_next_batch(job, 10)["packets"][0]["id"]
        server.submit_batch(job, [{"id": first, "response": _code("trust")}])
        server._jobs.save_artifact(job, "result.json", json.dumps([{"code_label": "TRUST", "definition": "d"}]))
        server._jobs.update(job, status="complete")
        with self.assertRaisesRegex(ValueError, "no result yet"):
            server.ratify_codebook(codebook_job_id=job)


class TestDeskNoOrphan(StoreBase):
    """tla: Desk mint-first NoOrphan FAIL, current NoOrphan PASS: a finish interrupted before
    finishing.json names its ratification leaves no ratification job behind."""

    def _desk(self):
        built = server._build_desk("codebook", "t", "", desk_helpers.load("codebook"),
                                   desk_helpers.load("cases"), None, None, True).structured_content
        desk_id = built["desk_id"]
        desk = server._jobs.read(desk_id)["payload"]
        doc = {"schema": "aat/desk-decisions@1", "desk_id": desk_id, "card_checksum": desk["card_checksum"],
               "exclusive": False, "decisions": {c["card_id"]: {"action": "adopt"} for c in desk["cards"]}}
        return desk_id, doc

    def _ratifications(self):
        return sorted(p.name for p in Path(self._tmp).iterdir()
                      if p.name.startswith("ratification-") and (p / "job.json").is_file())

    def _dies_writing(self, target):
        real = JobStore.save_artifact

        def dies(store, job_id, name, content):
            if name == target:
                raise OSError("the process died")
            return real(store, job_id, name, content)
        return mock.patch.object(JobStore, "save_artifact", dies)

    def test_dying_before_finishing_json_leaves_no_ratification(self):
        desk_id, doc = self._desk()
        before = self._ratifications()
        with self._dies_writing("finishing.json"), self.assertRaises(OSError):
            server.record_desk_decisions(desk_id, doc, "chat")
        self.assertEqual(self._ratifications(), before)
        rid = server.record_desk_decisions(desk_id, doc, "chat")["ratification_id"]
        self.assertEqual(self._ratifications(), sorted(before + [rid]))

    def test_dying_after_finishing_json_creates_the_ratification_it_names(self):
        desk_id, doc = self._desk()
        before = self._ratifications()
        with mock.patch.object(JobStore, "create", side_effect=OSError("the process died")), \
                self.assertRaises(OSError):
            server.record_desk_decisions(desk_id, doc, "chat")
        self.assertEqual(self._ratifications(), before)
        named = json.loads(server._jobs.load_artifact(desk_id, "finishing.json"))["ratification_id"]
        rid = server.record_desk_decisions(desk_id, doc, "chat")["ratification_id"]
        self.assertEqual(rid, named)
        self.assertEqual(self._ratifications(), sorted(before + [rid]))
        self.assertEqual(server._jobs.read(rid)["kind"], "ratification")

    def test_a_named_job_is_made_once_and_only_of_its_kind(self):
        rid = JobStore.new_id("ratification")
        self.assertEqual(server._jobs.create("ratification", {"codes": 1}, job_id=rid), rid)
        self.assertEqual(server._jobs.create("ratification", {"codes": 9}, job_id=rid), rid)
        self.assertEqual(server._jobs.read(rid)["payload"], {"codes": 1})
        with self.assertRaisesRegex(ValueError, "not an ID for a desk job"):
            server._jobs.create("desk", {}, job_id=rid)


class TestDeskInterruptedThenViewed(StoreBase):
    """tla: DeskView old NotStuck FAIL, current NotStuck PASS."""

    def _interrupted(self):
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
        self.assertIsNotNone(server._jobs.load_artifact(desk_id, "finishing.json"))
        return desk_id, doc

    def test_opening_the_view_after_an_interrupted_chat_finish_leaves_it_finishable(self):
        desk_id, doc = self._interrupted()
        server._sync(desk_id, None)  # the view opens the desk
        self.assertIsNone(server._jobs.load_artifact(desk_id, server._SAVED))
        out = server.record_desk_decisions(desk_id, doc, "chat")
        self.assertTrue(out["ratification_id"])
        self.assertIsNotNone(server._jobs.load_artifact(desk_id, "finished.json"))

    def test_the_view_says_where_an_interrupted_chat_finish_completes(self):
        desk_id, doc = self._interrupted()
        server._sync(desk_id, None)
        with self.assertRaisesRegex(ValueError, "from the conversation was interrupted.*record_desk_decisions"):
            server._sync(desk_id, {"name": "save", "context": {}})
        self.assertIsNone(server._jobs.load_artifact(desk_id, server._SAVED))

    def test_a_desk_an_earlier_release_left_stuck_can_be_finished(self):
        # The earlier view held the desk (saved.json) over the interrupted chat finish.
        desk_id, doc = self._interrupted()
        server._jobs.save_artifact(desk_id, server._SAVED, json.dumps(server._NOTHING_SAVED))
        out = server.record_desk_decisions(desk_id, doc, "chat")
        self.assertTrue(out["ratification_id"])

    def test_the_conversation_cannot_complete_a_finish_the_view_started(self):
        # tla: DeskView own-only ViewKeeps PASS, any-pending ViewKeeps FAIL
        from ai_anthro_toolkit.desk import gate
        built = server._build_desk("codebook", "t", "", desk_helpers.load("codebook"),
                                   desk_helpers.load("cases"), None, None, True).structured_content
        desk_id = built["desk_id"]
        desk = server._jobs.read(desk_id)["payload"]
        saved = {"decisions": {c["card_id"]: {"action": "adopt"} for c in desk["cards"]}, "exclusive": False}
        server._jobs.save_artifact(desk_id, server._SAVED, json.dumps(saved))  # the view decided
        with mock.patch.object(gate.record, "append", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                server._finish(desk_id)  # Ratify in the view, interrupted
        doc = server._document(desk_id, desk, saved)
        with self.assertRaisesRegex(ValueError, "open in its view"):
            server.record_desk_decisions(desk_id, doc, "chat")
        out = server._finish(desk_id)
        surfaces = {e["surface"] for e in server._desk_record.read(server._jobs, desk_id) if e["action"] == "ratify"}
        self.assertEqual((bool(out["ratification_id"]), surfaces), (True, {"app"}))

    def test_the_view_still_holds_a_desk_nobody_started_finishing(self):
        built = server._build_desk("codebook", "t", "", desk_helpers.load("codebook"),
                                   desk_helpers.load("cases"), None, None, True).structured_content
        desk_id = built["desk_id"]
        server._sync(desk_id, None)
        desk = server._jobs.read(desk_id)["payload"]
        doc = {"schema": "aat/desk-decisions@1", "desk_id": desk_id, "card_checksum": desk["card_checksum"],
               "exclusive": False, "decisions": {c["card_id"]: {"action": "adopt"} for c in desk["cards"]}}
        with self.assertRaisesRegex(ValueError, "open in its view"):
            server.record_desk_decisions(desk_id, doc, "chat")


class TestSeveralInterviewsDownstream(StoreBase):
    """Packets.lean packet_ids_distinct: each coded record carries its packet ID, and the
    rulings desk, compare_lenses and the lens network key on it."""

    CHUNKS = [{"chunk_id": n, "text": f"{who} says {n}", "source_file": who}
              for who in ("ana.txt", "ben.txt") for n in (1, 2)]

    def _coded(self, rid, answers):
        job = server.start_coding_job(self.CHUNKS, ratification_id=rid, llm_mode="delegated")["job_id"]
        packets = server.get_next_batch(job, 10)["packets"]
        server.submit_batch(job, [{"id": p["id"], "response": a} for p, a in zip(packets, answers)])
        return job

    def test_two_coding_passes_over_several_interviews_reach_the_rulings_desk(self):
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        first = self._coded(rid, ["trust", "risk", "trust", "risk"])
        second = self._coded(rid, ["trust", "risk", "risk", "risk"])
        desk = server._build_desk("rulings", "", "", None, None, [first, second], None, True).structured_content
        cards = server._jobs.read(desk["desk_id"])["payload"]["cards"]
        self.assertEqual([c["text"] for c in cards], ["ben.txt says 1"])
        records = server.get_job_result(first)["records"]
        self.assertEqual(len({r.get("packet_id") for r in records}), 4)

    def test_two_passes_in_different_orders_match_chunk_to_chunk(self):
        # Packets.lean packet_ids_name_the_chunk, order_kept
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        first = self._coded(rid, ["trust", "risk", "trust", "risk"])
        flipped = self.CHUNKS[2:] + self.CHUNKS[:2]  # ben's interview first
        job = server.start_coding_job(flipped, ratification_id=rid, llm_mode="delegated")["job_id"]
        packets = server.get_next_batch(job, 10)["packets"]
        self.assertEqual([p["id"] for p in packets], ["ben.txt#1", "ben.txt#2", "ana.txt#1", "ana.txt#2"])
        server.submit_batch(job, [{"id": p["id"], "response": a}
                                  for p, a in zip(packets, ["risk", "risk", "trust", "risk"])])
        proposals = {"ben.txt#1": {"codes": ["trust"], "rationale": "first coder"}}
        desk = server._build_desk("rulings", "", "", None, None, [first, job], proposals, True).structured_content
        cards = server._jobs.read(desk["desk_id"])["payload"]["cards"]
        self.assertEqual([(c["chunk_id"], c["text"], c["proposal"]["codes"]) for c in cards],
                         [("ben.txt#1", "ben.txt says 1", ["trust"])])
        from ai_anthro_toolkit import network
        graph = network.build_network([], kind="lens_agreement", results_by_lens={
            "a": server.get_job_result(first)["records"], "b": server.get_job_result(job)["records"]})
        self.assertEqual([e["size"] for e in graph["edges"]], [3.0])  # 3 of 4 chunks share a code

    def test_passes_without_source_files_match_chunk_to_chunk(self):
        # Packets.lean packet_ids_name_the_chunk, order_kept_without_sources: chunks passed with
        # no source_file are named by their text, so the order of the interviews does not pair
        # ana's chunk 1 with ben's.
        bare = [{k: v for k, v in c.items() if k != "source_file"} for c in self.CHUNKS]
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        passes = []
        for chunks, answers in ((bare, ["trust", "risk", "trust", "risk"]),
                                (bare[2:] + bare[:2], ["risk", "risk", "trust", "risk"])):
            job = server.start_coding_job(chunks, ratification_id=rid, llm_mode="delegated")["job_id"]
            packets = server.get_next_batch(job, 10)["packets"]
            server.submit_batch(job, [{"id": p["id"], "response": a} for p, a in zip(packets, answers)])
            passes.append(job)
        first, second = ([r["packet_id"] for r in server.get_job_result(j)["records"]] for j in passes)
        self.assertEqual(sorted(first), sorted(second))
        self.assertTrue(all("~" in pid for pid in first))  # named by text, not by position
        desk = server._build_desk("rulings", "", "", None, None, passes, None, True).structured_content
        cards = server._jobs.read(desk["desk_id"])["payload"]["cards"]
        self.assertEqual([c["text"] for c in cards], ["ben.txt says 1"])

    def test_interviews_whose_files_share_a_name_match_chunk_to_chunk(self):
        # Packets.lean name_perm, same_file_name_kept: chunk_transcript keeps a file's base
        # name, so P01/transcript.txt and P02/transcript.txt are both transcript.txt; their
        # chunks are then named by their text too, not numbered by order.
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        p01, p02 = ([{"chunk_id": 1, "text": said, "source_file": "transcript.txt"}]  # as chunk_transcript gives
                    for said in ("Ana: I trust the clinic.", "Ben: The clinic is a risk."))
        passes = []
        for chunks, answers in ((p01 + p02, ["trust", "risk"]), (p02 + p01, ["trust", "risk"])):
            job = server.start_coding_job(chunks, ratification_id=rid, llm_mode="delegated")["job_id"]
            packets = server.get_next_batch(job, 10)["packets"]
            server.submit_batch(job, [{"id": p["id"], "response": a} for p, a in zip(packets, answers)])
            passes.append(job)
        desk = server._build_desk("rulings", "", "", None, None, passes, None, True).structured_content
        cards = server._jobs.read(desk["desk_id"])["payload"]["cards"]
        self.assertEqual(sorted(c["text"] for c in cards), sorted(c["text"] for c in p01 + p02))

    def test_records_coded_in_api_mode_carry_their_packet_ids(self):
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        with mock.patch.dict(os.environ, {"AAT_MODE": "api"}), \
                mock.patch.object(server, "_api_llm", lambda model=None: lambda *a, **k: "trust"), \
                mock.patch.object(server, "_run_api_job", lambda job_id, worker: worker()):
            job = server.start_coding_job(self.CHUNKS, ratification_id=rid)["job_id"]
        records = json.loads(server._jobs.load_artifact(job, "result.json"))
        self.assertEqual([r["packet_id"] for r in records],
                         ["ana.txt#1", "ana.txt#2", "ben.txt#1", "ben.txt#2"])

    def test_a_job_from_before_packet_ids_still_matches_a_new_one(self):
        # Records without packet_id are matched on chunk_id, which a single interview's new
        # job also gives as its packet IDs.
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        new = server.start_coding_job(CHUNKS, ratification_id=rid, llm_mode="delegated")["job_id"]
        server.submit_batch(new, [{"id": c["chunk_id"], "response": "trust"} for c in CHUNKS])
        old = [dict(r, Deductive_Codes="risk") for r in server.get_job_result(new)["records"]]
        for r in old:
            del r["packet_id"]
        out = server.compare_lenses(results_by_lens={"new": server.get_job_result(new)["records"], "old": old})
        self.assertEqual(len(out["per_chunk_agreement"]), 4)
        self.assertEqual(out["warnings"], [])

    def test_a_record_is_keyed_by_its_packet_id_then_its_chunk_id(self):
        from ai_anthro_toolkit.models import record_key
        self.assertEqual(record_key({"packet_id": "2:1", "chunk_id": 1}), "2:1")
        self.assertEqual(record_key({"packet_id": " ", "chunk_id": 0}), "0")
        self.assertEqual(record_key({"chunk_id": None}), "")

    def test_compare_lenses_and_the_lens_network_keep_the_interviews_apart(self):
        rid = server.ratify_codebook(codebook=CODEBOOK)["ratification_id"]
        first = self._coded(rid, ["trust", "risk", "trust", "risk"])
        second = self._coded(rid, ["trust", "risk", "risk", "risk"])
        out = server.compare_lenses(job_ids={"a": first, "b": second})
        kinds = {w["type"] for w in out["warnings"]}
        self.assertFalse(kinds & {"duplicate_chunk_id", "text_mismatch"}, out["warnings"])
        self.assertEqual(len(out["per_chunk_agreement"]), 4)
        from ai_anthro_toolkit import network
        graph = network.build_network([], kind="lens_agreement", results_by_lens={
            "a": server.get_job_result(first)["records"], "b": server.get_job_result(second)["records"]})
        self.assertEqual({n["key"]: n["attributes"]["chunks"] for n in graph["nodes"]}, {"a": 4, "b": 4})



if __name__ == "__main__":
    unittest.main()
