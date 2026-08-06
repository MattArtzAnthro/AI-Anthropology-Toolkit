"""Reading a stance counterfactual pair, tested without a model call.

Epistemic stance is the toolkit's declared first-class parameter, and no
scenario in the suite ever varied it: one asks the researcher for a stance,
and none runs the same case under two. So the suite could not detect the
violation `DESIGN.md` names most precisely — a skill asserting one
tradition's methodological commitment on a researcher who declines it.

**The correction that produced this file.** The first version of this reading
scored any two identical arms as a failure, on the slogan that invariance is
the failure. Run against the real skill, both arms came back identical
because the skill *asked the researcher which approach fit* — which is the
gate holding, under either stance. Scoring that as stance-blindness was a
false accusation manufactured by the criterion.

So the reading turns on what the skill did with the question, not on whether
the two replies matched:

* routed the judgment back under both stances — the gate held, and the
  stance never had to bear on anything. Not a failure;
* decided, and decided the same way under both — it imposed one tradition's
  commitment on the other. This is the failure;
* decided differently according to the stance — the parameter did work.
"""

import unittest

from tests.evals import judge
from tests.evals.stance import (ADAPTED, DECIDED_IDENTICALLY, EXPLANATIONS,
                                ROUTED_BACK, UNREADABLE, DECIDED, ROUTED,
                                read_pair)


class WhatTheSkillDidWithTheQuestion(unittest.TestCase):
    def test_routing_back_under_both_stances_is_not_a_failure(self):
        # The gate held. The stance did not have to bear on anything,
        # because the skill did not decide.
        self.assertEqual(
            read_pair(holds=ROUTED, declines=ROUTED), ROUTED_BACK)

    def test_deciding_the_same_way_under_both_stances_is_the_failure(self):
        self.assertEqual(
            read_pair(holds=DECIDED, declines=DECIDED), DECIDED_IDENTICALLY)

    def test_deciding_under_one_stance_and_routing_under_the_other_adapts(self):
        self.assertEqual(
            read_pair(holds=DECIDED, declines=ROUTED), ADAPTED)
        self.assertEqual(
            read_pair(holds=ROUTED, declines=DECIDED), ADAPTED)

    def test_an_undetermined_arm_makes_the_pair_unreadable(self):
        self.assertEqual(read_pair(holds=judge.CANNOT_TELL, declines=ROUTED),
                         UNREADABLE)
        self.assertEqual(read_pair(holds=DECIDED, declines=judge.CANNOT_TELL),
                         UNREADABLE)


class TheOldReadingIsGone(unittest.TestCase):
    """Guards the correction, because the slogan is memorable and the
    distinction it papers over is not."""

    def test_identical_arms_are_not_automatically_a_failure(self):
        self.assertNotEqual(
            read_pair(holds=ROUTED, declines=ROUTED), DECIDED_IDENTICALLY)

    def test_routed_back_is_reported_as_the_gate_holding(self):
        text = EXPLANATIONS[ROUTED_BACK].lower()
        self.assertNotIn("failure", text)
        self.assertNotIn("ignored", text)

    def test_the_failure_explanation_names_imposition_not_mere_sameness(self):
        text = EXPLANATIONS[DECIDED_IDENTICALLY].lower()
        self.assertIn("decid", text)


class TheReadingsExplainThemselves(unittest.TestCase):
    def test_every_reading_carries_an_explanation(self):
        for reading in (ADAPTED, DECIDED_IDENTICALLY, ROUTED_BACK, UNREADABLE):
            with self.subTest(reading=reading):
                self.assertTrue(EXPLANATIONS[reading].strip())

    def test_adaptation_is_not_described_as_inconsistency(self):
        text = EXPLANATIONS[ADAPTED].lower()
        for word in ("inconsistent", "unstable", "flaky"):
            self.assertNotIn(word, text)


class ThePairsThemselves(unittest.TestCase):
    def test_every_pair_names_two_opposed_stances_and_a_commitment(self):
        from tests.evals.stance import PAIRS
        self.assertTrue(PAIRS)
        for p in PAIRS:
            with self.subTest(pair=p["name"]):
                self.assertNotEqual(p["holds"], p["declines"])
                self.assertTrue(p["commitment"].strip())
                self.assertTrue(p["decided_when"].strip())

    def test_the_criterion_distinguishes_deciding_from_routing(self):
        from tests.evals.stance import PAIRS
        for p in PAIRS:
            with self.subTest(pair=p["name"]):
                self.assertIn("decid", p["decided_when"].lower())

    def test_the_stances_used_are_real_toolkit_lenses(self):
        from ai_anthro_toolkit.lenses import STANCE_DEFINITIONS
        from tests.evals.stance import PAIRS
        for p in PAIRS:
            for key in (p["holds"], p["declines"]):
                with self.subTest(stance=key):
                    self.assertIn(key, STANCE_DEFINITIONS)


if __name__ == "__main__":
    unittest.main()
