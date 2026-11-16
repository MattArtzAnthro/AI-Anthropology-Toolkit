"""The desk's MCP tools: building a desk from what the server holds, and the MCP App
resource the desk opens in."""

import asyncio
import json
import re
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from mcp.server.mcpserver.exceptions import ToolError

from ai_anthro_toolkit import brand, design
from ai_anthro_toolkit.desk import a2ui, cards, decisions, gate, page, record
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.mcp import server
from tests.package import test_desk_surface as surf
from tests.package.desk_helpers import load

DESK_URI = "ui://ai-anthropology/ratification-desk"


def desk_sync(*args):
    """What desk_sync sends the view: its structured content."""
    return server.desk_sync(*args).structured_content


def desk_finish(desk_id):
    """What desk_finish sends the view: its structured content."""
    return server.desk_finish(desk_id).structured_content


class DeskCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.store = JobStore(Path(self._dir.name))
        patcher = mock.patch.object(server, "_jobs", self.store)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.codebook = load("codebook")
        self.cases = load("cases")

    def jobs(self, kind):
        return sorted(p.name for p in Path(self._dir.name).iterdir() if p.name.startswith(f"{kind}-"))

    def codebook_job(self, records=None):
        job_id = self.store.create("codebook", {"lens_key": "", "mode": "delegated"})
        self.store.save_artifact(job_id, "result.json", json.dumps(records or self.codebook))
        self.store.complete(job_id)
        return job_id

    def ratified(self, records=None):
        return server.ratify_codebook(codebook=records or self.codebook)["ratification_id"]

    def coding_job(self, name, ratification_id):
        job_id = self.store.create("coding", {"ratification_id": ratification_id, "mode": "delegated"})
        self.store.save_artifact(job_id, "result.json", json.dumps(load(name)))
        self.store.complete(job_id)
        return job_id

    def rulings(self, **kw):
        rid = kw.pop("ratification_id", None) or self.ratified()
        jobs = [self.coding_job("coding_a", rid), self.coding_job("coding_b", rid)]
        return rid, server.build_ratification_desk(stage="rulings", coding_job_ids=jobs, **kw)

    def payload(self, result):
        return self.store.read(result.structured_content["desk_id"])["payload"]


class TestCodebookDesk(DeskCase):
    def test_r1_1_codebook_desk_writes_page_and_returns_desk_id(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases,
                                                 title="Garden study")
        self.assertFalse(result.is_error)
        out = result.structured_content
        self.assertEqual(self.jobs("desk"), [out["desk_id"]])
        self.assertEqual(self.store.read(out["desk_id"])["kind"], "desk")
        built = cards.codebook_cards(self.codebook, self.cases)
        self.assertEqual(out["cards"], 6)  # the fixture codebook's six codes
        self.assertEqual([c["code_label"] for c in self.payload(result)["cards"]], [r["code_label"] for r in self.codebook])
        html = Path(out["page"]).read_text(encoding="utf-8")
        desk = {"desk_id": out["desk_id"], "stage": "codebook", "title": "Garden study", "cards": built}
        self.assertEqual(html, page.render_page(desk))
        self.assertEqual(Path(out["page"]).name, "desk.html")
        self.assertNotRegex(html, r"(?i)<script[^>]*\ssrc\s*=|<link[^>]*\shref\s*=")
        self.assertEqual(set(out), {"desk_id", "stage", "cards", "card_checksum", "page", "a2ui"})
        self.assertEqual(out["stage"], "codebook")
        self.assertEqual(out["a2ui"], a2ui.surface(desk))
        self.assertEqual(result.content[0].text, (
            f"Desk {out['desk_id']} built: {len(self.codebook)} codes to decide. The researcher decides "
            "in the desk, card by card; do not record decisions for them. If no desk appeared in this "
            f"client, give the researcher the page to open in a browser: {out['page']}"))
        built_at = datetime.fromisoformat(self.payload(result)["built_at"])
        self.assertEqual(built_at.utcoffset(), timedelta(0))
        self.assertLess(abs(datetime.now(timezone.utc) - built_at), timedelta(minutes=1))

    def test_the_title_is_trimmed(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases, title="  Garden study \n")
        self.assertEqual(self.payload(result)["title"], "Garden study")

    def test_codebook_job_id_must_name_a_codebook_job(self):
        rid = self.ratified()
        coding = self.coding_job("coding_a", rid)
        for job_id in (rid, coding):
            with self.subTest(job_id), self.assertRaisesRegex(ValueError, f"^'{job_id}' is not a codebook job"):
                server.build_ratification_desk(stage="codebook", codebook_job_id=job_id, cases=self.cases)
        self.assertEqual(self.jobs("desk"), [])

    def test_conflicting_arguments_are_refused(self):
        job_id = self.codebook_job()
        rid = self.ratified()
        jobs = [self.coding_job("coding_a", rid), self.coding_job("coding_b", rid)]
        base = {"codebook": self.codebook, "cases": self.cases}
        for stage, kw, message in (
                ("codebook", dict(base, codebook_job_id=job_id), "either codebook_job_id or codebook, not both"),
                ("codebook", dict(base, coding_job_ids=jobs), "coding_job_ids"),
                ("codebook", dict(base, proposals=load("proposals")), "proposals"),
                ("codebook", dict(base, blind_first=False), "blind_first"),
                ("rulings", {"coding_job_ids": jobs, "codebook": self.codebook}, "codebook"),
                ("rulings", {"coding_job_ids": jobs, "codebook_job_id": job_id}, "codebook_job_id"),
                ("rulings", {"coding_job_ids": jobs, "cases": self.cases}, "cases")):
            with self.subTest(stage=stage, kw=sorted(kw)), self.assertRaisesRegex(ValueError, message):
                server.build_ratification_desk(stage=stage, **kw)
        with self.assertRaisesRegex(ValueError, r"^A codebook desk does not take proposals, blind_first\.$"):
            server.build_ratification_desk(stage="codebook", proposals=load("proposals"), blind_first=False, **base)
        with self.assertRaisesRegex(ValueError, r"^A rulings desk does not take codebook, cases\.$"):
            server.build_ratification_desk(stage="rulings", coding_job_ids=jobs, **base)
        self.assertEqual(self.jobs("desk"), [])

    def test_records_that_are_not_a_list_are_refused_by_name(self):
        rid = self.ratified()
        bad = self.store.create("codebook", {})
        self.store.save_artifact(bad, "result.json", json.dumps({"rows": self.codebook}))
        with self.assertRaisesRegex(ToolError, f"Codebook job '{bad}' holds no list of records"):
            asyncio.run(server.mcp.call_tool("build_ratification_desk", {"stage": "codebook", "codebook_job_id": bad, "cases": self.cases}))
        coding = self.store.create("coding", {"ratification_id": rid})
        self.store.save_artifact(coding, "result.json", json.dumps(["not a record"]))
        with self.assertRaisesRegex(ToolError, f"Coding job '{coding}' holds no list of records"):
            asyncio.run(server.mcp.call_tool("build_ratification_desk", {
                "stage": "rulings", "coding_job_ids": [self.coding_job("coding_a", rid), coding]}))
        self.assertEqual(self.jobs("desk"), [])

    def test_the_result_counts_one_card_in_the_singular(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook[:1],
                                                 cases={self.codebook[0]["code_label"]: self.cases[self.codebook[0]["code_label"]]})
        self.assertIn(" built: 1 code to decide. ", result.content[0].text)

    def test_a_codebook_job_supplies_the_codebook(self):
        job_id = self.codebook_job()
        result = server.build_ratification_desk(stage="codebook", codebook_job_id=job_id, cases=self.cases)
        self.assertEqual(json.loads(self.store.load_artifact(result.structured_content["desk_id"], "codebook.json")), self.codebook)

    def test_r1_2_code_without_case_refused_and_named(self):
        cases = {k: v for k, v in self.cases.items() if k not in ("Land tenure", "Food access")}
        with self.assertRaises(ValueError) as caught:
            server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=cases)
        self.assertRegex(str(caught.exception), r"no case: .*Land tenure")
        self.assertRegex(str(caught.exception), r"no case: .*Food access")
        self.assertEqual(self.jobs("desk"), [])

    def test_r1_7_desk_stores_card_checksum(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases)
        stored = self.payload(result)
        self.assertEqual(stored["card_checksum"], cards.checksum(stored["cards"]))
        self.assertEqual(stored["card_checksum"], cards.checksum(cards.codebook_cards(self.codebook, self.cases)))
        self.assertEqual(result.structured_content["card_checksum"], stored["card_checksum"])

    def test_r6_2_build_records_machine_entries(self):
        drafted = server.build_ratification_desk(stage="codebook", codebook_job_id=self.codebook_job(), cases=self.cases)
        entries = record.read(self.store, drafted.structured_content["desk_id"])
        self.assertEqual([(e["card_id"], e["action"]) for e in entries],
                         [("desk", "build")] + [(c["card_id"], "draft") for c in self.payload(drafted)["cards"]])
        self.assertEqual({(e["decided_by"], e["surface"], e["note"]) for e in entries}, {("machine", "server", "")})
        self.assertEqual(entries[0]["detail"], {"stage": "codebook", "cards": len(self.codebook)})
        self.assertEqual([e["detail"] for e in entries[1:]], [{"label": r["code_label"]} for r in self.codebook])
        # Records the researcher supplies were not drafted by a model.
        given = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases)
        self.assertEqual([e["action"] for e in record.read(self.store, given.structured_content["desk_id"])], ["build"])

    def test_the_gate_finishes_a_codebook_desk_the_tool_built(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases)
        stored = self.payload(result)
        doc = {"schema": "aat/desk-decisions@1", "desk_id": result.structured_content["desk_id"],
               "card_checksum": stored["card_checksum"], "exclusive": False,
               "decisions": {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}}
        outcome = gate.apply(self.store, doc["desk_id"], doc, "chat")
        coding = server.start_coding_job(chunks=[{"chunk_id": 1, "text": "x"}], ratification_id=outcome["ratification_id"],
                                         llm_mode="delegated")
        self.assertEqual(coding["packets"], 1)

    def test_the_request_must_carry_a_codebook_and_cases(self):
        for kw, message in (({"cases": self.cases}, "^A codebook desk needs the codebook: pass codebook_job_id or the codebook records.$"),
                            ({"codebook": self.codebook}, "^A codebook desk needs cases for each code: pass cases as "),
                            ({"codebook_job_id": "codebook-00000000", "cases": self.cases}, "codebook-00000000")):
            with self.subTest(kw), self.assertRaisesRegex(ValueError, message):
                server.build_ratification_desk(stage="codebook", **kw)
        unfinished = self.store.create("codebook", {})
        with self.assertRaisesRegex(ValueError, f"^Codebook job '{unfinished}' has no result yet; wait for get_job_status to report complete.$"):
            server.build_ratification_desk(stage="codebook", codebook_job_id=unfinished, cases=self.cases)
        self.assertEqual(self.jobs("desk"), [])


