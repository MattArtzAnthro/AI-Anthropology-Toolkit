"""Cut a release in the one order that works.

    python3 -m scripts.release           # full release
    python3 -m scripts.release --dry-run # everything except the upload

Four consecutive releases shipped version pins ahead of the upload that would
satisfy them — including the commit that added RELEASING.md, which documents
the ordering. A document does not enforce an order, and a checklist you have
to remember is a gate that becomes a form. This script exists so the order
cannot be got wrong rather than merely written down.

The constraint it enforces: `.mcp.json`, `AGENTS.md`, and `GEMINI.md` carry
the package version and ship in the same commit as the code, so a push before
the upload publishes a pin to a version that does not exist, and every fresh
install fails until it lands.

Two things this deliberately does not do. It does not push, because that is
the author's, and it does not re-upload on a negative resolve: both PyPI read
paths are CDN-cached and lag by different amounts, so a negative result means
not yet visible rather than upload failed — and a PyPI version number cannot
be reclaimed once used.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Every file carrying the package version. A release breaks when one is
# missed, so the list is enumerated and tested rather than remembered.
PIN_SITES = (
    "pyproject.toml",
    "src/ai_anthro_toolkit/__init__.py",
    ".mcp.json",
    "AGENTS.md",
    "GEMINI.md",
)

# How long to keep checking for the upload to become visible before asking
# for a human. Observed lag has run to several minutes, and the extras
# -qualified spec has resolved minutes after the bare one.
RESOLVE_BUDGET = 900

VISIBLE = "visible"
NOT_YET_VISIBLE = "not-yet-visible"
UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class Step:
    name: str
    why: str


STEPS = (
    Step("preflight",
         "A release with a failing suite, a missing CHANGELOG entry, or "
         "disagreeing pins is broken before it is built."),
    Step("build",
         "Builds the wheel and sdist from the working tree, which is what "
         "will be uploaded."),
    Step("verify",
         "Installs the built wheel into a clean venv and imports the server. "
         "The test suite cannot catch a dependency-resolution break, because "
         "it runs against whatever is already installed."),
    Step("twine-check",
         "Validates the metadata. A PyPI version number cannot be reclaimed, "
         "so metadata errors are caught here or not at all."),
    Step("upload",
         "Publishes to PyPI. Everything above must pass first, because this "
         "step is irreversible."),
    Step("await-resolve",
         "Polls the extras-qualified spec until it resolves. A bare ==X "
         "resolves before [data]==X does, so the simplified form gives a "
         "false all-clear on the thing still broken."),
    Step("safe-to-push",
         "The only point at which pushing does not break installs."),
)


# ── Pure helpers, tested without a network call ─────────────────────────────

def read_version(repo: Path = REPO) -> str:
    text = (repo / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    if not match:
        raise RuntimeError("no version in pyproject.toml")
    return match.group(1)


def disagreeing_pins(repo: Path, version: str) -> list:
    """Which pin sites do not carry this version."""
    return [name for name in PIN_SITES
            if version not in (repo / name).read_text(encoding="utf-8")]


def changelog_has_entry(repo: Path, version: str) -> bool:
    text = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    return bool(re.search(rf"^###\s+{re.escape(version)}\b", text, re.M))


def resolve_spec(version: str) -> str:
    """The exact spec the plugin's .mcp.json invokes, extras and all."""
    return f"ai-anthropology-toolkit[data]=={version}"


def classify_resolve(succeeded: bool, elapsed: float, budget: float) -> str:
    """A negative resolve is not a failed upload. It is not yet visible."""
    if succeeded:
        return VISIBLE
    return NOT_YET_VISIBLE if elapsed <= budget else UNRESOLVED


# Tests that reach a network service or the `claude` CLI. They fail
# intermittently under a long suite run and pass in isolation, so a single
# failure here is not evidence of a broken release. A gate that cries wolf
# gets routed around, which is the gate that becomes a form; these report,
# and only block when the failure repeats.
LIVE_TESTS = (
    "TestApiModeLiveViaCli",
    "TestDataSourcesLive",
    "TestScrapersLive",
)


def is_live(failure_line: str) -> bool:
    return any(name in failure_line for name in LIVE_TESTS)


def blocks(is_live_test: bool, repeated: bool) -> bool:
    """A live failure blocks only if it survives a re-run."""
    return repeated if is_live_test else True


def _failed_ids(output: str) -> list:
    return re.findall(r"^(?:FAIL|ERROR):\s+(.+)$", output, re.M)


# ── The steps ───────────────────────────────────────────────────────────────

def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _suite_env() -> dict:
    """The environment the suite is actually run in.

    `tests/package/` imports the package, which is on `src/` rather than
    installed, so a bare `unittest discover` fails on import and looks like
    fifteen broken tests. That is a preflight defect, not a release blocker,
    and confusing the two is how a real failure gets waved through.
    """
    import os

    env = dict(os.environ)
    src = str(REPO / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src}{os.pathsep}{existing}" if existing else src
    return env


