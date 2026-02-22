# AI Anthropology Toolkit

A Claude Code plugin providing skills and agents for anthropological research across the full research lifecycle.

## Plugin Structure

```
AI-Anthropology-Toolkit/
├── .claude-plugin/plugin.json    # Plugin manifest
├── agents/                       # 7 research lifecycle agents
├── commands/                     # Slash commands
└── skills/                       # 15 research skills
    └── [skill-name]/
        ├── SKILL.md              # Skill definition (YAML frontmatter + instructions)
        └── references/           # Supporting reference files
```

## Components

**Skills (15):** Auto-activated based on user context. Each has a `SKILL.md` with YAML frontmatter (`name`, `description`) and a `references/` directory with detailed guides.

**Agents (7):** Phase-specific subagents covering research design, ethics, fieldwork, proposals, writing, dissemination, and career development. All use `model: inherit` and read-only tools.

**Commands (1):** `/ai-anthropology:new-project` — scaffolds a research project through guided phases.

## Conventions

- Skill names use kebab-case and match their directory name
- Skill descriptions include trigger phrases for auto-activation
- Reference files are Markdown, one level deep from SKILL.md
- Agent descriptions include `<example>` blocks with `<commentary>`
- All content is anthropology-specific, not generic academic advice
- Epistemic stance (interpretivist, critical, STS, feminist, applied, etc.) is treated as a first-class design parameter

## Research Lifecycle Phases

1. **Research Design** — question, methodology, plan
2. **Ethics & Compliance** — IRB, consent
3. **Fieldwork** — instruments, sampling, data management
4. **Funding** — grants, prospectuses
5. **Writing & Review** — articles, chapters, peer review
6. **Dissemination** — conferences, public engagement
7. **Career** — job materials, statements, teaching

## MCP Server

The AI Anthropology Toolkit MCP server (codebook building, transcript chunking, coding, thematic analysis) lives in a separate repository and is not bundled with this plugin.

## Citation

Artz, M. (2025). AI Anthropology Toolkit. DOI: https://doi.org/10.5281/zenodo.16728812
