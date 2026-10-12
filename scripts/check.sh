#!/usr/bin/env bash
# The repo quality gate: offline tests, the coverage floor, and lint. The global
# pre-commit hook runs this before every commit, so keep it offline and quick.
# Live tests stay opt-in and never run here. Bypass one commit with --no-verify.
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
cd "$(git rev-parse --show-toplevel)"
COV_DIR="${TMPDIR:-/tmp}/check-$(basename "$PWD")"
mkdir -p "$COV_DIR"
export COVERAGE_FILE="$COV_DIR/.coverage"

unset ANTHROPIC_API_KEY AAT_RUN_LIVE_CLAUDE AAT_RUN_INSTALL_CHECK AAT_RUN_PUBLISHED_INSTALL_CHECK
export AAT_SKIP_LIVE_SCRAPERS=1 PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
.venv/bin/ruff check . 2>/dev/null || ruff check .
.venv/bin/python -m unittest discover -s tests -t . 2>&1 | tail -3
.venv/bin/python -m coverage run -m unittest discover -s tests/package -t . >/dev/null 2>&1
.venv/bin/python -m coverage report --format=total >/dev/null
echo "coverage: $(.venv/bin/python -m coverage report --format=total)% (floor in pyproject.toml)"
