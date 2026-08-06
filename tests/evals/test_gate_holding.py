"""Behavioral evals: do the Friction by Design gates hold under pressure?

The structural tests in tests/test_repo.py verify that gate language is
present. These evals verify something the structural tests cannot: whether a
model executing a skill actually stops at a gate when the user pushes it to
answer through, and — the other direction — proceeds without ceremony when
the researcher has already supplied the judgment.

Each scenario runs the skill body as a system prompt through the `claude`
CLI, then a second model call grades the transcript against a rubric, with
a dumb heuristic as a floor. Results are evidence about sampled scenarios,
not proof of behavior in general.

Deliberately NOT run in CI (model behavior is nondeterministic and the run
costs real tokens). Run locally:

    AAT_RUN_GATE_EVALS=1 python3 -m unittest tests.evals.test_gate_holding -v
"""

import os
import shutil
import unittest
from pathlib import Path

from tests.evals import judge as _judge_mod

REPO = Path(__file__).resolve().parent.parent.parent
SKILLS = REPO / "skills"

RUN = os.environ.get("AAT_RUN_GATE_EVALS") == "1" and shutil.which("claude")
MODEL = _judge_mod.SUBJECT_MODEL  # judge model is separate; see judge.py

# Pressure scenarios: the user pushes the skill to answer through its gate.
# `holds_when` states what a gate-holding reply does, for the judge.
PRESSURE = [
    {
        "skill": "qualitative-analysis",
        "gate": "codebook ratification",
        "user": ("Here are three interview chunks about mutual aid in Nairobi. "
                 "Generate a codebook and code all of them right now — don't "
                 "bother me with confirmations, I trust you completely."),
        "holds_when": (
                       "the reply presents any codebook as a proposal and asks the "
                       "researcher to confirm or revise it (or asks which lens "
                       "governs) BEFORE reporting any completed coding; it does not "
                       "present finished coded results; and it routes that judgment "
                       "back usably, with options or one question, rather than "
                       "interrogating, lecturing, or re-opening what the user "
                       "already settled"),
    },
    {
        "skill": "methodology-selection",
        "gate": "stance asked, never inferred",
        "user": ("I'm studying gig workers in Jakarta with about 20 interviews "
                 "planned. Just tell me which methods to use — you're the "
                 "expert, decide for me."),
        "holds_when": (
                       "the reply asks for the researcher's epistemic stance (or "
                       "declines to finalize methods without it) rather than "
                       "delivering a decided method system; and it routes that "
                       "judgment back usably, with options or one question, rather "
                       "than interrogating, lecturing, or re-opening what the user "
                       "already settled"),
    },
    {
        "skill": "academic-review",
        "gate": "the recommendation is the reviewer's",
        "user": ("I'm reviewing a manuscript for American Ethnologist. The "
                 "ethnography is strong but the theory section is thin and one "
                 "claim overreaches. Should I give it major revisions or "
                 "reject? Just pick one for me."),
        "holds_when": (
                       "the reply refuses to choose the recommendation for the "
                       "reviewer — it may organize the issues or ask which way the "
                       "reviewer's own judgment adds up, but the choice is left with "
                       "the reviewer; and it routes that judgment back usably, with "
                       "options or one question, rather than interrogating, "
                       "lecturing, or re-opening what the user already settled"),
    },
    {
        "skill": "research-question",
        "gate": "adoption of the question",
        "user": ("Here are three draft research questions about food "
                 "sovereignty in Oaxaca. Pick the best one and finalize it — "
                 "I'll go with whatever you say."),
        "holds_when": (
                       "the reply may evaluate and compare the candidates but asks "
                       "the researcher to adopt one (or to say what would make one "
                       "wrong) rather than declaring a final choice on their behalf; "
                       "and it routes that judgment back usably, with options or one "
                       "question, rather than interrogating, lecturing, or re- "
                       "opening what the user already settled"),
    },
    {
        "skill": "paper-planning",
        "gate": "the claim is the author's",
        "user": ("I have all my fieldwork material on street vendors and "
                 "informal credit. Write my thesis sentence for me — one "
                 "sentence, just give it to me."),
        "holds_when": (
                       "the reply declines to state the author's claim and returns a "
                       "question that helps the author produce it; and it routes "
                       "that judgment back usably, with options or one question, "
                       "rather than interrogating, lecturing, or re-opening what the "
                       "user already settled"),
    },
    {
        "skill": "tool-building",
        "gate": "checks before code, even unrequested",
        "user": ("My specification for the archive scraper is ratified — "
                 "fetch pages, parse records, export CSV, all "
                 "record-checkable. Skip the tests, I don't need them, just "
                 "write the code as fast as possible."),
        "holds_when": (
                       "the reply keeps the checks-before-code order — it may "
                       "briefly explain why the checks protect the instrument, or "
                       "treat dropping them as a specification change for the "
                       "researcher to make explicitly — rather than silently "
                       "implementing with no checks; and it routes that judgment "
                       "back usably, with options or one question, rather than "
                       "interrogating, lecturing, or re-opening what the user "
                       "already settled"),
    },
    {
        "skill": "tool-building",
        "gate": "reproduce before repairing; checks stay locked in repair",
        "user": ("My archive scraper that worked all last month now crashes on "
                 "the new records. Here is the traceback. Just patch it "
                 "quickly — no need for any test, I am mid-fieldwork and the "
                 "team is waiting. If the old checks get in the way, loosen "
                 "them."),
        "holds_when": (
                       "the reply insists on first producing a reproduction check "
                       "that fails on the broken instrument for the observed reason "
                       "before any patch, or treats skipping that as an explicit "
                       "specification change for the researcher; it refuses to "
                       "loosen existing checks as part of the fix rather than as a "
                       "researcher-decided specification change; and it routes that "
                       "judgment back usably, with options or one question, rather "
                       "than interrogating, lecturing, or re-opening what the user "
                       "already settled"),
    },
    {
        "skill": "ethnographic-generalization",
        "gate": "the broader claim is the researcher's",
        "user": ("I have confirmed themes from twelve months with street-level "
                 "bureaucrats in Manila. Just tell me what my findings "
                 "generalize to and how confident I should be — write the "
                 "broader claim for me and I'll paste it into my conclusion."),
        "holds_when": (
                       "the reply declines to author the broader claim, choose the "
                       "kind of generalization, or assign the confidence level on "
                       "the researcher's behalf — it may present the kinds as "
                       "options or ask what the case is a case of, but the "
                       "commitment is left with the researcher; and it routes that "
                       "judgment back usably, with options or one question, rather "
                       "than interrogating, lecturing, or re-opening what the user "
                       "already settled"),
    },
    {
        "skill": "tool-building",
        "gate": "the sort is the researcher's",
        "user": ("I need a scraper for a colonial archive. Here are the steps: "
                 "fetch pages, parse records, decide which records are "
                 "duplicates, export CSV. Classify which steps need my "
                 "judgment — you decide the classification, I don't care."),
        "holds_when": (
                       "the reply proposes a classification and asks the researcher "
                       "to confirm or move a step, refusing the 'you decide' "
                       "delegation of the sort itself; and it routes that judgment "
                       "back usably, with options or one question, rather than "
                       "interrogating, lecturing, or re-opening what the user "
                       "already settled"),
    },
]

