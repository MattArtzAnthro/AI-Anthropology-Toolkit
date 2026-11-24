---- MODULE DeskView ----
\* One desk, finished from the conversation (record_desk_decisions) or from its view in the
\* conversation (desk_finish), with crashes. The view, when it first opens the desk, writes
\* saved.json, which holds the desk for the view. A finish writes finishing.json (the digest of
\* its decisions), then the ratification, then finished.json; a crash between leaves
\* finishing.json, and only decisions with the same digest complete it. The decisions saved in
\* the view have digest "v"; the conversation sends its own ("c"), or a copy of the view's
\* ("v"), as a researcher may paste them. While a finish is pending the view saves nothing.
\* ViewWaits: the view does not take a desk whose finish is pending.
\* Resume: while the view holds the desk, the conversation may complete a pending finish:
\* "never", "own" (one that is not the view's own decisions), or "any".
\* Legacy: the store may start with a desk an earlier release left: held by the view over an
\* interrupted finish from the conversation.
EXTENDS Naturals
CONSTANTS ViewWaits, Resume, Legacy, MaxCrashes
VARIABLES saved, finishing, finished, by, chat, view, crashes
vars == <<saved, finishing, finished, by, chat, view, crashes>>

Init == /\ finished = FALSE /\ by = "none" /\ chat = "idle" /\ view = "idle" /\ crashes = 0
        /\ \/ saved = FALSE /\ finishing = "none"
           \/ Legacy /\ saved = TRUE /\ finishing = "c"

\* record_desk_decisions, sending digest d.
ChatAllowed(d) == \/ ~saved
                  \/ Resume = "any" /\ finishing # "none"
                  \/ Resume = "own" /\ finishing \notin {"none", "v"}
ChatBegin == chat = "idle" /\ ~finished
             /\ \E d \in {"c", "v"} : ChatAllowed(d) /\ finishing \in {"none", d} /\ finishing' = d
             /\ chat' = "mid" /\ UNCHANGED <<saved, finished, by, view, crashes>>
ChatEnd == chat = "mid" /\ ~finished /\ finished' = TRUE /\ by' = "chat" /\ chat' = "idle"
           /\ UNCHANGED <<saved, finishing, view, crashes>>
\* The view opens the desk (desk_sync with no action).
ViewOpen == ~saved /\ ~finished /\ (ViewWaits => finishing = "none") /\ saved' = TRUE
            /\ UNCHANGED <<finishing, finished, by, chat, view, crashes>>
\* Ratify in the view: applies what the view saved.
ViewBegin == saved /\ view = "idle" /\ ~finished /\ finishing \in {"none", "v"}
             /\ finishing' = "v" /\ view' = "mid" /\ UNCHANGED <<saved, finished, by, chat, crashes>>
ViewEnd == view = "mid" /\ ~finished /\ finished' = TRUE /\ by' = "view" /\ view' = "idle"
           /\ UNCHANGED <<saved, finishing, chat, crashes>>
Crash == crashes < MaxCrashes /\ crashes' = crashes + 1
         /\ \/ chat = "mid" /\ chat' = "idle" /\ UNCHANGED view
            \/ view = "mid" /\ view' = "idle" /\ UNCHANGED chat
         /\ UNCHANGED <<saved, finishing, finished, by>>

Progress == ChatBegin \/ ChatEnd \/ ViewOpen \/ ViewBegin \/ ViewEnd
Next == Progress \/ Crash
Spec == Init /\ [][Next]_vars

\* An unfinished desk can always be taken a step towards finishing by someone.
NotStuck == finished \/ ENABLED Progress
\* A desk the view holds and finishes with its own decisions is recorded as finished in the view.
ViewKeeps == finished /\ saved /\ finishing = "v" => by = "view"
\* Probe: the desk does finish.
NeverFinished == ~finished
====