class TestRulingsDesk(DeskCase):
    def test_r1_3_one_card_per_disagreement(self):
        _, result = self.rulings()
        expected = cards.rulings_cards(load("coding_a"), load("coding_b"), self.codebook)
        self.assertEqual([c["card_id"] for c in self.payload(result)["cards"]], [c["card_id"] for c in expected])
        self.assertEqual(result.structured_content["cards"], len(expected))
        self.assertEqual(result.structured_content["stage"], "rulings")
        self.assertTrue(result.content[0].text.endswith(result.structured_content["page"]))
        self.assertIn(f" built: {len(expected)} disagreements to decide. ", result.content[0].text)
        # A rulings desk reads its codebook from the ratification in force.
        self.assertIsNone(self.store.load_artifact(result.structured_content["desk_id"], "codebook.json"))

    def test_r1_4_jobs_under_different_ratifications_refused(self):
        first, second = self.ratified(), self.ratified()
        jobs = [self.coding_job("coding_a", first), self.coding_job("coding_b", second)]
        with self.assertRaises(ValueError) as caught:
            server.build_ratification_desk(stage="rulings", coding_job_ids=jobs)
        self.assertIn(first, str(caught.exception))
        self.assertIn(second, str(caught.exception))
        self.assertEqual(self.jobs("desk"), [])

    def test_a_rulings_desk_needs_two_finished_coding_jobs(self):
        rid = self.ratified()
        done = self.coding_job("coding_a", rid)
        running = self.store.create("coding", {"ratification_id": rid})
        codebook_job = self.codebook_job()
        two = "^A rulings desk compares two coding passes: pass exactly two coding_job_ids.$"
        for ids, message in (([done], two), ([done, done, done], two), ([done, running], f"^Coding job '{running}' has no result yet"),
                             ([done, codebook_job], f"^'{codebook_job}' is not a coding job.$"), (None, two)):
            with self.subTest(ids), self.assertRaisesRegex(ValueError, message):
                server.build_ratification_desk(stage="rulings", coding_job_ids=ids)
        unratified = self.store.create("coding", {"ratification_id": ""})
        self.store.save_artifact(unratified, "result.json", json.dumps(load("coding_b")))
        with self.assertRaisesRegex(ValueError, f"^Coding job '{unratified}' names no ratification"):
            server.build_ratification_desk(stage="rulings", coding_job_ids=[done, unratified])
        self.assertEqual(self.jobs("desk"), [])

    def test_the_same_coding_job_twice_is_refused(self):
        rid = self.ratified()
        done = self.coding_job("coding_a", rid)
        with self.assertRaisesRegex(ValueError, "two different coding jobs"):
            server.build_ratification_desk(stage="rulings", coding_job_ids=[done, done])
        self.assertEqual(self.jobs("desk"), [])
        self.assertNotIn("desks", json.loads(self.store.load_artifact(rid, "ratification.json")))

    def test_a_proposal_for_an_agreed_chunk_is_refused(self):
        with self.assertRaisesRegex(ValueError, "chunk 1 is for a chunk with no disagreement"):
            self.rulings(proposals={"1": {"codes": ["Shared labour"], "rationale": "r"}})
        self.assertEqual(self.jobs("desk"), [])

    def test_a_malformed_desks_listing_is_refused_before_anything_is_written(self):
        rid = self.ratified()
        held = json.loads(self.store.load_artifact(rid, "ratification.json"))
        self.store.save_artifact(rid, "ratification.json", json.dumps(dict(held, desks=None)))
        with self.assertRaisesRegex(ValueError, f"{rid}'s list of desks is damaged"):
            self.rulings(ratification_id=rid)
        self.assertEqual(self.jobs("desk"), [])

    def test_re_ratifying_a_codebook_job_keeps_its_desks(self):
        job_id = self.codebook_job()
        server.ratify_codebook(codebook_job_id=job_id)
        _, result = self.rulings(ratification_id=job_id)
        server.ratify_codebook(codebook_job_id=job_id, note="looked again")
        held = json.loads(self.store.load_artifact(job_id, "ratification.json"))
        self.assertEqual((held["desks"], held["note"]), ([result.structured_content["desk_id"]], "looked again"))

    def test_a_ratification_without_its_codebook_is_refused(self):
        rid = self.ratified()
        held = self.store.load_artifact(rid, "ratification.json")
        for keep in ("", "ratification.json", "result.json"):
            empty = self.store.create("ratification", {"codes": 0})
            if keep:
                self.store.save_artifact(empty, keep, self.store.load_artifact(rid, keep) or "")
            jobs = [self.coding_job("coding_a", empty), self.coding_job("coding_b", empty)]
            with self.subTest(keep=keep), self.assertRaisesRegex(ValueError, f"The ratification in force, {empty}, holds no codebook"):
                server.build_ratification_desk(stage="rulings", coding_job_ids=jobs)
        self.assertTrue(held)
        self.assertEqual(self.jobs("desk"), [])

    def test_an_unknown_stage_is_refused(self):
        with self.assertRaisesRegex(ValueError, "stage is 'codebook' or 'rulings'"):
            server.build_ratification_desk(stage="themes", codebook=self.codebook, cases=self.cases)
        self.assertEqual(self.jobs("desk"), [])

    def test_r3_8_rulings_desk_blind_first_by_default(self):
        _, result = self.rulings(proposals=load("proposals"))
        self.assertIs(self.payload(result)["blind_first"], True)
        sent = json.dumps(result.structured_content["a2ui"])
        for proposal in load("proposals").values():
            self.assertNotIn(proposal["rationale"], sent)
        _, seen = self.rulings(proposals=load("proposals"), blind_first=False)
        self.assertIs(self.payload(seen)["blind_first"], False)
        self.assertIn(load("proposals")["7"]["rationale"], json.dumps(seen.structured_content["a2ui"]))

    def test_r6_2_rulings_build_records_each_proposal(self):
        rid, result = self.rulings(proposals=load("proposals"))
        desk_id = result.structured_content["desk_id"]
        entries = record.read(self.store, desk_id)
        self.assertEqual(entries[0]["action"], "build")
        self.assertEqual(entries[0]["detail"], {"stage": "rulings", "cards": result.structured_content["cards"],
                                                "blind_first": True, "ratification_id": rid})
        proposed = {e["card_id"]: e["detail"] for e in entries[1:]}
        self.assertEqual(sorted(proposed), sorted(f"chunk-{k}" for k in load("proposals")))
        # As the card shows it: the proposal's codes in codebook order.
        self.assertEqual(proposed, {c["card_id"]: c["proposal"] for c in self.payload(result)["cards"] if c["proposal"]})
        self.assertEqual(proposed["chunk-9"]["codes"], ["Land tenure", "Municipal relations"])
        self.assertEqual({(e["action"], e["decided_by"], e["surface"], e["note"]) for e in entries[1:]}, {("propose", "machine", "server", "")})

    def test_the_desk_holds_what_the_gate_reads(self):
        rid, result = self.rulings()
        stored = self.payload(result)
        self.assertEqual(stored["ratification_id"], rid)
        self.assertEqual(sorted(stored["coding_job_ids"]), self.jobs("coding"))
        self.assertEqual(stored["codes"], [r["code_label"] for r in self.codebook])
        self.assertIs(stored["exclusive"], False)  # a table ratification never asked
        coded = len(load("coding_a"))
        self.assertEqual((coded, len(stored["cards"]), stored["agreed"]), (12, 4, 8))
        self.assertEqual(json.loads(self.store.load_artifact(rid, "ratification.json"))["desks"],
                         [result.structured_content["desk_id"]])

    def test_exclusivity_comes_from_the_ratification_in_force(self):
        rid = self.ratified()
        held = json.loads(self.store.load_artifact(rid, "ratification.json"))
        self.store.save_artifact(rid, "ratification.json", json.dumps(dict(held, exclusive=True, desks=["desk-00000000"])))
        _, result = self.rulings(ratification_id=rid)
        self.assertIs(self.payload(result)["exclusive"], True)
        self.assertEqual(json.loads(self.store.load_artifact(rid, "ratification.json"))["desks"],
                         ["desk-00000000", result.structured_content["desk_id"]])

    def test_the_gate_finishes_a_rulings_desk_the_tool_built(self):
        rid, result = self.rulings(proposals=load("proposals"))
        stored = self.payload(result)
        decisions = {c["card_id"]: {"codes": c["coder_a"] or [stored["codes"][0]], "is_rule": False} for c in stored["cards"]}
        doc = {"schema": "aat/desk-decisions@1", "desk_id": result.structured_content["desk_id"],
               "card_checksum": stored["card_checksum"], "exclusive": None, "decisions": decisions}
        outcome = gate.apply(self.store, doc["desk_id"], doc, "chat")
        self.assertEqual(outcome["ratification_id"], rid)
        self.assertEqual(outcome["resolved"], len(stored["cards"]))


