# Formal models

Lean 4 proofs and TLA+ model checks of the MCP server's job store: what `submit_batch` accepts and
when it calls a job complete, what `ratify_codebook` will ratify, and what happens when two calls,
or two server processes, work on one job or desk at once.

## What is modeled

| Model | Code | What it proves or checks |
|---|---|---|
| `AatModel/Submit.lean` | `server.submit_batch`, `server._submit_held` | A job reported complete has an answer for every packet it issued; only issued packets are recorded; no codebook packet is counted twice; a complete job and an api-mode job take no batches |
| `AatModel/Ratify.lean` | `server.ratify_codebook`, `server.start_coding_job` | Only a finished codebook job is ratified by its ID; a ratification holds the checksum of the result it names; once a `ratification_id` holds a checksum it holds it for ever |
| `tla/Submit.tla` | `submit_batch` under `JobStore.locked` | Two batches at once on one job: every packet recorded as answered keeps its codes |
| `tla/Desk.tla` | `desk.gate.apply` under `JobStore.locked` | Two callers finishing one desk, in one process or two, with crashes and retries: the decision record names the ratification the desk finished as, and every caller is told that one |
| `tla/DeskList.tla` | `build_ratification_desk`, `ratify_codebook` | Rulings desks built at once on one ratification all stay on its list of desks |

Each Lean file keeps the rule as it was before the fix beside the rule as fixed. For every hole a
theorem shows the old rule let it through and another shows the fixed rule stops it. Each TLA+
model turns its guard into a constant, so the table checks the old rule and the new one.

## Running

```bash
bash formal/check.sh            # Lean, vectors, TLC, then the stamp
bash formal/check.sh --update   # after a reviewed model change: rewrite vectors.json first
TRACES=1 bash formal/tla/check.sh   # print each counterexample
```

Needs Lean 4.36.0 (`LEAN_LAKE`, or a release unpacked under `~/.local/lean/`), Java 11 or later,
and `tla2tools.jar` 1.7.4 (`TLA_JAR`, default `~/.local/share/tla/tla2tools.jar`). Core Lean only,
no Mathlib. `lean.sh` refuses `sorry`, `native_decide` and new axioms, and checks that every
theorem rests on `propext`, `Classical.choice` and `Quot.sound` alone. `.lake/` is build output;
the scripts delete it.

## How the code is held to the models

`lake exe vectors` prints `vectors.json`, the fixed rules' verdict on every small case (512).
`tests/package/test_formal_conformance.py` runs the real `submit_batch` (on a coding job and a
codebook job) and `ratify_codebook` on each case and requires the same verdict. It fails on an
empty file and carries a planted fault. `lean.sh` fails when the committed `vectors.json` differs
from what the model prints. `tests/package/test_formal_findings.py` holds one test per defect the
models found, each naming its theorem or TLC row.

`stamp.json` holds the SHA-256 of every file here. The gate (`scripts/check.sh`) runs
`python3 formal/stamp.py --check` and fails when a model, a script or `vectors.json` changed
since the provers last passed. Only `check.sh` writes the stamp. `modeled.txt` lists the code the
models describe; a push that changes one of those files runs the provers.

## Expected FAIL rows

| Row | Why it fails |
|---|---|
| `Submit current NeverBothEnd`, `Desk current NeverFinished`, `DeskList current NeverBuilt` | Probes: the states are reachable |
| `Submit unlocked *`, `DeskList unlocked DesksKept` | The rule before `JobStore.locked`: a parallel call loses the other's write |
| `Desk two-processes *`, `Desk two-same-digest` | The rule before: `_desk_lock` held within one process only |
| `Desk current NoOrphan` | Limit: a crash between minting a ratification and writing `finishing.json` leaves a ratification job nothing names. It holds no ratification record, so coding refuses it |

## What is taken as given

The job store's files hold what was last written (`_write_atomic`), `flock` excludes other
processes on the same host (on Windows, where there is no `fcntl`, the lock holds within one
process only), and `codebook_checksum` tells codebooks apart. The models do not look at what a
response says, how codes are parsed or refined, or the network and scraper tools.
