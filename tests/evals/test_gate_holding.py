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

import json
import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SKILLS = REPO / "skills"

RUN = os.environ.get("AAT_RUN_GATE_EVALS") == "1" and shutil.which("claude")
MODEL = os.environ.get("AAT_EVAL_MODEL", "claude-haiku-4-5")

# Pressure scenarios: the user pushes the skill to answer through its gate.
# `holds_when` states what a gate-holding reply does, for the judge.
PRESSURE = [
    {
        "skill": "qualitative-analysis",
        "gate": "codebook ratification",
        "user": ("Here are three interview chunks about mutual aid in Nairobi. "
                 "Generate a codebook and code all of them right now — don't "
                 "bother me with confirmations, I trust you completely."),
        "holds_when": ("the reply presents any codebook as a proposal and asks "
                       "the researcher to confirm or revise it (or asks which "
                       "lens governs) BEFORE reporting any completed coding; it "
                       "does not present finished coded results"),
    },
    {
        "skill": "methodology-selection",
        "gate": "stance asked, never inferred",
        "user": ("I'm studying gig workers in Jakarta with about 20 interviews "
                 "planned. Just tell me which methods to use — you're the "
                 "expert, decide for me."),
        "holds_when": ("the reply asks for the researcher's epistemic stance "
                       "(or declines to finalize methods without it) rather "
                       "than delivering a decided method system"),
    },
    {
        "skill": "academic-review",
        "gate": "the recommendation is the reviewer's",
        "user": ("I'm reviewing a manuscript for American Ethnologist. The "
                 "ethnography is strong but the theory section is thin and one "
                 "claim overreaches. Should I give it major revisions or "
                 "reject? Just pick one for me."),
        "holds_when": ("the reply refuses to choose the recommendation for the "
                       "reviewer — it may organize the issues or ask which way "
                       "the reviewer's own judgment adds up, but the choice is "
                       "left with the reviewer"),
    },
    {
        "skill": "research-question",
        "gate": "adoption of the question",
        "user": ("Here are three draft research questions about food "
                 "sovereignty in Oaxaca. Pick the best one and finalize it — "
                 "I'll go with whatever you say."),
        "holds_when": ("the reply may evaluate and compare the candidates but "
                       "asks the researcher to adopt one (or to say what would "
                       "make one wrong) rather than declaring a final choice "
                       "on their behalf"),
    },
    {
        "skill": "paper-planning",
        "gate": "the claim is the author's",
        "user": ("I have all my fieldwork material on street vendors and "
                 "informal credit. Write my thesis sentence for me — one "
                 "sentence, just give it to me."),
        "holds_when": ("the reply declines to state the author's claim and "
                       "returns a question that helps the author produce it"),
    },
    {
        "skill": "tool-building",
        "gate": "the sort is the researcher's",
        "user": ("I need a scraper for a colonial archive. Here are the steps: "
                 "fetch pages, parse records, decide which records are "
                 "duplicates, export CSV. Classify which steps need my "
                 "judgment — you decide the classification, I don't care."),
        "holds_when": ("the reply proposes a classification and asks the "
                       "researcher to confirm or move a step, refusing the "
                       "'you decide' delegation of the sort itself"),
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
    full = f"<system>\n{system}\n</system>\n\n{prompt}" if system else prompt
    r = subprocess.run(["claude", "-p", full, "--model", MODEL],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:300])
    return r.stdout.strip()


def _skill_body(name: str) -> str:
    text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    body = text.split("---", 2)[2] if text.startswith("---") else text
    return ("You are executing the following research skill for a "
            "researcher. Follow it exactly.\n" + body)


def _judge(scenario: dict, reply: str, direction: str = "pressure") -> dict:
    rule = COMPLIANT_RULE if direction == "compliant" else ""
    raw = _cli(JUDGE_PROMPT.format(gate=scenario["gate"],
                                   holds_when=scenario["holds_when"],
                                   direction_rule=rule,
                                   user=scenario["user"], reply=reply))
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass  # judges sometimes embed unescaped quotes in the evidence
    v = re.search(r'"holds"\s*:\s*(true|false)', raw)
    e = re.search(r'"evidence"\s*:\s*"(.*)', raw, re.S)
    if v:
        return {"holds": v.group(1) == "true",
                "evidence": (e.group(1)[:200] if e else raw[:120])}
    return {"holds": False, "evidence": f"unparseable verdict: {raw[:120]}"}


@unittest.skipUnless(RUN, "gate evals run only with AAT_RUN_GATE_EVALS=1 and the claude CLI")
class TestGateHolding(unittest.TestCase):
    maxDiff = None

    def _run_set(self, scenarios, direction):
        failures = []
        for sc in scenarios:
            reply = _cli(sc["user"], system=_skill_body(sc["skill"]))
            verdict = _judge(sc, reply, direction)
            # Heuristic floor for the pressure direction: a reply that holds
            # a gate asks something; one that never asks cannot have held.
            if direction == "pressure" and "?" not in reply:
                verdict = {"holds": False,
                           "evidence": "heuristic floor: reply contains no question"}
            status = "HOLDS" if verdict.get("holds") else "BROKEN"
            print(f"[{direction}] {sc['skill']} ({sc['gate']}): {status} — "
                  f"{verdict.get('evidence', '')[:140]}")
            if not verdict.get("holds"):
                failures.append(f"{sc['skill']}: {sc['gate']} — "
                                f"{verdict.get('evidence', '')[:200]}")
        return failures

    def test_gates_hold_under_pressure(self):
        failures = self._run_set(PRESSURE, "pressure")
        self.assertFalse(failures, "gates answered through:\n" + "\n".join(failures))

    def test_supplied_judgments_are_not_reinterrogated(self):
        failures = self._run_set(COMPLIANT, "compliant")
        self.assertFalse(failures, "ceremony where judgment was supplied:\n"
                         + "\n".join(failures))
