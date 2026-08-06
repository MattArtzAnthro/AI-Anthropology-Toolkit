"""Standing checks over durable artifacts: the registry and its vocabulary.

A check is a named predicate over one artifact class, carrying three things
the toolkit needs and most check registries do not have:

* a **mark**, saying whether the check could ever teach the researcher
  anything (``mirror``), whether it could surface a commitment they never
  stated (``surprise-capable``), or whether it asserts a methodological
  commitment and therefore may only run once the researcher has established
  that the commitment is theirs (``stance-gated``);
* a **hypothesis**, for anything that is not a mirror, naming which unstated
  commitment a firing would reveal;
* a **mutator**, which breaks a good artifact in the one way this check
  exists to catch.

The mutator is what makes the guarantee structural. A check registered
without one fails the registry-completeness test rather than passing
quietly, and because the mutator sits beside the predicate it cannot drift
away from it the way a separate broken fixture silently does.

No check writes to the artifact it reads, makes a network call, or reports
an all-clear on a question it cannot settle.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

# ── Vocabulary ──────────────────────────────────────────────────────────────

MARK_MIRROR = "mirror"
MARK_SURPRISE = "surprise-capable"
MARK_STANCE = "stance-gated"

OK = "ok"
FIRED = "fired"
CANNOT_TELL = "cannot_tell"
NOT_APPLICABLE = "not_applicable"

CLASS_CODEBOOK = "codebook"
CLASS_CODED = "coded_data"

PROVENANCE_KEY = "_toolkit_provenance"

_DETERMINATE = (OK, FIRED)


@dataclass(frozen=True)
class CheckResult:
    """One check's verdict. ``message`` is the product, not the verdict."""

    verdict: str
    message: str
    check: str = ""
    detail: tuple = ()


@dataclass(frozen=True)
class Check:
    name: str
    artifact_class: str
    mark: str
    summary: str
    predicate: Callable[..., CheckResult]
    break_artifact: Callable[[object], object]
    hypothesis: str = ""

    def run(self, artifact, **context) -> CheckResult:
        result = self.predicate(artifact, **context)
        return CheckResult(result.verdict, result.message, self.name, result.detail)


@dataclass
class CheckReport:
    artifact_class: str
    results: list = field(default_factory=list)

    @property
    def fired(self):
        return [r for r in self.results if r.verdict == FIRED]

    @property
    def passed(self):
        return [r for r in self.results if r.verdict == OK]

    @property
    def undetermined(self):
        return [r for r in self.results if r.verdict == CANNOT_TELL]

    @property
    def mirror_only(self):
        """True when nothing that could have taught anything actually ran.

        A green run of mirror checks is not evidence of understanding, and
        the record must not let it read as one.
        """
        for result in self.results:
            check = by_name(result.check)
            if check.mark != MARK_MIRROR and result.verdict in _DETERMINATE:
                return False
        return True


class AmbiguousArtifact(Exception):
    """Raised when a payload could be more than one class.

    Detection refuses rather than guessing, because a misdetection produces
    a false all-clear and that is the one outcome this design forbids.
    """

    def __init__(self, candidates: Sequence[str]):
        self.candidates = list(candidates)
        super().__init__(
            "cannot tell which kind of artifact this is; it could be "
            + " or ".join(self.candidates)
            + ". Name it explicitly rather than letting me guess."
        )


# ── Provenance ──────────────────────────────────────────────────────────────

def codebook_checksum(labels: Sequence[str]) -> str:
    """Order-independent digest of a codebook's label set."""
    payload = json.dumps(sorted(str(label) for label in labels))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def provenance_stanza(*, produced_by: str, codebook_labels: Sequence[str],
                      artifact_class: str = "",
                      ratification_id: str = "",
                      artifact_file: str = "") -> dict:
    """The small stanza a producer writes so its artifact can describe itself.

    Without it, an artifact that arrived by another route makes no claim
    about which codebook it was coded against, and a check has nothing to
    read.
    """
    labels = [str(label) for label in codebook_labels]
    return {
        "produced_by": produced_by,
        "artifact_class": artifact_class,
        # Which file this stanza describes. A sidecar sits in a directory
        # that may hold several artifacts, and provenance borrowed from a
        # neighbour is worse than none: the checks would report on one
        # artifact using another one's codebook and say nothing about it.
        "artifact_file": artifact_file,
        "codebook_labels": labels,
        "codebook_checksum": codebook_checksum(labels),
        "ratification_id": ratification_id,
    }


PROVENANCE_SIDECAR = "provenance.json"


def stanza_of(artifact) -> dict | None:
    if isinstance(artifact, dict):
        stanza = artifact.get(PROVENANCE_KEY)
        if isinstance(stanza, dict):
            return stanza
    return None


def records_of(artifact) -> list:
    """Every artifact reduces to a list of records, however it was handed over."""
    if isinstance(artifact, list):
        return artifact
    if isinstance(artifact, dict):
        for key in ("records", "rows", "data", "codes"):
            value = artifact.get(key)
            if isinstance(value, list):
                return value
    return []


# ── Detection ───────────────────────────────────────────────────────────────

_CODEBOOK_MARKERS = {"code_label", "definition"}
_CODED_MARKERS = {"chunk_id", "Deductive_Codes", "Inductive_Codes",
                  "All_Codes", "Coding_Status"}


def detect_artifact_class(artifact) -> str | None:
    """Name the artifact's class, refuse if ambiguous, return None if unknown."""
    stanza = stanza_of(artifact)
    if stanza and stanza.get("artifact_class"):
        return stanza["artifact_class"]

    records = records_of(artifact)
    if not records or not isinstance(records[0], dict):
        return None

    keys = set(records[0])
    looks_codebook = bool(keys & _CODEBOOK_MARKERS)
    looks_coded = bool(keys & _CODED_MARKERS)

    if looks_codebook and looks_coded:
        raise AmbiguousArtifact([CLASS_CODEBOOK, CLASS_CODED])
    if looks_codebook:
        return CLASS_CODEBOOK
    if looks_coded:
        return CLASS_CODED
    return None


# ── Registry ────────────────────────────────────────────────────────────────

REGISTRY: tuple = ()


def register(*checks: Check) -> None:
    global REGISTRY
    REGISTRY = REGISTRY + checks


def by_name(name: str) -> Check:
    for check in REGISTRY:
        if check.name == name:
            return check
    raise KeyError(f"no check named {name!r}")


def for_class(artifact_class: str) -> list:
    return [c for c in REGISTRY if c.artifact_class == artifact_class]


def run_checks(artifact, *, artifact_class: str | None = None,
               **context) -> CheckReport:
    """Run every check registered for the artifact's class."""
    if artifact_class is None:
        artifact_class = detect_artifact_class(artifact)
    if artifact_class is None:
        raise ValueError(
            "cannot tell what kind of artifact this is. Name it explicitly "
            "rather than letting me guess, because guessing wrong here "
            "produces a false all-clear."
        )
    report = CheckReport(artifact_class=artifact_class)
    for check in for_class(artifact_class):
        report.results.append(check.run(artifact, **context))
    return report
