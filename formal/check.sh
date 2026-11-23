#!/usr/bin/env bash
# Runs every prover, then writes the proof stamp the gate checks (scripts/check.sh, `formal`
# stage). The only writer of stamp.json: it records the files before the provers run and refuses
# to stamp if any changed while they ran. A missing prover is a failure, never a pass.
#   bash formal/check.sh            Lean, vectors, TLC, stamp
#   bash formal/check.sh --update   first rewrite vectors.json after a reviewed model change
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${1:-}" == "--update" ]]; then
  bash formal/lean.sh --update
fi
snap=$(mktemp)
trap 'rm -f "$snap"' EXIT
python3 formal/stamp.py --snapshot "$snap"
bash formal/lean.sh
bash formal/tla/check.sh
python3 formal/stamp.py --write --snapshot "$snap"
echo "formal: ok"
