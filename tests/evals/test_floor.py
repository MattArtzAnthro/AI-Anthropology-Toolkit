"""Reading a scenario against the null floor, tested without a model call.

A scenario is supposed to measure whether a skill holds a gate. It can only
do that if the gate would *not* hold without the skill. The null floor runs
the same user message with no skill body at all: if the reply holds anyway,
the scenario is measuring the model's own defaults, and its green result says
nothing about the skill.

The floor is cheaper and stronger than ablating gate sentences. It costs one
run, needs no hand-authored removal, and cannot silently fail to remove
something — which is the failure mode an ablation has by construction.

A scenario that does not discriminate is a finding about the scenario, not a
reason to delete it: deleting it would destroy the finding.
"""

import unittest

from tests.evals import judge
from tests.evals.floor import (DEFAULTS, GATE_BROKEN, MEASURES_SKILL,
                               UNREADABLE, read_floor)


class ReadingTheArms(unittest.TestCase):
    def test_holds_with_the_skill_and_not_without_it_measures_the_skill(self):
        self.assertEqual(
            read_floor(intact=judge.CONFIRMED, floor=judge.REFUTED),
            MEASURES_SKILL)

    def test_holds_either_way_measures_the_models_defaults(self):
        self.assertEqual(
            read_floor(intact=judge.CONFIRMED, floor=judge.CONFIRMED),
            DEFAULTS)

    def test_a_gate_that_did_not_hold_is_reported_as_such(self):
        # The floor is irrelevant here: the skill failed its own scenario.
        self.assertEqual(
            read_floor(intact=judge.REFUTED, floor=judge.REFUTED),
            GATE_BROKEN)
        self.assertEqual(
            read_floor(intact=judge.REFUTED, floor=judge.CONFIRMED),
            GATE_BROKEN)

    def test_an_undetermined_arm_makes_the_pair_unreadable(self):
        for intact, fl in ((judge.CANNOT_TELL, judge.REFUTED),
                           (judge.CONFIRMED, judge.CANNOT_TELL),
                           (judge.INSUFFICIENT_CONTEXT, judge.CONFIRMED)):
            with self.subTest(intact=intact, floor=fl):
                self.assertEqual(read_floor(intact=intact, floor=fl),
                                 UNREADABLE)

    def test_unreadable_is_not_silently_folded_into_a_pass(self):
        self.assertNotIn(UNREADABLE, (MEASURES_SKILL, DEFAULTS))


class ReadingsAreDistinct(unittest.TestCase):
    def test_the_four_readings_are_distinct(self):
        self.assertEqual(
            len({MEASURES_SKILL, DEFAULTS, GATE_BROKEN, UNREADABLE}), 4)

    def test_every_reading_carries_an_explanation(self):
        from tests.evals.floor import EXPLANATIONS
        for reading in (MEASURES_SKILL, DEFAULTS, GATE_BROKEN, UNREADABLE):
            with self.subTest(reading=reading):
                self.assertTrue(EXPLANATIONS[reading].strip())

    def test_the_defaults_explanation_does_not_call_it_a_failure(self):
        # A gate the base model holds anyway is not a broken gate, and
        # reporting it as one would push toward deleting working scenarios.
        from tests.evals.floor import EXPLANATIONS
        text = EXPLANATIONS[DEFAULTS].lower()
        for word in ("broken", "failed", "failure"):
            self.assertNotIn(word, text)


class TheFloorIsNotAControlForTheCompliantDirection(unittest.TestCase):
    """Measured 2026-08-06: all four compliant scenarios read as
    measures-model-defaults. That is structural, not a finding about them.

    A compliant scenario asks whether the skill re-interrogates a judgment
    the researcher already supplied. Ceremony is something a skill adds, so a
    run with no skill has nothing to add it — the floor arm confirms by
    construction, and the comparison carries no information. Reporting those
    as "measures the model's defaults" would push toward deleting the only
    scenarios that guard the gate-becomes-a-form failure.
    """

    def test_a_compliant_scenario_is_marked_inapplicable_not_defaults(self):
        from tests.evals.floor import FLOOR_INAPPLICABLE
        self.assertEqual(
            read_floor(intact=judge.CONFIRMED, floor=judge.CONFIRMED,
                       direction="compliant"),
            FLOOR_INAPPLICABLE)

    def test_a_pressure_scenario_still_reads_as_defaults(self):
        self.assertEqual(
            read_floor(intact=judge.CONFIRMED, floor=judge.CONFIRMED,
                       direction="pressure"),
            DEFAULTS)

    def test_a_broken_compliant_gate_is_still_reported(self):
        # Inapplicability of the control does not excuse a failing scenario.
        self.assertEqual(
            read_floor(intact=judge.REFUTED, floor=judge.CONFIRMED,
                       direction="compliant"),
            GATE_BROKEN)

    def test_the_default_direction_is_pressure(self):
        self.assertEqual(
            read_floor(intact=judge.CONFIRMED, floor=judge.CONFIRMED),
            DEFAULTS)

    def test_inapplicable_explains_why_the_control_cannot_speak(self):
        from tests.evals.floor import EXPLANATIONS, FLOOR_INAPPLICABLE
        text = EXPLANATIONS[FLOOR_INAPPLICABLE].lower()
        self.assertIn("ceremony", text)
        for word in ("broken", "failed"):
            self.assertNotIn(word, text)


class TheFloorRunsWithoutASkill(unittest.TestCase):
    def test_the_floor_argv_carries_no_system_prompt(self):
        argv = judge.subject_argv("a user message", "", model="test-model")
        self.assertNotIn("--system-prompt", argv)

    def test_the_floor_argv_keeps_every_isolation_measure(self):
        argv = judge.subject_argv("a user message", "", model="test-model")
        self.assertIn("--strict-mcp-config", argv)
        self.assertIn("--disallowedTools", argv)


if __name__ == "__main__":
    unittest.main()
