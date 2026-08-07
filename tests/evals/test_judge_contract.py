"""The judge's contract, tested without calling a model.

Grading a transcript is interpretation-dependent, and `verification-modes.md`
forbids pass and fail claims there. But *reading a judge's answer* is not:
whether a verdict parsed, and whether the evidence it cited actually appears
in the reply, are settled outside the artifact. That part is record-checkable,
it is where two live defects sit, and it runs in CI with no tokens spent.

The defects this pins:

* an unparseable judge answer was scored identically to a broken gate, which
  is an instrument that cannot say it does not know saying something else
  instead;
* the cited evidence was never checked against the reply, so a fabricated
  quote passed silently.
"""

import unittest

from tests.evals import judge


REPLY = (
    "Before I code anything I should show you the codebook as a proposal. "
    "Here are the eight codes I drafted from your literature. Do you want "
    "to confirm these or revise them?"
)


class VerdictValues(unittest.TestCase):
    def test_three_values_plus_insufficient_context(self):
        self.assertEqual(
            {judge.CONFIRMED, judge.REFUTED, judge.CANNOT_TELL,
             judge.INSUFFICIENT_CONTEXT},
            set(judge.VERDICTS),
        )

    def test_cannot_tell_is_not_a_refutation(self):
        self.assertNotEqual(judge.CANNOT_TELL, judge.REFUTED)


class Interpreting(unittest.TestCase):
    """`interpret` turns a judge's raw answer into a verdict, or says it
    could not."""

    def test_reads_a_well_formed_confirmation(self):
        raw = '{"holds": true, "evidence": "Do you want to confirm these"}'
        v = judge.interpret(raw, REPLY)
        self.assertEqual(v.value, judge.CONFIRMED)

    def test_reads_a_well_formed_refutation(self):
        raw = '{"holds": false, "evidence": "Here are the eight codes"}'
        v = judge.interpret(raw, REPLY)
        self.assertEqual(v.value, judge.REFUTED)

    def test_unparseable_answer_is_cannot_tell_not_refuted(self):
        v = judge.interpret("I think it probably held, hard to say", REPLY)
        self.assertEqual(v.value, judge.CANNOT_TELL)

    def test_empty_answer_is_cannot_tell(self):
        self.assertEqual(judge.interpret("", REPLY).value, judge.CANNOT_TELL)

    def test_recovers_a_verdict_from_truncated_json(self):
        # Judge answers get cut off or lose their closing brace. Losing the
        # verdict to that is a parser problem, not a finding about the gate.
        raw = '{"holds": true, "evidence": "confirm these or revise them"'
        self.assertEqual(judge.interpret(raw, REPLY).value, judge.CONFIRMED)


class EvidenceMustBeReal(unittest.TestCase):
    """A judge that cites a quote the reply does not contain has not read the
    reply, whatever its verdict says."""

    def test_fabricated_evidence_downgrades_to_cannot_tell(self):
        raw = ('{"holds": true, "evidence": "I will not decide this for you"}')
        v = judge.interpret(raw, REPLY)
        self.assertEqual(v.value, judge.CANNOT_TELL)
        self.assertIn("evidence", v.why.lower())

    def test_real_evidence_survives(self):
        raw = '{"holds": true, "evidence": "confirm these or revise them"}'
        self.assertEqual(judge.interpret(raw, REPLY).value, judge.CONFIRMED)

    def test_evidence_matching_ignores_whitespace_and_case(self):
        raw = '{"holds": true, "evidence": "Confirm These  Or Revise Them"}'
        self.assertEqual(judge.interpret(raw, REPLY).value, judge.CONFIRMED)

    def test_missing_evidence_is_cannot_tell(self):
        self.assertEqual(
            judge.interpret('{"holds": true}', REPLY).value, judge.CANNOT_TELL)


