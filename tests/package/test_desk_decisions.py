"""A decisions document: its shape, and every problem it has against the desk it names."""

import copy
import unittest

from ai_anthro_toolkit.desk import cards, decisions
from tests.package.desk_helpers import codebook_desk, rulings_desk

SCHEMA = "aat/desk-decisions@1"


def document(desk, chosen, **top):
    doc = {"schema": SCHEMA, "desk_id": desk["desk_id"], "card_checksum": cards.checksum(desk["cards"]), "decisions": chosen}
    doc.update(top)
    return doc


def codebook_document(**changes):
    """A complete codebook document for the fixture desk: every code adopted, codes exclusive."""
    desk = codebook_desk()
    chosen = {card["card_id"]: {"action": "adopt"} for card in desk["cards"]}
    chosen.update(changes)
    return desk, document(desk, chosen, exclusive=True)


def rulings_document(**changes):
    """A complete rulings document: each disagreement ruled as its proposal proposes."""
    desk = rulings_desk()
    chosen = {card["card_id"]: {"codes": list(card["proposal"]["codes"])} for card in desk["cards"]}
    chosen.update(changes)
    return desk, document(desk, chosen)


def problems(desk, doc, complete=True):
    return decisions.validate(desk, decisions.parse(doc), complete)


def said(found):
    return [f"{p.card_id}: {p.message}" for p in found]


class TestParse(unittest.TestCase):
    def test_a_document_parses(self):
        desk, doc = codebook_document()
        parsed = decisions.parse(doc)
        self.assertEqual(parsed.desk_id, desk["desk_id"])
        self.assertEqual(parsed.card_checksum, cards.checksum(desk["cards"]))
        self.assertIs(parsed.exclusive, True)
        self.assertEqual(parsed.decisions["code-01"], {"action": "adopt"})

    def test_parse_leaves_the_document_unchanged(self):
        _, doc = codebook_document(**{"code-01": {"action": "split", "parts": [{"label": "A", "definition": "a"}, {"label": "B", "definition": "b"}]}})
        kept = copy.deepcopy(doc)
        parsed = decisions.parse(doc)
        parsed.decisions["code-01"]["parts"][0]["label"] = "Changed"
        parsed.decisions["code-02"]["action"] = "delete"
        self.assertEqual(doc, kept)

    def test_exclusive_may_be_left_out(self):
        _, doc = rulings_document()
        self.assertIsNone(decisions.parse(doc).exclusive)

    def test_documents_of_another_shape_are_refused(self):
        _, good = codebook_document()
        cases = {
            "not an object": ([], "a JSON object"),
            "another schema": (dict(good, schema="aat/desk-decisions@2"), "aat/desk-decisions@1"),
            "no schema": ({k: v for k, v in good.items() if k != "schema"}, "aat/desk-decisions@1"),
            "no desk": (dict(good, desk_id=""), "desk_id"),
            "no checksum": ({k: v for k, v in good.items() if k != "card_checksum"}, "card_checksum"),
            "decisions not an object": (dict(good, decisions=[]), "decisions"),
            "a decision not an object": (dict(good, decisions={"code-01": "adopt"}), "code-01"),
            "exclusive not a boolean": (dict(good, exclusive="yes"), "exclusive"),
            "an unknown field": (dict(good, ratified=True), "ratified"),
        }
        for name, (doc, named) in cases.items():
            with self.subTest(name), self.assertRaisesRegex(ValueError, named):
                decisions.parse(doc)


