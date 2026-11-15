"""Desk cards: one per code for a codebook desk, one per disagreement for a rulings desk."""

import copy
import json
import unittest
from pathlib import Path

from ai_anthro_toolkit.desk import cards

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "desk"


def _load(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


class TestRulingsCards(unittest.TestCase):
    def setUp(self):
        self.codebook = _load("codebook")
        self.a, self.b = _load("coding_a"), _load("coding_b")
        self.proposals = _load("proposals")

    def _cards(self, **changes):
        args = {"job_a": self.a, "job_b": self.b, "codebook": self.codebook, "proposals": self.proposals}
        args.update(changes)
        return cards.rulings_cards(**args)

    def test_r1_3_cards_only_for_chunks_whose_code_sets_differ(self):
        built = self._cards()
        self.assertEqual([c["chunk_id"] for c in built], ["7", "9", "11", "12"])
        self.assertEqual([c["card_id"] for c in built], ["chunk-7", "chunk-9", "chunk-11", "chunk-12"])

    def test_r1_3_order_of_codes_is_not_a_disagreement(self):
        self.a[8]["Deductive_Codes"] = "Land tenure, Municipal relations"
        self.b[8]["Deductive_Codes"] = "Municipal relations,Land tenure"
        del self.proposals["9"]
        self.assertNotIn("9", [c["chunk_id"] for c in self._cards()])

    def test_r1_3_inductive_codes_make_no_card(self):
        # coding_a carries an inductive code on chunk 1 that coding_b lacks.
        self.assertNotEqual(self.a[0]["Inductive_Codes"], self.b[0]["Inductive_Codes"])
        self.assertNotIn("1", [c["chunk_id"] for c in self._cards()])

    def test_r1_3_no_disagreement_no_cards(self):
        self.assertEqual(cards.rulings_cards(self.a, copy.deepcopy(self.a), self.codebook, None), [])

    def test_r3_1_card_carries_text_both_coders_and_their_entries(self):
        card = self._cards()[1]
        self.assertEqual(card["text"], "The council said the permit covers the shed but not the tunnel.")
        self.assertEqual(card["source"], "interview-04.txt")
        # Each coder's codes, in codebook order.
        self.assertEqual(card["coder_a"], ["Land tenure", "Municipal relations"])
        self.assertEqual(card["coder_b"], ["Municipal relations"])
        self.assertEqual(card["entries"], {
            "Land tenure": "Who holds the plot and on what terms.",
            "Municipal relations": "Dealings with the city or its staff.",
        })

    def test_r3_1_a_chunk_one_coder_left_uncoded_has_an_empty_list(self):
        card = self._cards()[3]
        self.assertEqual((card["coder_a"], card["coder_b"]), (["Shared labour"], []))

    def test_proposals_attach_to_their_cards(self):
        built = self._cards()
        self.assertEqual(built[0]["proposal"], {
            "codes": ["Charity framing"],
            "rationale": "Giving the harvest away is the point of the passage.",
        })
        self.assertIsNone(self._cards(proposals=None)[0]["proposal"])
        del self.proposals["11"]
        self.assertIsNone(self._cards()[2]["proposal"])

    def test_proposal_for_a_chunk_not_on_the_desk_is_refused(self):
        self.proposals["3"] = {"codes": ["Land tenure"], "rationale": "Both coders agree."}
        with self.assertRaisesRegex(ValueError, r"chunk 3\b.*no disagreement"):
            self._cards()

    def test_proposal_naming_a_code_outside_the_codebook_is_refused(self):
        self.proposals["7"]["codes"] = ["Gift economy"]
        with self.assertRaisesRegex(ValueError, r"chunk 7.*'Gift economy'"):
            self._cards()

    def test_a_proposal_of_no_codes_means_no_code_applies(self):
        self.proposals["12"]["codes"] = []
        self.assertEqual(self._cards()[3]["proposal"]["codes"], [])

    def test_a_proposal_must_list_its_codes(self):
        del self.proposals["7"]["codes"]
        with self.assertRaisesRegex(ValueError, r"chunk 7.*list of codes"):
            self._cards()
        self.proposals["7"]["codes"] = "Charity framing"
        with self.assertRaisesRegex(ValueError, r"chunk 7.*list of codes"):
            self._cards()

    def test_code_outside_the_codebook_is_refused(self):
        self.b[6]["Deductive_Codes"] = "Shared labour,Gift economy"
        with self.assertRaisesRegex(ValueError, r"'Gift economy'.*not in the codebook"):
            self._cards()

    def test_jobs_over_different_chunks_are_refused(self):
        with self.assertRaisesRegex(ValueError, r"did not code the same chunks.*12"):
            self._cards(job_b=self.b[:-1])

    def test_jobs_with_different_text_for_a_chunk_are_refused(self):
        self.b[2]["text"] = "Something else entirely."
        with self.assertRaisesRegex(ValueError, r"chunk 3.*different text"):
            self._cards()

    def test_records_without_a_chunk_id_are_refused(self):
        del self.a[4]["chunk_id"]
        with self.assertRaisesRegex(ValueError, r"1 record.*no chunk_id"):
            self._cards()

    def test_a_chunk_coded_twice_in_one_job_is_refused(self):
        self.a.append(copy.deepcopy(self.a[0]))
        with self.assertRaisesRegex(ValueError, r"chunk 1.*more than once"):
            self._cards()


    def test_an_empty_or_missing_code_field_is_no_codes(self):
        self.a[0]["Deductive_Codes"], self.b[0]["Deductive_Codes"] = None, float("nan")
        self.a[1]["Deductive_Codes"], self.b[1]["Deductive_Codes"] = " , ", ""
        self.assertEqual([c["chunk_id"] for c in self._cards()], ["7", "9", "11", "12"])
        self.a[0]["Deductive_Codes"] = "Shared labour"
        self.assertEqual(self._cards()[0]["coder_b"], [])

    def test_source_prefers_a_source_field(self):
        self.a[6]["source"] = "Interview 07, p. 3"
        self.assertEqual(self._cards()[0]["source"], "Interview 07, p. 3")

    def test_refusals_name_the_coding_job(self):
        self.b.append(copy.deepcopy(self.b[0]))
        with self.assertRaisesRegex(ValueError, r"chunk 1 appears more than once in the second coding job"):
            self._cards()
        self.b.pop()
        del self.b[3]["chunk_id"], self.b[4]["chunk_id"]
        with self.assertRaisesRegex(ValueError, r"^2 records in the second coding job have no chunk_id\.$"):
            self._cards()

    def test_one_unplaced_record_is_singular(self):
        del self.a[4]["chunk_id"]
        with self.assertRaisesRegex(ValueError, r"^1 record in the first coding job has no chunk_id\.$"):
            self._cards()

    def test_chunks_only_in_one_job_are_listed_by_job(self):
        extra = {**copy.deepcopy(self.b[0]), "chunk_id": 13}

        def refusal(job_a, job_b):
            with self.assertRaises(ValueError) as caught:
                self._cards(job_a=job_a, job_b=job_b)
            return str(caught.exception).removeprefix("The two coding jobs did not code the same chunks: ")

        self.assertEqual(refusal(self.a, [*self.b, extra]), "13 only in the second.")
        self.assertEqual(refusal([*self.a, extra], self.b[:-1]), "12, 13 only in the first.")
        # The first job holds chunks 1-11; the second 1-10 and 13.
        self.assertEqual(refusal(self.a[:-1], [*self.b[:-2], extra]), "11 only in the first; 13 only in the second.")

    def test_unknown_codes_name_the_coding_job(self):
        self.a[6]["Deductive_Codes"] = "Gift economy"
        with self.assertRaisesRegex(ValueError, r"^'Gift economy', which chunk 7 carries in the first coding job"):
            self._cards()
        self.a[6]["Deductive_Codes"] = "Charity framing"
        self.b[6]["Deductive_Codes"] = "Gift economy"
        with self.assertRaisesRegex(ValueError, r"^'Gift economy', which chunk 7 carries in the second coding job"):
            self._cards()

    def test_a_proposal_naming_two_unknown_codes_names_both(self):
        self.proposals["7"]["codes"] = ["Gift economy", "Mutual aid"]
        with self.assertRaisesRegex(ValueError, r"names 'Gift economy', 'Mutual aid', which"):
            self._cards()


class TestCodebookCards(unittest.TestCase):
    def setUp(self):
        self.codebook = _load("codebook")
        self.cases = _load("cases")

    def test_one_card_per_code_in_codebook_order(self):
        built = cards.codebook_cards(self.codebook, self.cases)
        self.assertEqual([c["card_id"] for c in built], [f"code-0{i}" for i in range(1, 7)])
        self.assertEqual([c["code_label"] for c in built], [r["code_label"] for r in self.codebook])

    def test_r2_1_card_carries_definition_criteria_and_marked_cases(self):
        card = cards.codebook_cards(self.codebook, self.cases)[2]
        self.assertEqual(card["code_label"], "Land tenure")
        self.assertEqual(card["definition"], "Who holds the plot and on what terms.")
        self.assertEqual(card["inclusion"], "Leases, permissions, ownership, eviction.")
        self.assertEqual(card["exclusion"], "Where plants are placed within the plot.")
        self.assertEqual([(c["case_id"], c["kind"]) for c in card["cases"]], [("c4", "typical"), ("c5", "borderline")])
        self.assertEqual(card["cases"][1]["source"], "Field notes, May")

    def test_r1_2_every_code_without_a_case_is_named(self):
        del self.cases["Food access"]
        self.cases["Volunteer burnout"] = []
        with self.assertRaises(ValueError) as caught:
            cards.codebook_cards(self.codebook, self.cases)
        self.assertEqual(
            str(caught.exception),
            "Can't build the desk. These codes have no case: Food access, Volunteer burnout.",
        )

    def test_cases_for_a_code_not_in_the_codebook_are_refused(self):
        self.cases["Gift economy"] = [{"text": "We swap seeds.", "kind": "typical"}]
        with self.assertRaisesRegex(ValueError, r"'Gift economy'.*not in the codebook"):
            cards.codebook_cards(self.codebook, self.cases)

    def test_a_case_must_be_typical_or_borderline(self):
        self.cases["Food access"][0]["kind"] = "edge"
        with self.assertRaisesRegex(ValueError, r"Food access.*typical or borderline"):
            cards.codebook_cards(self.codebook, self.cases)
        del self.cases["Food access"][0]["kind"]
        with self.assertRaisesRegex(ValueError, r"Food access.*typical or borderline"):
            cards.codebook_cards(self.codebook, self.cases)

    def test_a_case_needs_text(self):
        self.cases["Food access"][0]["text"] = "  "
        with self.assertRaisesRegex(ValueError, r"Food access.*no text"):
            cards.codebook_cards(self.codebook, self.cases)

    def test_cases_without_ids_or_sources_are_numbered(self):
        self.cases["Food access"] = [{"text": "Two buses.", "kind": "typical"}, {"text": "A corner shop.", "kind": "borderline"}]
        card = cards.codebook_cards(self.codebook, self.cases)[3]
        self.assertEqual([(c["case_id"], c["source"]) for c in card["cases"]], [("code-04-case-1", ""), ("code-04-case-2", "")])

    def test_a_code_listed_twice_is_refused(self):
        self.codebook.append(dict(self.codebook[0]))
        with self.assertRaisesRegex(ValueError, r"'Shared labour'.*more than once"):
            cards.codebook_cards(self.codebook, self.cases)

    def test_card_ids_widen_past_ninety_nine_codes(self):
        codebook = [{"code_label": f"Code {i}", "definition": "d"} for i in range(100)]
        cases = {f"Code {i}": [{"text": "t", "kind": "typical"}] for i in range(100)}
        built = cards.codebook_cards(codebook, cases)
        self.assertEqual((built[0]["card_id"], built[-1]["card_id"]), ("code-001", "code-100"))


    def test_a_record_without_a_label_is_refused(self):
        self.codebook[2]["code_label"] = "  "
        with self.assertRaisesRegex(ValueError, r"^A codebook record has no code_label\.$"):
            cards.codebook_cards(self.codebook, self.cases)
        del self.codebook[2]["code_label"]
        with self.assertRaisesRegex(ValueError, r"^A codebook record has no code_label\.$"):
            cards.codebook_cards(self.codebook, self.cases)

    def test_labels_are_trimmed(self):
        self.codebook[2]["code_label"] = "  Land tenure "
        self.assertEqual(cards.codebook_cards(self.codebook, self.cases)[2]["code_label"], "Land tenure")

    def test_a_code_without_a_definition_has_an_empty_one(self):
        # The desk is where a weak definition gets reworded, so a missing one is shown empty.
        del self.codebook[3]["definition"]
        self.assertEqual(cards.codebook_cards(self.codebook, self.cases)[3]["definition"], "")

    def test_cases_for_two_unknown_codes_name_both(self):
        self.cases["Gift economy"] = self.cases["Mutual aid"] = [{"text": "t", "kind": "typical"}]
        with self.assertRaisesRegex(ValueError, r"^Cases are given for 'Gift economy', 'Mutual aid', which"):
            cards.codebook_cards(self.codebook, self.cases)

    def test_a_wrong_kind_is_quoted(self):
        self.cases["Food access"][0]["kind"] = "edge"
        with self.assertRaisesRegex(ValueError, r"^A case for Food access is marked 'edge'; mark each case typical or borderline\.$"):
            cards.codebook_cards(self.codebook, self.cases)


class TestChecksum(unittest.TestCase):
    def setUp(self):
        self.built = cards.codebook_cards(_load("codebook"), _load("cases"))

    def test_r1_7_checksum_is_sixteen_hex_digits(self):
        self.assertRegex(cards.checksum(self.built), r"^[0-9a-f]{16}$")

    def test_r1_7_checksum_ignores_key_order(self):
        reordered = [dict(reversed(list(card.items()))) for card in self.built]
        self.assertEqual(cards.checksum(reordered), cards.checksum(self.built))

    def test_r1_7_checksum_changes_with_any_card_content(self):
        changed = copy.deepcopy(self.built)
        changed[5]["cases"][0]["text"] += "."
        self.assertNotEqual(cards.checksum(changed), cards.checksum(self.built))
        self.assertNotEqual(cards.checksum(self.built[::-1]), cards.checksum(self.built))

    def test_r1_7_checksum_is_stable_across_runs(self):
        # A fixed value: the checksum is stored with a desk and compared on import, so it
        # must not depend on the process (hash seeds, dict order, float formatting).
        self.assertEqual(cards.checksum([{"card_id": "code-01", "code_label": "Å"}]), _expected())


def _expected():
    import hashlib

    body = json.dumps([{"card_id": "code-01", "code_label": "Å"}], sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    unittest.main()
