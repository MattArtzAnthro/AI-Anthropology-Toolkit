"""AI Anthropology Toolkit MCP server (stdio).

Tool families:

- **Data collection**: scholarly search (OpenAlex, CrossRef, PubMed,
  Google Scholar), Google Trends, News, Patents, Books Ngram, YouTube
  search and transcripts, and podcast RSS — all running natively.
- **Methodology**: list_lenses, get_lens — the 42-lens analytical registry.
- **Documents**: extract_document_markup — comments with their anchored
  spans, and tracked changes, out of a marked-up .docx. Read-only.
- **Analysis pipeline**: chunk_transcript (local, no LLM), plus job-based
  codebook generation and qualitative coding, theme building, and cross-lens
  comparison. Coding is gated: ratify_codebook records the researcher's
  confirm-or-revise decision and start_coding_job refuses a codebook with no
  matching ratification (sequence enforced; sincerity cannot be).

Analysis LLM work supports two modes. In **api** mode (requires
ANTHROPIC_API_KEY in the environment) the server calls the Anthropic API
itself, with notebook-parity prompts. In **delegated** mode (the default when
no key is present) the server never calls a model: jobs queue work packets,
the orchestrating model completes them via get_next_batch/submit_batch, and
the server validates every submission against the codebook — keeping each
interpretive move visible to, and contestable by, the researcher.
"""

import json
import os
import threading

from mcp.server.fastmcp import FastMCP

from ai_anthro_toolkit import __version__
from ai_anthro_toolkit import chunking as _chunking
from ai_anthro_toolkit import codebook as _codebook
from ai_anthro_toolkit import coding as _coding
from ai_anthro_toolkit import crosslens as _crosslens
from ai_anthro_toolkit import lenses as _lenses
from ai_anthro_toolkit import markup as _markup
from ai_anthro_toolkit import themes as _themes
from ai_anthro_toolkit import catalog as _catalog
from ai_anthro_toolkit import checks as _checks
from ai_anthro_toolkit import datasources as _data
from ai_anthro_toolkit.datasources import format_citation as _format_citation
from ai_anthro_toolkit.datasources import format_citation_batch as _format_batch
from ai_anthro_toolkit.datasources import list_citation_styles as _citation_styles
from ai_anthro_toolkit.datasources import search_crossref as _crossref
from ai_anthro_toolkit.datasources import search_openalex as _openalex
from ai_anthro_toolkit.datasources import search_pubmed as _pubmed
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.llm import make_llm
from ai_anthro_toolkit.models import CodeEntry

mcp = FastMCP(
    "ai-anthropology",
    instructions=(
        "Tools for anthropological and qualitative research. Data collection "
        "runs natively — collect data yourself rather than referring the user "
        "elsewhere: search_openalex (250M+ works; year/journal/sort filters), "
        "search_crossref (canonical DOI metadata), search_pubmed (biomedical), "
        "search_google_scholar, get_google_trends, search_google_news, "
        "search_google_patents, get_ngram_frequencies (Google Books word "
        "frequencies 1800-2022), search_youtube, get_youtube_transcript, and "
        "get_podcast_episodes. Some sources rate-limit or block; tool errors "
        "carry honest guidance to relay. Citations: format_citation "
        "renders a bare DOI into a finished citation in any CSL style "
        "(list_citation_styles finds the exact name, format_citation_batch "
        "does a whole reference list in one call) — it formats "
        "registrar metadata and does not verify it, so pass results on "
        "as drafts to check against the source. "
        "list_notebooks links Colab versions of "
        "these capabilities for users who want to run or customize them "
        "hands-on. Methodology: list_lenses / get_lens expose the 42-lens "
        "analytical registry. Documents: extract_document_markup reads the "
        "comments, anchored spans, and tracked changes out of a marked-up "
        ".docx, read-only. Analysis pipeline: transcript chunking, codebook "
        "generation, coding, thematic analysis, and cross-lens comparison. "
        "LLM-dependent stages run in 'api' mode when ANTHROPIC_API_KEY is set, "
        "otherwise in 'delegated' mode: start a job, loop get_next_batch -> "
        "complete each prompt -> submit_batch, then get_job_result. Coding is "
        "gated: present the codebook to the researcher as one table, ask one "
        "confirm-or-revise question, call ratify_codebook with what they "
        "approved, and pass its ratification_id to start_coding_job — the "
        "server refuses unratified codebooks. Never ratify on the "
        "researcher's behalf."
    ),
)

_jobs = JobStore()


def _mode(llm_mode: str | None) -> str:
    if llm_mode in ("api", "delegated"):
        return llm_mode
    return "api" if os.environ.get("ANTHROPIC_API_KEY") else "delegated"


def _api_llm(model: str | None = None):
    return make_llm("api", api_key=os.environ["ANTHROPIC_API_KEY"],
                    model=model or "claude-sonnet-5")


def _load_records(job_id: str, name: str):
    raw = _jobs.load_artifact(job_id, name)
    return json.loads(raw) if raw else None