class TestRecordDecisions(DeskCase):
    """The model-visible import, for decisions the researcher made in chat or on the page."""

    def codebook_desk(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases)
        return result.structured_content["desk_id"], self.payload(result)

    def doc(self, desk_id, stored, decisions, exclusive=None):
        return {"schema": "aat/desk-decisions@1", "desk_id": desk_id, "card_checksum": stored["card_checksum"],
                "exclusive": exclusive, "decisions": decisions}

    def rulings_desk(self):
        rid, result = self.rulings(proposals=load("proposals"))
        stored = self.payload(result)
        agreeing = {c["card_id"]: {"codes": c["proposal"]["codes"]} if c["proposal"]["codes"] else {"none_apply": True}
                    for c in stored["cards"]}
        return rid, result.structured_content["desk_id"], stored, agreeing

    def test_r2_5_desk_ratification_accepted_by_start_coding_job(self):
        desk_id, stored = self.codebook_desk()
        outcome = server.record_desk_decisions(
            desk_id, self.doc(desk_id, stored, {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}, False), "page")
        self.assertEqual((outcome["stage"], outcome["version"], outcome["codes"]), ("codebook", "1.0", 6))
        job = server.start_coding_job(chunks=[{"chunk_id": 1, "text": "x"}], ratification_id=outcome["ratification_id"],
                                      llm_mode="delegated")
        self.assertEqual(json.loads(self.store.load_artifact(job["job_id"], "codebook.json")), self.codebook)

    def test_r2_7_actions_reach_ratified_codebook(self):
        desk_id, stored = self.codebook_desk()
        decisions = {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}
        decisions["code-01"] = {"action": "reword", "definition": "Garden work members share out between them."}
        decisions["code-02"] = {"action": "delete", "note": "Folded into the discussion of exchange."}
        outcome = server.record_desk_decisions(desk_id, self.doc(desk_id, stored, decisions, True), "chat")
        job = server.start_coding_job(chunks=[{"chunk_id": 1, "text": "x"}], ratification_id=outcome["ratification_id"],
                                      llm_mode="delegated")
        coded_with = json.loads(self.store.load_artifact(job["job_id"], "codebook.json"))
        self.assertEqual([r["code_label"] for r in coded_with], [r["code_label"] for r in self.codebook if r["code_label"] != "Charity framing"])
        self.assertEqual(coded_with[0]["definition"], "Garden work members share out between them.")
        self.assertEqual(coded_with[0]["inclusion_criteria"], self.codebook[0]["inclusion_criteria"])
        self.assertEqual(outcome["codes"], 5)

    def test_r3_6_differing_ruling_without_rule_answer_refused(self):
        rid, desk_id, stored, decisions = self.rulings_desk()
        decisions["chunk-7"] = {"codes": ["Food access"]}  # the proposal was Charity framing
        before = self.jobs("ratification")
        with self.assertRaisesRegex(ValueError, r"(?m)^- chunk-7: .*rule"):
            server.record_desk_decisions(desk_id, self.doc(desk_id, stored, decisions), "chat")
        self.assertEqual(self.jobs("ratification"), before)
        self.assertEqual([e["decided_by"] for e in record.read(self.store, desk_id)], ["machine"] * 5)

    def rule(self):
        rid, desk_id, stored, decisions = self.rulings_desk()
        prior = self.store.load_artifact(rid, "result.json")
        decisions["chunk-7"] = {"codes": ["Food access"], "is_rule": True,
                                "rule_text": "Selling produce below cost counts as food access, not charity."}
        outcome = server.record_desk_decisions(desk_id, self.doc(desk_id, stored, decisions), "chat")
        return rid, prior, outcome

    def test_r4_3_amendment_issues_next_minor_version(self):
        rid, prior, outcome = self.rule()
        self.assertEqual(outcome["version"], "1.1")
        self.assertNotEqual(outcome["ratification_id"], rid)
        self.assertEqual(self.store.load_artifact(rid, "result.json"), prior)  # the prior version is unchanged
        amended = {r["code_label"]: r for r in json.loads(self.store.load_artifact(outcome["ratification_id"], "result.json"))}
        self.assertEqual(amended["Food access"]["rules"], ["Selling produce below cost counts as food access, not charity."])

    def test_r4_4_amended_ratification_names_parent_and_amendments(self):
        rid, _, outcome = self.rule()
        held = json.loads(self.store.load_artifact(outcome["ratification_id"], "ratification.json"))
        self.assertEqual((held["method"], held["version"], held["parent"]), ("amendment", "1.1", rid))
        [amendment] = held["amendments"]
        self.assertEqual((amendment["amendment_id"], amendment["source_card"], amendment["from_version"]), ("1.1-1", "chunk-7", "1.0"))

    def test_r4_5_reports_unrechecked_agreed_chunks(self):
        _, _, outcome = self.rule()
        self.assertEqual(outcome["agreed_unchecked"], 8)
        self.assertEqual(outcome["unchecked"], "8 chunks both passes agreed on were coded under version 1.0 "
                                               "and have not been rechecked against the amendment.")

    def test_r7_4_chat_decisions_recorded_with_surface_chat(self):
        _, desk_id, stored, decisions = self.rulings_desk()
        server.record_desk_decisions(desk_id, self.doc(desk_id, stored, decisions), "chat")
        decided = [e for e in record.read(self.store, desk_id) if e["decided_by"] == "researcher"]
        self.assertEqual(len(decided), len(stored["cards"]) + 1)  # each card, then the ratify entry
        self.assertEqual({e["surface"] for e in decided}, {"chat"})

    def test_the_page_surface_is_recorded_as_page(self):
        desk_id, stored = self.codebook_desk()
        server.record_desk_decisions(desk_id, self.doc(desk_id, stored, {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}, False), "page")
        self.assertEqual({e["surface"] for e in record.read(self.store, desk_id) if e["decided_by"] == "researcher"}, {"page"})

    def test_only_chat_and_page_reach_the_desk_through_this_tool(self):
        desk_id, stored = self.codebook_desk()
        doc = self.doc(desk_id, stored, {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}, False)
        for surface in ("app", "table", "server", ""):
            with self.subTest(surface), self.assertRaisesRegex(ValueError, "^surface is 'chat' or 'page'"):
                server.record_desk_decisions(desk_id, doc, surface)
        self.assertEqual(self.jobs("ratification"), [])

    def test_refusals_reach_the_model_and_name_what_is_missing(self):
        desk_id, stored = self.codebook_desk()
        decisions = {c["card_id"]: {"action": "adopt"} for c in stored["cards"][1:]}
        with self.assertRaisesRegex(ToolError, "code-01"):
            asyncio.run(server.mcp.call_tool("record_desk_decisions", {
                "desk_id": desk_id, "decisions": self.doc(desk_id, stored, decisions, False), "surface": "chat"}))
        self.assertEqual(self.jobs("ratification"), [])

    def test_the_same_decisions_twice_return_the_same_ratification(self):
        desk_id, stored = self.codebook_desk()
        doc = self.doc(desk_id, stored, {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}, False)
        first = server.record_desk_decisions(desk_id, doc, "chat")
        entries = record.read(self.store, desk_id)
        self.assertEqual(server.record_desk_decisions(desk_id, doc, "chat"), first)
        self.assertEqual(record.read(self.store, desk_id), entries)