class TestCodebookDecisions(unittest.TestCase):
    def test_a_complete_document_has_no_problem(self):
        desk, doc = codebook_document(**{
            "code-02": {"action": "reword", "definition": "Talk of giving to people in need.", "label": "Charity", "note": "Shorter."},
            "code-03": {"action": "merge", "target": "Municipal relations"},
            "code-04": {"action": "split", "parts": [{"label": "Prices", "definition": "What food costs."}, {"label": "Supply", "definition": "Whether food is there."}]},
            "code-05": {"action": "delete"},
        })
        self.assertEqual(problems(desk, doc), [])

    def test_r2_8_merge_into_unknown_code_refused(self):
        desk, doc = codebook_document(**{"code-03": {"action": "merge", "target": "Garden politics"}})
        self.assertEqual(said(problems(desk, doc)), ["code-03: Land tenure is merged into 'Garden politics', which is not a code in this codebook."])

    def test_r2_8_merge_into_itself_or_a_code_that_goes_refused(self):
        desk, doc = codebook_document(**{
            "code-01": {"action": "merge", "target": "Shared labour"},
            "code-03": {"action": "merge", "target": "Food access"},
            "code-04": {"action": "delete"},
            "code-05": {"action": "merge", "target": "Charity framing"},
            "code-02": {"action": "merge", "target": "Municipal relations"},
        })
        self.assertEqual(said(problems(desk, doc)), [
            "code-01: Shared labour cannot be merged into itself.",
            "code-03: Land tenure is merged into Food access, which is deleted.",
            "code-05: Volunteer burnout is merged into Charity framing, which is itself merged.",
        ])
        desk, doc = codebook_document(**{
            "code-01": {"action": "split", "parts": [{"label": "Rosters", "definition": "a"}, {"label": "Workdays", "definition": "b"}]},
            "code-06": {"action": "merge", "target": "Shared labour"},
        })
        self.assertEqual(said(problems(desk, doc)), ["code-06: Municipal relations is merged into Shared labour, which is itself split."])

    def test_r2_8_split_needs_two_parts(self):
        one = {"action": "split", "parts": [{"label": "Rosters", "definition": "Who works when."}]}
        desk, doc = codebook_document(**{"code-01": one})
        self.assertEqual(said(problems(desk, doc)), ["code-01: A split needs at least two parts; Shared labour has 1."])
        desk, doc = codebook_document(**{"code-01": {"action": "split"}})
        self.assertEqual(said(problems(desk, doc)), ["code-01: A split needs at least two parts; Shared labour has 0."])

    def test_r2_8_split_parts_need_a_label_and_a_definition_each(self):
        parts = [{"label": "Rosters", "definition": " "}, {"label": "", "definition": "Days together."}, {"label": "Rosters", "definition": "Again."}]
        desk, doc = codebook_document(**{"code-01": {"action": "split", "parts": parts}})
        self.assertEqual(said(problems(desk, doc)), [
            "code-01: Part 1 of the split of Shared labour has no definition.",
            "code-01: Part 2 of the split of Shared labour has no label.",
            "code-01: The split of Shared labour names 'Rosters' twice.",
        ])
        desk, doc = codebook_document(**{"code-01": {"action": "split", "parts": ["Rosters", "Workdays"]}})
        self.assertEqual(said(problems(desk, doc)), ["code-01: Each part of the split of Shared labour needs a label and a definition."])

    def test_r2_8_empty_reword_refused(self):
        for definition in ("", "   ", None):
            desk, doc = codebook_document(**{"code-02": {"action": "reword", "definition": definition}})
            self.assertEqual(said(problems(desk, doc)), ["code-02: The reword of Charity framing has an empty definition."], repr(definition))

    def test_an_unknown_action_is_refused(self):
        desk, doc = codebook_document(**{"code-02": {"action": "keep"}})
        self.assertEqual(said(problems(desk, doc)), ["code-02: 'keep' is not an action; choose adopt, reword, merge, split or delete."])

    def test_fields_an_action_does_not_take_are_refused(self):
        desk, doc = codebook_document(**{"code-02": {"action": "adopt", "definition": "Typo'd intent."}})
        self.assertEqual(said(problems(desk, doc)), ["code-02: adopt does not take definition."])

    def test_text_fields_must_be_text(self):
        desk, doc = codebook_document(**{"code-02": {"action": "reword", "definition": "Giving.", "label": 7, "note": ["x"]}})
        self.assertEqual(said(problems(desk, doc)), ["code-02: label must be text.", "code-02: note must be text."])
        desk, doc = codebook_document(**{"code-02": {"action": "reword", "definition": 5}, "code-03": {"action": "merge", "target": 5}})
        self.assertEqual(said(problems(desk, doc)), ["code-02: definition must be text.", "code-03: target must be text."])

    def test_a_merge_into_an_undecided_code_waits_for_its_decision(self):
        desk, doc = codebook_document(**{"code-03": {"action": "merge", "target": "Food access"}})
        del doc["decisions"]["code-04"]
        self.assertEqual(problems(desk, doc, complete=False), [])

    def test_r2_6_missing_actions_and_question_named_when_complete(self):
        desk, doc = codebook_document()
        del doc["decisions"]["code-02"], doc["decisions"]["code-05"], doc["exclusive"]
        self.assertEqual(said(problems(desk, doc)), [
            "code-02: Charity framing has no decision.",
            "code-05: Volunteer burnout has no decision.",
            "exclusivity: The question whether the codes are mutually exclusive is unanswered.",
        ])
        self.assertEqual(problems(desk, doc, complete=False), [])

    def test_r5_2_a_document_from_another_desk_version_is_refused(self):
        desk, doc = codebook_document()
        doc["card_checksum"] = "0" * 16
        self.assertEqual(said(problems(desk, doc)), ["desk: These decisions were made on a different desk version."])

    def test_a_document_for_another_desk_is_refused(self):
        desk, doc = codebook_document()
        doc["desk_id"] = "desk-ffffffff"
        self.assertEqual(said(problems(desk, doc)), ["desk: These decisions are for desk-ffffffff, not desk-0a1b2c3d."])

    def test_r5_3_decision_for_card_not_on_desk_refused(self):
        desk, doc = codebook_document(**{"code-99": {"action": "adopt"}, "exclusivity": {"exclusive": True}})
        self.assertEqual(said(problems(desk, doc)), [
            "code-99: code-99 is not a card on this desk.",
            "exclusivity: exclusivity is not a card on this desk.",
        ])

    def test_ruling_fields_are_refused_on_a_codebook_desk(self):
        desk, doc = codebook_document(**{"code-02": {"codes": ["Charity framing"]}})
        self.assertEqual(said(problems(desk, doc)), ["code-02: The decision on Charity framing gives no action; choose adopt, reword, merge, split or delete."])


