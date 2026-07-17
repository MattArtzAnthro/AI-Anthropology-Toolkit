"""AI Anthropology Toolkit MCP server (stdio).

Tool families:

- **Data collection**: search_openalex, search_pubmed.
- **Methodology**: list_lenses, get_lens — the 42-lens analytical registry.
- **Analysis pipeline**: chunk_transcript (local, no LLM), plus job-based
  codebook generation and qualitative coding, theme building, and cross-lens
  comparison.

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
from ai_anthro_toolkit import themes as _themes
from ai_anthro_toolkit import catalog as _catalog
from ai_anthro_toolkit.datasources import search_crossref as _crossref
from ai_anthro_toolkit.datasources import search_openalex as _openalex
from ai_anthro_toolkit.datasources import search_pubmed as _pubmed
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.llm import make_llm
from ai_anthro_toolkit.models import CodeEntry

mcp = FastMCP(
    "ai-anthropology",
    instructions=(
        "Tools for anthropological and qualitative research. Scholarly search: "
        "search_openalex (250M+ works; supports year, journal, and sort filters) "
        "and search_crossref (canonical DOI metadata); search_pubmed covers "
        "biomedical literature specifically. Many more data sources — Google "
        "Trends, News, Patents, Scholar, Books Ngram, YouTube search and "
        "transcripts, podcast RSS — are available as Colab notebooks: call "
        "list_notebooks to get names, descriptions, and one-click Colab links "
        "whenever a user asks about finding or collecting data. Methodology: "
        "list_lenses / get_lens expose the 42-lens analytical registry. Analysis "
        "pipeline: transcript chunking, codebook generation, coding, thematic "
        "analysis, and cross-lens comparison. LLM-dependent stages run in 'api' "
        "mode when ANTHROPIC_API_KEY is set, otherwise in 'delegated' mode: start "
        "a job, loop get_next_batch -> complete each prompt -> submit_batch, then "
        "get_job_result."
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
                                 "search_pubmed", "list_notebooks"],
            "methodology": ["list_lenses", "get_lens"],
            "analysis": ["chunk_transcript", "start_codebook_job",
                          "start_coding_job", "get_next_batch", "submit_batch",
                          "get_job_status", "get_job_result", "build_themes",
                          "compare_lenses"],
        },
        "llm_mode_default": _mode(None),
        "notebooks": ("Additional data sources (Google Trends/News/Patents/"
                       "Scholar/Ngram, YouTube, podcast RSS) and analysis "
                       "capabilities run as Colab notebooks — call "
                       "list_notebooks for descriptions and links."),
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
def list_notebooks(category: str = "") -> list[dict]:
    """List the toolkit's Colab notebooks — capabilities beyond these tools.

    Use this whenever a user asks about finding or collecting data: the
    data_collection notebooks cover Google Trends, Google News, Google
    Patents, Google Scholar, Google Books Ngram, YouTube search and
    transcripts, and podcast RSS feeds, each with a one-click Colab link.
    Categories: data_collection, analysis, text_analysis; empty for all.
    """
    return _catalog.list_notebooks(category)


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
            _jobs.save_artifact(job_id, "result.json", json.dumps(
                _codebook.codebook_to_records(cb, lens_key)))
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
def start_coding_job(chunks: list[dict], codebook: list[dict],
                     lens_key: str = "", llm_mode: str = "",
                     approach: str = "deductive",
                     research_context: dict | None = None) -> dict:
    """Start qualitative coding of transcript chunks against a codebook.

    `chunks` come from chunk_transcript; `codebook` is codebook records
    (code_label + definition at minimum, e.g. from get_job_result of a
    codebook job). approach: deductive | hybrid (hybrid adds inductive
    discovery; api mode only). In delegated mode each chunk becomes a work
    packet: complete the prompt, submit via submit_batch, and the server
    validates every returned code against the codebook.
    """
    mode = _mode(llm_mode)
    if approach not in ("deductive", "hybrid"):
        raise ValueError("approach must be 'deductive' or 'hybrid'")
    if mode == "delegated" and approach == "hybrid":
        approach = "deductive"  # inductive discovery requires api mode for now
    records = list(codebook)
    valid_codes = list(_coding.normalize_codebook(codebook).keys())
    lens_context = _coding.build_lens_context(lens_key, research_context)
    job_id = _jobs.create("coding", {"lens_key": lens_key, "mode": mode,
                                     "approach": approach,
                                     "valid_codes": valid_codes})
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
            _jobs.save_artifact(job_id, "result.json", json.dumps(
                _codebook.codebook_to_records(refined, lens_key)))
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
                   job_ids: dict[str, str] | None = None) -> dict:
    """Compare coding results across analytical lenses (pure computation).

    Provide results_by_lens ({lens: coded records}) or job_ids ({lens:
    coding job_id}). Returns per-chunk Jaccard agreement, pairwise agreement
    matrix, friction points (agreement < 0.3), and consensus vs divergent
    codes — sustaining interpretive divergence for the researcher to weigh.
    """
    if job_ids and not results_by_lens:
        results_by_lens = {lens: _load_records(jid, "result.json") or []
                           for lens, jid in job_ids.items()}
    if not results_by_lens or len(results_by_lens) < 2:
        raise ValueError("Provide coded results for at least two lenses.")
    return _crosslens.compare_lenses(results_by_lens)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