class AppCase(DeskCase):
    """A desk decided in its MCP App view: each Save is a desk_sync call carrying the
    action the renderer sends, and Ratify is desk_finish."""

    def open_view(self, desk_id):
        self.desk_id = desk_id
        self.messages = desk_sync(desk_id)["a2ui"]
        self.found = surf.components(self.messages)
        self.data = surf.data_model(self.messages)

    def press(self, card_id, name="save_decision", **fields):
        n = next((i for i, c in enumerate(self.data["cards"]) if c["card_id"] == card_id), None)
        for key, value in fields.items():
            surf.set_path(self.data, f"/cards/{n}/{key}" if n is not None else f"/exclusivity/{key}", value)
        card = surf.card_component(self.found, card_id) if n is not None else card_id
        action_name, context = surf.fire(self.found, self.data, surf.button(self.found, card, name))
        out = desk_sync(self.desk_id, {"name": action_name, "context": context})
        self.assertEqual((set(out), out["desk_id"]), ({"desk_id", "saved", "document", "a2ui"}, self.desk_id))
        self.assertEqual(out["document"], self.document())
        self.assertEqual(a2ui.validate([*self.messages, *out["a2ui"]]), [])
        self.messages = [*self.messages, *out["a2ui"]]
        self.found = surf.components(self.messages)
        self.data = surf.apply_data(self.data, out["a2ui"])
        return out

    def saved(self):
        return json.loads(self.store.load_artifact(self.desk_id, "saved.json") or "null")

    def document(self):
        """The decisions document for what is saved: what Copy decisions as JSON copies (R7.3)."""
        saved = self.saved()
        return {"schema": "aat/desk-decisions@1", "desk_id": self.desk_id,
                "card_checksum": self.store.read(self.desk_id)["payload"]["card_checksum"],
                "exclusive": saved["exclusive"], "decisions": saved["decisions"]}


