"""A decisions document, ``aat/desk-decisions@1``: the one shape every surface sends.

``parse`` reads a document's shape and refuses one it cannot read. ``validate`` checks the
decisions against the desk they name and returns every problem, each naming its card, so
the gate can refuse a document whole and say everything that is wrong at once.

    {"schema": "aat/desk-decisions@1", "desk_id": "desk-1a2b3c4d5e6f", "card_checksum": "…",
     "exclusive": true,
     "decisions": {"code-01": {"action": "reword", "definition": "…", "note": "…"},
                   "chunk-12": {"codes": ["…"], "is_rule": true, "rule_text": "…"},
                   "chunk-15": {"exclude": {"reason": "…"}}}}

Codebook actions are ``adopt``; ``reword`` (``definition``, optional ``label``); ``merge``
(``target``, a code label); ``split`` (``parts``: two or more ``{label, definition}``); and
``delete``. A ruling gives ``codes``, ``none_apply: true`` or ``exclude: {reason}``, with
``is_rule`` and ``rule_text`` when it states a rule. Any decision may carry a ``note``.
"""

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ai_anthro_toolkit.desk.cards import checksum

__all__ = ["SCHEMA", "Decisions", "Problem", "differs", "parse", "validate"]

SCHEMA = "aat/desk-decisions@1"
ACTIONS = ("adopt", "reword", "merge", "split", "delete")
_TOP = {"schema", "desk_id", "card_checksum", "exclusive", "decisions"}
_ACTION_FIELDS = {
    "adopt": {"action", "note"},
    "reword": {"action", "definition", "label", "note"},
    "merge": {"action", "target", "note"},
    "split": {"action", "parts", "note"},
    "delete": {"action", "note"},
}
_RULING_FIELDS = {"codes", "none_apply", "exclude", "is_rule", "rule_text", "note"}
_RULING_KINDS = ("codes", "none_apply", "exclude")


@dataclass(frozen=True)
class Decisions:
    """A parsed decisions document. ``exclusive`` is None when the document leaves it out."""

    desk_id: str
    card_checksum: str
    exclusive: bool | None
    decisions: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class Problem:
    """One thing wrong with a document. ``card_id`` is the card's ID, ``desk`` for the
    document as a whole, or ``exclusivity`` for the codebook's question."""

    card_id: str
    message: str


def parse(doc: Any) -> Decisions:
    """The document's decisions, copied; refuses a document of any other shape."""
    if not isinstance(doc, Mapping):
        raise ValueError(f"A decisions document is a JSON object with schema {SCHEMA!r}.")
    if doc.get("schema") != SCHEMA:
        raise ValueError(f"This is not a decisions document: its schema is {doc.get('schema')!r}, not {SCHEMA!r}.")
    unknown = sorted(set(doc) - _TOP)
    if unknown:
        raise ValueError(f"A decisions document does not take {', '.join(unknown)}.")
    for key in ("desk_id", "card_checksum"):
        if not isinstance(doc.get(key), str) or not doc[key].strip():
            raise ValueError(f"A decisions document names its desk_id and card_checksum; {key} is missing.")
    exclusive = doc.get("exclusive")
    if exclusive is not None and not isinstance(exclusive, bool):
        raise ValueError("exclusive is true, false, or left out.")
    chosen = doc.get("decisions")
    if not isinstance(chosen, Mapping):
        raise ValueError("decisions is an object from card ID to decision.")
    for card_id, decision in chosen.items():
        if not isinstance(decision, Mapping):
            raise ValueError(f"The decision on {card_id} is not an object.")
    return Decisions(
        desk_id=doc["desk_id"].strip(),
        card_checksum=doc["card_checksum"].strip(),
        exclusive=exclusive,
        decisions={str(card_id): copy.deepcopy(dict(decision)) for card_id, decision in chosen.items()},
    )


def _blank(value: Any) -> bool:
    return not isinstance(value, str) or not value.strip()


