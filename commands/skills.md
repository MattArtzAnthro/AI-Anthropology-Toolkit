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
| research-question | Research Design | Helps you turn a research interest into a clear, answerable research question. Walks through the five parts a good question needs and checks it against a rubric. |
| literature-review | Research Design | Helps you plan and write a literature review, whether narrative, scoping, or systematic. Guides your search strategy, logs what you screened and why, and helps you build the bibliography or framework you need. |
| methodology-selection | Research Design | Helps you choose and justify research methods that fit your question and your stance. Checks that your methods actually match what you are trying to find out, including when you need more than one. |
| research-plan | Research Design | Helps you write a standalone research plan. Covers every section, from the problem statement through feasibility. |
| dissertation-prospectus | Research Design | Helps you write your dissertation prospectus. Covers qualifying exam and upgrade documents and what your committee expects. |
| irb-protocol | Ethics & Compliance | Helps you write your IRB protocol. Covers risk assessment and the specific ethics of digital ethnography, section by section. |
| informed-consent | Ethics & Compliance | Helps you design your informed consent process. Covers different consent modes, like written, verbal, layered, or community-based, and how to adapt them to your cultural context. |
| fieldwork-methods | Fieldwork | Helps you design your fieldwork instruments. Covers interview guides, observation protocols, sampling strategy, and how you will manage your data. |
| qualitative-analysis | Analysis | Helps you analyze your qualitative data. Covers building a codebook, coding it, and pulling out themes, including comparing across more than one analytical lens. |
| ethnographic-generalization | Analysis | Helps you figure out what your confirmed findings actually generalize to. Walks through the kind of claim you can make, tests it against disconfirming cases and rivals, and states its scope and how confident you can be. |
| digital-computational-methods | Data Collection & Analysis | Helps you design digital or computational research methods. Covers digital ethnography, platform ethics, computational text methods like topic modeling and text networks, and working alongside AI tools. |
| grant-proposal | Funding | Helps you write a grant proposal for a specific funder. Covers NSF CA-DDRIG, Wenner-Gren, Fulbright, ERC, SSHRC, and Wellcome, each with its own guidance. |
| paper-planning | Writing & Review | Helps you work out what your paper actually argues before you draft it. Extracts your claim, positions it against existing work, and sequences your argument through questions rather than writing. |
| research-writing | Writing & Review | Helps you write your journal article or thesis chapter. Covers ethnographic craft and the conventions of your subfield. |
| academic-review | Writing & Review | Helps you write peer reviews and respond to them. Covers writing the review itself, rebuttal letters, and your revision strategy. |
| rival-interpretations | Writing & Review | Helps you test a claim against rival readings before a reviewer does. Argues your material from three other analytical positions, separates what they agree on from what stays genuinely open, and leaves you a record for your methods section. |
| manuscript-markup | Writing & Review | Helps you work through a manuscript that came back marked up with comments. Reads each comment in place, sorts them, works through them, and drafts your reply letter. |
| proof-review | Writing & Review | Helps you check a publisher's typeset proof against the manuscript you submitted. Compares them word by word, checks that your pseudonyms, quoted speech, and citations survived production, and writes the correction list you send back. |
| conference-materials | Dissemination | Helps you prepare for a conference. Covers AAA abstracts, slide decks, posters, and speaker notes. |
| public-engagement | Dissemination | Helps you write for a general audience. Covers op-eds, blog posts, policy briefs, and community reports. |
| job-materials | Career | Helps you prepare your job market materials. Covers your CV, cover letter, job talk, and overall application strategy. |
| career-statements | Career | Helps you write your career statements. Covers research, teaching, and diversity statements, and tenure narratives. |
| applied-practice | Applied Practice | Helps you write client-facing deliverables for applied anthropology work. Covers statements of work, stakeholder readouts, insight synthesis, and workshops, without losing the anthropology in translation. |
| teaching-materials | Career | Helps you build your course materials. Covers syllabi, lesson plans, assignments, rubrics, and discussion guides. |
| repeated-work | Building | Helps you decide whether work you keep repeating is actually worth turning into a tool. Only if it is, helps you figure out what kind of tool it should be. |
| tool-building | Building | Helps you build your own research tool, like a scraper, MCP server, skill, or agent. Works out a specification with you before writing any code. |

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
| tool-builder | Building a research instrument, or a skill, agent, or MCP tool for this toolkit. The only agent here that writes files |

## Commands

- `/ai-anthropology:new-project` — scaffold a research project through guided lifecycle phases
- `/ai-anthropology:build-tool` — build a research instrument, specification first
- `/ai-anthropology:test-claim` — test one interpretive claim against rival readings, and record what stays open
- `/ai-anthropology:skills` — this catalog

## Guidance

- Skills activate automatically when the conversation matches their triggers;
  users can also ask for one by name.
- Agents suit multi-step tasks that span several skills; skills suit focused,
  single-document work.
- The bundled MCP server runs data collection and the analysis pipeline as
  native tools; the same capabilities exist as Colab notebooks in the
  repository's `notebooks/` directory for hands-on use — see the README.
- Skills adopt the Friction by Design conventions at declared tiers
  (`skills/DESIGN.md` carries the table): Tier 1 skills stop at their core
  judgments and ask, Tier 2 skills declare what they will not decide and
  keep two registers in their outputs, and three skills deliberately carry
  no added friction. When showing a skill's detail entry, name its tier.
