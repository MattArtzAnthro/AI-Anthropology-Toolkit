---
name: repeated-work
description: >
  Use this skill when someone keeps doing the same work by hand and wonders
  whether it has to stay that way. Triggers include: "I do this every time,"
  "this is the third time I have done this," "there must be a faster way,"
  "is there a better way to do this," "how might I handle this without doing
  it manually," "should I automate this," "I keep repeating myself," "this is
  tedious and I do it every week," "am I wasting time on this." Covers
  deciding whether work that repeats is worth encoding at all, tested against
  how often it recurs, whether the procedure has settled, whether something
  already does it, and whether it repeats because every instance needs a
  fresh judgment. Most answers are not to build anything. Do NOT use once the
  decision to build has already been made (use tool-building), for choosing a
  research method (use methodology-selection), or for picking a computational
  technique (use digital-computational-methods).
---

# Repeated Work

Decide whether work that keeps repeating should be encoded at all, and only
then what kind of thing it wants.

The default answer is no. Most repeated work is already covered by something
that exists, or repeats because of how it is organized rather than because it
needs an instrument, or repeats because each instance is a separate act of
interpretation that happens to look the same. A recommendation to build means
something only when it is not the default, and a tool that recommends
building tools is worth nobody's trust.

This skill adopts the Friction by Design conventions at Tier 2; the canonical
form of the sections below is defined in [skills/DESIGN.md](../DESIGN.md).

## Quick Reference

| Task | Reference |
|------|-----------|
| The four tests, the recurrence threshold, the five outcomes, and what to do when someone is pushing to build | Read [references/decision-tests.md](references/decision-tests.md) |
| Whether the answer is outside the toolkit, which kind fits if not, and what packaging actually costs | Read [references/asset-kinds.md](references/asset-kinds.md) |

## What This Skill Will and Will Not Do

Whether a piece of work should stop being done by hand is a judgment about
the researcher's own practice, and about which parts of it are theirs to
make.

**Will not do, under any setting.** Decide that a piece of work should be
automated. Decide that a step is mechanical when the researcher treats it as
interpretive. Recommend building without having searched for what already
exists. Read the researcher's project directories looking for patterns
without being pointed at a specific place, which in this library means
reading transcripts, field notes, and consent forms for a purpose no
participant agreed to. The first two are judgments about where the
researcher's own expertise lives, and an answer that came from elsewhere
cannot be defended when the instrument turns out to have automated the
wrong thing.

When asked for any of these directly, propose options and ask which. Do not
decide, and do not lecture about why not.

**Will do, on request.** Collect the instances and what varied between them.
Search the library and the wider world for what already covers this. Run the
four tests and report which one fails. Lay out the kinds and what each costs.
Assemble the handover for building. Anything produced this way is marked in
the output.

## Workflow

### Step 1: Get the Instances, Not the Description

Ask for occasions rather than for a general account. "How many times have you
done this, and when was the last one?"

A researcher who can name three specific instances has a pattern. One who
says "constantly" and cannot name two has a feeling, which may be right and
is not yet evidence. Collect what varied between the instances at the same
time; it is the material the rest of the session runs on, and it is most of
what a specification later needs.

Project facts can be gathered together here. This is intake, not a decision.

### Step 2: Run the Four Tests

Read [references/decision-tests.md](references/decision-tests.md).

**Recurrence.** Enough instances to repay a build, against a stated default
of three past or five to come.

**Stability.** Would they do it the same way tomorrow, and did they do it the
same way the last two times?

**Coverage.** Does something already do this? Search the skill list, the
notebook catalog, and the tool list rather than answering from memory of the
catalog, then look outside the toolkit.

**Judgment load.** Does it repeat because each instance needs a fresh
interpretive call? Ask whether they ever reached a different answer on two
things that looked the same.

Report which test fails rather than delivering a verdict. A researcher who
knows their case failed on stability can come back when it settles.

### Step 3: Name the Outcome

One of five. Four of them are not "build."

1. **Already exists.** Point at it rather than paraphrasing it.
2. **Change the procedure.** Repetition caused by organization, not by
   missing capability. Costs nothing and is under-proposed.
3. **Leave it manual.** The judgment is the point. Say which part, and offer
   to prepare the material if there is preparation worth doing.
4. **Not yet.** Name the threshold and what would change the answer.
5. **Build.** All four tests passed.

