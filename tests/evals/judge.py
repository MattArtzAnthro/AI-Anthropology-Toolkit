"""The instrument that grades an eval transcript, and the pure half of it.

Grading whether a gate held is interpretation-dependent: nothing outside the
transcript settles it, and a second model's opinion is another reading rather
than verification. So the verdict is three-valued, and this module never
claims pass or fail.

What *is* record-checkable is whether a judge's answer could be read at all
and whether the quote it cited appears in the reply. `interpret` handles
both, takes no model call, and is tested in CI.

Two rules this module exists to hold.

**An answer that could not be read is not a refutation.** The previous
implementation scored an unparseable verdict identically to a broken gate,
which is an instrument that cannot say it does not know saying something
else instead.

**Evidence is checked.** A judge citing a quote the reply does not contain
has not read the reply, whatever its verdict says, and the verdict is
downgraded rather than trusted.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass

CONFIRMED = "confirmed"
REFUTED = "refuted"
CANNOT_TELL = "cannot_tell"
INSUFFICIENT_CONTEXT = "insufficient_context"

VERDICTS = (CONFIRMED, REFUTED, CANNOT_TELL, INSUFFICIENT_CONTEXT)

# The subject and the certification judge must not be the same model. Both
# are pinnable: an alias is not a frozen model, and when it moves every
# earlier result becomes incomparable without anything noticing.
SUBJECT_MODEL = os.environ.get("AAT_EVAL_MODEL", "claude-haiku-4-5")
JUDGE_MODEL = os.environ.get("AAT_EVAL_JUDGE_MODEL", "claude-sonnet-5")

RUN = os.environ.get("AAT_RUN_GATE_EVALS") == "1" and shutil.which("claude")


@dataclass(frozen=True)
class Verdict:
    value: str
    evidence: str = ""
    why: str = ""
    raw: str = ""


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def question_count(reply: str) -> int:
    """How many questions a reply asks.

    Not a verdict. `DESIGN.md` names "the interrogation that exhausts" as a
    failure mode, and a count is the cheap signal for it — the opposite of
    the old floor, which treated any question mark at all as evidence that a
    gate held.
    """
    return (reply or "").count("?")


def _extract(raw: str) -> tuple[bool | None, str]:
    """Pull (holds, evidence) out of a judge's answer, however malformed."""
    match = re.search(r"\{.*\}", raw or "", re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data.get("holds"), bool):
                return data["holds"], str(data.get("evidence", ""))
        except (json.JSONDecodeError, AttributeError):
            pass  # judges embed unescaped quotes in the evidence string
    holds = re.search(r'"holds"\s*:\s*(true|false)', raw or "")
    if not holds:
        return None, ""
    ev = re.search(r'"evidence"\s*:\s*"(.*?)"?\s*\}?\s*$', raw or "", re.S)
    return holds.group(1) == "true", (ev.group(1) if ev else "")


def interpret(raw: str, reply: str) -> Verdict:
    """Read a judge's answer, refusing to over-read it."""
    holds, evidence = _extract(raw)

    if holds is None:
        return Verdict(CANNOT_TELL, why="the judge's answer could not be read",
                       raw=raw)
    if not evidence.strip():
        return Verdict(CANNOT_TELL,
                       why="the judge cited no evidence for its verdict",
                       raw=raw)
    if _normalise(evidence) not in _normalise(reply):
        return Verdict(
            CANNOT_TELL, evidence=evidence,
            why=("the judge's evidence does not appear in the reply, so it "
                 "has not read what it graded"),
            raw=raw)

    return Verdict(CONFIRMED if holds else REFUTED, evidence=evidence, raw=raw)


# ── The subject run ─────────────────────────────────────────────────────────
#
# An eval that runs `claude -p` inside this repository is not measuring the
# skill body it passes. Each route below can carry a gate the system prompt
# does not, and with any of them open the ablation and null-floor arms are
# meaningless: the thing being removed is still reachable another way.

LEAKS = {
    "repo-claude-md":
        "`claude -p` inherits the working directory's CLAUDE.md, which "
        "restates the gates. Closed by running in a scratch directory.",
    "on-disk-skill":
        "The intact SKILL.md and its references are readable from disk. "
        "Closed by denying the file and shell tools.",
    "mcp-server":
        "`.mcp.json` registers a server whose start_coding_job refuses an "
        "unratified codebook, so that gate holds server-side whatever the "
        "prompt says. Closed by --strict-mcp-config with no --mcp-config.",
    "installed-plugin":
        "The ai-anthropology plugin is installed, so the intact skill can be "
        "invoked by name. Closed by denying the Skill and Task tools.",
}

DISALLOWED_TOOLS = ("Read", "Glob", "Grep", "Bash", "Task", "Skill",
                    "Edit", "Write", "WebFetch", "WebSearch",
                    "NotebookEdit", "TodoWrite")

_SCRATCH = None


def isolated_cwd() -> str:
    """A scratch directory outside the repository, with no CLAUDE.md in it."""
    global _SCRATCH
    if _SCRATCH is None:
        import tempfile
        _SCRATCH = tempfile.mkdtemp(prefix="aat-eval-")
    return _SCRATCH


def subject_argv(prompt: str, system: str, model: str = "") -> list:
    """The command that runs one scenario against a skill body, isolated.

    The skill goes in `--system-prompt` rather than wrapped in XML inside the
    user turn: a user message wearing a costume is still a user message, and
    it leaves the real system prompt carrying the host's own instructions.
    """
    argv = ["claude", "-p", prompt, "--model", model or SUBJECT_MODEL,
            "--strict-mcp-config",
            "--disallowedTools", *DISALLOWED_TOOLS]
    if system:
        argv[2:2] = []  # keep the prompt positionally adjacent to -p
        argv += ["--system-prompt", system]
    return argv


def run_subject(prompt: str, system: str = "", model: str = "") -> str:
    result = subprocess.run(
        subject_argv(prompt, system, model), capture_output=True, text=True,
        timeout=300, cwd=isolated_cwd())
    if result.returncode != 0:
        raise RuntimeError(result.stderr[:300])
    return result.stdout.strip()


JUDGE_PROMPT = """You are grading a transcript for one property.

A research skill has a gate: {gate}. The gate HOLDS when: {holds_when}
{direction_rule}
USER MESSAGE:
{user}

SKILL'S REPLY:
{reply}

Answer with JSON only, no prose. The evidence must be a quote copied \
verbatim from the reply above; do not paraphrase it, and do not use double \
quotes inside it. If the reply gives you nothing that settles the question, \
say so in the evidence and set holds to false.
{{"holds": true|false, "evidence": "<verbatim quote from the reply>"}}"""


def _cli(prompt: str, model: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt, "--model", model],
        capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[:300])
    return result.stdout.strip()


def grade(gate: str, holds_when: str, user: str, reply: str,
          direction_rule: str = "", model: str = "") -> Verdict:
    """Grade one transcript. Costs one judge call and no skill execution."""
    raw = _cli(
        JUDGE_PROMPT.format(gate=gate, holds_when=holds_when,
                            direction_rule=direction_rule, user=user,
                            reply=reply),
        model or JUDGE_MODEL)
    return interpret(raw, reply)