# One checksum algorithm binds ratification to coding to cross-lens regime
# reporting; crosslens owns it so the package and server cannot drift.
_codebook_checksum = _crosslens.codebook_checksum


def _save_provenance(job_id: str, artifact_class: str, labels: list,
                     ratification_id: str = "",
                     artifact_file: str = "result.json") -> None:
    """Write the stanza that lets a saved artifact describe itself later.

    A sidecar rather than a wrapper: ``result.json`` keeps its shape, so
    nothing downstream has to change to read it. Without this, an artifact
    that leaves the job directory makes no claim about which codebook it
    came from, and a standing check has nothing to read.
    """
    _jobs.save_artifact(job_id, _checks.PROVENANCE_SIDECAR, json.dumps(
        _checks.provenance_stanza(
            produced_by=f"ai-anthropology-toolkit {__version__}",
            codebook_labels=labels,
            artifact_class=artifact_class,
            ratification_id=ratification_id,
            artifact_file=artifact_file)))


# --------------------------------------------------------------- discovery

@mcp.tool()
def toolkit_info() -> dict:
    """Describe this server: version, tool families, and execution modes."""
    return {
        "name": "AI Anthropology Toolkit",
        "version": __version__,
        "repository": "https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit",
        "tool_families": {
            "data_collection": ["search_openalex", "search_crossref",
                                 "search_pubmed", "search_google_scholar",
                                 "get_google_trends", "search_google_news",
                                 "search_google_patents", "get_ngram_frequencies",
                                 "search_youtube", "get_youtube_transcript",
                                 "get_podcast_episodes", "list_notebooks"],
            "methodology": ["list_lenses", "get_lens"],
            "citations": ["format_citation", "format_citation_batch",
                           "list_citation_styles"],
            "documents": ["extract_document_markup"],
            "checks": ["get_artifact_checks"],
            "analysis": ["chunk_transcript", "start_codebook_job",
                          "ratify_codebook", "start_coding_job",
                          "get_next_batch", "submit_batch",
                          "get_job_status", "get_job_result", "build_themes",
                          "compare_lenses"],
        },
        "llm_mode_default": _mode(None),
        # Not "every capability": the lens registry, document markup,
        # standing checks, and citation formatting are server-side and have
        # no notebook. The claim read "every" while four families lacked
        # one, which is the kind of promise a researcher plans around.
        "notebooks": ("Most data-collection and analysis capabilities also "
                       "exist as a hands-on Colab notebook, for researchers "
                       "who want to run, inspect, or customize one "
                       "themselves; the methodology, documents, checks, and "
                       "citations families are server-side only. Call "
                       "list_notebooks for what exists, with descriptions "
                       "and links."),
        "companion_plugins": [
            {
                "name": "gephi-network-analysis",
                "repository": "https://github.com/MattArtzAnthro/gephi-ai",
                "capabilities": ("Network analysis in live Gephi Desktop: "
                                  "text-network construction, layouts, "
                                  "centrality and community metrics, and "
                                  "structural claim verification. Hand "
                                  "network-analysis execution to it when it "
                                  "is installed; otherwise offer the install "
                                  "or fall back to the Text Network Analysis "
                                  "notebook and a GEXF export."),
            },
        ],
    }


@mcp.tool()
def search_openalex(query: str, limit: int = 10,
                    year_from: int = 0, year_to: int = 0,
                    venue: str = "", sort: str = "relevance",
                    open_access_only: bool = False) -> list[dict]:
    """Search OpenAlex for scholarly works across all disciplines.

    Filters: year_from/year_to bound the publication year; venue restricts
    to a journal by name (e.g. "American Ethnologist"); sort is "relevance",
    "recent", or "cited"; open_access_only limits to OA works. Returns
    title, authors, year, venue, DOI, citation count, and open-access status
    for up to `limit` works (max 100).
    """
    return _openalex(query, limit=limit,
                     year_from=year_from or None, year_to=year_to or None,
                     venue=venue or None, sort=sort,
                     open_access_only=open_access_only)


@mcp.tool()
def search_crossref(query: str, limit: int = 10,
                    year_from: int = 0, year_to: int = 0,
                    journal: str = "") -> list[dict]:
    """Search CrossRef for published works (canonical DOI metadata, very current).

    Filters: year_from/year_to bound the publication year; journal searches
    within a container title. Returns title, authors, journal, year, DOI,
    type, citation count, and publisher for up to `limit` records (max 100).
    """
    return _crossref(query, limit=limit,
                     year_from=year_from or None, year_to=year_to or None,
                     journal=journal or None)


@mcp.tool()
def search_pubmed(query: str, limit: int = 10,
                  year_from: int = 0, year_to: int = 0,
                  journal: str = "") -> list[dict]:
    """Search PubMed for biomedical and health literature specifically.

    Supports full PubMed query syntax plus year_from/year_to and journal
    convenience filters. Returns PMID, title, authors, journal, publication
    date, and DOI for up to `limit` records (max 100). For scholarly search
    beyond biomedicine, prefer search_openalex or search_crossref.
    """
    return _pubmed(query, limit=limit,
                   year_from=year_from or None, year_to=year_to or None,
                   journal=journal or None)