class TestAppOnlyTools(AppCase):
    def codebook_view(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases)
        self.open_view(result.structured_content["desk_id"])
        return self.payload(result)

    def rulings_view(self, **kw):
        _, result = self.rulings(proposals=load("proposals"), **kw)
        self.open_view(result.structured_content["desk_id"])
        return self.payload(result)

    def test_r7_7_desk_sync_is_app_only(self):
        tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
        for name in ("desk_sync", "desk_finish"):
            with self.subTest(name):
                self.assertEqual(tools[name].meta["ui"]["visibility"], ["app"])
                self.assertEqual(tools[name].meta["ui"]["resourceUri"], DESK_URI)
        visible_only_to_the_app = {n for n, t in tools.items() if (t.meta or {}).get("ui", {}).get("visibility") == ["app"]}
        self.assertEqual(visible_only_to_the_app, {"desk_sync", "desk_finish"})

    def test_r7_11_the_view_receives_structured_content_from_its_tools(self):
        """R7.11: the view reads each app-only tool's answer from structuredContent, as a host
        receives it through the MCP layer, and its text carries the same JSON."""
        self.codebook_view()

        def over_the_wire(name, args):
            res = asyncio.run(server.mcp.call_tool(name, args))
            self.assertFalse(res.is_error)
            self.assertIsNotNone(res.structured_content, name)
            self.assertEqual(json.loads(res.content[0].text), res.structured_content)
            return res.structured_content

        loaded = over_the_wire("desk_sync", {"desk_id": self.desk_id})
        self.assertEqual(set(loaded), {"desk_id", "saved", "finished", "document", "a2ui"})
        self.assertEqual(a2ui.validate(loaded["a2ui"]), [])
        n = len(self.data["cards"])
        for i, card in enumerate(self.data["cards"]):
            surf.set_path(self.data, f"/cards/{i}/action", ["adopt"])
            name, context = surf.fire(self.found, self.data, surf.button(self.found, surf.card_component(self.found, card["card_id"]), "save_decision"))
            saved = over_the_wire("desk_sync", {"desk_id": self.desk_id, "action": {"name": name, "context": context}})
            self.assertEqual((set(saved), saved["saved"]), ({"desk_id", "saved", "document", "a2ui"}, i + 1))
        self.assertEqual(n, len(self.saved()["decisions"]))
        over_the_wire("desk_sync", {"desk_id": self.desk_id, "action": {"name": "answer_exclusive", "context": {"exclusive": ["no"]}}})
        outcome = over_the_wire("desk_finish", {"desk_id": self.desk_id})
        self.assertRegex(outcome["ratification_id"], r"^ratification-[0-9a-f]{8}$")

    def test_a_save_is_kept_on_the_server_one_decision_at_a_time(self):
        self.codebook_view()
        self.assertEqual(self.saved(), {"decisions": {}, "exclusive": None})  # opening the view holds the desk, saving nothing
        out = self.press("code-02", action=["merge"], target=["Land tenure"], note=" Same thing. ")
        self.assertEqual(self.saved(), {"decisions": {"code-02": {"action": "merge", "target": "Land tenure", "note": "Same thing."}},
                                        "exclusive": None})
        self.assertEqual(out["saved"], 1)
        self.assertTrue(self.data["status"]["cards"][1]["done"])
        self.press("exclusivity", name="answer_exclusive", answer=["yes"])
        self.assertIs(self.saved()["exclusive"], True)
        # Saving a card again replaces its decision; the note still in its field goes with it.
        self.press("code-02", action=["adopt"])
        self.assertEqual(self.saved()["decisions"], {"code-02": {"action": "adopt", "note": "Same thing."}})

    def test_a_decision_the_desk_cannot_take_is_refused_and_not_saved(self):
        self.codebook_view()
        with self.assertRaisesRegex(ValueError, r"^This decision cannot be saved:\n- code-01: Shared labour is merged into 'Not a code'"):
            self.press("code-01", action=["merge"], target=["Not a code"])
        with self.assertRaisesRegex(ValueError, "Choose what to do with code-01"):
            self.press("code-01", action=[])
        self.assertEqual(self.saved(), {"decisions": {}, "exclusive": None})  # opening the view holds the desk, saving nothing
        for action, message in (({"name": "save_decision", "context": {"card_id": "code-99"}}, "code-99 is not a card on this desk"),
                                ({"name": "ratify", "context": {}}, "'ratify' is not an action"),
                                ({"context": {}}, r"^An action is \{name, context\}, as the desk's Save control sends it\.$"),
                                ({"name": "save_decision", "context": "code-01"}, "^An action is"), ("x", "^An action is")):
            with self.subTest(action), self.assertRaisesRegex(ValueError, message):
                desk_sync(self.desk_id, action)
        self.assertEqual(self.saved(), {"decisions": {}, "exclusive": None})  # opening the view holds the desk, saving nothing

    def test_r7_9_reopening_restores_every_saved_decision(self):
        self.rulings_view()
        self.press("chunk-7", codes=["Food access"])           # departs: the rule question stays open
        self.press("chunk-9", codes=["Land tenure", "Municipal relations"])
        reopened = desk_sync(self.desk_id)
        self.assertEqual(set(reopened), {"desk_id", "saved", "finished", "document", "a2ui"})
        self.assertEqual(reopened["document"], self.document())
        self.assertIsNone(reopened["finished"])
        self.assertEqual((reopened["desk_id"], reopened["saved"]), (self.desk_id, 2))
        restored = reopened["a2ui"]
        self.assertEqual(a2ui.validate(restored), [])
        # The ruling that departs from its proposal comes back asking whether it states a rule.
        found = surf.components(restored)
        asks = {n: any(found[k]["component"] == "ChoiceGroup" and found[k].get("value", {}).get("@path", "").endswith("/is_rule")
                       for k in surf.subtree(found, surf.card_component(found, f"chunk-{n}"))) for n in (7, 9)}
        self.assertEqual(asks, {7: True, 9: False})
        status = surf.data_model(restored)["status"]
        self.assertEqual([c["done"] for c in status["cards"]], [False, True, False, False])
        self.assertTrue(status["cards"][0]["open"])  # the ruling still waiting on its rule answer
        self.assertEqual(status["progress"], {"done": 1, "current": 0, "left": 3})
        # Both saved rulings have their proposals released; the undecided cards' stay hidden.
        shown = json.dumps(restored)
        for chunk, released in (("7", True), ("9", True), ("11", False), ("12", False)):
            with self.subTest(chunk):
                self.assertEqual(load("proposals")[chunk]["rationale"] in shown, released)

    def test_r7_3_the_document_the_view_holds_is_a_complete_decisions_document(self):
        """R7.3: what Copy decisions as JSON copies in the app, once everything is decided,
        reads as a decisions document and passes the import gate's full check."""
        self.codebook_view()
        for card in self.store.read(self.desk_id)["payload"]["cards"]:
            self.press(card["card_id"], action=["adopt"])
        out = self.press("exclusivity", name="answer_exclusive", answer=["no"])
        doc = decisions.parse(out["document"])
        self.assertEqual(decisions.validate(gate.load_desk(self.store, self.desk_id), doc, complete=True), [])

    def test_an_exclusivity_answer_saved_alone_is_restored(self):
        self.codebook_view()
        self.press("exclusivity", name="answer_exclusive", answer=["no"])
        status = surf.data_model(desk_sync(self.desk_id)["a2ui"])["status"]
        self.assertEqual(status["exclusivity"], {"open": False, "done": True, "result": "Not mutually exclusive"})
        self.assertTrue(status["cards"][0]["open"])

    def test_saved_decisions_for_cards_the_desk_lacks_are_refused(self):
        self.rulings_view()
        decisions = {"chunk-98": {"codes": ["Food access"]}, "chunk-99": {"none_apply": True}}
        self.store.save_artifact(self.desk_id, "saved.json", json.dumps({"decisions": decisions, "exclusive": None}))
        with self.assertRaisesRegex(ValueError, "^The saved decisions name cards this desk lacks: chunk-98, chunk-99.$"):
            desk_sync(self.desk_id)

    def test_restoring_nothing_is_the_desk_as_built(self):
        desk = gate.load_desk(self.store, self.rulings()[1].structured_content["desk_id"])
        self.assertEqual(a2ui.restore(desk, {}), a2ui.surface(desk))
        self.assertEqual(a2ui.restore(desk, {"decisions": {}, "exclusive": None}), a2ui.surface(desk))

    def test_r3_9_proposal_only_in_response_saving_its_ruling(self):
        self.rulings_view()
        rationales = {k: v["rationale"] for k, v in load("proposals").items()}
        self.assertFalse(any(text in json.dumps(self.messages) for text in rationales.values()))
        out = self.press("chunk-9", codes=["Land tenure", "Municipal relations"])
        sent = json.dumps(out["a2ui"])
        self.assertEqual([k for k, text in rationales.items() if text in sent], ["9"])

    def test_blind_first_off_shows_every_proposal_from_the_start(self):
        self.rulings_view(blind_first=False)
        shown = json.dumps(self.messages)
        self.assertTrue(all(p["rationale"] in shown for p in load("proposals").values()))

    def test_desk_finish_runs_the_gate_on_what_was_saved(self):
        stored = self.codebook_view()
        for card in stored["cards"]:
            self.press(card["card_id"], action=["adopt"])
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            desk_finish(self.desk_id)
        self.assertEqual(self.jobs("ratification"), [])
        self.press("exclusivity", name="answer_exclusive", answer=["no"])
        outcome = desk_finish(self.desk_id)
        self.assertEqual(self.jobs("ratification"), [outcome["ratification_id"]])
        decided = [e for e in record.read(self.store, self.desk_id) if e["decided_by"] == "researcher"]
        self.assertEqual({e["surface"] for e in decided}, {"app"})
        self.assertEqual(desk_finish(self.desk_id), outcome)  # Ratify pressed twice
        with self.assertRaisesRegex(ValueError, "finished"):
            self.press("code-01", action=["delete"])

    def test_r7_8_only_app_only_tool_mints_for_app_desk(self):
        stored = self.codebook_view()
        self.press("code-01", action=["adopt"])
        doc = {"schema": "aat/desk-decisions@1", "desk_id": self.desk_id, "card_checksum": stored["card_checksum"],
               "exclusive": False, "decisions": {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}}
        for surface in ("chat", "page"):
            with self.subTest(surface), self.assertRaisesRegex(ValueError, "Ratify"):
                server.record_desk_decisions(self.desk_id, doc, surface)
        self.assertEqual(self.jobs("ratification"), [])

    def test_r7_8_opening_the_view_holds_the_desk_for_it(self):
        stored = self.codebook_view()  # the view has loaded the desk; nothing is saved yet
        doc = {"schema": "aat/desk-decisions@1", "desk_id": self.desk_id, "card_checksum": stored["card_checksum"],
               "exclusive": False, "decisions": {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}}
        with self.assertRaisesRegex(ValueError, "Ratify"):
            server.record_desk_decisions(self.desk_id, doc, "chat")
        self.assertEqual(self.jobs("ratification"), [])

    def test_a_desk_finished_before_its_view_opened_says_so(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases)
        desk_id, stored = result.structured_content["desk_id"], self.payload(result)
        doc = {"schema": "aat/desk-decisions@1", "desk_id": desk_id, "card_checksum": stored["card_checksum"],
               "exclusive": False, "decisions": {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}}
        outcome = server.record_desk_decisions(desk_id, doc, "chat")
        loaded = desk_sync(desk_id)
        self.assertEqual(loaded["finished"], outcome)
        self.assertIsNone(self.store.load_artifact(desk_id, "saved.json"))
        self.assertIsNone(desk_sync(self.codebook_view_id())["finished"])

    def codebook_view_id(self):
        self.codebook_view()
        return self.desk_id

    def test_a_save_that_breaks_another_saved_decision_is_refused(self):
        self.codebook_view()
        self.press("code-02", action=["merge"], target=["Shared labour"])
        for fields in ({"action": ["delete"]}, {"action": ["merge"], "target": ["Land tenure"]}):
            with self.subTest(fields), self.assertRaisesRegex(ValueError, r"(?m)^This decision cannot be saved:\n- code-02: "):
                self.press("code-01", **fields)
        self.assertEqual(self.saved()["decisions"], {"code-02": {"action": "merge", "target": "Shared labour"}})

    def test_a_label_another_code_keeps_is_refused_when_saved(self):
        self.codebook_view()
        with self.assertRaisesRegex(ValueError, "code-01 gives the label 'Charity framing'"):
            self.press("code-01", action=["reword"], definition="Work.", label="Charity framing")
        with self.assertRaisesRegex(ValueError, "code-01 gives the label 'Land tenure'"):
            self.press("code-01", action=["split"], parts="Rosters: Who works when.\nLand tenure: The lease.")
        self.assertIsNone(self.saved()["decisions"].get("code-01"))

    def test_an_interrupted_ratify_holds_the_decisions_until_ratify_again(self):
        stored = self.codebook_view()
        for card in stored["cards"]:
            self.press(card["card_id"], action=["adopt"])
        self.press("exclusivity", name="answer_exclusive", answer=["no"])
        with mock.patch.object(record, "append", side_effect=OSError("disk full")), self.assertRaises(OSError):
            desk_finish(self.desk_id)
        with self.assertRaisesRegex(ValueError, r"^Ratify was interrupted before it finished\. Press Ratify again to complete it; "
                                                r"the decisions cannot change until it does\.$"):
            self.press("code-01", action=["delete"])
        outcome = desk_finish(self.desk_id)
        self.assertEqual(self.jobs("ratification"), [outcome["ratification_id"]])

    def test_saves_and_ratify_take_turns(self):
        """Saving reads, changes and writes the saved decisions; two at once must not lose one."""
        stored = self.codebook_view()
        started, release = threading.Event(), threading.Event()
        real = server._saved

        def slow(desk_id):
            state = real(desk_id)
            if threading.current_thread().name == "first":
                started.set()
                release.wait(2)
            return state

        context = {c["card_id"]: surf.fire(self.found, self.data, surf.button(self.found, surf.card_component(self.found, c["card_id"]), "save_decision"))[1]
                   for c in stored["cards"][:2]}
        for card_id in context:
            context[card_id]["decision"]["action"] = ["adopt"]
        with mock.patch.object(server, "_saved", side_effect=slow):
            first = threading.Thread(target=desk_sync, name="first",
                                     args=(self.desk_id, {"name": "save_decision", "context": context["code-01"]}))
            first.start()
            started.wait(2)
            second = threading.Thread(target=desk_sync, name="second",
                                      args=(self.desk_id, {"name": "save_decision", "context": context["code-02"]}))
            second.start()
            release.set()
            first.join(2)
            second.join(2)
        self.assertEqual(sorted(self.saved()["decisions"]), ["code-01", "code-02"])

    def test_damaged_saved_decisions_are_refused_by_name(self):
        self.codebook_view()
        for damaged in ({"decisions": {}}, {"decisions": {"code-01": "adopt"}, "exclusive": None}, ["x"], {"decisions": [], "exclusive": None},
                        {"decisions": {}, "exclusive": "no"}):
            self.store.save_artifact(self.desk_id, "saved.json", json.dumps(damaged))
            for call in (lambda: desk_sync(self.desk_id), lambda: desk_finish(self.desk_id)):
                with self.subTest(damaged), self.assertRaisesRegex(
                    ValueError, f"^The decisions saved for {self.desk_id} are damaged; build the desk again to decide it\\.$"):
                    call()

    def test_ratify_with_nothing_decided_names_what_is_open(self):
        self.codebook_view()
        with self.assertRaisesRegex(ValueError, r"(?s)^These decisions cannot be applied:\n- code-01.*no decision.*mutually exclusive"):
            desk_finish(self.desk_id)
        self.assertEqual(self.jobs("ratification"), [])

    def test_restoring_a_finished_desk_shows_every_decision_done(self):
        stored = self.codebook_view()
        for card in stored["cards"]:
            self.press(card["card_id"], action=["adopt"])
        self.press("exclusivity", name="answer_exclusive", answer=["yes"])
        outcome = desk_finish(self.desk_id)
        loaded = desk_sync(self.desk_id)
        self.assertEqual(loaded["finished"], outcome)
        status = surf.data_model(loaded["a2ui"])["status"]
        self.assertEqual(status["progress"]["left"], 0)

    def test_a_rulings_desk_takes_no_exclusivity_answer(self):
        self.rulings_view()
        with self.assertRaisesRegex(ValueError, "'answer_exclusive' is not an action that records a decision on a rulings desk"):
            desk_sync(self.desk_id, {"name": "answer_exclusive", "context": {"exclusive": ["yes"]}})

    def test_r5_5_app_route_and_json_route_give_identical_results(self):
        ruled = {"chunk-7": {"codes": ["Food access"], "is_rule": True, "rule_text": "Selling below cost is food access."},
                 "chunk-9": {"codes": ["Land tenure", "Municipal relations"]},
                 "chunk-11": {"exclude": {"reason": "Not about the garden."}},
                 "chunk-12": {"none_apply": True, "is_rule": False}}
        rid = self.ratified()
        jobs = [self.coding_job("coding_a", rid), self.coding_job("coding_b", rid)]
        by_app = server.build_ratification_desk(stage="rulings", coding_job_ids=jobs, proposals=load("proposals"))
        by_json = server.build_ratification_desk(stage="rulings", coding_job_ids=jobs, proposals=load("proposals"))
        self.open_view(by_app.structured_content["desk_id"])
        self.press("chunk-7", codes=["Food access"], is_rule=["yes"], rule_text="Selling below cost is food access.")
        self.press("chunk-9", codes=["Land tenure", "Municipal relations"])
        self.press("chunk-11", name="exclude_chunk", reason="Not about the garden.")
        self.press("chunk-12", codes=[surf.NO_CODE], is_rule=["no"])
        app = desk_finish(self.desk_id)
        json_id = by_json.structured_content["desk_id"]
        doc = {"schema": "aat/desk-decisions@1", "desk_id": json_id, "card_checksum": self.payload(by_json)["card_checksum"],
               "exclusive": None, "decisions": ruled}
        chat = server.record_desk_decisions(json_id, doc, "page")
        def same(outcome):
            return {k: v for k, v in outcome.items() if k not in ("desk_id", "ratification_id")}
        self.assertEqual(same(app), same(chat))
        for name in ("result.json",):
            self.assertEqual(self.store.load_artifact(app["ratification_id"], name), self.store.load_artifact(chat["ratification_id"], name))
        held = [json.loads(self.store.load_artifact(o["ratification_id"], "ratification.json")) for o in (app, chat)]
        for h in held:
            h.pop("desk_id")
            for amendment in h["amendments"]:
                amendment.pop("desk_id")
        self.assertEqual(held[0], held[1])
        self.assertEqual(self.store.load_artifact(self.desk_id, "result.json"), self.store.load_artifact(json_id, "result.json"))
        decided = [[(e["card_id"], e["action"], e["detail"], e["note"]) for e in record.read(self.store, d) if e["decided_by"] == "researcher" and e["action"] != "ratify"]
                   for d in (self.desk_id, json_id)]
        self.assertEqual(decided[0], decided[1])


