"""The decision record, the lineage behind a ratification, and the methods paragraph
assembled from it."""

import json
import tempfile
import unittest
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from ai_anthro_toolkit.desk import methods, record
from ai_anthro_toolkit.jobs import JobStore
from tests.package.desk_helpers import load

CODEBOOK_DESK, RULINGS_DESK = "desk-0a1b2c3d", "desk-9f8e7d6c"


def fixture():
    return load("record")


def clock(*stamps):
    """A now() that returns each stamp in turn."""
    times = iter(datetime(2026, 11, 15, 14, minute, tzinfo=UTC) for minute in stamps)
    return lambda: next(times)


class StoreCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.store = JobStore(Path(self._dir.name))

    def desk(self, stage="codebook"):
        return self.store.create("desk", {"stage": stage})

    def ratification(self, desk_id, parent=None, desks=()):
        rid = self.store.create("ratification", {})
        self.store.save_artifact(rid, "ratification.json", json.dumps(
            {"checksum": "0" * 16, "codes": 6, "desk_id": desk_id, "parent": parent, "desks": list(desks)}))
        return rid


class TestAppend(StoreCase):
    def test_r6_1_an_entry_carries_its_desk_card_action_note_time_surface_and_maker(self):
        desk = self.desk()
        record.append(self.store, desk, [
            {"card_id": "code-02", "action": "reword", "detail": {"definition": "Giving."}, "note": "Narrower.", "surface": "app", "decided_by": "researcher"},
        ], now=clock(5))
        self.assertEqual(record.read(self.store, desk), [{
            "desk_id": desk, "card_id": "code-02", "action": "reword", "detail": {"definition": "Giving."},
            "note": "Narrower.", "time": "2026-11-15T14:05:00Z", "surface": "app", "decided_by": "researcher",
        }])

    def test_appending_keeps_what_was_there(self):
        desk = self.desk()
        first = {"card_id": "code-01", "action": "adopt", "surface": "chat", "decided_by": "researcher"}
        second = {"card_id": "code-02", "action": "delete", "surface": "chat", "decided_by": "researcher"}
        record.append(self.store, desk, [first], now=clock(1))
        record.append(self.store, desk, [second], now=clock(2))
        entries = record.read(self.store, desk)
        self.assertEqual([(e["card_id"], e["time"]) for e in entries], [("code-01", "2026-11-15T14:01:00Z"), ("code-02", "2026-11-15T14:02:00Z")])
        self.assertEqual((entries[0]["detail"], entries[0]["note"]), ({}, ""))

    def test_one_time_stamps_one_append(self):
        desk = self.desk()
        entries = [{"card_id": f"code-0{n}", "action": "adopt", "surface": "page", "decided_by": "researcher"} for n in (1, 2)]
        record.append(self.store, desk, entries, now=clock(9))
        self.assertEqual({e["time"] for e in record.read(self.store, desk)}, {"2026-11-15T14:09:00Z"})

    def test_the_time_is_utc(self):
        desk = self.desk()
        eastern = datetime.fromisoformat("2026-11-15T09:30:00-05:00")
        record.append(self.store, desk, [{"card_id": "desk", "action": "build", "surface": "server", "decided_by": "machine"}], now=lambda: eastern)
        self.assertEqual(record.read(self.store, desk)[0]["time"], "2026-11-15T14:30:00Z")

    def test_an_entry_that_breaks_the_vocabulary_is_refused_and_nothing_is_written(self):
        desk = self.desk()
        good = {"card_id": "code-01", "action": "adopt", "surface": "app", "decided_by": "researcher"}
        cases = {
            "decided_by": dict(good, decided_by="model"),
            "surface": dict(good, surface="email"),
            "action": dict(good, action="approve"),
            "card_id": dict(good, card_id=""),
            "detail": dict(good, detail=["x"]),
            "note": dict(good, note=3),
            "unknown field": dict(good, decided="yes"),
        }
        for name, entry in cases.items():
            with self.subTest(name), self.assertRaisesRegex(ValueError, name.split()[0] if name != "unknown field" else "decided"):
                record.append(self.store, desk, [good, entry], now=clock(1))
        self.assertEqual(record.read(self.store, desk), [])

    def test_the_refusal_names_the_entry_and_every_fault_in_it(self):
        desk = self.desk()
        good = {"card_id": "code-01", "action": "adopt", "surface": "app", "decided_by": "researcher"}
        bad = {"card_id": " ", "action": "approve", "surface": "email", "decided_by": "researcher", "detail": [], "note": 3}
        with self.assertRaises(ValueError) as caught:
            record.append(self.store, desk, [good, bad], now=clock(1))
        self.assertEqual(str(caught.exception), (
            f"Record entry 2 for {desk} is refused: an entry names its card_id; 'approve' is not an action the "
            "researcher records; surface is one of app, page, chat, table, server, not 'email'; detail is an "
            "object; note is text."))
        with self.assertRaisesRegex(ValueError, r"entry 1 .*decided_by is researcher or machine, not 'model'\.$"):
            record.append(self.store, desk, [dict(good, decided_by="model")], now=clock(1))
        with self.assertRaisesRegex(ValueError, "'adopt' is not an action the machine records"):
            record.append(self.store, desk, [dict(good, decided_by="machine")], now=clock(1))

    def test_text_is_kept_as_written(self):
        desk = self.desk()
        record.append(self.store, desk, [dict(card_id="code-01", action="adopt", surface="app", decided_by="researcher", note="Café talk, ñ.")], now=clock(1))
        self.assertIn("Café talk, ñ.", self.store.load_artifact(desk, "record.jsonl"))

    def test_a_desk_with_no_record_reads_as_empty(self):
        self.assertEqual(record.read(self.store, self.desk()), [])