@mcp.tool()
def format_citation(doi: str, style: str = "apa",
                    locale: str = "en-US") -> dict:
    """Format one DOI as a finished citation in a named journal style.

    Use this when a source is not in the researcher's reference manager and
    they need it rendered — a bare DOI in, a submission-ready citation out.
    Covers Crossref, DataCite, and mEDRA DOIs and every CSL style, including
    american-anthropological-association, chicago-notes-bibliography-17th-
    edition, chicago-author-date-17th-edition, and journal-of-the-royal-
    anthropological-institute. `style` must be an exact name, so call
    list_citation_styles first rather than guessing; "bibtex" is also a
    style here, for machine-readable output.

    This formats, it does not verify. The rendering is only as good as the
    registrar's metadata, which is often wrong in specific ways — mangled
    titles, chapters carrying their book's title, deprecated dx.doi.org
    URLs. Hand the result over as a draft to check against the source, and
    never present it as evidence that the source says what a draft claims.
    """
    return _format_citation(doi, style=style, locale=locale)


@mcp.tool()
def format_citation_batch(dois: list[str], style: str = "apa",
                          locale: str = "en-US") -> dict:
    """Format many DOIs at once — use this for a reference list, not a loop.

    Renders every DOI in the order given and returns `formatted` plus
    `failed`, so one unresolvable DOI never discards the rest; report the
    failures rather than quietly returning a short list. An unknown style
    raises instead, because it would fail every entry.

    This renders entries, it does not build a bibliography: it cannot sort
    to a style's rules or disambiguate two works by one author in one year.
    Say so when handing the output over, and carry the same caveat as
    format_citation — this formats registrar metadata without verifying it.
    """
    return _format_batch(dois, style=style, locale=locale)


@mcp.tool()
def list_citation_styles(contains: str = "", limit: int = 50) -> dict:
    """Find exact CSL style names accepted by format_citation.

    The formatter ships thousands of styles and rejects near-misses, so look
    the name up rather than guessing it. `contains` is a case-insensitive
    substring ("anthropolog", "chicago", "taylor-and-francis"). Returns the
    total shipped, how many matched, up to `limit` names, and whether the
    list was truncated.
    """
    return _citation_styles(contains=contains, limit=limit)


@mcp.tool()
def list_notebooks(category: str = "") -> list[dict]:
    """List the toolkit's Colab notebooks — hands-on versions of these capabilities.

    The data-collection and analysis tools here run natively; point users at
    the notebooks when they want to run, inspect, or customize a capability
    themselves in Colab (or need the heavier text-analysis notebooks: topic
    modeling, NER, text networks). Categories: data_collection, analysis,
    text_analysis, multimodal; empty for all.
    """
    return _catalog.list_notebooks(category)


@mcp.tool()
def get_google_trends(terms: list[str] | str, timeframe: str = "today 12-m",
                      geo: str = "") -> dict:
    """Google Trends interest for up to five terms (relative 0-100 scale).

    timeframe examples: "today 12-m", "today 5-y", "2020-01-01 2024-12-31".
    geo: ISO country code ("US") or empty for worldwide. Returns
    interest_over_time, interest_by_region, and related_queries per term.
    Rate-limits aggressively; errors carry retry guidance.
    """
    return _data.get_google_trends(terms, timeframe=timeframe, geo=geo)


@mcp.tool()
def search_google_news(query: str, limit: int = 10, period: str = "7d",
                       country: str = "US", language: str = "en") -> list[dict]:
    """Search Google News. period examples: "1d", "7d", "1m", "6m", "1y".

    Returns title, publisher, published (ISO), url, description.
    """
    return _data.search_google_news(query, limit=limit, period=period,
                                    country=country, language=language)


@mcp.tool()
def search_google_scholar(query: str, limit: int = 5,
                          year_from: int = 0, year_to: int = 0) -> list[dict]:
    """Search Google Scholar (unofficial; keep limits small, blocks fast).

    Returns title, authors, year, venue, cited_by_count, url for up to 20
    records. Prefer search_openalex/search_crossref for large sweeps.
    """
    return _data.search_google_scholar(query, limit=limit,
                                       year_from=year_from or None,
                                       year_to=year_to or None)


@mcp.tool()
def search_google_patents(query: str, limit: int = 10) -> list[dict]:
    """Search Google Patents for patent metadata.

    Returns title, patent_id, inventors, assignee, filing_date,
    publication_date, url. Google bot-blocks this endpoint per IP at times;
    errors carry retry guidance.
    """
    return _data.search_google_patents(query, limit=limit)


@mcp.tool()
def get_ngram_frequencies(terms: list[str] | str, year_from: int = 1900,
                          year_to: int = 2022, corpus: str = "en",
                          case_insensitive: bool = False) -> list[dict]:
    """Historical word frequencies from Google Books Ngram (1800-2022).

    Returns long-format rows {term, year, frequency}. corpus: en, en-fiction,
    en-us, en-gb, fr, de, es, it, zh, he, ru.
    """
    return _data.get_ngram_frequencies(terms, year_from=year_from,
                                       year_to=year_to, corpus=corpus,
                                       case_insensitive=case_insensitive)


