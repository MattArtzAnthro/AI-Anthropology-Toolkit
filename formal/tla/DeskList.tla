---- MODULE DeskList ----
\* Two rulings desks built at once on one ratification (build_ratification_desk), while
\* ratify_codebook ratifies the same codebook job again. Each reads its list of desks, adds or
\* keeps it, and writes it back. get_decision_record reads the rulings of every desk listed; a
\* desk missing from the lists is missing from the record.
\* A third writer is the desk gate sending an interrupted finish again ("resend"): it rewrites
\* the ratification it minted, which was usable, and could carry desks, since it was minted.
\* A fourth is an earlier release building a desk on a ratification it made ("earlier"): it
\* reads ratification.json, adds its desk, and writes it back, without a lock.
\* Locked: each read-change-write here holds the ratification's lock (JobStore.locked).
\* ResendKeeps: the resend reads the list under the lock and keeps it; before, it wrote the
\* list its plan held (none) without reading.
\* Separate: the desks built here are listed in desks.json, which ratify, resend and the
\* earlier release do not write; without it, in ratification.json with everything else. With
\* it, ratify writes ratification.json with no list (it ratifies only this release's jobs, whose
\* desks are all in desks.json); resend keeps the list an earlier release may have written.
\* KeepWritten: the resend leaves a ratification.json already written as it is. A desk can be
\* built on a ratification only once that file is written (it is the last written), so the
\* resend's list is one only when it would be kept: with KeepWritten the resend writes no list.
\* Earlier: the earlier release builds its desk. A ratification it can open is one it made, which
\* ratify_codebook here never rewrites (it ratifies such a codebook job in a new job), so with
\* Separate, ratify does not act on it; the resend does, completing that release's own finish.
CONSTANTS Locked, ResendKeeps, Separate, Earlier, KeepWritten
Actors == {"desk1", "desk2", "ratify", "resend", "earlier"}
Here == {"desk1", "desk2"}
VARIABLES desks, own, pc, seen, holder
vars == <<desks, own, pc, seen, holder>>

Off(a) == (a = "earlier" /\ ~Earlier) \/ (a = "ratify" /\ Separate /\ Earlier)
           \/ (a = "resend" /\ KeepWritten)
Init == desks = {} /\ own = {} /\ pc = [a \in Actors |-> IF Off(a) THEN "end" ELSE "start"]
        /\ seen = [a \in Actors |-> {}] /\ holder = "none"

Blind(a) == a = "resend" /\ ~ResendKeeps
Locks(a) == Locked /\ ~Blind(a) /\ a # "earlier"
InOwn(a) == Separate /\ a \in Here
Read(a) == pc[a] = "start" /\ (Locks(a) => holder = "none")
           /\ holder' = (IF Locks(a) THEN a ELSE holder)
           /\ seen' = [seen EXCEPT ![a] = IF InOwn(a) THEN own ELSE desks]
           /\ pc' = [pc EXCEPT ![a] = "write"] /\ UNCHANGED <<desks, own>>
Write(a) == pc[a] = "write"
            /\ (IF InOwn(a) THEN own' = seen[a] \cup {a} /\ UNCHANGED desks
                ELSE desks' = (IF Blind(a) \/ (a = "ratify" /\ Separate) THEN {}
                               ELSE IF a \in {"ratify", "resend"} THEN seen[a]
                               ELSE seen[a] \cup {a})
                     /\ UNCHANGED own)
            /\ holder' = (IF Locks(a) THEN "none" ELSE holder)
            /\ pc' = [pc EXCEPT ![a] = "end"] /\ UNCHANGED seen

Next == \E a \in Actors : Read(a) \/ Write(a)
Spec == Init /\ [][Next]_vars

\* Every desk built here is listed once nobody is between reading and writing a list.
DesksKept == \A a \in Here : pc[a] = "end" /\ (\A b \in Actors : pc[b] # "write") => a \in desks \cup own
\* The earlier release's desk is listed too. It adds it without a lock, so a resend that read
\* the list under its own lock and wrote it back could drop it (without KeepWritten).
EarlierKept == pc["earlier"] = "end" /\ Earlier /\ (\A b \in Actors : pc[b] # "write") => "earlier" \in desks
NeverBuilt == desks \cup own = {}
====
