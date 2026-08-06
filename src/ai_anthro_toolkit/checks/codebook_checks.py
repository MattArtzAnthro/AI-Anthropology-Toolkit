"""Standing checks over a codebook.

The two mirror checks here are already computed once, at build time, inside
``refine_codebook`` Step 7. What is added is standing re-runnability over a
codebook that arrived by another route, so the predicates are shared rather
than written a second time.

The distinctness check is deliberately not a class-level invariant. A
class-level invariant may assert formal properties of an artifact and may
never assert a methodological commitment about its use, and mutual
exclusivity of codes is a commitment that grounded theory and several
interpretive traditions decline. It runs only once the researcher has said
the commitment is theirs.
"""

from __future__ import annotations

import copy

from .registry import (CANNOT_TELL, CLASS_CODEBOOK, FIRED, MARK_MIRROR,
                       MARK_STANCE, NOT_APPLICABLE, OK, Check, CheckResult,
                       records_of, register)

DISTINCTNESS_THRESHOLD = 0.85

_EXAMPLE_FIELDS = ("example_1", "example_2", "example_3")


def _label(record, index):
    return record.get("code_label") or record.get("label") or f"code {index}"


def _carry(count):
    return "code has" if count == 1 else "codes have"


# ── Predicates ──────────────────────────────────────────────────────────────

def definition_present(artifact, **_context) -> CheckResult:
    missing = [
        _label(record, i)
        for i, record in enumerate(records_of(artifact))
        if not str(record.get("definition", "")).strip()
    ]
    total = len(records_of(artifact))
    if missing:
        return CheckResult(
            FIRED,
            f"{len(missing)} of {total} {_carry(len(missing))} no definition: "
            f"{', '.join(missing)}.",
            detail=tuple(missing),
        )
    return CheckResult(OK, f"Every one of {total} codes carries a definition.")


def example_present(artifact, **_context) -> CheckResult:
    missing = []
    records = records_of(artifact)
    for i, record in enumerate(records):
        examples = [str(record.get(f, "")).strip() for f in _EXAMPLE_FIELDS]
        if not any(examples) and not record.get("examples"):
            missing.append(_label(record, i))
    if missing:
        return CheckResult(
            FIRED,
            f"{len(missing)} of {len(records)} {_carry(len(missing))} no "
            f"example: {', '.join(missing)}.",
            detail=tuple(missing),
        )
    return CheckResult(
        OK, f"Every one of {len(records)} codes carries at least one example.")


def distinctness(artifact, *, expect_distinct_codes=None, embedder=None,
                 **_context) -> CheckResult:
    if expect_distinct_codes is None:
        return CheckResult(
            CANNOT_TELL,
            "I cannot run this one yet. It asks whether any two codes are "
            "close enough to be the same code, which only matters if you "
            "hold codes to be mutually exclusive. Some traditions do and "
            "some deliberately do not, so it is yours to say rather than "
            "mine to assume.",
        )
    if not expect_distinct_codes:
        return CheckResult(
            NOT_APPLICABLE,
            "Skipped: you hold overlapping codes deliberately, so closeness "
            "between two of them is not a finding.",
        )
    if embedder is None:
        return CheckResult(
            CANNOT_TELL,
            "I cannot tell. Measuring closeness between definitions needs "
            "the sentence-transformers model, which is not installed here "
            "(it ships in the optional 'chunking' extra). Treat this as "
            "unrun rather than as nothing found.",
        )

    records = records_of(artifact)
    definitions = [str(r.get("definition", "")) for r in records]
    if len(definitions) < 2:
        return CheckResult(
            OK, "Fewer than two codes, so there is no pair to compare.")

    import numpy as np

    vectors = np.asarray(embedder(definitions), dtype=float)
    close = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            a, b = vectors[i], vectors[j]
            denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
            if denominator == 0.0:
                continue
            similarity = float(np.dot(a, b) / denominator)
            if similarity >= DISTINCTNESS_THRESHOLD:
                close.append((_label(records[i], i), _label(records[j], j),
                              round(similarity, 3)))

    if close:
        pairs = "; ".join(f"{a} and {b} ({s})" for a, b, s in close)
        return CheckResult(
            FIRED,
            f"These read as the same code to me: {pairs}. You told me codes "
            f"should be mutually exclusive here, so is that separation one "
            f"you still want, or were these meant to be one code?",
            detail=tuple(close),
        )
    return CheckResult(
        OK, "No two definitions read as the same code at the threshold used.")


# ── Mutators ────────────────────────────────────────────────────────────────

def _break_definition(artifact):
    broken = copy.deepcopy(artifact)
    records_of(broken)[0]["definition"] = "   "
    return broken


def _break_example(artifact):
    broken = copy.deepcopy(artifact)
    record = records_of(broken)[0]
    for field in _EXAMPLE_FIELDS:
        record[field] = ""
    record.pop("examples", None)
    return broken


def _break_distinctness(artifact):
    broken = copy.deepcopy(artifact)
    records = records_of(broken)
    records[1]["definition"] = records[0]["definition"]
    return broken


register(
    Check(
        name="codebook.definition-present",
        artifact_class=CLASS_CODEBOOK,
        mark=MARK_MIRROR,
        summary="Every code carries a definition",
        predicate=definition_present,
        break_artifact=_break_definition,
    ),
    Check(
        name="codebook.example-present",
        artifact_class=CLASS_CODEBOOK,
        mark=MARK_MIRROR,
        summary="Every code carries at least one example",
        predicate=example_present,
        break_artifact=_break_example,
    ),
    Check(
        name="codebook.distinctness",
        artifact_class=CLASS_CODEBOOK,
        mark=MARK_STANCE,
        summary="No two codes read as the same code",
        predicate=distinctness,
        break_artifact=_break_distinctness,
        hypothesis=(
            "That codes are mutually exclusive. Researchers routinely assume "
            "this without stating it, and traditions that deliberately hold "
            "overlapping codes are exactly who should not be asked."
        ),
    ),
)
