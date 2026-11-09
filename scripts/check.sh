#!/usr/bin/env bash
# The repo quality gate: lint, offline tests, a minimum test count, and the
# coverage floor. The global pre-commit hook runs this before every commit, so
# keep it offline and quick. Live tests stay opt-in and never run here.
# Bypass one commit with --no-verify.
#
# Every tool runs from the project's .venv, whose versions pyproject.toml
# bounds, so the gate cannot pass on a stray copy from PATH. Set it up once:
#   uv venv && uv pip install -e ".[data,test]"
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Fewer tests than this means discovery broke or tests were deleted. Raise it
# when the suite grows; lowering it is a decision to explain in the commit.
MIN_TESTS=741

PY=.venv/bin/python
if ! "$PY" -c "import ruff, coverage, bandit, mypy" 2>/dev/null; then
    echo "check.sh: .venv lacks a gate tool (ruff, coverage, bandit, mypy). Run: uv pip install -e \".[data,test]\"" >&2
    exit 2
fi

COV_DIR="${TMPDIR:-/tmp}/check-$(basename "$PWD")"
mkdir -p "$COV_DIR"
export COVERAGE_FILE="$COV_DIR/.coverage"
unset ANTHROPIC_API_KEY AAT_RUN_LIVE_CLAUDE AAT_RUN_INSTALL_CHECK AAT_RUN_PUBLISHED_INSTALL_CHECK
export AAT_SKIP_LIVE_SCRAPERS=1 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1

"$PY" -m ruff check .
"$PY" -m mypy
"$PY" -m bandit -q -c pyproject.toml -r src

LOG="$COV_DIR/unittest.log"
if ! "$PY" -m unittest discover -s tests -t . >"$LOG" 2>&1; then
    tail -40 "$LOG"
    exit 1
fi
tail -3 "$LOG"
RAN=$(sed -n 's/^Ran \([0-9]*\) test.*/\1/p' "$LOG")
if [ "${RAN:-0}" -lt "$MIN_TESTS" ]; then
    echo "check.sh: ran ${RAN:-0} tests, fewer than MIN_TESTS=$MIN_TESTS." >&2
    exit 1
fi

"$PY" -m coverage run -m unittest discover -s tests/package -t . >/dev/null 2>&1
if ! TOTAL=$("$PY" -m coverage report --format=total); then
    echo "check.sh: coverage ${TOTAL}% is under the floor in pyproject.toml." >&2
    "$PY" -m coverage report | tail -25 >&2
    exit 1
fi
echo "coverage: ${TOTAL}% (floor in pyproject.toml)"
