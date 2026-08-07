"""Standing checks generated from the researcher's own Stage 4 answers.

`tool-building` Stage 4 asks the researcher to settle five commitments about
what their instrument should do: what an empty result means, whether a
duplicate identifier is an error, whether a partly present field is required,
what an unparseable value does, and whether source order carries meaning.
Those answers go into the specification, and until now nothing enforced them.

This turns each answered commitment into a check the researcher can re-run
over their own data — the same standing-check machinery the toolkit ships for
codebooks, pointed at whatever they built.

Three rules hold it honest.

**An unanswered commitment generates nothing.** Silence is not consent to a
default, and a check the researcher never asked for is the toolkit asserting
a methodological commitment about their work.

**An answer that cannot be checked is reported, not dropped.** Ordering is the
clear case: whether source order was preserved cannot be read off a single
artifact. A researcher who answered five commitments and received three
checks is told which two and why.

**Nothing here executes anything from a project directory.** A checks file
lives beside a researcher's data. It is data, it is validated against a fixed
vocabulary, and a loader that could run what it found there would turn "check
my data" into "run whatever is in that folder".
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from .registry import (FIRED, MARK_SURPRISE, OK, Check, CheckResult,
                       records_of, register)

DOCUMENT_VERSION = 1


@dataclass(frozen=True)
class Unenforceable:
    commitment: str
    answer: str
    why: str


@dataclass
class Generated:
    checks: list = field(default_factory=list)
    unenforceable: list = field(default_factory=list)


# ── Predicates, one per checkable answer ────────────────────────────────────

def _empty_is_failure(artifact, **_kw) -> CheckResult:
    if not records_of(artifact):
        return CheckResult(
            FIRED,
            "Nothing came back. You said an empty result is a failure of the "
            "instrument rather than a fact about the source, so this is the "
            "case you asked to be told about.")
    return CheckResult(OK, "The result is not empty.")


def _duplicates_are_errors(field_name):
    def predicate(artifact, **_kw) -> CheckResult:
        seen, dupes = set(), []
        for record in records_of(artifact):
            key = record.get(field_name) if isinstance(record, dict) else None
            if key is None:
                continue
            if key in seen and key not in dupes:
                dupes.append(key)
            seen.add(key)
        if dupes:
            return CheckResult(
                FIRED,
                f"{len(dupes)} repeated value(s) of '{field_name}': "
                f"{', '.join(map(str, dupes))}. You said a duplicate here is "
                f"an error rather than a real duplicate in the source.",
                detail=tuple(dupes))
        return CheckResult(OK, f"No repeated '{field_name}' values.")
    return predicate


def _field_is_required(field_name):
    def predicate(artifact, **_kw) -> CheckResult:
        missing = [i for i, r in enumerate(records_of(artifact))
                   if isinstance(r, dict) and not str(r.get(field_name, "")).strip()]
        if missing:
            return CheckResult(
                FIRED,
                f"{len(missing)} record(s) carry no '{field_name}'. You said "
                f"this field is required, so its absence is a signal rather "
                f"than an option.",
                detail=tuple(missing))
        return CheckResult(OK, f"Every record carries '{field_name}'.")
    return predicate


_UNPARSEABLE_MARKER = "not-a-value"


def _unparseable_stops(field_name):
    def predicate(artifact, **_kw) -> CheckResult:
        bad = [i for i, r in enumerate(records_of(artifact))
               if isinstance(r, dict)
               and str(r.get(field_name, "")).strip() == _UNPARSEABLE_MARKER]
        if bad:
            return CheckResult(
                FIRED,
                f"{len(bad)} record(s) carry a '{field_name}' value that will "
                f"not parse. You said the instrument should stop and report "
                f"rather than skip or null it.",
                detail=tuple(bad))
        return CheckResult(OK, f"Every '{field_name}' value parses.")
    return predicate


# ── Mutators, reusing the commitment mutations ──────────────────────────────

def _break_empty(artifact):
    return []


def _break_duplicate(artifact):
    out = copy.deepcopy(records_of(artifact))
    if out:
        out.insert(1, copy.deepcopy(out[0]))
    return out


def _break_missing(field_name):
    def mutate(artifact):
        out = copy.deepcopy(records_of(artifact))
        if out and isinstance(out[0], dict):
            out[0].pop(field_name, None)
        return out
    return mutate


def _break_unparseable(field_name):
    def mutate(artifact):
        out = copy.deepcopy(records_of(artifact))
        if out and isinstance(out[0], dict):
            out[0][field_name] = _UNPARSEABLE_MARKER
        return out
    return mutate


# ── The answer vocabulary ───────────────────────────────────────────────────
#
# Fixed on purpose. Free text would put the machine back in the business of
# deciding what the researcher meant, which is the judgment Stage 4 exists to
# route to them.

ANSWERS = {
    "emptiness": {
        "failure": {
            "checkable": True, "needs_field": False,
            "means": "an empty result is a failure of the instrument",
            "predicate": lambda _f: _empty_is_failure,
            "mutator": lambda _f: _break_empty,
            "hypothesis": "that nothing coming back means the instrument "
                          "broke, rather than that the source holds nothing",
        },
        "fact": {
            "checkable": False, "needs_field": False,
            "means": "an empty result is a fact about the source",
            "why": "Nothing to check: an empty result is an acceptable "
                   "outcome, so no artifact can violate it.",
        },
    },
    "duplication": {
        "error": {
            "checkable": True, "needs_field": True,
            "means": "a repeated identifier is an error to reject",
            "predicate": _duplicates_are_errors,
            "mutator": lambda _f: _break_duplicate,
            "hypothesis": "that the identifier is unique in the source, "
                          "rather than that the source really repeats it",
        },
        "real": {
            "checkable": False, "needs_field": False,
            "means": "a repeated identifier is a real duplicate to preserve",
            "why": "Nothing to check: duplicates are expected, so their "
                   "presence cannot violate the commitment.",
        },
    },
    "partial-presence": {
        "required": {
            "checkable": True, "needs_field": True,
            "means": "the field is required, so its absence is a signal",
            "predicate": _field_is_required,
            "mutator": _break_missing,
            "hypothesis": "that every record carries this field, so a gap "
                          "means the source changed rather than that the "
                          "field was always optional",
        },
        "optional": {
            "checkable": False, "needs_field": False,
            "means": "the field is optional",
            "why": "Nothing to check: an absent value is permitted, so no "
                   "artifact can violate it.",
        },
    },
    "unparseable": {
        "stop": {
            "checkable": True, "needs_field": True,
            "means": "an unparseable value should stop the run and report",
            "predicate": _unparseable_stops,
            "mutator": _break_unparseable,
            "hypothesis": "that an unparseable value is worth interrupting "
                          "for, rather than something to pass over quietly",
        },
        "skip": {
            "checkable": False, "needs_field": False,
            "means": "an unparseable value means skip the record",
            "why": "Nothing to check in the output: a skipped record is "
                   "absent, and absence is indistinguishable from a record "
                   "the source never held.",
        },
        "null": {
            "checkable": False, "needs_field": False,
            "means": "an unparseable value is kept as null",
            "why": "Nothing to check: a null is the intended result, so its "
                   "presence cannot violate the commitment.",
        },
    },
    "ordering": {
        "meaningful": {
            "checkable": False, "needs_field": False,
            "means": "source order carries meaning and must be preserved",
            "why": "Cannot be checked from one artifact. Whether order was "
                   "preserved is a claim about the source and the output "
                   "together, and only the source settles it.",
        },
        "incidental": {
            "checkable": False, "needs_field": False,
            "means": "source order is incidental",
            "why": "Nothing to check: any order is acceptable.",
        },
    },
}


def _spec(commitment: str, answer: str) -> dict:
    if commitment not in ANSWERS:
        raise ValueError(f"unknown commitment {commitment!r}")
    if answer not in ANSWERS[commitment]:
        allowed = ", ".join(sorted(ANSWERS[commitment]))
        raise ValueError(
            f"{commitment}: {answer!r} is not one of the answers this "
            f"commitment offers ({allowed}). The vocabulary is fixed so that "
            f"nothing has to interpret what an answer meant.")
    return ANSWERS[commitment][answer]


def from_answers(answers: dict, *, artifact: str,
                 fields: dict | None = None) -> Generated:
    """Build checks from the answers the researcher gave at Stage 4."""
    fields = fields or {}
    out = Generated()
    for commitment, answer in answers.items():
        spec = _spec(commitment, answer)
        if not spec["checkable"]:
            out.unenforceable.append(
                Unenforceable(commitment, answer, spec["why"]))
            continue
        field_name = fields.get(commitment, "")
        if spec["needs_field"] and not field_name:
            raise ValueError(
                f"{commitment}: the answer {answer!r} is about a particular "
                f"field, so it needs one named. Nothing here guesses which.")
        summary = spec["means"] + (f" ({field_name})" if field_name else "")
        out.checks.append(Check(
            name=f"{artifact}.{commitment}",
            artifact_class=artifact,
            mark=MARK_SURPRISE,
            summary=summary,
            predicate=spec["predicate"](field_name),
            break_artifact=spec["mutator"](field_name),
            hypothesis=spec["hypothesis"],
        ))
    return out


# ── Persistence ─────────────────────────────────────────────────────────────

def to_document(answers: dict, *, artifact: str, instrument: str,
                fields: dict | None = None) -> dict:
    """The file that ships beside a researcher's project.

    Data, not code. It records what they answered, which answers produced a
    check, and which could not — so a suite that enforces three of five
    commitments says so on its face.
    """
    built = from_answers(answers, artifact=artifact, fields=fields)
    return {
        "version": DOCUMENT_VERSION,
        "instrument": instrument,
        "artifact": artifact,
        "answers": dict(answers),
        "fields": dict(fields or {}),
        "enforced": [c.name for c in built.checks],
        "not_enforced": [
            {"commitment": u.commitment, "answer": u.answer, "why": u.why}
            for u in built.unenforceable],
    }


def from_document(document: dict) -> Generated:
    """Rebuild checks from a saved document, validating as it goes."""
    return from_answers(document.get("answers", {}),
                        artifact=document.get("artifact", "artifact"),
                        fields=document.get("fields", {}))


def register_document(document: dict) -> Generated:
    """Load a project's checks into the registry for this run."""
    built = from_document(document)
    if built.checks:
        register(*built.checks)
    return built
