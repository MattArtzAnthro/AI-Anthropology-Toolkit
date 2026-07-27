# Changelog

All notable changes to the AI Anthropology Toolkit are documented here. Dates are UTC.

This project has two release tracks: the `ai-anthropology-toolkit` Python package (notebooks, MCP server, data-collection tools; published to PyPI) and the Claude Code plugin (skills, agents, MCP registration). Versions are tracked separately below.

## Package (`ai-anthropology-toolkit` on PyPI)

### 3.1.0 — 2026-07-27
- toolkit_info now carries a companion_plugins field listing tools the toolkit hands off to
  rather than duplicating — first entry: gephi-network-analysis (network analysis in live Gephi
  Desktop), with its capabilities, repository, and the fallback when it is absent — so an
  orchestrating model can route network-analysis execution even in hosts where the companion's
  own skills are not loaded

### 3.0.0 — 2026-07-27
- BREAKING: start_coding_job now requires a ratification_id and refuses a codebook the researcher
  has not ratified. The gate implements the toolkit's Friction by Design conventions server-side:
  an unratified codebook never governs a coding pass, because every downstream claim inherits its
  authority from that decision
- Added the ratify_codebook tool (25th tool): records the researcher's confirm-or-revise decision
  for a codebook job or externally supplied records, with an optional note for what was changed or
  rejected on review, and returns a ratification_id bound to an order-insensitive content checksum
  over code labels and definitions — so revising after ratification is ordinary and simply means
  re-ratifying what actually runs
- The gate enforces sequence, not sincerity: the server verifies that a ratification event preceded
  coding and that the ratified content is what runs; it cannot verify that the researcher read the
  codebook, and its error messages instruct the orchestrating model to surface the question rather
  than answer it
- Server instructions and tool docstrings carry the gate protocol; api and delegated modes are
  gated identically

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

### 1.15.0 — 2026-07-27
- tool-building now covers the instrument that breaks after it shipped. New repair discipline
  (references/repair-discipline.md): the repair's first artifact is a reproduction check that fails
  on the broken instrument for the observed reason; a triage sorts assertion failures (defect) from
  setup errors (the environment changed) from reproductions that pass (misdiagnosis, or the source
  changed — a specification question for the researcher, not a patch); the repair loop refines on
  movement and pivots on a repeated failure, bounded at three dead hypotheses before the question
  returns to the researcher; checks stay locked during repair — weakening one to let a patch pass
  is a specification change only the researcher makes; and every repaired defect closes as a
  one-line class-level rule in the decision record, so a researcher's instruments stop repeating
  each other's defects
- The reproduction-first rule is inherited from software engineering practice (fail-to-pass
  reproduction tests in automated program repair) and restated in research terms, per the library's
  convention of crediting inherited techniques
- Two new failure modes (patching before reproducing; repairing the code when the world changed),
  a repair pressure scenario in the gate-holding evals, a repair routing prompt, and a repair
  example on the tool-builder agent

### 1.14.0 — 2026-07-27
- Added the ethnographic-generalization skill (22nd): the move from confirmed findings to the
  broader claim they can support. Covers the kinds of generalization (analytic, theoretical,
  transferability, middle-range, case-to-case) and the within-case and extended-case pathways,
  emic-to-etic translation with a what-is-lost column, disconfirmation logs and rival
  explanations, comparison discipline for connected sites (diffusion / common context /
  co-variation), scope conditions specific enough to fail, confidence calibration, and an
  ethics-at-scale check before any claim ships. Produces a claim record that hands the claim
  to paper-planning as the candidate thesis
- The skill adopts the Friction by Design conventions at Tier 1: what a case is a case of, the
  kind of generalization, the scope conditions, and the confidence level are gated as the
  researcher's decisions; the machine assembles evidence, drafts candidates, and keeps the record
- analysis-advisor now carries the generalization arc as the analysis lifecycle's exit:
  new draw-on entry, a process step for dispatching the skill, and a fourth routing example
- qualitative-analysis (theme confirmation) and paper-planning (Phase 1) carry body-level
  handoffs to the new skill in both directions

### 1.13.0 — 2026-07-27
- digital-computational-methods now hands network-analysis execution to the
  gephi-network-analysis companion plugin when it is installed — text-network construction,
  layouts, centrality and communities, structural claim verification — and otherwise offers the
  install or falls back to the Text Network Analysis notebook and a GEXF export. The handoff
  lives in the skill body, not the description, so the companion keeps winning its own routing
  triggers, and the validation obligation (read the passages behind any edge given analytic
  weight) travels with it
