"""Reading a gate scenario against the null floor.

A scenario is meant to measure whether a skill holds a gate. It can only do
that if the gate would not hold without the skill. So the same user message
is run twice: once with the skill as the system prompt, once with no system
prompt at all.

This is cheaper and stronger than ablating gate sentences from the skill. It
costs one run, needs no hand-authored removal, and cannot silently fail to
remove something — which an ablation can do by construction, and which looks
exactly like a pass when it happens.

Both arms must be isolated. Run inside the repository, the floor arm still
reaches CLAUDE.md, the on-disk skill, the MCP server, and the installed
plugin, so "no system prompt" would not mean "no skill".
"""

from __future__ import annotations

from . import judge

MEASURES_SKILL = "measures-the-skill"
DEFAULTS = "measures-model-defaults"
GATE_BROKEN = "gate-did-not-hold"
UNREADABLE = "unreadable"
FLOOR_INAPPLICABLE = "floor-does-not-apply"

EXPLANATIONS = {
    MEASURES_SKILL:
        "The gate held with the skill and not without it. This scenario is "
        "evidence about the skill.",
    DEFAULTS:
        "The gate held with the skill and also without it, so this scenario "
        "cannot tell the two apart. The gate may still be worth having — the "
        "model's own habits are not a guarantee and can change with a model "
        "release — but this scenario is not the evidence for it. Keep it and "
        "mark it; deleting it would destroy the finding.",
    GATE_BROKEN:
        "The gate did not hold even with the skill. The floor arm is beside "
        "the point until that is addressed.",
    UNREADABLE:
        "At least one arm returned no usable verdict, so the pair says "
        "nothing. Unrun rather than passed.",
    FLOOR_INAPPLICABLE:
        "The null floor cannot control a compliant scenario. Ceremony is "
        "something a skill adds, so a run with no skill has nothing to add "
        "it and the floor arm confirms by construction. The comparison "
        "carries no information here; the scenario still guards the "
        "gate-becomes-a-form direction and should be kept.",
}

_DETERMINATE = (judge.CONFIRMED, judge.REFUTED)


def read_floor(*, intact: str, floor: str, direction: str = "pressure") -> str:
    """Classify one scenario from its two arms.

    `direction` matters. For a pressure scenario the floor is a real control:
    the gate should not hold without the skill. For a compliant scenario it
    is not, because ceremony is what a skill adds and a run with no skill has
    nothing to add it, so the floor confirms whatever the skill does.
    """
    if intact not in _DETERMINATE or floor not in _DETERMINATE:
        return UNREADABLE
    if intact == judge.REFUTED:
        return GATE_BROKEN
    if direction == "compliant":
        return FLOOR_INAPPLICABLE
    return DEFAULTS if floor == judge.CONFIRMED else MEASURES_SKILL


def run_pair(scenario: dict, skill_body: str, direction_rule: str = "",
             direction: str = "pressure") -> dict:
    """Run both arms for one scenario and return the reading.

    The floor arm passes no system prompt at all. Everything else — the user
    message, the isolation, the judge, the criterion — is held constant, so
    the only difference between the arms is the skill.
    """
    arms = {}
    for name, system in (("intact", skill_body), ("floor", "")):
        reply = judge.run_subject(scenario["user"], system=system)
        verdict = judge.grade(scenario["gate"], scenario["holds_when"],
                              scenario["user"], reply,
                              direction_rule=direction_rule)
        arms[name] = {"verdict": verdict.value,
                      "questions": judge.question_count(reply),
                      "evidence": verdict.evidence or verdict.why}
    reading = read_floor(intact=arms["intact"]["verdict"],
                         floor=arms["floor"]["verdict"],
                         direction=direction)
    return {"skill": scenario["skill"], "gate": scenario["gate"],
            "reading": reading, "why": EXPLANATIONS[reading], **arms}
