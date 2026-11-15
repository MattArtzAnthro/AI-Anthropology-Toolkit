"""A draft methods paragraph assembled from the decision record (R6.3–R6.6).

Every number in it is counted from the record's entries, desk by desk, in the order the
desks were built; where a card was decided more than once, the latest entry counts. It is
labelled as assembled, because the researcher, not the record, is the author of a methods
section.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

__all__ = ["LABEL", "paragraph"]

LABEL = (
    "Assembled from the decision record, not written by the researcher; check it against "
    "your own account before you use it."
)
_DONE = {"adopt": "adopted", "reword": "reworded", "merge": "merged into another code", "split": "split", "delete": "deleted"}


def _n(count: int, one: str, many: str) -> str:
    return f"{count} {one if count == 1 else many}"


def _listed(parts: list[str]) -> str:
    return parts[0] if len(parts) == 1 else f"{', '.join(parts[:-1])} and {parts[-1]}"


def _by_desk(entries: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    desks: dict[str, list[Mapping[str, Any]]] = {}
    for entry in entries:
        desks.setdefault(entry["desk_id"], []).append(entry)
    return desks


def _latest(entries: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The researcher's decision in force on each card: the latest of theirs for it. (The
    ratify entry sits on the card ``desk``, which no count reads.)"""
    latest: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        if entry["decided_by"] == "researcher":
            latest[entry["card_id"]] = entry
    return list(latest.values())


def _version(entries: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    ratified = [entry for entry in entries if entry["action"] == "ratify"]
    return ratified[-1]["detail"] if ratified else None


def _codebook(entries: list[Mapping[str, Any]], build: Mapping[str, Any]) -> list[str]:
    drafted = any(entry["action"] == "draft" for entry in entries)
    size = _n(build["detail"]["cards"], "code", "codes")
    version = _version(entries)
    if version is None:
        opening = f"A model drafted a codebook of {size}." if drafted else f"A codebook of {size} was put on a codebook desk."
        return [opening, "The codebook desk has not been finished."]
    decided = _latest(entries)
    actions = Counter(entry["action"] for entry in decided if entry["action"] in _DONE)
    done = [f"{actions[action]} {word}" for action, word in _DONE.items() if actions[action]]
    deciding = "deciding each code against the cases it would take"
    if drafted:
        said = [f"A model drafted a codebook of {size}.",
                f"The researcher ratified it on a codebook desk, {deciding}"]
    else:
        said = [f"The researcher ratified a codebook of {size} on a codebook desk, {deciding}"]
    said[-1] += f": {_listed(done)}." if done else "."
    answers = [entry["detail"].get("exclusive") for entry in decided if entry["action"] == "answer_exclusive"]
    if answers:
        said.append(f"The researcher judged the codes {'' if answers[-1] else 'not '}mutually exclusive.")
    said.append(f"This made codebook version {version['version']}.")
    return said


def _rulings(entries: list[Mapping[str, Any]], build: Mapping[str, Any]) -> list[str]:
    proposed = any(entry["action"] == "propose" for entry in entries)
    cards = build["detail"]["cards"]
    opening = f"A rulings desk presented {_n(cards, 'chunk', 'chunks')} on which two coding passes disagreed"
    if not proposed:
        opening += ", with no model proposals."
    elif build["detail"].get("blind_first", True):
        opening += ", with blind-first on, so each model proposal stayed hidden until the researcher had saved a ruling on its chunk."
    else:
        opening += ", with blind-first off, so each model proposal was shown beside its chunk from the start."
    version = _version(entries)
    if version is None:
        return [opening, "The rulings desk has not been finished."]
    decided = _latest(entries)
    rulings = [entry for entry in decided if entry["action"] == "ruling"]
    excluded = sum(entry["action"] == "exclude" for entry in decided)
    said = [opening, f"The researcher ruled on {len(rulings)} and excluded {excluded} from the analysis."]
    departed = sum(entry["detail"].get("departs") is True for entry in rulings)
    rules = sum(entry["detail"].get("is_rule") is True for entry in rulings)
    sentence = f"{_n(departed, 'ruling', 'rulings')} departed from the proposal" if proposed else ""
    if rules:
        adopted = f"{rules} {'was' if rules == 1 else 'were'} adopted as {'a rule' if rules == 1 else 'rules'}"
        adopted += f", amending the codebook to version {version['version']}"
        sentence = f"{sentence}, and {adopted}" if sentence else adopted
    if sentence:
        said.append(sentence + ".")
    return said


def _unchecked(entries: list[Mapping[str, Any]], prior: str) -> list[str]:
    """R6.6: agreed chunks not rechecked against this desk's amendments, until a sweep runs."""
    version = _version(entries)
    if not version or not version.get("amendments") or not version.get("agreed_unchecked"):
        return []
    ratified_at = max(entry["time"] for entry in entries if entry["action"] == "ratify")
    if any(entry["action"] == "sweep" and entry["time"] >= ratified_at for entry in entries):
        return []
    count, amendments = version["agreed_unchecked"], version["amendments"]
    were = "was" if count == 1 else "were"
    have = "has" if count == 1 else "have"
    under = f" under version {prior}" if prior else ""
    against = "the amendment" if amendments == 1 else f"the {amendments} amendments"
    return [f"{_n(count, 'chunk', 'chunks')} on which both passes agreed {were} coded{under} and {have} not been rechecked against {against}."]


def paragraph(lineage: Sequence[Mapping[str, Any]]) -> str:
    """The methods paragraph for a lineage, as ``record.read_lineage`` returns it."""
    said = [LABEL]
    prior = ""
    for entries in _by_desk(lineage).values():
        builds = [entry for entry in entries if entry["action"] == "build"]
        if not builds:
            continue
        build = builds[-1]
        if build["detail"].get("stage") == "codebook":
            said += _codebook(entries, build)
        else:
            said += _rulings(entries, build)
            said += _unchecked(entries, prior)
        version = _version(entries)
        prior = version["version"] if version else prior
    if len(said) == 1:
        said.append("The record holds no desk decisions.")
    return " ".join(said)
