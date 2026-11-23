---- MODULE DeskList ----
\* Two rulings desks built at once on one ratification (build_ratification_desk), while
\* ratify_codebook ratifies the same codebook job again. Each reads ratification.json, adds or
\* keeps the desks list, and writes it back. get_decision_record reads the rulings of every desk
\* on that list; a desk missing from it is missing from the record.
\* Locked: each read-change-write holds the ratification's lock (JobStore.locked).
CONSTANTS Locked
Actors == {"desk1", "desk2", "ratify"}
VARIABLES desks, pc, seen, holder
vars == <<desks, pc, seen, holder>>

Init == desks = {} /\ pc = [a \in Actors |-> "start"] /\ seen = [a \in Actors |-> {}] /\ holder = "none"

Read(a) == pc[a] = "start" /\ (Locked => holder = "none")
           /\ holder' = (IF Locked THEN a ELSE holder)
           /\ seen' = [seen EXCEPT ![a] = desks] /\ pc' = [pc EXCEPT ![a] = "write"] /\ UNCHANGED desks
Write(a) == pc[a] = "write"
            /\ desks' = (IF a = "ratify" THEN seen[a] ELSE seen[a] \cup {a})
            /\ holder' = (IF Locked THEN "none" ELSE holder)
            /\ pc' = [pc EXCEPT ![a] = "end"] /\ UNCHANGED seen

Next == \E a \in Actors : Read(a) \/ Write(a)
Spec == Init /\ [][Next]_vars

DesksKept == \A a \in {"desk1", "desk2"} : pc[a] = "end" /\ (\A b \in Actors : pc[b] # "write") => a \in desks
NeverBuilt == desks = {}
====
