# MCP Workflow Guide

Reference file for driving the analysis pipeline through the toolkit's MCP
server. Loaded by the qualitative-analysis SKILL.md when `ai-anthropology`
MCP tools are available in the session (tool names begin with
`mcp__` and include `ai-anthropology`). When they are available, prefer them
over conversational hand-processing for any corpus beyond a few documents;
when they are not, fall back to conversational analysis or the Colab
notebooks per the notebook-pipeline-guide.

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

## Working Practices

- Keep the researcher in the loop at stage boundaries: show the codebook
  before coding with it, surface friction points from `compare_lenses`
  rather than averaging them away, and quote evidence verbatim from
  `get_job_result` records.
- Multi-lens designs: run `start_coding_job` once per lens over the same
  chunks, then `compare_lenses` with the collected job results.
- Data-collection tools can rate-limit or block (Google sources
  especially); their errors carry honest guidance — relay it instead of
  treating an error as "no data exists."