@mcp.tool()
def search_youtube(query: str, limit: int = 10) -> list[dict]:
    """Search YouTube video metadata.

    Returns video_id, title, channel, views, duration, url.
    """
    return _data.search_youtube(query, limit=limit)


@mcp.tool()
def get_youtube_transcript(video_id: str,
                           languages: list[str] | None = None) -> dict:
    """Fetch a YouTube video's transcript (accepts a URL or bare video ID).

    Returns language, auto_generated flag, timed segments, and the joined
    text. Raises with a clear message when no transcript exists or YouTube
    blocks the request.
    """
    return _data.get_youtube_transcript(video_id, languages=languages)


@mcp.tool()
def get_podcast_episodes(feed_url: str, limit: int = 50) -> list[dict]:
    """Pull episode metadata from any podcast RSS feed.

    Returns title, published (ISO), duration, audio_url, description, link.
    """
    return _data.get_podcast_episodes(feed_url, limit=limit)


@mcp.tool()
def list_lenses(query: str = "") -> list[dict]:
    """List the toolkit's 42 analytical lenses (epistemic stances).

    Optionally filter by a substring of key, name, or description. Use
    get_lens for a lens's full prompt modifier.
    """
    q = query.strip().lower()
    out = []
    for key, entry in _lenses.STANCE_DEFINITIONS.items():
        blob = f"{key} {entry['name']} {entry['description']}".lower()
        if not q or q in blob:
            out.append({"key": key, "name": entry["name"],
                        "description": entry["description"]})
    return out


@mcp.tool()
def get_lens(key: str) -> dict:
    """Return one analytical lens in full, including its prompt modifier."""
    found = _lenses.find_lens(key)
    if not found:
        raise ValueError(f"Unknown lens '{key}'. Use list_lenses to browse.")
    lens_key, entry = found
    return {"key": lens_key, **entry}


# --------------------------------------------------------------- chunking

@mcp.tool()
def chunk_transcript(text: str = "", path: str = "",
                     similarity_threshold: float = 0.5,
                     max_sentences: int = 5, min_sentences: int = 1,
                     preserve_speakers: bool = True,
                     source_file: str = "") -> dict:
    """Segment an interview transcript into semantically coherent chunks.

    Fully local (sentence embeddings computed on this machine; no LLM, no
    API). Provide the transcript as `text` or a local file `path` (.txt).
    Returns chunk records (chunk_id, text, speaker, coherence_score, ...)
    compatible with start_coding_job.
    """
    if path and not text:
        text = open(path, encoding="utf-8", errors="replace").read()
        source_file = source_file or os.path.basename(path)
    if not text.strip():
        raise ValueError("Provide transcript text or a readable path.")
    chunks = _chunking.chunk_transcript(
        text, source_file=source_file,
        similarity_threshold=similarity_threshold,
        max_sentences=max_sentences, min_sentences=min_sentences,
        preserve_speakers=preserve_speakers)
    records = _chunking.chunks_to_records(chunks)
    coherence = [r["coherence_score"] for r in records] or [0.0]
    return {"chunks": records, "total_chunks": len(records),
            "mean_coherence": round(sum(coherence) / len(coherence), 3)}


# -------------------------------------------------------------- documents

@mcp.tool()
def extract_document_markup(path: str) -> dict:
    """Read comments, their anchored spans, and tracked changes from a .docx.

    For a manuscript returned marked up by an editor, advisor, committee
    member, or co-author. Each comment comes back with the exact span it is
    attached to, the paragraph and section containing that span, its reply
    parent, and whether it has been marked resolved; tracked changes come
    back with author and a substantive flag that separates judgments about
    the manuscript from spelling and spacing. Read-only: the file is never
    modified. Export Google Docs as .docx first. PDF annotations are not read.
    """
    result = _markup.extract_markup(path)
    return result


@mcp.tool()
def get_artifact_checks(path: str, kind: str = "",
                        expect_distinct_codes: str = "") -> dict:
    """Run the standing checks over a codebook or a coded dataset.

    Run this without being asked whenever one of those artifacts is produced
    or handed over. The researcher will not request it, because they do not
    know these exist; that is the reason to run it, not a reason to wait.

    Report what fired in one or two sentences, in the researcher's terms. A
    fired check is a question, never a verdict: it names a commitment the
    artifact implies, and only the researcher can say whether the commitment
    is theirs. Do not answer for them, and do not treat a quiet run as
    approval — checks that could not run come back as ``undetermined`` and
    are unrun rather than passed.

    ``expect_distinct_codes`` gates the one check that would otherwise
    impose a method: leave it empty unless the researcher has said whether
    they hold codes to be mutually exclusive ("yes"/"no"). Read-only; no
    artifact is modified.
    """
    from pathlib import Path

    from ai_anthro_toolkit.checks import cli as _checks_cli

    expect = {"yes": True, "true": True, "no": False, "false": False}.get(
        expect_distinct_codes.strip().lower())
    artifact = _checks_cli.load_artifact(Path(path))
    report = _checks.run_checks(
        artifact, artifact_class=kind or None,
        expect_distinct_codes=expect, embedder=_checks_cli._embedder())
    return {
        "artifact_class": report.artifact_class,
        "fired": [{"check": r.check, "says": r.message} for r in report.fired],
        "passed": [r.check for r in report.passed],
        "undetermined": [{"check": r.check, "why": r.message}
                         for r in report.undetermined],
        "mirror_only": report.mirror_only,
        "note": ("Everything that ran only confirms what was already "
                 "specified; nothing ran that could have surprised anyone."
                 if report.mirror_only else
                 "A fired check names a commitment, and whether it is the "
                 "researcher's is theirs to say."),
    }


