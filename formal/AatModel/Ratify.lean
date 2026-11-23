/-!
# ratify_codebook: what can be ratified, and what a ratification_id names

Models `server.ratify_codebook` given a `codebook_job_id`, `server.submit_batch` as it changes a
codebook job's result, and the check `start_coding_job` makes. A job has a kind, a status, the
content of its `result.json` (`result`, abstract: equal numbers are equal codebooks, so a
codebook's checksum is the number itself) and the checksum its `ratification.json` holds (`held`).

Taken as given: the checksum tells codebooks apart (`codebook_checksum` is SHA-256 over labels and
definitions), and the job store holds what was last written.

Specification:
* R1 `RatifiedIsCodebook`: only a finished codebook job is ratified by its id.
* R2 `Bound`: a ratification holds the checksum of the result it names, and the job is finished,
  so `start_coding_job`, which compares the two, codes with what was ratified.
* R3: once a ratification_id holds a checksum it holds that checksum for ever, whatever runs next:
  coding jobs and the rulings desks built on them are bound to one codebook.
-/
namespace AatModel.Ratify

inductive Kind | codebook | coding | desk | ratification
  deriving DecidableEq, Repr

inductive Status | inProgress | complete | failed
  deriving DecidableEq, Repr

structure RJob where
  kind : Kind
  status : Status
  result : Option Nat
  held : Option Nat
  deriving DecidableEq, Repr

def Bound (j : RJob) : Prop := ∀ c, j.held = some c → j.status = .complete ∧ j.result = some c

/-- `start_coding_job` with no codebook supplied: the ratification exists and the job's result
still has its checksum. -/
def startOk (j : RJob) : Bool := match j.held, j.result with
  | some c, some r => c == r
  | _, _ => false

/-! ## Before the fix -/

/-- Any job with a `result.json`, of any kind and status, is ratified, and ratifying again writes
whatever checksum the result has now. -/
def oldRatify (j : RJob) : Option RJob := match j.result with
  | some r => some { j with held := some r }
  | none => none

/-- `submit_batch` on a codebook job: any time, any status; a full queue writes a new result. -/
def oldSubmit (j : RJob) (r : Nat) : Option RJob :=
  if j.kind = .codebook then some { j with result := some r, status := .complete } else none

/-! ## As fixed -/

def newRatify (j : RJob) : Option RJob :=
  if j.kind ≠ .codebook ∨ j.status ≠ .complete then none
  else match j.result, j.held with
    | some r, none => some { j with held := some r }
    | some r, some c => if c = r then some j else none
    | none, _ => none

/-- `submit_batch` refuses a complete job (see `Submit.newSubmit`). -/
def newSubmit (j : RJob) (r : Nat) : Option RJob :=
  if j.kind = .codebook ∧ j.status ≠ .complete then some { j with result := some r, status := .complete }
  else none

inductive Step | ratify | submit (r : Nat)

def newStep (j : RJob) : Step → Option RJob
  | .ratify => newRatify j
  | .submit r => newSubmit j r

def oldStep (j : RJob) : Step → Option RJob
  | .ratify => oldRatify j
  | .submit r => oldSubmit j r

/-! ## The fixed rules meet the specification -/

/-- R1. -/
theorem new_ratifies_only_finished_codebooks (j j' : RJob) (h : newRatify j = some j') :
    j.kind = .codebook ∧ j.status = .complete := by
  unfold newRatify at h
  split at h
  · contradiction
  · rename_i hk; simp only [not_or, Classical.not_not] at hk; exact hk

/-- R2 holds from a job with no ratification, and every step keeps it. -/
theorem bound_initially (k : Kind) (s : Status) (r : Option Nat) : Bound ⟨k, s, r, none⟩ := by
  intro c h; cases h

theorem new_step_keeps_bound (j j' : RJob) (st : Step) (hb : Bound j)
    (h : newStep j st = some j') : Bound j' := by
  cases st with
  | ratify =>
    simp only [newStep, newRatify] at h
    split at h
    · contradiction
    · rename_i hk
      simp only [not_or, Classical.not_not] at hk
      split at h
      · cases h; intro c hc; cases hc; exact ⟨hk.2, by assumption⟩
      · split at h
        · cases h; exact hb
        · contradiction
      · contradiction
  | submit r =>
    simp only [newStep, newSubmit] at h
    split at h
    · rename_i hk
      cases h
      intro c hc
      exact absurd (hb c hc).1 hk.2
    · contradiction

/-- R3. -/
theorem new_held_never_changes (j j' : RJob) (st : Step) (c : Nat) (hb : Bound j)
    (hc : j.held = some c) (h : newStep j st = some j') : j'.held = some c := by
  cases st with
  | ratify =>
    simp only [newStep, newRatify] at h
    split at h
    · contradiction
    · split at h
      · rename_i heq; rw [hc] at heq; cases heq
      · split at h
        · cases h; exact hc
        · contradiction
      · contradiction
  | submit r =>
    simp only [newStep, newSubmit] at h
    split at h
    · rename_i hk; exact absurd (hb c hc).1 hk.2
    · contradiction

/-- R2 is what makes the coding gate mean something: a bound ratification always passes it. -/
theorem bound_start_ok (j : RJob) (c : Nat) (hb : Bound j) (hc : j.held = some c) :
    startOk j = true := by
  have := (hb c hc).2
  simp [startOk, hc, this]

/-! ## The holes in the old rules -/

/-- A coding job still in progress is ratified as a codebook. -/
theorem old_ratifies_coding_job :
    (oldRatify ⟨.coding, .inProgress, some 5, none⟩).isSome = true := by decide

theorem new_refuses_coding_job : newRatify ⟨.coding, .inProgress, some 5, none⟩ = none := by decide

/-- A packet sent again to a finished, ratified codebook job changes its result; ratifying the
same id again moves the ratification to the new codebook, under coding jobs bound to the old. -/
def ratified : RJob := ⟨.codebook, .complete, some 1, some 1⟩

theorem old_ratification_drifts :
    ((oldStep ratified (.submit 2)).bind (oldStep · .ratify)).map RJob.held = some (some 2) := by decide

theorem new_refuses_drift : newStep ratified (.submit 2) = none := by decide

theorem new_refuses_rebinding : newRatify ⟨.codebook, .complete, some 2, some 1⟩ = none := by decide

end AatModel.Ratify
