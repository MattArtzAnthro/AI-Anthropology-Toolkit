# Formal models

Lean 4 proofs and TLA+ model checks of the MCP server's job store: what `submit_batch` accepts and
when it calls a job complete, what `ratify_codebook` will ratify, and what happens when two calls,
or two server processes, work on one job or desk at once.

## What is modeled

| Model | Code | What it proves or checks |
|---|---|---|
| `AatModel/Submit.lean` | `server.submit_batch`, `server._submit_held`, `server._codebook_ledger`, `server._issued` | A job reported complete has an answer for every packet it issued; only issued packets are recorded; no codebook packet is counted twice; a complete job and an api-mode job take no batches. On jobs an earlier release wrote: a queue that gave two chunks one packet ID takes no batches, IDs it never issued do not count as answered, a job marked complete with packets unanswered takes them, and the packets taken as merged include those it merged without entering them in `ledger.json` (by construction; that their codes are read is `Count.tla`'s) |
| `AatModel/Packets.lean` | `server._packet_ids`, `start_coding_job` | Every chunk gets a packet and no two packets share an ID, even when chunks of several interviews share chunk IDs; IDs that are already different are kept; when they repeat and every chunk names its source file, a packet ID is the chunk's source and ID (`ana.txt#3`), so two coding passes in different orders match chunk to chunk |
| `AatModel/Ratify.lean` | `server.ratify_codebook`, `server.start_coding_job` | Only a finished codebook job is ratified by its ID; a ratification holds the checksum of the result it names; once a `ratification_id` holds a checksum it holds it for ever |
| `tla/Submit.tla` | `submit_batch` under `JobStore.locked` | Two batches at once on one job: every packet recorded as answered keeps its codes |
| `tla/Desk.tla` | `desk.gate.apply` under `JobStore.locked` | Two callers finishing one desk, in one process or two, with crashes and retries: the decision record names the ratification the desk finished as, and every caller is told that one |
| `tla/Count.tla` | the codebook branch of `submit_batch` (`ledger.json`) | A batch that fails after its codes were merged (refinement raises, the process dies) and is sent again is counted once; a packet an earlier release, sharing the job store, merges between this release's calls keeps its codes, also when it is sent packets this release has merged |
| `tla/DeskView.tla` | `desk_sync`, `desk_finish`, `record_desk_decisions` | A desk whose finish from the conversation was interrupted, and which is then opened in its view, can still be finished; so can one an earlier release left held by its view; and the view's own interrupted Ratify is completed only in the view, so the record names the surface the decisions were made on |
| `tla/DeskList.tla` | `build_ratification_desk`, `ratify_codebook`, `desk.gate._commit` | Rulings desks built at once on one ratification, while it is ratified again or an interrupted desk finish that minted it is sent again, all stay on its list of desks |

Each Lean file keeps the rule as it was before the fix beside the rule as fixed. For every hole a
theorem shows the old rule let it through and another shows the fixed rule stops it.
`Submit.lean` keeps two earlier rules: `oldSubmit`, before any fix, and `fix1Submit`, the first
fix, which a second review found mishandled jobs an earlier release wrote. Each TLA+
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

`lake exe vectors` prints `vectors.json`, the fixed rules' verdict on every small case (2,360
submit cases, among them jobs an earlier release wrote and ledgers that count a packet more or
fewer than `done_ids.json`; 72 ratify cases; and the packet IDs for 23 lists of chunks). A ledger
case seeds the files as they stand in that state (the test's docstring says how), so a server
that read `entries.json` where it should read `ledger.json` disagrees with the vectors.
`tests/package/test_formal_conformance.py` runs the real `submit_batch` (on a coding job and a
codebook job), `ratify_codebook` and `_packet_ids` on each case and requires the same verdict;
a refused case must also leave every file of the job as it was. It fails on an empty file and
carries planted faults: a flipped verdict, a refusal that writes, each rule of `fix1Submit`, a
stale ledger read as counting only `done_ids.json`, and a server that never reads `ledger.json`. `lean.sh` fails when the committed `vectors.json` differs
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
| `DeskList resend-rewrites DesksKept` | The rule before: a desk finish sent again wrote its plan's empty list of desks |
| `Count no-ledger CountedOnce` | The rule before `ledger.json`: the packets merged were read from `done_ids.json`, written last, so each resend after a failure merged again |
| `Count ledger-only Kept` | The first fix: a ledger an earlier release left out of date was read as the merge, and the packet that release merged lost its codes |
| `Count stale-to-done CountedOnce` | A stale ledger read as counting only `done_ids.json`: its own packet, merged by a batch whose refinement then failed, is merged again |
| `Count between Kept` | Limit: the process dies between writing `ledger.json` and `entries.json`, and an earlier release then submits to the job: the packet is counted but its codes are not in `entries.json` |
| `Count earlier-resent CountedOnce` (failures) | Limit: an earlier release adds to a code's frequency for every packet it is sent, merged before or not, as it always did; sent a packet whose batch failed here after merging, it counts it twice. Upgrade every host |
| `DeskView old NotStuck` | The rule before: the view took a desk whose finish from the conversation was pending, and then neither surface could finish it |
| `DeskView view-waits-only NotStuck` (legacy) | The view no longer takes such a desk, but a desk an earlier release left that way needs the conversation to be able to complete its own finish |
| `DeskView any-pending ViewKeeps` | A rule letting the conversation complete any pending finish: it completed the view's own interrupted Ratify, and the record named the conversation |
| `Desk two-processes *`, `Desk two-same-digest` | The rule before: `_desk_lock` held within one process only |
| `Desk current NoOrphan` | Limit: a crash between minting a ratification and writing `finishing.json` leaves a ratification job nothing names. It holds no ratification record, so coding refuses it |

## Known limits

- `flock` waits without a timeout: a call holding a codebook job's lock through a slow
  refinement (an embedding model being downloaded) holds back every `submit_batch` on that job.
- `flock` on a network file system (SMB, NFS) may not exclude other hosts; the job store is
  assumed to be on a local disk.
- A job shared with an earlier release (a host still running it) is covered only where the
  earlier release runs between this release's calls; it takes no lock, so two calls at once,
  one from each release, can still lose a batch, and an earlier release still counts a packet it
  is sent again (`Count earlier-resent`). Upgrade every host that shares a job store.
- A packet ID names its chunk's source file only when every chunk has one; chunks of several
  interviews passed without `source_file` get positional IDs (`3:1`), and two coding passes over
  them in different orders pair different chunks. `compare_lenses` and the rulings desk warn or
  refuse on differing text; the lens network does not.
- Each Lean model takes one call as one step. Failures part-way through a call are covered by
  the TLA+ models (`Count.tla`, `Desk.tla`), not by the proofs.

## What is taken as given

The job store's files hold what was last written (`_write_atomic`), `flock` excludes other
processes on the same host (on Windows, where there is no `fcntl`, the lock holds within one
process only), and `codebook_checksum` tells codebooks apart. The models do not look at what a
response says, how codes are parsed or refined, or the network and scraper tools.