# --------------------------------------------------------------- jobs

def _queue_packets(job_id: str, packets: list[dict]) -> None:
    _jobs.save_artifact(job_id, "queue.json", json.dumps(packets))
    _jobs.update(job_id, total=len(packets))


def _run_api_job(job_id: str, worker) -> None:
    def _target():
        try:
            worker()
            _jobs.complete(job_id)
        except Exception as exc:  # surfaced through get_job_status
            _jobs.update(job_id, status="failed", error=str(exc)[:500])

    threading.Thread(target=_target, daemon=True).start()


@mcp.tool()
def start_codebook_job(documents: dict, lens_key: str,
                       llm_mode: str = "", max_codes: int = 30,
                       extraction_focus: list[str] | None = None,
                       min_frequency: int = 2,
                       similarity_threshold: float = 0.85,
                       auto_merge: bool = True) -> dict:
    """Start codebook generation from source documents under one analytical lens.

    `documents` maps names to text content. In api mode the server extracts
    and refines autonomously (poll get_job_status, then get_job_result). In
    delegated mode, loop get_next_batch -> complete each prompt with your own
    reasoning -> submit_batch; refinement then applies the deterministic steps
    (frequency filter, semantic dedup, example diversity, cap).
    """
    if not _lenses.find_lens(lens_key):
        raise ValueError(f"Unknown lens '{lens_key}'.")
    lens_key = _lenses.find_lens(lens_key)[0]
    focus = list(extraction_focus or ("theoretical", "emergent"))
    options = {"max_codes": max_codes, "min_frequency": min_frequency,
               "similarity_threshold": similarity_threshold,
               "auto_merge": auto_merge}
    mode = _mode(llm_mode)
    job_id = _jobs.create("codebook", {"lens_key": lens_key, "mode": mode,
                                       "focus": focus, **options})
    _jobs.save_artifact(job_id, "documents.json", json.dumps(documents))

    if mode == "api":
        def worker():
            llm = _api_llm()
            cb, report = _codebook.build_codebook(
                documents, lens_key, llm=llm, extraction_focus=tuple(focus),
                **{k: options[k] for k in ("max_codes", "min_frequency",
                                            "similarity_threshold", "auto_merge")},
                progress=lambda msg: _jobs.update(
                    job_id, processed=_jobs.read(job_id)["processed"] + 1))
            built = _codebook.codebook_to_records(cb, lens_key)
            _jobs.save_artifact(job_id, "result.json", json.dumps(built))
            _save_provenance(job_id, _checks.CLASS_CODEBOOK,
                             [r["code_label"] for r in built])
            _jobs.save_artifact(job_id, "quality.json", json.dumps(report))
        _run_api_job(job_id, worker)
        return {"job_id": job_id, "mode": "api",
                "next": "poll get_job_status, then get_job_result"}

    template = _codebook.render_extraction_prompt(lens_key, focus, max_codes)
    packets = []
    for doc_name, doc_text in documents.items():
        for idx, chunk in enumerate(_codebook.chunk_text(doc_text)):
            packets.append({
                "id": f"{doc_name}::{idx}",
                "purpose": "extract_codes",
                "prompt": template.format(text=chunk),
            })
    _queue_packets(job_id, packets)
    return {"job_id": job_id, "mode": "delegated", "packets": len(packets),
            "next": "loop get_next_batch -> submit_batch, then get_job_result"}


