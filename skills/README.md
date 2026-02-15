# Anthropology Skills Library

A library of `SKILL.md` files that enable LLMs and agents to support anthropological research across the full research lifecycle — from question formulation through dissemination, teaching, and professional development.

## Architecture

Each skill is a self-contained folder with a `SKILL.md` router (under 500 lines) and optional `references/` files for domain-specific depth. Skills use progressive disclosure: only the relevant SKILL.md and its reference files load when triggered, keeping context window costs manageable.

For the full architectural rationale and shared parameter framework, see [DESIGN.md](../DESIGN.md).

## Skills

| # | Skill | Folder | Status | Description |
|---|-------|--------|--------|-------------|
| 1 | Research Design & Planning | `research-design/` | Stub | Research questions, proposals, grants, methodology selection |
| 2 | Ethics, Consent & Governance | `ethics-consent/` | Stub | IRB protocols, consent documents, community agreements |
| 3 | Fieldwork Instruments & Protocols | `fieldwork-instruments/` | Stub | Interview guides, focus groups, surveys, observation protocols, codebooks |
| 4 | Academic Paper Writing & Revision | `academic-paper/` | **Draft** | Paper sections, ethnographic voice, reviewer responses, journal conventions |
| 5 | Peer Review | `peer-review/` | **Draft** | Constructive peer reviews for anthropology journals |
| 6 | Conference Abstracts & Presentations | `conference-presentations/` | Stub | Abstracts, slides, posters, speaker notes |
| 7 | Public Engagement & Communication | `public-engagement/` | Stub | Blog posts, op-eds, media prep, community summaries, policy briefs |
| 8 | Academic Career & Teaching | `academic-career/` | Stub | Syllabi, teaching materials, tenure portfolios, statements |

## Development Phases

- **Phase 1 (next):** `academic-paper/` and `peer-review/` — flagship skill + quick validation
- **Phase 2:** `ethics-consent/`, `fieldwork-instruments/`, `conference-presentations/`
- **Phase 3:** `public-engagement/`, `academic-career/`
- **Phase 4:** Knowledge base, evals, and DESIGN.md

## Relationship to Other Toolkit Components

These skills handle **writing and communication tasks** — where the LLM needs to know how to write something, what the genre expects, and what quality looks like. Computational analysis tasks (coding, thematic analysis, entity extraction, knowledge graphs) are handled by the toolkit's MCP servers and standalone tools.

## Template

See `template/SKILL.md` for the starter template used to create new skills.