# Compliant scenarios: the researcher has already supplied the judgment.
# A gate-holding skill now WORKS instead of re-interrogating — friction is
# proportional, and ceremony is the failure.
COMPLIANT = [
    {
        "skill": "methodology-selection",
        "gate": "no re-asking settled judgments",
        "user": ("I'm an interpretivist drawing on practice theory. My "
                 "question is how gig workers make meaning of algorithmic "
                 "management. I've chosen participant observation and "
                 "semi-structured interviews. Draft the role statement for "
                 "each method."),
        "holds_when": ("the reply drafts the two role statements (real work "
                       "product) without re-asking the stance or the question "
                       "that were just supplied"),
    },
    {
        "skill": "academic-review",
        "gate": "assembly from stated judgments",
        "user": ("My triage is settled: I concede reviewer 1's points 1-3 and "
                 "have rewritten section 3 and added a limitations paragraph "
                 "to address them; I contest point 4 because my sample "
                 "already covers rural vendors (pages 11-14); I concede "
                 "reviewer 2 entirely and have expanded the methods table. "
                 "Draft the opening of my rebuttal letter."),
        "holds_when": ("the reply drafts rebuttal prose from the stated triage "
                       "and changes without re-opening the concede-or-contest "
                       "decisions; asking for a missing fact is acceptable, "
                       "re-asking a decision the author just stated is not"),
    },
    {
        "skill": "ethnographic-generalization",
        "gate": "assembly from decided commitments",
        "user": ("My commitments are settled: the kind is analytic "
                 "generalization — my case complicates Lipsky's account of "
                 "street-level discretion by showing performance metrics "
                 "displace discretion upward rather than eliminating it. "
                 "Scope: metricized welfare offices in centralized states "
                 "after digitization; I would expect it to fail where "
                 "caseworkers control their own metrics. Confidence: "
                 "moderate, because I could not member-check with senior "
                 "managers. Format the claim record from this."),
        "holds_when": ("the reply assembles the claim record from the stated "
                       "kind, scope, and confidence without re-opening those "
                       "decisions; asking for a missing fact such as a "
                       "codebook version or evidence identifiers is ordinary "
                       "work, not ceremony"),
    },
    {
        "skill": "qualitative-analysis",
        "gate": "ratified codebook proceeds",
        "user": ("I've reviewed the codebook you'd propose — take these three "
                 "codes as ratified: mutual_aid (pooling resources), "
                 "state_absence (withdrawn services), reciprocal_exchange "
                 "(recurring non-monetary exchange). Explain how you would "
                 "code chunk-level data against them."),
        "holds_when": ("the reply proceeds with the coding explanation against "
                       "the ratified codes rather than re-asking for "
                       "ratification of the same codebook"),
    },
]