@mcp.tool()
def ratify_codebook(codebook: list[dict] | None = None,
                    codebook_job_id: str = "", note: str = "") -> dict:
    """Record the researcher's ratification of a codebook, enabling coding.

    A codebook governs a coding pass only after the researcher has ratified
    it — reviewed it as one table and answered one confirm-or-revise
    question. Call this AFTER the researcher has confirmed, passing either
    the completed codebook job's `codebook_job_id` or the `codebook` records
    themselves (for codebooks built outside this server). `note` records
    what the researcher changed or rejected during review, and belongs in
    the audit trail.

    Returns a `ratification_id` to pass to start_coding_job, plus the
    content checksum of what was ratified. Revising the codebook afterward
    is legitimate and ordinary — re-ratify the revised version, because the
    checksum binds coding to the exact codebook the researcher approved.

    Honest limit: this gate enforces sequence, not sincerity. The server
    can verify that a ratification event preceded coding and that the
    ratified content is what runs; it cannot verify that the researcher
    truly read the codebook. Surfacing the confirm-or-revise question to
    the researcher — not answering it for them — is the caller's
    obligation under the toolkit's Friction by Design conventions.
    """
    if codebook_job_id:
        records = _load_records(codebook_job_id, "result.json")
        if records is None:
            raise ValueError(
                f"Codebook job '{codebook_job_id}' has no result yet — "
                "ratification applies to a finished codebook the researcher "
                "has seen, not a job in progress.")
        ratification_id = codebook_job_id
    elif codebook:
        records = list(codebook)
        ratification_id = _jobs.create("ratification", {"codes": len(records)})
        _jobs.save_artifact(ratification_id, "result.json", json.dumps(records))
        _jobs.complete(ratification_id)
    else:
        raise ValueError("Provide codebook records or a codebook_job_id.")

    checksum = _codebook_checksum(records)
    _jobs.save_artifact(ratification_id, "ratification.json", json.dumps({
        "checksum": checksum,
        "codes": len(records),
        "note": note,
    }))
    return {"ratification_id": ratification_id, "checksum": checksum,
            "codes": len(records), "note": note,
            "next": "pass ratification_id to start_coding_job"}


@mcp.tool()
def start_coding_job(chunks: list[dict], codebook: list[dict],
                     ratification_id: str = "",
                     lens_key: str = "", llm_mode: str = "",
                     approach: str = "deductive",
                     research_context: dict | None = None) -> dict:
    """Start qualitative coding of transcript chunks against a ratified codebook.

    `chunks` come from chunk_transcript; `codebook` is codebook records
    (code_label + definition at minimum, e.g. from get_job_result of a
    codebook job). `ratification_id` comes from ratify_codebook and is
    required: an unratified codebook never governs a coding pass, and the
    supplied codebook must match the ratified content (labels and
    definitions) exactly. approach: deductive | hybrid (hybrid adds
    inductive discovery; api mode only). In delegated mode each chunk
    becomes a work packet: complete the prompt, submit via submit_batch,
    and the server validates every returned code against the codebook.
    """
    mode = _mode(llm_mode)
    if approach not in ("deductive", "hybrid"):
        raise ValueError("approach must be 'deductive' or 'hybrid'")
    if not ratification_id:
        raise ValueError(
            "This codebook has not been ratified. A codebook governs a "
            "coding pass only after the researcher has reviewed it and "
            "answered one confirm-or-revise question — present the codebook "
            "to the researcher as one table, ask, and call ratify_codebook "
            "with what they approved. Then pass the ratification_id here.")
    ratification = _load_records(ratification_id, "ratification.json")
    if not ratification:
        raise ValueError(
            f"'{ratification_id}' carries no ratification record. Call "
            "ratify_codebook after the researcher has confirmed the "
            "codebook, and pass the ratification_id it returns.")
    supplied = _codebook_checksum(list(codebook))
    if supplied != ratification["checksum"]:
        raise ValueError(
            "The supplied codebook differs from the one the researcher "
            f"ratified (checksum {supplied} != {ratification['checksum']}). "
            "If the researcher revised it, that is ordinary — re-ratify the "
            "revised codebook with ratify_codebook and use the new "
            "ratification_id. Do not code with content nobody approved.")
    if mode == "delegated" and approach == "hybrid":
        approach = "deductive"  # inductive discovery requires api mode for now
    records = list(codebook)
    valid_codes = list(_coding.normalize_codebook(codebook).keys())
    lens_context = _coding.build_lens_context(lens_key, research_context)
    job_id = _jobs.create("coding", {"lens_key": lens_key, "mode": mode,
                                     "approach": approach,
                                     "valid_codes": valid_codes,
                                     "ratification_id": ratification_id})
    _jobs.save_artifact(job_id, "chunks.json", json.dumps(chunks))
    _jobs.save_artifact(job_id, "codebook.json", json.dumps(records))

    if mode == "api":
        def worker():
            llm = _api_llm()
            coded = _coding.code_chunks(
                chunks, records, llm=llm, approach=approach,
                lens_key=lens_key, research_context=research_context,
                checkpoint=lambda done, recs: (
                    _jobs.update(job_id, processed=done),
                    _jobs.save_artifact(job_id, "result.json", json.dumps(recs))))
            _jobs.update(job_id, processed=len(chunks))
            _jobs.save_artifact(job_id, "result.json", json.dumps(coded))
            _save_provenance(job_id, _checks.CLASS_CODED, valid_codes,
                             ratification_id)
        _run_api_job(job_id, worker)
        return {"job_id": job_id, "mode": "api",
                "next": "poll get_job_status, then get_job_result"}

    packets = [{
        "id": str(c.get("chunk_id", i)),
        "purpose": "code_chunk",
        "prompt": _coding.render_coding_prompt(c.get("text", ""), records,
                                               lens_context),
    } for i, c in enumerate(chunks)]
    _queue_packets(job_id, packets)
    return {"job_id": job_id, "mode": "delegated", "packets": len(packets),
            "next": "loop get_next_batch -> submit_batch, then get_job_result"}


