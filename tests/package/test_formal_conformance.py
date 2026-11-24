"""Holds the server to the Lean models in formal/: `formal/vectors.json` is what the proved
rules (AatModel/Submit.lean `newSubmit`, AatModel/Ratify.lean `newRatify`) say on every small
case, printed by `lake exe vectors`; these tests run the real `submit_batch` and
`ratify_codebook` on each case and require the same verdict. They need no prover.

A submit case may hold a job an earlier release wrote: a queue that repeats an id, a job marked
complete with packets unanswered, or a ledger (`ledger.json`) that counts a packet more or one
fewer than done_ids.json, or done_ids.json holding an id the job never issued. A ledger case is
seeded as the files stand in that state. ledger.json holds its counted packets merged. A ledger
that counts every answered packet is this release's own: its entries.json holds the answered
packets only, as when a call died after writing ledger.json and before entries.json, so a
server that read entries.json instead would count wrongly. A ledger that lacks an answered packet
is out of date: an earlier release, which writes entries.json but not ledger.json, merged since,
and entries.json is seeded with the packets done_ids.json records, as that release writes them
when neither of its two writes fails (formal/tla/Count.tla checks the failures); a packet the
ledger counted beyond them died here before reaching entries.json.
`formal/check.sh` regenerates the file and fails if the committed copy differs.

    python3 -m unittest tests.package.test_formal_conformance -v
"""

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_anthro_toolkit.crosslens import codebook_checksum
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.mcp import server

VECTORS = Path(__file__).resolve().parents[2] / "formal" / "vectors.json"
CODEBOOKS = {1: [{"code_label": "trust", "definition": "Relying on others."}],
             2: [{"code_label": "risk", "definition": "Exposure to harm."}]}
def _files(job):
    """The job's files and their contents: a refusal must leave them as they were."""
    folder = Path(server._jobs.root) / job
    return {f.name: f.read_bytes() for f in folder.iterdir() if f.name != ".lock"}


def _trust(frequency):
    return [{"label": "TRUST", "definition": "d", "frequency": frequency}] if frequency else []


LABEL = json.dumps([{"label": "trust", "definition": "d", "extraction_type": "emergent"}])


def _submit_case(case, kind):
    """What the server does with one case, in the model's terms."""
    ids = [str(q) for q in case["queue"]]
    payload = {"mode": "delegated" if case["delegated"] else "api", "lens_key": "interpretive",
               "valid_codes": ["TRUST"], "ratification_id": "", "min_frequency": 1,
               "similarity_threshold": 0.85, "auto_merge": False}
    job = server._jobs.create(kind, payload)
    server._jobs.save_artifact(job, "queue.json", json.dumps([{"id": i, "prompt": "p"} for i in ids]))
    server._jobs.save_artifact(job, "chunks.json", json.dumps([{"chunk_id": i, "text": "t"} for i in ids]))
    done = [str(d) for d in case["done"]]
    server._jobs.save_artifact(job, "done_ids.json", json.dumps(done))
    ledger = case["ledger"]
    if kind == "codebook":
        merged = len(set(done))
        if merged:
            server._jobs.save_artifact(job, "entries.json", json.dumps(_trust(merged)))
        if ledger is not None:
            server._jobs.save_artifact(job, "ledger.json", json.dumps(
                {"counted": [str(c) for c in ledger], "entries": _trust(len(ledger))}))
    server._jobs.update(job, status="complete" if case["complete"] else "in_progress")
    response = LABEL if kind == "codebook" else "trust"
    before = _files(job)
    try:
        server.submit_batch(job, [{"id": str(x), "response": response} for x in case["submit"]])
    except ValueError:
        return {"refused": True} if _files(job) == before else {"refused": True, "wrote": True}
    got = {"refused": False,
           "done": sorted(json.loads(server._jobs.load_artifact(job, "done_ids.json") or "[]")),
           "complete": server._jobs.read(job)["status"] == "complete"}
    if kind == "codebook":
        got["counted"] = sum(e["frequency"] for e in server._codebook_entries(job))
    return got


def _expected_submit(case, kind):
    if case["refused"]:
        return {"refused": True}
    want = {"refused": False, "done": sorted(str(d) for d in case["done_after"]),
            "complete": case["complete_after"]}
    if kind == "codebook":
        want["counted"] = len(case["counted"])
    return want


def _ratify_case(case):
    job = server._jobs.create(case["kind"], {"mode": "delegated"})
    server._jobs.update(job, status=case["status"])
    if case["result"] is not None:
        server._jobs.save_artifact(job, "result.json", json.dumps(CODEBOOKS[case["result"]]))
    if case["held"] is not None:
        server._jobs.save_artifact(job, "ratification.json", json.dumps(
            {"checksum": codebook_checksum(CODEBOOKS[case["held"]]), "codes": 1}))
    before = _files(job)
    try:
        out = server.ratify_codebook(codebook_job_id=job)
    except ValueError:
        return {"refused": True} if _files(job) == before else {"refused": True, "wrote": True}
    return {"refused": False, "checksum": out["checksum"]}


