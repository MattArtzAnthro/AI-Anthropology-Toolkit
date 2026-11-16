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

Analysis LLM work supports two modes. In **api** mode the server calls the
Anthropic API itself, with notebook-parity prompts; it needs ANTHROPIC_API_KEY
and an explicit opt-in, AAT_MODE=api, because a key in the environment is not
consent to spend it. In **delegated** mode (the default) the server never
calls a model: jobs queue work packets,
the orchestrating model completes them via get_next_batch/submit_batch, and
the server validates every submission against the codebook — keeping each
interpretive move visible to, and contestable by, the researcher.
"""

import functools
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import Field

from ai_anthro_toolkit import __version__, brand, design
from ai_anthro_toolkit import catalog as _catalog
from ai_anthro_toolkit import checks as _checks
from ai_anthro_toolkit import chunking as _chunking
from ai_anthro_toolkit import codebook as _codebook
from ai_anthro_toolkit import coding as _coding
from ai_anthro_toolkit import crosslens as _crosslens
from ai_anthro_toolkit import datasources as _data
from ai_anthro_toolkit import lenses as _lenses
from ai_anthro_toolkit import markup as _markup
from ai_anthro_toolkit import network as _network
from ai_anthro_toolkit import themes as _themes
from ai_anthro_toolkit._extras import MissingExtra
from ai_anthro_toolkit.checks.cli import LoadError
from ai_anthro_toolkit.datasources import format_citation as _format_citation
from ai_anthro_toolkit.datasources import format_citation_batch as _format_batch
from ai_anthro_toolkit.datasources import list_citation_styles as _citation_styles
from ai_anthro_toolkit.datasources import search_crossref as _crossref
from ai_anthro_toolkit.datasources import search_openalex as _openalex
from ai_anthro_toolkit.datasources import search_pubmed as _pubmed
from ai_anthro_toolkit.desk import a2ui as _a2ui
from ai_anthro_toolkit.desk import cards as _desk_cards
from ai_anthro_toolkit.desk import decisions as _desk_decisions
from ai_anthro_toolkit.desk import gate as _desk_gate
from ai_anthro_toolkit.desk import methods as _desk_methods
from ai_anthro_toolkit.desk import page as _desk_page
from ai_anthro_toolkit.desk import record as _desk_record
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.llm import make_llm
from ai_anthro_toolkit.models import CodeEntry

# Where a host that builds its own page finds the toolkit's tokens and components.
_DESIGN_SYSTEM = f"{brand.REPOSITORY}/tree/main/design/system"

mcp = MCPServer(
    "ai-anthropology",
    version=__version__,
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
        "Networks: build_network turns a coding job into a graph of codes, "
        "speakers, or lenses and returns a network_id; analyze_network lays it "
        "out and reads it, view_network shows it in chat, and export_network "
        "writes GEXF for Gephi, each taking that network_id. "
        "list_notebooks links Colab versions of "
        "these capabilities for users who want to run or customize them "
        "hands-on. Methodology: list_lenses / get_lens expose the 42-lens "
        "analytical registry. Documents: extract_document_markup reads the "
        "comments, anchored spans, and tracked changes out of a marked-up "
        ".docx, read-only. Analysis pipeline: transcript chunking, codebook "
        "generation, coding, thematic analysis, and cross-lens comparison. "
        "LLM-dependent stages run in 'delegated' mode unless the researcher "
        "has set AAT_MODE=api for the server (never request llm_mode='api' "
        "on their behalf): start a job, loop get_next_batch -> "
        "complete each prompt -> submit_batch, then get_job_result. Coding is "
        "gated: present the codebook to the researcher as one table, ask one "
        "confirm-or-revise question, call ratify_codebook with what they "
        "approved, and pass its ratification_id to start_coding_job (the "
        "server holds the ratified codebook, so it need not be sent again) — "
        "the server refuses unratified codebooks. Never ratify on the "
        "researcher's behalf. Any page you build from toolkit output "
        "keeps the credit, "
        f'"{brand.CREDIT}" linked to {brand.WEBSITE}, and takes its colours, '
        f"type and components from the toolkit design system ({_DESIGN_SYSTEM})."
    ),
)

_jobs = JobStore()

# Since mcp 2.x the SDK forwards an exception's text to the model only when it
# is a ToolError; anything else counts as a crash and the model reads just
# "Error executing tool <name>". Every message this server writes for the
# model (an unknown job, a blocked scraper, an unratified codebook) is one of
# these anticipated types, so they are relayed at the MCP boundary. The Python
# functions keep raising their own types for direct callers. Programming
# errors (TypeError, KeyError, ...) still stay on the server.
_RELAYED = (ValueError, RuntimeError, OSError, LoadError, MissingExtra)


def _tool(**kwargs):
    """Register a tool whose anticipated errors reach the model verbatim."""
    def register(fn):
        @functools.wraps(fn)
        def relay(*args, **kw):
            try:
                return fn(*args, **kw)
            except ToolError:
                raise
            except _RELAYED as exc:
                raise ToolError(str(exc)) from exc
        mcp.tool(**kwargs)(relay)
        return fn
    return register

# Tool annotations. Hints, not guarantees: they tell a host which calls are
# safe to run without asking. The jobs tools write only to the local job
# store; their open-world reach depends on the mode, so it is left unstated.
_LOCAL_READ = ToolAnnotations(read_only_hint=True, open_world_hint=False)
_WEB_READ = ToolAnnotations(read_only_hint=True, open_world_hint=True)
_LOCAL_WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False,
                               open_world_hint=False)
_JOB_WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False)
_FILE_WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=True,
                              idempotent_hint=True, open_world_hint=False)

# Parameter types shared by several tools, so each carries one description.
LlmMode = Annotated[Literal["", "delegated", "api"], Field(
    description="Leave empty. The server runs delegated unless the researcher "
                "set AAT_MODE=api; never pass 'api' on their behalf.")]
YearFrom = Annotated[int, Field(description="Earliest publication year; 0 for no lower bound.")]
YearTo = Annotated[int, Field(description="Latest publication year; 0 for no upper bound.")]
JobId = Annotated[str, Field(
    description="An ID a start_* tool or ratify_codebook returned, e.g. coding-1a2b3c4d.")]
LensKey = Annotated[str, Field(
    description="A lens key from list_lenses, e.g. 'interpretive'; empty for none.")]
NetworkId = Annotated[str, Field(
    description="The network_id build_network returned, e.g. network-1a2b3c4d.")]
GraphArg = Annotated[dict | None, Field(
    description="A graph dict, for networks built outside this server. "
                "Prefer network_id.")]
IncludeGraph = Annotated[bool, Field(
    description="Also return the full graph (nodes and edges). Off by default: "
                "it is large, and network_id carries it between tools.")]


# API mode spends the researcher's money, so it is never inferred from a key
# that happens to be in the environment, and the orchestrating model cannot
# switch it on per job: the researcher sets AAT_MODE=api in the server's own
# configuration (the "env" block of .mcp.json). Delegated is the default.
API_OPT_IN = "AAT_MODE"


def _api_opted_in() -> bool:
    return os.environ.get(API_OPT_IN, "").strip().lower() == "api"


def _mode(llm_mode: str | None) -> str:
    if llm_mode == "delegated":
        return "delegated"
    if llm_mode == "api" and not _api_opted_in():
        raise ValueError(
            "api mode calls the Anthropic API with the researcher's key and "
            "bills them, so it runs only when they have turned it on by "
            f"setting {API_OPT_IN}=api in the server's environment. It is not "
            "on here. Run this job in delegated mode (the default), or ask "
            "the researcher whether they want to enable api mode.")
    if llm_mode == "api":
        return "api"
    return "api" if _api_opted_in() else "delegated"


def _api_llm(model: str | None = None):
    # .get, not [...]: a missing key must reach make_llm, whose error says
    # what to do, rather than surface as a bare KeyError naming the variable.
    return make_llm("api", api_key=os.environ.get("ANTHROPIC_API_KEY"),
                    model=model or "claude-sonnet-5")


def _load_records(job_id: str, name: str):
    raw = _jobs.load_artifact(job_id, name)
    return json.loads(raw) if raw else None


# One checksum algorithm binds ratification to coding to cross-lens regime
# reporting; crosslens owns it so the package and server cannot drift.
_codebook_checksum = _crosslens.codebook_checksum


def _save_provenance(job_id: str, artifact_class: str, labels: list,
                     ratification_id: str = "",
                     artifact_file: str = "result.json",
                     similarity_method: str = "") -> None:
    """Write the stanza that lets a saved artifact describe itself later.

    A sidecar rather than a wrapper: ``result.json`` keeps its shape, so
    nothing downstream has to change to read it. Without this, an artifact
    that leaves the job directory makes no claim about which codebook it
    came from, and a standing check has nothing to read.
    """
    stanza = _checks.provenance_stanza(
        produced_by=f"ai-anthropology-toolkit {__version__}",
        codebook_labels=labels,
        artifact_class=artifact_class,
        ratification_id=ratification_id,
        artifact_file=artifact_file)
    if similarity_method:
        # How duplicate codes were found: "lexical-fallback" means by shared
        # words, without sentence-transformers, and that merges were only
        # suggested.
        stanza["similarity_method"] = similarity_method
    _jobs.save_artifact(job_id, _checks.PROVENANCE_SIDECAR, json.dumps(stanza))


# --------------------------------------------------------------- discovery

@_tool(annotations=_LOCAL_READ)
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
            "network": ["build_network", "analyze_network", "view_network",
                        "export_network"],
            "desk": ["build_ratification_desk", "record_desk_decisions", "get_decision_record",
                     "desk_sync", "desk_finish"],
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


@_tool(annotations=_WEB_READ)
def search_openalex(query: str, limit: int = 10,
                    year_from: YearFrom = 0, year_to: YearTo = 0,
                    venue: str = "",
                    sort: Literal["relevance", "recent", "cited"] = "relevance",
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


@_tool(annotations=_WEB_READ)
def search_crossref(query: str, limit: int = 10,
                    year_from: YearFrom = 0, year_to: YearTo = 0,
                    journal: str = "") -> list[dict]:
    """Search CrossRef for published works (canonical DOI metadata, very current).

    Filters: year_from/year_to bound the publication year; journal searches
    within a container title. Returns title, authors, journal, year, DOI,
    type, citation count, and publisher for up to `limit` records (max 100).
    """
    return _crossref(query, limit=limit,
                     year_from=year_from or None, year_to=year_to or None,
                     journal=journal or None)


@_tool(annotations=_WEB_READ)
def search_pubmed(query: str, limit: int = 10,
                  year_from: YearFrom = 0, year_to: YearTo = 0,
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


@_tool(annotations=_WEB_READ)
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


@_tool(annotations=_WEB_READ)
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


@_tool(annotations=_LOCAL_READ)
def list_citation_styles(contains: str = "", limit: int = 50) -> dict:
    """Find exact CSL style names accepted by format_citation.

    The formatter ships thousands of styles and rejects near-misses, so look
    the name up rather than guessing it. `contains` is a case-insensitive
    substring ("anthropolog", "chicago", "taylor-and-francis"). Returns the
    total shipped, how many matched, up to `limit` names, and whether the
    list was truncated.
    """
    return _citation_styles(contains=contains, limit=limit)


@_tool(annotations=_LOCAL_READ)
def list_notebooks(category: Literal["", "data_collection", "analysis", "text_analysis",
                                    "multimodal"] = "") -> list[dict]:
    """List the toolkit's Colab notebooks — hands-on versions of these capabilities.

    The data-collection and analysis tools here run natively; point users at
    the notebooks when they want to run, inspect, or customize a capability
    themselves in Colab (or need the heavier text-analysis notebooks: topic
    modeling, NER, text networks). Categories: data_collection, analysis,
    text_analysis, multimodal; empty for all.
    """
    return _catalog.list_notebooks(category)


@_tool(annotations=_WEB_READ)
def get_google_trends(terms: list[str] | str, timeframe: str = "today 12-m",
                      geo: str = "") -> dict:
    """Google Trends interest for up to five terms (relative 0-100 scale).

    timeframe examples: "today 12-m", "today 5-y", "2020-01-01 2024-12-31".
    geo: ISO country code ("US") or empty for worldwide. Returns
    interest_over_time, interest_by_region, and related_queries per term.
    Rate-limits aggressively; errors carry retry guidance.
    """
    return _data.get_google_trends(terms, timeframe=timeframe, geo=geo)


@_tool(annotations=_WEB_READ)
def search_google_news(query: str, limit: int = 10, period: str = "7d",
                       country: str = "US", language: str = "en") -> list[dict]:
    """Search Google News. period examples: "1d", "7d", "1m", "6m", "1y".

    Returns title, publisher, published (ISO), url, description.
    """
    return _data.search_google_news(query, limit=limit, period=period,
                                    country=country, language=language)


@_tool(annotations=_WEB_READ)
def search_google_scholar(query: str, limit: int = 5,
                          year_from: YearFrom = 0, year_to: YearTo = 0) -> list[dict]:
    """Search Google Scholar (unofficial; keep limits small, blocks fast).

    Returns title, authors, year, venue, cited_by_count, url for up to 20
    records. Prefer search_openalex/search_crossref for large sweeps.
    """
    return _data.search_google_scholar(query, limit=limit,
                                       year_from=year_from or None,
                                       year_to=year_to or None)


@_tool(annotations=_WEB_READ)
def search_google_patents(query: str, limit: int = 10) -> list[dict]:
    """Search Google Patents for patent metadata.

    Returns title, patent_id, inventors, assignee, filing_date,
    publication_date, url. Google bot-blocks this endpoint per IP at times;
    errors carry retry guidance.
    """
    return _data.search_google_patents(query, limit=limit)


@_tool(annotations=_WEB_READ)
def get_ngram_frequencies(terms: list[str] | str, year_from: int = 1900,
                          year_to: int = 2022,
                          corpus: Literal["en", "en-fiction", "en-us", "en-gb", "fr", "de",
                                          "es", "it", "zh", "he", "ru"] = "en",
                          case_insensitive: bool = False) -> list[dict]:
    """Historical word frequencies from Google Books Ngram (1800-2022).

    Returns long-format rows {term, year, frequency}. corpus: en, en-fiction,
    en-us, en-gb, fr, de, es, it, zh, he, ru.
    """
    return _data.get_ngram_frequencies(terms, year_from=year_from,
                                       year_to=year_to, corpus=corpus,
                                       case_insensitive=case_insensitive)


@_tool(annotations=_WEB_READ)
def search_youtube(query: str, limit: int = 10) -> list[dict]:
    """Search YouTube video metadata.

    Returns video_id, title, channel, views, duration, url.
    """
    return _data.search_youtube(query, limit=limit)


@_tool(annotations=_WEB_READ)
def get_youtube_transcript(video_id: str,
                           languages: list[str] | None = None) -> dict:
    """Fetch a YouTube video's transcript (accepts a URL or bare video ID).

    Returns language, auto_generated flag, timed segments, and the joined
    text. Raises with a clear message when no transcript exists or YouTube
    blocks the request.
    """
    return _data.get_youtube_transcript(video_id, languages=languages)


@_tool(annotations=_WEB_READ)
def get_podcast_episodes(feed_url: str, limit: int = 50) -> list[dict]:
    """Pull episode metadata from any podcast RSS feed.

    Returns title, published (ISO), duration, audio_url, description, link.
    """
    return _data.get_podcast_episodes(feed_url, limit=limit)


@_tool(annotations=_LOCAL_READ)
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


@_tool(annotations=_LOCAL_READ)
def get_lens(key: Annotated[str, Field(
        description="A lens key or name from list_lenses, e.g. 'interpretive'.")]) -> dict:
    """Return one analytical lens in full, including its prompt modifier."""
    found = _lenses.find_lens(key)
    if not found:
        raise ValueError(f"Unknown lens '{key}'. Use list_lenses to browse.")
    lens_key, entry = found
    return {"key": lens_key, **entry}


# --------------------------------------------------------------- chunking

@_tool(annotations=_LOCAL_READ)
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
        source = Path(path).expanduser()
        if not source.is_file():
            raise ValueError(f"No transcript file at {source.resolve()}. Pass an "
                             "absolute path to a .txt file, or the text itself.")
        text = source.read_text(encoding="utf-8", errors="replace")
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

@_tool(annotations=_LOCAL_READ)
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


@_tool(annotations=_LOCAL_READ)
def get_artifact_checks(
        path: Annotated[str, Field(description="Local path to a codebook or coded "
                                               "dataset (.json or .csv), or a job "
                                               "directory holding one.")],
        kind: Annotated[Literal["", "codebook", "coded_data"], Field(
            description="Empty to detect from the file.")] = "",
        expect_distinct_codes: Literal["", "yes", "no"] = "") -> dict:
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


@_tool(annotations=_JOB_WRITE)
def start_codebook_job(documents: Annotated[dict[str, str], Field(
                           description="Document name -> full text.")],
                       lens_key: Annotated[str, Field(
                           description="A lens key from list_lenses, e.g. 'interpretive'.")],
                       llm_mode: LlmMode = "", max_codes: int = 30,
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
    found = _lenses.find_lens(lens_key)
    if not found:
        raise ValueError(f"Unknown lens '{lens_key}'. Use list_lenses to browse.")
    lens_key = found[0]
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
                             [r["code_label"] for r in built],
                             similarity_method=report.get("similarity_method", ""))
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


@_tool(annotations=_LOCAL_WRITE)
def ratify_codebook(codebook: list[dict] | None = None,
                    codebook_job_id: Annotated[str, Field(
                        description="A completed codebook job's ID, e.g. "
                                    "codebook-1a2b3c4d.")] = "",
                    note: str = "") -> dict:
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
    held = {"checksum": checksum, "codes": len(records), "note": note, "method": "table", "version": "1.0"}
    # Ratifying a codebook job again keeps the desks already built on it.
    earlier = _load_records(ratification_id, "ratification.json") if codebook_job_id else None
    if earlier and earlier.get("desks"):
        held["desks"] = earlier["desks"]
    _jobs.save_artifact(ratification_id, "ratification.json", json.dumps(held))
    return {"ratification_id": ratification_id, "checksum": checksum,
            "codes": len(records), "note": note,
            "next": "pass ratification_id to start_coding_job"}


@_tool(annotations=_JOB_WRITE)
def start_coding_job(chunks: list[dict],
                     codebook: list[dict] | None = None,
                     ratification_id: Annotated[str, Field(
                         description="The ratification_id ratify_codebook returned.")] = "",
                     lens_key: LensKey = "", llm_mode: LlmMode = "",
                     approach: Literal["deductive", "hybrid"] = "deductive",
                     research_context: dict | None = None) -> dict:
    """Start qualitative coding of transcript chunks against a ratified codebook.

    `chunks` come from chunk_transcript. `ratification_id` comes from
    ratify_codebook and is required: an unratified codebook never governs a
    coding pass. The server already holds the ratified codebook, so leave
    `codebook` empty and it codes with exactly what the researcher approved.
    If you do pass `codebook` records, they must match the ratified content
    (labels and definitions) exactly. approach: deductive | hybrid (hybrid
    adds inductive discovery; api mode only). In delegated mode each chunk
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
    if not codebook:
        codebook = _load_records(ratification_id, "result.json")
        if not codebook:
            raise ValueError(
                f"Ratification '{ratification_id}' holds no codebook records. "
                "Re-ratify with ratify_codebook, or pass the ratified "
                "codebook records as `codebook`.")
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