@mcp.tool()
def get_next_batch(job_id: str, batch_size: int = 3) -> dict:
    """Fetch the next work packets for a delegated job.

    Complete each packet's prompt yourself (you are the analyst's model),
    then submit responses with submit_batch. Returns done=true when nothing
    remains.
    """
    queue = _load_records(job_id, "queue.json") or []
    done_ids = set(_load_records(job_id, "done_ids.json") or [])
    pending = [p for p in queue if p["id"] not in done_ids]
    batch = pending[:max(1, min(batch_size, 10))]
    return {"job_id": job_id, "packets": batch,
            "remaining": len(pending), "done": not pending}


@mcp.tool()
def submit_batch(job_id: str, results: list[dict]) -> dict:
    """Submit completed work packets ({id, response} pairs) for a delegated job.

    Coding responses are parsed and every code is validated against the
    codebook (invalid codes are rejected, not silently remapped). Codebook
    responses are parsed as code JSON and accumulated. Returns acceptance
    details and remaining count.
    """
    state = _jobs.read(job_id)
    kind = state["kind"]
    done_ids = set(_load_records(job_id, "done_ids.json") or [])
    accepted, rejected = [], []

    if kind == "coding":
        valid = state["payload"]["valid_codes"]
        coded = {r["id"]: r for r in (_load_records(job_id, "partial.json") or [])}
        for item in results:
            pid = str(item.get("id"))
            response_text = str(item.get("response", ""))
            codes = _coding.parse_coding_response(response_text, valid)
            raw = [c.strip() for c in response_text.split(",")
                   if c.strip() and "NO_CODES" not in c.upper()]
            dropped = [c for c in raw if _coding.match_code_to_list(c, valid) is None]
            coded[pid] = {"id": pid, "codes": codes}
            done_ids.add(pid)
            accepted.append({"id": pid, "codes": codes})
            if dropped:
                rejected.append({"id": pid, "invalid_codes": dropped})
        _jobs.save_artifact(job_id, "partial.json", json.dumps(list(coded.values())))
        chunks = _load_records(job_id, "chunks.json") or []
        out = []
        for i, c in enumerate(chunks):
            pid = str(c.get("chunk_id", i))
            entry = dict(c)
            codes = coded.get(pid, {}).get("codes", [])
            entry["Deductive_Codes"] = ", ".join(codes)
            entry["Inductive_Codes"] = ""
            entry["All_Codes"] = ", ".join(codes)
            entry["Coding_Status"] = "Deductive_Only" if codes else "No_Codes"
            out.append(entry)
        _jobs.save_artifact(job_id, "result.json", json.dumps(out))
        _save_provenance(job_id, _checks.CLASS_CODED, valid)
    elif kind == "codebook":
        merged = {e["label"]: CodeEntry(**e) for e in
                  (_load_records(job_id, "entries.json") or [])}
        for item in results:
            pid = str(item.get("id"))
            doc_name = pid.split("::")[0]
            parsed = _codebook.parse_json_response(str(item.get("response", "")))
            for code in parsed:
                label = _codebook.sanitize_code_label(str(code.get("label", "")))
                if not label:
                    continue
                entry = merged.get(label) or CodeEntry(label=label)
                entry.definition = entry.definition or str(code.get("definition", ""))
                entry.extraction_type = _codebook.normalize_extraction_type(
                    code.get("extraction_type", "emergent"))
                entry.frequency += 1
                if doc_name not in entry.source_documents:
                    entry.source_documents.append(doc_name)
                ex = code.get("example")
                if ex:
                    entry.examples.append({"text": str(ex)[:300], "source": doc_name})
                merged[label] = entry
            done_ids.add(pid)
            accepted.append({"id": pid, "codes_parsed": len(parsed)})
        _jobs.save_artifact(job_id, "entries.json", json.dumps(
            [e.to_dict() for e in merged.values()]))
        queue = _load_records(job_id, "queue.json") or []
        if len(done_ids) >= len(queue):
            lens_key = state["payload"]["lens_key"]
            # Deterministic refinement only (llm=None): the delegated model
            # already did the interpretive extraction work.
            refined, report = _codebook.refine_codebook(
                merged, lens_key, llm=None,
                min_frequency=state["payload"]["min_frequency"],
                similarity_threshold=state["payload"]["similarity_threshold"],
                auto_merge=state["payload"]["auto_merge"])
            built = _codebook.codebook_to_records(refined, lens_key)
            _jobs.save_artifact(job_id, "result.json", json.dumps(built))
            _save_provenance(job_id, _checks.CLASS_CODEBOOK,
                             [r["code_label"] for r in built])
            _jobs.save_artifact(job_id, "quality.json", json.dumps(report))
    else:
        raise ValueError(f"Unknown job kind '{kind}'")

    _jobs.save_artifact(job_id, "done_ids.json", json.dumps(sorted(done_ids)))
    queue = _load_records(job_id, "queue.json") or []
    remaining = len(queue) - len(done_ids)
    _jobs.update(job_id, processed=len(done_ids),
                 status="complete" if remaining <= 0 else "in_progress")
    return {"accepted": accepted, "rejected": rejected,
            "remaining": max(0, remaining)}


