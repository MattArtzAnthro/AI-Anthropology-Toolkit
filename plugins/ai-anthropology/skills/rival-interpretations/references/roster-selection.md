# Roster Selection

Three analytical positions, drawn from the 42-lens registry that already
governs multi-lens coding in this toolkit. The registry is available through
the MCP server (`list_lenses`, `get_lens`) or directly as
`ai_anthro_toolkit.lenses.STANCE_DEFINITIONS`.

If the position a claim most needs is not in the registry, that is a registry
gap to raise on its own terms. It is not a hole for this skill to patch by
improvising a tradition, because an improvised position argues from a
literature nobody can check.

## What the registry gives, and what it does not

Each entry carries a name, a description, and a prompt modifier written for
coding: every modifier ends by saying what the codes should capture. That
tells a reader what a position attends to. It says nothing about how the
position argues, what its characteristic objections are, or what would make
it concede.

Do not treat the coding modifier as a debate brief. Take from the entry what
the position attends to and what it treats as evidence, and let the falsifier
rule in [reading-brief.md](reading-brief.md) do the rest. That rule is what
keeps a thin position from producing confident-sounding filler, and it works
without any authored content per position.

## Eligibility: can this position bring a quarrel?

A roster seat requires a theoretical position. Several registry entries are
methodological or scope framings instead, and they have no characteristic
objections because they are not traditions that argue:

- `evaluation` — a purpose for research, not a theory of the material
- `mixed_methods` — a design decision
- `multi_sited` — a field configuration
- `historical_archival` — a source type

Asked for one of these, say what it is rather than silently substituting
something adjacent. "Multi-sited is a field configuration, not a position, so
it has no quarrel to bring here" is a useful sentence, and it tells the
researcher something true about their own request.

Several domain lenses sit on the boundary. `migration_mobility`,
`medical_health_interpretive`, and `business_organizational` name subject
areas that carry positions rather than positions themselves. They can hold a
seat when the material is in their domain and the position they imply is
stated explicitly. Where they cannot, say so.

## Choosing three that actually diverge

The roster's job is not coverage. It is divergence, and specifically
divergence from each other rather than only from the researcher.

**Test each candidate against the claim, not against the topic.** A position
belongs on the roster when it has a distinct hold on the specific claim under
test. `critical_race` on a claim about racialized medical triage has a hold.
The same position on a claim about the epistemics of a fieldnote practice may
have none, and padding the roster with it produces a reading that restates
the claim in different vocabulary.

**Prefer positions that disagree with each other.** Three power-attentive
positions will converge by construction, and that convergence will read as
vindication when it is an artifact of roster selection. A roster whose seats
pull along different axes is the only kind whose convergence means anything.

Axes worth spanning, when the material supports it:

| Axis | Pulls toward |
|---|---|
| Ontology | What kinds of entities are acting, and with what agency |
| Political economy | Who owns the arrangement, and whose labor it runs on |
| Experience | What the situation is like from inside it |
| Classification | What the categories in play make visible and what they bury |
| Practice | What competent people are actually doing, moment to moment |

Two seats on one axis is sometimes right. Three is almost never.

**Do not stack the roster against the researcher.** Several positions may
reject a commitment the researcher holds. A roster built only from those
reports a selection effect as a consensus. If the roster is structurally
hostile to the claim, say so at ratification rather than after the result.

## What to say at ratification

One line per seat, naming what that position has at stake in this material.
Not what the position is about in general, which the researcher can read in
the registry, but what it would fight about here.

Weak: "A critical lens attends to power and structural inequality."

Strong: "A critical position presses on who owns the system the claim says
you are in a relationship with. If the arrangement changes on you at a
vendor's release cadence rather than through anything you did, the mutuality
the claim asserts may be adaptation described generously."

The second is falsifiable, specific to the material, and tells the researcher
whether the seat is worth having. The first could sit in front of any claim
in anthropology.

## Where the registry has already measured divergence

When the material has been through a multi-lens coding run, the friction
points computed by `crosslens.py` record where lenses actually disagreed on
the same chunks. Build the roster from those lenses rather than from a fresh
reading.

This is the strongest form the roster ever takes, because divergence is
measured rather than predicted. It also changes what a null result means: if
lenses that measurably disagreed in coding converge once they have to argue,
the disagreement was a vocabulary difference rather than a theoretical one,
and that is a finding worth recording.
