# AI Anthropology Toolkit

A Claude Code plugin providing skills and agents for anthropological research across the full research lifecycle.

## Plugin Structure

```
AI-Anthropology-Toolkit/
├── .claude-plugin/plugin.json    # Plugin manifest
├── agents/                       # 8 research lifecycle agents
├── commands/                     # Slash commands
├── tests/                        # Repository validation suite
└── skills/                       # 16 research skills
    └── [skill-name]/
        ├── SKILL.md              # Skill definition (YAML frontmatter + instructions)
        └── references/           # Supporting reference files
```

## Components

**Skills (16):** Auto-activated based on user context. Each has a `SKILL.md` with YAML frontmatter (`name`, `description`) and a `references/` directory with detailed guides. Shared conventions and the canonical stance list live in `skills/DESIGN.md`.

**Agents (8):** Phase-specific subagents covering research design, ethics, fieldwork, analysis, proposals, writing, dissemination, and career development. All use `model: inherit` and carry the `Skill` tool plus read-only file tools, invoking the plugin's skills by name.

**Commands (2):** `/ai-anthropology:new-project` — scaffolds a research project through guided lifecycle phases; `/ai-anthropology:skills` — lists the catalog of skills, agents, and commands.

**Tests:** `python3 -m unittest tests/test_repo.py` validates plugin structure, notebook hygiene, and documentation consistency. CI runs the suite on every push and pull request.

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
4. **Analysis** — coding, codebooks, thematic analysis
5. **Funding** — grants, prospectuses
6. **Writing & Review** — articles, chapters, peer review
7. **Dissemination** — conferences, public engagement
8. **Career** — job materials, statements, teaching

## MCP Server & Python Package

The `ai-anthropology-toolkit` Python package ships in this repository (`pyproject.toml`, `src/ai_anthro_toolkit/`) with an MCP server exposing the analysis pipeline as tools: scholarly search (OpenAlex, PubMed), the 42-lens registry, transcript chunking (fully local), and job-based codebook generation, qualitative coding, thematic analysis, and cross-lens comparison. LLM-dependent stages run in `api` mode (ANTHROPIC_API_KEY set) or `delegated` mode, where the orchestrating model completes work packets via `get_next_batch`/`submit_batch` and the server validates every submitted code against the codebook. Install with `pip install -e .` (add `.[chunking]` for local transcript chunking) and register with `claude mcp add ai-anthropology -- python3 -m ai_anthro_toolkit.mcp`. Prompt templates are extracted verbatim from the notebooks; `tests/package/` enforces parity. The same capabilities remain available as the Colab notebooks in `notebooks/`.

## Citation

Artz, M. (2025). AI Anthropology Toolkit. DOI: https://doi.org/10.5281/zenodo.16728812
