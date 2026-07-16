---
name: qualitative-analysis
description: >
  Use this skill whenever a user needs help coding qualitative data, building
  a codebook, or conducting thematic analysis for anthropological research.
  Triggers include: "code my interviews," "qualitative coding," "codebook,"
  "thematic analysis," "themes," "deductive coding," "inductive coding,"
  "hybrid coding," "code frequencies," "co-occurrence," "intercoder
  reliability," "analyze my transcripts," "analyze my field notes,"
  "AI-assisted coding," "NVivo," "MAXQDA," "QDPX," or "how do I analyze my
  qualitative data." Covers codebook development from literature or data,
  applying codes (deductive, inductive, hybrid), building themes from coded
  data, multi-lens parallel analysis, and quality validation. Bridges to the
  toolkit's computational notebooks (Semantic Chunker, Codebook Builder,
  Coding and Thematic Analysis). Do NOT use for designing data collection
  instruments (use fieldwork-methods skill), method selection (use
  methodology-selection skill), or writing up findings (use research-writing
  skill).
---

# Qualitative Analysis & Coding

Guide qualitative coding, codebook development, and thematic analysis for
anthropological research — from raw transcripts and field notes to themes
ready for writing. Analysis in this tradition is an interpretive act, not a
counting exercise: codes are claims about what matters in the data, and the
epistemic stance (or analytical lens) governing the analysis shapes what the
coder attends to. Treat AI assistance as a way to scale and systematize
interpretation while keeping interpretive authority with the researcher.

## Quick Reference

| Task | Reference |
|------|-----------|
| Codebook construction, coding passes, theme building, quality validation | Read [references/coding-workflow-guide.md](references/coding-workflow-guide.md) |
| The toolkit's computational pipeline (Semantic Chunker → Codebook Builder → Coding and Thematic Analysis notebooks) | Read [references/notebook-pipeline-guide.md](references/notebook-pipeline-guide.md) |
| Canonical stance/lens list | See DESIGN.md (skills library root) |

## Workflow

### Step 1: Identify the Analysis Task

Determine which of these the user needs — they are distinct tasks with
different workflows:

1. **Codebook development.** Building a structured set of codes (labels,
   definitions, inclusion/exclusion criteria, examples) from source
   literature, prior theory, or the data itself.
2. **Coding.** Applying codes to data segments — deductively (from an
   existing codebook), inductively (discovering codes from the data), or
   hybrid (deductive first, then inductive discovery, then integration).
3. **Thematic analysis.** Synthesizing coded data into themes — patterned
   meanings that answer the research question — with constituent codes,
   sub-themes, and supporting evidence.
4. **Multi-lens analysis.** Running the same data through more than one
   stance/lens in parallel and comparing where the lenses converge, diverge,
   or productively conflict.

If the user says "analyze my data" without specifying, walk them through the
full arc: chunk → codebook → code → themes.

### Step 2: Gather Context

Collect before starting (ask only for what is missing):

- **Data state.** What exists: raw audio, transcripts, field notes, already
  segmented chunks, an existing codebook, partially coded data? Data format
  (PDF, DOCX, TXT, CSV) and volume (how many interviews or documents)?
- **Epistemic stance / analytical lens.** Which lens(es) will govern the
  analysis (see DESIGN.md for the canonical list). A single lens is the
  default; multi-lens parallel analysis is warranted when the project's
  claims depend on epistemic pluralism.
- **Coding approach.** Deductive, inductive, or hybrid — and why. The
  approach should follow from the research design, not from convenience.
- **Research context.** Project name, governing research question, and a
  short study description — these ground every analytic judgment.
- **Tooling mode.** Conversational analysis (working through data together in
  this session), the toolkit's computational notebooks (for large corpora,
  reproducible runs, and multi-lens parallelism), or export to QDA software
  (NVivo, MAXQDA, ATLAS.ti via QDPX). Recommend the notebooks when the corpus
  exceeds what fits comfortably in conversation; read
  [references/notebook-pipeline-guide.md](references/notebook-pipeline-guide.md)
  before advising on them.

### Step 3: Build or Refine the Codebook

Read [references/coding-workflow-guide.md](references/coding-workflow-guide.md)
before drafting codes.

Every code needs five parts: a short label, a definition, inclusion criteria,
exclusion criteria, and at least one example. Codes without exclusion criteria
drift; codes without examples cannot be applied consistently.

- Derive deductive codes from the literature and theoretical framework the
  stance makes relevant.
- Keep the codebook small enough to hold in mind — 15-40 codes for most
  projects. Consolidate semantic near-duplicates before coding begins.
- Version the codebook. Analysis decisions must be traceable to the codebook
  version in force when they were made.

### Step 4: Apply Codes

- Code at the level of meaning units (a claim, an exchange, an episode), not
  fixed word counts. If the data is not yet segmented, segment first — by
  topic shift, preserving speaker turns.
