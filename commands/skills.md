---
name: skills
description: List the AI Anthropology Toolkit's skills, agents, and commands with what each covers and when to use it
argument-hint: "[optional: skill or agent name for detail]"
---

# AI Anthropology Toolkit Catalog

Present the catalog below to the user. If an argument names a specific skill
or agent, show only that entry plus its trigger guidance and closest
neighbors. Format the output as readable tables or lists; do not dump raw
markdown.

## Skills (auto-activate from context; invocable via the Skill tool)

| Skill | Phase | Covers |
|-------|-------|--------|
| research-question | Research Design | Question formulation: five-slot grammar, evaluation rubric, genre conventions |
| methodology-selection | Research Design | Method choice and justification, method-stance compatibility, multi-method design |
| research-plan | Research Design | Standalone research plans: ten-section architecture, problem through feasibility |
| dissertation-prospectus | Research Design | Prospectuses, qualifying exam and upgrade documents, committee expectations |
| irb-protocol | Ethics & Compliance | IRB protocol narratives, risk assessment, digital ethnography ethics |
| informed-consent | Ethics & Compliance | Consent modes (written, verbal, layered, community-based), cultural adaptation |
| fieldwork-methods | Fieldwork | Interview guides, observation protocols, sampling, data management plans |
| qualitative-analysis | Analysis | Codebooks, deductive/inductive/hybrid coding, thematic analysis, multi-lens comparison |
| grant-proposal | Funding | NSF CA-DDRIG, Wenner-Gren, Fulbright, ERC, SSHRC, Wellcome funder-specific guidance |
| research-writing | Writing & Review | Journal articles, thesis and dissertation chapters, ethnographic craft |
| academic-review | Writing & Review | Peer review writing, rebuttal letters, revision strategy |
| conference-materials | Dissemination | AAA abstracts, slide decks, posters, speaker notes |
| public-engagement | Dissemination | Op-eds, blog posts, policy briefs, community reports, media preparation |
| job-materials | Career | Academic CVs, cover letters, job talks, application strategy |
| career-statements | Career | Research, teaching, and diversity statements; tenure narratives |
| teaching-materials | Career | Syllabi, lesson plans, assignments, rubrics, discussion guides |

## Agents (autonomous, multi-step work across skills)

| Agent | Use for |
|-------|---------|
| research-design | End-to-end research design: question + methods + plan |
| ethics-reviewer | Ethics review, IRB protocols, consent design |
| fieldwork-advisor | Data collection instruments, sampling, data management |
| analysis-advisor | Qualitative coding, codebook development, thematic analysis |
| proposal-advisor | Grant proposals and dissertation prospectuses for a specific funder or committee |
| writing-advisor | Articles, chapters, and the peer review / R&R process |
| dissemination-advisor | Conference materials and public-facing writing |
| career-advisor | Application packages, career statements, course design |

## Commands

- `/ai-anthropology:new-project` — scaffold a research project through guided lifecycle phases
- `/ai-anthropology:skills` — this catalog

## Guidance

- Skills activate automatically when the conversation matches their triggers;
  users can also ask for one by name.
- Agents suit multi-step tasks that span several skills; skills suit focused,
  single-document work.
- The bundled MCP server runs data collection and the analysis pipeline as
  native tools; the same capabilities exist as Colab notebooks in the
  repository's `notebooks/` directory for hands-on use — see the README.
