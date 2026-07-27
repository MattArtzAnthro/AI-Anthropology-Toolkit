# What Would Count as Correct

Every specification declares exactly one verification mode, and the mode governs
what the acceptance examples are allowed to claim. Declaring it is not a
formality: it is where a researcher decides whether their instrument can be
checked at all.

## record-checkable

Correctness is decidable against something outside the artifact. A record exists
or it does not. A DOI resolves or it does not. A schema validates or it does not.
A count matches the source or it does not.

Executable acceptance tests are legitimate here and are required. So is a
hand-checked sample, because a test written from the same misunderstanding as the
code will pass.

The worked case is a bibliographic pipeline. Whether an article is present in a
public database is not a matter of interpretation, which is what made the
deduplication error findable: two records existed where one should have, and
comparing output against the source said so plainly.

## interpretation-dependent

Correctness depends on reading. Whether a passage is an instance of a code,
whether a cluster is a theme, whether a description is apt, whether an annotation
is fair.

**Pass and fail claims are forbidden in this mode.** Not discouraged. An
acceptance example that says a thematic grouping "must pass a coherence check"
has asserted that interpretation is decidable, and the specification is making a
claim the artifact cannot support.

What replaces them:

- **Adjudication samples.** A set of cases the researcher reads and rules on
  directly, recorded with their ruling.
- **Disconfirming cases.** Instances chosen because they should not fit, kept to
  see whether the instrument forces them in anyway.
- **A stated divergence expectation.** How much disagreement is normal for this
  material. An instrument that never diverges from the researcher is either
  trivial or has stopped being informative.

**The three-valued verdict.** Confirmed, refuted, or cannot tell. "Cannot tell"
is frequently the honest answer here and must remain available. An instrument that
cannot say it does not know will say something else instead.

## Deciding between them

**If you cannot name the thing outside the artifact that settles correctness, the
mode is interpretation-dependent.**

Uncertainty resolves to interpretation-dependent, never the reverse. The
asymmetry is deliberate: an interpretive artifact wrongly marked record-checkable
will produce confident numbers about something that was never decidable, and
those numbers travel. The reverse error costs a researcher some
executable tests they could have had.

Two things that look like the outside world and are not:

- **A model's judgment.** Asking a second model whether the first was right
  produces agreement, not verification. It is another reading.
- **Your own earlier annotation.** Consistency with what you decided last month
  is reliability, which is worth measuring and is not correctness.

## The order of checks and code

The mode declares what a check may claim. Order declares whether the check
means anything. The rule, for every record-checkable step: **the checks are
written from the ratified specification, before any implementation exists,
and each one is seen to fail once.** A check that has never failed proves
nothing, in the same way an interview guide that was never piloted against a
known case proves nothing about what it can elicit. The failing check is the
executable form of "what would count as correct," and running it red is the
moment the specification stops being prose.

Three failure patterns make the order load-bearing rather than ceremonial:

**The instrument that grades its own work.** A model asked to produce the
implementation and its checks in one pass writes checks that mirror the
code — they verify what the instrument does, not what the specification
requires, the way a codebook validated only by the person who wrote it
confirms its author's reading. The separation that prevents this is not
another model; it is the order. The specification authors the checks, the
researcher ratifies them as part of ratifying the specification, and only
then does implementation begin.

**The check bent to fit.** Under pressure to reach green, a model will
sometimes satisfy the check rather than the requirement: weaken an
assertion, special-case the exact fixture, delete what keeps failing. So
the checks freeze at ratification. **Once implementation starts, any change
to a check is a change to the specification, and it returns to the
researcher as one.** This is not a new gate; it is Gate 3 recognizing that
a redefinition of correct is a decision about what the instrument should
do.

**The green suite that was never red.** A passing suite is evidence about
the instrument only to the extent that the checks have been shown to fire.
Before trusting a suite, break each thing it guards once, deliberately,
and watch the check fail; a check that stays green over a broken artifact
is measuring nothing, and it is invisible until tested exactly this way.
Record the breakage pass in the decision record — it is the difference
between "the checks passed" and "the checks were checked."

Bound the attempts. When implementation cannot reach green within a few
tries, the finding is almost never that more effort is needed; it is that
the specification and the checks disagree, or the step was misclassified in
the sort. Stop, say which, and return to the researcher. A long chase after
green accretes exactly the complexity the specification existed to prevent.

**Whose work this is.** The order discipline is the builder's obligation,
never the researcher's burden. A researcher who has never heard of
test-first development still gets checks written for every record-checkable
step, from the specification they ratified, without asking — because the
proportionality rule cuts both ways: judgment stops for the researcher, and
mechanics run smoothly without them. Tell them once, in a sentence, what is
happening and why ("before writing the code I write the checks that would
catch it being wrong, and run them to see them fail — the way an instrument
gets piloted before it is fielded"). That sentence is a teaching moment,
not a request; the researcher is never asked to write, read, or approve
test code, and the red run is recorded in the decision record where they
and their readers can see it was done. The discipline re-fires for as long
as the instrument lives: every later addition gets its failing check before
its code, whether or not anyone asks.

For interpretation-dependent steps, none of this licenses pass and fail —
the mode's prohibition stands. The order discipline still applies in one
form: **choose the adjudication samples and disconfirming cases before the
artifact exists.** A sample selected after seeing output drifts toward the
cases the instrument handles well, which is the interpretive version of the
check bent to fit.

## What this distinction does not settle

Whether the specify, check, revise discipline holds when the check is
interpretation of ethnographic material rather than agreement with a record is an
open question, and this skill does not close it. The mode declaration manages the
problem by refusing the claims the weaker case cannot support. It does not
establish that the practice works there.

Say so to the researcher when the mode comes out interpretation-dependent. A
researcher who believes their interpretive instrument has been verified is worse
off than one who knows it has been specified and read.

## Mixed artifacts

Most real instruments have both kinds of step. A pipeline that fetches records
and then categorises them is record-checkable at the fetch and
interpretation-dependent at the categorisation.

Declare the mode for the artifact as a whole by its **weakest** step, and note in
the specification which steps are the stronger kind. The reason is that a single
mode governs what the acceptance examples may claim, and one interpretive step is
enough to make a pass/fail claim about the whole artifact false.