def _text_fields(decision: Mapping[str, Any], keys: tuple[str, ...]) -> list[str]:
    return [f"{key} must be text." for key in keys if decision.get(key) is not None and not isinstance(decision[key], str)]


def _code_problems(card: Mapping[str, Any], decision: Mapping[str, Any], chosen: Mapping[str, Any], labels: dict[str, str]) -> list[str]:
    label = card["code_label"]
    action = decision.get("action")
    if action is None:
        return [f"The decision on {label} gives no action; choose {', '.join(ACTIONS[:-1])} or {ACTIONS[-1]}."]
    if action not in ACTIONS:
        return [f"{action!r} is not an action; choose {', '.join(ACTIONS[:-1])} or {ACTIONS[-1]}."]
    extra = sorted(set(decision) - _ACTION_FIELDS[action])
    if extra:
        return [f"{action} does not take {', '.join(extra)}."]
    untyped = _text_fields(decision, ("definition", "label", "target", "note"))
    if untyped:
        return untyped
    if action == "reword" and _blank(decision.get("definition")):
        return [f"The reword of {label} has an empty definition."]
    if action == "merge":
        return _merge_problems(label, decision.get("target"), chosen, labels)
    if action == "split":
        return _split_problems(label, decision.get("parts"))
    return []


def _merge_problems(label: str, target: Any, chosen: Mapping[str, Any], labels: dict[str, str]) -> list[str]:
    if target == label:
        return [f"{label} cannot be merged into itself."]
    if target not in labels:
        return [f"{label} is merged into {target!r}, which is not a code in this codebook."]
    fate = chosen.get(labels[target], {}).get("action")
    if fate == "delete":
        return [f"{label} is merged into {target}, which is deleted."]
    if fate in ("merge", "split"):
        return [f"{label} is merged into {target}, which is itself {'merged' if fate == 'merge' else 'split'}."]
    return []


def _split_problems(label: str, parts: Any) -> list[str]:
    parts = [] if parts is None else parts
    if not isinstance(parts, list) or not all(isinstance(part, Mapping) for part in parts):
        return [f"Each part of the split of {label} needs a label and a definition."]
    if len(parts) < 2:
        return [f"A split needs at least two parts; {label} has {len(parts)}."]
    found = []
    seen: set[str] = set()
    for n, part in enumerate(parts, start=1):
        if _blank(part.get("label")):
            found.append(f"Part {n} of the split of {label} has no label.")
        elif part["label"].strip() in seen:
            found.append(f"The split of {label} names {part['label'].strip()!r} twice.")
        else:
            seen.add(part["label"].strip())
        if _blank(part.get("definition")):
            found.append(f"Part {n} of the split of {label} has no definition.")
    return found


def differs(card: Mapping[str, Any], decision: Mapping[str, Any]) -> bool:
    """Whether a ruling departs from its card's proposal, so that the researcher is asked
    whether it states a rule (R3.6). An exclusion is not a ruling, and a card with no
    proposal has nothing to depart from."""
    if card.get("proposal") is None or "exclude" in decision:
        return False
    return set(decision.get("codes", [])) != set(card["proposal"]["codes"])  # none_apply rules no codes


def _ruling_problems(desk: Mapping[str, Any], card: Mapping[str, Any], decision: Mapping[str, Any], complete: bool) -> list[str]:
    extra = sorted(set(decision) - _RULING_FIELDS)
    if extra:
        return [f"A ruling does not take {', '.join(extra)}."]
    kinds = [kind for kind in _RULING_KINDS if kind in decision]
    if len(kinds) != 1:
        given = " and ".join(kinds) or "none"
        return [f"A ruling gives codes, no code applies, or an exclusion; this one gives {given}."]
    untyped = _text_fields(decision, ("rule_text", "note"))
    if untyped:
        return untyped
    if "exclude" in decision:
        exclude = decision["exclude"]
        found = [] if isinstance(exclude, Mapping) and not _blank(exclude.get("reason")) else ["An exclusion needs a reason."]
        if "is_rule" in decision or "rule_text" in decision:
            found.append("An exclusion does not state a rule; take out is_rule and rule_text.")
        return found
    found = _ruled_problems(desk, decision)
    if "is_rule" in decision and not isinstance(decision["is_rule"], bool):
        found.append("is_rule must be true or false.")
    elif decision.get("is_rule") is True and _blank(decision.get("rule_text")):
        found.append("The ruling is marked as a rule but gives no rule text.")
    elif complete and not found and "is_rule" not in decision and differs(card, decision):
        found.append("The ruling differs from the proposal; say whether it states a rule.")
    return found