class TestLineage(StoreCase):
    def test_the_lineage_walks_from_the_first_ratification_to_this_one(self):
        codebook_desk, rulings_desk, later_desk = self.desk(), self.desk("rulings"), self.desk("rulings")
        record.append(self.store, codebook_desk, [{"card_id": "code-01", "action": "adopt", "surface": "app", "decided_by": "researcher"}], now=clock(1))
        record.append(self.store, rulings_desk, [{"card_id": "chunk-7", "action": "exclude", "detail": {"reason": "x"}, "surface": "app", "decided_by": "researcher"}], now=clock(2))
        record.append(self.store, later_desk, [{"card_id": "chunk-3", "action": "exclude", "detail": {"reason": "y"}, "surface": "app", "decided_by": "researcher"}], now=clock(3))
        first = self.ratification(codebook_desk, desks=[rulings_desk])
        second = self.ratification(rulings_desk, parent=first, desks=[later_desk])
        lineage = record.read_lineage(self.store, second)
        self.assertEqual([e["desk_id"] for e in lineage], [codebook_desk, rulings_desk, later_desk])
        self.assertEqual([e["desk_id"] for e in record.read_lineage(self.store, first)], [codebook_desk, rulings_desk])

    def test_a_desk_is_read_once_however_often_the_chain_names_it(self):
        codebook_desk, rulings_desk = self.desk(), self.desk("rulings")
        record.append(self.store, rulings_desk, [{"card_id": "chunk-7", "action": "exclude", "detail": {"reason": "x"}, "surface": "app", "decided_by": "researcher"}], now=clock(1))
        first = self.ratification(codebook_desk, desks=[rulings_desk])
        second = self.ratification(rulings_desk, parent=first, desks=[rulings_desk])
        self.assertEqual(len(record.read_lineage(self.store, second)), 1)

    def test_a_ratification_made_from_a_table_has_an_empty_lineage(self):
        rid = self.store.create("ratification", {})
        self.store.save_artifact(rid, "ratification.json", json.dumps({"checksum": "0" * 16, "codes": 6, "note": ""}))
        self.assertEqual(record.read_lineage(self.store, rid), [])

    def test_an_id_with_no_ratification_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no ratification record"):
            record.read_lineage(self.store, self.desk())

    def test_a_chain_that_loops_is_refused(self):
        desk = self.desk()
        first = self.store.create("ratification", {})
        second = self.ratification(desk, parent=first)
        self.store.save_artifact(first, "ratification.json", json.dumps({"checksum": "0" * 16, "codes": 6, "desk_id": desk, "parent": second, "desks": []}))
        with self.assertRaisesRegex(ValueError, "loops"):
            record.read_lineage(self.store, second)


