/-!
# Packet IDs: one per chunk, all different

Models `server._packet_ids`. A chunk's ID is its chunk_id, or its position when it has none (a
number here). `chunk_transcript` numbers each transcript's chunks from 1, so the chunks of
several interviews share IDs. Before, the packet ID was the chunk's ID: two chunks shared one
packet, one answer coded both, and the job never completed (`Submit.old_duplicate_ids_never_complete`).

Specification:
* P1: every chunk gets a packet, and no two packets share an ID.
* P2: when the chunks' IDs are already all different, the packet IDs are those IDs (jobs and
  answers keep the IDs a caller knows).
-/
namespace AatModel.Packets

/-- A packet ID: the chunk's ID, prefixed with its position when IDs repeat. -/
inductive PacketId | plain (id : Nat) | placed (pos id : Nat)
  deriving DecidableEq, Repr

def oldIds (ids : List Nat) : List PacketId := ids.map .plain

def packetIds (ids : List Nat) : List PacketId :=
  if ids.Nodup then ids.map .plain
  else ((List.range ids.length).zip ids).map (fun p => .placed p.1 p.2)

theorem packet_ids_one_per_chunk (ids : List Nat) : (packetIds ids).length = ids.length := by
  unfold packetIds; split <;> simp

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

/-- P1. -/
theorem packet_ids_distinct (ids : List Nat) : (packetIds ids).Nodup := by
  unfold packetIds
  split
  · rename_i h
    induction ids with
    | nil => simp
    | cons a t ih =>
      simp only [List.nodup_cons, List.map_cons, List.mem_map] at h ⊢
      refine ⟨?_, ih h.2⟩
      rintro ⟨b, hb, e⟩; cases e; exact h.1 hb
  · apply placed_nodup
    rw [List.map_fst_zip (by simp)]
    exact List.nodup_range

/-- P2. -/
theorem packet_ids_keep_distinct_ids (ids : List Nat) (h : ids.Nodup) :
    packetIds ids = ids.map .plain := by
  unfold packetIds; simp [h]

/-- Two interviews chunked separately: the old rule gave chunk 1 of each the same packet. -/
theorem old_ids_collide : ¬ (oldIds [1, 2, 1, 2]).Nodup := by decide

end AatModel.Packets