def _expected_ratify(case):
    if case["refused"]:
        return {"refused": True}
    return {"refused": False, "checksum": codebook_checksum(CODEBOOKS[case["held_after"]])}


def load_vectors():
    """The committed vectors, with each case's before and after kept apart."""
    data = json.loads(VECTORS.read_text(encoding="utf-8"))
    submit = []
    for raw in data["submit"]:
        case = {k: raw[k] for k in ("queue", "delegated", "done", "ledger", "complete", "submit", "refused")}
        if not raw["refused"]:
            case.update(done_after=raw["done_after"], counted=raw["counted"], complete_after=raw["complete_after"])
        submit.append(case)
    ratify = []
    for raw in data["ratify"]:
        case = {k: raw[k] for k in ("kind", "status", "result", "held", "refused")}
        if not raw["refused"]:
            case["held_after"] = raw["held_after"]
        ratify.append(case)
    return submit, ratify


def mismatches(submit, ratify):
    """Every case where the server and the model disagree."""
    found = []
    for case in submit:
        for kind in ("coding", "codebook") if case["ledger"] is None else ("codebook",):  # a coding job keeps no ledger
            got, want = _submit_case(case, kind), _expected_submit(case, kind)
            if got != want:
                found.append(("submit", kind, case, got, want))
    for case in ratify:
        got, want = _ratify_case(case), _expected_ratify(case)
        if got != want:
            found.append(("ratify", case, got, want))
    return found


