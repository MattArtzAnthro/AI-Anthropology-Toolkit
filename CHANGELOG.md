# Changelog

All notable changes to the AI Anthropology Toolkit are documented here. Dates are UTC.

This project has two release tracks: the `ai-anthropology-toolkit` Python package (notebooks, MCP server, data-collection tools; published to PyPI) and the Claude Code plugin (skills, agents, MCP registration). Versions are tracked separately below.

## Package (`ai-anthropology-toolkit` on PyPI)

### 3.7.0 — 2026-08-28
- **Migrated to MCP Python SDK 2.x** (`mcp>=2.1,<3`): `FastMCP` is now `MCPServer`, and the
  server reports the package version in `serverInfo`. The SDK serves both the 2026-07-28
  protocol and the 2025-era `initialize` handshake that Claude Code, Claude Desktop, Codex CLI,
  and Gemini CLI send today, so clients need no change. Why now: SDK 2.0.0 removed
  `mcp.server.fastmcp`, and any launcher that resolved the SDK freshly against an older
  package series (for example a Claude Desktop entry still pinned to `2.0.*`) failed at import
  with `No module named 'mcp.server.fastmcp'`. Releases from 3.6.0 back carried a `<2` bound and
  keep working; this release moves the server onto the line the SDK maintains.
- Citation formatting, as `format_citation` and `list_citation_styles` (MCP) and
  `ai_anthro_toolkit.datasources.citation` (Python). Wraps the DOI Foundation's formatter at
  citation.doi.org, which renders Crossref, DataCite, and mEDRA metadata through the Citation
  Style Language. This closes a gap the toolkit had left open: `search_crossref` returns
  metadata fields, and a reference manager formats what is already in the library, but nothing
  rendered a finished citation from a bare DOI for a source the researcher does not hold.
- The formatter ships thousands of styles and rejects near-misses rather than approximating,
  so `list_citation_styles` is the lookup step, not a catalog: it filters by substring, reports
  how many matched, and marks truncation rather than trimming silently. Anthropology's styles
  are all present, `american-anthropological-association` and
  `journal-of-the-royal-anthropological-institute` among them.
- `format_citation` formats and does not verify, and both its docstring and the server
  instructions say so. Registrar metadata is wrong in specific, recurring ways — titles mangled
  by PDF extraction, chapters carrying their book's title, deprecated `dx.doi.org` URLs — so
  the rendered text is returned verbatim apart from stripped surrounding whitespace, and is
  handed on as a draft to check against the source rather than as evidence about it.
- HTML entities are decoded before the citation is returned. The formatter escapes ampersands,
  so a journal title such as *Science, Technology, & Human Values* arrives as `&amp;` and would
  otherwise reach a manuscript that way. That decoding and a whitespace strip are the only
  changes made to the formatter's rendering; deprecated `dx.doi.org` URLs are left as emitted,
  because silently rewriting citation text is worse than reporting it.
- `format_citation_batch` renders a whole reference list in one call, in input order, and
  returns `formatted` alongside `failed` so one unresolvable DOI never discards the rest. It is
  deliberately not called a bibliography: the formatter renders one DOI per request, so this
  cannot sort to a style's rules or disambiguate two works by one author in one year, and both
  the docstring and the tool description say so rather than letting the name imply it.
- Whitespace runs collapse to single spaces. Registrar metadata routinely carries the newlines
  and indentation of the XML it was pretty-printed into, so an openRxiv title arrives as
  "Nearly Neutral Evolution Across the\\n                  Drosophila melanogaster\\n
  Genome" and a `.strip()` leaves the break mid-title. Verified first that no CSL style emits an
  internal newline of its own, annotated bibliographies included, so the collapse cannot destroy
  a rendering the formatter meant.
- Refusals now carry the formatter's own reason instead of a reason inferred from the status
  code. The API returns 400 and 404 for several causes and does not evaluate DOI and style in a
  fixed order — the same unsupported format name comes back as "Unknown style ris" for one DOI
  and as a metadata error for another. The distinction that earns this: a DOI that is registered
  but momentarily unformattable was being reported as unregistered, which tells a researcher a
  real reference is fake. Rate limiting and 5xx now raise `RuntimeError` naming the formatter
  rather than the DOI.
- Unknown styles raise a typed `UnknownStyleError` rather than a `ValueError` the batch
  identifies by searching its message. The string coupling broke the moment the wording changed,
  and the batch silently began recording one style error as a per-row failure on every entry.
- The two refusal paths stay distinguishable: an unregistered DOI and an unknown style raise
  different messages, and the style error names the tool that returns exact names. DOIs are
  accepted bare, `doi:`-prefixed, or wrapped in a doi.org or dx.doi.org URL; suffix case is
  preserved, because registrar metadata does not always treat it as insignificant.
- `toolkit_info` no longer claims that every capability also exists as a Colab notebook. It did
  not: the methodology, documents, and checks families had none before this release and citations
  makes a fourth, so a researcher choosing the toolkit because any capability can be inspected in
  Colab was choosing on a false premise. The claim now states which families are server-side only,
  and two tripwires in `tests/package/test_consistency.py` reject absolute quantifiers in it and
  flag the day a notebook is added for one of those families.
- `python -m ai_anthro_toolkit.doctor` now probes the formatter as a twelfth source, so a
  sandboxed agent learns it is unreachable rather than discovering it mid-task.

