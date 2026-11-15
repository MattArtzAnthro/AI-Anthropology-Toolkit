"""The cards a desk shows: one per code for a codebook desk, one per disagreement for a
rulings desk, and the checksum that ties decisions to the cards they were made on.

A card is a plain dict, stored with the desk and never edited after the desk is built.

- Codebook card: ``card_id`` (``code-01``, ...), ``code_label``, ``definition``,
  ``inclusion``, ``exclusion``, ``cases`` (``case_id``, ``text``, ``source``, and ``kind``,
  which is ``typical`` or ``borderline``).
- Rulings card: ``card_id`` (``chunk-<chunk_id>``), ``chunk_id``, ``text``, ``source``,
  ``coder_a`` and ``coder_b`` (each coder's deductive codes, in codebook order),
  ``entries`` (label to definition for those codes), and ``proposal``
  (``{codes, rationale}``, or None).

Every builder refuses input it cannot card faithfully, naming what is wrong, rather than
dropping it.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from ai_anthro_toolkit.coding import normalize_codebook

__all__ = ["checksum", "codebook_cards", "rulings_cards"]

Card = dict[str, Any]
KINDS = ("typical", "borderline")


def _codebook(records: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, str]]:
    """Label to {definition, inclusion, exclusion}, in codebook order."""
    entries: dict[str, dict[str, str]] = {}
    for record in records:
        label = str(record.get("code_label") or "").strip()
        if not label:
            raise ValueError("A codebook record has no code_label.")
        if label in entries:
            raise ValueError(f"The codebook lists {label!r} more than once.")
        row = normalize_codebook([{**record, "code_label": label, "definition": record.get("definition") or ""}])
        entry = row[label]
        entries[label] = {"definition": str(entry["definition"]), "inclusion": entry["inclusion"], "exclusion": entry["exclusion"]}
    return entries


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def codebook_cards(codebook: Sequence[Mapping[str, Any]], cases: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[Card]:
    """One card per code, in codebook order, each with the cases it would take (R2.1).

    ``cases`` maps a code label to its cases: ``text`` and ``kind`` (``typical`` or
    ``borderline``) required, ``case_id`` and ``source`` optional. Refuses, naming every
    one, codes with no case (R1.2), and refuses cases for a code the codebook lacks.
    """
    entries = _codebook(codebook)
    unknown = [label for label in cases if label not in entries]
    if unknown:
        raise ValueError(f"Cases are given for {', '.join(map(repr, unknown))}, which is not in the codebook.")
    caseless = [label for label in entries if not cases.get(label)]
    if caseless:
        raise ValueError(f"Can't build the desk. These codes have no case: {', '.join(caseless)}.")
    width = max(2, len(str(len(entries))))
    built = []
    for n, (label, entry) in enumerate(entries.items(), start=1):
        card_id = f"code-{n:0{width}d}"
        card_cases = []
        for m, case in enumerate(cases[label], start=1):
            if case.get("kind") not in KINDS:
                raise ValueError(f"A case for {label} is marked {case.get('kind')!r}; mark each case typical or borderline.")
            text = _text(case.get("text"))
            if not text:
                raise ValueError(f"A case for {label} has no text.")
            card_cases.append({
                "case_id": _text(case.get("case_id")) or f"{card_id}-case-{m}",
                "text": text,
                "source": _text(case.get("source")),
                "kind": case["kind"],
            })
        built.append({"card_id": card_id, "code_label": label, **entry, "cases": card_cases})
    return built


def _codes(raw: Any) -> set[str]:
    """A coding record's comma-separated code field as a set of labels."""
    if raw is None or raw != raw:  # None or NaN
        return set()
    return {code.strip() for code in str(raw).split(",") if code.strip()}


