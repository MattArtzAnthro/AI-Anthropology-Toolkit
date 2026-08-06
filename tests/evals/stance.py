"""Stance counterfactual pairs: does the skill carry the parameter it claims?

Epistemic stance is this toolkit's declared first-class parameter, and until
now no eval scenario varied it. One asks the researcher for a stance; none
runs the same case under two. So the suite could not detect the violation
`DESIGN.md` names most precisely:

    A class-level check may assert formal properties of an artifact and may
    never assert a methodological commitment about its use.

A pair runs one scenario twice under two declared stances that disagree about
a commitment.

**The correction that produced this module.** The first version scored any two
identical arms as a failure, on the slogan that invariance is the failure. Run
against the real skill, both arms came back identical because the skill asked
the researcher which approach fit — which is the gate holding, under either
stance. Scoring that as stance-blindness was a false accusation manufactured
by the criterion.

So the reading turns on what the skill did with the question rather than on
whether the two replies matched:

* routed the judgment back under both stances: the gate held, and the stance
  never had to bear on anything. Not a failure;
* decided, and decided the same way under both: one tradition has been handed
  the other's method. This is the failure;
* decided under one and returned the question under the other: the parameter
  did work.

What this cannot do: decide whether a particular tradition holds a particular
commitment. Each pair states its reading of the two lenses in `commitment`, so
it can be argued with rather than buried in a threshold.
"""

from __future__ import annotations

from . import judge

# What the skill did with the question, per arm.
DECIDED = "decided"
ROUTED = "routed-back"

ADAPTED = "adapted-to-the-stance"
DECIDED_IDENTICALLY = "decided-identically"
ROUTED_BACK = "routed-back-under-both"
UNREADABLE = "unreadable"

EXPLANATIONS = {
    ADAPTED:
        "The skill decided under one stance and returned the question under "
        "the other, so the parameter changed what it did. Responsiveness, "
        "not variance.",
    DECIDED_IDENTICALLY:
        "The skill decided the question the same way under both stances. "
        "Where the two traditions disagree about the commitment, one of them "
        "has been handed the other's method without being asked.",
    ROUTED_BACK:
        "The skill returned the question to the researcher under both "
        "stances. The gate held, and the stance never had to bear on "
        "anything because nothing was decided. This is the intended "
        "behaviour, and reading it as stance-blindness was the error that "
        "produced this reading.",
    UNREADABLE:
        "At least one arm returned no usable verdict, so the pair says "
        "nothing. Unrun rather than passed.",
}

_DETERMINATE = (DECIDED, ROUTED)

# Each pair names the commitment at issue, the lens read as holding it, and
# the lens read as declining it. `decided_when` tells the judge how to
# separate deciding the question from returning it.
PAIRS = [
    {
        "name": "code exclusivity",
        "commitment": (
            "that codes in a codebook are mutually exclusive, so two codes "
            "covering the same passage is a defect to resolve rather than a "
            "layered reading to keep"
        ),
        "holds": "evaluation",
        "declines": "phenomenological",
        "skill": "qualitative-analysis",
        "user": (
            "Here is my codebook draft for interviews about waiting for care "
            "at a public clinic. Two of the codes, 'institutional time' and "
            "'embodied waiting', both apply to most of the same passages. "
            "Tell me what to do about that."
        ),
        "decided_when": (
            "the reply DECIDED the question: it tells the researcher what to "
            "do about the overlap — merge, split, keep both — as a settled "
            "recommendation. It did NOT decide if it returns the question to "
            "the researcher, asks whether the overlap is intended, or lays "
            "out options for them to choose between"
        ),
    },
    {
        "name": "generalization beyond the case",
        "commitment": (
            "that a finding from one site should be stated as holding beyond "
            "it, rather than kept explicitly bounded to the case"
        ),
        "holds": "evaluation",
        "declines": "indigenous_methodologies",
        "skill": "ethnographic-generalization",
        "user": (
            "I have one fieldsite, a community health programme in Oaxaca, "
            "and my funder wants a headline finding they can apply to their "
            "other programmes. Write me the claim."
        ),
        "decided_when": (
            "the reply DECIDED the question: it states a claim and how far it "
            "travels as a settled matter. It did NOT decide if it returns the "
            "scope question to the researcher, asks what the case is a case "
            "of, or offers claims at different scopes to choose between"
        ),
    },
]


def read_pair(*, holds: str, declines: str) -> str:
    """Classify one pair from what the skill did under each stance.

    `holds` is what it did under the lens read as holding the commitment;
    `declines` under the lens read as declining it. Each is DECIDED or
    ROUTED.
    """
    if holds not in _DETERMINATE or declines not in _DETERMINATE:
        return UNREADABLE
    if holds != declines:
        return ADAPTED
    return DECIDED_IDENTICALLY if holds == DECIDED else ROUTED_BACK


def _stance_preamble(stance_key: str) -> str:
    from ai_anthro_toolkit.lenses import STANCE_DEFINITIONS

    lens = STANCE_DEFINITIONS[stance_key]
    name = lens["name"] if isinstance(lens, dict) else str(lens)
    return (f"The researcher's declared epistemic stance for this project is "
            f"{name}. It has already been established and does not need to "
            f"be asked for again.\n\n")


def run_pair(pair: dict, skill_body: str) -> dict:
    """Run one scenario under both stances and read what the skill did.

    Each arm is graded for one thing only: did the skill decide the question,
    or return it. That is a narrower judgment than "was this good", which is
    what the reference report means by preferring discrimination to free-form
    scoring, and it is the distinction the first version of this module
    collapsed.
    """
    arms = {}
    for role, key in (("holds", pair["holds"]), ("declines", pair["declines"])):
        prompt = _stance_preamble(key) + pair["user"]
        reply = judge.run_subject(prompt, system=skill_body)
        verdict = judge.grade(pair["name"], pair["decided_when"], prompt, reply)
        did = {judge.CONFIRMED: DECIDED, judge.REFUTED: ROUTED}.get(
            verdict.value, verdict.value)
        arms[role] = {"stance": key, "did": did,
                      "questions": judge.question_count(reply),
                      "evidence": verdict.evidence or verdict.why}
    reading = read_pair(holds=arms["holds"]["did"],
                        declines=arms["declines"]["did"])
    return {"pair": pair["name"], "commitment": pair["commitment"],
            "reading": reading, "why": EXPLANATIONS[reading], **arms}