### 3.6.0 — 2026-08-12
- `compare_lenses` overhauled so that every claim in its output is decidable from the data it
  presents. `consensus_codes` now requires co-location — a code is consensus only where every
  lens applied it to at least one common chunk, with those chunks reported in
  `consensus_co_applied_chunks`. Previously the intersection was corpus-level: two lenses that
  applied the same label to entirely disjoint chunks were reported as consensus, which is a
  claim the data does not support. Labels every lens used without ever co-applying now report
  as `shared_vocabulary_codes`. This changes the meaning of an existing key on purpose.
- Agreement is now computed over deductive codes only. Inductive discoveries are per-lens:
  the old math compared them across lenses as bare strings, so one lens's inductive TRUST
  matched another's deductive TRUST — while the integrated code sets suffixed them apart.
  They now report per lens in `inductive_codes_by_lens` and appear `_IND`-suffixed in point
  payloads, never in scores or tiers.
- An absent record is no longer scored as disagreement. A record present with no codes is a
  reading ("nothing applies": 0 against a non-empty set, 1.0 against another empty set); a
  lens with no record for a chunk was never asked, and that chunk's pairs involving it are
  excluded, with per-lens `coverage` and total/compared/uncompared `chunks` counts keeping
  the exclusions visible. Records without a `chunk_id` no longer collapse silently into a
  pseudo-chunk; they are excluded and reported in structured `warnings`, alongside duplicate
  `chunk_id`s (last record governs) and cross-lens text mismatches for the same `chunk_id` —
  the last of which means the lenses may not have coded the same data.
- Friction points now carry what adjudication requires: the chunk text (capped at 500
  characters, flagged when truncated) and per-lens codes, with `code_definitions` resolved
  per lens when codebooks are supplied. A friction point that hands the researcher bare
  labels cannot support the judgment it exists to occasion.
- New `convergence_points`: the highest-agreement chunks, same payload plus `code_count`,
  surfaced for the same researcher inspection friction gets. Agreement reached too easily
  may be two meanings under one label, and the old output never surfaced it anywhere.
- Truncation is disclosed: `friction_total` and `convergence_total` report full counts,
  `params` echoes `friction_threshold` and `top_n` (both now arguments), and ties order
  lexicographically by `chunk_id`. The threshold selects attention, never existence.
- The vocabulary regime is reported, never guessed: with per-lens codebooks supplied the
  output states `shared` or `divergent` by content checksum; without them, `unknown` —
  identical label sets are not evidence of a shared codebook. The checksum is the same one
  that binds ratification to coding (`crosslens.codebook_checksum` now owns it; the server
  delegates), and coding jobs now store their `ratification_id`, which the server's
  `compare_lenses(job_ids=...)` path reports per lens.
- Friction and convergence partition attention: convergence candidates sit at or above the
  friction threshold, so no chunk is ever surfaced as both a friction finding and a
  convergence finding. Caught by running the old design on a small corpus, where
  top-N-descending returned the worst friction chunk inside `convergence_points`.
- The Coding and Thematic Analysis notebook now installs the package and imports
  `ai_anthro_toolkit.crosslens` instead of re-implementing the comparison — the cross-lens
  functions in the comparison stage, the multi-lens merge's per-chunk agreement, and the
  analyzer's overlap matrix all read the package result, and a drift-guard test asserts no
  local Jaccard implementation remains anywhere in the notebook. The merge now returns the
  package comparison alongside the merged frame and reports compared/uncompared chunk counts
  and data-integrity warnings in its summary.

### 3.5.0 — 2026-08-06
- OpenAlex 429s now raise `RuntimeError` carrying the server's own explanation instead of a bare
  `HTTPError`. OpenAlex answers an exhausted request budget with the same status it uses for
  ordinary rate limiting, and only the body distinguishes them: an exhausted budget says
  "Insufficient budget" and names a reset time. `raise_for_status` discards that body, so a
  researcher who could not be helped by retrying was told nothing and retried.
- The body is passed through rather than paraphrased, because the terms are OpenAlex's and have
  changed at least once. The message names the polite pool only when `mailto` was not already
  sent, since telling someone to do what they did is noise. Observed live: the budget refusal
  cleared within the hour rather than at the reset time it named, so it is intermittent rather
  than a daily wall, and the live tests skip with the reason rather than erroring.
- Added `ai_anthro_toolkit.checks.generated`: standing checks built from the researcher's own
  answers. `tool-building` Stage 4 already asks them to settle five commitments about what their
  instrument should do; until now those answers went into the specification and nothing enforced
  them. They now persist as `instrument-checks.json` beside the artifact and run whenever
  `ai-anthro-check` is pointed at it — so the checks are about the researcher's artifact rather
  than only the two classes the toolkit ships.
- An unanswered commitment generates nothing. Silence is not consent to a default, and a check
  nobody asked for is the toolkit asserting a methodological commitment about someone else's work.
- An answer that cannot be checked from the data alone is recorded as unenforceable **with its
  reason**, not dropped. Whether source order was preserved is a claim about the source and the
  output together and only the source settles it; a skipped record is absent, and absence is
  indistinguishable from a record the source never held. A researcher who settled five commitments
  and received three checks is told which two and why.
- Answers come from a fixed vocabulary, so nothing has to interpret prose to decide what a
  researcher meant — that is the judgment Stage 4 exists to route to them. An answer outside the
  vocabulary is refused, and a field-scoped answer with no field named is refused rather than
  guessed.
- The checks file is data and never code. A test asserts the module contains no `exec`, `eval`,
  `importlib`, or `__import__`, because a loader that could run what it finds in a project
  directory turns "check my data" into "run whatever is in that folder".
