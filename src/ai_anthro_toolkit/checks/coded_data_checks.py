"""Standing checks over a coded dataset.

``coding.py`` composes the unified code column as ``deductive + [c + "_IND"
for c in inductive]``. Inductive codes are therefore absent from the
codebook by construction, and a resolve check that does not know this
reports failure on every hybrid and inductive run. That is handled here by
splitting the question in two rather than by special-casing it: codes that
should resolve are checked as a mirror, and inductive codes that never made
it back into the codebook are surfaced separately, where they are genuinely
interesting.

Every check here needs to know which codebook the data was coded against.
Where the artifact carries no provenance stanza and no codebook is supplied,
the answer is "cannot tell" and never a failure: the datasets these checks
exist for are exactly the ones that arrived by other routes, and firing on
all of them is how a gate becomes a form.
"""

from __future__ import annotations

import copy

from .registry import (CANNOT_TELL, CLASS_CODED, FIRED, MARK_MIRROR,
                       MARK_SURPRISE, OK, Check, CheckResult,
                       codebook_checksum, records_of, register, stanza_of)

_INDUCTIVE_SUFFIX = "_IND"

_NO_CODEBOOK = (
    "I cannot tell, because this dataset does not say which codebook it was "
    "coded against and none was to hand. That is not a fault in the data; "
    "it is what happens when an artifact arrives without provenance."
)


def _split(value) -> list:
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def _known_labels(artifact, codebook=None) -> list | None:
    if codebook is not None:
        labels = [r.get("code_label") or r.get("label")
                  for r in records_of(codebook)]
        return [label for label in labels if label]
    stanza = stanza_of(artifact)
    if stanza and stanza.get("codebook_labels"):
        return list(stanza["codebook_labels"])
    return None


def _applied(artifact) -> tuple[list, list]:
    """Return (deductive, inductive) code labels applied across the dataset."""
    deductive, inductive = [], []
    for record in records_of(artifact):
        for code in _split(record.get("Deductive_Codes")):
            if code not in deductive:
                deductive.append(code)
        for code in _split(record.get("Inductive_Codes")):
            if code not in inductive:
                inductive.append(code)
        for code in _split(record.get("All_Codes")):
            if code.endswith(_INDUCTIVE_SUFFIX):
                stripped = code[: -len(_INDUCTIVE_SUFFIX)]
                if stripped and stripped not in inductive:
                    inductive.append(stripped)
            elif code not in deductive:
                deductive.append(code)
    return deductive, inductive


# ── Predicates ──────────────────────────────────────────────────────────────

def codes_resolve(artifact, *, codebook=None, **_context) -> CheckResult:
    labels = _known_labels(artifact, codebook)
    if labels is None:
        return CheckResult(CANNOT_TELL, _NO_CODEBOOK)

    deductive, _ = _applied(artifact)
    unknown = [code for code in deductive if code not in labels]
    if unknown:
        return CheckResult(
            FIRED,
            f"{len(unknown)} applied code(s) are not in the codebook: "
            f"{', '.join(unknown)}. Inductive codes are excluded from this "
            f"count, so these are codes the deductive pass applied without "
            f"having.",
            detail=tuple(unknown),
        )
    return CheckResult(
        OK,
        f"All {len(deductive)} deductively applied code(s) resolve to the "
        f"codebook.",
    )


def inductive_unfolded(artifact, *, codebook=None, **_context) -> CheckResult:
    labels = _known_labels(artifact, codebook)
    if labels is None:
        return CheckResult(CANNOT_TELL, _NO_CODEBOOK)

    _, inductive = _applied(artifact)
    unfolded = [code for code in inductive if code not in labels]
    if unfolded:
        return CheckResult(
            FIRED,
            f"{len(unfolded)} code(s) were discovered during coding and never "
            f"entered the codebook: {', '.join(unfolded)}. Did you mean to "
            f"fold them back in, or are they meant to stay beside it?",
            detail=tuple(unfolded),
        )
    return CheckResult(
        OK, "Every inductively discovered code is also in the codebook.")


def unused_codes(artifact, *, codebook=None, **_context) -> CheckResult:
    labels = _known_labels(artifact, codebook)
    if labels is None:
        return CheckResult(CANNOT_TELL, _NO_CODEBOOK)

    deductive, inductive = _applied(artifact)
    applied = set(deductive) | set(inductive)
    unused = [label for label in labels if label not in applied]
    if unused:
        return CheckResult(
            FIRED,
            f"{len(unused)} code(s) in the codebook were never applied: "
            f"{', '.join(unused)}. Should every code have earned its place "
            f"in this data, or were some carried for a later pass?",
            detail=tuple(unused),
        )
    return CheckResult(
        OK, f"Each of the {len(labels)} codes in the codebook was applied at "
            f"least once.")