class TestFormalConformance(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old = server._jobs
        server._jobs = JobStore(self._tmp)

    def tearDown(self):
        server._jobs = self._old
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_vectors_exist_and_cover_both_verdicts(self):
        submit, ratify = load_vectors()
        for cases in (submit, ratify):
            self.assertGreater(len(cases), 50)  # zero cases compared is not a pass
            self.assertEqual({c["refused"] for c in cases}, {True, False})
        accepted = [c for c in submit if not c["refused"]]
        # the earlier-release states are reached and accepted, not only refused
        self.assertTrue(any(c["complete"] for c in accepted))
        self.assertTrue(any(c["ledger"] is not None and set(c["done"]) - set(c["ledger"]) for c in accepted))
        self.assertTrue(any(c["ledger"] is not None and set(c["ledger"]) - set(c["done"]) for c in accepted))
        self.assertTrue(any(len(set(c["queue"])) < len(c["queue"]) for c in submit))

    def test_server_agrees_with_the_models_on_every_case(self):
        submit, ratify = load_vectors()
        found = mismatches(submit, ratify)
        self.assertEqual(found, [], f"{len(found)} disagreements; first: {found[:2]}")

    def test_a_flipped_verdict_is_caught(self):
        submit, ratify = load_vectors()
        planted_submit = copy.deepcopy(next(c for c in submit if not c["refused"]))
        planted_submit["complete_after"] = not planted_submit["complete_after"]
        planted_ratify = copy.deepcopy(next(c for c in ratify if c["refused"]))
        planted_ratify["refused"], planted_ratify["held_after"] = False, 1
        self.assertEqual(len(mismatches([planted_submit], [])), 2)  # coding and codebook
        self.assertEqual(len(mismatches([], [planted_ratify])), 1)

    def test_packet_ids_match_the_model(self):
        # Packets.lean packet_ids_distinct, packet_ids_keep_distinct_ids, packet_ids_name_the_chunk.
        # A packet is written: the chunk ID; "<source>#<id>"; "<id>~<first 12 hex digits of the
        # text's SHA-256>"; and a repeat of a name "/<n>" for its n-th chunk.
        cases = json.loads(VECTORS.read_text(encoding="utf-8"))["packets"]
        self.assertGreater(len(cases), 10)
        self.assertTrue(any(len({i for _, i, _ in c["chunks"]}) < len(c["chunks"]) for c in cases))
        kinds = {p[0] for c in cases for p in c["packets"]}
        self.assertEqual(kinds, {"plain", "sourced", "sourced_text", "content"})
        self.assertTrue(any(p[-1] > 0 for c in cases for p in c["packets"] if p[0] != "plain"))

        def text(t):
            return f"text {t}"

        def written(p):
            if p[0] == "plain":
                return str(p[1])
            def digest(t):
                return hashlib.sha256(text(t).encode()).hexdigest()[:12]
            name = {"sourced": lambda: f"s{p[1]}#{p[2]}",
                    "sourced_text": lambda: f"s{p[1]}#{p[2]}~{digest(p[3])}",
                    "content": lambda: f"{p[1]}~{digest(p[2])}"}[p[0]]()
            return name if p[-1] == 0 else f"{name}/{p[-1] + 1}"

        for case in cases:
            chunks = [{"chunk_id": i, "text": text(t), **({"source_file": f"s{src}"} if src else {})}
                      for src, i, t in case["chunks"]]
            self.assertEqual(server._packet_ids(chunks), [written(p) for p in case["packets"]], case)

    def test_packet_ids_are_written_as_documented(self):
        # The written form, fixed apart from the code: SHA-256 of "yes" begins 8a798890fe93.
        bare = [{"chunk_id": 1, "text": "yes"}, {"chunk_id": 1, "text": "no"}]
        self.assertEqual(server._packet_ids(bare), ["1~8a798890fe93", "1~9390298f3fb0"])
        same = [{"chunk_id": 1, "text": "yes", "source_file": "t.txt"}] * 2 + [
            {"chunk_id": 2, "text": "no", "source_file": "t.txt"}, {"chunk_id": 1, "text": "no", "source_file": "u.txt"}]
        self.assertEqual(server._packet_ids(same),
                         ["t.txt#1~8a798890fe93", "t.txt#1~8a798890fe93/2", "t.txt#2", "u.txt#1"])

    def test_ids_that_collide_as_strings_fall_back_to_positions(self):
        # Not modelled: the server numbers chunks by their written name; a numbered name that
        # another chunk's own name spells ("s#1~<digest of x>/2") leaves every chunk its position.
        x = hashlib.sha256(b"x").hexdigest()[:12]
        chunks = [{"chunk_id": "1", "text": "x", "source_file": "s"},
                  {"chunk_id": "1", "text": "x", "source_file": "s"},
                  {"chunk_id": f"1~{x}/2", "text": "y", "source_file": "s"}]
        self.assertEqual(server._packet_ids(chunks), ["0:1", "1:1", f"2:1~{x}/2"])

    def test_each_earlier_rule_is_caught(self):
        # The rules Submit.lean keeps as fix1Submit, each planted in the server, on the cases
        # that reach it: the vectors must tell every one from the fixed rule.
        submit, _ = load_vectors()
        real = server._submit_held

        def ledger_only(job_id, done_ids):  # fix1_loses_stale_ledger
            ledger = server._load_records(job_id, "ledger.json")
            if ledger is None:
                return server._load_records(job_id, "entries.json") or [], set(done_ids)
            return ledger["entries"], set(ledger["counted"])

        def entries_only(job_id, done_ids):  # never reads ledger.json's merge
            ledger = server._load_records(job_id, "ledger.json")
            counted = set(ledger["counted"]) if ledger else set()
            return server._load_records(job_id, "entries.json") or [], counted | set(done_ids)

        def union(job_id, done_ids):  # fix2_takes_unwritten_as_merged
            ledger = server._load_records(job_id, "ledger.json")
            if ledger is None:
                return server._load_records(job_id, "entries.json") or [], set(done_ids)
            counted = set(ledger["counted"])
            if done_ids <= counted:
                return ledger["entries"], counted
            return server._load_records(job_id, "entries.json") or [], counted | done_ids

        def complete_is_final(job_id, results):  # fix1_stuck_on_early_complete
            if server._jobs.read(job_id).get("status") == "complete":
                raise ValueError("already complete")
            return real(job_id, results)

        ledgered = [c for c in submit if c["ledger"] is not None and c["delegated"] and len(c["queue"]) >= 2][:120]
        plants = [
            ("ledger only", "_codebook_ledger", ledger_only, ledgered),
            ("counted and answered", "_codebook_ledger", union, ledgered),
            ("entries only", "_codebook_ledger", entries_only, ledgered),
            ("repeated queue taken", "_issued", lambda job_id: server._load_records(job_id, "queue.json") or [],
             [c for c in submit if len(set(c["queue"])) < len(c["queue"])]),
            ("complete is final", "_submit_held", complete_is_final, [c for c in submit if c["complete"]][:80]),
        ]
        for name, attr, planted, cases in plants:
            with self.subTest(name), mock.patch.object(server, attr, planted):
                self.assertTrue(mismatches(cases, []))

    def test_a_refusal_that_writes_is_caught(self):
        submit, ratify = load_vectors()
        refused = [c for c in submit if c["refused"]][:5]
        real = server._submit_held

        def writes_then_refuses(job_id, results):
            server._jobs.update(job_id, status="complete")
            return real(job_id, results)

        with mock.patch.object(server, "_submit_held", writes_then_refuses):
            self.assertTrue(mismatches(refused, []))


if __name__ == "__main__":
    unittest.main()