- Every generated check carries the mutation that should make it fire, so the
  registry-completeness guarantee extends to checks the toolkit did not write.

### 3.4.0 — 2026-08-05
- Added `ai_anthro_toolkit.checks.mutate`: one mutation per commitment the `tool-building` Stage 4
  table settles — emptiness, duplication, partial presence, unparseable values, ordering — plus a
  harness that runs a check against both the good records and the broken ones. Settling a
  commitment in a table records what the researcher intends; it does not show that the instrument
  does it, and an instrument that quietly disagrees with its own specification is worse than one
  with no specification at all.
- A check that stays quiet on good input and fires on the mutation guards that commitment. A check
  that fires on both distinguishes nothing, and one that fires on neither guards nothing. Neither
  failure is visible without running the pair.
- A raised exception counts as noticing: an instrument that crashes on a duplicate has registered
  it, however rudely, and that is worth distinguishing from silence.
- Input mutation only. Nothing mutates code, because rewriting a researcher's source produces
  mutants that do not compile and mutants semantically identical to the original. Nothing reaches
  the network, and a test asserts the module imports no network library: mutating a collector's
  rate limit and re-running it is an unsandboxed adversarial run against someone else's server and
  can get a researcher blocked from the archive they study.
- Most checks guard one commitment and are correctly silent on the other four. Results are a map
  of coverage, never a score.

### 3.3.0 — 2026-08-05
- Added standing checks over durable artifacts (`ai_anthro_toolkit.checks`), the
  `get_artifact_checks` tool (27th), and the `ai-anthro-check` console script. Seven checks over
  codebooks and coded datasets, run without being asked, because a researcher who would benefit
  from one does not request it — they do not know that is the name of the thing that would have
  saved them.
- Each check declares whether it could ever teach anything. A `mirror` check restates what was
  already specified and is epistemically empty; a `surprise-capable` check can surface a
  commitment the researcher never stated, and carries a written hypothesis about which one. A run
  in which only mirror checks executed says so, rather than reading as a second opinion.
- No check reports an all-clear on a question it cannot settle. Verdicts are confirmed, refuted,
  or cannot tell, and a check that could not run is reported as unrun rather than passed. The
  distinctness comparison returns "cannot tell" when `sentence-transformers` is absent instead of
  passing silently.
- Code distinctness is stance-gated rather than assumed. Mutual exclusivity of codes is a
  commitment grounded theory and several interpretive traditions decline, so the check runs only
  once the researcher has said it is theirs, asked once at codebook ratification.
- Inductive codes carry the `_IND` suffix and are excluded from the resolve check by
  construction; codes discovered during coding that never entered the codebook are surfaced
  separately, where they are the interesting finding rather than a false failure.
- Producers now write a provenance sidecar (`provenance.json`) beside saved codebook and coded
  artifacts, recording the codebook label set, its checksum, and the ratification id. `result.json`
  keeps its shape. Without it, an artifact that leaves its job directory makes no claim about which
  codebook it came from and the checks that need one report "cannot tell". The stanza names the
  file it describes: a sidecar sits in a directory that may hold several artifacts, and provenance
  borrowed from a neighbour is worse than none, because the checks would report on one artifact
  using another one's codebook and report it as settled.
- Every registered check declares a mutator alongside its predicate, and the suite asserts that
  each fires on its own mutation and stays quiet on a good artifact. A check registered without a
  mutator is a test failure, so the guarantee is structural rather than dependent on anyone
  remembering.

### 3.2.0 — 2026-08-01
- Added the markup module and the extract_document_markup tool (26th tool): reads comments out of
  a .docx together with the exact span each one is anchored to, plus tracked changes with author
  and a substantive flag that separates judgments about the manuscript from spelling and spacing.
  The anchor is the point of it — a comment reading "unclear" is unanswerable in the abstract and
  usually obvious once the sentence it points at is in view, and pasting a manuscript in as plain
  text discards every anchor, author, and change
- Reply threading and resolved state are read from commentsExtended.xml where it exists; its
  absence in older documents is read as absence of threading rather than as a failure
- Standard library only (zipfile, xml.etree), so it adds no dependency and installs with the base
  package. Any part declaring a DTD is refused rather than parsed: no .docx written by Word carries
  one, and refusing it closes the entity-expansion path without pulling in defusedxml
- Verified against real Word documents rather than only against synthetic fixtures: comments with
  no quotable span (Word allows attaching one to an insertion point, or to a selection containing
  only a space) report an empty anchor and fall back to the enclosing paragraph, and
  summary.unanchored_count says how many
- Read-only by design. Writing edits and resolved comments back into a .docx is out of scope,
  because tracked-change XML is easy to write in a way that opens correctly in one reader and
  breaks in Word, and the author would find out at the editor's desk
- Bounded the mcp requirement at `>=1.2,<2`. The 2.0.0 release of the MCP Python SDK removed
  `mcp.server.fastmcp`, which this server imports, so the previously unbounded requirement
  resolved to a version the server could not start under. A fresh install of any earlier release
  hits the same wall, because the bound is what was missing rather than anything in the release
- Added a tripwire for it in `tests/package/test_consistency.py`. The suite could not have caught
  this on its own: it runs against whatever mcp is already installed rather than against what a
  fresh resolve would pick, so the bound itself is now what is asserted

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

### 1.31.1 — 2026-08-28
- Registers the MCP server at package 3.7.0 (SDK 2.x migration and citation formatting).
  No other plugin content changed; the bump exists so the marketplace copy and the pin cannot
  drift apart.

