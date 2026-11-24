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
dk() { run Desk "$1" "Shared = $2 SameDigest = $3 NameFirst = $4 MaxCrashes = $5" "$6" "$7"; }
#  name             shared same   first crashes property             expect
dk current          TRUE   FALSE  TRUE  2       RecordNamesFinished  PASS
dk current          TRUE   FALSE  TRUE  2       ToldWhatHolds        PASS
dk current          TRUE   TRUE   TRUE  2       RecordNamesFinished  PASS
dk current          TRUE   TRUE   TRUE  2       ToldWhatHolds        PASS
dk current          TRUE   FALSE  TRUE  0       NeverFinished        FAIL  # probe: a desk finishes
dk current          TRUE   FALSE  TRUE  2       NoOrphan             PASS  # a crash before finishing.json names it creates no ratification job
dk mint-first       TRUE   FALSE  FALSE 1       NoOrphan             FAIL  # the rule before: a crash after minting left an unused ratification job
dk mint-first       TRUE   FALSE  FALSE 0       NoOrphan             PASS  # without a crash, the rule before minted one per desk too
dk two-processes    FALSE  FALSE  TRUE  0       RecordNamesFinished  FAIL  # old: _desk_lock is per process; the record names another ratification
dk two-processes    FALSE  FALSE  TRUE  0       ToldWhatHolds        FAIL  # old: a caller is told a ratification the desk does not hold
dk two-same-digest  FALSE  TRUE   TRUE  0       RecordNamesFinished  FAIL  # old: even the same decisions mint two ratifications

# ---- DeskList: rulings desks built on one ratification, and re-ratifying it
dl() { run DeskList "$1" "Locked = $2 ResendKeeps = $3" "$4" "$5"; }
#  name               locked keeps  property    expect
dl current            TRUE   TRUE   DesksKept   PASS
dl current            TRUE   TRUE   NeverBuilt  FAIL  # probe: desks are built
dl unlocked           FALSE  TRUE   DesksKept   FAIL  # a desk dropped from the ratification's list, and its rulings from the record
dl resend-rewrites    TRUE   FALSE  DesksKept   FAIL  # an interrupted desk finish sent again emptied the list

# ---- Count: a codebook batch sent again after it failed past the merge, and an earlier release
# sharing the job (DoneFirst: done_ids.json is written before refinement; W1/W2: may die between writes)
ct() { run Count "$1" "Ledger = $2 StaleCheck = $3 Union = $4 DoneFirst = $5 Earlier = \"$6\" EarlierFails = ${12:-FALSE} CrashW1 = $7 CrashW2 = $8 MaxFailures = $9" "${10}" "${11}"; }
#  name             ledger stale union first earlier w1    w2    fails property     expect
ct current          TRUE   TRUE  FALSE TRUE  any     TRUE  FALSE 3     CountedOnce  PASS
ct current          TRUE   TRUE  FALSE TRUE  any     TRUE  FALSE 3     Kept         PASS
ct current          TRUE   TRUE  FALSE TRUE  any     TRUE  FALSE 3     NeverDone    FAIL  # probe: the job finishes after failures
ct one-release      TRUE   TRUE  FALSE TRUE  none    TRUE  TRUE  3     CountedOnce  PASS
ct one-release      TRUE   TRUE  FALSE TRUE  none    TRUE  TRUE  3     Kept         PASS
ct dies-w2          TRUE   TRUE  FALSE TRUE  any     TRUE  TRUE  3     Kept         PASS
ct dies-w2          TRUE   TRUE  FALSE TRUE  any     TRUE  TRUE  3     CountedOnce  FAIL  # residual: dies after entries.json, before done_ids.json, and an earlier release submits next (its own files' window); only a job an earlier release started
ct earlier-fails    TRUE   TRUE  FALSE TRUE  any     TRUE  FALSE 3     Kept         PASS  TRUE
ct earlier-fails    TRUE   TRUE  FALSE TRUE  any     TRUE  FALSE 3     CountedOnce  FAIL  TRUE  # residual: the earlier release's own refinement raised after it merged; its packet, unrecorded, is served and merged again (as with that release alone); only a job an earlier release started
ct no-ledger        FALSE  FALSE FALSE FALSE none    FALSE FALSE 3     CountedOnce  FAIL  # merged again on each resend: a code's frequency climbs
ct no-ledger        FALSE  FALSE FALSE FALSE none    FALSE FALSE 0     CountedOnce  PASS  # without a failure the old order counts once
ct ledger-only      TRUE   FALSE FALSE FALSE other   FALSE FALSE 0     Kept         FAIL  # the earlier release's packet: answered, its codes lost
ct stale-to-done    TRUE   TRUE  FALSE FALSE other   FALSE FALSE 3     CountedOnce  FAIL  # done_ids.json after refinement: a stale ledger's own packet merged again after a failed refinement
ct union            TRUE   TRUE  TRUE  FALSE other   TRUE  FALSE 3     Kept         FAIL  # the second fix: dies between ledger.json and entries.json, then an earlier release submits
ct union-resent     TRUE   TRUE  TRUE  FALSE any     FALSE FALSE 3     CountedOnce  FAIL  # the second fix: an earlier release is served a packet whose refinement failed here
ct union-first      TRUE   TRUE  TRUE  TRUE  other   TRUE  FALSE 3     Kept         FAIL  # writing done_ids.json first is not enough: the ledger's count still hides the lost packet

# ---- DeskView: a desk finished from the conversation or its view, with crashes
dv() { run DeskView "$1" "ViewWaits = $2 Resume = \"$3\" Legacy = $4 MaxCrashes = $5" "$6" "$7"; }
#  name               waits resume legacy crashes property       expect
dv current            TRUE  own    TRUE   2       NotStuck       PASS
dv current            TRUE  own    TRUE   2       ViewKeeps      PASS
dv current            TRUE  own    FALSE  2       NeverFinished  FAIL  # probe: the desk finishes
dv old                FALSE never  FALSE  2       NotStuck       FAIL  # interrupted in chat, then opened in the view: nobody can finish it
dv view-waits-only    TRUE  never  FALSE  2       NotStuck       PASS  # new desks no longer get stuck...
dv view-waits-only    TRUE  never  TRUE   2       NotStuck       FAIL  # ...but one an earlier release left stays stuck
dv any-pending        TRUE  any    TRUE   2       ViewKeeps      FAIL  # the conversation completes the view's own interrupted Ratify, recorded as chat

if [[ $bad -ne 0 ]]; then echo "tla: FAILED: a row differs from its expected result" >&2; exit 1; fi
echo "tla: ok"
