"""The import gate: the one path by which decisions made at a desk enter the analysis."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ai_anthro_toolkit import crosslens
from ai_anthro_toolkit.desk import apply, cards, gate, methods, record
from ai_anthro_toolkit.desk.decisions import SCHEMA
from ai_anthro_toolkit.jobs import JobStore, UnknownJobError
from ai_anthro_toolkit.mcp import server
from tests.package.desk_helpers import codebook_desk, load, rulings_desk

CODEBOOK_DECISIONS = {
    "code-01": {"action": "adopt"},
    "code-02": {"action": "reword", "definition": "Talk of giving to those in need.", "note": "Narrower."},
    "code-03": {"action": "adopt"},
    "code-04": {"action": "adopt"},
    "code-05": {"action": "adopt"},
    "code-06": {"action": "adopt"},
}
RULINGS = {
    "chunk-7": {"codes": ["Shared labour"], "is_rule": True, "rule_text": "Shared work outweighs giving."},
    "chunk-9": {"codes": ["Land tenure", "Municipal relations"]},
    "chunk-11": {"exclude": {"reason": "Not about the garden."}},
    "chunk-12": {"none_apply": True, "is_rule": False, "note": "Planning talk."},
}


class GateCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.store = JobStore(Path(self._dir.name))

    def jobs(self, kind):
        return sorted(p.name for p in Path(self._dir.name).glob(f"locked/{kind}-*"))

    def codebook_desk(self, **changes):
        desk = codebook_desk(**changes)
        payload = {k: v for k, v in desk.items() if k != "desk_id"}
        desk_id = self.store.create("desk", dict(payload, card_checksum=cards.checksum(desk["cards"])))
        self.store.save_artifact(desk_id, "codebook.json", json.dumps(load("codebook")))
        return desk_id, desk["cards"]

    def doc(self, desk_id, desk_cards, decisions, exclusive=False, checksum=None):
        found = {"schema": SCHEMA, "desk_id": desk_id, "card_checksum": checksum or cards.checksum(desk_cards), "decisions": decisions}
        if exclusive is not None:
            found["exclusive"] = exclusive
        return found

    def ratified(self):
        """A codebook ratified on a desk: the ratification in force for a rulings desk."""
        desk_id, desk_cards = self.codebook_desk()
        outcome = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS), "app")
        return desk_id, outcome["ratification_id"]

    def rulings_desk(self, in_force):
        desk = rulings_desk()
        payload = {k: v for k, v in desk.items() if k != "desk_id"}
        payload.update(card_checksum=cards.checksum(desk["cards"]), ratification_id=in_force, agreed=8)
        desk_id = self.store.create("desk", payload)
        # The builder (task 14) lists a rulings desk under the ratification in force.
        held = json.loads(self.store.load_artifact(in_force, "ratification.json"))
        self.store.save_artifact(in_force, "ratification.json", json.dumps(dict(held, desks=[*held.get("desks", []), desk_id])))
        return desk_id, desk["cards"]

    def assert_nothing_written(self, desk_id, ratifications=()):
        self.assertEqual(self.jobs("ratification"), sorted(ratifications))
        self.assertEqual(record.read(self.store, desk_id), [])
        for name in ("finished.json", "finishing.json", "result.json"):
            self.assertIsNone(self.store.load_artifact(desk_id, name), name)


class TestRefusals(GateCase):
    def test_r5_2_changed_card_checksum_refused(self):
        desk_id, desk_cards = self.codebook_desk()
        doc = self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS, checksum="0123456789abcdef")
        with self.assertRaises(ValueError) as caught:
            gate.apply(self.store, desk_id, doc, "page")
        self.assertEqual(str(caught.exception), "These decisions cannot be applied:\n- These decisions were made on a different desk version.")
        self.assert_nothing_written(desk_id)

    def test_a_desk_whose_cards_no_longer_match_their_checksum_is_refused(self):
        desk_id, desk_cards = self.codebook_desk()
        self.store.update(desk_id, payload=dict(self.store.read(desk_id)["payload"], card_checksum="0123456789abcdef"))
        with self.assertRaisesRegex(ValueError, f"cards stored with {desk_id} no longer match their checksum"):
            gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS), "app")
        self.assert_nothing_written(desk_id)

    def test_r5_1_unknown_desk_refused(self):
        with self.assertRaises(UnknownJobError):
            gate.apply(self.store, "desk-00000000", {"schema": SCHEMA}, "app")
        with self.assertRaisesRegex(ValueError, "not a job ID"):
            gate.apply(self.store, "../desk", {"schema": SCHEMA}, "app")
        other = self.store.create("ratification", {})
        with self.assertRaisesRegex(ValueError, f"{other} is not a desk"):
            gate.apply(self.store, other, {"schema": SCHEMA}, "app")

    def test_r5_3_decision_for_card_not_on_desk_refused(self):
        desk_id, desk_cards = self.codebook_desk()
        doc = self.doc(desk_id, desk_cards, {**CODEBOOK_DECISIONS, "code-99": {"action": "adopt"}})
        with self.assertRaises(ValueError) as caught:
            gate.apply(self.store, desk_id, doc, "app")
        self.assertEqual(str(caught.exception), "These decisions cannot be applied:\n- code-99 is not a card on this desk.")
        self.assert_nothing_written(desk_id)

    def test_r2_6_missing_action_mints_nothing(self):
        desk_id, desk_cards = self.codebook_desk()
        partial = {k: v for k, v in CODEBOOK_DECISIONS.items() if k not in ("code-03", "code-05")}
        with self.assertRaises(ValueError) as caught:
            gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, partial, exclusive=None), "app")
        self.assertEqual(str(caught.exception), (
            "These decisions cannot be applied:\n- code-03: Land tenure has no decision.\n- code-05: Volunteer burnout has no decision.\n"
            "- The question whether the codes are mutually exclusive is unanswered."))
        self.assert_nothing_written(desk_id)

    def test_every_problem_is_named_at_once(self):
        desk_id, desk_cards = self.codebook_desk()
        bad = {**CODEBOOK_DECISIONS, "code-02": {"action": "reword", "definition": " "}, "code-04": {"action": "split", "parts": []}}
        with self.assertRaises(ValueError) as caught:
            gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, bad), "app")
        self.assertRegex(str(caught.exception), r"(?s)^These decisions cannot be applied:\n- code-02: .+\n- code-04: .+$")
        self.assert_nothing_written(desk_id)

    def test_a_document_of_another_shape_is_refused(self):
        desk_id, _ = self.codebook_desk()
        with self.assertRaisesRegex(ValueError, "not a decisions document"):
            gate.apply(self.store, desk_id, {"schema": "other"}, "app")
        self.assert_nothing_written(desk_id)

    def test_a_surface_the_desk_does_not_have_is_refused_before_anything_is_written(self):
        desk_id, desk_cards = self.codebook_desk()
        for surface in ("table", "server", "email"):
            with self.subTest(surface), self.assertRaisesRegex(ValueError, "app, page or chat"):
                gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS), surface)
        self.assert_nothing_written(desk_id)

    def test_a_result_the_codebook_cannot_hold_writes_nothing(self):
        desk_id, desk_cards = self.codebook_desk()
        clash = {**CODEBOOK_DECISIONS, "code-02": {"action": "reword", "definition": "Giving.", "label": "Food access"}}
        with self.assertRaisesRegex(ValueError, "code-02 gives the label 'Food access'"):
            gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, clash), "app")
        self.assert_nothing_written(desk_id)

    def test_a_codebook_desk_without_its_codebook_is_refused(self):
        desk = codebook_desk()
        desk_id = self.store.create("desk", dict({k: v for k, v in desk.items() if k != "desk_id"}, card_checksum=cards.checksum(desk["cards"])))
        with self.assertRaisesRegex(ValueError, "holds no codebook"):
            gate.apply(self.store, desk_id, self.doc(desk_id, desk["cards"], CODEBOOK_DECISIONS), "app")
        self.assert_nothing_written(desk_id)


class TestRefusalsThroughTheGate(GateCase):
    """Each check the gate relies on refuses through the gate itself, writing nothing."""

    def test_a_desk_missing_what_its_stage_needs_writes_nothing(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        self.store.update(desk_id, payload={k: v for k, v in self.store.read(desk_id)["payload"].items() if k != "agreed"})
        with self.assertRaisesRegex(ValueError, f"{desk_id} lacks agreed; build the desk again"):
            gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, RULINGS, exclusive=None), "app")
        self.assert_nothing_written(desk_id, [in_force])
        self.store.update(desk_id, payload=dict(self.store.read(desk_id)["payload"], stage="review"))
        with self.assertRaisesRegex(ValueError, "neither a codebook desk nor a rulings desk"):
            gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, RULINGS, exclusive=None), "app")

    def test_rulings_refusals(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        cases = {
            "The ruling differs from the proposal; say whether it states a rule": self.doc(
                desk_id, desk_cards, {**RULINGS, "chunk-12": {"none_apply": True}}, exclusive=None),
            "the codebook in force says they are not": self.doc(desk_id, desk_cards, RULINGS, exclusive=True),
            f"These decisions are for desk-00000000, not {desk_id}": dict(self.doc(desk_id, desk_cards, RULINGS, exclusive=None), desk_id="desk-00000000"),
            "chunk-7: .*'Garden politics'": self.doc(desk_id, desk_cards, {**RULINGS, "chunk-7": {"codes": ["Garden politics"], "is_rule": False}}, exclusive=None),
            "chunk-7: .*rule": self.doc(desk_id, desk_cards, {**RULINGS, "chunk-7": {"codes": ["Shared labour"], "is_rule": True, "rule_text": " "}}, exclusive=None),
        }
        for message, doc in cases.items():
            with self.subTest(message), self.assertRaisesRegex(ValueError, message):
                gate.apply(self.store, desk_id, doc, "app")
        self.assert_nothing_written(desk_id, [in_force])

    def test_a_code_without_an_action_is_refused(self):
        desk_id, desk_cards = self.codebook_desk()
        doc = self.doc(desk_id, desk_cards, {**CODEBOOK_DECISIONS, "code-04": {"note": "Not sure yet."}})
        with self.assertRaisesRegex(ValueError, "- code-04: "):
            gate.apply(self.store, desk_id, doc, "app")
        self.assert_nothing_written(desk_id)


class TestInterruptedFinish(GateCase):
    """A finish that stops part-way is completed by sending the same decisions again, with
    one ratification and one copy of each record entry."""

    def interrupt(self, target, desk_id, doc):
        with mock.patch.object(*target, side_effect=OSError("disk full")), self.assertRaises(OSError):
            gate.apply(self.store, desk_id, doc, "app")

    def test_a_finish_interrupted_before_the_record_resumes_with_one_ratification(self):
        desk_id, desk_cards = self.codebook_desk()
        doc = self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS)
        self.interrupt((record, "append"), desk_id, doc)
        [minted] = self.jobs("ratification")
        self.assertEqual(record.read(self.store, desk_id), [])
        outcome = gate.apply(self.store, desk_id, doc, "app")
        self.assertEqual(outcome["ratification_id"], minted)
        self.assertEqual(self.jobs("ratification"), [minted])
        self.assertEqual(len(record.read(self.store, desk_id)), 8)

    def test_a_finish_interrupted_after_the_record_appends_nothing_twice(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        doc = self.doc(desk_id, desk_cards, RULINGS, exclusive=None)
        real = self.store.save_artifact

        def fail_on_finish(job_id, name, content):
            if name == "finished.json":
                raise OSError("disk full")
            return real(job_id, name, content)

        with mock.patch.object(self.store, "save_artifact", side_effect=fail_on_finish), self.assertRaises(OSError):
            gate.apply(self.store, desk_id, doc, "app")
        entries = record.read(self.store, desk_id)
        self.assertEqual(len(entries), 5)
        outcome = gate.apply(self.store, desk_id, doc, "page")
        self.assertEqual(record.read(self.store, desk_id), entries)
        self.assertEqual(len(self.jobs("ratification")), 2)  # the codebook's and the amendment's
        self.assertEqual(entries[-1]["detail"]["ratification_id"], outcome["ratification_id"])

    def test_other_decisions_cannot_complete_an_interrupted_finish(self):
        desk_id, desk_cards = self.codebook_desk()
        self.interrupt((record, "append"), desk_id, self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS))
        minted = self.jobs("ratification")
        other = self.doc(desk_id, desk_cards, {**CODEBOOK_DECISIONS, "code-06": {"action": "delete"}})
        with self.assertRaisesRegex(ValueError, "with other decisions was interrupted; send those decisions again"):
            gate.apply(self.store, desk_id, other, "app")
        self.assertEqual(self.jobs("ratification"), minted)
        self.assertEqual(record.read(self.store, desk_id), [])


class TestCodingAcceptsWhatTheGateMints(GateCase):
    """R2.5: start_coding_job codes with a ratification the gate minted, from either desk."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(server, "_jobs", self.store)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_coding_accepts_a_desk_ratification_and_an_amended_one(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        amended = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, RULINGS, exclusive=None), "app")["ratification_id"]
        chunks = [{"chunk_id": 1, "text": "Saturdays we all turn the compost together."}]
        for rid in (in_force, amended):
            with self.subTest(rid):
                job = server.start_coding_job(chunks, ratification_id=rid, llm_mode="delegated")
                payload = self.store.read(job["job_id"])["payload"]
                self.assertEqual(payload["ratification_id"], rid)
                self.assertEqual(payload["valid_codes"], [r["code_label"] for r in load("codebook")])


