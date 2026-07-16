# AI Anthropology Toolkit

A suite of AI anthropology tools for qualitative research

[Matt Artz](https://www.mattartz.me/) | [GitHub](https://github.com/MattArtzAnthro) | [ORCID](https://orcid.org/0000-0002-3822-1429)

---

## Overview

The **AI Anthropology Toolkit** provides computational tools for anthropological and qualitative research. Every component is grounded in the conventions, debates, and craft knowledge of anthropology and cognate qualitative social sciences. Epistemic stance (interpretivist, critical, STS, feminist, applied, etc.) is treated as a first-class design parameter that shapes methods, writing, and analysis.

The toolkit includes standalone notebooks for qualitative data analysis, a Claude Code plugin with research lifecycle skills and agents, and will expand to include MCP servers and additional components over time.

## What is AI Anthropology?

AI Anthropology is an emerging field that combines:
- **Studying AI as cultural artifact** — Understanding how AI systems reflect and shape human culture
- **Using AI to enhance ethnographic research** — Leveraging computational methods to scale qualitative analysis
- **Applying anthropological insights to AI development** — Bringing cultural understanding to technology design

This toolkit focuses on the second aspect: using AI to enhance traditional anthropological research methods while preserving the interpretive frameworks that make the discipline unique.

## Notebooks

Standalone notebooks for computational qualitative analysis. Most can be run directly in Google Colab. Notebooks marked **Local** should be run on your own machine (see [Running Locally](#running-locally) below).

| Notebook | Run | Description |
|:---------|:---:|:------------|
| [Academic Literature Explorer](notebooks/Academic_Literature_Explorer.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Academic_Literature_Explorer.ipynb) | Search 250M+ scholarly works across all disciplines via OpenAlex with citation counts and open access detection |
| [Qualitative Codebook Builder](notebooks/Qualitative_Codebook_Builder.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Qualitative_Codebook_Builder.ipynb) | Build qualitative codebooks from source literature with AI-assisted code generation, validation, and structured export |
| [Interview Transcript Semantic Chunker](notebooks/Interview_Transcript_Semantic_Chunker.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Interview_Transcript_Semantic_Chunker.ipynb) | Segment interview transcripts into semantically coherent chunks with speaker-aware processing and coherence scoring |
| [Coding and Thematic Analysis](notebooks/Coding_and_Thematic_Analysis.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Coding_and_Thematic_Analysis.ipynb) | Apply codes to qualitative data and build themes using deductive, inductive, or hybrid approaches |
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

Claude Code skills that activate automatically based on context. Requires the [AI Anthropology Toolkit plugin](https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit) installed in Claude Code.

| Skill | Description |
|:------|:------------|
| research-question | Five-slot question grammar, evaluation rubric, genre conventions |
| methodology-selection | Method-stance compatibility, evidence need decomposition, multi-method design |
| research-plan | Ten-section plan architecture covering problem through feasibility |
| irb-protocol | 13-section protocol narratives, risk assessment, digital ethnography ethics |
| informed-consent | Consent modes (written, verbal, layered, community-based), cultural adaptation |
| grant-proposal | NSF CA-DDRIG, Wenner-Gren, Fulbright, ERC, SSHRC, Wellcome — funder-specific guidance |
| dissertation-prospectus | Section-by-section prospectus development (8-30 pages) |
| fieldwork-methods | Interview guides, observation protocols, sampling strategies, data management plans |
| qualitative-analysis | Codebook development, deductive/inductive/hybrid coding, thematic analysis, multi-lens comparison |
| research-writing | Article architecture, ethnographic craft, subfield conventions, journal requirements |
| academic-review | Peer review writing, rebuttal letters, revision strategy |
| conference-materials | AAA abstracts, slide decks, posters, speaker notes, oral delivery |
| public-engagement | Op-eds, blog posts, policy briefs, community reports, media preparation |
| job-materials | Academic CVs, cover letters, job talks, application strategy |
| career-statements | Research, teaching, and diversity statements; tenure narratives |
| teaching-materials | Syllabi, lesson plans, assignments, rubrics, discussion guides |

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

This project is licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). You may remix, adapt, and build upon the material for non-commercial purposes, provided you credit Matt Artz and link to the repository.

## Citation

If you use this toolkit in your academic research, please cite:

> Artz, Matt. 2025. AI Anthropology Toolkit. Software. Zenodo. https://doi.org/10.5281/zenodo.16728812

## References

Artz, Matt. 2023. From Machine Learning to Machine Knowing: A Digital Anthropology Approach for the Machine Interpretation of Cultures. UNESCO. https://unesdoc.unesco.org/ark:/48223/pf0000384902.

Artz, Matt. 2023. "Ten Predictions for AI and the Future of Anthropology." Anthropology News, May 8. https://doi.org/10.1111/AN.1605.

Artz, Matt. 2026. "Artificial Intelligence: The AI Anthropology Lifecycle (of, by, for AI)." In Practicing Digital Ethnography, edited by Devin Proctor. Routledge. https://doi.org/10.4324/9781032672663-29.

Artz, Matt. 2026. "Multi-Agent Ethnography: Post-Conventional Anthropological Practice Through Human-AI Collaboration." Human Organization. https://doi.org/10.1080/00664677.2026.2614501.

Artz, Matt. Forthcoming. "AI Anthropology: The Future of Applied Anthropological Practice." In Routledge Handbook of Applied Anthropology, edited by Christina Wasson, Edward B. Liebow, Karine L. Narahara, Ndukuyakhe Ndlovu, and Alaka Wali. New York: Routledge.