- Track code status per segment: deductive-only, inductive-only, both, or no
  codes. Segments with no codes are analytically informative — inspect them
  before dismissing them.
- For hybrid coding: complete the deductive pass first, then ask what the
  codebook failed to see. Inductive candidates must earn codebook entry with
  the same five-part structure.
- Record co-occurrences: codes that repeatedly appear together are theme
  candidates.

### Step 5: Build Themes

Themes are not piles of codes, and they are not frequency rankings. A theme
is an analytical claim about patterned meaning that answers (part of) the
research question. For each theme, state: the claim, the constituent codes,
representative evidence (verbatim quotes with source identifiers), and what
the theme contributes to the argument.

For multi-lens analysis, tag each theme by convergence: **convergent**
(appears across lenses), **lens-specific** (visible only under one lens), or
**friction** (lenses actively disagree about the same data). Friction points
are findings, not errors — they show where interpretive commitments do real
work.

### Step 6: Validate and Export

- Spot-check: for a sample of coded segments, verify the code definitions
  actually license the assignments.
- Search for disconfirming evidence for each theme before accepting it.
- Report saturation honestly: when did new data stop producing new codes?
- Export in the format the downstream workflow needs: tabular (CSV/Excel)
  for audit and co-analysis, QDPX for QDA software, structured summaries for
  writing. Every export must preserve segment-to-source traceability.

## Parameters

- **Epistemic stance / analytical lens:** All 42 stances are relevant (see
  DESIGN.md). The lens governs what codes are salient, how themes are framed,
  and what counts as evidence.
- **Coding approach:** Deductive, inductive, hybrid.
- **Tooling mode:** Conversational, toolkit notebooks, QDA software export.
- **Granularity:** Segment size (meaning units), codebook size cap, theme
  count target.
- **Output format:** Codebook (CSV/Markdown), coded data table, theme
  report, cross-lens comparison.

## Guardrails

- **Interpretive authority stays with the researcher.** AI assistance
  proposes; the researcher disposes. Never present machine-generated codes or
  themes as final without human review checkpoints built into the workflow.
- **Never fabricate quotes.** Every quoted segment must come verbatim from
  the user's data with a source identifier. If evidence for a theme is thin,
  say so — do not improvise illustrative material.
- **Provenance throughout.** Every code assignment must be traceable to a
  segment, a codebook version, and an analysis decision. An analysis that
  cannot be audited cannot be defended.
- **Frequency is not significance.** A code appearing often is not
  automatically a theme; a code appearing once may matter enormously.
  Interpretive weight, not counts, drives theme claims.
- **Privacy is a design decision.** Sending data to an API is a disclosure
  event. For sensitive data, prefer local processing and flag consent-scope
  questions to the irb-protocol and informed-consent skills.

## Common Failure Modes

**Generic codes.** Codes like "communication" or "challenges" that could come
from any qualitative project in any discipline. Anthropological codes name
cultural and relational processes with the specificity the stance demands.

**Themes that restate codes.** "Theme: Trust issues (codes: trust,
distrust)." A theme must add an analytical claim beyond its constituent
codes' labels.

**Codebook sprawl.** Sixty codes with overlapping definitions guarantee
inconsistent application. Consolidate before coding, not after.

**Single-lens defaults.** Running everything through an unexamined
interpretive default when the project's stance is actually critical,
feminist, STS, or plural. Ask which lens governs — the answer changes the
codes.

**Coding to confirm.** Applying the codebook only where it fits and ignoring
what it misses. The inductive pass and the no-code segments are where the
data pushes back.

## Examples

**Example 1: Full arc, single lens**

Input: "I have 12 interview transcripts from my fieldwork with community
health workers in Nairobi. Interpretivist project. How do I analyze them?"

Output approach: Confirm the research question and data format. Recommend the
notebook pipeline for 12 transcripts (chunking, then codebook, then coding)
or conversational analysis if the user prefers working through them together.
Build a hybrid codebook grounded in the interpretivist literature the user
is in conversation with; code with status tracking; build themes with
verbatim evidence; validate against disconfirming cases.

**Example 2: Multi-lens comparison**

Input: "My committee wants to see how my analysis would differ under a
critical lens versus an interpretivist one."

Output approach: Read the notebook-pipeline-guide reference. Use the
Codebook Builder to generate one codebook per lens with lens-specific
prompting, run a coding pass per codebook, and compare the results:
per-segment agreement, consensus codes, divergent codes, friction points.
Present convergent themes and lens-specific themes separately — the
divergence is the finding.

**Example 3: Rescue an existing analysis**

Input: "I coded everything in NVivo but my themes feel flat — they're just
my code names with more words."

Output approach: Diagnose theme-restates-code failure. Work upward from
co-occurrence patterns and downward from the research question: what claim
about patterned meaning would answer it? Rebuild themes as analytical claims,
attach constituent codes and disconfirming evidence, and check each theme
against the stance's account of what counts as significance.