class TestCodebookDesk(GateCase):
    def test_r2_7_the_ratified_codebook_is_the_result_of_the_actions(self):
        desk_id, desk_cards = self.codebook_desk()
        decided = {**CODEBOOK_DECISIONS, "code-03": {"action": "merge", "target": "Municipal relations"}, "code-05": {"action": "delete"}}
        outcome = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, decided, exclusive=True), "page")
        rid = outcome["ratification_id"]
        expected = apply.apply_actions(load("codebook"), desk_cards, decided)
        ratified = json.loads(self.store.load_artifact(rid, "result.json"))
        self.assertEqual(ratified, expected)
        self.assertEqual([r["code_label"] for r in ratified], ["Shared labour", "Charity framing", "Food access", "Municipal relations"])
        self.assertEqual(ratified[1]["definition"], "Talk of giving to those in need.")
        self.assertEqual(ratified[0], load("codebook")[0])
        self.assertEqual(json.loads(self.store.load_artifact(rid, "ratification.json")), {
            "checksum": crosslens.codebook_checksum(expected), "codes": 4, "note": "", "method": "desk",
            "version": "1.0", "parent": None, "desk_id": desk_id, "exclusive": True, "amendments": [], "desks": [],
        })
        self.assertEqual(self.store.read(rid)["status"], "complete")
        self.assertEqual(self.store.read(rid)["payload"], {"codes": 4})
        self.assertEqual(self.store.read(desk_id)["status"], "complete")
        self.assertEqual(outcome, {
            "desk_id": desk_id, "stage": "codebook", "ratification_id": rid, "version": "1.0",
            "checksum": crosslens.codebook_checksum(expected), "codes": 4,
            "next": "pass ratification_id to start_coding_job",
        })

    def test_r6_1_accepted_decisions_recorded(self):
        desk_id, desk_cards = self.codebook_desk()
        decided = {**CODEBOOK_DECISIONS, "code-05": {"action": "split", "note": "Two things.", "parts": [
            {"label": "Fatigue", "definition": "Being worn out."}, {"label": "Turnover", "definition": "People leaving."}]}}
        outcome = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, decided), "chat")
        entries = record.read(self.store, desk_id)
        self.assertEqual({(e["surface"], e["decided_by"], e["desk_id"]) for e in entries}, {("chat", "researcher", desk_id)})
        self.assertEqual(len({e["time"] for e in entries}), 1)
        self.assertEqual([(e["card_id"], e["action"], e["detail"], e["note"]) for e in entries], [
            ("code-01", "adopt", {}, ""),
            ("code-02", "reword", {"definition": "Talk of giving to those in need."}, "Narrower."),
            ("code-03", "adopt", {}, ""), ("code-04", "adopt", {}, ""),
            ("code-05", "split", {"parts": decided["code-05"]["parts"]}, "Two things."),
            ("code-06", "adopt", {}, ""),
            ("exclusivity", "answer_exclusive", {"exclusive": False}, ""),
            ("desk", "ratify", {"ratification_id": outcome["ratification_id"], "version": "1.0", "parent": None, "amendments": 0}, ""),
        ])

    def test_the_decisions_follow_what_the_builder_recorded(self):
        desk_id, desk_cards = self.codebook_desk()
        built = [{"card_id": "desk", "action": "build", "detail": {"stage": "codebook", "cards": 6}, "surface": "server", "decided_by": "machine"},
                 {"card_id": "code-01", "action": "draft", "detail": {"label": "Shared labour"}, "surface": "server", "decided_by": "machine"}]
        record.append(self.store, desk_id, built)
        gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS), "app")
        entries = record.read(self.store, desk_id)
        self.assertEqual([e["action"] for e in entries[:2]], ["build", "draft"])
        self.assertEqual(len(entries), 2 + 8)
        self.assertEqual(entries[-1]["action"], "ratify")

    def test_r5_6_same_decisions_twice_same_ratification(self):
        desk_id, desk_cards = self.codebook_desk()
        doc = self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS)
        first = gate.apply(self.store, desk_id, doc, "app")
        entries = record.read(self.store, desk_id)
        # The same decisions from another surface, with the keys in another order.
        reordered = dict(reversed(list(doc.items())), decisions=dict(reversed(list(doc["decisions"].items()))))
        again = gate.apply(self.store, desk_id, reordered, "page")
        self.assertEqual(again, first)
        self.assertEqual(record.read(self.store, desk_id), entries)
        self.assertEqual(self.jobs("ratification"), [first["ratification_id"]])

    def test_a_finished_desk_refuses_different_decisions(self):
        desk_id, desk_cards = self.codebook_desk()
        first = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS), "app")
        changed = {**CODEBOOK_DECISIONS, "code-06": {"action": "delete"}}
        with self.assertRaisesRegex(ValueError, f"already finished.*{first['ratification_id']}.*new desk"):
            gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, changed), "app")
        self.assertEqual(self.jobs("ratification"), [first["ratification_id"]])


