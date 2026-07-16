# Notebook Pipeline Guide

Reference file for the AI Anthropology Toolkit's computational analysis
notebooks. Loaded by the qualitative-analysis SKILL.md when the user's
corpus, reproducibility needs, or multi-lens design make notebook-based
analysis preferable to conversational analysis.

The notebooks live in the toolkit repository's `notebooks/` directory and
run in Google Colab: https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit

---

## The Pipeline

Three notebooks chain into a complete transcript-to-themes workflow. Each
also works standalone.

```
Interview Transcript          Qualitative                Coding and
Semantic Chunker      ─────►  Codebook Builder   ─────►  Thematic Analysis
(transcripts → chunks)        (literature → codebook)    (chunks + codebook →
                                                          codes → themes)
```

### 1. Interview Transcript Semantic Chunker

Segments interview transcripts into semantically coherent chunks for
downstream coding.

- **Input:** Raw transcripts (PDF, DOCX, TXT), with or without speaker
  labels and timestamps.
- **How it works:** Sentence embeddings identify topic shifts; boundaries
  respect speaker turns; each chunk receives a coherence score so
  low-coherence chunks can be reviewed manually.
- **Output:** CSV/JSON of chunks (`chunk_id`, `text`, `speaker`, coherence
  score, source file) — the exact input format the coding notebook expects.
- **Choose it when:** transcripts are long enough that hand-segmentation is
  impractical, or when segmentation decisions need to be reproducible and
  documented.

### 2. Qualitative Codebook Builder

Builds codebooks from source literature with AI-assisted code generation and
validation.

- **Input:** Academic source documents, an analytical lens selection, and
  quality thresholds.
- **How it works:** Extracts candidate codes from the literature under
  lens-specific prompting, then refines them: completeness validation,
  semantic-similarity distinctness checks, deduplication, definition
  synthesis, and example selection. Supports generating codebooks under
  multiple analytical lenses in parallel for epistemically plural designs.
- **Output:** Structured code entries (label, definition,
  inclusion/exclusion criteria, examples) exported as CSV, JSON, Markdown,
  and QDPX, with an NVivo import guide as fallback.
- **Choose it when:** the codebook should be grounded in a defined body of
  literature, when code quality checks (distinctness, completeness) need to
  be explicit, or when the design calls for parallel lens-specific
  codebooks.

### 3. Coding and Thematic Analysis

Applies codes to chunked data and builds themes.

- **Input:** Chunked transcripts (from the Chunker or equivalent) plus one
  or more codebooks (from the Codebook Builder or equivalent CSV).
- **How it works:** Deductive coding against the codebook, inductive
  discovery of codes the codebook missed, hybrid integration with per-chunk
  status tracking, code frequency and co-occurrence analysis, and AI-assisted
  theme building under the governing analytical lens. With multiple
  lens-specific codebooks, coding passes run per lens and results are
  compared across lenses — per-chunk agreement, consensus and divergent
  codes, and convergence tagging of themes.
- **Output:** Coded data with status tracking, frequency and co-occurrence
  tables, themes with constituent codes, and reports exported to Excel,
  Word, JSON, and HTML.
- **Choose it when:** the corpus is too large to code conversationally, the
  analysis must be re-runnable end to end, or the design compares multiple
  lenses over the same data.

---

## Choosing a Tooling Mode

| Situation | Recommendation |
|-----------|----------------|
| A handful of short documents, exploratory | Conversational analysis in-session; apply the coding-workflow-guide directly |
| Dozens of transcripts, defined codebook, reproducibility matters | Notebook pipeline |
| Multi-lens parallel design | Notebook pipeline (lens-specific codebooks + cross-lens comparison) |
| Team already works in NVivo/MAXQDA/ATLAS.ti | Build the codebook (conversationally or via notebook), export QDPX, code in the QDA application |
| Highly sensitive data, no cloud processing permitted | Chunker runs fully locally; for coding, prefer conversational or QDA-software analysis and flag consent scope to the ethics skills |

Practical notes for advising users:

- The notebooks run in Google Colab; the coding and codebook notebooks call
  the Claude API and require the user's Anthropic API key. Data sent to an
  API is a disclosure event — check consent scope first.
- Notebook outputs are designed to chain: Chunker output loads directly into
  the coding notebook; Codebook Builder CSVs carry the lens in a `stance`
  column the coding notebook reads.
- Keep the human in the loop at each stage boundary: review chunk
  boundaries and coherence flags before codebook application, review the
  codebook before coding, and review machine-proposed themes against the
  evidence before reporting them.