@_tool(annotations=_LOCAL_READ)
def get_next_batch(job_id: JobId,
                   batch_size: Annotated[int, Field(description="Packets to return, 1 to 10.")] = 3
                   ) -> dict:
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


@_tool(annotations=_LOCAL_WRITE)
def submit_batch(job_id: JobId,
                 results: Annotated[list[dict], Field(
                     description='[{"id": <packet id>, "response": <your completion>}, ...]')]
                 ) -> dict:
    """Submit completed work packets ({id, response} pairs) for a delegated job.

    Coding responses are parsed and every code is validated against the
    codebook (invalid codes are rejected, not silently remapped). Codebook
    responses are parsed as code JSON and accumulated. Returns acceptance
    details and remaining count.
    """
    state = _jobs.read(job_id)
    kind = state["kind"]
    done_ids = set(_load_records(job_id, "done_ids.json") or [])
    accepted: list[dict] = []
    rejected: list[dict] = []

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
        _save_provenance(job_id, _checks.CLASS_CODED, valid,
                         state["payload"].get("ratification_id", ""))
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
                code_entry = merged.get(label) or CodeEntry(label=label)
                code_entry.definition = code_entry.definition or str(code.get("definition", ""))
                code_entry.extraction_type = _codebook.normalize_extraction_type(
                    code.get("extraction_type", "emergent"))
                code_entry.frequency += 1
                if doc_name not in code_entry.source_documents:
                    code_entry.source_documents.append(doc_name)
                ex = code.get("example")
                if ex:
                    code_entry.examples.append({"text": str(ex)[:300], "source": doc_name})
                merged[label] = code_entry
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
                             [r["code_label"] for r in built],
                             similarity_method=report.get("similarity_method", ""))
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


