# The Commitments a Specification Leaves Open

A specification that says "collect the case files" has not said what should
happen when the archive returns nothing, when two files carry the same
identifier, when a field is present in most records and absent in the rest,
or when a date will not parse.

Those are not edge cases. Each one is a commitment the researcher is already
making, whichever way the code happens to go, and it will govern their data
whether or not anyone decided it. Left unsurfaced, the instrument's first
implementer settles them by accident and the researcher inherits the
settlement without ever seeing the choice.

Surfacing them is Stage 4's work, because they are what would count as
correct.

## Why Stage 4 and not later

The acceptance checks are authored by the ratified specification, and they
freeze at ratification. A commitment settled after that is a change to the
specification, and it returns to the researcher as one.

So a commitment discovered while writing the checks arrived too late. If
these decisions are load-bearing enough to need settling — and they are, they
decide what the data means — then a specification ratified without them was
ratified incomplete.

**Stage 6 asks the researcher nothing, and that does not change.** Checks get
written for them, run red, and reported in one sentence. Anything that
surfaces only during implementation returns through the Stage 7 gate as a
specification change, which is the route that already exists.

## State the commitment, not the question

A question surfaces nothing. "What should this return when the source returns
nothing?" carries no claim about the researcher, so there is nothing for them
to recognize and nothing for them to refute. It is a gap report, and it puts
the work of noticing back on the person who did not notice.

State instead what the specification currently commits them to:

> As written, this treats an empty result as a failure rather than as a fact
> about the archive. Is that yours?

That can be wrong. Being told it is wrong is the point: a reconstruction the
researcher rejects has surfaced a commitment neither of you had stated, which
is what a question could not do. Where it is right, they have seen a decision
they were making silently.

Reconstruct from the specification, never from what would be convenient to
implement.

## The recurring five

Most instruments that read a source leave the same commitments open. Work
through these before looking for others:

| Commitment | The two readings |
|---|---|
| **Emptiness** | An empty result is a failure of the instrument, or a fact about the source worth recording |
| **Duplication** | Two records with one identifier are an error to reject, or a real duplicate in the archive to preserve |
| **Partial presence** | A field absent from some records is optional, or required and therefore a signal the source changed |
| **Unparseable values** | A date that will not parse means skip the record, keep it with the value null, or stop and report |
| **Ordering** | Source order carries meaning and must be preserved, or is incidental and may be sorted |

For an instrument that categorises, assigns, or counts, Stage 3a is already
asking the harder version of this and these do not replace it.

## The form

**One table, one question.** Every row carries the reconstructed commitment,
a proposed answer, and the reason for the proposal. Then a single
confirm-or-revise question over the whole table.

Not row by row. Batching facts is efficient and batching decisions is a form,
but a classification presented as one table with one question is neither —
it is the shape Stage 2's sort gate already uses, and it works for the same
reason: the researcher reads a whole picture and rules on it once.

Mark each row:

- **mirror** — the specification already settles this and the row restates
  it. Necessary to show, and it will teach nobody anything.
- **surprise-capable** — the specification does not settle it, and the row
  states what the instrument would do by default. Each of these carries a
  stated hypothesis about which unstated commitment a rejection would reveal.

A table of nothing but mirrors means the specification was more complete than
expected. Say so plainly rather than manufacturing rows to fill it.

## What the answers become

They enter the specification before it is ratified, which is the whole point
of placing this at Stage 4. The acceptance checks are then authored from a
specification that settles them, and the record shows which behaviors were
decided rather than inherited.

Record the rejected reconstructions too. A reconstruction the researcher
turned down is the most informative thing on the table: it marks a place
where the obvious reading of their specification was not their reading, and
that gap is worth more to a methods appendix than the answers that were
guessed correctly.

## Scope and limits

**This reaches record-checkable steps.** For a step whose correctness depends
on reading, a commitment about what the instrument should do is still worth
surfacing, but it may not become a check that claims to pass or fail. Those
steps get adjudication samples and disconfirming cases, chosen before the
artifact exists.

**Declare the artifact's mode alongside the table.** A researcher looking at
a settled list of behaviors can easily read it as a settled instrument. Where
the artifact is interpretation-dependent, say which steps the table does not
reach.

**Every artifact family is in scope, including notebooks.** A table of
commitments needs no filesystem, no runner, and no persistence between
sessions, so it reaches surfaces that execution-based verification cannot.

**This is not a completeness claim.** The five above are the ones that recur,
not the ones that exist. An instrument can carry a commitment none of them
names, and a table that found nothing beyond the five has probably not looked
at the researcher's actual source.
