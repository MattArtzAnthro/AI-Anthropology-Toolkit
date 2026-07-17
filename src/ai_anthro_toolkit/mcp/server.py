"""AI Anthropology Toolkit MCP server (stdio).

Phase 1 tool surface: scholarly data collection (OpenAlex, PubMed) and the
canonical analytical-lens registry. Analysis tools (chunking, codebook
building, coding, themes) arrive with the core-package extraction.
"""

from mcp.server.fastmcp import FastMCP

from ai_anthro_toolkit import __version__
from ai_anthro_toolkit import lenses as _lenses
from ai_anthro_toolkit.datasources import search_openalex as _openalex
from ai_anthro_toolkit.datasources import search_pubmed as _pubmed

mcp = FastMCP(
    "ai-anthropology",
    instructions=(
        "Tools for anthropological and qualitative research. Data collection: "
        "search_openalex (250M+ scholarly works, all disciplines), search_pubmed "
        "(biomedical literature). Methodology: list_lenses and get_lens expose the "
        "toolkit's 42 analytical lenses (epistemic stances) used to frame "
        "qualitative codebook generation and coding."
    ),
)


@mcp.tool()
def search_openalex(query: str, limit: int = 10) -> list[dict]:
    """Search OpenAlex for scholarly works across all disciplines.

    Returns title, authors, year, venue, DOI, citation count, and open-access
    status for up to `limit` works (max 100).
    """
    return _openalex(query, limit=limit)


@mcp.tool()
def search_pubmed(query: str, limit: int = 10) -> list[dict]:
    """Search PubMed for biomedical and health literature.

    Supports full PubMed query syntax (e.g. 'medical anthropology[MeSH]').
    Returns PMID, title, authors, journal, publication date, and DOI for up
    to `limit` records (max 100). No API key required for small volumes.
    """
    return _pubmed(query, limit=limit)


@mcp.tool()
def list_lenses(query: str = "") -> list[dict]:
    """List the toolkit's 42 analytical lenses (epistemic stances).

    Optionally filter by a substring of the lens key, name, or description.
    Returns key, name, and description for each match; use get_lens for the
    full prompt modifier.
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
    """Return one analytical lens in full, including its prompt modifier.

    Accepts a registry key (e.g. 'critical_race') or display name
    (e.g. 'Critical Race'), case-insensitively.
    """
    found = _lenses.find_lens(key)
    if not found:
        known = ", ".join(sorted(_lenses.STANCE_DEFINITIONS))
        raise ValueError(f"Unknown lens '{key}'. Known keys: {known}")
    lens_key, entry = found
    return {"key": lens_key, **entry}


@mcp.tool()
def toolkit_info() -> dict:
    """Describe this server: version, tool families, and the notebook pipeline it mirrors."""
    return {
        "name": "AI Anthropology Toolkit",
        "version": __version__,
        "repository": "https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit",
        "tool_families": {
            "data_collection": ["search_openalex", "search_pubmed"],
            "methodology": ["list_lenses", "get_lens"],
        },
        "notebooks": "Colab notebooks covering the same capabilities live in the repository's notebooks/ directory.",
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
