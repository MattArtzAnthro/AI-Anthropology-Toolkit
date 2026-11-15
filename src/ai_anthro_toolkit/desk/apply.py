"""Decisions applied, as pure transforms the gate calls once a document has passed
``decisions.validate``.

- ``apply_actions``: the codebook a codebook desk ratifies (R2.7).
- ``resolve``: one resolved record per disagreement, and an amendment for each ruling
  that states a rule (R4.1).
- ``amend``: a codebook whose amended codes carry their rules, for the next version.

Nothing here writes, numbers versions or mints IDs; the gate does, after everything
here has succeeded.
"""

import copy
from collections.abc import Mapping, Sequence
from typing import Any

__all__ = ["amend", "apply_actions", "resolve"]

Record = dict[str, Any]


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def apply_actions(
    codebook: Sequence[Mapping[str, Any]],
    cards: Sequence[Mapping[str, Any]],
    decisions: Mapping[str, Mapping[str, Any]],
) -> list[Record]:
    """The codebook after each card's action, in codebook order: a reword replaces the
    definition (and the label, when given) and keeps every other field, a merge or a
    delete drops the code, and a split's parts take its place. Refuses a result that
    would hold one label twice, naming the card that introduces it.
    """
    records = {_clean(record.get("code_label")): record for record in codebook}
    missing = [card["code_label"] for card in cards if card["code_label"] not in records]
    if missing:
        raise ValueError(f"The codebook does not match its desk: it lacks {', '.join(missing)}.")
    _check_labels(cards, decisions)
    result: list[Record] = []
    for card in cards:
        decision = decisions[card["card_id"]]
        record = copy.deepcopy(dict(records[card["code_label"]]))
        action = decision["action"]
        if action == "reword":
            record["definition"] = _clean(decision["definition"])
            record["code_label"] = _new_label(card, decision)
        if action in ("adopt", "reword"):
            result.append(record)
        elif action == "split":
            result += [{"code_label": _clean(part["label"]), "definition": _clean(part["definition"])} for part in decision["parts"]]
    return result


def _new_label(card: Mapping[str, Any], decision: Mapping[str, Any]) -> str:
    return _clean(decision.get("label")) or card["code_label"]


def _check_labels(cards: Sequence[Mapping[str, Any]], decisions: Mapping[str, Mapping[str, Any]]) -> None:
    """Refuse a result holding one label twice. Labels that stay as they were are claimed
    first; each new label (a relabel, or a split's parts) is then claimed in card order,
    so a clash names the card that brings the second copy."""
    kept = {
        card["code_label"] for card in cards
        if decisions[card["card_id"]]["action"] in ("adopt", "reword")
        and _new_label(card, decisions[card["card_id"]]) == card["code_label"]
    }
    for card in cards:
        decision = decisions[card["card_id"]]
        if decision["action"] == "reword" and _new_label(card, decision) != card["code_label"]:
            new = [_new_label(card, decision)]
        elif decision["action"] == "split":
            new = [_clean(part["label"]) for part in decision["parts"]]
        else:
            continue
        for label in new:
            if label in kept:
                raise ValueError(f"{card['card_id']} gives the label {label!r}, which the ratified codebook already has.")
            kept.add(label)


def resolve(cards: Sequence[Mapping[str, Any]], decisions: Mapping[str, Mapping[str, Any]]) -> tuple[list[Record], list[Record]]:
    """One resolved record per card, in card order, and one amendment per ruling that
    states a rule. A record holds the chunk, its codes as the coded data writes them
    (``Deductive_Codes``, comma-separated), and how it was resolved: ``ruled``,
    ``no_code`` or ``excluded`` (with the reason). An amendment cites its card and names
    the codes in dispute there, both passes' and any the ruling adds, in that order.
    Refuses cards without a decision.
    """
    undecided = [card["card_id"] for card in cards if card["card_id"] not in decisions]
    if undecided:
        raise ValueError(f"These cards have no decision: {', '.join(undecided)}.")
    records: list[Record] = []
    amendments: list[Record] = []
    for card in cards:
        decision = decisions[card["card_id"]]
        record: Record = {"chunk_id": card["chunk_id"], "card_id": card["card_id"], "text": card["text"], "source": card["source"]}
        if "exclude" in decision:
            record.update(Deductive_Codes="", resolution="excluded", exclusion_reason=_clean(decision["exclude"]["reason"]))
        elif decision.get("none_apply"):
            record.update(Deductive_Codes="", resolution="no_code")
        else:
            ruled = [code for code in card["entries"] if code in decision["codes"]]
            ruled += [code for code in decision["codes"] if code not in ruled]
            record.update(Deductive_Codes=", ".join(ruled), resolution="ruled")
        records.append(record)
        if decision.get("is_rule") is True:
            disputed = list(dict.fromkeys([*card["entries"], *decision.get("codes", [])]))
            amendments.append({"source_card": card["card_id"], "rule_text": _clean(decision["rule_text"]), "codes": disputed})
    return records, amendments


def amend(codebook: Sequence[Mapping[str, Any]], amendments: Sequence[Mapping[str, Any]]) -> list[Record]:
    """A copy of ``codebook`` in which each code an amendment names carries its rule text
    under ``rules``, after any rules it already has. The codebook passed in is unchanged,
    so the prior version stays as it was."""
    result = [copy.deepcopy(dict(record)) for record in codebook]
    by_label = {_clean(record.get("code_label")): record for record in result}
    for amendment in amendments:
        for code in amendment["codes"]:
            if code not in by_label:
                raise ValueError(f"The rule from {amendment['source_card']} names {code!r}, which is not in the codebook in force.")
            by_label[code]["rules"] = [*by_label[code].get("rules", []), amendment["rule_text"]]
    return result
