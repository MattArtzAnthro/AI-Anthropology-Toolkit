---
name: new-project
description: Scaffold a new anthropological research project by guiding the user through each phase of the research lifecycle
allowed-tools:
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
2. Ask about their career stage (undergraduate, MA, PhD, postdoc, faculty) and institutional context.
3. Create a project directory with the project name.
4. Create a TodoWrite checklist tracking progress through the phases below.

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

## Completion

After all phases, present the user with:
- A summary of what was created
- The project directory listing
- Suggested next steps (e.g., "develop your research plan into a full grant proposal using the grant-proposal skill")

## Guidelines

- Use AskUserQuestion at each phase to gather key decisions from the user
- Do not skip phases — walk through each one, even briefly
- Each output file should be a working draft, not just an outline
- Adapt depth to the user's needs — a faculty member may need less scaffolding than a first-year PhD student
- Cross-reference between phases — methods should align with questions, ethics should address methods