class TestDecisionRecord(DeskCase):
    """get_decision_record: the record behind a ratification or a desk, and the paragraph."""

    PARAGRAPH = (
        "Assembled from the decision record, not written by the researcher; check it against "
        "your own account before you use it. "
        "A model drafted a codebook of 6 codes. The researcher ratified it on a codebook desk, "
        "deciding each code against the cases it would take: 5 adopted and 1 reworded. The researcher "
        "judged the codes not mutually exclusive. This made codebook version 1.0. "
        "A rulings desk presented 4 chunks on which two coding passes disagreed, with "
        "blind-first on, so each model proposal stayed hidden until the researcher had saved "
        "a ruling on its chunk. The researcher ruled on 3 and excluded 1 from the analysis. "
        "1 ruling departed from the proposal, and 1 was adopted as a rule, amending the "
        "codebook to version 1.1. "
        "8 chunks on which both passes agreed were coded under version 1.0 and have not been "
        "rechecked against the amendment."
    )

    def doc(self, desk_id, stored, decisions, exclusive=None):
        return {"schema": "aat/desk-decisions@1", "desk_id": desk_id, "card_checksum": stored["card_checksum"],
                "exclusive": exclusive, "decisions": decisions}

    def codebook_desk(self):
        result = server.build_ratification_desk(stage="codebook", codebook_job_id=self.codebook_job(), cases=self.cases)
        return result.structured_content["desk_id"], self.payload(result)

    def ratified_on_a_desk(self):
        desk_id, stored = self.codebook_desk()
        decisions = {c["card_id"]: {"action": "adopt"} for c in stored["cards"]}
        decisions["code-01"] = {"action": "reword", "definition": "Garden work members share out between them."}
        outcome = server.record_desk_decisions(desk_id, self.doc(desk_id, stored, decisions, False), "page")
        return desk_id, outcome["ratification_id"]

    def rulings_desk(self, rid):
        _, result = self.rulings(ratification_id=rid, proposals=load("proposals"))
        return result.structured_content["desk_id"], self.payload(result)

    def amended(self):
        first_desk, rid = self.ratified_on_a_desk()
        desk_id, stored = self.rulings_desk(rid)
        decisions = {c["card_id"]: {"codes": c["proposal"]["codes"]} if c["proposal"]["codes"] else {"none_apply": True}
                     for c in stored["cards"]}
        decisions["chunk-7"] = {"codes": ["Food access"], "is_rule": True,
                                "rule_text": "Selling produce below cost counts as food access, not charity."}
        decisions["chunk-11"] = {"exclude": {"reason": "Not about the garden."}}
        outcome = server.record_desk_decisions(desk_id, self.doc(desk_id, stored, decisions), "chat")
        return first_desk, rid, desk_id, outcome["ratification_id"]

    def test_r6_3_record_tool_returns_counted_paragraph(self):
        first_desk, _, rulings_desk, amended = self.amended()
        out = server.get_decision_record(ratification_id=amended)
        self.assertEqual(out["paragraph"], self.PARAGRAPH)
        self.assertEqual(out["ratification_id"], amended)
        self.assertEqual(out["record"], record.read(self.store, first_desk) + record.read(self.store, rulings_desk))
        self.assertEqual(set(out), {"ratification_id", "desk_id", "record", "paragraph"})
        self.assertIsNone(out["desk_id"])

    def test_a_finished_desk_leads_to_the_ratification_it_made(self):
        first_desk, rid, rulings_desk, amended = self.amended()
        out = server.get_decision_record(desk_id=rulings_desk)
        self.assertEqual((out["ratification_id"], out["desk_id"]), (amended, rulings_desk))
        self.assertEqual(out["paragraph"], self.PARAGRAPH)
        earlier = server.get_decision_record(desk_id=first_desk)
        self.assertEqual(earlier["ratification_id"], rid)
        self.assertEqual(earlier["record"], record.read(self.store, first_desk) + record.read(self.store, rulings_desk))

    def test_an_unfinished_rulings_desk_reads_under_the_ratification_in_force(self):
        first_desk, rid = self.ratified_on_a_desk()
        desk_id, _ = self.rulings_desk(rid)
        out = server.get_decision_record(desk_id=desk_id)
        self.assertEqual(out["ratification_id"], rid)
        self.assertEqual(out["record"], record.read(self.store, first_desk) + record.read(self.store, desk_id))
        self.assertIn("The rulings desk has not been finished.", out["paragraph"])

    def test_an_unfinished_codebook_desk_reads_its_own_record(self):
        desk_id, _ = self.codebook_desk()
        out = server.get_decision_record(desk_id=desk_id)
        self.assertEqual((out["ratification_id"], out["desk_id"]), (None, desk_id))
        self.assertEqual(out["record"], record.read(self.store, desk_id))
        self.assertEqual([e["decided_by"] for e in out["record"]], ["machine"] * 7)  # the build, then six drafts
        self.assertIn("The codebook desk has not been finished.", out["paragraph"])

    def test_a_ratification_made_from_a_table_holds_no_desk_decisions(self):
        out = server.get_decision_record(ratification_id=self.ratified())
        self.assertEqual(out["record"], [])
        self.assertTrue(out["paragraph"].endswith(" The record holds no desk decisions."))

    def test_one_of_the_two_ids_is_required(self):
        desk_id, rid = self.ratified_on_a_desk()
        for kw, message in (({}, r"^Pass ratification_id or desk_id\.$"),
                            ({"ratification_id": " ", "desk_id": ""}, r"^Pass ratification_id or desk_id\.$"),
                            ({"ratification_id": rid, "desk_id": desk_id}, r"^Pass ratification_id or desk_id, not both\.$")):
            with self.subTest(kw), self.assertRaisesRegex(ValueError, message):
                server.get_decision_record(**kw)

    def test_ids_of_the_wrong_kind_are_refused(self):
        desk_id, rid = self.ratified_on_a_desk()
        with self.assertRaisesRegex(ValueError, f"^'{desk_id}' is not a ratification job\\.$"):
            server.get_decision_record(ratification_id=desk_id)
        with self.assertRaisesRegex(ValueError, f"^{rid} is not a desk\\.$"):
            server.get_decision_record(desk_id=rid)
        with self.assertRaises(ValueError):
            server.get_decision_record(ratification_id="ratification-nonexistent")

    def test_the_tool_only_reads(self):
        tool = asyncio.run(server.mcp.list_tools())
        [found] = [t for t in tool if t.name == "get_decision_record"]
        self.assertTrue(found.annotations.read_only_hint)