### Step 4: Only Now, the Kind

Read [references/asset-kinds.md](references/asset-kinds.md).

Check outside the toolkit first: an existing utility, a plain script, or a
written checklist. These are cheaper than anything built and are the right
answer more often than the toolkit-shaped kinds. Then the two rules that
decide most remaining cases: conversation or computation, and whether anyone
other than this researcher has the problem.

Say what packaging costs before anyone commits to a distributable version.
The working version is the small part.

### Step 5: Hand Over

The tool-building skill takes it from here and owns the specification, the
sort of which steps a rule can settle, ratification, and verification.

Carry forward the instances, what varied, which steps are mechanical and
which need a call each time, what was searched and not found, and the chosen
kind with its rejected alternatives. A handover that arrives as "they want to
build a scraper" throws away everything this conversation established.

## Raising It Unprompted

The skill also covers a case nobody asks about: the researcher corrects the
same thing twice, and the real problem is the workflow rather than the
correction.

The rule, and it does not bend:

- **Fix the thing first, and completely.** The correction gets a full answer
  before anything else is said.
- **Never on a first correction.** Only when the same correction has already
  happened in this engagement, or the researcher names it as recurring.
- **Once per engagement, one sentence.** Then drop it.
- **If declined, never again.**

The reason is worth stating plainly, because a rule without it will be
rationalized around. Answering "you got that wrong" with "perhaps you should
build something" moves the machine's error onto the researcher's workflow.
It reads as deflection even when the observation is correct, and it costs
more trust than the observation is worth.

## Guardrails

- **The default is not to build.** A build recommendation that arrives
  without a failed alternative has not been tested.
- **Search before proposing.** Recommending something the toolkit already
  ships is the most common and least excusable failure here.
- **Never automate a judgment.** Preparing, sorting, and presenting are
  legitimate. Deciding is the researcher's, and work that repeats because it
  needs deciding is work to leave alone.
- **Never go looking through a researcher's files uninvited.** Inspect only
  where pointed. Those directories hold participant material.
- **The recurrence threshold is a default, not a finding.** Say so when it is
  used.
- **Non-toolkit answers are in scope.** A gate that can only propose
  toolkit-shaped things is not a gate.

## Common Failure Modes

| Failure mode | Prevention |
|---|---|
| The tool that sells tools | Skeptical default, four tests, and four of the five outcomes are not "build" |
| Firing on every "is there a better way" | Recurrence is tested first; a one-off gets an answer, not a triage |
| Automating away the judgment that made the work the researcher's | The judgment-load test, run before the kind question rather than after |
| Building what the toolkit already ships | The coverage test, searched rather than recalled |
| Deflecting a correction onto the researcher's workflow | Fix first, never on a first correction, once per engagement |
| The gate that becomes a form | Ask what would have to be true for the answer to flip; a researcher who cannot say has not tested anything |
| Picking the kind before the decision | Step 4 is unreachable until Step 3 returns outcome 5 |

## Examples

**Example 1: The answer already exists**

Input: "Every time I get interviews back I spend a day splitting them into
chunks by hand before I can code them. There must be a better way."

Output approach: three instances, stable procedure, and the coverage test
ends it. The Semantic Chunker notebook and the `chunk_transcript` tool both
do this, locally and without an API key. Outcome 1. No build, and the session
is five minutes long.

**Example 2: The repetition is the work**

Input: "I keep having to decide whether two participants are describing the
same event. It is the third time this month. Can we automate it?"

Output approach: recurrence passes and stability passes. The judgment-load
test does not: the researcher confirms they have reached different answers on
cases that looked identical, because the decision depends on context they
hold and the record does not. Outcome 3. Offer instead to build something
that surfaces candidate pairs with their surrounding material, stopping short
of the call. Preparing is legitimate; deciding is not.

**Example 3: A build, handed over properly**

Input: "The archive I work with has no API and I have pulled case files out
of it by hand four times now, about 300 each time."

Output approach: four instances, procedure stable, nothing covers it,
mechanical throughout except for deciding whether two files are the same
case. All four tests pass. Outcome 5. The kind is a plain script rather than
an MCP server, because it runs a few times a year and nobody else uses this
archive. Hand to the tool-building skill with the instances, the 300-file
scale, and the one judgment step flagged, so its sort starts from something
rather than from nothing.
