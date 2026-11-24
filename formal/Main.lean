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

/-- Ledgers a job may hold beside `done`: none (counted = done), the same, one more (a batch
merged then failed before done_ids.json), one fewer (an earlier release answered a packet the
ledger never counted), and one fewer with one more (both). -/
def ledgers (q d : List Nat) : List (Option (List Nat)) :=
  let extra := q.eraseDups.filter (· ∉ d)
  [none, some d] ++ extra.map (fun x => some (d ++ [x]))
    ++ d.map (fun x => some (d.erase x))
    ++ (d.flatMap fun x => extra.map fun y => some (d.erase x ++ [y]))

def jsonOpt : Option (List Nat) → String
  | none => "null" | some l => jsonList l

def submitCases : List String := Id.run do
  let mut out := []
  for q in queues do
    -- an earlier release may have recorded id 9, never issued, as answered
    for (d, legacy) in (sublists q.eraseDups).map (·, false) ++ (sublists q.eraseDups).map (· ++ [9], true) do
      for del in (if legacy then [true] else [true, false]) do
        for comp in [false, true] do
          for led in (if del && !legacy then ledgers q d else [none]) do
            for s in batches do
              let j : Submit.Job := ⟨q, del, d, led.getD d, comp⟩
              let v := match Submit.newSubmit j s with
                | none => "\"refused\": true"
                | some j' => s!"\"refused\": false, \"done_after\": {jsonList j'.done}, \"counted\": {jsonList j'.counted}, \"complete_after\": {jsonBool j'.complete}"
              out := out ++ [s!"\{\"queue\": {jsonList q}, \"delegated\": {jsonBool del}, \"done\": {jsonList d}, \"ledger\": {jsonOpt led}, \"complete\": {jsonBool comp}, \"submit\": {jsonList s}, {v}}"]
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

/-- Chunks as (source, id, text); source 0 has no source_file. -/
def chunkLists : List (List (Nat × Nat × Nat)) := Id.run do
  let mut out : List (List (Nat × Nat × Nat)) := [[]]
  for a in [1, 2] do
    out := out ++ [[(1, a, a)]]
    for b in [1, 2] do
      out := out ++ [[(1, a, a), (1, b, 10 + b)]]
      for c in [1, 2, 3] do
        out := out ++ [[(1, a, a), (1, b, 10 + b), (1, c, 20 + c)]]
  -- two interviews, in both orders, with and without source files
  for srcs in [[1, 1, 2, 2], [2, 2, 1, 1], [0, 0, 2, 2], [1, 1, 1, 1], [0, 0, 0, 0]] do
    out := out ++ [(srcs.zip [1, 2, 1, 2]).zip [1, 2, 3, 4] |>.map fun ((s, i), t) => (s, i, t)]
  out := out ++ [[(0, 2, 4), (0, 1, 3), (0, 2, 2), (0, 1, 1)]]
  -- chunks alike in ID and text, with and without a source
  out := out ++ [[(0, 1, 5), (0, 1, 5)], [(0, 1, 5), (0, 2, 6), (0, 1, 5)], [(3, 1, 5), (3, 1, 6)],
                 [(3, 1, 6), (3, 1, 5)], [(3, 1, 5), (0, 1, 5), (3, 1, 5)], [(3, 1, 5), (3, 2, 6), (3, 1, 7)]]
  return out

/-- A packet as JSON: ["plain", id], ["sourced", source, id, k],
["sourced_text", source, id, text, k] or ["content", id, text, k]. -/
def pidJson : Packets.PacketId → String
  | .plain i => s!"[\"plain\", {i}]"
  | .named (.sourced s i) k => s!"[\"sourced\", {s}, {i}, {k}]"
  | .named (.sourcedText s i t) k => s!"[\"sourced_text\", {s}, {i}, {t}, {k}]"
  | .named (.content i t) k => s!"[\"content\", {i}, {t}, {k}]"

def jsonChunks (cs : List (Nat × Nat × Nat)) : String :=
  "[" ++ ", ".intercalate (cs.map fun c => s!"[{c.1}, {c.2.1}, {c.2.2}]") ++ "]"

def packetCases : List String :=
  chunkLists.map fun cs =>
    s!"\{\"chunks\": {jsonChunks cs}, \"packets\": [{", ".intercalate ((Packets.packetIds cs).map pidJson)}]}"

def main : IO Unit := do
  IO.println "{\"submit\": ["
  IO.println (",\n".intercalate submitCases)
  IO.println "], \"ratify\": ["
  IO.println (",\n".intercalate ratifyCases)
  IO.println "], \"packets\": ["
  IO.println (",\n".intercalate packetCases)
  IO.println "]}"
