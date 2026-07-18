---
name: literature-review
description: >
  Use this skill whenever a user needs to find, screen, organize, or
  synthesize scholarly literature — literature reviews, annotated
  bibliographies, literature matrices, systematic or scoping reviews, or
  building a theoretical or conceptual framework from sources. Triggers
  include: "literature review," "lit review," "review the literature,"
  "annotated bibliography," "literature matrix," "synthesize these
  papers," "systematic review," "scoping review," "PRISMA," "screen these
  abstracts," "research gap," "theoretical framework," "conceptual
  framework," "organize my sources," "what does the literature say."
  Covers review-type selection, search strategy and logging, screening
  with audit trails, annotation and matrix construction, and framework
  development. Do NOT use for formulating research questions (use
  research-question), writing the article or chapter prose (use
  research-writing), or collecting non-scholarly data (use
  digital-computational-methods).
---

# Literature Review & Evidence Synthesis

Guide the full arc from scattered sources to synthesized argument:
choosing the right review genre, searching systematically, screening
with an audit trail, extracting into structured forms (annotated
bibliography, literature matrix), and building the theoretical or
conceptual framework the study will stand on. The unifying principle:
a literature review is an argument about a field, not a pile of
summaries — every stage exists to turn vertical reading (paper by
paper) into horizontal synthesis (across papers, by theme, method, and
theoretical stance).

## Quick Reference

| Task | Reference |
|------|-----------|
| Choosing a review type; search strategy, logging, and the toolkit's literature tools | Read [references/search-and-review-types.md](references/search-and-review-types.md) |
| Screening with audit trails, annotated bibliographies, literature matrices | Read [references/screening-and-synthesis-guide.md](references/screening-and-synthesis-guide.md) |
| Theoretical vs. conceptual frameworks and how to build one | Read [references/framework-construction-guide.md](references/framework-construction-guide.md) |

## Workflow

### Step 1: Establish the Review's Genre and Purpose

Read [references/search-and-review-types.md](references/search-and-review-types.md)
before searching. Ask what the review must *do* for the project:

- **Narrative–theoretical review** (the anthropological default):
  positions the study within ongoing scholarly conversations, traces
  concepts genealogically, and builds toward a framework. Selection is
  purposive and argued, not exhaustive.
- **Scoping review**: maps what exists across a broad or emerging area
  — how much, of what kind, using which methods — without appraising
  every study in depth.
- **Systematic review**: answers a focused question by exhaustively
  identifying, screening, and appraising all relevant studies under a
  registered protocol (PRISMA). Common in applied, medical, and policy
  anthropology; rarely the right default for interpretive projects.

The genre determines everything downstream: search exhaustiveness,
screening formality, and what counts as done.

### Step 2: Search Systematically and Log Everything

- Build the search from the research question's concepts plus their
  variants (synonyms, subfield vocabularies, spelling variants).
- Use the toolkit's literature tools where available — the
  ai-anthropology MCP tools (`search_openalex`, `search_crossref`,
  `search_pubmed`, `search_google_scholar`) or the corresponding Colab
  notebooks — and complement database search with citation chasing
  (backward through reference lists, forward through cited-by) and
  grey literature where the field lives outside journals.
- **Log every search**: database, exact query, filters, date run,
  record count. A review that cannot state how it searched cannot
  defend what it found. Note preprints as preprints.

### Step 3: Screen with an Audit Trail

Read [references/screening-and-synthesis-guide.md](references/screening-and-synthesis-guide.md).

- Define inclusion and exclusion criteria *before* screening, from the
  review's purpose — then apply them in two passes: title/abstract,
  then full text.
- Record every exclusion with its reason. For systematic reviews,
  track counts at each PRISMA stage; for narrative reviews, a lighter
  decision log still pays for itself at the writing stage.
- **Disclose AI assistance**: when a model helps screen or extract,
  the write-up must say which tool, how it was configured, and how its
  recommendations were human-verified — this is a PRISMA 2020
  requirement and good practice in every genre. Never let the model's
  screening judgment stand unreviewed.

### Step 4: Annotate and Extract

- Build the **annotated bibliography** as an analytical instrument,
  not a formality: each entry gets a summary (aims, methods, findings),
  an evaluation (credibility, limitations, evidentiary weight), and a
  reflection (what it does for *this* project).