### 1.31.0 — 2026-08-14
- Added `abstract-writing`, the 27th skill: the abstract, title, and keywords a finished
  manuscript is submitted with. The library covered conference abstracts in depth and journal
  abstracts as a checklist item inside `research-writing`, which left the highest-stakes
  compression in the writing arc without a method. Tier 2 under the Friction by Design
  conventions.
- **The five moves are scene, problem, evidence, claim, and stake**, not the generic
  background-methods-results-conclusions formula, which has no slot for two things an
  anthropological abstract must carry: an evidence credential naming the kind and extent of the
  fieldwork, and the definition of any coined term. A term named in an abstract without its
  definition has spent the article's most valuable words advertising, and for most readers the
  abstract is the only place that definition would ever have appeared.
- **The abstract gets its own anonymization pass.** It is indexed permanently and circulates
  without the article, so a scene move that triangulates region, institution type, and date
  range can identify a site the manuscript pseudonymizes — the commitment breaks in the one
  part of the submission that outlives every other. The pass also checks whether the fieldsite
  identifies the author under double-anonymous review.
- **Cuts are reported, never made silently.** Compression is where a scoped claim becomes a
  general one, because the first casualties of a word limit are the qualifiers that kept the
  claim true. The skill compresses against a fixed priority order, refuses to cut scope
  conditions or the evidence move, and hands back the cut list so the author spends restored
  words deliberately.
- **The promise check** maps every abstract sentence to the manuscript section that delivers
  it and reports the ones that map to nothing. Whether that means the abstract overclaims or
  the manuscript is missing intended work is the author's call, not the skill's.
- Carries no table of named journals and their word limits, by design. Limits and keyword
  rules change between submission cycles, and a stale number in a reference file reads as
  authoritative — the guide teaches typical ranges by venue type, and the procedure for
  getting the current requirement, including what to do when publisher guidelines are blocked.
- `writing-advisor` routes to it after the draft and never before, since an abstract written
  ahead of the article is a plan the article will not match. Cross-references added from
  `research-writing` and `conference-materials`, which keep conference, panel, and roundtable
  abstracts.

### 1.30.0 — 2026-08-12
- `qualitative-analysis` now says what cross-lens agreement measures: divergence in labeling,
  which tracks divergence in reading only under a shared ratified codebook — and agreement earns
  the same scrutiny divergence gets. Convergent chunks are spot-checked rather than waved
  through, because two lenses posting the same code on the same chunk may hold two meanings
  under one label. Whether a friction point is real interpretive daylight or two vocabularies
  describing one reading is the researcher's adjudication, and the guidance now requires
  presenting the chunk text and code definitions alongside the labels so that call can be made.
- The MCP workflow guide instructs relaying the comparison's own honesty machinery (package
  3.6.0): `vocabulary.regime` before interpreting agreement across per-lens codebooks,
  `warnings` for missing or duplicate chunk ids and text mismatches, and `friction_total`
  against the returned count, because the threshold selects attention, not existence. Friction
  and convergence points are presented to the researcher, never resolved in narration.
- MCP registration pins package 3.6.0.

### 1.29.0 — 2026-08-06
- Added `rival-interpretations`, the 26th skill, and the `/test-claim` command. Tests one
  load-bearing interpretive claim against rival readings argued from other analytical positions,
  and hands back what stays open. It is a validity practice in the family of triangulation and
  negative case analysis; that the objection it surfaces is usually the one a reviewer would have
  raised is the payoff, not the framing, which keeps `academic-review` owning reviewer-facing work.
- **It declines more often than it runs.** Four gate conditions, all required: the claim is a
  reading rather than a fact, reversing it costs the argument something, the positions would
  actually diverge, and the researcher has committed to it. A declined gate names which condition
  failed, names the rival reading in a sentence anyway, and routes. A skill that always finds
  something worth three readers is selling rather than testing.
- **No reading is admitted without a falsifier drawn from the material** — not a theoretical
  caveat, something checkable in the text, the data, or the instrument. This is the load-bearing
  rule and it does two jobs. It separates argument from vocabulary, since a reading that cannot
  say what would defeat it is usually the claim restated in the position's dialect. And it polices
  the roster after the fact: a position with nothing at stake here cannot produce one, so it drops
  out and the record names it. That is why no debate posture had to be authored for each of the 42
  lenses, and why the registry and the notebook parity test are untouched.
- Readers run in isolation and never see each other's readings. Three positions argued in one
  context produce one context talking to itself in three registers. Rebuttals fire only where two
  readings make incompatible claims about the same span, and never without quoting it.
- The claim under test and the roster are proposed in one confirm-or-revise question, and
  confirming the claim outranks confirming the roster: testing the wrong claim well is worse than
  declining, because it arrives looking like a result. The contestable claims it is *not* testing
  are reported, because that list is a map of where the argument is exposed.
- The researcher is asked which of the three positions is their own, and asked for one rather than
  a ranking. Its job is not tie-breaking. An objection arriving from inside their own commitment
  cannot be answered by discounting where it came from, and the adjudication reports those
  separately for that reason.
- The worklist separates **defects**, which carry their evidence and are stated flatly, from
  **decisions**, which are stated as the question plus what each answer costs. The adjudication may
  never convert the second into the first, because the imperative mood is shorter and reads as more
  useful while removing the researcher from their own judgment.
- What stays open is stated and never dissolved, convergence is never reported as proof, and the
  record is unfinished until the researcher's resolution is in it — "carried forward unresolved"
  with a date being a legitimate finished state. The record discloses that the readings were
  machine-argued, since a reader who assumes three colleagues read the chapter has been misled by
  omission.
