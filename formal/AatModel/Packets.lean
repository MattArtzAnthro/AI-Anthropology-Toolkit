/-!
# Packet IDs: one per chunk, all different, named by the chunk

Models `server._packet_ids`. A chunk is its source file (`source_file`; `0` here for none), its
ID (its chunk_id, or its position when it has none), and its text (a number here; the server
names it by a digest). `chunk_transcript` numbers each transcript's chunks from 1, so the chunks
of several interviews share IDs. Before, the packet ID was the chunk's ID: two chunks shared one
packet, one answer coded both, and the job never completed
(`Submit.old_duplicate_ids_never_complete`).

The packet ID is what coded records are matched on across coding passes (`models.record_key`),
so it names the chunk rather than its place in the list: two passes over the same interviews in
another order still match chunk to chunk. When IDs repeat, a chunk is named by its source and ID;
by its source, ID and text when another chunk has that source and ID (`chunk_transcript` keeps a
file's base name, so `P01/transcript.txt` and `P02/transcript.txt` are both `transcript.txt`);
and with no source, by its ID and text. Chunks with the same name are numbered in order, and
only they depend on the order, being alike in source, ID and text, or in ID and text.

Specification:
* P1: every chunk gets a packet, and no two packets share an ID.
* P2: when the chunks' IDs are already all different, the packet IDs are those IDs (jobs and
  answers keep the IDs a caller knows).
* P3: when IDs repeat, a chunk no other chunk is named like gets the same packet ID wherever it
  stands in the list.

Not modelled: the server writes each name as a string (`s#3`, `3~<digest>`) and numbers the
chunks whose strings are alike, a repeat written `/2`; two names that differ here but are written
alike (a source or chunk ID holding `#` or `~`) are numbered as alike. Should a numbered string be
another chunk's own (a chunk ID holding `/2`), every chunk carries its position (`0:3`), unique
by the position.
-/
namespace AatModel.Packets

/-- What a chunk is named by when chunk IDs repeat. -/
inductive Name | sourced (src id : Nat) | sourcedText (src id text : Nat) | content (id text : Nat)
  deriving DecidableEq, Repr

/-- A packet ID: the chunk's ID, or its name and its rank among chunks so named. -/
inductive PacketId | plain (id : Nat) | named (n : Name) (k : Nat)
  deriving DecidableEq, Repr

abbrev Chunk := Nat × Nat × Nat  -- (source, id, text); source 0 is none

def chunkId (c : Chunk) : Nat := c.2.1

def key (c : Chunk) : Nat × Nat := (c.1, c.2.1)

/-- A chunk's name among `cs`: it depends on `cs` only through how many chunks share its source
and ID, so not on their order (`name_perm`). -/
def name (cs : List Chunk) (c : Chunk) : Name :=
  if c.1 = 0 then .content c.2.1 c.2.2
  else if (cs.map key).count (key c) = 1 then .sourced c.1 c.2.1
  else .sourcedText c.1 c.2.1 c.2.2

/-- Each name with the number of times it came before (`acc`, the names already seen). -/
def number : List Name → List Name → List (Name × Nat)
  | _, [] => []
  | acc, n :: ns => (n, acc.count n) :: number (acc ++ [n]) ns

def oldIds (cs : List Chunk) : List PacketId := cs.map (fun c => .plain (chunkId c))

def packetIds (cs : List Chunk) : List PacketId :=
  if (cs.map chunkId).Nodup then cs.map (fun c => .plain (chunkId c))
  else (number [] (cs.map (name cs))).map (fun p => .named p.1 p.2)

/-! ## Lemmas -/

theorem number_length (acc l : List Name) : (number acc l).length = l.length := by
  induction l generalizing acc with
  | nil => rfl
  | cons n ns ih => simp [number, ih]

theorem number_ge (acc l : List Name) : ∀ p ∈ number acc l, acc.count p.1 ≤ p.2 := by
  induction l generalizing acc with
  | nil => simp [number]
  | cons n ns ih =>
    intro p hp
    simp only [number, List.mem_cons] at hp
    cases hp with
    | inl h => subst h; exact Nat.le_refl _
    | inr h =>
      have := ih (acc ++ [n]) p h
      rw [List.count_append] at this
      omega

theorem number_lt (acc l : List Name) : ∀ p ∈ number acc l, p.2 < (acc ++ l).count p.1 := by
  induction l generalizing acc with
  | nil => simp [number]
  | cons n ns ih =>
    intro p hp
    simp only [number, List.mem_cons] at hp
    cases hp with
    | inl h => subst h; simp [List.count_append]
    | inr h =>
      have := ih (acc ++ [n]) p h
      simpa [List.append_assoc] using this

theorem number_mem (acc l : List Name) : ∀ n ∈ l, ∃ k, (n, k) ∈ number acc l := by
  induction l generalizing acc with
  | nil => simp
  | cons m ms ih =>
    intro n hn
    simp only [number, List.mem_cons] at hn ⊢
    cases hn with
    | inl h => subst h; exact ⟨acc.count n, Or.inl rfl⟩
    | inr h => obtain ⟨k, hk⟩ := ih (acc ++ [m]) n h; exact ⟨k, Or.inr hk⟩

