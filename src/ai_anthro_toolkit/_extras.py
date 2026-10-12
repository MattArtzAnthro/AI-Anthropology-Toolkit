"""Optional dependencies, imported where they are used, with a message that
says what to install when they are missing.

The MCP plugin installs the `[data]` extra. sentence-transformers (and the
torch it pulls in) stays in `[chunking]` because it is large, and anthropic
stays in `[api]` because delegated mode needs no client at all. A bare
ModuleNotFoundError from inside a tool tells the researcher nothing they can
act on; these errors name the extra.
"""

PLUGIN_NOTE = (
    "If you run the toolkit through the Claude Code or Codex plugin, the "
    "server is started by uvx from the plugin's .mcp.json; add the extra to "
    "its `--from` spec, for example ai-anthropology-toolkit[data,{extra}]."
)


class MissingExtra(ImportError):
    """An optional dependency is not installed; the message names the extra."""


def missing(module: str, extra: str, purpose: str) -> MissingExtra:
    return MissingExtra(
        f"{purpose} needs the `{module}` package, which is not installed. "
        f'Install it with: pip install "ai-anthropology-toolkit[{extra}]". '
        + PLUGIN_NOTE.format(extra=extra))


def sentence_transformer(purpose: str):
    """The SentenceTransformer class, or a MissingExtra naming `[chunking]`."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise missing("sentence-transformers", "chunking", purpose) from None
    return SentenceTransformer
