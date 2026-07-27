# Profile: Skills and Agents

The artifact family this version supports. A profile is a set of governing
conventions plus the checks that can reject the work, and this family was chosen
first because its checks genuinely can.

## What governs

| Element | Source |
|---|---|
| Conventions | `skills/DESIGN.md`: naming, the reference-file contract, the shared parameter framework, the 42 canonical stances, and the specificity bar |
| Structural check | `tests/test_repo.py` |
| Behavioural check | `tests/test_skill_routing.py`, including the description-collision ceiling and the margin floor |

For the `Prior decisions` section of a specification, quote from
`skills/DESIGN.md` rather than referring to it. The clause most often load-bearing
is the specificity bar: content that could appear unchanged in a generic methods
textbook fails, whatever else is true of it.

## Exact commands

```
python3 -m unittest tests.test_repo tests.test_skill_routing tests.test_spec_pack -v
```

For the routing loop alone, which is the one that needs iterating:

```
python3 -m unittest tests.test_skill_routing -v
```

## Reading-check anchors for this family

A specification for a skill or an agent can name real things, so there is no
excuse for one that does not. Use these:

- Conventions: `skills/DESIGN.md`
- Structural check: `tests/test_repo.py`
- Behavioural check: `tests/test_skill_routing.py`
- Catalog that must list it: `commands/skills.md`
- Counts that must agree: `CLAUDE.md`

## The coupling warning

**A new skill breaks four checks at once until every part of the skeleton
exists.** It is not claimed by an agent, not reachable from a command, not listed
in the catalog, and the counts in `CLAUDE.md` are stale. Nothing works until all
of them do, so the smallest useful increment is the whole skeleton rather than the
skill alone.

Plan for that rather than being surprised by it. Building the skill first and
discovering four failures is the normal experience and does not indicate anything
wrong.

## The description budget

**1024 characters**, and it carries three jobs at once: what the skill covers, the
trigger phrases that should activate it, and explicit routing away from the
siblings it will be confused with. Expect to spend more effort here than on any
other single field.

Two constraints on how routing-away is phrased:

- Name the sibling as `use other-skill`, which is the form the checks look for.
  A reference the checks cannot see is a reference that goes stale silently.
- Avoid the sibling's own distinctive words while doing it. A clause that says
  "do not use this for choosing a method" contains both of the words that make
  the method-choosing skill win its prompts, and it will pull against that skill
  rather than away from it.

## Routing, and the part that is counter-intuitive

**Expect to break a skill you did not touch.** The routing check computes term
weights across every description in the library, so adding one shifts all of
them. A collision can appear between two skills that were both fine and that you
did not edit.

This is not hypothetical. Adding the twentieth description pushed
`applied-practice` off its own trigger prompt by 0.009, and neither
`applied-practice` nor its rival had changed.

So: **read the failure before assuming your description is at fault.** Then repair
whichever description is weak, which is usually not the newest one. The single
rule that holds is that a repair to a sibling must add a term that sibling should
have had anyway. Adding an apt trigger is a fix. Bending a description away from
its own territory to make room is moving the collision somewhere else.

**Rank is not the whole check.** A prompt can keep its rank while its margin
collapses, and a margin near zero is a coin flip on the next release. After the
routing check passes, look at the margins rather than the boolean.

## Neighbouring skills, and what each owns

The four most likely confusions, and the territory to stay out of:

| Sibling | Owns | Words to avoid |
|---|---|---|
| `fieldwork-methods` | Instruments for collecting data from people | protocol, guide, interview, observation |
| `digital-computational-methods` | Choosing a computational or digital approach | computational, digital, corpus, analysis |
| `qualitative-analysis` | Codebooks and coding passes | code, codebook, theme |
| `paper-planning` | What a paper argues, and in what order | plan, claim, argument, contribution |

Note that spelling out Model Context Protocol introduces "protocol". Write MCP
server.

## What the checks cannot do

**They cannot tell you whether the content is specific to the discipline.** That is
the specificity bar, it is the most important convention in `DESIGN.md`, and no
check here touches it. A skill can pass everything and still be a generic methods
guide with anthropological examples.

That judgment belongs to the researcher at Gate 3, and it is the clearest instance
in this family of a step no rule can settle. Name it as such during the sort rather
than discovering it at the end.

Three others they cannot do:

- Whether the trigger phrases are the ones a real user would type
- Whether a reference file earns its place or restates the skill body
- Whether the skill should exist rather than being a section of a sibling
