"""The desk's MCP tools: building a desk from what the server holds, and the MCP App
resource the desk opens in."""

import asyncio
import json
import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from mcp.server.mcpserver.exceptions import ToolError

from ai_anthro_toolkit import design
from ai_anthro_toolkit.desk import a2ui, cards, gate, page, record
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.mcp import server
from tests.package.desk_helpers import load

DESK_URI = "ui://ai-anthropology/ratification-desk"


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


if __name__ == "__main__":
    unittest.main()