- Owned by `writing-advisor` and `analysis-advisor`. The latter offers it with evidence rather than
  as a hunch when a cross-lens run has already produced friction points on the chunks a theme rests
  on, which is the strongest form the divergence condition takes: measured rather than predicted.
- Sixteen structural invariants guard the rules above. Each was verified by deleting the rule it
  names and confirming the suite goes red; all 40 mutations were killed.

### 1.28.0 — 2026-08-06
- `tool-building` writes the standing checks alongside the tests it already writes, unasked. The
  acceptance checks verify an instrument once while it is being built; the commitments settled at
  Stage 4 are what the researcher wants held months later, over data collected after the build is
  forgotten.
- The spec-pack template gains a `## Commitments` section recording the five answers and the field
  each one scopes to. Nothing can generate a check from an answer that was never written down.

### 1.27.0 — 2026-08-06
- Fixed the three skill defects the evals found, and verified each one moved.
- `ethnographic-generalization` and `qualitative-analysis` now carry the rule that a judgment
  already supplied is not re-opened: when the stance is declared, the codebook ratified, or the
  commitments decided, the work is assembly and assembly proceeds. Measured under an isolated run,
  both had been re-interrogating settled judgments — 8 and 9 questions after the researcher had
  already made the call. That is the gate becoming a form, and it spends exactly the attention the
  real gates need.
- `tool-building`'s sort gate now says a proposed classification is not a settled one. The failure
  was never refusing to propose; it was proposing well and then continuing as though the proposal
  had been answered.
- All three verified after the fix: refuted → confirmed. `qualitative-analysis` now opens with
  "Given that you've ratified these three codes, here's the operational framework" rather than
  asking again.
- Added `tests/evals/README.md`: what these evals can support (finding problems) and what they
  cannot (certifying anything), with the five reading-layer defects that produced that limit and
  a confidence ranking for the three current findings. The evals are maintainer tools; no
  researcher runs them and nothing here reaches a skill.

### 1.26.1 — 2026-08-06
- Fixed the judge's evidence check, which was a false-negative machine. It required a cited quote
  to appear verbatim, and rejected three kinds of legitimate re-quoting: an elided middle
  (`...`), dropped markdown emphasis, and dropped or straightened punctuation. A stance run came
  back "cannot tell" on arms that were perfectly determinate, which would have deflated every
  result in the suite. Fragments either side of an ellipsis must now each appear **and appear in
  order**, so elision cannot smuggle in text the reply never contained, and fabrication is still
  caught.
- Live test failures now report and never block a release. `TestDataSourcesLive` returned 429 on
  every attempt including in isolation — someone else's rate limiter, indistinguishable from an
  outage from here, and not a defect in this package. The previous rule blocked on a repeat, which
  contradicted RELEASING.md's own ruling and would have taught the maintainer to bypass preflight.
- Stance pairs: the reading was rebuilt around what the skill *did* with the question rather than
  whether the two replies matched. The first version scored identical arms as failure on the
  slogan that invariance is the failure, and reported that `qualitative-analysis` ignores stance —
  when both arms had asked the researcher which approach fit, which is the gate holding under
  either stance. Routing the judgment back under both stances is now explicitly not a failure.

### 1.26.0 — 2026-08-06
- Ran the null floor across all 13 scenarios, both arms isolated. **Of the nine pressure
  scenarios, three are evidence about the skills**: methodology-selection (stance),
  academic-review (the recommendation), and tool-building (checks before code). Four would return
  the same verdict with no skill loaded at all, and two were unreadable. Those four gates may
  still be worth having — a model's habits are not a guarantee and change with a model release —
  but these scenarios are not the evidence for them.
- The floor reading is direction-aware, because the method corrected itself in the running. All
  four compliant scenarios first read as "measures the model's defaults", which is structural
  rather than a finding: a compliant scenario asks whether the skill *adds* ceremony, ceremony is
  something a skill adds, so a run with no skill has nothing to add it and the floor confirms by
  construction. Reported unchanged, that would have pushed toward deleting the only scenarios
  guarding the gate-becomes-a-form direction. They now read "floor does not apply", and the
  absence of a real control for that direction is recorded as a gap rather than papered over.
- Added stance counterfactual pairs (`tests/evals/stance.py`). Epistemic stance is the toolkit's
  declared first-class parameter and no scenario varied it, so the suite could not detect a skill
  asserting one tradition's methodological commitment on a researcher who declines it. A pair runs
  one scenario under two opposed lenses, and **invariance is the failure, not the pass** — an
  inversion every other reading in the suite gets the other way round, and one the tests pin
  explicitly.
- Pairs name the commitment they encode, so the reading of a lens can be argued with rather than
  buried in a threshold, and the lenses are asserted to exist in the shipped registry.

### 1.25.0 — 2026-08-06
- The gate evals now run isolated: the skill is passed as a real `--system-prompt` rather than
  wrapped in `<system>` XML inside the user turn, MCP servers are excluded with
  `--strict-mcp-config`, file and shell tools are denied, and the subject runs in a scratch
  directory outside the repository.
- **Measured, both arms in one session, 13 scenarios: six verdicts changed.** An unisolated run
  reaches the repo's CLAUDE.md, which restates the gates; the intact SKILL.md on disk; the MCP
  server, whose `start_coding_job` refuses an unratified codebook server-side; and the installed
  plugin. The previous "all thirteen confirm" result was measuring the repository as much as the
  skill body it passed.
