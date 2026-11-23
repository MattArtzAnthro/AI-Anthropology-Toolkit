---- MODULE DeskList ----
\* Two rulings desks built at once on one ratification (build_ratification_desk), while
\* ratify_codebook ratifies the same codebook job again. Each reads ratification.json, adds or
\* keeps the desks list, and writes it back. get_decision_record reads the rulings of every desk
\* on that list; a desk missing from it is missing from the record.
\* A third writer is the desk gate sending an interrupted finish again ("resend"): it rewrites
\* the ratification it minted, which was usable, and could carry desks, since it was minted.
\* Locked: each read-change-write holds the ratification's lock (JobStore.locked).
\* ResendKeeps: the resend reads the list under the lock and keeps it; before, it wrote the
\* list its plan held (none) without reading.
CONSTANTS Locked, ResendKeeps
Actors == {"desk1", "desk2", "ratify", "resend"}
VARIABLES desks, pc, seen, holder
vars == <<desks, pc, seen, holder>>

Init == desks = {} /\ pc = [a \in Actors |-> "start"] /\ seen = [a \in Actors |-> {}] /\ holder = "none"

Blind(a) == a = "resend" /\ ~ResendKeeps
Read(a) == pc[a] = "start" /\ (Locked /\ ~Blind(a) => holder = "none")
           /\ holder' = (IF Locked /\ ~Blind(a) THEN a ELSE holder)
           /\ seen' = [seen EXCEPT ![a] = desks] /\ pc' = [pc EXCEPT ![a] = "write"] /\ UNCHANGED desks
Write(a) == pc[a] = "write"
            /\ desks' = (IF Blind(a) THEN {} ELSE IF a \in {"ratify", "resend"} THEN seen[a] ELSE seen[a] \cup {a})
            /\ holder' = (IF Locked /\ ~Blind(a) THEN "none" ELSE holder)
            /\ pc' = [pc EXCEPT ![a] = "end"] /\ UNCHANGED seen

Next == \E a \in Actors : Read(a) \/ Write(a)
Spec == Init /\ [][Next]_vars

DesksKept == \A a \in {"desk1", "desk2"} : pc[a] = "end" /\ (\A b \in Actors : pc[b] # "write") => a \in desks
NeverBuilt == desks = {}
====
