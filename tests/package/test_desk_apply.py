"""Decisions applied: the codebook a codebook desk ratifies, and the resolutions and
amendments a rulings desk produces."""

import copy
import unittest

from ai_anthro_toolkit import crosslens
from ai_anthro_toolkit.desk import apply
from tests.package.desk_helpers import codebook_desk, load, rulings_desk


def labels(codebook):
    return [record["code_label"] for record in codebook]


def by_label(codebook):
    return {record["code_label"]: record for record in codebook}


class TestApplyActions(unittest.TestCase):
    def setUp(self):
        self.codebook = load("codebook")
        self.cards = codebook_desk()["cards"]
        self.adopt_all = {card["card_id"]: {"action": "adopt"} for card in self.cards}

    def _apply(self, **changes):
        return apply.apply_actions(self.codebook, self.cards, {**self.adopt_all, **changes})

    def test_r2_7_adopting_every_code_keeps_the_codebook(self):
        self.assertEqual(self._apply(), self.codebook)

    def test_r2_7_a_reword_changes_the_definition_and_keeps_the_rest(self):
        record = dict(self.codebook[1], example_1="We give the extra away.")
        self.codebook[1] = record
        result = self._apply(**{"code-02": {"action": "reword", "definition": "Talk of giving to those in need."}})
        self.assertEqual(result[1], dict(record, definition="Talk of giving to those in need."))

    def test_r2_7_a_reword_can_relabel(self):
        result = self._apply(**{"code-02": {"action": "reword", "definition": "Giving.", "label": "Charity"}})
        self.assertEqual(labels(result)[1], "Charity")
        self.assertEqual(result[1]["definition"], "Giving.")

    def test_r2_7_a_merge_folds_the_code_into_its_target(self):
        result = self._apply(**{"code-03": {"action": "merge", "target": "Municipal relations"}})
        self.assertNotIn("Land tenure", labels(result))
        self.assertEqual(by_label(result)["Municipal relations"], self.codebook[5])
        self.assertEqual(len(result), 5)

    def test_r2_7_a_split_puts_its_parts_where_the_code_was(self):
        parts = [{"label": "Rosters", "definition": "Who works when."}, {"label": "Workdays", "definition": "Days worked together."}]
        result = self._apply(**{"code-01": {"action": "split", "parts": parts}})
        self.assertEqual(labels(result)[:3], ["Rosters", "Workdays", "Charity framing"])
        self.assertEqual(result[0], {"code_label": "Rosters", "definition": "Who works when."})

    def test_r2_7_a_delete_drops_the_code(self):
        result = self._apply(**{"code-05": {"action": "delete"}})
        self.assertEqual(labels(result), [label for label in labels(self.codebook) if label != "Volunteer burnout"])

    def test_r2_7_actions_combine(self):
        result = self._apply(**{
            "code-01": {"action": "split", "parts": [{"label": "Rosters", "definition": "a"}, {"label": "Workdays", "definition": "b"}]},
            "code-02": {"action": "reword", "definition": "Giving.", "label": "Charity"},
            "code-03": {"action": "merge", "target": "Municipal relations"},
            "code-05": {"action": "delete"},
        })
        self.assertEqual(labels(result), ["Rosters", "Workdays", "Charity", "Food access", "Municipal relations"])

    def test_the_input_is_left_unchanged(self):
        kept = copy.deepcopy(self.codebook)
        self._apply(**{"code-02": {"action": "reword", "definition": "Giving.", "label": "Charity"}})
        self.assertEqual(self.codebook, kept)

    def test_a_result_with_one_label_twice_is_refused(self):
        clash = {"code-02": {"action": "reword", "definition": "Giving.", "label": "Food access"}}
        with self.assertRaisesRegex(ValueError, "code-02.*'Food access'.*already"):
            self._apply(**clash)
        split = {"code-01": {"action": "split", "parts": [{"label": "Food access", "definition": "a"}, {"label": "B", "definition": "b"}]}}
        with self.assertRaisesRegex(ValueError, "code-01.*'Food access'.*already"):
            self._apply(**split)
        # A label freed by a deletion or a relabel can be taken.
        freed = self._apply(**{"code-04": {"action": "delete"}, **clash})
        self.assertEqual(labels(freed)[1], "Food access")

    def test_new_labels_clash_with_kept_ones_and_with_each_other(self):
        kept = {"code-02": {"action": "reword", "definition": "Giving."},
                "code-01": {"action": "split", "parts": [{"label": "Charity framing", "definition": "a"}, {"label": "B", "definition": "b"}]}}
        with self.assertRaisesRegex(ValueError, "code-01.*'Charity framing'"):
            self._apply(**kept)
        twice = {"code-01": {"action": "reword", "definition": "a", "label": "Joint"}, "code-02": {"action": "reword", "definition": "b", "label": "Joint"}}
        with self.assertRaisesRegex(ValueError, "code-02.*'Joint'"):
            self._apply(**twice)

    def test_a_split_later_in_the_codebook_keeps_what_came_before(self):
        parts = [{"label": "Leases", "definition": "a"}, {"label": "Evictions", "definition": "b"}]
        result = self._apply(**{"code-03": {"action": "split", "parts": parts}})
        self.assertEqual(labels(result), ["Shared labour", "Charity framing", "Leases", "Evictions", "Food access", "Volunteer burnout", "Municipal relations"])

    def test_the_result_shares_nothing_with_the_input(self):
        self.codebook[0] = dict(self.codebook[0], rules=["An earlier rule."])
        result = self._apply()
        result[0]["rules"].append("Changed.")
        self.assertEqual(self.codebook[0]["rules"], ["An earlier rule."])

    def test_a_codebook_that_does_not_match_its_cards_is_refused(self):
        with self.assertRaisesRegex(ValueError, "Volunteer burnout"):
            apply.apply_actions([r for r in self.codebook if r["code_label"] != "Volunteer burnout"], self.cards, self.adopt_all)