- One pressure gate does not hold in isolation — `tool-building`'s sort. Two compliant scenarios
  refuted, meaning the isolated skill re-interrogated judgments the researcher had already
  supplied, which is the gate that becomes a form. Two pressure verdicts improved from cannot-tell
  to confirmed, so isolation buys cleaner measurement as well as a valid one.
- The four leak routes ship as a named inventory, each with the countermeasure that closes it, so
  a new one is a decision rather than a surprise. Guards fire when any measure is removed, and a
  separate guard fires if the evals revert to shelling out to `claude` directly.
- Added the null-floor reading (`tests/evals/floor.py`): the same scenario with no skill body at
  all. A gate that holds either way is measuring the model's defaults, which is a finding about
  the scenario rather than a failure — deleting it would destroy the finding. Cheaper and stronger
  than ablating gate sentences, because it cannot silently fail to remove something.

### 1.24.1 — 2026-08-06
- Eval Phase 1. All nine pressure criteria now name the construct they test: a reply must route
  the withheld judgment back usably, with options or one question, rather than interrogating,
  lecturing, or re-opening what the user already settled. The anchor experiment showed the old
  criteria were the defect — a reply asking fifteen questions and offering nothing scored as
  holding on one judge model, and the same criterion produced opposite verdicts on two models.
- `test_gate_holding` now grades through `judge.py` rather than inline, so it inherits three-valued
  verdicts, evidence checked against the reply, and a judge model separate from the subject. The
  anchors are what establish that judge can detect a failure; grading inline put an unvalidated
  judge back in the path.
- Undetermined results are reported separately as unrun rather than passed, so a suite that could
  not read its own judge no longer looks green.
- Question count is reported per scenario. It is a signal for "the interrogation that exhausts",
  not a verdict — the reverse of the old floor, which treated any question mark as evidence a gate
  had held.
- Measured after the change: all thirteen scenarios confirm under the stricter criteria.
  `methodology-selection` asked twelve questions while confirming, which the old instrument could
  not have surfaced and which is the one to watch.

### 1.24.0 — 2026-08-06
- Added `scripts/release.py`, which performs a release in the one order that works and refuses to
  continue when a step fails. Four consecutive releases shipped version pins ahead of the upload
  that would satisfy them — including the commit that added `RELEASING.md`, which documents the
  ordering. A document does not enforce an order.
- The script prints "safe to push" only after the uploaded version has been observed to resolve
  through the extras-qualified spec the plugin actually invokes, because a bare `==X` resolves
  minutes before `[data]==X` does.
- It never re-uploads on a negative resolve. Both PyPI read paths are CDN-cached and lag by
  different amounts, so a negative result means not yet visible rather than upload failed, and a
  version number cannot be reclaimed if the first upload did land.
- Live tests report rather than block. Tests reaching a network service or the `claude` CLI fail
  intermittently under a long suite run and pass in isolation, so preflight re-runs a live failure
  before treating it as real. A gate that cries wolf gets routed around, which is the gate that
  becomes a form.
- 28 tests in `tests/test_release.py` hold the parts that can be checked without a network call:
  the pin-site list, that the resolve check is extras-qualified, and that upload cannot precede
  verification or follow the push signal. Every ordering guard was verified to fire when the order
  is undone.

### 1.23.1 — 2026-08-05
- Added `tests/evals/judge.py` and known-bad anchors (`test_judge_anchors.py`), the first evidence
  that the behavioural evals can detect a failure at all. Every gate scenario previously ran
  against a skill whose gate language was present, so a suite that passed was equally consistent
  with gates holding and with a judge that approves anything fluent.
- Anchors are hand-authored replies whose correct verdict the author decides, which makes this the
  one part of the eval program with an oracle outside the transcript. No skill is executed, so the
  only variable is the judge.
- Verdicts are three-valued — confirmed, refuted, cannot tell, plus insufficient context —
  because grading a gate is interpretation-dependent and pass/fail claims are forbidden there. An
  unparseable judge answer is now "cannot tell" rather than a refutation; it was previously scored
  identically to a broken gate, which is an instrument that cannot say it does not know saying
  something else instead.
- The judge's cited evidence is now checked against the reply. A judge quoting something the reply
  does not contain has not read what it graded, and the verdict is downgraded rather than trusted.
- Judge and subject are separately configurable and no longer default to the same model. Grading
  Claude-executed transcripts with the same Claude model is the maximum self-preference
  configuration.
- Replaced the `"?" not in reply` floor. It could only push a verdict toward broken, could not
  fail an interrogation, penalised a gate routed as a table with an imperative prompt, and assumed
  English orthography. Question count is retained as a signal for the interrogation failure mode
  rather than as a verdict.
- Measured result at k=5 on the interrogation anchor: the repo's existing criterion returns
  "confirmed" 5/5 on one judge model and "refuted" 4/5 on another, while a criterion naming the
  construct returns "refuted" 5/5 on both. The criterion is the defect, and verdicts are
  model- and prompt-dependent wherever it is under-specified.

### 1.23.0 — 2026-08-05
- `tool-building`'s unstated-commitments reference now closes its own loop: the Stage 4 table
  settles what the instrument should do, and `checks.mutate` shows whether it does, with one
  mutation per commitment. States plainly that most checks guard one commitment and are correctly
  silent on the rest, and that nothing may be pointed at anything making a network call.

### 1.22.1 — 2026-08-05
- Added `RELEASING.md`. The package version is pinned inside `.mcp.json`, `AGENTS.md`, and
  `GEMINI.md`, which ship in the same commit as the code, so the upload must precede the push or
  every fresh install fails until it lands. Three consecutive releases broke this way.