- Build the **literature matrix** in parallel: one row per source,
  columns for citation, question, theoretical orientation or lens,
  design and sample, key concepts, findings, and relevance to the
  study. The matrix is what turns reading into synthesis — patterns,
  conflicts, and gaps appear down its columns, not within its rows.

### Step 5: Synthesize

Work from the matrix, not from memory of the papers:

- Group by theme, debate, and theoretical commitment — not by paper.
- Name the disagreements: where findings conflict, ask whether the
  conflict is empirical (different populations, periods, methods) or
  theoretical (different assumptions about what counts).
- State the gaps precisely: a gap is not "little research exists" but
  "existing work assumes X, has not examined Y under conditions Z."
- Sample-check every claim against its source before it enters the
  synthesis — verbatim quotes carry page numbers; paraphrases stay
  faithful.

### Step 6: Build the Framework

Read [references/framework-construction-guide.md](references/framework-construction-guide.md).

- **Theoretical framework**: an existing theory (or theories) adopted
  to interpret the phenomenon — it drives the questions and the
  methods.
- **Conceptual framework**: the researcher's own synthesis of concepts
  and relationships, built when no single theory covers the study's
  terrain.
- Construct in three movements: delimit the phenomenon and gather
  evidence; extract concepts and map their relationships; verify
  internal consistency and render the framework as diagram plus
  narrative. Every element must trace back to the matrix.

## Guardrails

- **Never fabricate or embellish citations.** Every reference must
  correspond to a real, verified source — check DOIs resolve, verify
  metadata against the databases, and flag any source the model
  "remembers" but cannot verify. A hallucinated citation is the single
  fastest way to destroy a review's credibility.
- **Read before citing.** No source enters the synthesis on the
  strength of its abstract alone; if only the abstract was read, the
  write-up says so.
- **Selection is an argument.** In narrative reviews, justify what is
  in and what is out; purposive is not the same as arbitrary.
- **Disclose AI participation** in searching, screening, or extraction
  as a methods fact, with human verification described.
- **Preprints are labeled as preprints**, and retraction status is
  worth checking for load-bearing sources.

## Common Failure Modes

**Serial summarizing.** One paragraph per paper, in sequence, with no
cross-referencing — a book report, not a review. The cure is the
matrix: synthesis reads down columns, across studies.

**The annotated bibliography as endpoint.** Annotations that only
describe ("this study examined...") without evaluation or reflection
do none of the analytical work the format exists for.

**Matrix without synthesis.** A beautifully complete matrix that is
never read for patterns — extraction is preparation, not conclusion.

**Framework as literature dump.** A "framework" section that lists
theories without committing to relationships among concepts. A
framework makes claims; it can be drawn.

**Faux-systematic claims.** Calling a purposive narrative review
"systematic" — the word is a protocol claim, not a compliment. Use the
genre's real name and meet its real standard.

**Unverified citations.** Accepting model-recalled references without
resolution against a database. Verify, then cite.

## Examples

**Example 1: Dissertation literature review**

Input: "I need to do the literature review for my dissertation on
medical pluralism in urban Ghana."

Output approach: Narrative–theoretical genre. Search OpenAlex/CrossRef
for medical pluralism + regional and conceptual variants; chase
citations from the field-defining pieces; log queries. Screen
purposively with a decision log; build annotated bibliography and a
matrix with a theoretical-orientation column; synthesize by debate
(e.g., pluralism as system vs. as practice); build toward the
theoretical framework the analysis will use.

**Example 2: Systematic review in applied anthropology**

Input: "We're doing a systematic review of community health worker
interventions for a policy client."

Output approach: PRISMA genre. Define criteria and protocol first;
parallel database searches with logged queries and counts;
deduplicate; two-pass screening with per-exclusion reasons and stage
counts for the flow diagram; disclose any AI-assisted screening with
verification procedure; extract into the matrix; synthesize with
attention to intervention heterogeneity.

**Example 3: From matrix to framework**

Input: "I've read forty papers on platform labor. How do I turn this
into a conceptual framework?"

Output approach: Read the framework-construction guide. Extract
recurring concepts from the matrix; classify relationships (what
shapes what, what mediates); commit to a diagram with narrative
justification; verify every element traces to sources; identify which
relationships are well-evidenced versus the study's own contribution.