- skills/DESIGN.md records the cross-plugin handoff convention: body-level placement,
  capabilities named rather than versions pinned, presence checked in the session, and a
  fallback for when the companion is absent
- README gains a Companion Plugins section

### 1.12.2 — 2026-07-27
- The tool-building skill now carries the order of checks and code: for record-checkable steps,
  acceptance checks are written from the ratified specification and seen to fail once before any
  implementation exists, because a check that has never failed proves nothing — the same reason an
  unpiloted interview guide proves nothing about what it can elicit
- Three failure patterns of machine-written verification are named in the verification-modes
  reference: the instrument that grades its own work (checks written alongside code mirror the
  code, like a codebook validated only by its author), the check bent to fit (checks freeze at
  ratification, and changing one mid-implementation is a specification change that returns to the
  researcher), and the green suite that was never red (break each guarded thing once and watch its
  check fire before trusting the suite)
- Implementation attempts are bounded: failure to reach green within a few tries is read as a
  specification finding or a sort misclassification, and it returns to the researcher rather than
  fueling a longer chase
- For interpretation-dependent steps the pass/fail prohibition stands unchanged; the order
  discipline survives in one form — adjudication samples and disconfirming cases are chosen before
  the artifact exists, because a sample selected after seeing output drifts toward what the
  instrument handles well
- The discipline is the builder's obligation, never the researcher's burden: checks are written
  unasked for every record-checkable step, the researcher is told once in plain language what is
  happening and why, and is never asked to write, read, or approve test code — the researcher who
  does not know to ask for tests is exactly who the order protects
- The decision record now requires a red-run section (each check with its observed first failure,
  dated before implementation), enforced by the spec-pack template checks, so skipping the order
  is a visible omission rather than a silent one; later additions to a shipped instrument re-enter
  the same order
- Added a checks-before-code pressure scenario to the behavioral evals: told to skip the tests and
  implement fast, the tool-building workflow keeps the order or treats dropping the checks as an
  explicit specification change — held on its first live run

### 1.12.1 — 2026-07-27
- Cleared the wording seams left from writing the Friction by Design canon after its two carrier
  skills: paper-planning now asks the depth question in the canonical phrasing rather than its
  older variant, and the five skills that ask the depth question state that a setting already
  asked for the engagement — by the advisor that dispatched the skill — is used, not re-asked,
  matching what DESIGN.md and the advisors already said
- The canonical shared sentences are now test-guarded: Tier 1 depth sections must carry the
  default-to-asking rule and the received-setting clause verbatim, closing the silent per-skill
  drift class the earlier checks left open (headings and lead-ins were guarded; surrounding
  rules were not)

### 1.12.0 — 2026-07-27
- The Friction by Design conventions now reach every surface: AGENTS.md and GEMINI.md instruct
  non-Claude agents to honor the gates when executing skills, the /ai-anthropology:skills catalog
  names each skill's adoption tier, and /ai-anthropology:new-project honors the gates through the
  lifecycle phases and carries each phase's Unresolved items forward as the next phase's agenda
- skills/DESIGN.md now states how each surface carries the philosophy — conversational gates in
  the plugin, native analytic friction in the server and package, and cell-gated execution in the
  notebooks, where the cell boundary already stops exactly where review belongs
- The depth setting gained its carrier: an advisor agent whose engagement uses a Tier 1 skill asks
  full-pass-or-advisory once at dispatch and passes the answer into every skill invocation, so
  three skills in one session no longer each re-ask; a skill activated directly asks for itself,
  and declared variances keep their defaults. A structural check requires the carrier language of
  every advisor that draws on a Tier 1 skill
- Added behavioral gate-holding evals (tests/evals/test_gate_holding.py, run locally with
  AAT_RUN_GATE_EVALS=1 and the claude CLI; never in CI): six pressure scenarios test that Tier 1
  gates refuse to be answered through, and three compliant scenarios test the opposite failure —
  that judgments the researcher has already supplied are not re-interrogated. First run: all six
  pressure gates held; the one compliant failure was a miscalibrated rubric, corrected to permit
  fact-gathering while forbidding the re-opening of stated decisions

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