def _ruled_problems(desk: Mapping[str, Any], decision: Mapping[str, Any]) -> list[str]:
    """What is wrong with the codes, or the none_apply, a ruling gives (R3.3, R3.7)."""
    exclusive = bool(desk.get("exclusive"))
    if "none_apply" in decision:
        if decision["none_apply"] is not True:
            return ["none_apply is true when given."]
        if exclusive:
            return ["The codes are mutually exclusive, so a ruling takes exactly one code, not No code applies."]
        return []
    codes = decision["codes"]
    if not isinstance(codes, list) or not all(isinstance(code, str) for code in codes):
        return ["codes must be a list of code labels."]
    if not codes:
        return ["A ruling with codes names at least one; for none, give none_apply."]
    found = [f"The ruling names {code!r} twice." for code in dict.fromkeys(c for c in codes if codes.count(c) > 1)]
    found += [f"The ruling names {code!r}, which is not in the codebook in force." for code in codes if code not in desk["codes"]]
    if exclusive and len(set(codes)) > 1:
        found.append(f"The codes are mutually exclusive, so a ruling takes exactly one code; this one takes {len(set(codes))}.")
    return found


def validate(desk: Mapping[str, Any], decisions: Decisions, complete: bool) -> list[Problem]:
    """Every problem with ``decisions`` against ``desk``: first the document's, then each
    card's in desk order, then decisions for cards the desk lacks. With ``complete``, a
    desk with a card left undecided, or a codebook desk with its question unanswered, or
    a differing ruling whose rule question is unanswered, is a problem too; without it
    (a decision saved one at a time) those may follow later.
    """
    found: list[Problem] = []
    if decisions.desk_id != desk["desk_id"]:
        found.append(Problem("desk", f"These decisions are for {decisions.desk_id}, not {desk['desk_id']}."))
    if decisions.card_checksum != checksum(desk["cards"]):
        found.append(Problem("desk", "These decisions were made on a different desk version."))
    stage = desk["stage"]
    if stage == "rulings" and decisions.exclusive is not None and decisions.exclusive != bool(desk["exclusive"]):
        said, holds = ("are", "are not") if decisions.exclusive else ("are not", "are")
        found.append(Problem("desk", f"These rulings say the codes {said} mutually exclusive; the codebook in force says they {holds}."))
    chosen = decisions.decisions
    open_cards = [card["card_id"] for card in desk["cards"] if card["card_id"] not in chosen]
    if complete and stage == "rulings" and open_cards:
        found.append(Problem("desk", f"{len(open_cards)} of {len(desk['cards'])} cards are still open."))
    labels = {card["code_label"]: card["card_id"] for card in desk["cards"]} if stage == "codebook" else {}
    for card in desk["cards"]:
        card_id = card["card_id"]
        if card_id not in chosen:
            if complete and stage == "codebook":
                found.append(Problem(card_id, f"{card['code_label']} has no decision."))
            continue
        decision = chosen[card_id]
        messages = (
            _code_problems(card, decision, chosen, labels) if stage == "codebook"
            else _ruling_problems(desk, card, decision, complete)
        )
        found += [Problem(card_id, message) for message in messages]
    on_desk = {card["card_id"] for card in desk["cards"]}
    found += [Problem(card_id, f"{card_id} is not a card on this desk.") for card_id in chosen if card_id not in on_desk]
    if complete and stage == "codebook" and decisions.exclusive is None:
        found.append(Problem("exclusivity", "The question whether the codes are mutually exclusive is unanswered."))
    return found