@_tool(annotations=_LOCAL_READ)
def get_job_status(job_id: JobId) -> dict:
    """Progress and state for a job (processed, total, pct, status)."""
    status = _jobs.status(job_id)
    state = _jobs.read(job_id)
    if state.get("error"):
        status["error"] = state["error"]
    return status


@_tool(annotations=_LOCAL_READ)
def get_job_result(job_id: JobId,
                   offset: Annotated[int, Field(description="First record to return.")] = 0,
                   limit: Annotated[int, Field(
                       description="Most records to return, 1 to 500.")] = 100,
                   include_text: Annotated[bool, Field(
                       description="False drops each chunk's text, keeping IDs, "
                                   "speakers, and codes: use it to count or tally.")] = True
                   ) -> dict:
    """Final output of a completed job: codebook records or coded chunk records.

    A job that is still running or has failed is not ready, even when it has
    written a checkpoint: partial records are never returned as the result.
    Records come a page at a time (`total`, `returned`, `next_offset`); a
    coded dataset of many interviews runs to several pages. Tools that take a
    coding job_id (build_themes, compare_lenses, build_network) read the
    whole result themselves, so fetch pages only to show or quote records.
    A coded dataset's result also carries `coding_status_counts` over all
    records (No_Codes, Deductive_Only, ...), so a count needs no paging; to
    tally codes record by record, pass include_text=false.
    """
    result = _load_records(job_id, "result.json")
    status = _jobs.status(job_id)
    if result is None or status["status"] != "complete":
        out = {"job_id": job_id, "ready": False, "status": status}
        error = _jobs.read(job_id).get("error")
        if error:
            out["error"] = error
        return out
    offset = max(0, offset)
    page = result[offset:offset + max(1, min(limit, 500))]
    if not include_text:
        page = [{k: v for k, v in r.items() if k != "text"} for r in page]
    out = {"job_id": job_id, "ready": True, "total": len(result),
           "returned": len(page), "offset": offset}
    statuses = [r.get("Coding_Status") for r in result if isinstance(r, dict)]
    if any(statuses):
        counts: dict[str, int] = {}
        for s in statuses:
            counts[str(s)] = counts.get(str(s), 0) + 1
        out["coding_status_counts"] = counts
    out["records"] = page
    if offset + len(page) < len(result):
        out["next_offset"] = offset + len(page)
        out["note"] = (f"{len(result) - offset - len(page)} more records; call "
                       f"again with offset={offset + len(page)}.")
    quality = _load_records(job_id, "quality.json")
    if quality:
        out["quality_report"] = quality
        if quality.get("similarity_method"):
            out["similarity_method"] = quality["similarity_method"]
    return out


