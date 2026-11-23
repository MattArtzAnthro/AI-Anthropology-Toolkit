#!/usr/bin/env bash
# TLC over the TLA+ models in this folder: every property in every configuration, against the
# expected result. An expected FAIL is a rule the server no longer follows (the row turns its
# guard off, to show the guard is needed), a probe that a state is reachable, or a residual the
# code cannot close. If an expected FAIL starts passing, the model has lost the behaviour, and
# this check fails. "current" rows are the server as it ships.
#
# Needs Java 11 or later and tla2tools.jar (TLA_JAR; default ~/.local/share/tla/tla2tools.jar,
# from https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar).
# TRACES=1 prints the counterexample for each FAIL.
set -euo pipefail
cd "$(dirname "$0")"
JAR=${TLA_JAR:-$HOME/.local/share/tla/tla2tools.jar}
[[ -f "$JAR" ]] || { echo "tla: FAILED: no tla2tools.jar at $JAR" >&2; exit 1; }
command -v java >/dev/null || { echo "tla: FAILED: no java on PATH" >&2; exit 1; }
work=$(mktemp -d "${TMPDIR:-/tmp}/tla-XXXXXX")
trap 'rm -rf "$work"' EXIT
cp ./*.tla "$work/"
bad=0

# run MODULE NAME "CONSTANTS ..." PROPERTY EXPECT
run() {
  local module=$1 name=$2 consts=$3 prop=$4 expect=$5 out got
  printf 'CONSTANTS %s\nSPECIFICATION Spec\nINVARIANT %s\n' "$consts" "$prop" > "$work/m.cfg"
  out=$(cd "$work" && java -XX:+UseParallelGC -Djava.io.tmpdir="$work" -cp "$JAR" tlc2.TLC -config m.cfg \
        -workers auto -deadlock -cleanup -metadir "$work/states" "$module.tla" 2>&1 || true)
  if grep -q "No error has been found" <<< "$out"; then got=PASS
  elif grep -q "is violated" <<< "$out"; then got=FAIL
  else echo "$out" >&2; echo "tla: FAILED: TLC did not finish: $module $name $prop" >&2; exit 1; fi
  local states mark
  states=$(grep -oE "[0-9,]+ distinct states found" <<< "$out" | tail -1 || true)
  if [[ "$got" == "$expect" ]]; then mark=ok; else mark=UNEXPECTED; bad=1; fi
  printf '%-7s %-16s %-20s %-4s (expected %-4s) %-10s %s\n' "$module" "$name" "$prop" "$got" "$expect" "$mark" "$states"
  if [[ "${TRACES:-}" == 1 && "$got" == FAIL ]]; then
    sed -n '/is violated/,/states generated/p' <<< "$out" | grep -E '^State [0-9]+|^/\\ ' | sed 's/^/      /'
  fi
}

# ---- Submit: two submit_batch calls at once on one job
sb() { run Submit "$1" "Locked = $2" "$3" "$4"; }
#  name      locked property      expect
sb current   TRUE   TypeOK        PASS
sb current   TRUE   DoneHasCodes  PASS
sb current   TRUE   BothKept      PASS
sb current   TRUE   NeverBothEnd  FAIL  # probe: both calls finish
sb unlocked  FALSE  DoneHasCodes  FAIL  # a packet marked answered with its codes lost (reported No_Codes)
sb unlocked  FALSE  BothKept      FAIL  # one batch dropped from done_ids or partial

# ---- Desk: finishing one desk from two callers, with crashes
dk() { run Desk "$1" "Shared = $2 SameDigest = $3 MaxCrashes = $4" "$5" "$6"; }
#  name             shared same   crashes property             expect
dk current          TRUE   FALSE  2       RecordNamesFinished  PASS
dk current          TRUE   FALSE  2       ToldWhatHolds        PASS
dk current          TRUE   TRUE   2       RecordNamesFinished  PASS
dk current          TRUE   TRUE   2       ToldWhatHolds        PASS
dk current          TRUE   FALSE  0       NeverFinished        FAIL  # probe: a desk finishes
dk current          TRUE   FALSE  1       NoOrphan             FAIL  # residual: a crash after minting leaves an unused ratification job
dk current          TRUE   FALSE  0       NoOrphan             PASS  # without a crash, one ratification per desk
dk two-processes    FALSE  FALSE  0       RecordNamesFinished  FAIL  # old: _desk_lock is per process; the record names another ratification
dk two-processes    FALSE  FALSE  0       ToldWhatHolds        FAIL  # old: a caller is told a ratification the desk does not hold
dk two-same-digest  FALSE  TRUE   0       RecordNamesFinished  FAIL  # old: even the same decisions mint two ratifications

# ---- DeskList: rulings desks built on one ratification, and re-ratifying it
dl() { run DeskList "$1" "Locked = $2" "$3" "$4"; }
#  name      locked property   expect
dl current   TRUE   DesksKept  PASS
dl current   TRUE   NeverBuilt FAIL  # probe: desks are built
dl unlocked  FALSE  DesksKept  FAIL  # a desk dropped from the ratification's list, and its rulings from the record

if [[ $bad -ne 0 ]]; then echo "tla: FAILED: a row differs from its expected result" >&2; exit 1; fi
echo "tla: ok"
