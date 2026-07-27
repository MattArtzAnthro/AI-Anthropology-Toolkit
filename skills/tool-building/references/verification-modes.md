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
