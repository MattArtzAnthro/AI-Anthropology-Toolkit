# MCP Workflow Guide

Reference file for driving the analysis pipeline through the toolkit's MCP
server. Loaded by the qualitative-analysis SKILL.md when `ai-anthropology`
MCP tools are available in the session (tool names begin with
`mcp__` and include `ai-anthropology`). When they are available, prefer them
over conversational hand-processing for any corpus beyond a few documents;
when they are not, work through the fallback chain in "When the MCP Tools
Are Absent" below.

---

## Task-to-Tool Mapping

| Analysis task | Tool sequence |
|---------------|---------------|
| Segment a transcript | `chunk_transcript` (fully local — no data leaves the machine) |
| Browse or select lenses | `list_lenses`, `get_lens` |
| Build a codebook from literature | `start_codebook_job` → (delegated: `get_next_batch`/`submit_batch` loop) → `get_job_result` |
| Code chunks against a codebook | `start_coding_job` → (delegated loop) → `get_job_result` |
| Build themes from coded data | `build_themes` (two-step in delegated mode: fetch prompt, complete it, resubmit) |
| Compare lenses on the same data | one coding job per lens, then `compare_lenses` |
| Collect source material | `search_openalex` / `search_crossref` / `search_google_scholar` and the other data-collection tools |
| Point the user at a hands-on version | `list_notebooks` |

## Execution Modes

Check `toolkit_info` for the session's default mode.

- **api mode** (ANTHROPIC_API_KEY set on the server): jobs run autonomously;
  poll `get_job_status`, then fetch `get_job_result`. Suited to unattended
  runs and larger corpora.
- **delegated mode** (default without a key): the server never calls a
  model — you are the analyst's model. Loop `get_next_batch`, complete each
  packet's prompt with genuine interpretive care (the prompts carry the
  codebook and lens framing), and `submit_batch`. The server validates every
  code you return against the codebook and rejects anything not in it, so
  report rejections to the researcher rather than retrying silently.

## When the MCP Tools Are Absent

If the session has code execution (a sandbox, a CLI environment), the same
package the MCP server is built from installs from PyPI:

```bash
pip install "ai-anthropology-toolkit[data]"
python -m ai_anthro_toolkit.doctor
```

Run the doctor first — it probes each data source from the current network.
Sandbox policies typically allow the scholarly APIs (OpenAlex, CrossRef,
PubMed) and block Google/YouTube scraping endpoints. Collect from reachable
sources via `ai_anthro_toolkit.datasources`, chunk transcripts locally via
`ai_anthro_toolkit.chunking.chunk_transcript` (needs the `[chunking]`
extra), and use `ai_anthro_toolkit.lenses` for lens framing. Tell the
researcher honestly which sources the environment blocks and hand them the
Colab link the doctor prints — do not retry against the firewall, and do
not substitute a proxy source without saying so.

If there is no code execution either, fall back to conversational analysis
or the Colab notebooks per the notebook-pipeline-guide.

## Working Practices

- Keep the researcher in the loop at stage boundaries: show the codebook
  before coding with it, surface friction points from `compare_lenses`
  rather than averaging them away, and quote evidence verbatim from
  `get_job_result` records.
- Multi-lens designs: run `start_coding_job` once per lens over the same
  chunks, then `compare_lenses` with the collected job ids (the job path
  also resolves code definitions and the vocabulary regime into the
  output).
- Know what agreement measures: divergence in labeling, which tracks
  divergence in reading only when the lenses share a ratified codebook —
  check the output's `vocabulary.regime`, and treat agreement across
  per-lens codebooks as structurally deflated rather than as findings.
  Present friction points AND convergence points to the researcher with
  their chunk text and code definitions; whether a friction point is real
  interpretive daylight or two vocabularies describing one reading is the
  researcher's call, and so is whether an easy consensus is real. Never
  resolve either in narration. Relay `warnings` (missing or duplicate
  chunk ids, text mismatches) and the `friction_total` versus returned
  count — the threshold selects attention, not existence.
- Data-collection tools can rate-limit or block (Google sources
  especially); their errors carry honest guidance — relay it instead of
  treating an error as "no data exists."
