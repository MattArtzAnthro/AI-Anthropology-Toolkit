"""Cross-lens comparison of coding results.

Pure computation — no LLM calls. Compares how analytical lenses coded the
same chunks and returns the comparison for the researcher to adjudicate.
Friction points and convergence points are presented to the researcher;
this module measures divergence in labeling, and whether a labeling
difference is real interpretive daylight or two vocabularies describing one
reading is a judgment that stays with the researcher — the payloads exist
to equip that call, never to make it.

Semantics (ratified 2026-08-12):

- Agreement is mean pairwise Jaccard over **deductive** code labels.
  Inductive discoveries are per-lens: two lenses independently discovering
  the same surface name is a fact about naming, not vocabulary-governed
  agreement, so inductive codes never enter agreement scores or vocabulary
  tiers. They are reported per lens in ``inductive_codes_by_lens`` and shown
  ``_IND``-suffixed in point payloads.
- A record that is present with no codes is a reading ("nothing applies"):
  it scores 0 against a non-empty set and 1.0 against another empty set.
  An absent record means the lens was never asked, and that chunk's pairs
  involving the lens are excluded rather than scored; per-lens ``coverage``
  and the ``chunks`` compared/uncompared counts keep the exclusions visible.
- ``consensus_codes`` requires co-location: every lens applied the label to
  at least one common chunk, with the chunks recorded in
  ``consensus_co_applied_chunks``. A label every lens used but never on the
  same chunk is ``shared_vocabulary_codes``, not consensus.
- Nothing is truncated silently: ``friction_total`` and
  ``convergence_total`` report full counts, ``params`` echoes the
  thresholds, and ties order lexicographically by ``chunk_id``.
- The vocabulary regime is reported, never guessed: with per-lens codebooks
  supplied it is ``shared`` or ``divergent`` by content checksum; without
  them it is ``unknown`` — identical label sets are not evidence of a
  shared codebook.
"""

import hashlib
import json
import math

FRICTION_THRESHOLD = 0.3
FRICTION_TOP_N = 20
TEXT_CAP = 500


