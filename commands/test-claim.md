---
name: test-claim
description: Test one interpretive claim against rival readings argued from other analytical positions, and record what stays open
allowed-tools:
  - Skill
  - Read
  - Grep
  - Glob
  - AskUserQuestion
  - TodoWrite
argument-hint: "[path to the material, or the claim you want tested]"
---

# Test a Claim Against Rival Readings

Invoke the `rival-interpretations` skill and work from the loaded skill rather
than from this file.

## Run the gate before promising anything

This command does not guarantee a test. The skill's gate runs first, and
declining is its common outcome. Do not tell the user what will happen until
the gate has run.

The four conditions are in the skill. All four must hold:

1. It is a reading, not a fact
2. It is load-bearing
3. The positions would diverge
4. The researcher has committed to the reading

## When the gate declines

Say which condition failed, name the rival reading in a sentence anyway, and
route. Prose and craft belong to the `research-writing` skill. An argument
that has not formed belongs to the `paper-planning` skill. A method question
belongs to the `methodology-selection` skill. Answering an actual reviewer
belongs to the `academic-review` skill.

A declined gate is a result, not a failure to deliver. Report it as one.

## When the gate passes, tell the user the shape

State these plainly before running, so nothing arrives as a surprise.

1. **One claim gets tested, not the document.** The other contestable claims
   are listed and left alone.
2. **You confirm the claim before anything runs.** Testing the wrong claim
   well is worse than declining, because it arrives looking like a result.
3. **Three positions read in isolation** and never see each other's readings,
   which is why the divergence means something.
4. **A reading that cannot say what would falsify it is not admitted.** A
   position with nothing at stake here drops out, and the record says which
   and why.
5. **What stays open is handed to you unresolved.** The output separates
   defects, which carry evidence, from decisions, which are yours.
6. **You will get a record** in a form that can go into a methods section,
   and it is not finished until your resolution is in it.

## Ask how deep to go

Ask once, as a single-select question with exactly two options:

| Option | Description to offer |
|---|---|
| Full pass | Stop at the claim under test, and again at what stays open. Best for a first article or a reading you have not argued in public before |
| Advisory pass | Confirm the claim in one exchange, run, and report. Best when you arrive with the claim already stated sharply |

The ratification gate holds under both. An advisory pass calibrates how much
is discussed, not whether you get to say what your own claim is.

If an advisor already asked the depth setting for this engagement, use it and
do not re-ask.

## Ask where the record goes

Ask where the record should be written. Do not assume the current directory,
and do not create directories outside what the user names.