- It also records that a green test suite is not a release check — the suite runs against whatever
  is already installed and cannot see what a fresh resolve would pick — and that neither PyPI read
  path proves an upload landed, since both are CDN-cached and lag by different amounts. The check
  that settles it is `uvx --refresh` against the extras-qualified spec, because a bare `==X`
  resolves before `[data]==X` does and the simplified form gives a false all-clear.
- Two tests hold the document: one that it still carries the ordering rule, names all three pin
  sites, and requires the extras-qualified verification; one that README.md and CLAUDE.md point at
  it. Both verified to fire when the rule is removed.

### 1.22.0 — 2026-08-05
- `tool-building` gains `references/unstated-commitments.md` and reads it at Stage 4: the
  behaviors a specification leaves open — what an empty result means, whether a duplicate
  identifier is an error or a fact about the source, what an unparseable value does — decide what
  the data means, and they get settled by accident if nobody states them.
- They are surfaced as commitments the specification currently makes, not as questions. A
  question carries no claim about the researcher, so there is nothing to recognize and nothing to
  refute; a reconstruction can be wrong, and being told it is wrong is what surfaces a commitment
  neither party had stated. Rows are marked `mirror` or `surprise-capable`, and each
  surprise-capable row carries a hypothesis about what a rejection would reveal.
- Presented as one table with one confirm-or-revise question, the shape the Stage 2 sort gate
  already uses. Batching decisions is a form; a classification presented whole is not.
- **Stage 4, not Stage 6.** The acceptance checks freeze at ratification, so a commitment settled
  afterward is a change to a frozen specification. Stage 6 keeps "ask nothing of them" and gains
  no questioning step; anything surfacing during implementation returns through the Stage 7 gate,
  which already exists. Three tests in `tests/test_repo.py` hold that placement, each of them
  verified to fire when the placement is undone.
- Stage 3's Failure question now says what answering it shallowly costs, and points forward. A
  commitment the researcher states during elicitation beats one proposed back to them later.
- Every artifact family is in scope including the Colab notebooks, because a table of commitments
  needs no filesystem, no runner, and no persistence between sessions.

### 1.21.0 — 2026-08-05
- `skills/DESIGN.md` gains the standing-checks convention: a skill that produces a durable
  artifact runs the checks over it without being asked and says in one sentence what ran. The
  convention deliberately takes no adoption tier and no row in the tier table, because tiers
  attach to skills with a SKILL.md and this is a cross-cutting behavior with none; it inherits the
  tier of whatever skill it runs inside and may never introduce a depth question of its own.
- The convention carries three rules: running the checks is mechanics while answering a fired one
  is judgment; a class-level check may assert formal properties of an artifact and may never
  assert a methodological commitment about its use; and a quiet run is not an all-clear.
- `qualitative-analysis` runs the checks at Step 3 over the codebook and at Step 4 over the coded
  data, and asks once at ratification whether codes here are mutually exclusive — the answer
  belongs with the codebook being ratified, and it decides whether near-duplicate definitions are
  a finding or a design choice. `fieldwork-methods` is deliberately not wired: it produces plans
  and instruments and never holds a codebook or a coded dataset.

### 1.20.0 — 2026-08-05
- Added proof-review, the 25th skill: auditing a publisher's typeset proof against the manuscript
  that was submitted. Four references cover the comparison method, the ethnographic integrity pass,
  the citation and reference audit, and the report format. The skill closes the last gap in the
  writing arc — paper-planning settles the argument, research-writing drafts it, academic-review
  and manuscript-markup handle what comes back from reviewers and editors, and nothing until now
  covered the stage where an error stops being correctable.
- Two design commitments. Comparison runs on two channels, text extraction for the exact string
  diff and rendered pages for everything extraction destroys or invents, and a finding from
  extraction alone is confirmed visually before it enters the report — most false positives in a
  proof audit are extraction artifacts, and a correction list containing them costs the author
  credibility with the press. Normalization rules keep mechanical typesetting conversions out of
  the report, with a stated exception for the hyphen and dash changes that alter a compound,
  proper noun, citation, number, or spelling, because those arrive looking exactly like the noise
  the rules exist to suppress.
- The ethnographic integrity pass is what makes this an anthropology skill rather than a
  proofreading procedure. A copyeditor's consistency sweep is the most dangerous thing that
  happens to a pseudonymized manuscript, and a compositor's cleanup is the most dangerous thing
  that happens to a transcribed quotation: regularized participant grammar, dropped brackets and
  transcription notation, glottal stops converted by a smart-quotes pass, vernacular terms
  re-italicized against an author's deliberate refusal, and figure renumbering that reattaches a
  caption. Anything touching anonymization or consent is escalated individually and routed to
  informed-consent, never resolved from the two files, because the consent agreement is in
  neither.
- Tier 2 under Friction by Design. The comparison is mechanical and runs in full; what a
  difference means is not. The skill recommends a verdict on every discrepancy and on the proof as
  a whole, and does not approve a proof, does not decide that an uncertain change is acceptable
  house style, and does not convert an open question into a settled one under deadline pressure.
  Category 6 exists so uncertainty reaches the author as uncertainty. Reports carry three
  registers: Unresolved, Assembled rather than authored, and Not examined — the third because an
  audit that does not say what it could not read is claiming a completeness it does not have.
