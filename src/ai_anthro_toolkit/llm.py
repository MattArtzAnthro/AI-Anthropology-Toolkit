"""LLM access for the analysis pipeline.

Two execution modes:

- **api**: calls the Anthropic API directly with retry/backoff — notebook
  parity, suited to unattended runs.
- **delegated**: no API calls are made; pipeline stages that need a model
  raise :class:`WorkPacket` carrying the rendered prompt, so an orchestrating
  model (e.g. Claude driving the MCP server) can perform the completion and
  submit the result back. This keeps interpretive work visible to, and
  contestable by, the researcher.
"""

import time

DEFAULT_MODEL = "claude-sonnet-5"


class WorkPacket(Exception):
    """Raised in delegated mode: the caller's model should complete `prompt`."""

    def __init__(self, prompt: str, *, purpose: str, system: str | None = None):
        super().__init__(f"delegated work: {purpose}")
        self.prompt = prompt
        self.system = system
        self.purpose = purpose


class ClaudeLLM:
    """Thin Anthropic wrapper with exponential-backoff retries (api mode)."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, max_retries: int = 3):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_retries = max_retries

    def __call__(self, prompt: str, *, system: str | None = None,
                 temperature: float = 0.3, max_tokens: int = 4096) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        last = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(**kwargs)
                return response.content[0].text
            except Exception as exc:  # transient API failures
                last = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        raise last


class DelegatedLLM:
    """Delegated mode: every completion request surfaces as a WorkPacket."""

    def __call__(self, prompt: str, *, system: str | None = None,
                 temperature: float = 0.3, max_tokens: int = 4096) -> str:
        raise WorkPacket(prompt, purpose="completion", system=system)


def make_llm(mode: str = "api", api_key: str | None = None,
             model: str = DEFAULT_MODEL):
    """Build an LLM callable for the requested mode.

    Returns a callable `llm(prompt, *, system, temperature, max_tokens) -> str`.
    """
    if mode == "delegated":
        return DelegatedLLM()
    if not api_key:
        raise ValueError("api mode requires an Anthropic API key; "
                         "use mode='delegated' to have the driving model do the work")
    return ClaudeLLM(api_key=api_key, model=model)