class TestRulingsDesk(GateCase):
    def test_r5_4_incomplete_rulings_write_nothing(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        partial = {k: v for k, v in RULINGS.items() if k != "chunk-9"}
        with self.assertRaisesRegex(ValueError, "1 of 4 cards are still open."):
            gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, partial, exclusive=None), "app")
        self.assert_nothing_written(desk_id, [in_force])

    def test_rulings_without_a_rule_resolve_under_the_codebook_in_force(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        decided = {**RULINGS, "chunk-7": {"codes": ["Shared labour"], "is_rule": False}}
        outcome = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, decided, exclusive=None), "app")
        records, amendments = apply.resolve(desk_cards, decided)
        self.assertEqual(amendments, [])
        self.assertEqual(json.loads(self.store.load_artifact(desk_id, "result.json")), records)
        self.assertEqual(self.jobs("ratification"), [in_force])
        self.assertEqual(outcome, {"desk_id": desk_id, "stage": "rulings", "ratification_id": in_force, "version": "1.0",
                                   "resolved": 4, "amendments": 0})
        self.assertEqual(record.read(self.store, desk_id)[-1]["detail"],
                         {"ratification_id": in_force, "version": "1.0", "parent": None, "amendments": 0})

    def test_r4_1_to_r4_5_a_rule_amends_the_codebook_as_its_next_version(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        prior_records = self.store.load_artifact(in_force, "result.json")
        prior_ratification = json.loads(self.store.load_artifact(in_force, "ratification.json"))
        outcome = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, RULINGS, exclusive=None), "app")
        rid = outcome["ratification_id"]
        self.assertNotEqual(rid, in_force)
        amendment = {"amendment_id": "1.1-1", "from_version": "1.0", "to_version": "1.1", "rule_text": "Shared work outweighs giving.",
                     "source_card": "chunk-7", "desk_id": desk_id, "codes": ["Shared labour", "Charity framing", "Food access"]}
        amended = apply.amend(json.loads(prior_records), [amendment])
        self.assertEqual(json.loads(self.store.load_artifact(rid, "result.json")), amended)
        self.assertEqual(json.loads(self.store.load_artifact(rid, "ratification.json")), {
            "checksum": crosslens.codebook_checksum(amended), "codes": 6, "note": "", "method": "amendment", "version": "1.1",
            "parent": in_force, "desk_id": desk_id, "exclusive": False, "amendments": [amendment], "desks": [],
        })
        self.assertEqual(json.loads(self.store.load_artifact(desk_id, "result.json")), apply.resolve(desk_cards, RULINGS)[0])
        # R4.3: the prior version is kept as it was.
        self.assertEqual(self.store.load_artifact(in_force, "result.json"), prior_records)
        self.assertEqual(json.loads(self.store.load_artifact(in_force, "ratification.json")), prior_ratification)
        # R4.5: the agreed chunks are reported, not yet rechecked.
        self.assertEqual(outcome, {
            "desk_id": desk_id, "stage": "rulings", "ratification_id": rid, "version": "1.1", "resolved": 4, "amendments": 1,
            "parent": in_force, "checksum": crosslens.codebook_checksum(amended), "codes": 6,
            "agreed_unchecked": 8,
            "unchecked": "8 chunks both passes agreed on were coded under version 1.0 and have not been rechecked against the amendment.",
            "next": "pass ratification_id to start_coding_job",
        })

    def test_r6_1_rulings_recorded_and_the_methods_paragraph_reads_them(self):
        codebook_desk_id, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        outcome = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, RULINGS, exclusive=None), "page")
        entries = record.read(self.store, desk_id)
        self.assertEqual([(e["card_id"], e["action"], e["detail"], e["note"], e["surface"]) for e in entries], [
            ("chunk-7", "ruling", {"codes": ["Shared labour"], "departs": True, "is_rule": True, "rule_text": "Shared work outweighs giving."}, "", "page"),
            ("chunk-9", "ruling", {"codes": ["Land tenure", "Municipal relations"], "departs": False}, "", "page"),
            ("chunk-11", "exclude", {"reason": "Not about the garden."}, "", "page"),
            ("chunk-12", "ruling", {"none_apply": True, "departs": True, "is_rule": False}, "Planning talk.", "page"),
            ("desk", "ratify", {"ratification_id": outcome["ratification_id"], "version": "1.1", "parent": in_force,
                                "amendments": 1, "agreed_unchecked": 8}, "", "page"),
        ])
        # The builder (task 14) records the build, drafts and proposals; stand in for it here.
        record.append(self.store, desk_id, [{"card_id": "desk", "action": "build", "surface": "server", "decided_by": "machine",
                                            "detail": {"stage": "rulings", "cards": 4, "blind_first": True, "ratification_id": in_force}}])
        record.append(self.store, codebook_desk_id, [{"card_id": "desk", "action": "build", "surface": "server", "decided_by": "machine",
                                                     "detail": {"stage": "codebook", "cards": 6}}])
        lineage = record.read_lineage(self.store, outcome["ratification_id"])
        self.assertEqual(methods.paragraph(lineage), (
            f"{methods.LABEL} The researcher ratified a codebook of 6 codes on a codebook desk, deciding each code against "
            "the cases it would take: 5 adopted and 1 reworded. The researcher judged the codes not mutually exclusive. "
            "This made codebook version 1.0. A rulings desk presented 4 chunks on which two coding passes disagreed, with "
            "no model proposals. The researcher ruled on 3 and excluded 1 from the analysis. 1 was adopted as a rule, "
            "amending the codebook to version 1.1. 8 chunks on which both passes agreed were coded under version 1.0 and "
            "have not been rechecked against the amendment."
        ))

    def test_r5_6_the_same_rulings_twice_mint_one_amendment(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        doc = self.doc(desk_id, desk_cards, RULINGS, exclusive=None)
        first = gate.apply(self.store, desk_id, doc, "app")
        entries = record.read(self.store, desk_id)
        self.assertEqual(gate.apply(self.store, desk_id, doc, "chat"), first)
        self.assertEqual(record.read(self.store, desk_id), entries)
        self.assertEqual(self.jobs("ratification"), sorted([in_force, first["ratification_id"]]))

    def test_a_rulings_desk_under_a_table_ratification_starts_from_version_one(self):
        rid = self.store.create("ratification", {"codes": 6})
        self.store.save_artifact(rid, "result.json", json.dumps(load("codebook")))
        self.store.save_artifact(rid, "ratification.json", json.dumps(
            {"checksum": crosslens.codebook_checksum(load("codebook")), "codes": 6, "note": ""}))
        desk_id, desk_cards = self.rulings_desk(rid)
        outcome = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, RULINGS, exclusive=None), "app")
        self.assertEqual((outcome["version"], outcome["parent"]), ("1.1", rid))

    def test_a_second_rulings_desk_works_from_the_amended_version(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        amended = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, RULINGS, exclusive=None), "app")["ratification_id"]
        later_id, later_cards = self.rulings_desk(amended)
        no_rule = {**RULINGS, "chunk-7": {"codes": ["Shared labour"], "is_rule": False}}
        outcome = gate.apply(self.store, later_id, self.doc(later_id, later_cards, no_rule, exclusive=None), "app")
        self.assertEqual((outcome["ratification_id"], outcome["version"]), (amended, "1.1"))
        last = record.read(self.store, later_id)[-1]
        self.assertEqual((last["card_id"], last["action"], last["detail"]),
                         ("desk", "ratify", {"ratification_id": amended, "version": "1.1", "parent": in_force, "amendments": 0}))
        third_id, third_cards = self.rulings_desk(amended)
        outcome = gate.apply(self.store, third_id, self.doc(third_id, third_cards, RULINGS, exclusive=None), "app")
        self.assertEqual((outcome["version"], outcome["parent"]), ("1.2", amended))

    def test_an_amended_codebook_keeps_the_exclusivity_in_force(self):
        desk_id, desk_cards = self.codebook_desk()
        in_force = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, CODEBOOK_DECISIONS, exclusive=True), "app")["ratification_id"]
        rulings_id, rulings_cards = self.rulings_desk(in_force)
        self.store.update(rulings_id, payload=dict(self.store.read(rulings_id)["payload"], exclusive=True))
        single = {**RULINGS, "chunk-9": {"codes": ["Municipal relations"], "is_rule": False}, "chunk-12": {"codes": ["Shared labour"]}}
        outcome = gate.apply(self.store, rulings_id, self.doc(rulings_id, rulings_cards, single, exclusive=None), "app")
        self.assertIs(json.loads(self.store.load_artifact(outcome["ratification_id"], "ratification.json"))["exclusive"], True)

    def test_one_agreed_chunk_reads_in_the_singular(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        self.store.update(desk_id, payload=dict(self.store.read(desk_id)["payload"], agreed=1))
        outcome = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, RULINGS, exclusive=None), "app")
        self.assertEqual(outcome["unchecked"], "1 chunk both passes agreed on was coded under version 1.0 and has not been rechecked against the amendment.")

    def test_the_next_version_counts_past_nine(self):
        self.assertEqual(gate.next_version("1.9"), "1.10")
        self.assertEqual(gate.next_version("2.0"), "2.1")
        for bad in ("one", "1.x", "x.1", "1", "1.2.3"):
            with self.subTest(bad), self.assertRaisesRegex(ValueError, f"'{bad}' is not a codebook version"):
                gate.next_version(bad)

    def test_two_rules_are_numbered_in_card_order(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        decided = {**RULINGS, "chunk-12": {"none_apply": True, "is_rule": True, "rule_text": "Deciding is not labour."}}
        outcome = gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, decided, exclusive=None), "app")
        held = json.loads(self.store.load_artifact(outcome["ratification_id"], "ratification.json"))
        self.assertEqual([(a["amendment_id"], a["source_card"]) for a in held["amendments"]], [("1.1-1", "chunk-7"), ("1.1-2", "chunk-12")])
        self.assertTrue(outcome["unchecked"].endswith("against the 2 amendments."))

    def test_a_ruling_under_a_missing_ratification_is_refused(self):
        _, in_force = self.ratified()
        desk_id, desk_cards = self.rulings_desk(in_force)
        self.store.save_artifact(in_force, "result.json", "")
        with self.assertRaisesRegex(ValueError, f"in force, {in_force}, holds no codebook"):
            gate.apply(self.store, desk_id, self.doc(desk_id, desk_cards, RULINGS, exclusive=None), "app")
        self.assert_nothing_written(desk_id, [in_force])


if __name__ == "__main__":
    unittest.main()