class TestDiffers(unittest.TestCase):
    """R3.6: which rulings depart from their proposal, so the rule question is asked."""

    def test_differs(self):
        card = {"proposal": {"codes": ["Land tenure", "Municipal relations"], "rationale": ""}}
        self.assertFalse(decisions.differs(card, {"codes": ["Municipal relations", "Land tenure"]}))
        self.assertTrue(decisions.differs(card, {"codes": ["Land tenure"]}))
        self.assertTrue(decisions.differs(card, {"none_apply": True}))
        self.assertFalse(decisions.differs(card, {"exclude": {"reason": "Off topic."}}))
        self.assertFalse(decisions.differs({"proposal": None}, {"codes": ["Land tenure"]}))
        self.assertFalse(decisions.differs({"proposal": {"codes": [], "rationale": ""}}, {"none_apply": True}))
        self.assertTrue(decisions.differs({"proposal": {"codes": [], "rationale": ""}}, {"codes": ["Land tenure"]}))


class TestRulingDecisions(unittest.TestCase):
    def test_a_complete_document_has_no_problem(self):
        desk, doc = rulings_document(**{
            "chunk-7": {"codes": ["Shared labour"], "is_rule": True, "rule_text": "Shared work outweighs giving.", "note": "Clear."},
            "chunk-9": {"codes": ["Municipal relations"], "is_rule": False},
            "chunk-11": {"exclude": {"reason": "Not about the garden."}},
            "chunk-12": {"none_apply": True, "is_rule": False, "rule_text": "Typed, then answered no."},
        })
        self.assertEqual(problems(desk, doc), [])

    def test_r3_7_ruling_with_unknown_code_refused(self):
        desk, doc = rulings_document(**{"chunk-9": {"codes": ["Land tenure", "Garden politics"]}})
        self.assertEqual(said(problems(desk, doc)), ["chunk-9: The ruling names 'Garden politics', which is not in the codebook in force."])

    def test_r3_3_an_exclusive_desk_takes_exactly_one_code(self):
        desk = rulings_desk(exclusive=True)
        doc = document(desk, {
            "chunk-7": {"codes": ["Charity framing"]},
            "chunk-9": {"codes": ["Land tenure", "Municipal relations"], "is_rule": False},
            "chunk-11": {"codes": ["Food access"]},
            "chunk-12": {"none_apply": True, "is_rule": False},
        })
        self.assertEqual(said(problems(desk, doc)), [
            "chunk-9: The codes are mutually exclusive, so a ruling takes exactly one code; this one takes 2.",
            "chunk-12: The codes are mutually exclusive, so a ruling takes exactly one code, not No code applies.",
        ])

    def test_r3_3_a_ruling_is_codes_or_none_or_an_exclusion(self):
        cases = {
            "nothing": ({}, "chunk-7: A ruling gives codes, no code applies, or an exclusion; this one gives none."),
            "two kinds": ({"codes": ["Food access"], "none_apply": True}, "chunk-7: A ruling gives codes, no code applies, or an exclusion; this one gives codes and none_apply."),
            "empty codes": ({"codes": []}, "chunk-7: A ruling with codes names at least one; for none, give none_apply."),
            "codes not a list": ({"codes": "Food access"}, "chunk-7: codes must be a list of code labels."),
            "a code twice": ({"codes": ["Food access", "Food access"]}, "chunk-7: The ruling names 'Food access' twice."),
            "none_apply false": ({"none_apply": False}, "chunk-7: none_apply is true when given."),
        }
        for name, (decision, message) in cases.items():
            desk, doc = rulings_document(**{"chunk-7": decision})
            with self.subTest(name):
                self.assertEqual(said(problems(desk, doc)), [message])

    def test_r3_4_an_exclusion_needs_a_reason(self):
        for exclude in ({"reason": ""}, {"reason": "  "}, {}, "Off topic."):
            desk, doc = rulings_document(**{"chunk-11": {"exclude": exclude}})
            self.assertEqual(said(problems(desk, doc)), ["chunk-11: An exclusion needs a reason."], repr(exclude))

    def test_an_exclusion_states_no_rule(self):
        for extra in ({"is_rule": True, "rule_text": "x"}, {"is_rule": False}, {"rule_text": "x"}):
            desk, doc = rulings_document(**{"chunk-11": {"exclude": {"reason": "Off topic."}, **extra}})
            self.assertEqual(said(problems(desk, doc)), ["chunk-11: An exclusion does not state a rule; take out is_rule and rule_text."], extra)

    def test_r4_2_rule_without_text_refused(self):
        for text in (None, "", "   "):
            ruling = {"codes": ["Shared labour"], "is_rule": True}
            if text is not None:
                ruling["rule_text"] = text
            desk, doc = rulings_document(**{"chunk-7": ruling})
            self.assertEqual(said(problems(desk, doc)), ["chunk-7: The ruling is marked as a rule but gives no rule text."], repr(text))

    def test_is_rule_is_a_boolean(self):
        desk, doc = rulings_document(**{"chunk-7": {"codes": ["Shared labour"], "is_rule": "yes", "rule_text": "x"}})
        self.assertEqual(said(problems(desk, doc)), ["chunk-7: is_rule must be true or false."])

    def test_r3_6_a_differing_ruling_needs_the_rule_answer_when_complete(self):
        desk, doc = rulings_document(**{"chunk-7": {"codes": ["Shared labour"]}, "chunk-12": {"none_apply": True}})
        self.assertEqual(said(problems(desk, doc)), [
            "chunk-7: The ruling differs from the proposal; say whether it states a rule.",
            "chunk-12: The ruling differs from the proposal; say whether it states a rule.",
        ])
        # Saved one at a time, the answer may follow.
        self.assertEqual(problems(desk, doc, complete=False), [])

    def test_a_ruling_matching_the_proposal_in_another_order_needs_no_rule_answer(self):
        desk, doc = rulings_document(**{"chunk-9": {"codes": ["Municipal relations", "Land tenure"]}})
        self.assertEqual(problems(desk, doc), [])

    def test_a_card_without_a_proposal_needs_no_rule_answer(self):
        desk = rulings_desk(cards=[{**card, "proposal": None} for card in rulings_desk()["cards"]])
        doc = document(desk, {card["card_id"]: {"codes": ["Volunteer burnout"]} for card in desk["cards"]})
        self.assertEqual(problems(desk, doc), [])

    def test_rule_text_and_notes_must_be_text(self):
        desk, doc = rulings_document(**{"chunk-7": {"codes": ["Shared labour"], "is_rule": True, "rule_text": 5, "note": 1}})
        self.assertEqual(said(problems(desk, doc)), ["chunk-7: rule_text must be text.", "chunk-7: note must be text."])

    def test_r5_4_open_cards_are_counted_when_complete(self):
        desk, doc = rulings_document()
        del doc["decisions"]["chunk-9"], doc["decisions"]["chunk-12"]
        self.assertEqual(said(problems(desk, doc)), ["desk: 2 of 4 cards are still open."])
        self.assertEqual(problems(desk, doc, complete=False), [])

    def test_an_exclusive_answer_that_disagrees_with_the_desk_is_refused(self):
        desk, doc = rulings_document()
        doc["exclusive"] = True
        self.assertEqual(said(problems(desk, doc)), ["desk: These rulings say the codes are mutually exclusive; the codebook in force says they are not."])
        doc["exclusive"] = False
        self.assertEqual(problems(desk, doc), [])
        desk = rulings_desk(exclusive=True)
        doc = document(desk, {card["card_id"]: {"exclude": {"reason": "Set aside."}} for card in desk["cards"]}, exclusive=False)
        self.assertEqual(said(problems(desk, doc)), ["desk: These rulings say the codes are not mutually exclusive; the codebook in force says they are."])
        doc["exclusive"] = True
        self.assertEqual(problems(desk, doc), [])

    def test_fields_a_ruling_does_not_take_are_refused(self):
        desk, doc = rulings_document(**{"chunk-7": {"codes": ["Charity framing"], "action": "adopt"}})
        self.assertEqual(said(problems(desk, doc)), ["chunk-7: A ruling does not take action."])

    def test_every_problem_is_reported_in_card_order(self):
        desk, doc = rulings_document(**{
            "chunk-12": {"exclude": {"reason": ""}},
            "chunk-7": {"codes": ["Garden politics"]},
        })
        doc["card_checksum"] = "0" * 16
        self.assertEqual([p.card_id for p in problems(desk, doc)], ["desk", "chunk-7", "chunk-12"])


if __name__ == "__main__":
    unittest.main()