EXPECTED = (
    "Assembled from the decision record, not written by the researcher; check it against "
    "your own account before you use it. "
    "A model drafted a codebook of 6 codes. The researcher ratified it on a codebook desk, "
    "deciding each code against the cases it would take: 3 adopted, 1 reworded, 1 merged "
    "into another code and 1 deleted. The researcher judged the codes not mutually "
    "exclusive. This made codebook version 1.0. "
    "A rulings desk presented 4 chunks on which two coding passes disagreed, with "
    "blind-first on, so each model proposal stayed hidden until the researcher had saved "
    "a ruling on its chunk. The researcher ruled on 3 and excluded 1 from the analysis. "
    "2 rulings departed from the proposal, and 1 was adopted as a rule, amending the "
    "codebook to version 1.1. "
    "8 chunks on which both passes agreed were coded under version 1.0 and have not been "
    "rechecked against the amendment."
)


class TestMethodsParagraph(unittest.TestCase):
    def test_r6_3_paragraph_counts_match_fixture_record(self):
        entries = fixture()
        latest = {(e["desk_id"], e["card_id"]): e for e in entries if e["decided_by"] == "researcher"}
        actions = Counter(e["action"] for (desk, _), e in latest.items() if desk == CODEBOOK_DESK)
        rulings = [e for (desk, _), e in latest.items() if desk == RULINGS_DESK and e["action"] == "ruling"]
        counts = {
            "adopted": actions["adopt"], "reworded": actions["reword"], "merged": actions["merge"], "deleted": actions["delete"],
            "ruled": len(rulings), "excluded": sum(e["action"] == "exclude" for (desk, _), e in latest.items() if desk == RULINGS_DESK),
            "departed": sum(e["detail"]["departs"] for e in rulings), "rules": sum(e["detail"].get("is_rule") is True for e in rulings),
        }
        self.assertEqual(counts, {"adopted": 3, "reworded": 1, "merged": 1, "deleted": 1, "ruled": 3, "excluded": 1, "departed": 2, "rules": 1})
        self.assertEqual(methods.paragraph(entries), EXPECTED)

    def test_r6_4_paragraph_labelled_assembled(self):
        self.assertTrue(methods.paragraph(fixture()).startswith("Assembled from the decision record, not written by the researcher"))
        self.assertTrue(methods.paragraph([]).startswith("Assembled from the decision record, not written by the researcher"))

    def test_r6_5_paragraph_states_blind_first_per_desk(self):
        entries = fixture()
        later = [dict(e, desk_id="desk-77777777") for e in entries if e["desk_id"] == RULINGS_DESK]
        for entry in later:
            if entry["action"] == "build":
                entry["detail"] = dict(entry["detail"], blind_first=False)
        text = methods.paragraph(entries + later)
        self.assertIn("A rulings desk presented 4 chunks on which two coding passes disagreed, with blind-first off, so", text)
        self.assertIn("with blind-first on, so each model proposal stayed hidden until the researcher had saved a ruling on its chunk.", text)
        self.assertIn("with blind-first off, so each model proposal was shown beside its chunk from the start.", text)

    def test_r6_6_paragraph_states_unrechecked_chunks(self):
        entries = fixture()
        self.assertIn("8 chunks on which both passes agreed were coded under version 1.0 and have not been rechecked against the amendment.", methods.paragraph(entries))
        swept = [*entries, {"desk_id": RULINGS_DESK, "card_id": "desk", "action": "sweep", "detail": {"rechecked": 8}, "note": "",
                            "time": "2026-11-15T15:00:00Z", "surface": "server", "decided_by": "machine"}]
        self.assertNotIn("not been rechecked", methods.paragraph(swept))
        one = [dict(e, detail=dict(e["detail"], agreed_unchecked=1)) if e["action"] == "ratify" and e["desk_id"] == RULINGS_DESK else e for e in entries]
        self.assertIn("1 chunk on which both passes agreed was coded under version 1.0 and has not been rechecked against the amendment.", methods.paragraph(one))

    def test_with_no_amendment_nothing_is_said_about_rechecking(self):
        entries = [e for e in fixture() if e["desk_id"] == CODEBOOK_DESK]
        self.assertNotIn("rechecked", methods.paragraph(entries))

    def test_a_researcher_supplied_codebook_without_proposals(self):
        entries = [e for e in fixture() if e["action"] not in ("draft", "propose")]
        text = methods.paragraph(entries)
        self.assertIn("The researcher ratified a codebook of 6 codes on a codebook desk", text)
        self.assertIn("with no model proposals.", text)
        self.assertNotIn("A model drafted", text)

    def test_plurals_follow_the_counts(self):
        entries = [e for e in fixture() if not (e["desk_id"] == RULINGS_DESK and e["card_id"] == "chunk-12")]
        entries = [dict(e, detail=dict(e["detail"], cards=3)) if e["action"] == "build" and e["desk_id"] == RULINGS_DESK else e for e in entries]
        text = methods.paragraph(entries)
        self.assertIn("1 ruling departed from the proposal, and 1 was adopted as a rule", text)
        self.assertIn("A rulings desk presented 3 chunks", text)

    def test_amendments_are_counted(self):
        entries = [dict(e, detail=dict(e["detail"], amendments=2)) if e["action"] == "ratify" and e["desk_id"] == RULINGS_DESK else e for e in fixture()]
        self.assertIn("have not been rechecked against the 2 amendments.", methods.paragraph(entries))

    def test_a_desk_not_yet_finished_says_so(self):
        built = [e for e in fixture() if e["action"] in ("build", "draft", "propose")]
        text = methods.paragraph(built)
        self.assertIn("A model drafted a codebook of 6 codes. The codebook desk has not been finished.", text)
        self.assertIn("ruling on its chunk. The rulings desk has not been finished.", text)
        self.assertNotIn("ruled on", text)
        bare = [e for e in built if e["action"] == "build" and e["desk_id"] == CODEBOOK_DESK]
        self.assertIn("A codebook of 6 codes was put on a codebook desk. The codebook desk has not been finished.", methods.paragraph(bare))

    def test_rulings_without_proposals_or_rules(self):
        entries = [e for e in fixture() if e["action"] != "propose"]
        entries = [dict(e, detail={k: v for k, v in e["detail"].items() if k != "is_rule"}) if e["action"] == "ruling" else e for e in entries]
        text = methods.paragraph(entries)
        self.assertIn("disagreed, with no model proposals. The researcher ruled on 3 and excluded 1 from the analysis. 8 chunks", text)
        rule = [dict(e, detail=dict(e["detail"], is_rule=True)) if e["card_id"] == "chunk-9" else e for e in entries]
        self.assertIn("from the analysis. 1 was adopted as a rule, amending the codebook to version 1.1.", methods.paragraph(rule))
        proposed = [e for e in fixture() if not (e["action"] == "ruling" and e["detail"].get("is_rule"))]
        self.assertIn("1 ruling departed from the proposal. 8 chunks", methods.paragraph(proposed))

    def test_two_rules(self):
        entries = [dict(e, detail=dict(e["detail"], is_rule=True)) if e["card_id"] == "chunk-12" else e for e in fixture()]
        self.assertIn("2 rulings departed from the proposal, and 2 were adopted as rules, amending", methods.paragraph(entries))

    def test_an_unanswered_question_and_a_desk_without_a_build_are_left_out(self):
        entries = [e for e in fixture() if e["action"] != "answer_exclusive"]
        entries.append({"desk_id": "desk-55555555", "card_id": "code-01", "action": "adopt", "detail": {}, "note": "",
                        "time": "2026-11-15T16:00:00Z", "surface": "chat", "decided_by": "researcher"})
        text = methods.paragraph(entries)
        self.assertNotIn("mutually exclusive", text)
        self.assertEqual(text.count("ratified"), 1)

    def test_codes_judged_exclusive(self):
        entries = [dict(e, detail={"exclusive": True}) if e["action"] == "answer_exclusive" else e for e in fixture()]
        self.assertIn("The researcher judged the codes mutually exclusive.", methods.paragraph(entries))

    def test_without_a_prior_version_the_unrechecked_chunks_name_none(self):
        entries = [e for e in fixture() if e["desk_id"] == RULINGS_DESK]
        self.assertIn("8 chunks on which both passes agreed were coded and have not been rechecked against the amendment.", methods.paragraph(entries))

    def test_blind_first_is_on_unless_the_build_says_otherwise(self):
        entries = [dict(e, detail={k: v for k, v in e["detail"].items() if k != "blind_first"}) if e["action"] == "build" else e for e in fixture()]
        self.assertIn("with blind-first on", methods.paragraph(entries))

    def test_one_code_and_one_chunk_read_in_the_singular(self):
        def one(stage, desk_id, card, decision):
            return [
                {"desk_id": desk_id, "card_id": "desk", "action": "build", "detail": {"stage": stage, "cards": 1}, "decided_by": "machine"},
                {"desk_id": desk_id, "card_id": card, **decision, "decided_by": "researcher"},
                {"desk_id": desk_id, "card_id": "desk", "action": "ratify", "detail": {"version": "1.0"}, "decided_by": "researcher",
                 "time": "2026-11-15T14:00:00Z"},
            ]
        codebook = one("codebook", "desk-1", "code-01", {"action": "adopt", "detail": {}})
        text = methods.paragraph(codebook)
        self.assertIn("The researcher ratified a codebook of 1 code on a codebook desk, deciding each code against the cases it would take: 1 adopted.", text)
        drafted = [codebook[0], {"desk_id": "desk-1", "card_id": "code-01", "action": "draft", "detail": {}, "decided_by": "machine"}, *codebook[1:]]
        self.assertIn("A model drafted a codebook of 1 code. The researcher ratified it on a codebook desk", methods.paragraph(drafted))
        self.assertIn("A codebook of 1 code was put on a codebook desk.", methods.paragraph(codebook[:1]))
        rulings = one("rulings", "desk-2", "chunk-7", {"action": "exclude", "detail": {"reason": "x"}})
        self.assertIn("A rulings desk presented 1 chunk on which", methods.paragraph(rulings))

    def test_a_ratified_desk_with_no_recorded_decisions_still_reads(self):
        entries = [e for e in fixture() if e["desk_id"] == CODEBOOK_DESK and e["action"] in ("build", "ratify")]
        self.assertIn("deciding each code against the cases it would take. This made codebook version 1.0.", methods.paragraph(entries))

    def test_a_later_machine_entry_does_not_displace_the_decision(self):
        entries = fixture()
        late = {"desk_id": RULINGS_DESK, "card_id": "chunk-11", "action": "propose", "detail": {"codes": ["Food access"]}, "note": "",
                "time": "2026-11-15T15:00:00Z", "surface": "server", "decided_by": "machine"}
        self.assertEqual(methods.paragraph([*entries, late]), EXPECTED)

    def test_a_desk_without_a_build_does_not_stop_the_reading(self):
        stray = {"desk_id": "desk-55555555", "card_id": "code-01", "action": "adopt", "detail": {}, "note": "",
                 "time": "2026-11-15T13:00:00Z", "surface": "chat", "decided_by": "researcher"}
        self.assertEqual(methods.paragraph([stray, *fixture()]), EXPECTED)

    def test_only_a_sweep_after_the_ratification_settles_the_rechecking(self):
        entries = fixture()
        ratified_at = next(e["time"] for e in entries if e["action"] == "ratify" and e["desk_id"] == RULINGS_DESK)
        sweep = {"desk_id": RULINGS_DESK, "card_id": "desk", "action": "sweep", "detail": {"rechecked": 8}, "note": "",
                 "surface": "server", "decided_by": "machine"}
        decided_at = max(e["time"] for e in entries if e["desk_id"] == RULINGS_DESK and e["action"] != "ratify")
        self.assertLess(decided_at, ratified_at)
        earlier = [e for e in entries if e["action"] != "ratify" or e["desk_id"] != RULINGS_DESK]
        earlier += [dict(sweep, time=decided_at)] + [e for e in entries if e["action"] == "ratify" and e["desk_id"] == RULINGS_DESK]
        self.assertIn("have not been rechecked", methods.paragraph(earlier))
        self.assertNotIn("have not been rechecked", methods.paragraph([*entries, dict(sweep, time=ratified_at)]))

    def test_without_amendments_unchecked_chunks_are_not_mentioned(self):
        entries = [dict(e, detail=dict(e["detail"], amendments=0)) if e["action"] == "ratify" and e["desk_id"] == RULINGS_DESK else e for e in fixture()]
        self.assertNotIn("rechecked", methods.paragraph(entries))

    def test_an_empty_record_says_so(self):
        self.assertEqual(
            methods.paragraph([]),
            "Assembled from the decision record, not written by the researcher; check it against "
            "your own account before you use it. The record holds no desk decisions.",
        )


if __name__ == "__main__":
    unittest.main()