def preflight(version: str) -> None:
    bad = disagreeing_pins(REPO, version)
    if bad:
        raise SystemExit(
            f"pins disagree with pyproject ({version}): {', '.join(bad)}")
    if not changelog_has_entry(REPO, version):
        raise SystemExit(f"CHANGELOG.md has no entry for {version}")
    result = _run([sys.executable, "-m", "unittest", "discover",
                   "-s", "tests", "-t", "."], cwd=REPO, env=_suite_env())
    if result.returncode == 0:
        return

    failed = _failed_ids(result.stderr)
    hard = [f for f in failed if not is_live(f)]
    if hard or not failed:
        raise SystemExit("test suite is not green:\n" + result.stderr[-2000:])

    # Only live tests failed. Re-run them in isolation before blocking.
    still = []
    for line in failed:
        target = re.search(r"\(([\w.]+)", line)
        if not target:
            still.append(line)
            continue
        rerun = _run([sys.executable, "-m", "unittest", target.group(1)],
                     cwd=REPO, env=_suite_env())
        if rerun.returncode != 0:
            still.append(line)
        else:
            print(f"  live test flaky, passed on re-run: {line[:70]}")
    if still:
        raise SystemExit(
            "live tests failed twice, which is a real failure:\n"
            + "\n".join(still))


def build(dist: Path) -> None:
    shutil.rmtree(dist, ignore_errors=True)
    result = _run([sys.executable, "-m", "build", "--outdir", str(dist)],
                  cwd=REPO)
    if result.returncode != 0:
        raise SystemExit("build failed:\n" + result.stderr[-2000:])


def verify(dist: Path, version: str, venv: Path) -> None:
    shutil.rmtree(venv, ignore_errors=True)
    _run([sys.executable, "-m", "venv", str(venv)])
    wheel = next(dist.glob("*.whl"))
    if _run([str(venv / "bin" / "pip"), "install", "-q", str(wheel)]).returncode:
        raise SystemExit("clean-venv install failed")
    probe = _run([str(venv / "bin" / "python"), "-c",
                  "import ai_anthro_toolkit as t;"
                  "from ai_anthro_toolkit.mcp.server import main;"
                  "print(t.__version__)"])
    if probe.returncode or probe.stdout.strip() != version:
        raise SystemExit(f"clean-venv probe failed: {probe.stderr[-500:]}")
    missing = [s for s in ("ai-anthro-mcp", "ai-anthro-doctor", "ai-anthro-check")
               if not (venv / "bin" / s).exists()]
    if missing:
        raise SystemExit(f"console scripts missing: {', '.join(missing)}")


def _require_twine() -> None:
    if _run([sys.executable, "-m", "twine", "--version"]).returncode != 0:
        raise SystemExit(
            f"twine is not installed for {sys.executable}.\n"
            f"Install it with: {sys.executable} -m pip install twine")


def twine_check(dist: Path) -> None:
    _require_twine()
    result = _run([sys.executable, "-m", "twine", "check",
                   *map(str, dist.glob("*"))])
    if result.returncode or "FAILED" in result.stdout:
        # Report both streams. A release tool that says a step failed and
        # shows nothing is worse than one that does not check at all.
        raise SystemExit("twine check failed:\n"
                         + (result.stdout[-800:] or "")
                         + (result.stderr[-800:] or ""))


def upload(dist: Path) -> None:
    _require_twine()
    result = _run([sys.executable, "-m", "twine", "upload", "--non-interactive",
                   *map(str, dist.glob("*"))])
    if result.returncode != 0:
        raise SystemExit("upload failed:\n"
                         + (result.stderr[-800:] or "")
                         + (result.stdout[-800:] or ""))


def await_resolve(version: str, budget: float = RESOLVE_BUDGET) -> str:
    """Poll until the extras-qualified spec resolves, or ask for a human.

    Never re-uploads. A negative resolve means the index has not caught up,
    and a PyPI version number cannot be reclaimed if the first upload did in
    fact land.
    """
    spec = resolve_spec(version)
    started = time.monotonic()
    while True:
        ok = _run(["uvx", "--refresh", "--from", spec,
                   "python", "-c", "import ai_anthro_toolkit"]).returncode == 0
        elapsed = time.monotonic() - started
        state = classify_resolve(ok, elapsed, budget)
        if state is VISIBLE or state == VISIBLE:
            return VISIBLE
        if state == UNRESOLVED:
            return UNRESOLVED
        print(f"  not yet visible after {int(elapsed)}s; waiting")
        time.sleep(30)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="release")
    parser.add_argument("--dry-run", action="store_true",
                        help="everything except the upload")
    args = parser.parse_args(argv)

    version = read_version()
    dist, venv = REPO / "dist", REPO / ".release-venv"
    print(f"releasing ai-anthropology-toolkit {version}\n")

    for step in STEPS:
        print(f"[{step.name}]")
        if step.name == "preflight":
            preflight(version)
        elif step.name == "build":
            build(dist)
        elif step.name == "verify":
            verify(dist, version, venv)
        elif step.name == "twine-check":
            twine_check(dist)
        elif step.name == "upload":
            if args.dry_run:
                print("  skipped (--dry-run)")
                print("\nDry run complete. Nothing was published.")
                return 0
            upload(dist)
        elif step.name == "await-resolve":
            if await_resolve(version) == UNRESOLVED:
                print(f"\n{resolve_spec(version)} has still not resolved.")
                print("The upload was accepted; the index has not caught up.")
                print("Do NOT re-upload — the version cannot be reclaimed.")
                print("Re-check with: uvx --refresh --from "
                      f'"{resolve_spec(version)}" python -c "import ai_anthro_toolkit"')
                return 1

    print(f"\nSafe to push. Then:")
    print("  claude plugin marketplace update ai-anthropology")
    print("  claude plugin update ai-anthropology@ai-anthropology")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
