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
| Research Design | [Grant & Proposal Writing](grant-proposal/) | `grant-proposal/` | Available |
| Research Design | [Dissertation Prospectus](dissertation-prospectus/) | `dissertation-prospectus/` | Available |
| Research Design | [Methodology Selection](methodology-selection/) | `methodology-selection/` | Available |
| Research Design | [Research Plan Writing](research-plan/) | `research-plan/` | Available |
| Ethics | [IRB & Ethics Protocols](irb-protocol/) | `irb-protocol/` | Available |
| Ethics | Informed Consent Design | `informed-consent/` | Planned |
| Fieldwork | Interview & Focus Group Guides | `interview-guides/` | Planned |
| Fieldwork | Observation Protocols | `observation-protocols/` | Planned |
| Writing | Literature Review | `literature-review/` | Planned |
| Writing | Ethnographic Description | `ethnographic-description/` | Planned |
| Writing | Theoretical Framework | `theoretical-framework/` | Planned |
| Writing | Methods Section | `methods-section/` | Planned |
| Writing | Discussion & Conclusion | `discussion-conclusion/` | Planned |
| Writing | Abstract Writing | `abstract-writing/` | Planned |
| Writing | Revision & Response to Reviewers | `revision-response/` | Planned |
| Writing | Thesis/Dissertation Chapter | `thesis-chapter/` | Planned |
| Review | Peer Review | `peer-review/` | Planned |
| Review | Manuscript Evaluation | `manuscript-evaluation/` | Planned |
| Dissemination | Conference Abstract | `conference-abstract/` | Planned |
| Dissemination | Conference Presentation | `conference-presentation/` | Planned |
| Engagement | Public Writing & Op-Eds | `public-writing/` | Planned |
| Engagement | Community Reports | `community-reports/` | Planned |
| Career | Teaching Statements | `teaching-statement/` | Planned |
| Career | Research Statements | `research-statement/` | Planned |
| Career | CV & Job Materials | `cv-job-materials/` | Planned |

## Installation

```bash
/plugin marketplace add MattArtzAnthro/AI-Anthropology-Toolkit
```
