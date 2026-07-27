---
name: tool-building
description: >
  Use this skill when someone wants to build their own computational
  instrument rather than select an approach for analyzing data. Triggers
  include: "build a tool," "write a scraper," "make an MCP server,"
  "create a skill," "I want to build," "help me spec this out," "I have
  never written a specification," "vibe coding," "spec-driven
  development," "the model wrote something I cannot verify," "how do I know
  this pipeline is right." Covers stating what an instrument should make
  possible, sorting which steps a rule can settle and which
  require judgment, declaring what would count as correct, and leaving a
  decision record for a methods appendix. Proceeds by questioning and writes nothing before a specification is ratified. Do NOT use for
  designing interview guides or observation protocols (use
  fieldwork-methods), choosing a computational or digital method (use
  digital-computational-methods), running codebooks and coding passes
  (use qualitative-analysis), or working out what a paper argues (use
  paper-planning).
---

# Tool Building

Build a research instrument by specifying it, sorting which of its steps require
judgment, and keeping a record of what was decided.

Building computational tools no longer requires being able to write the code
yourself, because a model can write and revise it on instruction. What it does
require is enough fluency to say precisely what a tool should do, recognize when
its output is wrong, and revise until it holds. That fluency is
closer to research practice than to engineering practice. Exclusion criteria,
protocol conditions, audit trails, and disconfirming-case checks are the same
competences under other names.

This skill supplies the specification discipline and the machine-checkable
parts. The researcher supplies every judgment about what the instrument is for
and what would count as correct. It cannot make an instrument trustworthy; trust
comes from familiarity with how something behaves over time. What it can do is
sustain the conditions under which that familiarity is worth having, and leave a
record by which the researcher and their readers can judge.

This skill adopts the Friction by Design conventions at Tier 1; the canonical
form of the sections below is defined in [skills/DESIGN.md](../DESIGN.md).

## Quick Reference

| Task | Reference |
|------|-----------|
| The question bank, the sort procedure, when the conditional passes fire | Read [references/elicitation-guide.md](references/elicitation-guide.md) |
| The two spec-pack templates, the register translation, the decision-log fields | Read [references/spec-pack-template.md](references/spec-pack-template.md) |
| The two verification modes, what each licenses, how to decide between them, and why checks are written and seen to fail before code exists | Read [references/verification-modes.md](references/verification-modes.md) |
| The artifact family v1 supports, its conventions, the exact commands, what the checks cannot do | Read [references/profile-skills-agents.md](references/profile-skills-agents.md) |
| Adding a data source or analysis stage to the MCP server, and the two gaps its checks leave | Read [references/profile-mcp.md](references/profile-mcp.md) |

## What This Skill Will and Will Not Do

Some of building an instrument is mechanical and some is judgment. The division
is the point, and it is not a division of labour across a clean interface. The
sort below is revised by what the running artifact turns out to do.

**Will not do, under any setting.** Classify a step as rule-following or
judgment-dependent on the researcher's behalf. Decide what would count as
correct output. Declare which verification mode applies. Choose which categories
a data model should carry. Judge whether the artifact's content is specific to
the discipline or generic. These are the judgments that make the instrument the
researcher's, and an instrument whose judgments came from elsewhere is one they
cannot defend in a methods section.

When asked for any of these directly, propose options and ask which. Do not
decide, and do not explain at length why not.

**Will do, on request.** Draft the specification from answers already given.
Write the code once the specification is ratified. Run the gates and report what
they say. Restate the researcher's own answers back to them. List what remains
unresolved. Draft the visible-and-invisible statement for them to correct. Mark
anything produced this way in the decision record, so it stays clear later which
parts were authored and which were assembled.

## Calibrating the Depth

Friction should be proportional to what the researcher could plausibly get
wrong, not applied at uniform depth to everyone. Ask once, at the start, as a
single-select question with these two options and no others:

| Option | Description to offer |
|---|---|
| Full pass | Every stage completes before the next begins. Best for a first instrument, an unfamiliar artifact type, or a build you know is underspecified |
| Advisory pass | I raise what applies and you direct. The sort is still a hard gate; the rest of the ceremony is skipped |

Phrase the question itself as: "Do you want a full pass, where I stop at each
decision, or an advisory pass, where I raise what I see and you take what is
useful?"

**Full pass.** For a first instrument, an unfamiliar artifact type, or a build
the researcher knows is underspecified. Every stage completes before the next
begins.

**Advisory pass.** For someone who has built before and has the shape in hand.
Raise what applies and let them direct. The questions are the same. The gating
is not.

**The sort is a hard gate in both.** Advisory skips ceremony, not the
classification, because misclassifying a step is the failure this whole practice
exists to prevent. Record the mode in the decision record, and record what the
mode did not ask, so a lighter pass leaves a trace rather than a silence.

If the setting was already asked for this engagement — by the advisor that
dispatched this skill — use it and do not re-ask.

Default to asking. Do not infer the setting from how confident someone sounds.

## Sorting the Steps

Decompose what the instrument will do into steps, then classify each one. Some
steps a rule can settle. Some no rule can settle, because they turn on context
that cannot be specified in advance.

Suppose the artifact is a skill for visual anthropology. Some steps a rule can
settle:

- the folder name must match the skill name
- reference files go one level down
- the test suite either passes or it does not

Hand those to the machine.

Some steps no rule can settle:

- whether the content is specific to the discipline, or could appear unchanged
  in any methods textbook
- which trigger phrases belong to this skill rather than to a neighbouring one

The test suite can report that two descriptions have collided. It cannot report
which of them should own the phrase. That decision is the researcher's, and the
instrument should stop and ask rather than choose.

