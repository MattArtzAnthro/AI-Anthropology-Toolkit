# Changelog

All notable changes to the AI Anthropology Toolkit are documented here. Dates are UTC.

This project has two release tracks: the `ai-anthropology-toolkit` Python package (notebooks, MCP server, data-collection tools; published to PyPI) and the Claude Code plugin (skills, agents, MCP registration). Versions are tracked separately below.

## Package (`ai-anthropology-toolkit` on PyPI)

### 2.2.3 — 2026-07-18
- Added five notebooks: World Bank Data Explorer, UN Data Explorer, BLS Labor Statistics Explorer, Multimodal Embedding Explorer, and Visual Analysis & Image Annotation
- Added a Multimodal & Visual Analysis notebook category
- Notebook catalog now serves 23 notebooks across four categories

### 2.2.2 — 2026-07-18
- Added the CrossRef Reference Verifier notebook: verifies reference lists against CrossRef metadata, flags mismatches, invalid or retracted DOIs, and recovers missing DOIs
- Keyless throughout; runs from Colab, locally, or in sandboxed agent environments

### 2.2.1 — 2026-07-18
- Added the Audio Transcription with Whisper notebook: local faster-whisper transcription with timestamped segments, optional speaker diarization, GPU auto-detection, and multiple export formats
- Output feeds directly into the Interview Transcript Semantic Chunker notebook

### 2.2.0 — 2026-07-18
- Added a `doctor` module (`ai-anthro-doctor` / `python -m ai_anthro_toolkit.doctor`) that probes each data source from the current network and reports reachable vs. blocked, with per-source Colab fallbacks
- Added `AGENTS.md` and `GEMINI.md` repository instructions so coding agents (Codex CLI, Gemini CLI, and other AGENTS.md readers) follow the same fallback chain as Claude Code: MCP tools when present, the installed Python API in sandboxes, Colab notebooks otherwise
- Added a "Coding Agents & Sandboxes" section to the README

### 2.1.1 — 2026-07-18
- Documentation and consistency updates describing the MCP server as running data collection and analysis natively, with notebooks as the hands-on alternative
- Added consistency tests covering the tool registry, tool descriptions, and notebook/documentation parity

### 2.1.0 — 2026-07-17
- The remaining seven data sources became native MCP tools (ported from the corresponding notebooks): Google Trends, Google News, Google Patents, Google Scholar, Google Books Ngram, YouTube search and transcripts, and podcast RSS
- The MCP agent now collects this data directly instead of pointing users to a notebook; notebooks remain available as the hands-on, customizable layer
- Scraper failures now raise explicit rate-limit guidance instead of returning empty results

### 2.0.1 — 2026-07-17
- `search_openalex` gained year, journal, sort, and open-access filters
- `search_crossref` added as a second scholarly literature source
- `search_pubmed` gained date and journal filters
- Added a `list_notebooks` tool surfacing the full Colab catalog

### 2.0.0 — 2026-07-17
- The Python package and MCP server moved to the PolyForm Noncommercial 1.0.0 license (free for research, education, and nonprofit use; commercial licensing available by arrangement)
- Notebooks and documentation remain under CC BY-NC 4.0

## Claude Code Plugin

### 1.8.3 — 2026-07-19
- Added a manuscript anonymization guide to the research-writing skill, covering preparation of an anonymous manuscript for double-anonymous peer review

### 1.7.0 — 2026-07-18
- Added the applied-practice skill (19th skill) for anthropologists working in consulting, UX research, and business settings: statements of work, stakeholder readouts, insight formulation, workshop facilitation, research repositories, and portfolio case studies

### 1.6.0 — 2026-07-18
- Added the literature-review skill (18th skill): review-genre selection, search strategy, two-pass screening with audit trails, annotated bibliographies, literature matrices, and framework construction

### 1.5.0 — 2026-07-18
- Added the digital-computational-methods skill (17th skill), routing to the toolkit's computational notebooks (topic modeling, named entity recognition, text network analysis) and covering digital ethnography and AI-assisted analysis

### 1.3.0 — 2026-07-17
- Updated alongside package 2.1.0 for native data collection across seven additional sources

### 1.2.1 — 2026-07-17
- Updated alongside package 2.0.1 for expanded data-discovery filters and the `list_notebooks` tool

### 1.2.0 — 2026-07-17
- The MCP server is now bundled and installable via PyPI