class TestTableRatification(DeskCase):
    """ratify_codebook, the one-table path, keeps its behaviour and names its method (R7.5)."""

    def test_r7_5_table_ratification_records_method_table(self):
        job_id = self.codebook_job()
        for kw in ({"codebook": self.codebook}, {"codebook_job_id": job_id}):
            with self.subTest(sorted(kw)):
                out = server.ratify_codebook(note="Merged two codes.", **kw)
                self.assertEqual(set(out), {"ratification_id", "checksum", "codes", "note", "next"})
                self.assertEqual((out["codes"], out["note"]), (6, "Merged two codes."))
                held = json.loads(self.store.load_artifact(out["ratification_id"], "ratification.json"))
                self.assertEqual(held, {"checksum": out["checksum"], "codes": 6, "note": "Merged two codes.",
                                        "method": "table", "version": "1.0"})
                job = server.start_coding_job(chunks=[{"chunk_id": 1, "text": "x"}],
                                              ratification_id=out["ratification_id"], llm_mode="delegated")
                self.assertEqual(json.loads(self.store.load_artifact(job["job_id"], "codebook.json")), self.codebook)

    def test_ratifying_a_codebook_job_again_keeps_its_desks_and_method(self):
        job_id = self.codebook_job()
        rid = server.ratify_codebook(codebook_job_id=job_id)["ratification_id"]
        self.rulings(ratification_id=rid)
        server.ratify_codebook(codebook_job_id=job_id)
        held = json.loads(self.store.load_artifact(rid, "ratification.json"))
        self.assertEqual((held["method"], held["version"], len(held["desks"])), ("table", "1.0", 1))


