#!/usr/bin/env bash
# Builds the Lean model, checks every theorem rests only on Lean's three standard axioms, and
# regenerates vectors.json, failing if it differs from the committed copy (--update rewrites it
# after a reviewed model change). Needs Lean 4.36.0 (LEAN_LAKE, or a release unpacked into
# ~/.local/lean). .lake/ is deleted on exit.
set -euo pipefail
cd "$(dirname "$0")"
trap 'rm -rf .lake' EXIT

lake_bin=${LEAN_LAKE:-}
if [[ -z "$lake_bin" ]]; then
  for d in "$HOME"/.local/lean/*/bin; do [[ -x "$d/lake" ]] && lake_bin="$d/lake"; done
fi
if [[ -z "$lake_bin" || ! -x "$lake_bin" ]]; then
  echo "lean: FAILED: no Lean toolchain (set LEAN_LAKE, or unpack a release into ~/.local/lean)" >&2
  exit 1
fi
PATH="$(dirname "$lake_bin"):$PATH"
export PATH
echo "== lean: $(lean --version)"

if grep -rnE '\bsorry\b|native_decide|^\s*axiom\b' AatModel AatModel.lean Main.lean; then
  echo "lean: FAILED: sorry, native_decide or a new axiom in the sources" >&2
  exit 1
fi
if ! build=$("$lake_bin" build 2>&1); then
  echo "$build" | grep -E 'error' | head -20 >&2
  echo "lean: FAILED: lake build" >&2
  exit 1
fi

theorems=$(for f in AatModel/*.lean; do m=$(basename "$f" .lean); grep -h '^theorem' "$f" | awk -v m="$m" '{print m "." $2}'; done | sort)
listed=$(grep -oE '#print axioms AatModel\.[A-Za-z0-9_.]+' axioms.lean | sed 's/#print axioms AatModel\.//' | sort)
if [[ "$theorems" != "$listed" ]]; then
  echo "lean: FAILED: axioms.lean does not list exactly the theorems in AatModel/" >&2
  exit 1
fi
axioms=$("$lake_bin" env lean axioms.lean 2>&1)
bad=$(echo "$axioms" | grep -oE "depends on axioms: \[[^]]*\]" | sed 's/.*\[//; s/\]//' | tr ',' '\n' \
  | sed 's/ //g' | grep -vE '^(propext|Classical.choice|Quot.sound)$' || true)
count=$(echo "$theorems" | wc -l | tr -d ' ')
if [[ -n "$bad" ]] || [[ $(echo "$axioms" | grep -c "axioms\|does not depend") -ne $count ]]; then
  echo "$axioms" >&2
  echo "lean: FAILED: unexpected axioms or an unchecked theorem: ${bad:-}" >&2
  exit 1
fi
echo "   $count theorems, standard axioms only"

"$lake_bin" build vectors >/dev/null
fresh=$(mktemp)
"$lake_bin" exe vectors > "$fresh"
if [[ "${1:-}" == "--update" ]]; then
  mv "$fresh" vectors.json
  echo "   vectors.json rewritten"
elif ! cmp -s "$fresh" vectors.json; then
  rm -f "$fresh"
  echo "lean: FAILED: vectors.json differs from what the model prints; review, then --update" >&2
  exit 1
else
  rm -f "$fresh"
  echo "   vectors.json matches the model ($(grep -c '"refused"' vectors.json) cases)"
fi
echo "lean: ok"