# --------------------------------------------------------------- themes & lenses

@_tool(annotations=_JOB_WRITE)
def build_themes(coded: list[dict] | None = None, job_id: JobId = "",
                 lens_key: LensKey = "", llm_mode: LlmMode = "",
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


@_tool(annotations=_LOCAL_READ)
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
        ratification_ids = {lens: _jobs.read(jid).get("payload", {}).get(
            "ratification_id", "") for lens, jid in job_ids.items()}
    if not results_by_lens or len(results_by_lens) < 2:
        raise ValueError("Provide coded results for at least two lenses.")
    result = _crosslens.compare_lenses(results_by_lens,
                                       codebooks_by_lens=codebooks_by_lens,
                                       friction_threshold=friction_threshold,
                                       top_n=top_n)
    if ratification_ids is not None:
        result["vocabulary"]["ratification_ids"] = ratification_ids
    return result


# ─── Networks of coded material ─────────────────────────────────────────

def _store_network(graph: dict, network_id: str = "") -> str:
    if not network_id:
        network_id = _jobs.create("network", {"kind": graph.get("kind", "")})
        _jobs.complete(network_id)
    _jobs.save_artifact(network_id, "graph.json", json.dumps(graph))
    return network_id


def _resolve_network(graph: dict | None, network_id: str) -> tuple[dict, str]:
    """Find the graph a network tool should work on, by ID or by value.

    A dict that carries only a network_id (what build_network and
    analyze_network now return) resolves by ID, so callers that pass the
    previous tool's whole output keep working.
    """
    if not network_id and graph and "nodes" not in graph and graph.get("network_id"):
        network_id = graph["network_id"]
    if network_id:
        stored = _load_records(network_id, "graph.json")
        if stored is None:
            raise ValueError(f"Network '{network_id}' holds no graph. Build it "
                             "again with build_network.")
        return stored, network_id
    if graph and "nodes" in graph:
        return graph, ""
    raise ValueError("Pass the network_id build_network returned (or a graph "
                     "dict with nodes and edges).")


@_tool(annotations=_LOCAL_WRITE)
def build_network(records: Annotated[list[dict] | None, Field(
                      description="Coded records. Prefer job_id.")] = None,
                  job_id: Annotated[str, Field(
                      description="A completed coding job's ID; its records are "
                                  "read on the server.")] = "",
                  kind: Literal["code_cooccurrence", "speaker_code",
                                "lens_agreement"] = "code_cooccurrence",
                  min_weight: Annotated[float, Field(
                      description="Drop ties lighter than this after counting.")] = 1.0,
                  results_by_lens: Annotated[dict | None, Field(
                      description="{lens: coded records}; lens_agreement only.")] = None,
                  include_graph: IncludeGraph = False) -> dict:
    """Build a network from coded records, without Gephi.

    kind "code_cooccurrence": nodes are codes; two codes are tied each time
    they are applied to the same chunk, weighted by how many chunks. This is
    the network of an analysis: which codes travel together. kind
    "speaker_code": two-mode, speakers tied to the codes they voice. kind
    "lens_agreement": lenses tied by the number of chunks on which they
    applied a common code (pass results_by_lens={lens: coded records}).
    Give a coding `job_id` (preferred: the records never pass through the
    conversation) or the coded `records` themselves. Returns a `network_id`
    and node and edge counts; pass the network_id to analyze_network. Pure
    computation; nothing leaves the process.
    """
    if job_id and records is None:
        records = _load_records(job_id, "result.json")
        if records is None:
            raise ValueError(f"Job '{job_id}' has no result yet; wait for "
                             "get_job_status to report complete.")
    if records is None and kind != "lens_agreement":
        raise ValueError("Pass a coding job_id or the coded records.")
    graph = _network.build_network(records or [], kind=kind, min_weight=min_weight,
                                   results_by_lens=results_by_lens)
    network_id = _store_network(graph)
    out = {"network_id": network_id, "kind": kind,
           "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]),
           "next": "analyze_network(network_id=...)"}
    if include_graph:
        out["graph"] = graph
    return out


@_tool(annotations=_LOCAL_WRITE)
def analyze_network(graph: GraphArg = None, network_id: NetworkId = "",
                    seed: Annotated[int, Field(
                        description="Layout and community seed; same seed, same result.")] = 0,
                    community_resolution: Annotated[float, Field(
                        description="Louvain resolution; above 1 gives more, "
                                    "smaller communities.")] = 1.0,
                    include_graph: IncludeGraph = False) -> dict:
    """Lay out, size, color, and read a network built by build_network.

    Lays the graph out, sizes nodes by degree, colors them by modularity
    community, and records degree, weighted degree, betweenness, and
    community on every node. Returns a summary (density, components,
    isolates, community sizes, top nodes, a one-sentence reading) and the
    visual-QA reading Gephi AI uses (warnings and whether the community
    partition is topologically real). The reading describes hub dominance as
    a property of this network and never calls a distribution scale-free.
    Deterministic for a seed. The analyzed graph is kept under the same
    network_id; pass it to view_network or export_network.
    """
    source, network_id = _resolve_network(graph, network_id)
    result = _network.analyze_network(source, seed=seed,
                                      community_resolution=community_resolution)
    network_id = _store_network(result["graph"], network_id)
    out = {"network_id": network_id, "summary": result["summary"],
           "visual": result["visual"],
           "next": "view_network(network_id=...) or export_network(network_id=..., path=...)"}
    if include_graph:
        out["graph"] = result["graph"]
    return out


@mcp.resource("ui://ai-anthropology/network-view", name="network-view",
              description="Interactive in-chat view of a network built from coded material (MCP App).",
              mime_type="text/html;profile=mcp-app")
def network_view_resource() -> str:
    return _network.build_app_html()


@_tool(name="view_network", annotations=_LOCAL_READ,
          meta={"ui": {"resourceUri": "ui://ai-anthropology/network-view"}})
def view_network(graph: GraphArg = None, network_id: NetworkId = "",
                 title: str = "Code network",
                 caption_names: Annotated[dict[str, str] | None, Field(
                     description='Community number -> name, e.g. {"0": "Care work"}.')] = None
                 ) -> CallToolResult:
    """Show an analyzed network as an interactive map in chat (MCP App).

    Pass the network_id from analyze_network (an unanalyzed network is laid
    out first). Hosts that render MCP Apps (Claude Desktop, claude.ai) show
    the map inline: pan, zoom, hover a node's neighborhood, search, a legend
    of communities to click, and "Ask about it" on a node. caption_names
    labels communities. If no visual appears in this client, render
    structuredContent yourself as an interactive visualization: every node
    carries x, y, size, color, label, and attributes. Keep the node colors
    (they encode communities), take everything around them from the toolkit
    design system (https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/tree/main/design/system),
    and include the credit "AI Anthropology Toolkit by Matt Artz" linked to
    https://www.mattartz.me.
    """
    try:
        graph, network_id = _resolve_network(graph, network_id)
    except ValueError as exc:
        return CallToolResult(content=[TextContent(type="text", text=str(exc))], is_error=True)
    nodes = graph.get("nodes") or []
    if not nodes:
        return CallToolResult(content=[TextContent(type="text", text="The graph has no nodes; build and analyze one first.")],
                              is_error=True)
    if "x" not in nodes[0] or "community" not in (nodes[0].get("attributes") or {}):
        graph = _network.analyze_network(graph)["graph"]
    structured = {**graph, "title": title,
                  "captions": {"column": "community", "names": caption_names or {}}}
    summary = (f"Interactive view rendered: {len(nodes)} nodes and {len(graph.get('edges') or [])} ties. "
               "If no visual appeared in this client, render structuredContent yourself as an "
               "interactive visualization (nodes have x, y, color, size); keep the node colors, "
               f"take everything around them from the toolkit design system ({_DESIGN_SYSTEM}), "
               f'and carry the credit: "{brand.CREDIT}" linked to {brand.WEBSITE}.')
    return CallToolResult(content=[TextContent(type="text", text=summary)], structured_content=structured)


@_tool(annotations=_FILE_WRITE)
def export_network(path: Annotated[str, Field(
                       description="Where to write, absolute or starting with ~, "
                                   "e.g. ~/research/codes.gexf.")],
                   network_id: NetworkId = "", graph: GraphArg = None,
                   fmt: Literal["gexf", "graphml"] = "gexf",
                   overwrite: Annotated[bool, Field(
                       description="Replace a file already at path.")] = False) -> dict:
    """Write a network to GEXF (default) or GraphML with positions, sizes,
    and colors, so it opens in Gephi as a laid-out map and Gephi AI can take
    it further. Refuses to replace an existing file unless overwrite=true.
    A relative path resolves against the server's working directory, so the
    returned `path` is absolute: report that one. Returns path, format, and
    counts.
    """
    graph, _ = _resolve_network(graph, network_id)
    target = Path(path).expanduser().resolve()
    if target.exists() and not overwrite:
        raise ValueError(f"{target} already exists. Ask the researcher before "
                         "replacing it, then call again with overwrite=true, or "
                         "choose another path.")
    if not target.parent.is_dir():
        raise ValueError(f"The folder {target.parent} does not exist.")
    return _network.export_network(graph, str(target), fmt=fmt)


# --------------------------------------------------------- ratification desk

DESK_URI = "ui://ai-anthropology/ratification-desk"


@mcp.resource(DESK_URI, name="ratification-desk",
              description="The ratification desk, where the researcher decides each code or "
                          "disagreement in the conversation (MCP App).",
              mime_type="text/html;profile=mcp-app",
              meta={"ui": {"csp": {"resourceDomains": list(design.FONT_DOMAINS)}}})
def ratification_desk_resource() -> str:
    return _desk_page.app_shell()


def _finished_records(job_id: str, what: str) -> list[dict]:
    records = _load_records(job_id, "result.json")
    if records is None:
        raise ValueError(f"{what} '{job_id}' has no result yet; wait for get_job_status "
                         "to report complete.")
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise ValueError(f"{what} '{job_id}' holds no list of records in its result.json.")
    return records


def _job_of_kind(job_id: str, kind: str) -> dict:
    job = _jobs.read(job_id)  # refuses an ID the store did not issue
    if job.get("kind") != kind:
        raise ValueError(f"'{job_id}' is not a {kind} job.")
    return job


def _unused(stage: str, **given: object) -> None:
    """Refuses arguments the stage does not take, rather than ignoring them."""
    named = [name for name, value in given.items() if value]
    if named:
        raise ValueError(f"A {stage} desk does not take {', '.join(named)}.")


def _listed_desks(held: dict, ratification_id: str) -> list[str]:
    desks = held.get("desks", [])
    if not isinstance(desks, list) or not all(isinstance(d, str) for d in desks):
        raise ValueError(f"{ratification_id}'s list of desks is damaged; ratify the "
                         "codebook again before building a desk on it.")
    return desks


def _codebook_desk(codebook_job_id: str, codebook: list[dict] | None,
                   cases: dict | None) -> tuple[dict, list[dict], list[dict]]:
    """A codebook desk's payload, its source records, and the machine's record entries."""
    if codebook_job_id and codebook:
        raise ValueError("Pass either codebook_job_id or codebook, not both.")
    if codebook_job_id:
        _job_of_kind(codebook_job_id, "codebook")
        records = _finished_records(codebook_job_id, "Codebook job")
    elif codebook:
        records = list(codebook)
    else:
        raise ValueError("A codebook desk needs the codebook: pass codebook_job_id or "
                         "the codebook records.")
    if not cases:
        raise ValueError("A codebook desk needs cases for each code: pass cases as "
                         "{code_label: [{text, kind}, ...]}.")
    built = _desk_cards.codebook_cards(records, cases)
    # A codebook job is a model's draft; records the caller supplies may be the
    # researcher's own, so only the job's codes are recorded as drafted.
    drafted = [{"card_id": card["card_id"], "action": "draft",
                "detail": {"label": card["code_label"]}} for card in built] if codebook_job_id else []
    return {"stage": "codebook", "cards": built}, records, drafted


def _rulings_desk(coding_job_ids: list[str] | None,
                  proposals: dict | None) -> tuple[dict, list[dict]]:
    """A rulings desk's payload and the machine's record entries."""
    if not coding_job_ids or len(coding_job_ids) != 2:
        raise ValueError("A rulings desk compares two coding passes: pass exactly two "
                         "coding_job_ids.")
    if coding_job_ids[0] == coding_job_ids[1]:
        raise ValueError("A rulings desk compares two different coding jobs; "
                         f"'{coding_job_ids[0]}' is given twice.")
    coded, ratifications = [], []
    for job_id in coding_job_ids:
        job = _job_of_kind(job_id, "coding")
        ratification_id = (job.get("payload") or {}).get("ratification_id") or ""
        if not ratification_id:
            raise ValueError(f"Coding job '{job_id}' names no ratification; a rulings "
                             "desk needs passes coded under a ratified codebook.")
        coded.append(_finished_records(job_id, "Coding job"))
        ratifications.append(ratification_id)
    if ratifications[0] != ratifications[1]:
        raise ValueError(
            f"The two coding jobs were coded under different ratifications "
            f"({ratifications[0]} and {ratifications[1]}), so their disagreements "
            "would mix codebooks. Code both passes under one ratification_id.")
    in_force = ratifications[0]
    held = _load_records(in_force, "ratification.json")
    codebook = _load_records(in_force, "result.json")
    if not held or not codebook:
        raise ValueError(f"The ratification in force, {in_force}, holds no codebook.")
    _listed_desks(held, in_force)
    built = _desk_cards.rulings_cards(coded[0], coded[1], codebook, proposals)
    payload = {"stage": "rulings", "cards": built,
               "codes": [str(r["code_label"]).strip() for r in codebook],
               "exclusive": bool(held.get("exclusive", False)),
               "ratification_id": in_force, "coding_job_ids": list(coding_job_ids),
               # chunks both passes coded alike; rulings desks card only the rest
               "agreed": len(coded[0]) - len(built)}
    proposed = [{"card_id": card["card_id"], "action": "propose",
                 "detail": dict(card["proposal"])}
                for card in built if card["proposal"] is not None]
    return payload, proposed


@_tool(annotations=_JOB_WRITE, meta={"ui": {"resourceUri": DESK_URI}})
def build_ratification_desk(
        stage: Literal["codebook", "rulings"],
        title: Annotated[str, Field(description="The study or desk name shown as the page header.")] = "",
        codebook_job_id: Annotated[str, Field(
            description="Codebook stage: a completed codebook job's ID. Or pass codebook.")] = "",
        codebook: Annotated[list[dict] | None, Field(
            description="Codebook stage: the codebook records, for codebooks built elsewhere.")] = None,
        cases: Annotated[dict[str, list[dict]] | None, Field(
            description="Codebook stage: {code_label: [{text, kind, case_id?, source?}]}, "
                        "kind 'typical' or 'borderline'; every code needs a case.")] = None,
        coding_job_ids: Annotated[list[str] | None, Field(
            description="Rulings stage: exactly two coding job IDs, coded under one ratification.")] = None,
        proposals: Annotated[dict[str, dict] | None, Field(
            description="Rulings stage, optional: {chunk_id: {codes, rationale}}, a proposed "
                        "resolution per disagreement; empty codes proposes that none apply.")] = None,
        blind_first: Annotated[bool, Field(
            description="Rulings stage: hide each proposal until the researcher has ruled. "
                        "Leave on unless the researcher turns it off.")] = True,
) -> CallToolResult:
    """Build a ratification desk: a page where the researcher decides, one card at a time.

    stage "codebook": one card per code with the cases it would take, typical
    and borderline; the researcher adopts, rewords, merges, splits or deletes
    each code and says whether codes are mutually exclusive. Pass the codebook
    (codebook_job_id or codebook) and cases for every code.

    stage "rulings": one card per chunk on which two coding passes disagree;
    the researcher rules on each, and a ruling that states a rule amends the
    codebook. Pass two coding_job_ids coded under the same ratification, and
    optionally proposals, which stay hidden until each ruling (blind_first).

    Returns a desk_id and the path of a self-contained page. Hosts that render
    MCP Apps show the desk in the conversation. The researcher decides in the
    desk; never decide, rule or ratify on the researcher's behalf.
    """
    return _build_desk(stage, title, codebook_job_id, codebook, cases, coding_job_ids,
                       proposals, blind_first)


def _build_desk(stage: str, title: str, codebook_job_id: str, codebook: list[dict] | None,
                cases: dict | None, coding_job_ids: list[str] | None, proposals: dict | None,
                blind_first: bool) -> CallToolResult:
    if stage == "codebook":
        _unused(stage, coding_job_ids=coding_job_ids, proposals=proposals,
                blind_first=not blind_first)
        payload, source, entries = _codebook_desk(codebook_job_id, codebook, cases)
    elif stage == "rulings":
        _unused(stage, codebook_job_id=codebook_job_id, codebook=codebook, cases=cases)
        payload, entries = _rulings_desk(coding_job_ids, proposals)
        payload["blind_first"] = bool(blind_first)
        source = None
    else:
        raise ValueError("stage is 'codebook' or 'rulings'.")
    payload.update(title=title.strip(), card_checksum=_desk_cards.checksum(payload["cards"]),
                   built_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    desk_id = _jobs.create("desk", payload)
    desk = dict(payload, desk_id=desk_id)
    if source is not None:
        _jobs.save_artifact(desk_id, "codebook.json", json.dumps(source))
    path = _jobs.save_artifact(desk_id, "desk.html", _desk_page.render_page(desk))
    built: dict = {"stage": stage, "cards": len(payload["cards"])}
    if stage == "rulings":
        built.update(blind_first=payload["blind_first"], ratification_id=payload["ratification_id"])
    _desk_record.append(_jobs, desk_id, [
        dict(entry, surface="server", decided_by="machine", note="")
        for entry in [{"card_id": "desk", "action": "build", "detail": built}, *entries]])
    if stage == "rulings":
        held = _load_records(payload["ratification_id"], "ratification.json")
        held["desks"] = [*_listed_desks(held, payload["ratification_id"]), desk_id]
        _jobs.save_artifact(payload["ratification_id"], "ratification.json", json.dumps(held))
    kind = "code" if stage == "codebook" else "disagreement"
    count = len(payload["cards"])
    text = (f"Desk {desk_id} built: {count} {kind}{'' if count == 1 else 's'} to decide. "
            "The researcher decides in the desk, card by card; do not record decisions "
            "for them. If no desk appeared in this client, give the researcher the page "
            f"to open in a browser: {path}")
    structured = {"desk_id": desk_id, "stage": stage, "cards": count,
                  "card_checksum": payload["card_checksum"], "page": str(path),
                  "a2ui": _a2ui.surface(desk)}
    return CallToolResult(content=[TextContent(type="text", text=text)],
                          structured_content=structured)


@_tool(annotations=_LOCAL_WRITE)
def record_desk_decisions(
        desk_id: Annotated[str, Field(description="The desk_id build_ratification_desk returned.")],
        decisions: Annotated[dict, Field(
            description='The decisions document, {"schema": "aat/desk-decisions@1", "desk_id", '
                        '"card_checksum", "exclusive", "decisions": {card_id: decision}}.')],
        surface: Annotated[Literal["chat", "page"], Field(
            description="'page' for a document the researcher copied from the desk page; "
                        "'chat' for decisions the researcher stated in the conversation.")],
) -> dict:
    """Apply the researcher's decisions on a desk, from the desk page or the conversation.

    Use this only for decisions the researcher made: the JSON the desk page's
    "Copy decisions as JSON" gives (surface "page"), or a document built from
    what the researcher said in the conversation, card by card (surface
    "chat"). Never fill in, infer or complete a decision the researcher did
    not make; a desk that runs in the conversation as an MCP App records its
    own decisions.

    A codebook desk needs an action on every code and an answer on whether
    codes are mutually exclusive; it returns the ratification_id to pass to
    start_coding_job. A rulings desk needs a ruling or exclusion on every
    card; a ruling that states a rule amends the codebook and returns the
    amended version's ratification_id. Every decision is checked against the
    desk first; nothing is written unless all of them pass, and the refusal
    names each problem. The same decisions sent again return the same result.
    """
    if surface not in ("chat", "page"):
        raise ValueError(f"surface is 'chat' or 'page', not {surface!r}; decisions made in the "
                         "desk's MCP App are recorded by the desk itself.")
    with _desk_lock:
        _desk_gate.load_desk(_jobs, desk_id)  # refuses an ID that is not a desk before reading it
        if _jobs.load_artifact(desk_id, _SAVED) is not None:
            raise ValueError(
                f"{desk_id} is open in its view in the conversation, which keeps each decision "
                "as it is made. The researcher finishes it there with Ratify; it cannot be "
                "finished from here. To decide in chat instead, build a new desk.")
        return _desk_gate.apply(_jobs, desk_id, decisions, surface)


@_tool(annotations=_LOCAL_READ)
def get_decision_record(
        ratification_id: Annotated[str, Field(
            description="A ratification_id from ratify_codebook, record_desk_decisions or a desk's Ratify.")] = "",
        desk_id: Annotated[str, Field(description="A desk_id from build_ratification_desk.")] = "",
) -> dict:
    """The decision record behind a ratification or a desk, and a draft methods paragraph.

    Pass one of the two IDs. A ratification reads every desk in its lineage,
    from the first ratification to this one. A finished desk reads the
    lineage of the ratification it made; an unfinished rulings desk, that of
    the ratification in force; an unfinished codebook desk, its own record.

    Each entry names its desk, card, action, note, time, surface, and whether
    the researcher or the machine made it. The paragraph's counts are taken
    from the record, and it says it was assembled, not written: give it to the
    researcher as a draft to check against their own account, not as their
    methods section.
    """
    return _decision_record(ratification_id.strip(), desk_id.strip())


def _decision_record(ratification_id: str, desk_id: str) -> dict:
    if not ratification_id and not desk_id:
        raise ValueError("Pass ratification_id or desk_id.")
    if ratification_id and desk_id:
        raise ValueError("Pass ratification_id or desk_id, not both.")
    if desk_id:
        desk = _desk_gate.load_desk(_jobs, desk_id)
        finished = _load_records(desk_id, "finished.json")
        if finished is not None:
            ratification_id = finished["outcome"]["ratification_id"]
        elif desk["stage"] == "rulings":
            ratification_id = desk["ratification_id"]
        else:
            entries = _desk_record.read(_jobs, desk_id)
            return {"ratification_id": None, "desk_id": desk_id, "record": entries,
                    "paragraph": _desk_methods.paragraph(entries)}
    _job_of_kind(ratification_id, "ratification")
    entries = _desk_record.read_lineage(_jobs, ratification_id)
    return {"ratification_id": ratification_id, "desk_id": desk_id or None, "record": entries,
            "paragraph": _desk_methods.paragraph(entries)}


# Decisions saved one at a time through the desk's MCP App: {"decisions", "exclusive"}.
# The view writes it when it first opens the desk, which holds the desk for the view
# (R7.8): from then on only its Ratify control, desk_finish, can finish it.
_SAVED = "saved.json"
_NOTHING_SAVED: dict[str, Any] = {"decisions": {}, "exclusive": None}
# Saving reads, changes and writes saved.json, and finishing reads it and writes the
# outcome; each runs whole, one at a time, so no save is lost or lands mid-finish.
_desk_lock = threading.RLock()


def _saved(desk_id: str) -> dict:
    saved = _load_records(desk_id, _SAVED)
    if saved is None:
        return dict(_NOTHING_SAVED)
    if not (isinstance(saved, dict) and set(saved) == {"decisions", "exclusive"}
            and isinstance(saved["decisions"], dict)
            and all(isinstance(d, dict) for d in saved["decisions"].values())
            and saved["exclusive"] in (True, False, None)):
        raise ValueError(f"The decisions saved for {desk_id} are damaged; build the desk "
                         "again to decide it.")
    return saved


@_tool(annotations=_LOCAL_WRITE, meta={"ui": {"resourceUri": DESK_URI, "visibility": ["app"]}})
def desk_sync(desk_id: Annotated[str, Field(description="The desk shown in the view.")],
              action: Annotated[dict | None, Field(
                  description="The A2UI action a Save control sent: {name, context}. "
                              "Omit to load the desk as saved.")] = None) -> CallToolResult:
    """The desk's view saves one decision, or loads the desk with its saved decisions.

    Called only by the ratification desk's view, when the researcher presses a
    Save control in it (app-only: the model cannot call it). Checks the decision
    against the desk, keeps it on the server, and returns the A2UI messages
    that follow: the card marked decided and the next one opened, and a ruling's
    proposal once that ruling is saved. Without an action, returns the whole desk
    with every saved decision restored.
    """
    return _for_the_view(_sync(desk_id, action))


def _sync(desk_id: str, action: dict | None) -> dict:
    with _desk_lock:
        return _sync_held(desk_id, action)


def _sync_held(desk_id: str, action: dict | None) -> dict:
    desk = _desk_gate.load_desk(_jobs, desk_id)
    finished = _load_records(desk_id, "finished.json")
    saved = _saved(desk_id)
    if action is None:
        if finished is None and _jobs.load_artifact(desk_id, _SAVED) is None:
            _jobs.save_artifact(desk_id, _SAVED, json.dumps(saved))  # the view holds the desk
        return {"desk_id": desk_id, "saved": len(saved["decisions"]),
                "finished": finished["outcome"] if finished else None,
                "document": _document(desk_id, desk, saved), "a2ui": _a2ui.restore(desk, saved)}
    if finished is not None:
        raise ValueError(f"{desk_id} is finished; its decisions can no longer change.")
    if _jobs.load_artifact(desk_id, "finishing.json") is not None:
        raise ValueError("Ratify was interrupted before it finished. Press Ratify again to "
                         "complete it; the decisions cannot change until it does.")
    if not isinstance(action, dict) or not isinstance(action.get("name"), str) \
            or not isinstance(action.get("context"), dict):
        raise ValueError("An action is {name, context}, as the desk's Save control sends it.")
    card_id, decision = _a2ui.decision_from_action(desk, action["name"], action["context"])
    if card_id == "exclusivity":
        candidate = dict(saved, exclusive=decision["exclusive"])
    else:
        candidate = dict(saved, decisions={**saved["decisions"], card_id: decision})
    codebook = (_load_records(desk_id, "codebook.json") or []) if desk["stage"] == "codebook" else None
    _desk_gate.check_save(desk, candidate, codebook)
    _jobs.save_artifact(desk_id, _SAVED, json.dumps(candidate))
    return {"desk_id": desk_id, "saved": len(candidate["decisions"]),
            "document": _document(desk_id, desk, candidate),
            "a2ui": _a2ui.after_decision(desk, candidate, card_id)}


def _document(desk_id: str, desk: dict, saved: dict) -> dict:
    """The decisions document for what the view has saved: what its Copy control copies
    and what Ratify applies."""
    return {"schema": _desk_decisions.SCHEMA, "desk_id": desk_id, "card_checksum": desk["card_checksum"],
            "exclusive": saved["exclusive"], "decisions": saved["decisions"]}


@_tool(annotations=_LOCAL_WRITE, meta={"ui": {"resourceUri": DESK_URI, "visibility": ["app"]}})
def desk_finish(desk_id: Annotated[str, Field(description="The desk shown in the view.")]) -> CallToolResult:
    """The desk's view ratifies: applies every decision saved in it through the import gate.

    Called only by the ratification desk's view, when the researcher presses
    Ratify (app-only: the model cannot call it). Refuses, writing nothing, while
    any card or question is undecided. Returns the outcome, with the
    ratification_id to pass to start_coding_job.
    """
    return _for_the_view(_finish(desk_id))


def _for_the_view(out: dict[str, Any]) -> CallToolResult:
    """An app-only tool's answer: the view reads structuredContent; the text carries the
    same JSON for a host that passes on only the text."""
    return CallToolResult(content=[TextContent(type="text", text=json.dumps(out))],
                          structured_content=out)


def _finish(desk_id: str) -> dict:
    with _desk_lock:
        desk = _desk_gate.load_desk(_jobs, desk_id)
        return _desk_gate.apply(_jobs, desk_id, _document(desk_id, desk, _saved(desk_id)), "app")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
