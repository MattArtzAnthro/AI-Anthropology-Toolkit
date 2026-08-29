# Screening, Annotation, and the Literature Matrix

Reference file for the literature-review skill. Loaded when screening
retrieved records and extracting them into annotated bibliographies and
literature matrices.

---

## Screening with an Audit Trail

### Criteria first

Define inclusion and exclusion criteria before screening begins,
derived from the review's purpose: population/setting, phenomenon,
study types, period, languages. Write them down; screening against
criteria invented mid-stream is post-hoc rationalization.

### Two-pass screening

1. **Title/abstract pass**: fast, inclusive — when in doubt, keep for
   full text. Record each exclusion with a one-line reason.
2. **Full-text pass**: read the surviving records; exclude with
   explicit reasons ("wrong population," "no empirical material,"
   "concept used only in passing"). If a full text cannot be obtained,
   log it as *not retrieved* rather than silently dropping it.

### The audit trail

For systematic reviews, track counts at every PRISMA 2020 stage —
identified, deduplicated, screened, retrieved, assessed, included —
separately for database results and other sources (citation chasing,
expert recommendation). The counts feed the flow diagram; the
per-record reasons feed the methods section. For narrative reviews, a
lighter decision log (source, in/out, reason) still pays for itself
when a committee member asks "did you consider X?"

Where a reference-manager MCP server is connected (Zotero servers are
the common case), persist screening state there: collections for
stages, tags for exclusion reasons, notes for decisions. Otherwise
keep the trail in files (CSV log alongside the search log). Either
way, the trail lives outside the conversation — a screening decision
that exists only in chat history does not exist.

### Screening when the unit is a book

Anthropology's screening pain point is that much of the field's conversation
happens in monographs and edited-volume chapters — records that arrive
without abstracts, often without database entries, and at a length that
makes "full-text screening" a different activity:

- **Title/abstract pass substitutes:** for books, screen on publisher
  description, table of contents, introduction, and book reviews (reviews
  in the discipline's journals function as expert abstracts — use them).
- **Log book screening honestly:** "screened on introduction and chapters
  3–4" is a defensible, recordable decision; pretending the whole
  monograph was read is not.
- **Edited volumes disaggregate:** the screening unit is the chapter, with
  the volume logged as its source; a volume can contribute one essential
  chapter and eleven exclusions.
- **Criteria translate differently:** "wrong population" logic built for
  clinical studies misfires on ethnography, where sites are singular by
  design — the workable criterion is whether the case speaks to the
  review's concepts, not whether it samples the same population.
- **Coverage claim scales down:** database-exhaustive claims cannot be made
  for book literatures; state the strategy instead (databases + citation
  chasing + press catalogs + review essays) and its known limits.

### AI-assisted screening must be disclosed

PRISMA 2020 requires that automation used in screening be reported:
which tool, what version and configuration, and how its judgments were
verified by humans. Apply the same standard in every genre. The
workable pattern: the model proposes include/exclude with reasons; the
researcher reviews all exclusions (or a stated sample plus every
borderline); the write-up reports both the assistance and the
verification.

## The Annotated Bibliography

Three annotation registers, combined per entry (rather than choosing
one):

1. **Summary** (2–4 sentences): aims, methods, sample/site, core
   findings. Written from the text, not the abstract.
2. **Evaluation** (1–2 sentences): credibility, design limitations,
   generalizability, where the evidence is thin.
3. **Reflection** (1–2 sentences): what this source does for the
   present project — supports, complicates, provides a method, marks a
   boundary.

Descriptive-only annotations are the format's failure mode: they defer
all the analytical work to a later self who no longer remembers the
paper. Store annotations with the sources (reference-manager notes) or
in one document keyed by citation.

## The Literature Matrix

The matrix transposes vertical reading into horizontal synthesis
(Garrard 2020): one row per source, consistent columns, patterns read
down the columns.

### Anthropology-adapted columns

| Column | Notes |
|---|---|
| Citation | Verified, with DOI |
| Research question / aim | As the authors state it |
| Theoretical orientation / lens | The distinctive anthropological column — practice theory, political economy, ontological, STS, etc. (see the canonical lens list in the toolkit's DESIGN.md) |
| Design, site, and sample | Method, fieldwork duration, who/where |
| Key concepts | The terms doing analytical work |
| Findings / claims | Core empirical and theoretical claims |
| Relevance to this study | Supports / complicates / gap it leaves |

Add domain columns as the question demands (population, intervention,
outcome for applied work; period and region for historical work).

### Reading the matrix

- **Down the lens column**: which theoretical commitments dominate the
  field, and what does each make visible or invisible?
- **Down the findings column**: where do results conflict — and is the
  conflict empirical (different sites, periods, methods) or
  theoretical (different assumptions about what counts as the
  phenomenon)?
- **Across the gaps**: a defensible gap statement names what existing
  work assumes, what it has not examined, and under what conditions —
  not merely "little research exists."

The matrix lives as a spreadsheet (CSV/Excel) so it can be sorted,
filtered, and — when useful — handed to the toolkit's analysis
pipeline: matrix rows chunk naturally, and the qualitative-analysis
skill can code a large corpus of extracted findings under an explicit
lens.

## Citations

- Garrard, Judith. 2020. *Health Sciences Literature Review Made Easy:
  The Matrix Method*. 6th ed. Burlington, MA: Jones & Bartlett.
- Page, Matthew J., et al. 2021. "The PRISMA 2020 Statement: An
  Updated Guideline for Reporting Systematic Reviews." *BMJ* 372: n71.