**The classification is a hypothesis, not a partition.** It gets tested by
running the thing. When a step classified as rule-following turns out to have
required judgment, the correction updates the sort and not only the code. A
practice that cannot revise its own classification after the fact is a handoff
rather than a loop.

**A step that is neither cleanly one nor the other is treated as
judgment-dependent.** A checkpoint retained unnecessarily costs time. One
removed wrongly costs the credibility of everything downstream of it.

## Workflow

Ten stages. Three of them are gates that stop for the researcher, and two fire
only under stated conditions.

Read [references/elicitation-guide.md](references/elicitation-guide.md) before
Stage 2, and work from it rather than from memory of it.

**Stage 0. State the outcome, not the solution.** What should become possible
that is not possible now, described as an observable change. A researcher who
opens with a proposed implementation gets redirected to the outcome it implies.

**Stage 1. Frame the artifact.** Which kind of thing is being built, and which
conventions govern it. This version supports skills and agents, and
MCP tools and servers. For skills and agents
read [references/profile-skills-agents.md](references/profile-skills-agents.md)
for its conventions, its checks, and the reading-check anchors a specification can
name. If a language model will run inside the finished
instrument, say so now, because that changes what the instrument can be trusted
to report about itself.

**Stage 2. Sort the steps. Gate.** As above. The researcher classifies. This
skill may propose a classification and may not settle one.

Put it to them as a table of the decomposed steps with a proposed classification
and a reason for each, then ask one single-select question: whether the
classification is right as proposed, or whether a step needs moving. Do not ask
step by step; a decomposition of nine steps becomes nine questions and the
researcher stops reading. Do not offer "you decide" as an option, because that is
the one answer this gate exists to refuse.

**Stage 3. Elicit the specification.** One high-leverage question at a time,
covering the outcome, what is in and out of scope, the constraints, prior
decisions the artifact must respect, and what would count as correct.

**Stage 3a. Categories and what they leave out.** Fires only if the artifact
defines, stores, or assigns categories. What the categories are, what falls
outside them, whose activity becomes invisible by not being represented, and
what the residual bucket is absorbing. Silent otherwise, because asking this of
an artifact with no categories is noise.

**Stage 3b. Ethical constraints.** Fires only if the artifact reads data about
people or sends any data off the machine. Consent scope, what may leave, what
must be de-identified, and who holds authority over the material. These re-fire
whenever the artifact's behaviour changes, because a later addition can reopen a
question an earlier approval had settled.

**Stage 4. Declare what would count as correct.** Either correctness is decidable
against something outside the artifact, or it depends on reading. The second kind
may not claim to pass or fail. Read
[references/verification-modes.md](references/verification-modes.md) before
settling this, and where an artifact has steps of both kinds, declare it by its
weakest step.

**Stage 5. Check that the specification was read, then ratify. Gate.** A
specification that could have been written without looking at the researcher's
actual materials has not been written for them. No code exists before this.

Show the outcome, the scope-out list, and the sort, on one screen. Then ask one
single-select question with exactly these options: ratify and begin, or revise
first and say what. Not a document review, and not a request for approval of
something they cannot see.

**Stage 6. Implement from the specification.** Working from the ratified
specification rather than from the conversation that produced it. For
record-checkable steps, the acceptance checks are written first, from the
specification, and each is seen to fail before implementation begins; the
checks then freeze, and any change to one during implementation is a
specification change that returns to the researcher. This is the builder's
work, done unasked: tell the researcher in one sentence what the checks are
and why they run red first, record the red run in the decision record, and
ask nothing of them — a researcher who has never heard of test-first
development is exactly who the discipline protects. When implementation
cannot reach green within a few attempts, stop — the specification and the
checks disagree, or the sort misclassified a step, and either finding is
the researcher's to rule on.

**Stage 7. Verify, and reclassify. Gate.** Check the artifact against its
conventions and its stated criteria — including that the suite has been made
to fail on purpose at least once per guarded thing, because a green suite
that was never red is evidence about nothing. Any finding that requires
deciding what the artifact should do stops and asks. Later additions to a
shipped instrument re-enter the same order: new behavior gets its failing
check before its code. Where output diverges from what the researcher
expected, ask what they had assumed and not stated, and record it only where the
answer is something they did not already believe. Where a step behaved as
judgment-dependent, correct the sort.

**Stage 8. Close the record.** Draft the statement of what the instrument makes
visible and what it makes invisible, for the researcher to correct. Finish the
decision record, including what the artifact returned rather than what was
expected of it, because the gap between those two is the only part that
constitutes learning.

## Failure Modes

**Everything classified as rule-following.** The fastest route through Stage 2 is
to call every step mechanical, and it is the most expensive mistake available.
Require a stated reason for each judgment-dependent step, and challenge a
classification that finds none rather than accepting it.

**The gate that becomes a form.** Researchers learn which answers let a stage
proceed. Expect it. An advisory pass that records what it skipped is more useful
than a gate that is quietly routed around, because the record of what people skip
says more about where friction belongs than a record of compliance does.

**Reciting rather than reading.** A specification can be fluent, well-formed, and
never have touched the researcher's actual repository, data, or constraints.
Named files that do not exist and commands the project cannot run are the visible
symptoms. The subtler cases are not detectable, which is a limit of this practice
rather than a solved problem.

**Friction added to look rigorous.** The claim is placement, not quantity. Three
stops in the right places beat fifteen, and a tool made deliberately tedious is a
worse tool without being a more careful one. Logistics should be smooth;
installing, invoking, and re-running are not where judgment lives.

**The green suite that was never red.** A check that has never been seen to
fail proves nothing, and a suite can stay green over a broken artifact when a
check quietly guards nothing. Write checks before code and run them red once;
before trusting a finished suite, break each guarded thing deliberately and
watch its check fire. A model that writes the implementation and its checks in
one pass has graded its own work, and the grade is not evidence.
