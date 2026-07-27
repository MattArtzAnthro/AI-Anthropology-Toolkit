# Changelog

All notable changes to the AI Anthropology Toolkit are documented here. Dates are UTC.

This project has two release tracks: the `ai-anthropology-toolkit` Python package (notebooks, MCP server, data-collection tools; published to PyPI) and the Claude Code plugin (skills, agents, MCP registration). Versions are tracked separately below.

## Package (`ai-anthropology-toolkit` on PyPI)

### 2.2.3 — 2026-07-18
- Added five notebooks: World Bank Data Explorer, UN Data Explorer, BLS Labor Statistics Explorer, Multimodal Embedding Explorer, and Visual Analysis & Image Annotation
- Added a Multimodal & Visual Analysis notebook category
- Notebook catalog now serves 23 notebooks across four categories
- Hardened the three computational text-analysis notebooks, 47 fixes, recorded here late. Named
  Entity Recognition: the confidence slider did not reach the extractor, so the threshold stayed at
  the library default and values below 0.5 had no effect. Text Network Analysis: comparative
  multi-document export crashed when writing GEXF and GraphML, because list-valued source attributes
  were not serialized first; empty networks and scanned PDFs yielding no text now report honestly
  rather than raising or showing success. Across all three: PyPDF2 replaced with pypdf, spaCy calls
  batched via nlp.pipe, betweenness sampled on large graphs

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

### 1.11.0 — 2026-07-27
- Named Friction by Design as the toolkit's governing design philosophy in skills/DESIGN.md, with
  two layers: analytic friction (divergence between machine readings sustained as data, the sense
  operationalized in the analysis pipeline; slowing reasoning with machine friction remains Madsen,
  Munk, and Søltoft's documented technique) and interactional friction (gates and questions that
  withhold production where a judgment is not the machine's to make)
- The interactional layer generalizes the framework the paper-planning and tool-building skills
  already carried: a declared division of labour, depth calibrated once per engagement, questioning
  over production, record registers (an Unresolved list and an Assembled-rather-than-authored
  register), and failure modes aimed at the method itself
- Adoption is tiered because the framework's own proportionality rule forbids uniform depth: six
  skills adopt the full framework (the two carriers plus research-question, methodology-selection,
  qualitative-analysis, and academic-review), twelve adopt the division of labour and record
  registers, and three adopt nothing, with each assignment and its reason recorded in the DESIGN.md
  adoption table
- Tier 1 skills gate their core judgments: codebook ratification and theme confirmation in
  qualitative-analysis; stance, claim envelope, high-tension resolution, and method-system
  ratification in methodology-selection; the recommendation and the concede-or-contest triage in
  academic-review, which also gains a conditional confidentiality stage that fires when someone
  else's unpublished manuscript would enter the session; research-question keeps its
  draft-and-react method as a declared variance, with adoption of the question as its hard gate
- research-writing and conference-materials now route unsettled arguments to paper-planning
  instead of developing them in-house, so the planning gate cannot be bypassed from a neighboring
  skill; research-design, analysis-advisor, and writing-advisor honor the new gates
- tests/test_repo.py gains TestFrictionConvention: adoption declarations, the DESIGN.md tier
  table, and the required sections must agree in both directions, with Tier 3 checked for absence
  of ceremony; every check was mutation-tested against a deliberately broken copy before shipping

### 1.10.0 — 2026-07-26
- Added the tool-building skill (21st skill), the tool-builder agent (9th agent), and the
  /ai-anthropology:build-tool command: specification, verification, and provenance discipline for
  researchers building their own research instruments
- Version 1 supports one artifact family, Claude Code skills and agents, where the repository's
  routing evals and structure tests can genuinely reject the work
- tool-builder is the first agent in this plugin that writes files rather than advising
- Added tests/test_spec_pack.py, which enforces specification completeness and a reading check
  against fixtures rather than by convention
- Routing evals now check the margin by which each prompt wins, not only that it wins; commands and
  agents are validated as families rather than one file each; and a skill's routing clause must name
  a skill that exists, which closed a gap affecting 19 references across 6 descriptions

### 1.9.0 — 2026-07-26
- Added the paper-planning skill (20th skill), for working out what a paper argues before drafting it: claim extraction from ethnographic or archival material, testing a claim for disputability, scope, and load-bearing premises, six ways of positioning a contribution against the existing conversation, argument sequencing, and eight diagnostic vectors for an unresolved plan
- The skill proceeds by questioning rather than by producing text. It will not state an author's claim, name their contribution, or write their thesis sentence, and it calibrates the depth of interrogation to what the author could plausibly get wrong rather than applying uniform depth
- writing-advisor now orchestrates paper-planning alongside research-writing and academic-review, and routes to argument planning before structural work when a claim is unsettled
- Sharpened the applied-practice description with "scope of work" and "client engagement" triggers, which were routing to career-statements

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