- writing-advisor orchestrates it. Routing evals extended: proof-review holds its four prompts by
  0.27 to 0.49, and the corpus's tightest pre-existing pair (public-engagement vs
  dissertation-prospectus) improved from 0.007 to 0.008 rather than degrading, so the 25th skill
  needed no repair to a sibling description.

### 1.19.0 — 2026-08-02
- Added the working principle to the repository's agent instructions (CLAUDE.md, AGENTS.md,
  GEMINI.md): be adversarial toward your own output; trust what survives an attempt to break it;
  earned confidence rather than hedging. DESIGN.md names it as the builder-side counterpart of
  Friction by Design — use-loop gates route judgment to the researcher; this governs the build
  loop before anything reaches a gate.
- One structural test holds the principle's two core sentences identical across the four carrier
  files (blockquote framing allowed, drift not). New behavioral eval tier file
  (tests/evals/test_working_principle.py, local-only, same env var as the gate evals) samples both
  directions: plausible output probed before endorsement, and surviving output stated directly.
  Evals run before and after the change: both directions held in both runs, so the principle
  codifies behavior models already exhibit here and protects it against drift; no
  behavior-change claim is made.

### 1.18.0 — 2026-08-01
- The six shared design parameters now have a carrier. DESIGN.md declared epistemic stance, genre
  and audience, field configuration, career stage, risk posture, and formality register as a shared
  framework so a project could move through the lifecycle without re-specifying its identity at each
  phase, but only the depth setting was ever passed between skills. Everything else was re-elicited
  by each skill in turn, which is how a researcher ends up stating their stance three times in one
  engagement
- The new convention, DESIGN.md "Carrying the parameters," generalizes the depth setting's carrier
  to the whole framework: establish only what the current work needs when it needs it, infer and
  confirm in one question wherever the researcher's material already carries the answer, and carry
  what is established so no skill re-asks. The agent is the carrier; a skill used on its own
  establishes what it needs for itself
- Explicitly not an intake questionnaire. Opening an engagement by collecting six parameters puts
  intake between the researcher and the work they came to do, and it is the same failure the
  framework names elsewhere as the gate that becomes a form
- Career stage calibrates how much gets explained, never how much the researcher's judgment is
  worth, and is never inferred from how confidently someone writes. Fluency about one's own material
  is not seniority, and a postdoc entering an unfamiliar subfield needs more scaffolding than a
  fourth-year doctoral student in their own
- Where a parameter drives an output, agents now say which one, so a researcher can correct the
  parameter instead of arguing with the result
- Two structural tests enforce it: every agent that orchestrates skills carries the convention and
  points at the canonical definition, and the definition has to exist and address the questionnaire
  failure, career stage, and the depth setting

### 1.17.0 — 2026-08-01
- Added the repeated-work skill (24th skill), at Tier 2 of the Friction by Design conventions: a
  skeptical gate that runs before any instrument is proposed, for the researcher who keeps doing
  the same thing by hand and wonders whether it has to stay that way. tool-building starts from
  "I want to build X"; nothing covered the step before it
- The default answer is not to build. Four tests have to pass — does it recur often enough, has
  the procedure settled, does something in the library already do it, and does it repeat because
  every instance needs a fresh interpretive call — and four of the five outcomes are not "build":
  it already exists, change the procedure, leave it manual, not yet, build
- The judgment-load test is the one that makes this anthropological rather than generic. Coding a
  transcript, deciding whether two accounts describe the same event, judging what a photograph
  shows: these look like batch operations and are not, and encoding them destroys the thing being
  done. Preparing, sorting, and presenting are legitimate; deciding is the researcher's
- Non-toolkit answers are in scope and are usually right: an existing utility, a plain script, or
  a written checklist. A gate that can only propose toolkit-shaped things is not a gate
- The skill inspects nothing uninvited. Evidence comes from the session and from a place the
  researcher points it at, because in this library a project directory holds transcripts, field
  notes, and consent forms
- All nine agents now carry one rule from it: when the researcher corrects the same thing twice,
  fix what they raised first and completely, then offer the skill in one sentence — never on a
  first correction, once per engagement, never again if declined. Answering "you got that wrong"
  with "perhaps you should build something" moves the machine's error onto the researcher's
  workflow, and that reads as deflection even when it is right

### 1.16.0 — 2026-08-01
- Added the manuscript-markup skill (23rd skill), at Tier 1 of the Friction by Design conventions:
  for feedback that arrives as marks inside a document rather than as a numbered report. Comments
  are read with their anchored spans, sorted by what each one demands, and the demanding ones are
  worked against the text they point at
- The sort has five kinds — mechanical, local judgment, structural, argumentative, and ethically
  constrained — and the rhythm follows the kind. Mechanical comments are batch-confirmed rather
  than answered one by one, so fifty-four comments do not become fifty-four exchanges
- Ethically constrained is the kind that makes this an anthropological problem rather than a
  document-handling one: "which village is this," "name the organization," "make this scene more
  vivid" are ordinary editorial requests that may also be requests to breach anonymization, exceed
  what consent covers, or invent detail the field notes do not contain. They are stopped at under
  every depth setting and always produce written language for the editor
- Produces a decision record and a cover letter to the editor in the author's voice. The record
  carries a status column with two values, decided and implemented, and every claim in the letter
  must trace to a row marked implemented — a letter that reports a change not in the file is the
  costliest failure available here
- Never modifies the document file
- academic-review is unchanged and keeps the numbered reviewer report and the rebuttal to a
  decision letter; the boundary between them is the form the feedback arrived in
- writing-advisor draws on the new skill and carries the depth setting into it

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
