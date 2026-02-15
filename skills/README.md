# Anthropology Skills Library

A library of `SKILL.md` files that enable LLMs and agents to support anthropological research across the full research lifecycle — from question formulation through dissemination, teaching, and professional development.

## Architecture

Each skill is a self-contained folder with a `SKILL.md` router and optional `references/` files for domain-specific depth. Skills use progressive disclosure: only the relevant SKILL.md and its reference files load when triggered, keeping context window costs manageable.

For the full architectural rationale and shared parameter framework, see [DESIGN.md](DESIGN.md).

## Skills

| # | Skill | Folder | Status | Description |
|---|-------|--------|--------|-------------|
| 1 | [Research Design & Planning](https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/tree/main/skills/research-design-planning) | `research-design/` | In Process | Research questions, proposals, grants, methodology selection |
| 2 | Ethics, Consent & Governance | `ethics-consent/` | In Process | IRB protocols, consent documents, community agreements |
| 3 | Fieldwork Instruments & Protocols | `fieldwork-instruments/` | In Process | Interview guides, focus groups, surveys, observation protocols, codebooks |
| 4 | Academic Paper Writing & Revision | `academic-paper/` | In Process | Paper sections, ethnographic voice, reviewer responses, journal conventions |
| 5 | Peer Review | `peer-review/` | In Process | Constructive peer reviews for anthropology journals |
| 6 | Conference Abstracts & Presentations | `conference-presentations/` | In Process | Abstracts, slides, posters, speaker notes |
| 7 | Public Engagement & Communication | `public-engagement/` | In Process | Blog posts, op-eds, media prep, community summaries, policy briefs |
| 8 | Academic Career & Teaching | `academic-career/` | In Process | Syllabi, teaching materials, tenure portfolios, statements |
