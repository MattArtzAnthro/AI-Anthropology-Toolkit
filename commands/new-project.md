---
name: new-project
description: Scaffold a new anthropological research project by guiding the user through each phase of the research lifecycle
allowed-tools:
  - Skill
  - Read
  - Write
  - Grep
  - Glob
  - AskUserQuestion
  - TodoWrite
argument-hint: "[project name or research topic]"
---

# New Anthropological Research Project

Guide the user through scaffolding a new anthropological research project. Work through each phase sequentially, creating starter documents that the user can develop further.

## Setup

1. Ask the user for their project name or research topic (if not provided as an argument).
2. Ask where the project should live (parent directory). Default to the current working directory if the user has no preference.
3. Ask about their career stage (undergraduate, MA, PhD, postdoc, faculty) and institutional context.
4. Check whether the project directory already exists (use Glob). If it already exists, ask whether to resume it — creating only the missing phase documents — or to pick a different name. Never overwrite an existing phase document without explicit confirmation.
5. Create the project directory.
6. Create a TodoWrite checklist tracking progress through the phases below.

## Phase 1: Research Question

Use the research-question skill's five-slot grammar to help the user formulate:
- A governing research question
- 2-4 subsidiary questions

Ask about their epistemic stance (interpretivist, critical, STS, feminist, applied, etc.) early — it shapes everything downstream.

Save output to `[project]/01-research-questions.md`.

## Phase 2: Methodology Selection

Use the methodology-selection skill to:
- Define the claim envelope for their research question
- Decompose evidence needs
- Check method-stance compatibility
- Recommend a method composition (single or multi-method)

Save output to `[project]/02-methodology.md`.

## Phase 3: Research Plan

Use the research-plan skill to draft a research plan outline covering:
- Problem statement and significance
- Research context and site description
- Methods and analysis strategy
- Reflexivity and trustworthiness
- Ethics considerations
- Feasibility and timeline

Save output to `[project]/03-research-plan.md`.

## Phase 4: Ethics Planning

Use the irb-protocol and informed-consent skills to:
- Identify key ethical considerations for their research
- Recommend consent mode (written, verbal, layered, community-based)
- Outline data security requirements
- Flag any vulnerable population considerations

Save output to `[project]/04-ethics-plan.md`.

## Phase 5: Fieldwork Instruments

Use the fieldwork-methods skill to create initial drafts of:
- Interview guide skeleton (if using interviews)
- Observation protocol outline (if using observation)
- Data management plan outline

Save output to `[project]/05-fieldwork-instruments.md`.

## Phase 6: Analysis Planning

Use the qualitative-analysis skill to outline:
- Coding approach (deductive, inductive, or hybrid) and its rationale
- Codebook development plan (sources, lens or lenses, size cap)
- Thematic analysis and validation plan
- Tooling mode (conversational, toolkit notebooks, or QDA software)

Save output to `[project]/06-analysis-plan.md`.

## Later-Lifecycle Phases (optional)

After Phase 6, ask which of the following phases to scaffold now. Create
files only for the phases the user selects; note skipped phases as future
steps in the completion summary.

### Phase 7: Funding

Use the grant-proposal skill (and the dissertation-prospectus skill for
doctoral projects) to outline candidate funders, deadlines, eligibility
notes, and a proposal development sequence. Save output to
`[project]/07-funding-plan.md`.

### Phase 8: Writing & Review

Use the research-writing skill to outline target venues and an article or
chapter plan, and the academic-review skill to sketch the expected
review-and-revision cycle. Save output to `[project]/08-writing-plan.md`.

### Phase 9: Dissemination

Use the conference-materials skill (conference targets, abstract deadlines)
and the public-engagement skill (public writing, community-facing outputs)
to outline a dissemination plan. Save output to
`[project]/09-dissemination-plan.md`.

### Phase 10: Teaching & Career Materials

Use the teaching-materials skill for courses or workshops arising from the
project, and the job-materials and career-statements skills to note how the
project will feed CVs, research statements, and application narratives. Save
output to `[project]/10-career-materials.md`.

## Completion

After the core phases (1-6) and any selected later phases, present the user
with:
- A summary of what was created
- The project directory listing
- Suggested next steps, including any later-lifecycle phases they skipped

## Guidelines

- Invoke each phase's skill explicitly with the Skill tool (e.g., `ai-anthropology:research-question`) before drafting that phase's document — do not work from memory of the skill's contents
- Use AskUserQuestion for genuinely closed choices (career stage, consent mode, epistemic stance); gather free-text input (project name, topic, research questions) through plain conversation
- Do not skip phases — walk through each one, even briefly
- Each output file should be a working draft, not just an outline
- Adapt depth to the user's needs — a faculty member may need less scaffolding than a first-year PhD student
- Cross-reference between phases — methods should align with questions, ethics should address methods
