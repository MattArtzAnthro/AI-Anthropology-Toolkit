# AI Anthropology Toolkit

*A Claude Code plugin for anthropological research across the full research lifecycle*

**Created by [Matt Artz](https://www.mattartz.me/)**

---

## Overview

The **AI Anthropology Toolkit** is a Claude Code plugin that provides discipline-specific skills, agents, and workflows for anthropological research. It covers the entire research lifecycle — from formulating research questions through publication and career advancement.

Rather than offering generic academic advice, every component is grounded in the conventions, debates, and craft knowledge of anthropology and cognate qualitative social sciences. Epistemic stance (interpretivist, critical, STS, feminist, applied, etc.) is treated as a first-class design parameter that shapes methods, writing, and analysis.

## What is AI Anthropology?

AI Anthropology is an emerging field that combines:
- **Studying AI as cultural artifact** — Understanding how AI systems reflect and shape human culture
- **Using AI to enhance ethnographic research** — Leveraging computational methods to scale qualitative analysis
- **Applying anthropological insights to AI development** — Bringing cultural understanding to technology design

This toolkit focuses on the second aspect: using AI to enhance traditional anthropological research methods while preserving the interpretive frameworks that make the discipline unique.

## Installation

Install the plugin in Claude Code:

```bash
claude plugin add /path/to/AI-Anthropology-Toolkit
```

Or test locally:

```bash
claude --plugin-dir /path/to/AI-Anthropology-Toolkit
```

## What's Included

The plugin provides **15 skills**, **7 agents**, and **1 command**, organized across 7 research lifecycle phases.

### Phase 1: Research Design

Design a study from the ground up — formulate questions, select methods, build a plan.

| Component | Type | What It Does |
|---|---|---|
| research-question | Skill | Five-slot question grammar, evaluation rubric, genre conventions |
| methodology-selection | Skill | Method-stance compatibility, evidence need decomposition, multi-method design |
| research-plan | Skill | Ten-section plan architecture covering problem through feasibility |
| research-design | Agent | Orchestrates all three skills for end-to-end research design |

### Phase 2: Ethics and Compliance

Navigate IRB requirements and design ethically sound research.

| Component | Type | What It Does |
|---|---|---|
| irb-protocol | Skill | 13-section protocol narratives, risk assessment, digital ethnography ethics |
| informed-consent | Skill | Consent modes (written, verbal, layered, community-based), cultural adaptation |
| ethics-reviewer | Agent | Reviews research designs for ethics issues, drafts protocols and consent documents |

### Phase 3: Funding and Proposals

Write grant proposals and dissertation prospectuses.

| Component | Type | What It Does |
|---|---|---|
| grant-proposal | Skill | NSF CA-DDRIG, Wenner-Gren, Fulbright, ERC, SSHRC, Wellcome — funder-specific guidance |
| dissertation-prospectus | Skill | Section-by-section prospectus development (8-30 pages) |
| proposal-advisor | Agent | Translates research designs into persuasive funder-specific narratives |

### Phase 4: Fieldwork

Design data collection instruments and plan fieldwork logistics.

| Component | Type | What It Does |
|---|---|---|
| fieldwork-methods | Skill | Interview guides, observation protocols, sampling strategies, data management plans |
| fieldwork-advisor | Agent | Designs instruments tailored to specific research questions and fieldwork contexts |

### Phase 5: Writing and Review

Write research articles, manage peer review, handle revisions.

| Component | Type | What It Does |
|---|---|---|
| research-writing | Skill | Article architecture, ethnographic craft, subfield conventions, journal requirements |
| academic-review | Skill | Peer review writing, rebuttal letters, revision strategy |
| writing-advisor | Agent | Guides article/chapter writing and R&R management |

### Phase 6: Dissemination

Prepare conference presentations and public-facing work.

| Component | Type | What It Does |
|---|---|---|
| conference-materials | Skill | AAA abstracts, slide decks, posters, speaker notes, oral delivery |
| public-engagement | Skill | Op-eds, blog posts, policy briefs, community reports, media preparation |
| dissemination-advisor | Agent | Handles register translation between academic and public audiences |

### Phase 7: Career Development

Build job applications, career statements, and teaching materials.

| Component | Type | What It Does |
|---|---|---|
| job-materials | Skill | Academic CVs, cover letters, job talks, application strategy |
| career-statements | Skill | Research, teaching, and diversity statements; tenure narratives |
| teaching-materials | Skill | Syllabi, lesson plans, assignments, rubrics, discussion guides |
| career-advisor | Agent | Coordinates application packages and course design |

### Commands

| Command | What It Does |
|---|---|
| `/ai-anthropology:new-project` | Scaffold a new research project through guided phases |

## How It Works

**Skills** activate automatically when Claude detects relevant context in your request. Ask about research questions, and the research-question skill loads. Ask about IRB protocols, and the irb-protocol skill loads.

**Agents** are autonomous subprocesses that handle multi-step tasks. They orchestrate across multiple skills for a given research phase. Claude delegates to them when the task requires coordinated, phase-level guidance.

**Commands** are user-initiated workflows you invoke with a slash command.

## Companion Notebooks

The toolkit is complemented by three standalone Jupyter notebooks for computational qualitative analysis. These are separate repositories that can be used independently or alongside the plugin. They will eventually be integrated into the plugin as an MCP server.

| Notebook | What It Does |
|---|---|
| [Qualitative Codebook Builder](https://github.com/MattArtzAnthro/Qualitative_Codebook_Builder) | AI-assisted development of qualitative coding frameworks with theory-driven code generation, inclusion/exclusion criteria, and export for analysis software |
| [Interview Transcript Semantic Chunker](https://github.com/MattArtzAnthro/Interview_Transcript_Semantic_Chunker) | Segments interview transcripts into semantically coherent chunks with speaker-aware processing, multi-format support (PDF, DOCX, TXT, RTF), and export for NVivo/ATLAS.ti |
| [Coding and Thematic Analysis](https://github.com/MattArtzAnthro/Coding_and_Thematic_Analysis) | Applies codes to qualitative data and builds themes using deductive, inductive, or hybrid approaches with visualizations and professional export (Excel, Word) |

## Subfield Coverage

The toolkit covers anthropology broadly:
- Sociocultural anthropology
- Linguistic anthropology
- Medical anthropology
- Archaeological methods (qualitative components)
- Biological anthropology (qualitative components)
- Applied and design anthropology
- Science and Technology Studies (STS)
- Cognate qualitative social sciences

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) license. You may remix, adapt, and build upon the material for non-commercial purposes, provided you credit Matt Artz and link to the repository.

**Full license details**: https://creativecommons.org/licenses/by-nc/4.0/

## Attribution

If you use or adapt this project in your work, please cite:

> Built with the AI Anthropology Toolkit (Matt Artz, 2025) — https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit

## Citation

If you use this toolkit in your academic research, please cite:

> Artz, Matt. 2025. AI Anthropology Toolkit. Software. Zenodo. https://doi.org/10.5281/zenodo.16728812

## References

Artz, Matt. Forthcoming. "AI Anthropology: The Future of Applied Anthropological Practice." In Routledge Handbook of Applied Anthropology, edited by Christina Wasson, Edward B. Liebow, Karine L. Narahara, Ndukuyakhe Ndlovu, and Alaka Wali. New York: Routledge.