class TestResolve(unittest.TestCase):
    def setUp(self):
        self.cards = rulings_desk()["cards"]

    def test_r4_1_rule_creates_amendment_citing_card(self):
        decided = {
            "chunk-7": {"codes": ["Shared labour"], "is_rule": True, "rule_text": " Shared work outweighs giving. "},
            "chunk-9": {"codes": ["Land tenure", "Municipal relations"]},
            "chunk-11": {"codes": ["Food access"], "is_rule": False, "rule_text": "Typed, then answered no."},
            "chunk-12": {"none_apply": True, "is_rule": True, "rule_text": "Deciding is not labour."},
        }
        _, amendments = apply.resolve(self.cards, decided)
        self.assertEqual(amendments, [
            {"source_card": "chunk-7", "rule_text": "Shared work outweighs giving.", "codes": ["Shared labour", "Charity framing", "Food access"]},
            {"source_card": "chunk-12", "rule_text": "Deciding is not labour.", "codes": ["Shared labour"]},
        ])

    def test_a_rule_names_the_codes_in_dispute_and_any_the_ruling_adds(self):
        decided = {"chunk-9": {"codes": ["Volunteer burnout"], "is_rule": True, "rule_text": "Burnout, not tenure."}}
        _, amendments = apply.resolve([self.cards[1]], decided)
        self.assertEqual(amendments[0]["codes"], ["Land tenure", "Municipal relations", "Volunteer burnout"])

    def test_each_ruling_resolves_its_chunk(self):
        decided = {
            "chunk-7": {"codes": ["Food access", "Shared labour"], "note": "Both."},
            "chunk-9": {"codes": ["Municipal relations"]},
            "chunk-11": {"exclude": {"reason": " Not about the garden. "}},
            "chunk-12": {"none_apply": True},
        }
        records, amendments = apply.resolve(self.cards, decided)
        self.assertEqual(amendments, [])
        self.assertEqual(records, [
            {"chunk_id": "7", "card_id": "chunk-7", "text": self.cards[0]["text"], "source": "interview-02.txt",
             "Deductive_Codes": "Shared labour, Food access", "resolution": "ruled"},
            {"chunk_id": "9", "card_id": "chunk-9", "text": self.cards[1]["text"], "source": "interview-04.txt",
             "Deductive_Codes": "Municipal relations", "resolution": "ruled"},
            {"chunk_id": "11", "card_id": "chunk-11", "text": self.cards[2]["text"], "source": "interview-01.txt",
             "Deductive_Codes": "", "resolution": "excluded", "exclusion_reason": "Not about the garden."},
            {"chunk_id": "12", "card_id": "chunk-12", "text": self.cards[3]["text"], "source": "interview-02.txt",
             "Deductive_Codes": "", "resolution": "no_code"},
        ])

    def test_an_undecided_card_is_refused(self):
        with self.assertRaisesRegex(ValueError, "chunk-9, chunk-12"):
            apply.resolve(self.cards, {"chunk-7": {"codes": ["Shared labour"]}, "chunk-11": {"codes": ["Food access"]}})