class TestPagesHostsBuild(DeskCase):
    """What the server tells a host that builds its own page from toolkit output (R8.8)."""

    SYSTEM = f"{brand.REPOSITORY}/tree/main/design/system"

    def says_credit_and_system(self, text, where):
        flat = " ".join(text.split())
        self.assertIn(f'"{brand.CREDIT}" linked to {brand.WEBSITE}', flat, where)
        self.assertIn(f"the toolkit design system ({self.SYSTEM})", flat, where)
        self.assertNotIn("monochrome", flat.lower(), where)

    def test_r8_8_instructions_name_credit_and_design_system(self):
        self.says_credit_and_system(server.mcp.instructions, "server instructions")
        self.assertRegex(" ".join(server.mcp.instructions.split()), r"Any page you build from toolkit output")

    def test_the_network_fallback_names_credit_and_design_system(self):
        from tests.package.test_network import CODED
        result = server.view_network(server.build_network(CODED))
        self.says_credit_and_system(result.content[0].text, "view_network result")
        [tool] = [t for t in asyncio.run(server.mcp.list_tools()) if t.name == "view_network"]
        self.says_credit_and_system(tool.description, "view_network description")
        self.assertIn("keep the node colors", " ".join(result.content[0].text.split()))

    def test_the_design_system_link_points_at_the_shipped_system(self):
        self.assertTrue((Path(__file__).resolve().parents[2] / "design" / "system" / "README.md").is_file())


class TestRegistration(DeskCase):
    def test_r7_6_tool_carries_desk_resource_uri(self):
        tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
        self.assertEqual(tools["build_ratification_desk"].meta["ui"]["resourceUri"], DESK_URI)
        [resource] = [r for r in asyncio.run(server.mcp.list_resources()) if str(r.uri) == DESK_URI]
        self.assertEqual(resource.mime_type, "text/html;profile=mcp-app")
        self.assertEqual(resource.meta["ui"]["csp"]["resourceDomains"], list(design.FONT_DOMAINS))
        [content] = asyncio.run(server.mcp.read_resource(DESK_URI))
        self.assertEqual(content.content, page.app_shell())

    def test_the_result_tells_the_model_the_researcher_decides(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases)
        text = result.content[0].text
        self.assertRegex(text, r"researcher decides")
        self.assertRegex(text, r"(?i)do not (?:record|make) (?:any )?decisions")
        tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
        self.assertRegex(tools["build_ratification_desk"].description, r"(?i)never .*on the researcher's behalf")

    def test_refusals_reach_the_model_through_the_mcp_boundary(self):
        with self.assertRaisesRegex(ToolError, "no case: Land tenure"):
            asyncio.run(server.mcp.call_tool("build_ratification_desk", {
                "stage": "codebook", "codebook": self.codebook,
                "cases": {k: v for k, v in self.cases.items() if k != "Land tenure"}}))

    def test_the_built_page_carries_no_job_store_path(self):
        result = server.build_ratification_desk(stage="codebook", codebook=self.codebook, cases=self.cases)
        html = Path(result.structured_content["page"]).read_text(encoding="utf-8")
        self.assertNotIn(self._dir.name, html)
        self.assertIsNone(re.search(r"/Users/[A-Za-z]|/home/[A-Za-z]|file://", html))



# What reading or writing a hosted artifact's database looks like in the desk's code: the
# artifact runtime's own object, and the database calls and names that R7.1 withdrew.
_ARTIFACT_DB = re.compile(r"window\.claude|window\.storage|ArtifactData|\b(?:read|write)_db\b|artifact[_ -]?(?:db|database)", re.I)


class TestWithdrawnArtifactDatabase(unittest.TestCase):
    def files(self):
        desk = Path(page.__file__).parent
        found = [p for p in desk.rglob("*") if p.suffix in {".py", ".js", ".mjs", ".html"} and "node_modules" not in p.parts]
        return [*found, Path(server.__file__)]

    def test_r7_1_no_artifact_database_path(self):
        """R7.1 is withdrawn: decisions are saved on the server through the MCP App (R7.6-R7.9)
        or in the browser (R7.2), and no desk module, page or bundle reads or writes an
        artifact's database."""
        files = self.files()
        self.assertIn("desk-app.js", {p.name for p in files})
        for path in files:
            with self.subTest(path.name):
                self.assertIsNone(_ARTIFACT_DB.search(path.read_text(encoding="utf-8")))

    def test_the_guard_finds_an_artifact_database_call(self):
        for line in ("await window.claude.db.set('d', x)", "window.storage.get(key)", "write_db(collection)",
                     "the artifact database", "ArtifactData"):
            with self.subTest(line):
                self.assertIsNotNone(_ARTIFACT_DB.search(line))


if __name__ == "__main__":
    unittest.main()
