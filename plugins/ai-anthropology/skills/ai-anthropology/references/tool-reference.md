# MCP tool reference

This list is checked against the `@mcp.tool` registrations in `src/ai_anthro_toolkit/mcp/server.py`. Adding or removing a server tool requires updating this reference in the same change.

## Orientation and sources

- `toolkit_info` — report package and capability information.
- `list_notebooks` — find the browser-based notebook alternatives.
- `search_openalex`, `search_crossref`, `search_pubmed` — search scholarly APIs.
- `get_google_trends`, `search_google_news`, `search_google_scholar`, `search_google_patents` — collect platform search data when reachable.
- `get_ngram_frequencies` — collect Google Books Ngram frequencies.
- `search_youtube`, `get_youtube_transcript` — find videos and retrieve transcripts.
- `get_podcast_episodes` — read podcast RSS feeds.

## Citations and lenses

- `format_citation`, `format_citation_batch`, `list_citation_styles` — format DOI metadata; formatting does not independently verify a citation.
- `list_lenses`, `get_lens` — inspect the analytical-lens registry.

## Local preparation and checks

- `chunk_transcript` — split transcript text into analysis records locally.
- `extract_document_markup` — extract comments and revisions from supported documents.
- `get_artifact_checks` — inspect codebooks and coded datasets for implied commitments; findings are questions for the researcher.

## Gated qualitative-analysis pipeline

- `start_codebook_job` — begin codebook generation.
- `ratify_codebook` — record the researcher's confirm-or-revise decision and checksum.
- `start_coding_job` — begin coding only from a matching ratified codebook.
- `build_ratification_desk` — build a desk where the researcher ratifies each code against its cases, or rules on each disagreement between two coding passes; it opens as an MCP App or as a self-contained page. The researcher decides there; never decide for them.
- `record_desk_decisions` — apply the decisions the researcher made on a desk page (the JSON it copies) or stated in chat, through the same gate; it returns the ratification_id to code with. Never fill in a decision they did not make.
- `desk_sync`, `desk_finish` — app-only: the desk's view calls them when the researcher saves a decision or presses Ratify. The model cannot call them.
- `get_next_batch`, `submit_batch` — run delegated interpretive batches through the orchestrating model.
- `get_job_status`, `get_job_result` — inspect asynchronous or delegated jobs.
- `build_themes` — develop themes from coded material.
- `compare_lenses` — compare results produced under different analytical lenses.

## Networks of coded material

- `build_network` — construct a code co-occurrence, speaker-to-code, or lens-agreement graph.
- `analyze_network` — compute and interpret structural properties without Gephi.
- `view_network` — display the network as an interactive MCP App.
- `export_network` — export GEXF or another supported format for Gephi or downstream use.
