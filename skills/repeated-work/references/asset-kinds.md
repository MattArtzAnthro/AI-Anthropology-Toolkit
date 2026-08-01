# What Kind of Thing to Build

Reached only after all four tests have passed. Asking this earlier turns a
triage into a shopping trip, and a researcher who has picked a kind before
establishing that anything should be built will find reasons for it.

The first question here is not which kind. It is whether the answer is
outside the toolkit entirely, because it usually is.

## Start outside

**An existing utility.** A command line tool, an option in software the
researcher already runs, a package that does this and is maintained by
someone else. Almost always cheaper than anything built, and it keeps
working when the researcher stops maintaining it.

**A plain script.** Thirty lines that run on demand and belong to one
researcher. No packaging, no distribution, no tests beyond a check that it
did the right thing. This is the correct answer far more often than the
toolkit-shaped ones, and it is under-proposed because it is unglamorous.

**A written procedure.** Where the work is stable but the difficulty is
remembering the order, a checklist beats code and cannot break.

Only when none of those fit does the kind question become a toolkit question.

## The toolkit kinds

| Kind | Fits when | Does not fit when |
|---|---|---|
| **Skill** | The repeated thing is a *conversation*: the researcher needs the same questions asked, the same conventions applied, the same judgments surfaced each time. Its output is guidance and structure | The work is computation. A skill that describes an algorithm instead of running it is a worse version of a script |
| **Agent** | Several skills have to be orchestrated across one long engagement, and the phase boundaries are stable | There is only one skill to invoke. An agent wrapping a single skill adds a layer and no capability |
| **MCP server or tool** | Code that has to be callable from inside a conversation, repeatedly, with structured results. Data collection, extraction, parsing, anything with an API | It runs once a month and the researcher is happy to run it themselves. A script is less to maintain |
| **Notebook** | The researcher needs to see and adjust intermediate results, and the review between stages is the point. Long pipelines with human checkpoints | The steps never need inspecting. A notebook that is always run top to bottom is a script with extra ceremony |
| **Command** | A frequently used entry point into work that already exists, where the friction is invocation rather than capability | It would be the only way to reach the capability. Then the capability is the thing to build |

## Two rules that decide most cases

**Conversation or computation.** If the repeated difficulty is knowing what
to ask, what to check, or what convention applies, it is a skill. If the
repeated difficulty is doing something to data, it is code. Work that is
genuinely both is usually two things, and building it as one produces an
artifact that does neither well.

**Who else has this problem.** A thing for one researcher is a script or a
personal skill. A thing for a lab, a cohort, or a field is worth packaging,
and packaging costs several times what the working version cost. That
multiple is the part people underestimate, and it is worth saying out loud
before anyone commits.

## What packaging actually costs

Anyone choosing a toolkit-shaped kind should hear this once, plainly, because
the working version is the small part:

- Tests, and a way to run them
- Documentation that survives the author forgetting how it works
- A decision about what happens when it breaks and the author is in the field
- Versioning, if anyone else depends on it

None of this argues against building. It argues against building the
distributable version first. The usual right sequence is to make the thing
work for one person, use it for a while, and package it only once it has
survived contact with the work.

## Handing over

Once the kind is settled, the tool-building skill takes it from here: the
sort of which steps a rule can settle and which need judgment, the
specification, ratification, and the verification that follows. Carry
forward what this conversation established, because it is most of the
opening material:

- The instances, and what varied between them
- Which steps are mechanical and which need a call each time
- What was already searched and found not to exist
- The kind, and why the alternatives were rejected

A handover that arrives as "they want to build a scraper" throws all of that
away and starts the specification from nothing.