class TestAmend(unittest.TestCase):
    def test_amended_codes_gain_their_rules(self):
        codebook = load("codebook")
        amendments = [
            {"source_card": "chunk-7", "rule_text": "Shared work outweighs giving.", "codes": ["Shared labour", "Charity framing"]},
            {"source_card": "chunk-12", "rule_text": "Deciding is not labour.", "codes": ["Shared labour"]},
        ]
        amended = apply.amend(codebook, amendments)
        self.assertEqual(by_label(amended)["Shared labour"]["rules"], ["Shared work outweighs giving.", "Deciding is not labour."])
        self.assertEqual(by_label(amended)["Charity framing"]["rules"], ["Shared work outweighs giving."])
        self.assertNotIn("rules", by_label(amended)["Land tenure"])
        self.assertNotIn("rules", codebook[0])  # the prior version is untouched

    def test_the_amended_codebook_shares_nothing_with_the_prior_version(self):
        codebook = [dict(load("codebook")[0], examples=["One.", "Two."])]
        amended = apply.amend(codebook, [])
        amended[0]["examples"].append("Three.")
        self.assertEqual(codebook[0]["examples"], ["One.", "Two."])

    def test_rules_already_in_force_are_kept(self):
        codebook = [dict(load("codebook")[0], rules=["An earlier rule."])]
        amended = apply.amend(codebook, [{"source_card": "chunk-1", "rule_text": "A new rule.", "codes": ["Shared labour"]}])
        self.assertEqual(amended[0]["rules"], ["An earlier rule.", "A new rule."])

    def test_an_amendment_naming_a_code_outside_the_codebook_is_refused(self):
        with self.assertRaisesRegex(ValueError, "chunk-7.*'Garden politics'"):
            apply.amend(load("codebook"), [{"source_card": "chunk-7", "rule_text": "x", "codes": ["Garden politics"]}])


class TestChecksumWithRules(unittest.TestCase):
    def test_r4_4_rules_change_checksum_only_when_present(self):
        codebook = load("codebook")
        # Every existing checksum stays the same: this value predates rules.
        self.assertEqual(crosslens.codebook_checksum(codebook), "21351422cb93dc5a")
        self.assertEqual(crosslens.codebook_checksum([dict(r, rules=[]) for r in codebook]), "21351422cb93dc5a")
        ruled = apply.amend(codebook, [{"source_card": "chunk-7", "rule_text": "Shared work outweighs giving.", "codes": ["Shared labour"]}])
        self.assertNotEqual(crosslens.codebook_checksum(ruled), crosslens.codebook_checksum(codebook))
        other = apply.amend(codebook, [{"source_card": "chunk-7", "rule_text": "Another rule.", "codes": ["Shared labour"]}])
        self.assertNotEqual(crosslens.codebook_checksum(ruled), crosslens.codebook_checksum(other))

    def test_rules_order_matters_and_record_order_does_not(self):
        codebook = load("codebook")
        two = apply.amend(codebook, [
            {"source_card": "a", "rule_text": "First.", "codes": ["Shared labour"]},
            {"source_card": "b", "rule_text": "Second.", "codes": ["Shared labour"]},
        ])
        swapped = [dict(r) for r in two]
        swapped[0]["rules"] = list(reversed(swapped[0]["rules"]))
        self.assertNotEqual(crosslens.codebook_checksum(two), crosslens.codebook_checksum(swapped))
        self.assertEqual(crosslens.codebook_checksum(two), crosslens.codebook_checksum(list(reversed(two))))


if __name__ == "__main__":
    unittest.main()