def codebook_checksum(records: list[dict]) -> str:
    """Order-insensitive content checksum over (label, definition) pairs.

    Field order, extra columns, and record order do not change the checksum;
    changing, adding, or removing a code does. The MCP server uses this same
    checksum to bind coding jobs to ratified codebooks, which is what lets
    the comparison state which vocabulary regime produced it.
    """
    canon = sorted(
        (str(r.get("code_label") or r.get("label") or ""),
         str(r.get("definition") or ""))
        for r in records
    )
    return hashlib.sha256(
        json.dumps(canon, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]


def _split_codes(raw) -> set:
    """Parse a comma-separated code field (None/NaN/blank-safe)."""
    if raw is None or raw != raw or not str(raw).strip():
        return set()
    return {c.strip() for c in str(raw).split(",") if c.strip()}


def _cap_text(text: str) -> tuple[str, bool]:
    if len(text) > TEXT_CAP:
        return text[:TEXT_CAP], True
    return text, False


def _ingest(results_by_lens: dict[str, list[dict]]):
    """Build per-lens maps, applying the missing/duplicate chunk_id rules.

    Returns (ded_maps, ind_maps, texts, warnings) where ded_maps/ind_maps
    map lens -> {chunk_id: code set} for chunks whose record carries an id,
    and texts maps chunk_id -> first non-blank text seen.
    """
    ded_maps: dict[str, dict] = {}
    ind_maps: dict[str, dict] = {}
    texts: dict[str, str] = {}
    warnings: list[dict] = []
    mismatched: set = set()

    for lens, records in results_by_lens.items():
        ded_map: dict[str, set] = {}
        ind_map: dict[str, set] = {}
        missing = 0
        duplicates = []
        for record in records:
            raw_id = record.get("chunk_id")
            chunk_id = "" if raw_id is None else str(raw_id).strip()
            if not chunk_id:
                missing += 1
                continue
            if chunk_id in ded_map:
                duplicates.append(chunk_id)
            # C2: last record wins.
            ded_map[chunk_id] = _split_codes(record.get("Deductive_Codes"))
            ind_map[chunk_id] = _split_codes(record.get("Inductive_Codes"))

            text = record.get("text")
            text = "" if text is None or text != text else str(text).strip()
            if text:
                seen = texts.get(chunk_id, "")
                if seen and text != seen and chunk_id not in mismatched:
                    mismatched.add(chunk_id)
                    warnings.append({
                        "type": "text_mismatch", "chunk_id": chunk_id,
                        "detail": "lenses carry different text for this "
                                  "chunk_id; they may not have coded the "
                                  "same data"})
                elif not seen:
                    texts[chunk_id] = text
        if missing:
            warnings.append({
                "type": "missing_chunk_id", "lens": lens, "count": missing,
                "detail": "records without a chunk_id are excluded from "
                          "the comparison"})
        if duplicates:
            warnings.append({
                "type": "duplicate_chunk_id", "lens": lens,
                "chunk_ids": sorted(set(duplicates)),
                "detail": "the last record for each duplicated chunk_id "
                          "governs"})
        ded_maps[lens] = ded_map
        ind_maps[lens] = ind_map

    return ded_maps, ind_maps, texts, warnings


def _point(chunk_id: str, score: float, lens_names: list[str],
           ded_maps: dict, ind_maps: dict, texts: dict) -> dict:
    """Assemble one friction/convergence payload for the adjudicator."""
    codes_by_lens = {}
    for lens in lens_names:
        if chunk_id not in ded_maps[lens]:
            continue  # the lens was never asked about this chunk
        codes = sorted(ded_maps[lens][chunk_id])
        codes += sorted(c + "_IND" for c in ind_maps[lens].get(chunk_id, set()))
        codes_by_lens[lens] = codes
    text, truncated = _cap_text(texts.get(chunk_id, ""))
    return {"chunk_id": chunk_id, "agreement": score,
            "codes_by_lens": codes_by_lens,
            "text": text, "text_truncated": truncated}


def compare_lenses(results_by_lens: dict[str, list[dict]], *,
                   codebooks_by_lens: dict[str, list[dict]] | None = None,
                   friction_threshold: float = FRICTION_THRESHOLD,
                   top_n: int = FRICTION_TOP_N) -> dict:
    """Compare coding results across analytical lenses.

    Args:
        results_by_lens: Mapping of lens name to that lens's coded records
            (the output of :func:`ai_anthro_toolkit.coding.code_chunks`),
            aligned by ``chunk_id``.
        codebooks_by_lens: Optional mapping of lens name to the codebook
            records that governed its coding pass. Supplying it resolves
            code definitions into the output and settles the vocabulary
            regime; without it the regime is reported as ``unknown``.
        friction_threshold: Per-chunk agreement below this counts as
            friction (default 0.3). The threshold selects attention, never
            existence: ``friction_total`` reports the full count regardless.
        top_n: Maximum friction and convergence points returned. Ties order
            lexicographically by ``chunk_id`` (C5).

    Returns a dict with:

    - ``lenses``: lens names in input order.
    - ``per_chunk_agreement``: chunk_id -> mean pairwise Jaccard over
      deductive codes across lenses holding a record for the chunk; NaN
      when fewer than two lenses hold one. An empty-vs-empty pair scores
      1.0 (mutual "nothing applies" is agreement).
    - ``mean_agreement``: mean of the non-NaN scores (NaN when none).
    - ``coverage`` / ``chunks``: per-lens record counts and the
      total/compared/uncompared chunk universe — silence is visible,
      never scored.
    - ``agreement_matrix``: pairwise mean Jaccard over chunks both lenses
      hold with a non-empty union (diagonal 1.0, rounded to 3 places).
    - ``friction_points`` / ``friction_total``: lowest-agreement chunks
      (ascending), each carrying per-lens codes (inductive ``_IND``-marked),
      the chunk text (capped at 500 chars, flagged), for the researcher to
      adjudicate. Presented, never resolved here.
    - ``convergence_points`` / ``convergence_total``: highest-agreement
      chunks (descending) among those where at least two lenses applied
      codes at or above the friction threshold — friction and convergence
      partition attention, no chunk appears in both. Same payload plus
      ``code_count``. Agreement gets the same scrutiny divergence gets:
      an easy consensus may be two meanings under one label.
    - ``consensus_codes`` / ``consensus_co_applied_chunks``: labels every
      lens applied to at least one common chunk, with those chunks.
    - ``shared_vocabulary_codes``: labels every lens used, never co-applied.
    - ``partial_overlap``: labels used by some but not all lenses.
    - ``divergent_codes``: lens -> labels only that lens used.
    - ``inductive_codes_by_lens``: lens -> {discovered code: applications}.
    - ``code_definitions``: lens -> {label: definition} for surfaced labels,
      when codebooks were supplied.
    - ``vocabulary``: ``regime`` (shared | divergent | unknown) and per-lens
      codebook ``checksums`` (None without codebooks).
    - ``params``: the thresholds this comparison ran under.
    - ``warnings``: structured data-integrity findings (missing or
      duplicate chunk_ids, text mismatches).
    """
    lens_names = list(results_by_lens.keys())
    ded_maps, ind_maps, texts, warnings = _ingest(results_by_lens)

    chunk_ids = sorted(set().union(*(ded_maps[l].keys() for l in lens_names))
                       if lens_names else set())

    # Per-chunk agreement over lenses that hold a record for the chunk.
    per_chunk_agreement: dict[str, float] = {}
    for chunk_id in chunk_ids:
        present = [l for l in lens_names if chunk_id in ded_maps[l]]
        if len(present) < 2:
            per_chunk_agreement[chunk_id] = float("nan")
            continue
        scores = []
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                a = ded_maps[present[i]][chunk_id]
                b = ded_maps[present[j]][chunk_id]
                union = a | b
                scores.append(len(a & b) / len(union) if union else 1.0)
        per_chunk_agreement[chunk_id] = sum(scores) / len(scores)

    valid = [s for s in per_chunk_agreement.values() if not math.isnan(s)]
    mean_agreement = sum(valid) / len(valid) if valid else float("nan")

    coverage = {l: len(ded_maps[l]) for l in lens_names}
    chunks_meta = {"total": len(chunk_ids), "compared": len(valid),
                   "uncompared": len(chunk_ids) - len(valid)}

    # Pairwise matrix over chunks both lenses hold, non-empty union.
    agreement_matrix: dict[str, dict] = {l: {l: 1.0} for l in lens_names}
    for i, lens_a in enumerate(lens_names):
        for j in range(i + 1, len(lens_names)):
            lens_b = lens_names[j]
            total, count = 0.0, 0
            for chunk_id in chunk_ids:
                if chunk_id not in ded_maps[lens_a] or \
                        chunk_id not in ded_maps[lens_b]:
                    continue
                a = ded_maps[lens_a][chunk_id]
                b = ded_maps[lens_b][chunk_id]
                union = a | b
                if union:
                    total += len(a & b) / len(union)
                    count += 1
            score = round(total / count, 3) if count else 0
            agreement_matrix[lens_a][lens_b] = score
            agreement_matrix[lens_b][lens_a] = score

    # Friction: lowest agreement, ascending; disclosed truncation.
    friction_ids = [c for c in chunk_ids
                    if not math.isnan(per_chunk_agreement[c])
                    and per_chunk_agreement[c] < friction_threshold]
    friction_ids.sort(key=lambda c: (per_chunk_agreement[c], c))
    friction_points = [_point(c, per_chunk_agreement[c], lens_names,
                              ded_maps, ind_maps, texts)
                       for c in friction_ids[:top_n]]

    # Convergence: highest agreement among chunks at least two lenses
    # coded, at or above the friction threshold — friction and convergence
    # partition attention at the same disclosed parameter, so no chunk is
    # ever surfaced as both.
    convergence_ids = [
        c for c in chunk_ids
        if not math.isnan(per_chunk_agreement[c])
        and per_chunk_agreement[c] >= friction_threshold
        and sum(1 for l in lens_names if ded_maps[l].get(c)) >= 2
    ]
    convergence_ids.sort(key=lambda c: (-per_chunk_agreement[c], c))
    convergence_points = []
    for c in convergence_ids[:top_n]:
        point = _point(c, per_chunk_agreement[c], lens_names,
                       ded_maps, ind_maps, texts)
        point["code_count"] = len(set().union(
            *(ded_maps[l].get(c, set()) for l in lens_names)))
        convergence_points.append(point)

    # Vocabulary tiers over deductive labels, consensus requiring
    # co-location: a label is consensus only where every lens applied it
    # to at least one common chunk.
    lens_vocab = {l: set().union(*ded_maps[l].values())
                  if ded_maps[l] else set() for l in lens_names}
    all_labels = set().union(*lens_vocab.values()) if lens_vocab else set()
    in_all = (set.intersection(*lens_vocab.values())
              if lens_names else set())

    consensus, co_applied = [], {}
    for label in sorted(in_all):
        common = [c for c in chunk_ids
                  if all(label in ded_maps[l].get(c, set())
                         for l in lens_names)]
        if common:
            consensus.append(label)
            co_applied[label] = common
    shared_vocabulary = sorted(in_all - set(consensus))

    divergent: dict[str, list] = {}
    if len(lens_names) > 1:
        for lens in lens_names:
            others = set().union(*(lens_vocab[o] for o in lens_names
                                   if o != lens))
            unique = lens_vocab[lens] - others
            if unique:
                divergent[lens] = sorted(unique)
    divergent_all = set().union(*divergent.values()) if divergent else set()
    partial = sorted(all_labels - in_all - divergent_all)

    inductive_by_lens = {}
    for lens in lens_names:
        counts: dict[str, int] = {}
        for codes in ind_maps[lens].values():
            for code in codes:
                counts[code] = counts.get(code, 0) + 1
        inductive_by_lens[lens] = counts

    # Definitions for surfaced labels, and the vocabulary regime — stated
    # when codebooks are supplied, "unknown" otherwise, never inferred
    # from label overlap.
    surfaced: dict[str, set] = {l: set() for l in lens_names}
    for point in friction_points + convergence_points:
        for lens, codes in point["codes_by_lens"].items():
            surfaced[lens].update(c for c in codes if not c.endswith("_IND"))

    code_definitions: dict[str, dict] = {}
    checksums = None
    regime = "unknown"
    if codebooks_by_lens:
        checksums = {lens: codebook_checksum(list(records))
                     for lens, records in codebooks_by_lens.items()}
        known = [checksums.get(l) for l in lens_names if l in checksums]
        if known and len(known) == len(lens_names):
            regime = "shared" if len(set(known)) == 1 else "divergent"
        for lens, records in codebooks_by_lens.items():
            defs = {str(r.get("code_label") or r.get("label") or ""):
                    str(r.get("definition") or "") for r in records}
            code_definitions[lens] = {
                label: defs[label]
                for label in sorted(surfaced.get(lens, set()))
                if label in defs}

    return {
        "lenses": lens_names,
        "per_chunk_agreement": per_chunk_agreement,
        "mean_agreement": mean_agreement,
        "coverage": coverage,
        "chunks": chunks_meta,
        "agreement_matrix": agreement_matrix,
        "friction_points": friction_points,
        "friction_total": len(friction_ids),
        "convergence_points": convergence_points,
        "convergence_total": len(convergence_ids),
        "consensus_codes": consensus,
        "consensus_co_applied_chunks": co_applied,
        "shared_vocabulary_codes": shared_vocabulary,
        "divergent_codes": divergent,
        "partial_overlap": partial,
        "inductive_codes_by_lens": inductive_by_lens,
        "code_definitions": code_definitions,
        "vocabulary": {"regime": regime, "checksums": checksums},
        "params": {"friction_threshold": friction_threshold, "top_n": top_n},
        "warnings": warnings,
    }
