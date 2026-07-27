# The Spec Pack

Two files, not four. `SPEC.md` carries the specification, with acceptance
examples and checks as sections rather than separate documents. `DECISIONS.md`
carries the record, which is not part of the specification and outlives it.

Ceremony is what stops a protocol being used. A researcher building a scraper for
one archive should not be asked to produce four documents before any code exists.

## Every engineering term, in research terms

The specification has to be legible to two readers at once, the researcher and
the machine. These are not simplifications; each names a practice researchers
already perform rigorously under a different word.

| Engineering term | What it is in research terms |
|---|---|
| Scope out | Exclusion criteria |
| Acceptance examples | What a research assistant would need in order to know they did it right |
| Verification | Inter-coder reliability, member checking, spot-checking against the source |
| Constraints | Protocol conditions and ethical non-negotiables |
| Prior decisions | What the study has already settled and will not revisit |
| Decision log | Audit trail |
| Spec drift | Protocol deviation |

Use the research term when speaking to the researcher and keep the engineering
term in the file, so the artifact stays readable by both.

---

## SPEC.md

Ten sections, in this order. The order is not cosmetic: the first five settle
what the instrument is for, and a researcher who cannot fill them has not yet
decided what they are building.

Two sections carry rules that get checked mechanically before the specification
can be ratified, and the template says so where they appear.

```markdown
# [What the instrument is called]

## Outcome
What becomes possible that is not possible now, as an observable change. Not a
description of the mechanism.

## Scope in
The behaviour that is included.

## Scope out
What is excluded, deferred, or forbidden. Every step classified as
judgment-dependent belongs here, named, with the judgment left to a person.

## Constraints
What must not happen. What stays on this machine. Performance or compatibility
limits. Ethical non-negotiables, including consent scope where the material
concerns people.

## Prior decisions
What the study or the repository has already settled that this cannot revisit.
CHECKED: quote at least one specific convention from the governing document
rather than referring to it in general. A specification that cites conventions it
never read is recitation.

## Likely files and interfaces
CHECKED: name real paths, in backticks. Paths that do not exist are the clearest
sign a specification was written without opening the project.

## Verification mode
Exactly one of:
  record-checkable            correctness is decidable against something
                              outside the artifact
  interpretation-dependent    correctness depends on reading

## Verification
CHECKED: exact commands, in backticks, that this project can actually run.
- 
- 

## Acceptance examples
Declarative. Given / When / Then.
For an interpretation-dependent artifact these are adjudication samples and
disconfirming cases, and they may not claim to pass or fail.
- Given ...
  When ...
  Then ...

## Open questions
Only what materially affects design or correctness. An empty list after a full
pass usually means the specification was tidied rather than finished. Mark
anything that blocks implementation as critical, which stops ratification.
```

---

## DECISIONS.md

The record. It accretes while the work happens rather than being written up
afterward, because a decision reconstructed from memory months later is the thing
this file exists to prevent.

It is also the artifact that renders into a methods appendix, which is why it is
worth keeping even when the instrument is small.

```markdown
# Decision Record: [instrument]

**Artifact status:** specified | implemented | published | evaluated
**Depth:** full pass | advisory pass
**What the advisory pass did not ask:** [omit if full pass]

## The sort

| Step | Rule can settle it | Reason, required where judgment-dependent |
|---|---|---|

## Decisions at each gate

### Gate 1, the sort
### Gate 2, ratification
### Gate 3, verification findings

## The red run
Every check for a record-checkable step, with its observed first failure,
dated before the implementation that satisfied it. The researcher does not
write these and is not asked to review them; they are told once, plainly,
that the checks exist and why — a check that has never failed proves
nothing, so each is run red before code is written against it. Later
additions to a shipped instrument re-enter here: new behavior, new failing
check first. An empty section on an artifact with record-checkable steps
means the order was not followed, and the record should say so rather than
hide it.

## What the specification got wrong on its first pass
How the error surfaced, and what changed. This section being empty on a first
build is unusual rather than good.

## What the artifact returned
What running it actually produced, as against what was expected of it. The gap
between those two is the only part of this record that constitutes learning.

## Surprises worth keeping
Only where the researcher did not already believe the thing. A confirmed
expectation is worth knowing and is not a finding, and a record that does not
separate them stops being evidence.

## Friction not placed, and why
Where a checkpoint could have gone and deliberately did not. Naming the
unevenness is what makes the account credible; a claim of uniform rigour is
falsifiable by anyone who opens the artifact.

## What this instrument makes visible, and what it makes invisible
Drafted by the tool, corrected by the researcher. This belongs in a methods
section rather than in a comment.

## Assembled rather than authored
Anything produced on request rather than decided by the researcher.
```

## On filling these in

**Do not manufacture entries.** A step that went as planned earns no line. Padding
the sort table or the surprises section to look thorough is the same failure as
adding friction to look rigorous, and it costs the record its evidential value.

**Record what came back, not what was expected.** This is the one instruction that
distinguishes a decision record from a plan restated in the past tense.
