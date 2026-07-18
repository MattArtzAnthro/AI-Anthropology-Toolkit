# Computational Methods Guide

Reference file for the digital-computational-methods skill. Loaded when
matching computational text-analysis methods to a corpus and question,
and when routing to the toolkit notebooks that implement each method.

The governing principle throughout: computation extends interpretation
rather than replacing it — the "thick machine" stance in which
computational output is something to read, not a finding in itself
(Munk, Olesen, and Jacomy 2022). Every method below ends with a return
to the material.

---

## Method Selection

| Method | Use when the question is... | Corpus needs | Toolkit notebook |
|---|---|---|---|
| Topic modeling | "What thematic terrain does this corpus cover?" (exploratory) | Hundreds to millions of documents; texts long enough to carry topics (paragraph+) | [Topic Modeling (BERTopic)](https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Topic_Modeling_BERTopic.ipynb) |
| Named entity recognition | "Who, what, and where appear across this material?" (structured extraction) | Any size; benefits from consistent language | [Named Entity Recognition (GLiNER2)](https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Named_Entity_Recognition_GLiNER2.ipynb) |
| Text networks | "What co-occurs with what — how is the discourse structured relationally?" | Medium+ corpora; meaningful co-occurrence units | [Text Network Analysis](https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Text_Network_Analysis.ipynb) |
| Embedding similarity | "Which documents belong together — how should this corpus be organized or compared?" | Any size; works at chunk or document level | [Interview Transcript Semantic Chunker](https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/Interview_Transcript_Semantic_Chunker.ipynb) (chunk-level embeddings; fully local) |
| Qualitative coding at scale | "What does this material *mean* under an analytical lens?" | Any size | The qualitative-analysis skill and its pipeline — not this skill |

Corpus building: the toolkit's data-collection notebooks and MCP tools
(scholarly APIs, Google sources, YouTube, podcasts) feed all of the
above; transcription (Audio Transcription with Whisper) and semantic
chunking prepare interview material.

## Scale Honesty

- **Below ~200 documents**: careful reading and qualitative coding
  usually outperform computation. Topic models on small corpora produce
  unstable, over-interpreted topics. Route to qualitative-analysis.
- **Hundreds to low thousands**: computation as *reconnaissance* — map
  the terrain computationally, then close-read strategically sampled
  regions.
- **Tens of thousands and beyond**: computation becomes necessary
  infrastructure, but the interpretive obligations do not shrink;
  validation sampling grows more important, not less.

## Per-Method Guidance

### Topic Modeling

- Modern transformer-based approaches (BERTopic) cluster document
  embeddings rather than modeling word co-occurrence; they handle short
  texts better than classical LDA but still reward longer units.
- Decisions to report: embedding model, minimum topic size, whether
  zero-shot topics were seeded, how outliers were handled.
- **Validation**: read the top documents (not just top words) for every
  topic that enters the analysis; name topics only after reading;
  report the proportion of the corpus left as outliers.
- Failure smell: topics that are artifacts of format (boilerplate,
  greetings) rather than content — clean before modeling.

### Named Entity Recognition

- Zero-shot NER (GLiNER2) accepts custom entity types — design the type
  set from the research question (e.g., "healing practice," "kin term,"
  "institution"), not just the default person/place/organization.
- **Validation**: hand-check a sample per entity type; report precision
  informally if the counts carry analytic weight.
- Extraction output is a *view* of the corpus, useful for indexing,
  sampling, and de-identification prep — not itself an interpretation.

### Text Networks

- Co-occurrence networks make discourse structure visible: which terms,
  actors, or codes travel together. Communities and centrality suggest
  where meaning concentrates.
- Decisions to report: unit of co-occurrence (sentence, paragraph,
  document), edge thresholds, layout algorithm — all shape what the
  picture shows.
- **Validation**: for any edge or cluster given analytic weight, read
  the passages that produced it.
- Exports travel to Gephi (GEXF) for deeper network analysis.

### Embedding Similarity

- Sentence-transformer embeddings (as in the Semantic Chunker — fully
  local, no API) support similarity search, clustering, and
  organization of material at chunk level; the same logic scales to
  document collections.
- Similarity is a model's judgment shaped by its training, not a neutral
  fact — treat clusters as candidate groupings for interpretive review.

## Integration Pattern

The strongest designs run computation and interpretation as a loop:
compute to map, sample from the map, code the samples under an explicit
lens (qualitative-analysis pipeline), and let what the coding finds
reshape the next computational pass. Computation and thick description
as complementary impulses, not rivals (Munk and Winthereik 2022; Breslin
and Albris 2026).

## Citations

- Breslin, Samantha, and Kristoffer Albris. 2026. "Computational
  Anthropology." In *Handbook of Digital and Computational Research
  Methods*. Cheltenham: Edward Elgar.
- Munk, Anders Kristian, Asger Gehrt Olesen, and Mathieu Jacomy. 2022.
  "The Thick Machine: Anthropological AI between Explanation and
  Explication." *Big Data & Society* 9(1).
  https://doi.org/10.1177/20539517211069891
- Munk, Anders Kristian, and Brit Ross Winthereik. 2022. "Computational
  Ethnography: A Case of COVID-19's Methodological Consequences." In
  *The Palgrave Handbook of the Anthropology of Technology*. Singapore:
  Palgrave Macmillan.
- Venturini, Tommaso, Mathieu Jacomy, and Torben Elgaard Jensen. 2021.
  "What Do We See When We Look at Networks?" *Big Data & Society* 8(1).
  https://doi.org/10.1177/20539517211018488
