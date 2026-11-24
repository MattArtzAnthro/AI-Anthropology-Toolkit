---- MODULE Count ----
\* A delegated codebook job. This release sends packet 1, again and again when the batch fails
\* after its codes were merged (refinement raises: an embedding model that cannot be
\* downloaded; or the process dies). An earlier release, which shares the job store and knows
\* nothing of ledger.json, may submit a packet between those calls.
\* submit_batch's steps in this release, in its order: read what was merged and which packets
\* were merged; merge packet 1 unless it was merged before; write ledger.json; write
\* entries.json; refine; write done_ids.json. A failure returns the caller to the start, with
\* the same batch. The earlier release, in one step: merge its packet into entries.json, adding
\* to the code's frequency whether or not it was merged before, and add it to done_ids.json.
\* Earlier: "none"; "other" (it submits packet 2 once); "any" (it submits twice, each time a
\* packet not yet recorded as answered, as get_next_batch serves them, packet 1 among them).
\* Ledger: the merge and the packets merged into it are one file (ledger.json), written in one
\* step. Without it the packets merged are read from done_ids.json, written last.
\* StaleCheck: a ledger that lacks a packet done_ids.json records is out of date; the merge is
\* read from entries.json. Union: the packets merged are then those answered and those the
\* ledger counted, not those answered alone.
\* FailBetween: a failure may strike between the ledger.json and entries.json writes.
EXTENDS Naturals
CONSTANTS Ledger, StaleCheck, Union, Earlier, FailBetween, MaxFailures
P == {1, 2}
Zero == [p \in P |-> 0]
VARIABLES entries, ledgerOn, ledgerC, ledgerF, done, pc, seenF, seenC, failures, earlier
vars == <<entries, ledgerOn, ledgerC, ledgerF, done, pc, seenF, seenC, failures, earlier>>
files == <<entries, ledgerOn, ledgerC, ledgerF, done>>

Init == entries = Zero /\ ledgerOn = FALSE /\ ledgerC = {} /\ ledgerF = Zero /\ done = {}
        /\ pc = "start" /\ seenF = Zero /\ seenC = {} /\ failures = 0
        /\ earlier = 0

\* Whether a call reads the merge from ledger.json.
FromLedger == Ledger /\ ledgerOn /\ (~StaleCheck \/ done \subseteq ledgerC)
\* The codes a call starts from: what get_job_result and the next batch see.
Codes == IF FromLedger THEN ledgerF ELSE entries

Read == pc = "start" /\ pc' = "ledger"
        /\ seenF' = Codes
        /\ seenC' = (IF FromLedger THEN ledgerC
                     ELSE done \cup (IF Ledger /\ ledgerOn /\ Union THEN ledgerC ELSE {}))
        /\ UNCHANGED <<files, failures, earlier>>
Merged == IF 1 \in seenC THEN seenF ELSE [seenF EXCEPT ![1] = @ + 1]
WriteLedger == pc = "ledger" /\ pc' = "entries"
               /\ (IF Ledger THEN ledgerOn' = TRUE /\ ledgerF' = Merged /\ ledgerC' = seenC \cup {1}
                   ELSE UNCHANGED <<ledgerOn, ledgerF, ledgerC>>)
               /\ UNCHANGED <<entries, done, seenF, seenC, failures, earlier>>
WriteEntries == pc = "entries" /\ pc' = "refine" /\ entries' = Merged
                /\ UNCHANGED <<ledgerOn, ledgerC, ledgerF, done, seenF, seenC, failures, earlier>>
Refine == pc = "refine" /\ pc' = "done" /\ UNCHANGED <<files, seenF, seenC, failures, earlier>>
WriteDone == pc = "done" /\ pc' = "end" /\ done' = done \cup {1}
             /\ UNCHANGED <<entries, ledgerOn, ledgerC, ledgerF, seenF, seenC, failures, earlier>>
Fail == pc \in {"ledger", "entries", "refine", "done"} /\ (FailBetween \/ pc # "entries")
        /\ failures < MaxFailures /\ failures' = failures + 1
        /\ pc' = "start" /\ UNCHANGED <<files, seenF, seenC, earlier>>
\* The earlier release submits one packet between this release's calls.
EarlierSubmit == earlier < (CASE Earlier = "any" -> 2 [] Earlier = "other" -> 1 [] OTHER -> 0)
                 /\ pc \in {"start", "end"} /\ earlier' = earlier + 1
                 /\ \E p \in (IF Earlier = "any" THEN P \ done ELSE {2} \ done) :
                      entries' = [entries EXCEPT ![p] = @ + 1] /\ done' = done \cup {p}
                 /\ UNCHANGED <<ledgerOn, ledgerC, ledgerF, pc, seenF, seenC, failures>>

Next == Read \/ WriteLedger \/ WriteEntries \/ Refine \/ WriteDone \/ Fail \/ EarlierSubmit
Spec == Init /\ [][Next]_vars

\* Each packet's codes are counted once, however often it is sent.
CountedOnce == \A p \in P : Codes[p] <= 1
\* Every packet recorded as answered has its codes counted.
Kept == \A p \in done : Codes[p] >= 1
\* Probe: the job does finish.
NeverDone == pc # "end"
====
