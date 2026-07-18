# Review Types and Search Strategy

Reference file for the literature-review skill. Loaded when choosing a
review genre and designing the search.

---

## Choosing the Review Genre

| Genre | Question it answers | Selection logic | Screening formality | Typical anthropological use |
|---|---|---|---|---|
| Narrative–theoretical | "What conversation is this study joining, and on what terms?" | Purposive and argued | Decision log | Dissertations, articles, grant framing — the default |
| Scoping | "What exists in this area, of what kinds?" | Broad and mapped | Moderate; charted | Emerging topics (e.g., AI in ethnographic practice), interdisciplinary terrain |
| Systematic | "What does the evidence say about a focused question?" | Exhaustive under protocol | Full PRISMA audit trail | Applied, medical, policy anthropology; client and public-health work |

Genre selection notes:

- The systematic review's authority comes from its protocol; claiming
  it without the protocol is a methods error (see SKILL.md guardrails).
  Scoping reviews follow the framework of Arksey and O'Malley (2005).
- Narrative reviews in anthropology often work *genealogically*:
  tracing how a concept (e.g., structural violence, ontological
  politics) developed, split, and traveled — organize the search
  around lineages and debates, not just keywords.
- Hermeneutic approaches treat searching and interpreting as a circle
  rather than a pipeline: early reading refines the vocabulary that
  drives later searching (Boell and Cecez-Kecmanovic 2014). Log the
  iterations rather than pretending the search was one-shot.
- Reviews can themselves be standalone contributions, with their own
  methodological standards (Snyder 2019).

## Search Strategy

### Concept-to-query construction

1. Decompose the research question into concept blocks (phenomenon,
   population/setting, theoretical angle).
2. For each block, list variants: synonyms, subfield vocabulary,
   regional spellings, older terms the literature used before the
   current one.
3. Combine blocks with AND, variants with OR; adapt syntax per
   database.
4. In biomedical territory, map to controlled vocabularies (MeSH via
   PubMed) rather than relying on free text alone.

### The toolkit's literature tools

When the ai-anthropology MCP tools are present, drive the search
natively; otherwise use the corresponding Colab notebooks or the
pip-installed package (see the repository's AGENTS.md fallback chain):

- `search_openalex` — 250M+ works, all disciplines; filters for year,
  venue, open access. Venue filtering resolves journal names to IDs
  internally (names are ambiguous; identifiers are not).
- `search_crossref` — canonical DOI metadata; useful for verifying
  citations and coverage checks.
- `search_pubmed` — biomedical and health literature with date and
  journal filters; the right tool when the question touches clinical
  territory.
- `search_google_scholar` — broadest coverage including grey
  literature, but scraping-based: rate-limited, blocked from
  datacenter IPs, and unusable for exhaustive searching. Treat it as a
  discovery supplement, never the primary systematic source.

### Beyond database search

- **Citation chasing**: backward (mine reference lists of key papers)
  and forward (who cites the field-defining pieces). Essential in
  anthropology, where much of the conversation happens in books and
  edited volumes that keyword search underweights.
- **Grey literature**: reports, theses, working papers, conference
  papers — decide explicitly whether the genre needs them, and search
  them deliberately if so.
- **Books and edited volumes**: no single database indexes them well;
  combine OpenAlex, publisher catalogs, and citation chasing, and say
  in the write-up how book coverage was achieved.
- **Preprints**: include or exclude by explicit policy; label them as
  preprints wherever cited, and prefer the published version when one
  exists (a DOI prefix of 10.1101/ or 10.48550/ signals bioRxiv/
  medRxiv or arXiv respectively).

### Search logging

Log, for every search executed:

| Field | Example |
|---|---|
| Database/tool | search_openalex |
| Exact query | "medical pluralism" AND (Ghana OR "West Africa") |
| Filters | year_from=2000, OA only: no |
| Date run | 2026-07-18 |
| Records returned | 143 |

Keep the log as a file alongside the review. It is the difference
between "we searched the literature" and a method someone can trust or
repeat — and it is what makes an updated search possible a year later.

## Citations

- Arksey, Hilary, and Lisa O'Malley. 2005. "Scoping Studies: Towards a
  Methodological Framework." *International Journal of Social Research
  Methodology* 8(1): 19–32.
- Boell, Sebastian K., and Dubravka Cecez-Kecmanovic. 2014. "A
  Hermeneutic Approach for Conducting Literature Reviews and
  Literature Searches." *Communications of the Association for
  Information Systems* 34: 257–286.
- Page, Matthew J., et al. 2021. "The PRISMA 2020 Statement: An
  Updated Guideline for Reporting Systematic Reviews." *BMJ* 372: n71.
- Snyder, Hannah. 2019. "Literature Review as a Research Methodology:
  An Overview and Guidelines." *Journal of Business Research* 104:
  333–339.