theorem number_nodup (acc l : List Name) : (number acc l).Nodup := by
  induction l generalizing acc with
  | nil => simp [number]
  | cons n ns ih =>
    simp only [number, List.nodup_cons]
    refine ⟨?_, ih (acc ++ [n])⟩
    intro hmem
    have := number_ge (acc ++ [n]) ns (n, acc.count n) hmem
    simp [List.count_append] at this
    omega

theorem nodup_map_of_inj {α β : Type} (f : α → β) (hf : ∀ a b, f a = f b → a = b) :
    ∀ l : List α, l.Nodup → (l.map f).Nodup
  | [], _ => by simp
  | a :: t, h => by
    simp only [List.map_cons, List.nodup_cons, List.mem_map] at h ⊢
    refine ⟨?_, nodup_map_of_inj f hf t h.2⟩
    rintro ⟨b, hb, e⟩
    exact h.1 (hf b a e ▸ hb)

/-! ## The rule meets the specification -/

theorem packet_ids_one_per_chunk (cs : List Chunk) : (packetIds cs).length = cs.length := by
  unfold packetIds; split <;> simp [number_length]

/-- P1. -/
theorem packet_ids_distinct (cs : List Chunk) : (packetIds cs).Nodup := by
  unfold packetIds
  split
  · rename_i h
    have e : cs.map (fun c => PacketId.plain (chunkId c)) = (cs.map chunkId).map PacketId.plain := by
      simp [List.map_map]
    rw [e]
    exact nodup_map_of_inj _ (fun a b h => by injection h) _ h
  · exact nodup_map_of_inj _ (fun a b h => by injection h with h1 h2; exact Prod.ext h1 h2) _
      (number_nodup [] _)

/-- P2. -/
theorem packet_ids_keep_distinct_ids (cs : List Chunk) (h : (cs.map chunkId).Nodup) :
    packetIds cs = cs.map (fun c => .plain (chunkId c)) := by
  unfold packetIds; simp [h]

/-- A chunk's name is the same in any order of the chunks. -/
theorem name_perm {cs ds : List Chunk} (hp : cs.Perm ds) (c : Chunk) : name cs c = name ds c := by
  unfold name
  rw [(hp.map key).count_eq]

/-- P3: a chunk named like no other has packet `named (name cs c) 0`, wherever it stands. -/
theorem packet_ids_name_the_chunk (cs : List Chunk) (h : ¬ (cs.map chunkId).Nodup) (c : Chunk)
    (hc : c ∈ cs) (hu : (cs.map (name cs)).count (name cs c) = 1) :
    PacketId.named (name cs c) 0 ∈ packetIds cs := by
  unfold packetIds
  simp only [h, ite_false, List.mem_map]
  obtain ⟨k, hk⟩ := number_mem [] (cs.map (name cs)) (name cs c) (List.mem_map_of_mem hc)
  have hlt := number_lt [] (cs.map (name cs)) _ hk
  simp only [List.nil_append, hu] at hlt
  exact ⟨(name cs c, k), hk, by simp; omega⟩

/-- Two interviews chunked separately: the old rule gave chunk 1 of each the same packet. -/
theorem old_ids_collide : ¬ (oldIds [(1, 1, 5), (1, 2, 6), (2, 1, 7), (2, 2, 8)]).Nodup := by
  decide

/-- The same two interviews coded in the other order: each chunk keeps its packet ID. -/
theorem order_kept :
    packetIds [(2, 1, 7), (2, 2, 8), (1, 1, 5), (1, 2, 6)] =
      [.named (.sourced 2 1) 0, .named (.sourced 2 2) 0, .named (.sourced 1 1) 0,
       .named (.sourced 1 2) 0] ∧
    packetIds [(1, 1, 5), (1, 2, 6), (2, 1, 7), (2, 2, 8)] =
      [.named (.sourced 1 1) 0, .named (.sourced 1 2) 0, .named (.sourced 2 1) 0,
       .named (.sourced 2 2) 0] := by decide

/-- Without source files the chunks are named by their text, and keep their IDs in any order. -/
theorem order_kept_without_sources :
    packetIds [(0, 1, 7), (0, 2, 8), (0, 1, 5), (0, 2, 6)] =
      [.named (.content 1 7) 0, .named (.content 2 8) 0, .named (.content 1 5) 0,
       .named (.content 2 6) 0] := by decide

/-- Two interviews whose files share a base name: their chunks are named by their text too,
and keep their IDs in either order. -/
theorem same_file_name_kept :
    packetIds [(3, 1, 5), (3, 1, 6)] = [.named (.sourcedText 3 1 5) 0, .named (.sourcedText 3 1 6) 0] ∧
    packetIds [(3, 1, 6), (3, 1, 5)] = [.named (.sourcedText 3 1 6) 0, .named (.sourcedText 3 1 5) 0] := by
  decide

/-- Two chunks alike in ID and text are numbered in order. -/
theorem alike_numbered :
    packetIds [(0, 1, 5), (0, 1, 5)] = [.named (.content 1 5) 0, .named (.content 1 5) 1] := by
  decide

end AatModel.Packets
