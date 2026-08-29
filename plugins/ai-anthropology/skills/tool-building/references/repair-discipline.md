# When the Instrument Breaks

An instrument that fails after it shipped re-enters the same discipline it was
built under, through a different door. The specification still governs, the
sort can still be wrong, and the checks still freeze — what changes is the
pressure. A construction failure arrives at a desk; a repair failure arrives
mid-project, with collected data at stake and a researcher who wants the
fastest possible patch. That pressure is exactly why repair has its own
discipline rather than an exemption from the one that exists.

The reproduction-first rule below is inherited from software engineering
practice, where automated repair systems require a fail-to-pass reproduction
test before any patch; this skill restates it in research terms and does not
rename it.

## Reproduce Before Repairing

The first artifact of any repair is a reproduction check: a check that fails
on the broken instrument, for the reason the researcher observed, and will
pass when the defect is fixed. No patch is written before it exists and has
been seen to fail. This is the red-run discipline of Stage 6, re-entered:
a repair without a reproduction is a patch that fixed the failure in
someone's head, verified against nothing.

The reproduction is the builder's work, done unasked, and it earns its keep
twice: it proves the fix when it flips to passing, and it joins the suite
afterward so the same defect cannot return silently.

## The Triage: Fail for the Right Reason

Run the candidate reproduction against the broken instrument and read *why*
it fails. The outcome sorts the whole repair, and the three branches lead
three different places:

**It fails with an assertion naming the observed behavior.** The instrument
has a defect. Proceed to the repair loop below.

**It fails with a setup, import, or environment error.** The instrument may
not be broken at all — the environment around it changed: a dependency
updated, a credential expired, a path moved. Repair the environment first
and re-run. Patching instrument code to accommodate a broken environment
"fixes" code that was never wrong, and the fix becomes a defect the day the
environment is restored.

**It passes on the supposedly broken instrument.** Stop. The failure is
intermittent, environmental, or misdiagnosed — and one of these is a finding.
Ask what the researcher actually observed, exactly, before anything else
happens. The most common resolution for fieldwork instruments is that **the
world changed, not the code**: the archive redesigned its pages, the platform
changed its API, the source moved. That is not a defect to patch around; it
is a specification question — does the specification still describe the
source? — and it returns to the researcher as one, because deciding what the
instrument should now do about a changed world is theirs.

## The Repair Loop: Refine or Pivot

With a verified reproduction in hand, patch and re-run. Two states, and the
difference between them is what the last failure said:

**Refine** when the reproduction's failure changed — the patch moved
something, and a smaller correction on top of it is warranted. Keep the
working parts, adjust locally.

**Pivot** when the same failure appears twice. An identical failure means the
hypothesis behind the patch is wrong, not underdeveloped. Discard the patch
entirely, revert to the pre-repair state, write the dead hypothesis into the
decision record — what was believed, what the run showed — and take a
different approach. Iterating on a refuted hypothesis is how a repair session
accretes the complexity the specification existed to prevent.

Bound the loop. Three failed hypotheses is the default budget, and exhausting
it is a finding, not an embarrassment: repeated failure is evidence that the
specification and the instrument's reality have diverged, or that the sort
misclassified a step as rule-following that turns out to require judgment.
Either way the question goes back to the researcher, per Stage 7's rule that
any finding requiring a decision about what the artifact should do stops and
asks.

## The Checks Stay Locked

Everything the specification's verification section says about frozen checks
holds during repair with more force, not less, because repair is where the
pressure to bend a check peaks. No check is weakened, deleted, or rewritten
to let a patch pass. Wanting a check to be different is legitimate and
common — sources drift, tolerances prove wrong — but it is a specification
change, decided explicitly by the researcher at the specification level and
recorded, never made by the party writing the patch in order to succeed. The
one writing the fix is never also the one redefining correct.

## Every Repaired Defect Earns Its Rule

Close each repair in the decision record with four entries: what failed, what
the reproduction was, what fixed it, and — the part that compounds — whether
the defect could recur in a different instrument. Where the answer is yes,
state the class-level rule in one line, as a constraint the next
specification should carry ("timeouts on every network call," "never parse
dates without a stated timezone," "page structure is an assumption, record
it"). Label the entry as recognized retrospectively, since repair rules are
learned from failure rather than designed in advance.

Rules accumulate across a researcher's instruments through the decision
records, and a rule that appears twice is a candidate for the prior-decisions
field of the next spec pack — which is the mechanism by which a researcher's
instruments stop repeating each other's defects without anyone's memory being
relied on.

## What a Repair May Claim

A green reproduction licenses exactly one sentence: the observed failure no
longer occurs. It does not re-validate the instrument, it does not extend to
behaviors no check guards, and for interpretation-dependent steps the mode's
prohibition on pass and fail claims stands untouched. A repaired instrument
is a working instrument with one more known-and-guarded defect class — that
is the honest description, and it is the one the decision record supports.
