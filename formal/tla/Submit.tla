---- MODULE Submit ----
\* Two submit_batch calls at once on one delegated coding job. mcp 2.x runs each sync tool in a
\* worker thread, and a model often sends batches in parallel. Each call makes the file steps
\* server.submit_batch makes, in its order: read done_ids.json, read partial.json, write
\* partial.json, write done_ids.json. A file holds what was last written (writes are atomic).
\* Locked: each call holds the job's lock (JobStore.locked) for all of its steps.
EXTENDS FiniteSets
CONSTANTS Locked
Callers == {1, 2}
Batch == [c \in Callers |-> IF c = 1 THEN {"a"} ELSE {"b"}]
Queue == {"a", "b"}

VARIABLES partial, done, pc, seenDone, seenPartial, holder
vars == <<partial, done, pc, seenDone, seenPartial, holder>>

TypeOK == partial \subseteq Queue /\ done \subseteq Queue /\ holder \in Callers \cup {0}

Init == partial = {} /\ done = {} /\ pc = [c \in Callers |-> "start"]
        /\ seenDone = [c \in Callers |-> {}] /\ seenPartial = [c \in Callers |-> {}] /\ holder = 0

Go(c, from, to) == pc[c] = from /\ pc' = [pc EXCEPT ![c] = to]

Acquire(c) == Go(c, "start", "readDone") /\ (Locked => holder = 0)
              /\ holder' = (IF Locked THEN c ELSE holder)
              /\ UNCHANGED <<partial, done, seenDone, seenPartial>>
ReadDone(c) == Go(c, "readDone", "readPartial") /\ seenDone' = [seenDone EXCEPT ![c] = done]
               /\ UNCHANGED <<partial, done, seenPartial, holder>>
ReadPartial(c) == Go(c, "readPartial", "writePartial") /\ seenPartial' = [seenPartial EXCEPT ![c] = partial]
                  /\ UNCHANGED <<partial, done, seenDone, holder>>
WritePartial(c) == Go(c, "writePartial", "writeDone") /\ partial' = seenPartial[c] \cup Batch[c]
                   /\ UNCHANGED <<done, seenDone, seenPartial, holder>>
WriteDone(c) == Go(c, "writeDone", "end") /\ done' = seenDone[c] \cup Batch[c]
                /\ holder' = (IF Locked THEN 0 ELSE holder)
                /\ UNCHANGED <<partial, seenDone, seenPartial>>

Next == \E c \in Callers : Acquire(c) \/ ReadDone(c) \/ ReadPartial(c) \/ WritePartial(c) \/ WriteDone(c)
Spec == Init /\ [][Next]_vars

\* A packet recorded as answered keeps its codes. A packet answered but lost from done_ids is
\* served again by get_next_batch; a packet in done_ids with its codes lost is reported No_Codes.
DoneHasCodes == done \subseteq partial
\* Once both calls return, both batches are kept.
BothKept == (\A c \in Callers : pc[c] = "end") => done = Queue /\ partial = Queue
\* Probe: both calls do finish.
NeverBothEnd == ~(\A c \in Callers : pc[c] = "end")
====