def _chunks(job: Sequence[Mapping[str, Any]], name: str) -> dict[str, Mapping[str, Any]]:
    """A coding job's records by chunk_id, refusing records it cannot place."""
    unplaced = sum(1 for record in job if not _text(record.get("chunk_id")))
    if unplaced:
        noun = "record" if unplaced == 1 else "records"
        raise ValueError(f"{unplaced} {noun} in the {name} coding job {'has' if unplaced == 1 else 'have'} no chunk_id.")
    chunks: dict[str, Mapping[str, Any]] = {}
    for record in job:
        chunk_id = _text(record["chunk_id"])
        if chunk_id in chunks:
            raise ValueError(f"chunk {chunk_id} appears more than once in the {name} coding job.")
        chunks[chunk_id] = record
    return chunks


def _in_order(labels: set[str], entries: Mapping[str, Any]) -> list[str]:
    return [label for label in entries if label in labels]


def _proposal(chunk_id: str, proposal: Mapping[str, Any], entries: Mapping[str, Any]) -> dict[str, Any]:
    codes = proposal.get("codes")
    if not isinstance(codes, list) or not all(isinstance(code, str) for code in codes):
        raise ValueError(f"The proposal for chunk {chunk_id} must give a list of codes (empty when no code applies).")
    unknown = [code for code in codes if code not in entries]
    if unknown:
        raise ValueError(f"The proposal for chunk {chunk_id} names {', '.join(map(repr, unknown))}, which is not in the codebook.")
    return {"codes": _in_order(set(codes), entries), "rationale": _text(proposal.get("rationale"))}


def rulings_cards(
    job_a: Sequence[Mapping[str, Any]],
    job_b: Sequence[Mapping[str, Any]],
    codebook: Sequence[Mapping[str, Any]],
    proposals: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[Card]:
    """One card per chunk whose two sets of deductive codes differ, in the first job's
    chunk order (R1.3), with each coder's codes and their codebook entries (R3.1).

    ``proposals`` maps a chunk_id to ``{codes, rationale}``; an empty ``codes`` list
    proposes that no code applies. Refuses jobs that coded different chunks or different
    text, records without a chunk_id or coded twice, codes outside ``codebook``, and
    proposals for chunks without a disagreement.
    """
    entries = _codebook(codebook)
    first, second = _chunks(job_a, "first"), _chunks(job_b, "second")
    if first.keys() != second.keys():
        only_first = [c for c in first if c not in second]
        only_second = [c for c in second if c not in first]
        parts = [f"{', '.join(only)} only in the {name}" for only, name in ((only_first, "first"), (only_second, "second")) if only]
        raise ValueError(f"The two coding jobs did not code the same chunks: {'; '.join(parts)}.")
    proposals = {str(k): v for k, v in (proposals or {}).items()}
    built = []
    for chunk_id, record_a in first.items():
        record_b = second[chunk_id]
        text_a, text_b = _text(record_a.get("text")), _text(record_b.get("text"))
        if text_a != text_b:
            raise ValueError(f"chunk {chunk_id} has different text in the two coding jobs; they did not code the same data.")
        codes_a, codes_b = _codes(record_a.get("Deductive_Codes")), _codes(record_b.get("Deductive_Codes"))
        for codes, name in ((codes_a, "first"), (codes_b, "second")):
            for label in sorted(codes - entries.keys()):
                raise ValueError(f"{label!r}, which chunk {chunk_id} carries in the {name} coding job, is not in the codebook.")
        if codes_a == codes_b:
            continue
        proposal = proposals.get(chunk_id)
        built.append({
            "card_id": f"chunk-{chunk_id}",
            "chunk_id": chunk_id,
            "text": text_a,
            "source": _text(record_a.get("source") or record_a.get("source_file")),
            "coder_a": _in_order(codes_a, entries),
            "coder_b": _in_order(codes_b, entries),
            "entries": {label: entries[label]["definition"] for label in _in_order(codes_a | codes_b, entries)},
            "proposal": None if proposal is None else _proposal(chunk_id, proposal, entries),
        })
    carded = {card["chunk_id"] for card in built}
    for chunk_id in proposals:
        if chunk_id not in carded:
            raise ValueError(f"The proposal for chunk {chunk_id} is for a chunk with no disagreement.")
    return built


def checksum(cards: Sequence[Mapping[str, Any]]) -> str:
    """The first 16 hex digits of SHA-256 over the cards' canonical JSON (R1.7)."""
    body = json.dumps(list(cards), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
