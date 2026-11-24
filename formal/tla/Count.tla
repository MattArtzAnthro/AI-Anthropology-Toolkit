---- MODULE Count ----
\* A delegated codebook job. This release sends packet 1, again and again when the call fails:
\* refinement raises (an embedding model that cannot be downloaded), or the process dies between
\* two of its writes. An earlier release, which shares the job store and knows nothing of
\* ledger.json, may submit a packet between this release's calls.
\* submit_batch's steps in this release: read what was merged and which packets were merged;
\* merge packet 1 unless it was merged before; write ledger.json; write entries.json; then, with
\* DoneFirst, write done_ids.json and refine, or without it refine and then write done_ids.json.
\* A failure returns the caller to the start, with the same batch. The earlier release, in one
\* step: merge its packet into entries.json, adding to the code's frequency whether or not it was
\* merged before, and add it to done_ids.json; so entries.json holds the packets done_ids.json
\* records, unless a process died between the two writes. EarlierFails: the earlier release refines
\* between those writes, and its refinement may raise, leaving its packet merged and unrecorded.
\* Earlier: "none"; "other" (it submits packet 2 once); "any" (it submits twice, each time a
\* packet not yet recorded as answered, as get_next_batch serves them, packet 1 among them).
\* Ledger: the merge and the packets merged into it are one file (ledger.json), written in one
\* step. Without it the packets merged are read from done_ids.json.
\* StaleCheck: a ledger that lacks a packet done_ids.json records is out of date, and the merge is
\* read from entries.json, with the packets done_ids.json records as merged. Union: the packets
\* the ledger counted are taken as merged too.
\* Refinement may raise at any call. CrashW1: the process may die between the ledger.json and
\* entries.json writes; CrashW2: between the entries.json and done_ids.json writes.
EXTENDS Naturals
CONSTANTS Ledger, StaleCheck, Union, DoneFirst, Earlier, EarlierFails, CrashW1, CrashW2, MaxFailures
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
WriteEntries == pc = "entries" /\ pc' = (IF DoneFirst THEN "done" ELSE "refine")
                /\ entries' = Merged
                /\ UNCHANGED <<ledgerOn, ledgerC, ledgerF, done, seenF, seenC, failures, earlier>>
WriteDone == pc = "done" /\ pc' = (IF DoneFirst THEN "refine" ELSE "end") /\ done' = done \cup {1}
             /\ UNCHANGED <<entries, ledgerOn, ledgerC, ledgerF, seenF, seenC, failures, earlier>>
Refine == pc = "refine" /\ pc' = (IF DoneFirst THEN "end" ELSE "done")
          /\ UNCHANGED <<files, seenF, seenC, failures, earlier>>
\* Where a call can stop part-way: before its first write, when refinement raises, or where a
\* dying process leaves it. Without DoneFirst, a refinement that raises leaves the call between
\* entries.json and done_ids.json.
CanFail == \/ pc \in {"ledger", "refine"}
           \/ pc = "entries" /\ CrashW1
           \/ pc = "done" /\ (CrashW2 \/ ~DoneFirst)
Fail == CanFail /\ failures < MaxFailures /\ failures' = failures + 1
        /\ pc' = "start" /\ UNCHANGED <<files, seenF, seenC, earlier>>
\* The earlier release submits one packet between this release's calls.
EarlierSubmit == earlier < (CASE Earlier = "any" -> 2 [] Earlier = "other" -> 1 [] OTHER -> 0)
                 /\ pc \in {"start", "end"} /\ earlier' = earlier + 1
                 /\ \E p \in (IF Earlier = "any" THEN P \ done ELSE {2} \ done) :
                      /\ entries' = [entries EXCEPT ![p] = @ + 1]
                      /\ (done' = done \cup {p} \/ (EarlierFails /\ done' = done))
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
