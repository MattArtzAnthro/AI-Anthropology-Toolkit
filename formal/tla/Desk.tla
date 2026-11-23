---- MODULE Desk ----
\* Finishing a ratification desk (desk/gate.apply, through record_desk_decisions or desk_finish)
\* while another caller, in this server or in a second server process sharing the job store,
\* finishes the same desk; either may crash mid-way and be sent again.
\* apply's steps, in its order: read finished.json and finishing.json and decide; mint a
\* ratification job; write finishing.json; write the ratification's files; read the record and,
\* if it has no ratify entry, append one naming this caller's ratification; write finished.json;
\* return the outcome.
\* Shared: the lock spans both callers. The thread lock (_desk_lock) spans callers in one process
\* only; the job lock (JobStore.locked, flock on the desk) spans processes. A crash ends a process
\* and releases its lock.
EXTENDS Naturals, Sequences, FiniteSets
CONSTANTS Shared, SameDigest, MaxCrashes
Callers == {1, 2}
Digest == [c \in Callers |-> IF SameDigest \/ c = 1 THEN "d1" ELSE "d2"]
None == [d |-> "none", r |-> 0]

VARIABLES finishing, finished, record, minted, pc, mine, holder, crashes, returned
vars == <<finishing, finished, record, minted, pc, mine, holder, crashes, returned>>

Init == finishing = None /\ finished = None /\ record = <<>> /\ minted = 0
        /\ pc = [c \in Callers |-> "start"] /\ mine = [c \in Callers |-> 0]
        /\ holder = 0 /\ crashes = 0 /\ returned = [c \in Callers |-> 0]

Go(c, to) == pc' = [pc EXCEPT ![c] = to]

Start(c) == pc[c] = "start" /\ (Shared => holder = 0)
            /\ holder' = (IF Shared THEN c ELSE holder)
            /\ (IF finished # None
               THEN /\ returned' = [returned EXCEPT ![c] = IF finished.d = Digest[c] THEN finished.r ELSE 99]
                    /\ Go(c, "end") /\ UNCHANGED mine
               ELSE IF finishing # None /\ finishing.d # Digest[c]
               THEN /\ returned' = [returned EXCEPT ![c] = 99] /\ Go(c, "end") /\ UNCHANGED mine
               ELSE IF finishing # None
               THEN /\ mine' = [mine EXCEPT ![c] = finishing.r] /\ Go(c, "files") /\ UNCHANGED returned
               ELSE /\ Go(c, "mint") /\ UNCHANGED <<mine, returned>>)
            /\ UNCHANGED <<finishing, finished, record, minted, crashes>>
Mint(c) == pc[c] = "mint" /\ minted' = minted + 1 /\ mine' = [mine EXCEPT ![c] = minted + 1]
           /\ Go(c, "finishing") /\ UNCHANGED <<finishing, finished, record, holder, crashes, returned>>
Finishing(c) == pc[c] = "finishing" /\ finishing' = [d |-> Digest[c], r |-> mine[c]]
                /\ Go(c, "files") /\ UNCHANGED <<finished, record, minted, mine, holder, crashes, returned>>
Files(c) == pc[c] = "files" /\ Go(c, "record")
            /\ UNCHANGED <<finishing, finished, record, minted, mine, holder, crashes, returned>>
Record(c) == pc[c] = "record"
             /\ record' = (IF Len(record) = 0 THEN Append(record, mine[c]) ELSE record)
             /\ Go(c, "finished") /\ UNCHANGED <<finishing, finished, minted, mine, holder, crashes, returned>>
Finished(c) == pc[c] = "finished" /\ finished' = [d |-> Digest[c], r |-> mine[c]]
               /\ Go(c, "return") /\ UNCHANGED <<finishing, record, minted, mine, holder, crashes, returned>>
Return(c) == pc[c] = "return" /\ returned' = [returned EXCEPT ![c] = mine[c]] /\ Go(c, "end")
             /\ holder' = (IF Shared THEN 0 ELSE holder)
             /\ UNCHANGED <<finishing, finished, record, minted, mine, crashes>>
Release(c) == pc[c] = "end" /\ holder = c /\ holder' = 0
              /\ UNCHANGED <<finishing, finished, record, minted, pc, mine, crashes, returned>>
\* The process dies mid-apply; the same decisions are sent again.
Crash(c) == pc[c] \notin {"start", "end"} /\ crashes < MaxCrashes /\ crashes' = crashes + 1
            /\ Go(c, "start") /\ mine' = [mine EXCEPT ![c] = 0]
            /\ holder' = (IF holder = c THEN 0 ELSE holder)
            /\ UNCHANGED <<finishing, finished, record, minted, returned>>

Next == \E c \in Callers : Start(c) \/ Mint(c) \/ Finishing(c) \/ Files(c) \/ Record(c)
                           \/ Finished(c) \/ Return(c) \/ Release(c) \/ Crash(c)
Spec == Init /\ [][Next]_vars

\* The decision record's ratify entry names the ratification the desk finished as.
RecordNamesFinished == finished # None /\ Len(record) > 0 => record[1] = finished.r
\* A caller told "ratified as r" was told what the desk holds.
ToldWhatHolds == \A c \in Callers : returned[c] \in 1..98 => finished # None /\ finished.r = returned[c]
\* Residual: a crash between minting and finishing.json leaves an orphan ratification job.
NoOrphan == minted <= 1
\* Probe: the desk does finish.
NeverFinished == finished = None
====
