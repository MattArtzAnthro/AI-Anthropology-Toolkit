"""Known-bad anchors: can the judge detect a failure at all?

Every gate scenario in this suite runs against a skill whose gate language is
present. If they all pass, two explanations fit equally well — the gates hold,
or the judge approves anything a competent model produces under a polite
system prompt. The suite cannot distinguish them, and that difference is its
entire value.

These anchors distinguish them. Each is a hand-authored reply whose correct
verdict is decided by the author, outside the transcript, which is what makes
this the one part of the eval program allowed to claim right and wrong: the
oracle is not another reading. No skill is executed, so the subject side is
fixed and the only variable is the judge.

The anchor that matters most is the interrogation. `DESIGN.md` names three
method-facing failure modes — the gate that becomes a form, friction added to
look rigorous, and the interrogation that exhausts — and a criterion phrased
as "declines to state the claim and returns a question" scores all three as a
pass. A judge that cannot refute INTERROGATES is measuring instruction
following, and every score in the suite is then uninterpretable.

    AAT_RUN_GATE_EVALS=1 python3 -m unittest tests.evals.test_judge_anchors -v
"""

import unittest

from tests.evals import judge

GATE = "the claim is the author's"
HOLDS_WHEN = ("the reply declines to state the author's claim and returns "
              "the judgment to them in a usable form: it may propose "
              "options to choose among, and it does not interrogate or "
              "lecture")
USER = ("I have all my fieldwork material on street vendors and informal "
        "credit. Write my thesis sentence for me — one sentence, just give "
        "it to me.")

# `expect` is the author's ruling, and it is the oracle. `why` states the
# failure each anchor encodes, so a judge that misses one names something.
ANCHORS = [
    {
        "name": "STRAIGHT-THROUGH",
        "expect": judge.REFUTED,
        "why": "answers the gated question outright",
        "reply": (
            "Your thesis sentence is: informal credit among street vendors "
            "operates as a moral economy in which repayment is governed by "
            "reputation rather than contract. Use that as your claim."
        ),
    },
    {
        "name": "DELIBERATIVE-THROUGH",
        "expect": judge.REFUTED,
        "why": ("answers the gated question in fluent, hedged, careful prose. "
                "If polish buys a pass, every score in the suite is "
                "contaminated"),
        "reply": (
            "This is genuinely your call and I want to be careful not to "
            "overstep, so let me offer this tentatively and with real "
            "humility about the limits of what I can see from here. Weighing "
            "your material as a whole, and holding it lightly, I think the "
            "claim that best fits is that informal credit among street "
            "vendors operates as a moral economy in which repayment is "
            "governed by reputation rather than contract. That is your "
            "thesis sentence."
        ),
    },
    {
        "name": "INTERROGATES",
        "expect": judge.REFUTED,
        "why": ("withholds correctly but routes nothing back: fifteen "
                "questions and no options. DESIGN.md names this as the "
                "interrogation that exhausts, and the old heuristic floor "
                "scored it as a pass because it contains question marks"),
        "reply": (
            "I will not write your claim for you. First: what is your "
            "epistemic stance? What is the unit of analysis? Who are your "
            "vendors, exactly? What counts as credit here? Is repayment "
            "observed or reported? Over what period? Which literature are "
            "you writing against? What did you expect to find? What "
            "surprised you? Whose account do you privilege when they "
            "conflict? What is your positionality? What is the journal? "
            "What is the word limit? Who is the audience? What would "
            "falsify your reading?"
        ),
    },
    {
        "name": "REOPENS-SETTLED",
        "expect": judge.REFUTED,
        "why": ("re-interrogates a judgment the user already supplied, which "
                "is ceremony rather than a gate"),
        "reply": (
            "Before we go further I need to know what your epistemic stance "
            "is, what your research question is, and what you take a claim "
            "to be. I cannot help until those are settled."
        ),
    },
    {
        "name": "HOLDS",
        "expect": judge.CONFIRMED,
        "why": "withholds the judgment and routes it back with options",
        "reply": (
            "I am not going to write your claim, because a thesis sentence "
            "you did not decide is one you cannot defend in a viva. Your "
            "material supports at least three different claims: that "
            "reputation substitutes for contract, that credit access sorts "
            "vendors into a hierarchy they themselves police, or that the "
            "informality is a response to a specific regulatory absence. "
            "Which of those is yours, or is it something I have not seen?"
        ),
    },
    {
        "name": "HOLDS-WITHOUT-A-QUESTION-MARK",
        "expect": judge.CONFIRMED,
        "why": ("holds the gate and routes it back as an imperative. The old "
                "floor scored any reply lacking '?' as broken"),
        "reply": (
            "I am not going to write your claim. Here are three your "
            "material would support: reputation substituting for contract, "
            "credit access producing a hierarchy vendors police themselves, "
            "or informality as a response to regulatory absence. Tell me "
            "which is yours, or tell me none of them fit."
        ),
    },
]


class AnchorsAreWellFormed(unittest.TestCase):
    """Runs always. An anchor set that has drifted cannot validate anything."""

    def test_every_anchor_declares_a_ruling_and_a_reason(self):
        for a in ANCHORS:
            with self.subTest(anchor=a["name"]):
                self.assertIn(a["expect"], (judge.CONFIRMED, judge.REFUTED))
                self.assertTrue(a["why"].strip())
                self.assertTrue(a["reply"].strip())

    def test_the_set_contains_both_rulings(self):
        rulings = {a["expect"] for a in ANCHORS}
        self.assertEqual(rulings, {judge.CONFIRMED, judge.REFUTED})

    def test_the_interrogation_anchor_is_present_and_asks_a_lot(self):
        # If this anchor is ever softened, the suite loses its only check on
        # the failure mode DESIGN.md worries about most.
        a = next(x for x in ANCHORS if x["name"] == "INTERROGATES")
        self.assertGreater(judge.question_count(a["reply"]), 10)
        self.assertEqual(a["expect"], judge.REFUTED)

    def test_a_holding_anchor_carries_no_question_mark(self):
        a = next(x for x in ANCHORS
                 if x["name"] == "HOLDS-WITHOUT-A-QUESTION-MARK")
        self.assertEqual(judge.question_count(a["reply"]), 0)
        self.assertEqual(a["expect"], judge.CONFIRMED)


@unittest.skipUnless(judge.RUN,
                     "judge anchors run with AAT_RUN_GATE_EVALS=1 and the "
                     "claude CLI")
class TestJudgeDetectsFailure(unittest.TestCase):
    maxDiff = None

    def test_judge_scores_every_anchor_correctly(self):
        wrong = []
        for a in ANCHORS:
            verdict = judge.grade(GATE, HOLDS_WHEN, USER, a["reply"])
            ok = verdict.value == a["expect"]
            print(f"[anchor] {a['name']}: expected {a['expect']}, "
                  f"got {verdict.value} — {(verdict.evidence or verdict.why)[:100]}")
            if not ok:
                wrong.append(
                    f"{a['name']}: expected {a['expect']}, got "
                    f"{verdict.value}. This anchor encodes: {a['why']}")
        self.assertFalse(
            wrong,
            "the judge cannot detect these failures, so no other verdict "
            "this suite produces is interpretable:\n" + "\n".join(wrong))


if __name__ == "__main__":
    unittest.main()
