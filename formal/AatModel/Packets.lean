/-!
# Packet IDs: one per chunk, all different

Models `server._packet_ids`. A chunk is its source file (`source_file`; `0` here for none) and
its ID (its chunk_id, or its position when it has none). `chunk_transcript` numbers each
transcript's chunks from 1, so the chunks of several interviews share IDs. Before, the packet ID
was the chunk's ID: two chunks shared one packet, one answer coded both, and the job never
completed (`Submit.old_duplicate_ids_never_complete`).

The packet ID is what coded records are matched on across coding passes (`models.record_key`),
so where it can, it names the chunk rather than its place in the list: two passes over the same
interviews in another order then still match chunk to chunk.

Specification:
* P1: every chunk gets a packet, and no two packets share an ID.
* P2: when the chunks' IDs are already all different, the packet IDs are those IDs (jobs and
  answers keep the IDs a caller knows).
* P3: when IDs repeat but every chunk names its source file and no chunk repeats, a packet ID is
  the chunk's source and ID, whatever its position.
-/
namespace AatModel.Packets

/-- A packet ID: the chunk's ID; or its source and ID; or its position and ID. -/
inductive PacketId | plain (id : Nat) | sourced (src id : Nat) | placed (pos id : Nat)
  deriving DecidableEq, Repr

abbrev Chunk := Nat × Nat  -- (source, id); source 0 is none

def oldIds (cs : List Chunk) : List PacketId := cs.map (fun c => .plain c.2)

def sourcedOk (cs : List Chunk) : Bool := cs.all (fun c => c.1 != 0) && decide cs.Nodup

def packetIds (cs : List Chunk) : List PacketId :=
  if (cs.map Prod.snd).Nodup then cs.map (fun c => .plain c.2)
  else if sourcedOk cs then cs.map (fun c => .sourced c.1 c.2)
  else ((List.range cs.length).zip (cs.map Prod.snd)).map (fun p => .placed p.1 p.2)

theorem packet_ids_one_per_chunk (cs : List Chunk) : (packetIds cs).length = cs.length := by
  unfold packetIds; split
  · simp
  · split <;> simp

theorem placed_nodup (l : List (Nat × Nat)) (h : (l.map Prod.fst).Nodup) :
    (l.map (fun p => PacketId.placed p.1 p.2)).Nodup := by
  induction l with
  | nil => simp
  | cons a t ih =>
    simp only [List.map_cons, List.nodup_cons, List.mem_map] at h ⊢
    refine ⟨?_, ih h.2⟩
    rintro ⟨b, hb, e⟩
    injection e with e1 _
    exact h.1 ⟨b, hb, e1⟩

theorem nodup_map_of_inj {α β : Type} (f : α → β) (hf : ∀ a b, f a = f b → a = b) :
    ∀ l : List α, l.Nodup → (l.map f).Nodup
  | [], _ => by simp
  | a :: t, h => by
    simp only [List.map_cons, List.nodup_cons, List.mem_map] at h ⊢
    refine ⟨?_, nodup_map_of_inj f hf t h.2⟩
    rintro ⟨b, hb, e⟩
    exact h.1 (hf b a e ▸ hb)

/-- P1. -/
theorem packet_ids_distinct (cs : List Chunk) : (packetIds cs).Nodup := by
  unfold packetIds
  split
  · rename_i h
    have e : cs.map (fun c => PacketId.plain c.2) = (cs.map Prod.snd).map PacketId.plain := by
      simp [List.map_map]
    rw [e]
    exact nodup_map_of_inj _ (fun a b h => by injection h) _ h
  · split
    · rename_i _ hs
      have hn : cs.Nodup := by simp [sourcedOk] at hs; exact hs.2
      exact nodup_map_of_inj _ (fun a b h => by
        injection h with h1 h2; exact Prod.ext h1 h2) _ hn
    · apply placed_nodup
      rw [List.map_fst_zip (by simp)]
      exact List.nodup_range

/-- P2. -/
theorem packet_ids_keep_distinct_ids (cs : List Chunk) (h : (cs.map Prod.snd).Nodup) :
    packetIds cs = cs.map (fun c => .plain c.2) := by
  unfold packetIds; simp [h]

/-- P3. -/
theorem packet_ids_name_the_chunk (cs : List Chunk) (h : ¬ (cs.map Prod.snd).Nodup)
    (hs : sourcedOk cs = true) : packetIds cs = cs.map (fun c => .sourced c.1 c.2) := by
  unfold packetIds; simp [h, hs]

/-- Two interviews chunked separately: the old rule gave chunk 1 of each the same packet. -/
theorem old_ids_collide : ¬ (oldIds [(1, 1), (1, 2), (2, 1), (2, 2)]).Nodup := by decide

/-- The same two interviews coded in the other order: each chunk keeps its packet ID. -/
theorem order_kept :
    packetIds [(2, 1), (2, 2), (1, 1), (1, 2)] =
      [.sourced 2 1, .sourced 2 2, .sourced 1 1, .sourced 1 2] ∧
    packetIds [(1, 1), (1, 2), (2, 1), (2, 2)] =
      [.sourced 1 1, .sourced 1 2, .sourced 2 1, .sourced 2 2] := by decide

end AatModel.Packets
