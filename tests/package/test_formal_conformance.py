"""Holds the server to the Lean models in formal/: `formal/vectors.json` is what the proved
rules (AatModel/Submit.lean `newSubmit`, AatModel/Ratify.lean `newRatify`) say on every small
case, printed by `lake exe vectors`; these tests run the real `submit_batch` and
`ratify_codebook` on each case and require the same verdict. They need no prover.
`formal/check.sh` regenerates the file and fails if the committed copy differs.

    python3 -m unittest tests.package.test_formal_conformance -v
"""

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ai_anthro_toolkit.crosslens import codebook_checksum
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.mcp import server

VECTORS = Path(__file__).resolve().parents[2] / "formal" / "vectors.json"
CODEBOOKS = {1: [{"code_label": "trust", "definition": "Relying on others."}],
             2: [{"code_label": "risk", "definition": "Exposure to harm."}]}
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
    if kind == "codebook" and done:
        server._jobs.save_artifact(job, "entries.json", json.dumps(
            [{"label": "TRUST", "definition": "d", "frequency": len(done)}]))
    server._jobs.update(job, status="complete" if case["complete"] else "in_progress")
    response = LABEL if kind == "codebook" else "trust"
    try:
        server.submit_batch(job, [{"id": str(x), "response": response} for x in case["submit"]])
    except ValueError:
        return {"refused": True}
    got = {"refused": False,
           "done": sorted(json.loads(server._jobs.load_artifact(job, "done_ids.json") or "[]")),
           "complete": server._jobs.read(job)["status"] == "complete"}
    if kind == "codebook":
        entries = json.loads(server._jobs.load_artifact(job, "entries.json") or "[]")
        got["counted"] = sum(e["frequency"] for e in entries)
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
    try:
        out = server.ratify_codebook(codebook_job_id=job)
    except ValueError:
        return {"refused": True}
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
        case = {k: raw[k] for k in ("queue", "delegated", "done", "complete", "submit", "refused")}
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
        for kind in ("coding", "codebook"):
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


if __name__ == "__main__":
    unittest.main()
