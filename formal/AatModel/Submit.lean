/-!
# submit_batch: what a delegated job accepts, and when it is complete

Models `server.submit_batch` for one job. A job holds the packet ids it issued (`queue`, from
`queue.json`), the ids recorded as answered (`done`, `done_ids.json`), the ids whose responses
were merged into the result (`counted`, from `ledger.json`: for a codebook job each merge adds to
a code's frequency), and its status. Ids are numbers; the model does not look at what a response
says. A job may come from an earlier release, which issued one id for two chunks, recorded ids
it never issued as answered, marked a job complete with packets unanswered, and merged packets
without recording them in `ledger.json`; so a job's `queue` may repeat an id, its `done` may hold
ids it never issued, its `complete` may be early, and its `counted` may lack answered packets.

The model holds ids, not files: `Kept` says the packets taken as merged include every packet
answered, which the rule sets up by construction. That the codes are in the file the server then
reads is what `tla/Count.tla` and the findings tests check.

Taken as given: the JSON files hold what was last written (the TLA+ model `Submit.tla` covers two
calls at once), and `queue.json` is written once, at the start.

Specification, in the job's terms:
* S1 `Honest`: a job reported complete has an answer for every packet it issued.
* S2 `OnlyIssued`: only packets the job issued are recorded as answered.
* S3 `CountedOnce`: no packet's response is merged into the result twice.
* S4: nothing changes a complete job, and a job that is not delegated takes no packets.
* S5 `Kept`: every packet recorded as answered has its response merged.
* S6: a queue that gives two packets one id takes no batches: their answers cannot be told apart.
-/
namespace AatModel.Submit

structure Job where
  queue : List Nat
  delegated : Bool
  done : List Nat
  counted : List Nat
  complete : Bool
  deriving DecidableEq, Repr

def Honest (j : Job) : Prop := j.complete = true → ∀ q ∈ j.queue, q ∈ j.done
def OnlyIssued (j : Job) : Prop := ∀ d ∈ j.done, d ∈ j.queue
def CountedOnce (j : Job) : Prop := j.counted.Nodup
def Kept (j : Job) : Prop := ∀ d ∈ j.done, d ∈ j.counted

/-- `done_ids` as a set: each submitted id joins it once. -/
def addAll : List Nat → List Nat → List Nat
  | d, [] => d
  | d, x :: xs => addAll (if x ∈ d then d else d ++ [x]) xs

/-- The ids a batch adds that were not answered before, in order, each once. -/
def fresh : List Nat → List Nat → List Nat
  | _, [] => []
  | d, x :: xs => if x ∈ d then fresh d xs else x :: fresh (d ++ [x]) xs

/-! ## The rule before the fix

Every submitted id joins `done`, issued or not, whatever the job's mode or status. Each item's
response is merged (`counted ++ sub`). The job is complete when `len(done_ids) >= len(queue)`
(codebook) or `len(queue) - len(done_ids) <= 0` (coding): the same count. An api-mode job has no
`queue.json`, so its queue is empty. -/
def oldSubmit (j : Job) (sub : List Nat) : Job :=
  let d := addAll j.done sub
  { j with done := d, counted := j.counted ++ sub, complete := decide (j.queue.length ≤ d.length) }

/-! ## The rule as first fixed

`none` is a refusal that writes nothing. A batch is refused when the job is not delegated, is
already complete, or names any id the job did not issue. Ids not counted are merged. The job is
complete when every issued id is answered. -/
def fix1Submit (j : Job) (sub : List Nat) : Option Job :=
  if j.delegated = false then none
  else if j.complete = true then none
  else if sub.all (fun x => x ∈ j.queue) = false then none
  else
    let d := addAll j.done sub
    some { j with done := d, counted := j.counted ++ fresh j.counted sub,
                  complete := j.queue.all (fun q => q ∈ d) }

/-! ## The rule as fixed

As first fixed, and: a queue that repeats an id is refused; only issued ids count as answered
(`live`); a job is taken to be complete only when every issued id is answered, so a job marked
complete early takes its unanswered packets; and the packets merged are those counted and those
answered (`addAll counted live`), so a packet an earlier release merged without counting it is
not merged again. -/
def newSubmit (j : Job) (sub : List Nat) : Option Job :=
  if j.delegated = false then none
  else if decide j.queue.Nodup = false then none
  else if (j.complete && j.queue.all (fun q => q ∈ j.done)) = true then none
  else if sub.all (fun x => x ∈ j.queue) = false then none
  else
    let live := j.done.filter (fun x => x ∈ j.queue)
    let d := addAll live sub
    let base := addAll j.counted live
    some { j with done := d, counted := base ++ fresh base sub,
                  complete := j.queue.all (fun q => q ∈ d) }

/-! ## Lemmas -/

theorem mem_addAll (d s : List Nat) (x : Nat) : x ∈ addAll d s ↔ x ∈ d ∨ x ∈ s := by
  induction s generalizing d with
  | nil => simp [addAll]
  | cons y ys ih =>
    simp only [addAll]
    split
    · rw [ih]; constructor
      · intro h; cases h with
        | inl h => exact Or.inl h
        | inr h => exact Or.inr (List.mem_cons_of_mem _ h)
      · intro h; cases h with
        | inl h => exact Or.inl h
        | inr h =>
          cases List.mem_cons.mp h with
          | inl e => subst e; exact Or.inl (by assumption)
          | inr h => exact Or.inr h
    · rw [ih]; simp [List.mem_append, List.mem_cons, or_assoc]

theorem addAll_eq (d s : List Nat) : addAll d s = d ++ fresh d s := by
  induction s generalizing d with
  | nil => simp [addAll, fresh]
  | cons y ys ih =>
    simp only [addAll, fresh]
    split
    · exact ih d
    · rw [ih]; simp

theorem addAll_of_all_mem (d s : List Nat) (h : ∀ x ∈ s, x ∈ d) : addAll d s = d := by
  induction s generalizing d with
  | nil => simp [addAll]
  | cons y ys ih =>
    simp only [addAll]
    have hy : y ∈ d := h y (List.mem_cons_self ..)
    simp only [hy, ite_true]
    exact ih d (fun x hx => h x (List.mem_cons_of_mem _ hx))

theorem nodup_addAll (d s : List Nat) (h : d.Nodup) : (addAll d s).Nodup := by
  induction s generalizing d with
  | nil => simpa [addAll]
  | cons y ys ih =>
    simp only [addAll]
    split
    · exact ih d h
    · apply ih
      rw [List.nodup_append]
      refine ⟨h, List.pairwise_singleton _ y, ?_⟩
      intro a ha b hb
      simp at hb; subst hb
      intro e; subst e; contradiction

/-! ## The fixed rule meets the specification -/

/-- Opens an accepted call: the refusals did not fire. -/
theorem newSubmit_some (j j' : Job) (sub : List Nat) (h : newSubmit j sub = some j') :
    sub.all (fun x => decide (x ∈ j.queue)) = true ∧
    j' = { j with done := addAll (j.done.filter (fun x => x ∈ j.queue)) sub,
                  counted := addAll j.counted (j.done.filter (fun x => x ∈ j.queue)) ++
                    fresh (addAll j.counted (j.done.filter (fun x => x ∈ j.queue))) sub,
                  complete := j.queue.all (fun q => q ∈ addAll (j.done.filter (fun x => x ∈ j.queue)) sub) } := by
  unfold newSubmit at h
  split at h; · contradiction
  split at h; · contradiction
  split at h; · contradiction
  split at h
  · contradiction
  · rename_i hall
    refine ⟨?_, (Option.some.inj h).symm⟩
    cases e : (sub.all fun x => decide (x ∈ j.queue)) <;> simp_all

