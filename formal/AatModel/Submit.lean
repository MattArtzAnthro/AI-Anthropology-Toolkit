/-!
# submit_batch: what a delegated job accepts, and when it is complete

Models `server.submit_batch` for one job. A job holds the packet ids it issued (`queue`, from
`queue.json`), the ids recorded as answered (`done`, `done_ids.json`), the ids whose responses
were merged into the result (`counted`: for a codebook job each merge adds to a code's frequency),
and its status. Ids are numbers; the model does not look at what a response says.

Taken as given: the JSON files hold what was last written (the TLA+ model `Submit.tla` covers two
calls at once), and `queue.json` is written once, at the start.

Specification, in the job's terms:
* S1 `Honest`: a job reported complete has an answer for every packet it issued.
* S2 `OnlyIssued`: only packets the job issued are recorded as answered.
* S3 `CountedOnce`: no packet's response is merged into the result twice.
* S4: nothing changes a complete job, and a job that is not delegated takes no packets.
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

/-! ## The rule as fixed

`none` is a refusal that writes nothing. A batch is refused when the job is not delegated, is
already complete, or names any id the job did not issue. Only fresh ids are merged. The job is
complete when every issued id is answered. -/
def newSubmit (j : Job) (sub : List Nat) : Option Job :=
  if j.delegated = false then none
  else if j.complete = true then none
  else if sub.all (fun x => x ∈ j.queue) = false then none
  else
    let d := addAll j.done sub
    some { j with done := d, counted := j.counted ++ fresh j.done sub,
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

/-- S1. -/
theorem new_complete_is_honest (j j' : Job) (sub : List Nat) (h : newSubmit j sub = some j') :
    Honest j' := by
  unfold newSubmit at h
  split at h; · contradiction
  split at h; · contradiction
  split at h; · contradiction
  cases h
  intro hc q hq
  have := List.all_eq_true.mp hc q hq
  simpa using this

/-- S2, kept by every accepted batch. -/
theorem new_only_issued (j j' : Job) (sub : List Nat) (hj : OnlyIssued j)
    (h : newSubmit j sub = some j') : OnlyIssued j' := by
  unfold newSubmit at h
  split at h; · contradiction
  split at h; · contradiction
  split at h
  · contradiction
  · rename_i hall
    cases h
    intro x hx
    cases (mem_addAll _ _ _).mp hx with
    | inl h => exact hj x h
    | inr h =>
      have : (sub.all fun x => decide (x ∈ j.queue)) = true := by
        cases e : (sub.all fun x => decide (x ∈ j.queue)) <;> simp_all
      simpa using List.all_eq_true.mp this x h

/-- S3: what is merged is exactly what is newly answered, so `counted` stays `done`. -/
theorem new_counts_once (j j' : Job) (sub : List Nat) (hc : j.counted = j.done)
    (hn : j.done.Nodup) (h : newSubmit j sub = some j') :
    j'.counted = j'.done ∧ CountedOnce j' := by
  unfold newSubmit at h
  split at h; · contradiction
  split at h; · contradiction
  split at h; · contradiction
  cases h
  have e : j.counted ++ fresh j.done sub = addAll j.done sub := by rw [hc, addAll_eq]
  exact ⟨e, by unfold CountedOnce; simp only; rw [e]; exact nodup_addAll _ _ hn⟩

/-- S4. -/
theorem new_complete_is_final (j : Job) (sub : List Nat) (h : j.complete = true) :
    newSubmit j sub = none := by
  unfold newSubmit; simp [h]

theorem new_refuses_api_jobs (j : Job) (sub : List Nat) (h : j.delegated = false) :
    newSubmit j sub = none := by
  unfold newSubmit; simp [h]

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

/-- Two chunks sharing an id: every packet answered, yet the count never reaches the queue. -/
theorem old_duplicate_ids_never_complete :
    (oldSubmit ⟨[3, 3], true, [], [], false⟩ [3]).complete = false := by decide

theorem new_duplicate_ids_complete :
    (newSubmit ⟨[3, 3], true, [], [], false⟩ [3]).map Job.complete = some true := by decide

end AatModel.Submit
