---- MODULE Count ----
\* A delegated codebook job's last packet, sent again and again because the batch fails after
\* its codes were merged: refinement raises (an embedding model that cannot be downloaded), or
\* the process dies. submit_batch's steps, in its order: read what was merged and which packets
\* were merged; merge the packet unless it was merged before; write the merge; refine; write
\* done_ids.json. A failure returns the caller to the start, with the same batch.
\* Ledger: the merge and the packets merged into it are one file (ledger.json), written in one
\* step. Without it the packets merged are read from done_ids.json, written last.
EXTENDS Naturals
CONSTANTS Ledger, MaxFailures
VARIABLES freq, counted, done, pc, seenFreq, seenCounted, failures
vars == <<freq, counted, done, pc, seenFreq, seenCounted, failures>>

Init == freq = 0 /\ counted = FALSE /\ done = FALSE /\ pc = "start"
        /\ seenFreq = 0 /\ seenCounted = FALSE /\ failures = 0

Read == pc = "start" /\ pc' = "write" /\ seenFreq' = freq
        /\ seenCounted' = (IF Ledger THEN counted ELSE done)
        /\ UNCHANGED <<freq, counted, done, failures>>
Write == pc = "write" /\ pc' = "refine"
         /\ freq' = (IF seenCounted THEN seenFreq ELSE seenFreq + 1)
         /\ counted' = (IF Ledger THEN TRUE ELSE counted)
         /\ UNCHANGED <<done, seenFreq, seenCounted, failures>>
Refine == pc = "refine" /\ pc' = "done" /\ UNCHANGED <<freq, counted, done, seenFreq, seenCounted, failures>>
WriteDone == pc = "done" /\ pc' = "end" /\ done' = TRUE
             /\ UNCHANGED <<freq, counted, seenFreq, seenCounted, failures>>
Fail == pc \in {"write", "refine", "done"} /\ failures < MaxFailures /\ failures' = failures + 1
        /\ pc' = "start" /\ UNCHANGED <<freq, counted, done, seenFreq, seenCounted>>

Next == Read \/ Write \/ Refine \/ WriteDone \/ Fail
Spec == Init /\ [][Next]_vars

\* The packet's codes are counted once, however often it is sent.
CountedOnce == freq <= 1
\* Probe: the job does finish.
NeverDone == pc # "end"
====
