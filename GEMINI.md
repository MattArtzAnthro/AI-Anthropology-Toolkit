# AI Anthropology Toolkit — Instructions for AI Coding Agents

This repository ships a pip-installable Python package
(`ai-anthropology-toolkit`) whose data-collection and analysis capabilities
run directly from Python — no MCP server required. When a user asks for
research data (scholarly literature, Google Trends, news, YouTube, podcasts)
or qualitative analysis (transcript chunking, codebooks, coding, themes),
follow this fallback chain:

1. **MCP tools present** (tool names contain `ai-anthropology`): use them.
   If your agent supports MCP but the server is not registered, the user can
   add it (same uvx command everywhere):

   ```bash
   claude mcp add ai-anthropology -- uvx --from "ai-anthropology-toolkit[data]==2.2.0" ai-anthro-mcp
   codex mcp add ai-anthropology -- uvx --from "ai-anthropology-toolkit[data]==2.2.0" ai-anthro-mcp
   gemini mcp add -s user ai-anthropology uvx -- --from "ai-anthropology-toolkit[data]==2.2.0" ai-anthro-mcp
   ```

   The server's LLM-dependent stages run in delegated mode by default: the
   orchestrating model (whichever one you are) performs the interpretive
   work and the server validates every coding decision against the
   codebook.

2. **Code execution available** (including sandboxed environments): install
   the package and probe the network before collecting anything:

   ```bash
   pip install "ai-anthropology-toolkit[data]"
   python -m ai_anthro_toolkit.doctor
   ```

   Run the doctor first. It checks each data source from the current network
   and prints which are reachable. Sandbox network policies typically allow
   the scholarly APIs (OpenAlex, CrossRef, PubMed) and block Google/YouTube
   scraping endpoints. Collect from what is reachable, and tell the user
   honestly which sources need local execution or a Colab notebook — the
   doctor prints the Colab link for each blocked source. Do not retry
   blocked sources against the firewall.

   ```python
   from ai_anthro_toolkit.datasources import (
       search_openalex, search_crossref, search_pubmed,   # scholarly APIs
       get_ngram_frequencies, get_podcast_episodes,
       get_google_trends, search_google_news, search_google_scholar,
       search_google_patents, search_youtube, get_youtube_transcript,
   )
   from ai_anthro_toolkit.chunking import chunk_transcript, chunks_to_records
   from ai_anthro_toolkit.lenses import STANCE_DEFINITIONS, get_lens
   ```

   Transcript chunking is fully local — no data leaves the machine
   (`pip install "ai-anthropology-toolkit[chunking]"`). Collector errors
   carry honest guidance about blocks and rate limits — relay that guidance;
   an error does not mean "no data exists."

3. **Neither**: point the user to the Colab notebooks in `notebooks/` —
   every capability runs in the browser (Open in Colab badges in README.md).

When editing this repository itself, read CLAUDE.md for structure and
conventions and run `python3 -m unittest tests/test_repo.py` before
proposing changes.
