---
name: build-tool
description: Build a research instrument by specifying it first, sorting which steps require judgment, and keeping a decision record
allowed-tools:
  - Skill
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Bash
  - AskUserQuestion
  - TodoWrite
argument-hint: "[what you want the instrument to make possible]"
---

# Build a Research Instrument

Invoke the `tool-building` skill, then dispatch the `tool-builder` agent to run
the build. Work from the loaded skill rather than from this file.

## Before starting, tell the user the shape

State these four things plainly, so nothing arrives as a surprise partway
through.

1. **No code gets written until you have ratified a specification.** That is
   deliberate. The specification is what makes the instrument yours rather than
   the model's.
2. **You will be asked to sort the steps** into those a rule can settle and those
   that need your judgment. You decide; this proposes.
3. **The work stops and asks** at any point where what the instrument should do
   has to be decided. Those stops are the product rather than a delay.
4. **You will get a decision record** alongside the instrument, in a form that can
   go into a methods section.

## Ask how deep to go

Ask once, before anything else, as a single-select question with exactly two
options and no others:

| Option | Description to offer |
|---|---|
| Full pass | Every stage completes before the next begins. Best for a first instrument, an unfamiliar artifact type, or a build you know is underspecified |
| Advisory pass | I raise what applies and you direct. The sort is still a hard gate; the rest of the ceremony is skipped |

Phrase the question as: "Do you want a full pass, where I stop at each decision,
or an advisory pass, where I raise what I see and you take what is useful?"

An advisory pass skips the ceremony. It does not skip the sort, and it records
what it did not ask, so a lighter pass leaves a trace rather than a silence.
This block echoes the depth-calibration element of the Friction by Design
conventions in `skills/DESIGN.md`; that file carries the canonical form.

## Ask where things go

Ask where the instrument, its specification, and its decision record should be
written. Do not assume the current directory, and do not create directories
outside what the user names.

## Then hand over

Dispatch `tool-builder` with the outcome the user stated, the depth they chose,
and the location they named. If the user opened with a proposed implementation
rather than an outcome, redirect once before dispatching: ask what would become
possible that is not possible now.

If the request is not a build at all, route it rather than forcing it through
this command. Designing an interview guide or an observation protocol belongs to
the `fieldwork-methods` skill. Selecting a computational or digital approach
belongs to the `digital-computational-methods` skill. Running a codebook or a
coding pass belongs to the `qualitative-analysis` skill. Working out what a paper
argues belongs to the `paper-planning` skill.
