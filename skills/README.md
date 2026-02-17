# Anthropology Skills Library

A library of `SKILL.md` files that enable LLMs and agents to support anthropological research across the full research lifecycle — from question formulation through dissemination, teaching, and professional development.

## Architecture

Each skill is a self-contained folder under `skills/` with a `SKILL.md` file (YAML frontmatter + markdown instructions) and an optional `references/` directory for domain-specific depth. Skills follow the [Agent Skills specification](https://agentskills.io/specification):

- **Metadata** (~100 tokens): `name` and `description` fields loaded at startup for all skills
- **Instructions** (< 5,000 tokens): Full SKILL.md body loaded when the skill activates
- **Resources** (as needed): Reference files in `references/` loaded only when required

The directory name of each skill matches its `name` field. Reference files are one level deep from SKILL.md.

For the full architectural rationale and shared parameter framework, see [DESIGN.md](DESIGN.md).

## Skills

Skills are organized conceptually by research lifecycle phase. Each row is a separate installable skill.

| Phase | Skill | Folder | Status |
|-------|-------|--------|--------|
| Research Design | [Research Question Development](research-question/) | `research-question/` | Available |
| Research Design | [Dissertation Prospectus](dissertation-prospectus/) | `dissertation-prospectus/` | Available |
| Research Design | [Research Plan Writing](research-plan/) | `research-plan/` | Available |
| Research Design | [Methodology Selection](methodology-selection/) | `methodology-selection/` | Available |
| Funding & Proposals | [Grant & Proposal Writing](grant-proposal/) | `grant-proposal/` | Available |
| Ethics & Compliance | [IRB & Ethics Protocols](irb-protocol/) | `irb-protocol/` | Available |
| Ethics & Compliance | [Informed Consent Design](informed-consent/) | `informed-consent/` | Available |
| Data Collection | [Fieldwork Methods & Data Collection](fieldwork-methods/) | `fieldwork-methods/` | Available |
| Writing | [Research Writing](research-writing/) | `research-writing/` | Available |
| Peer Review | [Academic Review & Manuscript Evaluation](academic-review/) | `academic-review/` | Available |
| Conferences & Presentations | [Conference Materials & Presentations](conference-materials/) | `conference-materials/` | Available |
| Public Engagement | [Public Engagement & Communication](public-engagement/) | `public-engagement/` | Available |
| Teaching | [Teaching Materials](teaching-materials/) | `teaching-materials/` | Available |
| Career | [Career Statements](career-statements/) | `career-statements/` | Available |
| Career | [Job Application Materials](job-materials/) | `job-materials/` | Available |

## Installation

```bash
/plugin marketplace add MattArtzAnthro/AI-Anthropology-Toolkit
```
