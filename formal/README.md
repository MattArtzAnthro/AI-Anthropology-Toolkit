# Formal models

Lean 4 proofs and TLA+ model checks of the MCP server's job store: what `submit_batch` accepts and
when it calls a job complete, what `ratify_codebook` will ratify, and what happens when two calls,
or two server processes, work on one job or desk at once.

## What is modeled

| Model | Code | What it proves or checks |
|---|---|---|
| `AatModel/Submit.lean` | `server.submit_batch`, `server._submit_held`, `server._codebook_ledger`, `server._issued` | A job reported complete has an answer for every packet it issued; only issued packets are recorded; no codebook packet is counted twice; a complete job and an api-mode job take no batches. On jobs an earlier release wrote: a queue that gave two chunks one packet ID takes no batches, IDs it never issued do not count as answered, a job marked complete with packets unanswered takes them, and a ledger that lacks an answered packet is read as out of date, the packets merged then being those answered (that their codes are read is `Count.tla`'s) |
| `AatModel/Packets.lean` | `server._packet_ids`, `start_coding_job` | Every chunk gets a packet and no two packets share an ID, even when chunks of several interviews share chunk IDs; IDs that are already different are kept; when they repeat, a packet ID names the chunk, by its source and ID (`ana.txt#3`), by its source, ID and text when another chunk shares both (two folders' `transcript.txt`), or with no source by its ID and text (`3~<digest>`); a chunk's name does not depend on the order of the chunks, one named like no other gets the same packet wherever it stands, and two coding passes in different orders match chunk to chunk |
| `AatModel/Ratify.lean` | `server.ratify_codebook`, `server.start_coding_job` | Only a finished codebook job is ratified by its ID; a ratification holds the checksum of the result it names; once a `ratification_id` holds a checksum it holds it for ever |
| `tla/Submit.tla` | `submit_batch` under `JobStore.locked` | Two batches at once on one job: every packet recorded as answered keeps its codes |
| `tla/Desk.tla` | `desk.gate.apply` under `JobStore.locked` | Two callers finishing one desk, in one process or two, with crashes and retries: the decision record names the ratification the desk finished as, every caller is told that one, and no ratification job is made that the desk does not name |
| `tla/Count.tla` | the codebook branch of `submit_batch` (`ledger.json`, its write order) | A batch that fails after its codes were merged (refinement raises, the process dies between writes) and is sent again is counted once; with an earlier release sharing the job store and submitting between this release's calls, every packet answered keeps its codes, and none is counted twice unless a process died between writing `entries.json` and `done_ids.json`, or the earlier release's own refinement raised between its two writes. Only a job an earlier release started is shared: no earlier release opens one this release starts (`one-release`) |
| `tla/DeskView.tla` | `desk_sync`, `desk_finish`, `record_desk_decisions` | A desk whose finish from the conversation was interrupted, and which is then opened in its view, can still be finished; so can one an earlier release left held by its view; and the view's own interrupted Ratify is completed only in the view, so the record names the surface the decisions were made on |
| `tla/DeskList.tla` | `build_ratification_desk`, `ratify_codebook`, `desk.gate._commit`, `desk.record.add_desk` | Rulings desks built at once on one ratification, while it is ratified again, an interrupted desk finish that minted it is sent again, or an earlier release builds a desk on it without a lock, all stay on its lists of desks |

Each Lean file keeps the rule as it was before the fix beside the rule as fixed. For every hole a
theorem shows the old rule let it through and another shows the fixed rule stops it.
`Submit.lean` keeps three earlier rules: `oldSubmit`, before any fix; `fix1Submit`, the first
fix, which a second review found mishandled jobs an earlier release wrote; and `fix2Submit`,
which took the packets a stale ledger counted as merged. Each TLA+
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
fewer than `done_ids.json`; 72 ratify cases; and the packet IDs for 31 lists of chunks). A ledger
case seeds the files as they stand in that state (the test's docstring says how), so a server
that read `entries.json` where it should read `ledger.json` disagrees with the vectors.
`tests/package/test_formal_conformance.py` runs the real `submit_batch` (on a coding job and a
codebook job), `ratify_codebook` and `_packet_ids` on each case and requires the same verdict;
a refused case must also leave every file of the job as it was. It fails on an empty file and
carries planted faults: a flipped verdict, a refusal that writes, each rule of `fix1Submit`,
`fix2Submit`'s stale ledger, and a server that never reads `ledger.json`. `lean.sh` fails when the committed `vectors.json` differs
from what the model prints. `tests/package/test_formal_findings.py` holds one test per defect the
models found, each naming its theorem or TLC row.

`stamp.json` holds the SHA-256 of every file here. The gate (`scripts/check.sh`) runs
`python3 formal/stamp.py --check` and fails when a model, a script or `vectors.json` changed
since the provers last passed. Only `check.sh` writes the stamp. `modeled.txt` lists the code the
models describe; a push that changes one of those files runs the provers.

## Expected FAIL rows

| Row | Why it fails |
|---|---|
| `Submit current NeverBothEnd`, `Desk current NeverFinished`, `DeskList current NeverBuilt`, `Count current NeverDone`, `DeskView current NeverFinished` | Probes: the states are reachable |
| `Submit unlocked *`, `DeskList unlocked DesksKept` | The rule before `JobStore.locked`: a parallel call loses the other's write |
| `DeskList resend-rewrites DesksKept` | The rule before: a desk finish sent again wrote its plan's empty list of desks |
| `DeskList one-file-earlier DesksKept` | The rule before: desks built here were listed in `ratification.json`, which an earlier release rewrites without a lock |
| `DeskList separate-unlocked DesksKept` | A probe: `desks.json` alone is not enough; two desks built here at once still need the lock |
| `DeskList current EarlierKept` | Limit: a desk an earlier release adds, without a lock, while this release completes that release's interrupted desk finish |
| `Count no-ledger CountedOnce` | The rule before `ledger.json`: the packets merged were read from `done_ids.json`, written last, so each resend after a failure merged again |
| `Count ledger-only Kept` | The first fix: a ledger an earlier release left out of date was read as the merge, and the packet that release merged lost its codes |
| `Count stale-to-done CountedOnce` | `done_ids.json` written after refinement: a stale ledger's own packet, merged by a batch whose refinement then failed, is merged again |
| `Count union Kept`, `Count union-first Kept` | The second fix (`fix2Submit`), with or without the new write order: the process dies between writing `ledger.json` and `entries.json`, an earlier release submits, and the packet the ledger counted is taken as merged with its codes in no file |
| `Count union-resent CountedOnce` | The second fix: an earlier release is served a packet whose refinement failed here after merging, and counts it again |
| `Count earlier-fails CountedOnce` | Limit: the earlier release writes `entries.json`, refines, then writes `done_ids.json`; when its refinement raises, its packet is merged and unrecorded, and is served and merged again, as with that release alone. Codes are never lost (`earlier-fails Kept` passes). Only on a job an earlier release started |
| `Count dies-w2 CountedOnce` | Limit: the process dies between writing `entries.json` and `done_ids.json`, and an earlier release submits before this release runs again. Those two files are the earlier release's own record, and it has the same window between its two writes. Only on a job an earlier release started |
| `DeskView old NotStuck` | The rule before: the view took a desk whose finish from the conversation was pending, and then neither surface could finish it |
| `DeskView view-waits-only NotStuck` (legacy) | The view no longer takes such a desk, but a desk an earlier release left that way needs the conversation to be able to complete its own finish |
| `DeskView any-pending ViewKeeps` | A rule letting the conversation complete any pending finish: it completed the view's own interrupted Ratify, and the record named the conversation |
| `Desk two-processes *`, `Desk two-same-digest` | The rule before: `_desk_lock` held within one process only |
| `Desk mint-first NoOrphan` (crash) | The rule before: the ratification job was made before `finishing.json` named it, and a crash between left one nothing names |

## Known limits

- A job this release starts has an ID of twelve hex digits and lives in `<root>/locked/`, where
  no earlier release opens it: 3.10 and 3.11 refuse the ID before touching a file, and earlier
  releases look only at `<root>/<id>` (`TestEarlierReleasesFenced`). So it is `Count`'s
  `one-release` case. A job an earlier release started (eight hex digits, at `<root>/<id>`) can
  still be opened by both, and that release takes no lock and does not know `ledger.json`: two
  calls on it at the same moment, one from each release, can lose a batch; a packet that release
  merged and failed to record (its refinement raised, or its process died between its two
  writes) is counted twice when sent again; and it counts again a packet its own caller resends.
  Finish such a job on one release, or upgrade every host that shares a job store.
- A ratification an earlier release made is read here, and coding jobs and rulings desks can be
  built on it. This release lists the desks it builds in `desks.json`, which no earlier release
  opens, so an earlier release rewriting `ratification.json` cannot drop one. A codebook job an
  earlier release started is ratified in a new job (its `ratification.json` names the codebook
  job), not in its own folder. Two things remain between releases: an earlier release's decision
  record reads only `ratification.json`, so it lacks the desks built here; and a desk finish an
  earlier release started and this one completes rewrites that ratification's
  `ratification.json`, so a desk that release adds at that moment, without a lock, can be dropped
  (`DeskList current EarlierKept`).
- A release before 3.10 opens `<root>/<string>` for any string it is given. Handed a path
  (`locked/<id>`, or an absolute one) instead of a job ID, it opens a job this release started,
  without a lock. Every tool returns and takes bare IDs; only a path pasted by hand reaches it.
- A job store on an NFS or CIFS share whose file locks stay on one host is refused on Linux,
  which lists each mount's options (`nolock` or `local_lock=flock|all` on NFS, `nobrl` on CIFS),
  unless `AAT_JOBS_ONE_HOST=1` says no other host uses it. Other shares that can keep locks on
  one host (Lustre `localflock`, FUSE mounts such as sshfs, 9p, virtiofs, older CIFS clients
  without flock support) are not recognised, and macOS and Windows do not report mount options;
  there, `flock` on such a share holds on each host alone. On a local disk, and on NFS or SMB
  with locking, the lock holds across hosts.
- A call waits for a job's lock at most `jobs.LOCK_TIMEOUT` (two minutes) and is then refused,
  with nothing recorded; a codebook's last batch can hold its job that long while an embedding
  model downloads.
- Each Lean model takes one call as one step. Failures part-way through a call are covered by
  the TLA+ models (`Count.tla`, `Desk.tla`), not by the proofs.

## What is taken as given

The job store's files hold what was last written (`_write_atomic`), `flock` (or `msvcrt`'s lock
on Windows) excludes other processes, and `codebook_checksum` tells codebooks apart. The models do not look at what a
response says, how codes are parsed or refined, or the network and scraper tools.
