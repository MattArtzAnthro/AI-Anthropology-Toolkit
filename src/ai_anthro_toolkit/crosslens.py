"""Cross-lens comparison of coding results.

Port of the v16 cross-lens mathematics (merge_multi_lens_results,
calculate_agreement_scores, identify_consensus_and_divergent,
CrossLensAnalyzer.identify_friction_points). Pure computation — no LLM calls.

Agreement compares all applied codes (deductive + inductive) across lenses,
the notebook's unified definition.
"""

import math

FRICTION_THRESHOLD = 0.3
FRICTION_TOP_N = 20


def _applied_codes(record: dict) -> set:
    """The set of codes a lens applied to a chunk (deductive + inductive)."""
    codes = set()
    for column in ("Deductive_Codes", "Inductive_Codes"):
        raw = record.get(column, "")
        if raw is not None and raw == raw and str(raw).strip():
            codes.update(c.strip() for c in str(raw).split(",") if c.strip())
    return codes


def _integrated_codes(record: dict) -> set:
    """The chunk's integrated code set (``All_Codes``, ``_IND``-suffixed)."""
    raw = record.get("All_Codes")
    if raw is not None and raw == raw and str(raw).strip():
        return set(c.strip() for c in str(raw).split(",") if c.strip())
    deductive = set()
    inductive = set()
    raw_ded = record.get("Deductive_Codes", "")
    if raw_ded is not None and raw_ded == raw_ded and str(raw_ded).strip():
        deductive.update(c.strip() for c in str(raw_ded).split(",") if c.strip())
    raw_ind = record.get("Inductive_Codes", "")
    if raw_ind is not None and raw_ind == raw_ind and str(raw_ind).strip():
        inductive.update(c.strip() + "_IND" for c in str(raw_ind).split(",") if c.strip())
    return deductive | inductive


def compare_lenses(results_by_lens: dict[str, list[dict]]) -> dict:
    """Compare coding results across analytical lenses.

    Args:
        results_by_lens: Mapping of lens name to that lens's coded records
            (the output of :func:`ai_anthro_toolkit.coding.code_chunks`),
            aligned by ``chunk_id``.

    Returns:
        A dict with:

        - ``lenses``: lens names in input order.
        - ``per_chunk_agreement``: chunk_id -> mean pairwise Jaccard over all
          applied codes when at least two lenses coded the chunk, else NaN.
        - ``mean_agreement``: mean of the non-NaN per-chunk scores (NaN when
          none).
        - ``agreement_matrix``: lens -> lens -> mean Jaccard across chunks
          with a non-empty code union (diagonal 1.0, rounded to 3 places).
        - ``friction_points``: up to 20 chunks with agreement below 0.3
          (NaN-safe), ascending, each with its per-lens code sets.
        - ``consensus_codes``: integrated codes found by every lens.
        - ``divergent_codes``: lens -> integrated codes unique to that lens.
        - ``partial_overlap``: integrated codes shared by some lenses but not
          all.
    """
    lens_names = list(results_by_lens.keys())

    # Per-lens, per-chunk applied-code sets (deductive + inductive).
    code_maps = {}
    all_chunks = set()
    for lens_name, records in results_by_lens.items():
        code_map = {}
        for record in records:
            chunk_id = str(record.get("chunk_id", ""))
            all_chunks.add(chunk_id)
            code_map[chunk_id] = _applied_codes(record)
        code_maps[lens_name] = code_map
    chunk_ids = sorted(all_chunks)

    # Per-chunk agreement: mean pairwise Jaccard when >= 2 lenses applied
    # codes; pairs with an empty union count as full agreement.
    per_chunk_agreement = {}
    for chunk_id in chunk_ids:
        per_lens = {name: code_maps[name].get(chunk_id, set()) for name in lens_names}
        active = [name for name, codes in per_lens.items() if codes]
        if len(active) >= 2:
            jaccard_scores = []
            for i in range(len(lens_names)):
                for j in range(i + 1, len(lens_names)):
                    a = per_lens[lens_names[i]]
                    b = per_lens[lens_names[j]]
                    union = a | b
                    jaccard_scores.append(len(a & b) / len(union) if union else 1.0)
            per_chunk_agreement[chunk_id] = sum(jaccard_scores) / len(jaccard_scores)
        else:
            per_chunk_agreement[chunk_id] = float("nan")

    valid_scores = [s for s in per_chunk_agreement.values() if not math.isnan(s)]
    mean_agreement = sum(valid_scores) / len(valid_scores) if valid_scores else float("nan")

    # Pairwise agreement matrix: mean Jaccard over chunks with a non-empty union.
    agreement_matrix = {name: {} for name in lens_names}
    for name in lens_names:
        agreement_matrix[name][name] = 1.0
    for i, lens_a in enumerate(lens_names):
        for j in range(i + 1, len(lens_names)):
            lens_b = lens_names[j]
            jaccard_sum = 0.0
            valid_chunks = 0
            for chunk_id in chunk_ids:
                codes_a = code_maps[lens_a].get(chunk_id, set())
                codes_b = code_maps[lens_b].get(chunk_id, set())
                union = codes_a | codes_b
                if union:
                    jaccard_sum += len(codes_a & codes_b) / len(union)
                    valid_chunks += 1
            avg_jaccard = round(jaccard_sum / valid_chunks, 3) if valid_chunks > 0 else 0
            agreement_matrix[lens_a][lens_b] = avg_jaccard
            agreement_matrix[lens_b][lens_a] = avg_jaccard

    # Friction points: chunks where lenses diverge most (agreement < 0.3).
    friction_points = []
    for chunk_id in chunk_ids:
        score = per_chunk_agreement[chunk_id]
        if not math.isnan(score) and score < FRICTION_THRESHOLD:
            friction_points.append({
                "chunk_id": chunk_id,
                "agreement": score,
                "codes_by_lens": {name: sorted(code_maps[name].get(chunk_id, set()))
                                  for name in lens_names},
            })
    friction_points.sort(key=lambda point: point["agreement"])
    friction_points = friction_points[:FRICTION_TOP_N]

    # Consensus / divergent / partial-overlap over integrated code sets.
    lens_codes = {}
    for lens_name, records in results_by_lens.items():
        codes = set()
        for record in records:
            codes |= _integrated_codes(record)
        lens_codes[lens_name] = codes

    consensus = set.intersection(*lens_codes.values()) if lens_codes else set()

    divergent = {}
    for lens_name in lens_names:
        if len(lens_names) > 1:
            others = set.union(*(lens_codes[name] for name in lens_names
                                 if name != lens_name))
        else:
            others = set()
        unique = lens_codes[lens_name] - others
        if unique:
            divergent[lens_name] = sorted(unique)

    all_codes = set.union(*lens_codes.values()) if lens_codes else set()
    partial = all_codes - consensus
    for unique in divergent.values():
        partial -= set(unique)

    return {
        "lenses": lens_names,
        "per_chunk_agreement": per_chunk_agreement,
        "mean_agreement": mean_agreement,
        "agreement_matrix": agreement_matrix,
        "friction_points": friction_points,
        "consensus_codes": sorted(consensus),
        "divergent_codes": divergent,
        "partial_overlap": sorted(partial),
    }
