import AatModel
open AatModel

/-! Prints `vectors.json`: the fixed rules' verdicts on every small case, which
`tests/package/test_formal_conformance.py` holds the Python to. -/

def jsonList (xs : List Nat) : String := "[" ++ ", ".intercalate (xs.map toString) ++ "]"
def jsonBool (b : Bool) : String := if b then "true" else "false"

/-- Sublists of `l` without repeats, in order. -/
def sublists : List Nat → List (List Nat)
  | [] => [[]]
  | x :: xs => let r := sublists xs; r ++ r.map (x :: ·)

def queues : List (List Nat) := [[], [0], [0, 1], [0, 1, 2], [3, 3]]
def batches : List (List Nat) := [[], [0], [1], [9], [0, 1], [0, 0], [0, 9], [1, 2], [3], [0, 1, 2]]

def submitCases : List String := Id.run do
  let mut out := []
  for q in queues do
    for d in sublists q.eraseDups do
      for del in [true, false] do
        for comp in [false, true] do
          if comp && !(q.all (· ∈ d)) then continue
          for s in batches do
            let j : Submit.Job := ⟨q, del, d, d, comp⟩
            let v := match Submit.newSubmit j s with
              | none => "\"refused\": true"
              | some j' => s!"\"refused\": false, \"done_after\": {jsonList j'.done}, \"counted\": {jsonList j'.counted}, \"complete_after\": {jsonBool j'.complete}"
            out := out ++ [s!"\{\"queue\": {jsonList q}, \"delegated\": {jsonBool del}, \"done\": {jsonList d}, \"complete\": {jsonBool comp}, \"submit\": {jsonList s}, {v}}"]
  return out

def kindName : Ratify.Kind → String
  | .codebook => "codebook" | .coding => "coding" | .desk => "desk" | .ratification => "ratification"
def statusName : Ratify.Status → String
  | .inProgress => "in_progress" | .complete => "complete" | .failed => "failed"
def optNat : Option Nat → String
  | none => "null" | some n => toString n

def ratifyCases : List String := Id.run do
  let mut out := []
  for k in [Ratify.Kind.codebook, .coding, .desk, .ratification] do
    for st in [Ratify.Status.inProgress, .complete, .failed] do
      for r in [none, some 1] do
        for h in [none, some 1, some 2] do
          let v := match Ratify.newRatify ⟨k, st, r, h⟩ with
            | none => "\"refused\": true"
            | some j' => s!"\"refused\": false, \"held_after\": {optNat j'.held}"
          out := out ++ [s!"\{\"kind\": \"{kindName k}\", \"status\": \"{statusName st}\", \"result\": {optNat r}, \"held\": {optNat h}, {v}}"]
  return out

def idLists : List (List Nat) := Id.run do
  let mut out := [[]]
  for a in [1, 2] do
    out := out ++ [[a]]
    for b in [1, 2] do
      out := out ++ [[a, b]]
      for c in [1, 2, 3] do
        out := out ++ [[a, b, c]]
  return out

def pidName : Packets.PacketId → String
  | .plain i => s!"\"{i}\""
  | .placed p i => s!"\"{p}:{i}\""

def packetCases : List String :=
  idLists.map fun ids =>
    s!"\{\"chunk_ids\": {jsonList ids}, \"packets\": [{", ".intercalate ((Packets.packetIds ids).map pidName)}]}"

def main : IO Unit := do
  IO.println "{\"submit\": ["
  IO.println (",\n".intercalate submitCases)
  IO.println "], \"ratify\": ["
  IO.println (",\n".intercalate ratifyCases)
  IO.println "], \"packets\": ["
  IO.println (",\n".intercalate packetCases)
  IO.println "]}"