/-- S1. -/
theorem new_complete_is_honest (j j' : Job) (sub : List Nat) (h : newSubmit j sub = some j') :
    Honest j' := by
  obtain ⟨_, rfl⟩ := newSubmit_some j j' sub h
  intro hc q hq
  have := List.all_eq_true.mp hc q hq
  simpa using this

/-- S2, after every accepted batch, whatever an earlier release recorded. -/
theorem new_only_issued (j j' : Job) (sub : List Nat)
    (h : newSubmit j sub = some j') : OnlyIssued j' := by
  obtain ⟨hall, rfl⟩ := newSubmit_some j j' sub h
  intro x hx
  cases (mem_addAll _ _ _).mp hx with
  | inl h => exact (List.mem_filter.mp h).2 |> of_decide_eq_true
  | inr h => simpa using List.all_eq_true.mp hall x h

/-- S3: a packet is merged at most once, whatever the job holds. -/
theorem new_counts_once (j j' : Job) (sub : List Nat) (hc : j.counted.Nodup)
    (h : newSubmit j sub = some j') : CountedOnce j' := by
  obtain ⟨_, rfl⟩ := newSubmit_some j j' sub h
  unfold CountedOnce
  simp only
  rw [← addAll_eq]
  exact nodup_addAll _ _ (nodup_addAll _ _ hc)

/-- S5: every packet recorded as answered is merged after the call, whatever the job held
before (an earlier release may have answered packets the ledger never counted). -/
theorem new_keeps_answered (j j' : Job) (sub : List Nat) (h : newSubmit j sub = some j') :
    Kept j' := by
  obtain ⟨_, rfl⟩ := newSubmit_some j j' sub h
  intro x hx
  simp only at hx ⊢
  rw [← addAll_eq, mem_addAll, mem_addAll]
  cases (mem_addAll _ _ _).mp hx with
  | inl h => exact Or.inl (Or.inr h)
  | inr h => exact Or.inr h

/-- In a job this release wrote, the packets merged are the packets answered, and stay so. -/
theorem new_counted_stays_done (j j' : Job) (sub : List Nat) (hc : j.counted = j.done)
    (hi : OnlyIssued j) (h : newSubmit j sub = some j') : j'.counted = j'.done := by
  have hl : j.done.filter (fun x => decide (x ∈ j.queue)) = j.done :=
    List.filter_eq_self.mpr (fun x hx => by simpa using hi x hx)
  obtain ⟨_, rfl⟩ := newSubmit_some j j' sub h
  simp only
  rw [hl, hc, addAll_of_all_mem _ _ (fun _ hx => hx), ← addAll_eq]

/-- S4. -/
theorem new_complete_is_final (j : Job) (sub : List Nat) (h : j.complete = true)
    (ha : ∀ q ∈ j.queue, q ∈ j.done) : newSubmit j sub = none := by
  have hall : j.queue.all (fun q => decide (q ∈ j.done)) = true :=
    List.all_eq_true.mpr (fun q hq => by simpa using ha q hq)
  unfold newSubmit
  split; · rfl
  split; · rfl
  rw [h, hall]; simp

theorem new_refuses_api_jobs (j : Job) (sub : List Nat) (h : j.delegated = false) :
    newSubmit j sub = none := by
  unfold newSubmit; simp [h]

/-- S6. -/
theorem new_refuses_repeated_queue (j : Job) (sub : List Nat) (h : ¬ j.queue.Nodup) :
    newSubmit j sub = none := by
  unfold newSubmit
  split; · rfl
  simp [h]

/-! ## The holes in the old rule, and the fixed rule on the same inputs -/

def job3 : Job := ⟨[0, 1, 2], true, [], [], false⟩

/-- An id the job never issued counts toward completion: complete with packets 1 and 2 unanswered. -/
theorem old_completes_with_unanswered :
    (oldSubmit job3 [0, 7, 8]).complete = true ∧ 1 ∉ (oldSubmit job3 [0, 7, 8]).done := by decide

theorem new_refuses_unissued : newSubmit job3 [0, 7, 8] = none := by decide

/-- An api-mode job (no queue) is marked complete by any submission while its worker runs. -/
theorem old_completes_api_job :
    (oldSubmit ⟨[], false, [], [], false⟩ [0]).complete = true := by decide

/-- A packet sent twice is merged twice (a codebook code's frequency doubles). -/
theorem old_counts_twice :
    (oldSubmit (oldSubmit job3 [0]) [0]).counted = [0, 0] := by decide

theorem new_counts_resend_once :
    ((newSubmit job3 [0]).bind (newSubmit · [0])).map Job.counted = some [0] := by decide

/-- A submission to a complete job is merged and rewrites the result. -/
theorem old_takes_after_complete :
    (oldSubmit (oldSubmit job3 [0, 1, 2]) [1]).counted = [0, 1, 2, 1] := by decide

/-- Two chunks sharing an id (as `chunk_transcript` gives two interviews): every packet
answered, yet the count never reaches the queue. New jobs no longer issue such a queue
(`Packets.packet_ids_distinct`). -/
theorem old_duplicate_ids_never_complete :
    (oldSubmit ⟨[3, 3], true, [], [], false⟩ [3]).complete = false := by decide

/-! ## The holes the first fix left, on jobs an earlier release wrote -/

/-- A queue an earlier release issued with one id for two chunks completes on one answer, which
the result then gives to both chunks. -/
theorem fix1_repeated_queue_completes :
    (fix1Submit ⟨[3, 3], true, [], [], false⟩ [3]).map Job.complete = some true := by decide

theorem new_refuses_repeated_queue_example :
    newSubmit ⟨[3, 3], true, [], [], false⟩ [3] = none := by decide

/-- A job an earlier release marked complete with packet 1 unanswered can never be finished. -/
theorem fix1_stuck_on_early_complete :
    fix1Submit ⟨[0, 1], true, [0], [0], true⟩ [1] = none := by decide

theorem new_reopens_early_complete :
    (newSubmit ⟨[0, 1], true, [0], [0], true⟩ [1]).map Job.complete = some true := by decide

/-- Packet 1 merged by an earlier release, which does not write the ledger: the next batch
started from the ledger and lost it, though it is recorded as answered. -/
theorem fix1_loses_stale_ledger :
    (fix1Submit ⟨[0, 1, 2], true, [0, 1], [0], false⟩ [2]).map
      (fun j' => (decide (1 ∈ j'.done), decide (1 ∈ j'.counted))) = some (true, false) := by decide

/-- An earlier release recorded id 9, which the job never issued, as answered, and marked the
job complete. The fixed rule drops 9, takes the unanswered packet, and completes on it. -/
theorem fix1_stuck_on_unissued_done :
    fix1Submit ⟨[0, 1], true, [0, 9], [0, 9], true⟩ [1] = none := by decide

theorem new_drops_unissued_done :
    (newSubmit ⟨[0, 1], true, [0, 9], [0, 9], true⟩ [1]).map (fun j' => (j'.done, j'.complete))
      = some ([0, 1], true) := by decide

theorem new_keeps_stale_ledger :
    (newSubmit ⟨[0, 1, 2], true, [0, 1], [0], false⟩ [2]).map
      (fun j' => (decide (1 ∈ j'.done), decide (1 ∈ j'.counted))) = some (true, true) := by decide

end AatModel.Submit