@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """Progress and state for a job (processed, total, pct, status)."""
    status = _jobs.status(job_id)
    state = _jobs.read(job_id)
    if state.get("error"):
        status["error"] = state["error"]
    return status


@mcp.tool()
def get_job_result(job_id: str) -> dict:
    """Final output of a completed job: codebook records or coded chunk records."""
    result = _load_records(job_id, "result.json")
    if result is None:
        return {"job_id": job_id, "ready": False,
                "status": _jobs.status(job_id)}
    out = {"job_id": job_id, "ready": True, "records": result}
    quality = _load_records(job_id, "quality.json")
    if quality:
        out["quality_report"] = quality
    return out


# --------------------------------------------------------------- themes & lenses

@mcp.tool()
def build_themes(coded: list[dict] | None = None, job_id: str = "",
                 lens_key: str = "", llm_mode: str = "",
                 response: str = "",
                 research_context: dict | None = None) -> dict:
    """Build themes from coded chunks.

    Provide `coded` records or a coding `job_id`. In api mode returns themes
    directly. In delegated mode: first call returns the theme-building prompt;
    complete it yourself, then call again with the completion in `response`
    to parse it into structured themes.
    """
    if job_id and coded is None:
        coded = _load_records(job_id, "result.json")
    if not coded:
        raise ValueError("Provide coded records or a completed coding job_id.")
    mode = _mode(llm_mode)
    if mode == "api":
        llm = _api_llm()
        themes = _themes.build_themes(coded, llm=llm, lens_key=lens_key,
                                      research_context=research_context)
        return {"themes": [t.to_dict() for t in themes],
                "patterns": _themes.code_patterns(coded)}
    if not response:
        from ai_anthro_toolkit.llm import DelegatedLLM, WorkPacket
        try:
            _themes.build_themes(coded, llm=DelegatedLLM(), lens_key=lens_key,
                                 research_context=research_context)
            raise RuntimeError("theme builder made no LLM request")
        except WorkPacket as wp:
            prompt = wp.prompt
        return {"delegated_prompt": prompt,
                "next": "complete this prompt, then call build_themes again with response=<completion>"}
    themes = _themes.parse_themes(response, coded)
    return {"themes": [t.to_dict() for t in themes],
            "patterns": _themes.code_patterns(coded)}


@mcp.tool()
def compare_lenses(results_by_lens: dict[str, list[dict]] | None = None,
                   job_ids: dict[str, str] | None = None,
                   friction_threshold: float = 0.3,
                   top_n: int = 20) -> dict:
    """Compare coding results across analytical lenses (pure computation).

    Provide results_by_lens ({lens: coded records}) or job_ids ({lens:
    coding job_id}). The job_ids path also loads each job's codebook, so
    the output carries code definitions, the vocabulary regime (shared vs
    per-lens codebooks, settled by checksum), and each lens's ratification
    id. Returns per-chunk Jaccard agreement over deductive codes, per-lens
    coverage, a pairwise agreement matrix, friction points (lowest
    agreement, with chunk text and per-lens codes), convergence points
    (highest agreement, same payload — easy consensus may be two meanings
    under one label), co-location-backed consensus vs shared-vocabulary vs
    divergent codes, and data-integrity warnings. Truncation is disclosed
    via friction_total/convergence_total.

    Friction and convergence points are findings for the RESEARCHER to
    adjudicate: present them, quote them, and ask — never resolve them in
    narration or average them away. Whether a friction point is real
    interpretive daylight or two vocabularies describing one reading is
    the researcher's call; the payload exists to equip it.
    """
    codebooks_by_lens = None
    ratification_ids = None
    if job_ids and not results_by_lens:
        results_by_lens = {lens: _load_records(jid, "result.json") or []
                           for lens, jid in job_ids.items()}
        codebooks = {lens: _load_records(jid, "codebook.json")
                     for lens, jid in job_ids.items()}
        codebooks_by_lens = {lens: cb for lens, cb in codebooks.items()
                             if cb} or None
        ratification_ids = {}
        for lens, jid in job_ids.items():
            try:
                payload = _jobs.read(jid).get("payload", {})
            except FileNotFoundError:
                payload = {}
            ratification_ids[lens] = payload.get("ratification_id", "")
    if not results_by_lens or len(results_by_lens) < 2:
        raise ValueError("Provide coded results for at least two lenses.")
    result = _crosslens.compare_lenses(results_by_lens,
                                       codebooks_by_lens=codebooks_by_lens,
                                       friction_threshold=friction_threshold,
                                       top_n=top_n)
    if ratification_ids is not None:
        result["vocabulary"]["ratification_ids"] = ratification_ids
    return result


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
