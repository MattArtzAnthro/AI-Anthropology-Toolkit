# AI Anthropology Toolkit

Computational tools for anthropological research: a Claude Code plugin (skills, agents, commands), a Python package with an MCP server, and Colab notebooks — one repository, one release lineage.

**Working principle.** Be adversarial toward your own output. Trust what
survives an attempt to break it, and be most suspicious of what arrived
easily.

This is earned confidence rather than hedging. Test, then commit to what
survives, and be direct about it. It does not license performed doubt,
blanket qualification, or refusing to decide.

## Repository Structure

```
AI-Anthropology-Toolkit/
├── .claude-plugin/plugin.json    # Plugin manifest (bundles the MCP server via .mcp.json)
├── .mcp.json                     # uvx registration for the bundled MCP server
├── AGENTS.md / GEMINI.md         # Instructions for non-Claude coding agents
├── agents/                       # 9 agents (8 lifecycle advisors + tool-builder)
├── commands/                     # Slash commands
├── notebooks/                    # 23 Colab notebooks (data collection + analysis)
├── pyproject.toml                # ai-anthropology-toolkit package (PyPI)
├── src/ai_anthro_toolkit/        # Package: datasources, analysis pipeline, MCP server, doctor
├── tests/                        # Repo validation + skill routing evals
│   └── package/                  # Package behavior, consistency, and parity tests
└── skills/                       # 27 research skills
    └── [skill-name]/
        ├── SKILL.md              # Skill definition (YAML frontmatter + instructions)
        └── references/           # Supporting reference files
```

## Components

**Skills (27):** Auto-activated based on user context. Each has a `SKILL.md` with YAML frontmatter (`name`, `description`) and a `references/` directory with detailed guides. Shared conventions and the canonical stance list live in `skills/DESIGN.md`.

**Agents (9):** Eight phase-specific advisors covering research design, ethics, fieldwork, analysis, proposals, writing, dissemination, and career development, all carrying the `Skill` tool plus read-only file tools. The ninth, `tool-builder`, is the only agent that writes files: it runs the `tool-building` workflow, whose three gates stop for the researcher at the sort, at ratification of the specification, and at any verification finding that requires deciding what the artifact should do. All use `model: inherit`.

**Commands (4):** `/ai-anthropology:new-project` — scaffolds a research project through guided lifecycle phases; `/ai-anthropology:build-tool` — builds a research instrument, specification first; `/ai-anthropology:test-claim` — tests one interpretive claim against rival readings argued from other analytical positions, and records what stays open; `/ai-anthropology:skills` — lists the catalog of skills, agents, and commands.

**Tests:** `python3 -m unittest discover -s tests -t .` runs everything: `tests/test_repo.py` (plugin structure, notebook hygiene, documentation consistency), `tests/test_skill_routing.py` (deterministic routing evals — each skill description must win its typical prompts; description-collision ceiling), and `tests/package/` (package behavior, server consistency, notebook-prompt parity). A fourth tier, `tests/evals/` (behavioral gate-holding evals for the Friction by Design conventions), runs only locally with `AAT_RUN_GATE_EVALS=1` and the `claude` CLI — model behavior is nondeterministic and costs tokens, so CI never runs it. CI runs two jobs on every push: `validate` (repo + routing suites, stdlib only) and `package` (installs the package with extras and runs `tests/package/`; live scraper tests are skipped there via `AAT_SKIP_LIVE_SCRAPERS` because datacenter IPs are the blocked class and can hang in library retry loops).

## Conventions

- Skill names use kebab-case and match their directory name
- Skill descriptions include trigger phrases for auto-activation
- Reference files are Markdown, one level deep from SKILL.md
- Agent descriptions include `<example>` blocks with `<commentary>`
- All content is anthropology-specific, not generic academic advice
- Epistemic stance (interpretivist, critical, STS, feminist, applied, etc.) is treated as a first-class design parameter
- Friction by Design governs researcher-machine interaction: skills adopt the conventions at tiers declared in `skills/DESIGN.md`, enforced structurally by `tests/test_repo.py`

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

The `ai-anthropology-toolkit` Python package ships in this repository (`pyproject.toml`, `src/ai_anthro_toolkit/`) with an MCP server exposing the research pipeline as 27 tools: data collection (OpenAlex, CrossRef, PubMed, Google Scholar, Google Trends, Google News, Google Patents, Books Ngram, YouTube search and transcripts, podcast RSS — scraper dependencies via the `[data]` extra), the 42-lens registry, transcript chunking (fully local), and job-based codebook generation, qualitative coding, thematic analysis, and cross-lens comparison. LLM-dependent stages run in `api` mode (ANTHROPIC_API_KEY set) or `delegated` mode, where the orchestrating model completes work packets via `get_next_batch`/`submit_batch` and the server validates every submitted code against the codebook. Coding is gated under the Friction by Design conventions: `ratify_codebook` records the researcher's confirm-or-revise decision (with a content checksum), and `start_coding_job` refuses a codebook with no matching ratification — the server enforces sequence, not sincerity. Standing checks (`ai_anthro_toolkit.checks`) cover codebooks and coded datasets, and `checks.generated` builds a researcher's own checks from the five commitments `tool-building` settles at Stage 4 — persisted as `instrument-checks.json` beside their data, validated against a fixed answer vocabulary, never executed as code. An unanswered commitment generates nothing, and an answer that cannot be checked from the data alone is recorded as unenforceable with its reason. Install with `pip install -e ".[data]"` (add `chunking` to the extras for local transcript chunking) and register with `claude mcp add ai-anthropology -- python3 -m ai_anthro_toolkit.mcp`. Prompt templates are extracted verbatim from the notebooks; `tests/package/` enforces parity. The same capabilities remain available as the Colab notebooks in `notebooks/`.

In environments with code execution but no MCP tools (agent sandboxes such as Claude Cowork, Codex CLI, Gemini CLI), the fallback chain is: `pip install "ai-anthropology-toolkit[data]"`, run `python -m ai_anthro_toolkit.doctor` to see which data sources the network allows, collect from reachable sources via the Python API, and route blocked sources to local execution or their Colab notebook. AGENTS.md and GEMINI.md at the repo root carry these instructions for non-Claude agents.

## Releasing

Two release tracks ship from one commit and the ordering matters: the package version is pinned inside `.mcp.json`, `AGENTS.md`, and `GEMINI.md`, so the package must be uploaded to PyPI **before** the commit is pushed, or every fresh install fails until it lands. A green test suite is not a release check — it runs against whatever is already installed and cannot see what a fresh resolve would pick. Full checklist, including why neither PyPI read path proves an upload landed, is in [RELEASING.md](RELEASING.md).

## Citation

Artz, M. (2025). AI Anthropology Toolkit. DOI: https://doi.org/10.5281/zenodo.16728812
