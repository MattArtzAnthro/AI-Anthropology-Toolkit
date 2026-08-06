"""The five commitment mutations, and the harness that runs them.

Stage 4 of `tool-building` settles five recurring commitments about what an
instrument should do: what an empty result means, whether a duplicate
identifier is an error or a fact about the source, whether a partly present
field is required, what an unparseable value does, and whether source order
carries meaning.

Settling them in a table records what the researcher intends. It does not
show that the instrument does it. These mutations close that gap: each one
produces the input that would violate one commitment, so an instrument can be
*shown* to behave the way its researcher said rather than assumed to.

Two rules hold this module to input mutation and nothing more.

**Nothing here mutates code.** Rewriting a researcher's source produces
mutants that do not compile, mutants that are semantically identical to the
original, and — worst — mutants with side effects.

**Nothing here reaches the network, and nothing here should be pointed at
anything that does.** Mutating a collector's rate limit or retry cap and
running it is an unsandboxed adversarial run against someone else's server,
and it can get a researcher blocked from the archive they are studying. Run
these against records already in hand.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Sequence
from dataclasses import dataclass

_CORRUPT_MARKER = "not-a-value"


def _records(data) -> list:
    return copy.deepcopy(list(data or []))


# ── The five mutations ──────────────────────────────────────────────────────

def empty(data, **_kw) -> list:
    """Nothing came back. Is that a failure, or a fact about the source?"""
    return []


def duplicate_record(data, **_kw) -> list:
    """The same record twice. An error to reject, or a real duplicate?"""
    out = _records(data)
    if out:
        out.insert(1, copy.deepcopy(out[0]))
    return out


def drop_field(data, field: str = "", **_kw) -> list:
    """One record is missing a field the others have. Optional, or a signal?"""
    out = _records(data)
    if out and isinstance(out[0], dict):
        target = field or next(iter(out[0]), "")
        out[0].pop(target, None)
    return out


def corrupt_value(data, field: str = "", **_kw) -> list:
    """A value that will not parse. Skip the record, null it, or stop?"""
    out = _records(data)
    if out and isinstance(out[0], dict):
        target = field or next(iter(out[0]), "")
        if target in out[0]:
            out[0][target] = _CORRUPT_MARKER
    return out


def reorder(data, **_kw) -> list:
    """The same records in a different order. Does the order mean anything?"""
    return list(reversed(_records(data)))


@dataclass(frozen=True)
class Commitment:
    question: str
    mutation: Callable[..., list]


COMMITMENTS: dict[str, Commitment] = {
    "emptiness": Commitment(
        "Nothing came back. Is that a failure of the instrument, or a fact "
        "about the source worth recording?",
        empty),
    "duplication": Commitment(
        "Two records carry the same identifier. Is that an error to reject, "
        "or a real duplicate in the archive to preserve?",
        duplicate_record),
    "partial-presence": Commitment(
        "A field is present in most records and absent from one. Is it "
        "optional, or required and therefore a signal the source changed?",
        drop_field),
    "unparseable": Commitment(
        "A value will not parse. Skip the record, keep it with the value "
        "null, or stop and report?",
        corrupt_value),
    "ordering": Commitment(
        "The records arrive in a different order. Does source order carry "
        "meaning, or is it incidental?",
        reorder),
}


# ── The harness ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MutationResult:
    commitment: str
    question: str
    quiet_on_good: bool
    fired_on_mutation: bool
    detail: str = ""

    @property
    def guards(self) -> bool:
        """Whether the check distinguishes the good input from the broken one.

        A check that fires on everything and a check that fires on nothing
        both fail here, and both are invisible without running the pair.
        """
        return self.quiet_on_good and self.fired_on_mutation

    def __str__(self) -> str:
        if self.guards:
            return (f"{self.commitment}: the instrument notices. "
                    f"{self.question}")
        if not self.quiet_on_good:
            return (f"{self.commitment}: this check objects to input the "
                    f"researcher considers good, so it cannot tell the two "
                    f"apart.")
        return (f"{self.commitment}: nothing noticed. The instrument treats "
                f"the broken input exactly like the good one, so its answer "
                f"to this question is whatever the code happens to do.")


def _passes(check: Callable, records) -> tuple[bool, str]:
    """Run a check. A raised exception counts as noticing, loudly."""
    try:
        return bool(check(records)), ""
    except Exception as error:  # noqa: BLE001 - any failure is a signal
        return False, f"{type(error).__name__}: {error}"


def confirm_fires(check: Callable, records: Sequence, commitment: str,
                  **mutation_kwargs) -> MutationResult:
    """Break one commitment and report whether the check noticed.

    ``check`` receives the records and returns something truthy when it is
    satisfied. Raising counts as noticing: an instrument that crashes on a
    duplicate has registered it, however rudely, and that is worth
    distinguishing from silence.
    """
    entry = COMMITMENTS[commitment]
    good, _ = _passes(check, _records(records))
    broken, detail = _passes(
        check, entry.mutation(records, **mutation_kwargs))
    return MutationResult(
        commitment=commitment,
        question=entry.question,
        quiet_on_good=good,
        fired_on_mutation=not broken,
        detail=detail,
    )


def confirm_all(check: Callable, records: Sequence,
                **mutation_kwargs) -> list[MutationResult]:
    """Run every commitment against one check.

    Most checks guard one commitment and are silent on the rest, which is
    correct rather than a finding. Read the results as a map of what this
    check does and does not cover, never as a score.
    """
    return [confirm_fires(check, records, name, **mutation_kwargs)
            for name in COMMITMENTS]