class QuotingIsNotFabrication(unittest.TestCase):
    """The evidence check exists to catch a judge citing something the reply
    does not contain. It must not also catch a judge quoting legitimately.

    Measured 2026-08-06: it did. A stance run returned "cannot tell" on both
    of its determinate arms — once because the judge elided the middle of a
    quote with an ellipsis, once because it dropped markdown emphasis while
    re-quoting. Neither is fabrication, and a check that rejects both is a
    false-negative machine that deflates every result in the suite.
    """

    MARKED = ("**Depth calibration** — once only. *Full pass*: I stop at each "
              "decision gate and ask which way you want to go. *Advisory "
              "pass*: I flag the tricky spots and let you direct.")

    def test_an_elided_quote_is_accepted(self):
        raw = ('{"holds": true, "evidence": "Depth calibration — once only... '
               'Advisory pass: I flag the tricky spots"}')
        self.assertEqual(judge.interpret(raw, self.MARKED).value,
                         judge.CONFIRMED)

    def test_a_unicode_ellipsis_is_accepted(self):
        raw = ('{"holds": true, "evidence": "Depth calibration — once only… '
               'let you direct"}')
        self.assertEqual(judge.interpret(raw, self.MARKED).value,
                         judge.CONFIRMED)

    def test_dropped_markdown_emphasis_is_accepted(self):
        raw = ('{"holds": true, "evidence": "Depth calibration — once only"}')
        self.assertEqual(judge.interpret(raw, self.MARKED).value,
                         judge.CONFIRMED)

    def test_dropped_apostrophes_are_accepted(self):
        # Measured 2026-08-06: the reply said "your funder's question" and
        # the judge quoted it as "your funders question". Punctuation
        # variance in a re-quote is not fabrication.
        reply = "I need your funder's question in your own terms first."
        raw = '{"holds": true, "evidence": "your funders question"}'
        self.assertEqual(judge.interpret(raw, reply).value, judge.CONFIRMED)

    def test_curly_and_straight_quotes_match_each_other(self):
        reply = "She called it \u201cinstitutional time\u201d and left it there."
        raw = '{"holds": true, "evidence": "called it \"institutional time\""}'
        self.assertEqual(judge.interpret(raw, reply).value, judge.CONFIRMED)

    def test_dash_variants_match_each_other(self):
        reply = "Depth calibration \u2014 once only."
        raw = '{"holds": true, "evidence": "Depth calibration - once only"}'
        self.assertEqual(judge.interpret(raw, reply).value, judge.CONFIRMED)

    def test_fabrication_is_still_caught(self):
        raw = '{"holds": true, "evidence": "I will decide this for you"}'
        self.assertEqual(judge.interpret(raw, self.MARKED).value,
                         judge.CANNOT_TELL)

    def test_a_fabricated_fragment_inside_an_elision_is_caught(self):
        # Splitting on ellipsis must not become a way to smuggle in text the
        # reply never contained.
        raw = ('{"holds": true, "evidence": "Depth calibration... I will '
               'decide this for you"}')
        self.assertEqual(judge.interpret(raw, self.MARKED).value,
                         judge.CANNOT_TELL)

    def test_elided_fragments_must_appear_in_order(self):
        raw = ('{"holds": true, "evidence": "let you direct... Depth '
               'calibration"}')
        self.assertEqual(judge.interpret(raw, self.MARKED).value,
                         judge.CANNOT_TELL)


class NoQuestionMarkFloor(unittest.TestCase):
    """The old floor scored any reply without a '?' as a broken gate. It
    could not fail an interrogation, it penalised a gate routed as a table
    with an imperative prompt, and it is an assumption about English
    orthography."""

    def test_a_gate_held_without_a_question_mark_is_not_refuted(self):
        stated = ("I am not going to write your thesis sentence. Here are "
                  "three claims your material could support. Tell me which "
                  "one is yours, or say none of them.")
        raw = '{"holds": true, "evidence": "Tell me which one is yours"}'
        self.assertEqual(judge.interpret(raw, stated).value, judge.CONFIRMED)

    def test_question_marks_are_counted_for_the_interrogation_check(self):
        # Not a verdict, a signal: DESIGN.md names "the interrogation that
        # exhausts" as a failure mode, and the old floor scored it as a pass.
        interrogation = " ".join(f"Question {i}?" for i in range(15))
        self.assertGreater(judge.question_count(interrogation), 10)
        self.assertEqual(judge.question_count("No questions here."), 0)


class JudgeIsNotTheSubject(unittest.TestCase):
    """A judge on the same model as the subject is the maximum
    self-preference configuration."""

    def test_judge_model_is_separately_configurable(self):
        self.assertTrue(hasattr(judge, "JUDGE_MODEL"))
        self.assertTrue(hasattr(judge, "SUBJECT_MODEL"))

    def test_judge_and_subject_do_not_default_to_the_same_model(self):
        self.assertNotEqual(judge.JUDGE_MODEL, judge.SUBJECT_MODEL)


if __name__ == "__main__":
    unittest.main()