def codebook_provenance(artifact, *, codebook=None, **_context) -> CheckResult:
    stanza = stanza_of(artifact)
    if not stanza:
        return CheckResult(
            CANNOT_TELL,
            "I cannot tell whether the codebook moved under this coding, "
            "because the dataset does not record which codebook it was "
            "coded against. Treat this as unrun rather than as settled.",
        )

    recorded = stanza.get("codebook_checksum")
    labels = stanza.get("codebook_labels")
    if not recorded or not labels:
        return CheckResult(
            CANNOT_TELL,
            "The dataset carries a provenance stanza but not enough of one "
            "to check the codebook against.",
        )

    if codebook is not None:
        actual_labels = [r.get("code_label") or r.get("label")
                         for r in records_of(codebook)]
        actual = codebook_checksum([l for l in actual_labels if l])
        source = "the codebook you gave me"
    else:
        actual = codebook_checksum(labels)
        source = "the label set recorded alongside it"

    if actual != recorded:
        return CheckResult(
            FIRED,
            f"The codebook this dataset names does not match {source}. "
            f"Something moved between coding and now. Which of the two is "
            f"the one you meant to code against?",
            detail=(recorded, actual),
        )
    return CheckResult(
        OK, f"The dataset's recorded codebook matches {source}.")


# ── Mutators ────────────────────────────────────────────────────────────────

def _break_resolve(artifact):
    broken = copy.deepcopy(artifact)
    record = records_of(broken)[0]
    record["Deductive_Codes"] = "phantom_code"
    record["All_Codes"] = "phantom_code"
    return broken


def _break_inductive(artifact):
    broken = copy.deepcopy(artifact)
    records_of(broken).append({
        "chunk_id": 99,
        "text": "An utterance that produced a code nobody wrote down.",
        "Deductive_Codes": "",
        "Inductive_Codes": "never_folded_back",
        "All_Codes": "never_folded_back_IND",
        "Coding_Status": "Inductive_Only",
    })
    return broken


def _break_unused(artifact):
    broken = copy.deepcopy(artifact)
    records = records_of(broken)
    if len(records) > 1:
        records.pop()
    else:
        records[0]["Deductive_Codes"] = ""
        records[0]["All_Codes"] = ""
    return broken


def _break_provenance(artifact):
    broken = copy.deepcopy(artifact)
    stanza_of(broken)["codebook_checksum"] = "0" * 16
    return broken


register(
    Check(
        name="coded.codes-resolve",
        artifact_class=CLASS_CODED,
        mark=MARK_MIRROR,
        summary="Every deductively applied code is in the codebook",
        predicate=codes_resolve,
        break_artifact=_break_resolve,
    ),
    Check(
        name="coded.inductive-unfolded",
        artifact_class=CLASS_CODED,
        mark=MARK_SURPRISE,
        summary="Codes discovered during coding that never entered the codebook",
        predicate=inductive_unfolded,
        break_artifact=_break_inductive,
        hypothesis=(
            "That inductive discovery would be folded back into the codebook "
            "rather than left beside it. Hybrid work often assumes this "
            "without saying so, and the codes left outside are the ones the "
            "codebook was least prepared for."
        ),
    ),
    Check(
        name="coded.unused-codes",
        artifact_class=CLASS_CODED,
        mark=MARK_SURPRISE,
        summary="Codes in the codebook that were never applied",
        predicate=unused_codes,
        break_artifact=_break_unused,
        hypothesis=(
            "That every code in the book was expected to earn its place in "
            "this data. Inductive and multi-corpus work may not hold this, "
            "which is why it asks rather than enforces."
        ),
    ),
    Check(
        name="coded.codebook-provenance",
        artifact_class=CLASS_CODED,
        mark=MARK_SURPRISE,
        summary="The dataset was coded against the codebook it names",
        predicate=codebook_provenance,
        break_artifact=_break_provenance,
        hypothesis=(
            "That the codebook did not move under the coding. A codebook "
            "revised mid-pass leaves a dataset whose earlier and later "
            "records mean different things by the same label."
        ),
    ),
)
