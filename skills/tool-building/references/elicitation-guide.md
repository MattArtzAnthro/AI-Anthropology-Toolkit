# Elicitation Guide

The question bank, the sort procedure, and the conditions under which the two
conditional passes fire. Load this before Stage 2 and work from it rather than
from memory.

## The protocol

**One high-leverage question at a time.** Batching is what turns elicitation into
a form to fill in, and a form produces answers rather than decisions.

**Do not ask what is already inferable.** If the answer is in the repository, the
data, or something the researcher already said, read it instead of asking. A
question whose answer was available is a small tax on trust, and it accumulates.

**When two implementations would produce the same observable behaviour, ask about
the behaviour first.** Implementation questions asked early get answered with
whatever the researcher has heard of.

**Every five questions, restate.** What has been decided, what remains unknown,
what would count as correct so far, and what the risks would be of building it as
it currently stands. This is where a researcher discovers that the thing they
described is not the thing they want.

**Stop when no critical ambiguity remains for a first pass.** Not when the
questions run out. An unresolved list is a normal output; a specification with
nothing unresolved has usually been tidied rather than finished.

## The sort procedure

Decompose what the instrument will do into steps small enough that each one is a
single decision or a single operation. Then, for each:

1. Ask whether a rule could settle it, stated precisely enough that a person
   following the rule and a machine following the rule would reach the same
   answer.
2. If yes, it is a candidate for automation.
3. If no, it stays with the researcher and becomes a checkpoint inside the
   finished instrument.

**Require a stated reason for every judgment-dependent step.** Not a category
label, a reason: what varies case to case, and what a rule would have to know in
order to settle it. A step nobody can give a reason for is usually
rule-following and was misfiled out of caution.

**Challenge an all-rule-following classification rather than accepting it.** If
every step of an instrument that touches research material can be settled by
rule, either the instrument is doing something trivial or a judgment has been
overlooked. Ask which step the researcher would want to check by hand on the
first run, and why. That question usually finds it.

**Treat the classification as provisional.** Say so at the time. It will be
revised at Stage 7 by what the running artifact turns out to do, and a researcher
who was told the sort was final will read that revision as a failure rather than
as the mechanism working.

**Residual steps default to judgment-dependent.** Where a step is neither cleanly
one nor the other, keep the checkpoint. The asymmetry is the reason: a checkpoint
retained unnecessarily costs a little time, and one removed wrongly costs the
credibility of every result downstream of it.

## Questions for the specification

Ordered so that the load-bearing items come first.

**Outcome.** What becomes possible that is not possible now? What would you be
able to see, find, or do that you cannot today? If the instrument worked
perfectly and you told a colleague what it does, what would you say?

**Scope.** What is included? What is deliberately excluded? What would you refuse
to let it decide, even if it could?

**Constraints.** What must it not do? What has to stay on this machine? What
existing conventions does it have to respect? What would make you throw the
result away?

**Prior decisions.** What has already been settled that this cannot revisit?
Which existing conventions govern this kind of artifact, and which specific rule
in them matters most here?

**What would count as correct.** How would you know it worked? What would you
check first? If a colleague doubted the output, what would you show them?

**Failure.** What should happen when it cannot do the thing? What is the worst
plausible wrong answer, and would you notice it?

## Stage 3a: categories and what they leave out

**Fires if and only if** the artifact defines, stores, assigns, or counts
categories. If it does not, skip this and say nothing; asking about categories of
an artifact with none is noise, and noise spends attention that the real
questions need.

When it fires:

- What are the categories, stated as a list rather than as a principle?
- What falls outside all of them?
- Where does the residual go, and who looks at it?
- Whose activity becomes invisible by not having a category?
- If someone worked in a way none of these describes, what would happen to them?

The last question is the one that most often changes a data model. Every
classification produces residuals, and enlarging the list does not eliminate
them, so the useful outcome is not a longer list but a decision about what the
residual is for and who is responsible for reading it.

## Stage 3b: ethical constraints

**Fires if and only if** the artifact reads data about people, or sends any data
off this machine. Either condition is sufficient.

When it fires:

- What were participants told this material would be used for?
- Does that cover what this instrument will do with it?
- What may leave this machine, and what may not?
- What must be removed or altered before anything is stored or exported?
- Who holds authority over this material besides you, and do they need to be
  asked?
- If the instrument later sent data somewhere it does not now, would that reopen
  any of the above?

**These re-fire.** Whenever the artifact's behaviour changes, ask the last
question again. An approval covers what was described when it was given, and an
addition that sends data somewhere new is not covered by it. Record each firing
in the decision record, including the ones that changed nothing, because a
constraint that was checked and held is evidence and a constraint that was never
rechecked is not.

## Recording what came back

At Stage 7, when output diverges from what the researcher expected, ask what they
had assumed and had not stated. Then apply one test before recording it:

**Record it only if the answer is something they did not already believe.**

A researcher who is surprised and then says "yes, that is what I thought would
happen" has confirmed an expectation, which is worth knowing and is not a
finding. A researcher who says "I had not realized I was assuming that" has
learned something from the artifact, and that is the only kind of entry worth
keeping. Without this test the record fills with confirmations and stops being
evidence of anything.
