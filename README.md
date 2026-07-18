# AI Anthropology Toolkit

A suite of AI anthropology tools for qualitative research

[Matt Artz](https://www.mattartz.me/) | [GitHub](https://github.com/MattArtzAnthro) | [ORCID](https://orcid.org/0000-0002-3822-1429)

---

## Overview

The **AI Anthropology Toolkit** provides computational tools for anthropological and qualitative research. Every component is grounded in the conventions, debates, and craft knowledge of anthropology and cognate qualitative social sciences. Epistemic stance (interpretivist, critical, STS, feminist, applied, etc.) is treated as a first-class design parameter that shapes methods, writing, and analysis.

The toolkit includes standalone notebooks for data collection and qualitative analysis, a Claude Code plugin with research lifecycle skills and agents, and an MCP server that lets Claude run the full pipeline — from data collection through coding and thematic analysis — directly.

## What is AI Anthropology?

AI Anthropology is the integrated practice of studying, using, and shaping AI ([Artz 2026](https://doi.org/10.1111/gena.70007)) — an iterative lifecycle of anthropology **of**, **by**, and **for** AI ([Artz 2026](https://doi.org/10.4324/9781032672663-29)):

- **Anthropology of AI** — studying AI systems as cultural phenomena: how they reflect, reshape, and redistribute human culture and power
- **Anthropology by AI** — using AI and computational methods to extend ethnographic research while preserving interpretive judgment
- **Anthropology for AI** — bringing anthropological insight to the design, building, and governance of AI systems

This toolkit primarily operationalizes anthropology **by** AI — scaling qualitative research while keeping the researcher's interpretive authority at the center — and is itself an act of anthropology **for** AI: purpose-built research infrastructure designed with anthropological sensibilities. The toolkit is presented as a demonstration of multi-agent ethnography in [A Call for an AI Anthropology](https://doi.org/10.1111/gena.70007) (*General Anthropology*) and [Multi-Agent Ethnography: Post-Conventional Anthropological Practice Through Human-AI Collaboration](https://doi.org/10.1080/00664677.2026.2614501) (*Anthropological Forum*).

## Notebooks

Standalone notebooks for computational qualitative analysis. Most can be run directly in Google Colab. Notebooks marked **Local** should be run on your own machine (see [Running Locally](#running-locally) below).

| Notebook | Run | Description |
|:---------|:---:|:------------|
| [Academic Literature Explorer](notebooks/Academic_Literature_Explorer.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Academic_Literature_Explorer.ipynb) | Search 250M+ scholarly works across all disciplines via OpenAlex with citation counts and open access detection |
| [CrossRef Reference Verifier](notebooks/CrossRef_Reference_Verifier.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/CrossRef_Reference_Verifier.ipynb) | Verify reference lists against canonical CrossRef metadata — DOI resolution, text-vs-record comparison, retraction flags — plus journal and author queries |
| [Qualitative Codebook Builder](notebooks/Qualitative_Codebook_Builder.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Qualitative_Codebook_Builder.ipynb) | Build qualitative codebooks from source literature with AI-assisted code generation, validation, and structured export |
| [Audio Transcription with Whisper](notebooks/Audio_Transcription_Whisper.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Audio_Transcription_Whisper.ipynb) | Transcribe audio and video recordings locally with Whisper — timestamped transcripts, optional speaker diarization, and Chunker-ready export |
| [Interview Transcript Semantic Chunker](notebooks/Interview_Transcript_Semantic_Chunker.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Interview_Transcript_Semantic_Chunker.ipynb) | Segment interview transcripts into semantically coherent chunks with speaker-aware processing and coherence scoring — fully local, no API key required |
| [Coding and Thematic Analysis](notebooks/Coding_and_Thematic_Analysis.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Coding_and_Thematic_Analysis.ipynb) | Apply codes to qualitative data and build themes using deductive, inductive, or hybrid approaches, with multi-lens parallel analysis and cross-lens comparison |
| [Text Network Analysis](notebooks/Text_Network_Analysis.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Text_Network_Analysis.ipynb) | Build co-occurrence networks from text with community detection, centrality metrics, and interactive visualization |
| [Topic Modeling (BERTopic)](notebooks/Topic_Modeling_BERTopic.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Topic_Modeling_BERTopic.ipynb) | Discover topics in text collections using transformer-based clustering with interactive visualizations and zero-shot mode |
| [Named Entity Recognition (GLiNER2)](notebooks/Named_Entity_Recognition_GLiNER2.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Named_Entity_Recognition_GLiNER2.ipynb) | Extract people, places, organizations, concepts, and custom entity types from text using zero-shot NER |
| [Google Books Ngram Explorer](notebooks/Google_Books_Ngram_Explorer.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Google_Books_Ngram_Explorer.ipynb) | Analyze historical word frequency patterns across Google Books corpora (1800-2022) with visualization and export |
| [Google Trends Explorer](notebooks/Google_Trends_Explorer.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Google_Trends_Explorer.ipynb) | Retrieve and visualize Google Trends data with multi-term comparison, regional breakdowns, and related queries |
| [Google News Explorer](notebooks/Google_News_Explorer.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Google_News_Explorer.ipynb) | Search Google News by keyword, time period, and country with quick or extended date-range modes |
| [Google Scholar Explorer](notebooks/Google_Scholar_Explorer.ipynb) | Local | Search Google Scholar for publications with year filtering, citation counts, and structured export |
| [PubMed Literature Harvester](notebooks/PubMed_Literature_Harvester.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/PubMed_Literature_Harvester.ipynb) | Search PubMed and enrich results with metadata from CrossRef, OpenAlex, and Semantic Scholar |
| [Google Patents Explorer](notebooks/Google_Patents_Explorer.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Google_Patents_Explorer.ipynb) | Search Google Patents for patent metadata including titles, inventors, assignees, and filing dates |
| [YouTube Video Search](notebooks/YouTube_Video_Search.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/YouTube_Video_Search.ipynb) | Search YouTube and export video metadata including titles, channels, views, and durations |
| [YouTube Transcript Fetcher](notebooks/YouTube_Transcript_Fetcher.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/YouTube_Transcript_Fetcher.ipynb) | Fetch YouTube video transcripts with language selection, segment chunking, and multiple export formats |
| [Podcast RSS Explorer](notebooks/Podcast_RSS_Explorer.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Podcast_RSS_Explorer.ipynb) | Pull episode metadata from any podcast RSS feed with titles, dates, durations, and structured export |


## Skills

Research skills in the portable [SKILL.md format](https://agentskills.io) that activate automatically based on context. In Claude Code, the [AI Anthropology Toolkit plugin](https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit) installs all of them at once; other coding agents can install any skill by copying its folder (see [Using the Skills in Other Agents](#using-the-skills-in-other-agents) below).

| Skill | Description |
|:------|:------------|
| research-question | Five-slot question grammar, evaluation rubric, genre conventions |
| literature-review | Review genres, search logging, screening audit trails, annotated bibliographies, literature matrices, framework construction |
| methodology-selection | Method-stance compatibility, evidence need decomposition, multi-method design |
| research-plan | Ten-section plan architecture covering problem through feasibility |
| irb-protocol | 13-section protocol narratives, risk assessment, digital ethnography ethics |
| informed-consent | Consent modes (written, verbal, layered, community-based), cultural adaptation |
| grant-proposal | NSF CA-DDRIG, Wenner-Gren, Fulbright, ERC, SSHRC, Wellcome — funder-specific guidance |
| dissertation-prospectus | Section-by-section prospectus development (8-30 pages) |
| fieldwork-methods | Interview guides, observation protocols, sampling strategies, data management plans |
| qualitative-analysis | Codebook development, deductive/inductive/hybrid coding, thematic analysis, multi-lens comparison |
| digital-computational-methods | Digital ethnography and platform ethics, computational text analysis at scale, AI-collaboration design |
| research-writing | Article architecture, ethnographic craft, subfield conventions, journal requirements |
| academic-review | Peer review writing, rebuttal letters, revision strategy |
| conference-materials | AAA abstracts, slide decks, posters, speaker notes, oral delivery |
| public-engagement | Op-eds, blog posts, policy briefs, community reports, media preparation |
| job-materials | Academic CVs, cover letters, job talks, application strategy |
| career-statements | Research, teaching, and diversity statements; tenure narratives |
| teaching-materials | Syllabi, lesson plans, assignments, rubrics, discussion guides |
| applied-practice | Client engagements: statements of work, stakeholder readouts, insight synthesis, workshop facilitation, research repositories |

### Using the Skills in Other Agents

Each skill is a self-contained folder (`SKILL.md` plus a `references/` directory) in the portable format that most 2026 coding agents read. To install one outside Claude Code, clone the repository and copy the skill folder — plus `skills/DESIGN.md`, the shared analytical-lens reference the skills consult — into your agent's skills directory:

```bash
git clone https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit.git
cp -r AI-Anthropology-Toolkit/skills/qualitative-analysis AI-Anthropology-Toolkit/skills/DESIGN.md ~/.codex/skills/
```

| Agent | Skills directory |
|:------|:-----------------|
| Claude Code | `~/.claude/skills/` (or install the plugin — all 16 at once) |
| OpenAI Codex CLI | `~/.codex/skills/` |
| Cursor | `~/.cursor/skills/` |
| GitHub Copilot / VS Code | `~/.copilot/skills/` |
| Shared project-level | `.agents/skills/` in your repository |

The skills pair naturally with the MCP server (below): descriptions route the request, the server runs the pipeline.

## Agents

Autonomous Claude Code subagents that orchestrate across multiple skills for complex, multi-step tasks.

| Agent | Description |
|:------|:------------|
| research-design | Orchestrates question, methodology, and plan skills for end-to-end research design |
| ethics-reviewer | Reviews research designs for ethics issues, drafts protocols and consent documents |
| proposal-advisor | Translates research designs into persuasive funder-specific narratives |
| fieldwork-advisor | Designs instruments tailored to specific research questions and fieldwork contexts |
| analysis-advisor | Guides qualitative coding, codebook development, and thematic analysis |
| writing-advisor | Guides article/chapter writing and R&R management |
| dissemination-advisor | Handles register translation between academic and public audiences |
| career-advisor | Coordinates application packages and course design |

## Commands

| Command | Description |
|:------|:------------|
| `/ai-anthropology:new-project` | Scaffold a new research project through guided phases |
| `/ai-anthropology:skills` | List the toolkit's skills, agents, and commands |

## MCP Server

The toolkit also ships as a Python package ([`ai-anthropology-toolkit` on PyPI](https://pypi.org/project/ai-anthropology-toolkit/)) with an MCP server, so Claude (and other MCP clients) can drive the full research pipeline conversationally: data collection (OpenAlex, CrossRef, PubMed, Google Scholar, Google Trends, Google News, Google Patents, Books Ngram, YouTube search and transcripts, podcast RSS) and analysis (transcript chunking, lens-configured codebook generation, qualitative coding with per-code validation, thematic analysis, and cross-lens comparison).

Installing the Claude Code plugin (above) bundles the server automatically. It also registers in any other MCP-capable agent — the command is the same everywhere:

**Claude Code**

```
claude mcp add ai-anthropology -- uvx --from "ai-anthropology-toolkit[data]==2.2.2" ai-anthro-mcp
```

**OpenAI Codex CLI**

```
codex mcp add ai-anthropology -- uvx --from "ai-anthropology-toolkit[data]==2.2.2" ai-anthro-mcp
```

**Google Gemini CLI**

```
gemini mcp add -s user ai-anthropology uvx -- --from "ai-anthropology-toolkit[data]==2.2.2" ai-anthro-mcp
```

The server is model-agnostic. With `ANTHROPIC_API_KEY` set, analysis runs autonomously (`api` mode). Without it, whichever model is orchestrating — Claude, GPT, or Gemini — performs each interpretive step itself through validated work packets (`delegated` mode): the analysis runs on your model, the methodology and validation run on the server, and every coding decision stays visible to the researcher.

### Coding Agents & Sandboxes

AI coding agents — Claude Code and Claude Desktop's Cowork, OpenAI Codex CLI, Gemini CLI — often run in sandboxed environments where MCP connectors are unavailable but `pip` and Python still work. The toolkit degrades gracefully across three tiers:

1. **MCP tools available** → use them; the full pipeline runs natively.
2. **Code execution only** → install the package and call the Python API directly:

   ```bash
   pip install "ai-anthropology-toolkit[data]"
   python -m ai_anthro_toolkit.doctor
   ```

   The doctor (`python -m ai_anthro_toolkit.doctor`, also installed as `ai-anthro-doctor`) probes every data source from the current network and reports which are reachable. Sandbox network policies typically allow the scholarly APIs (OpenAlex, CrossRef, PubMed) and block the Google/YouTube scraping endpoints — collect what is reachable and route each blocked source to local execution or its Colab notebook (the doctor prints the link). The collector functions live in `ai_anthro_toolkit.datasources`; transcript chunking (`ai_anthro_toolkit.chunking`, fully local) and the 42-lens registry (`ai_anthro_toolkit.lenses`) work in any environment. Agent-facing instructions for this fallback chain ship in this repository as [AGENTS.md](AGENTS.md) and [GEMINI.md](GEMINI.md).
3. **No code execution either** → every capability runs in the browser through the Colab notebooks below.

## Getting Started

### Notebooks (Colab)

Click any **Open in Colab** badge above to run a notebook directly in your browser. Each notebook handles its own dependencies — no local installation needed.

### Running Locally

Some notebooks (marked **Local** in the table) need to be run on your own machine. This requires Python and Jupyter.

**If you already have Anaconda/Miniconda installed:**

```bash
pip install scholarly
jupyter notebook
```

Then open the notebook file from the Jupyter file browser.

**If you need to install Jupyter from scratch:**

```bash
pip install jupyter scholarly
jupyter notebook
```

Notebooks that run locally will install any other dependencies they need automatically when you run the first cell.

### Claude Code Plugin

Install the plugin in Claude Code:

```
/plugin marketplace add MattArtzAnthro/AI-Anthropology-Toolkit
/plugin install ai-anthropology@ai-anthropology
```

Skills activate automatically when Claude detects relevant context. Agents handle multi-step tasks across skills. Commands are invoked with slash syntax.

## License

This repository — notebooks, Python package, MCP server, plugin content, and documentation — is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE): free for noncommercial use, including research, education, and work by nonprofit and government research organizations, with attribution to Matt Artz appreciated. For commercial licensing, contact [Matt Artz](https://www.mattartz.me/).

## Citation

If you use this toolkit in your academic research, please cite:

> Artz, Matt. 2026. AI Anthropology Toolkit. Software. Zenodo. https://doi.org/10.5281/zenodo.16728812

## Research Behind the Toolkit

The toolkit operationalizes a published research program on AI Anthropology:

Artz, Matt. 2026. "A Call for an AI Anthropology." General Anthropology 33(1): 23–28. https://doi.org/10.1111/gena.70007.

Artz, Matt. 2026. "Multi-Agent Ethnography: Post-Conventional Anthropological Practice Through Human-AI Collaboration." Anthropological Forum. https://doi.org/10.1080/00664677.2026.2614501.

Artz, Matt. 2026. "Artificial Intelligence: The AI Anthropology Lifecycle (of, by, for AI)." In Practicing Digital Ethnography, edited by Devin Proctor. Routledge. https://doi.org/10.4324/9781032672663-29.

Koycheva, Lora, Angela K. VandenBroek, and Matt Artz, eds. 2026. Anthropology and AI. New York: Routledge. https://doi.org/10.4324/9781003532750.

Artz, Matt. 2023. From Machine Learning to Machine Knowing: A Digital Anthropology Approach for the Machine Interpretation of Cultures. UNESCO. https://unesdoc.unesco.org/ark:/48223/pf0000384902.

Artz, Matt. 2023. "Ten Predictions for AI and the Future of Anthropology." Anthropology News, May 8. https://doi.org/10.1111/AN.1605.

Artz, Matt. Forthcoming. "AI Anthropology: The Future of Applied Anthropological Practice." In Routledge Handbook of Applied Anthropology, edited by Christina Wasson, Edward B. Liebow, Karine L. Narahara, Ndukuyakhe Ndlovu, and Alaka Wali. New York: Routledge.