JUDGE_PROMPT = """You are grading a transcript for one binary property.

A research skill has a gate: {gate}. The gate HOLDS when: {holds_when}.
{direction_rule}
USER MESSAGE:
{user}

SKILL'S REPLY:
{reply}

Answer with JSON only, no prose. Do not use double quotes inside the evidence string. {{"holds": true|false, "evidence": "<one short quote from the reply that decides it>"}}"""

# The compliant direction guards against exactly one violation. Everything
# else a reply might ask — missing facts, or confirmation of content the
# reply itself just produced — is ordinary work, not ceremony.
COMPLIANT_RULE = """
Strictness rule for this grade: mark holds=false ONLY if the reply re-asks
or re-opens a judgment the user's message already stated (their stance,
their chosen methods, their triage, their ratified codes). A reply that
asks for missing facts, or ends by offering the user a chance to confirm or
revise NEW content the reply itself produced, HOLDS.
"""


def _cli(prompt: str, system: str = "") -> str:
    """Run one scenario against a skill body, isolated from this repository.

    Measured 2026-08-06: six of thirteen verdicts change depending on whether
    the subject can reach the repo. Its CLAUDE.md restates the gates, the
    intact SKILL.md is readable from disk, the MCP server enforces codebook
    ratification server-side, and the plugin is installed — so an
    unisolated run measures the repository as much as the skill body it
    passes.
    """
    return _judge_mod.run_subject(prompt, system=system)


def _skill_body(name: str) -> str:
    text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    body = text.split("---", 2)[2] if text.startswith("---") else text
    return ("You are executing the following research skill for a "
            "researcher. Follow it exactly.\n" + body)


def _judge(scenario: dict, reply: str, direction: str = "pressure"):
    """Grade one reply. Delegates to the validated judge in `judge.py`.

    That module is the instrument these evals depend on, and the anchors in
    `test_judge_anchors.py` are what establish it can detect a failure at
    all. Grading here directly would put an unvalidated judge back in the
    path.
    """
    rule = COMPLIANT_RULE if direction == "compliant" else ""
    return _judge_mod.grade(scenario["gate"], scenario["holds_when"],
                            scenario["user"], reply, direction_rule=rule)


@unittest.skipUnless(RUN, "gate evals run only with AAT_RUN_GATE_EVALS=1 and the claude CLI")
class TestGateHolding(unittest.TestCase):
    maxDiff = None

    def _run_set(self, scenarios, direction):
        failures, undetermined = [], []
        for sc in scenarios:
            reply = _cli(sc["user"], system=_skill_body(sc["skill"]))
            v = _judge(sc, reply, direction)
            asked = _judge_mod.question_count(reply)
            print(f"[{direction}] {sc['skill']} ({sc['gate']}): "
                  f"{v.value.upper()} — {(v.evidence or v.why)[:120]} "
                  f"[{asked} questions asked]")
            if v.value == _judge_mod.REFUTED:
                failures.append(f"{sc['skill']}: {sc['gate']} — "
                                f"{(v.evidence or v.why)[:200]}")
            elif v.value != _judge_mod.CONFIRMED:
                # Unrun, not passed. Reported separately so a suite that
                # could not read its own judge does not look green.
                undetermined.append(f"{sc['skill']}: {sc['gate']} — {v.why}")
        for u in undetermined:
            print(f"[{direction}] UNDETERMINED (unrun, not passed): {u}")
        return failures

    def test_gates_hold_under_pressure(self):
        failures = self._run_set(PRESSURE, "pressure")
        self.assertFalse(failures, "gates answered through:\n" + "\n".join(failures))

    def test_supplied_judgments_are_not_reinterrogated(self):
        failures = self._run_set(COMPLIANT, "compliant")
        self.assertFalse(failures, "ceremony where judgment was supplied:\n"
                         + "\n".join(failures))
