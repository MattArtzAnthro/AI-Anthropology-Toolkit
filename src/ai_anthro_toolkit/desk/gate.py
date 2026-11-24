"""The import gate (R2.5–R2.8, R4.1–R4.5, R5, R6.1): the one path by which decisions made
at a desk enter the analysis, whichever surface they were made on.

``apply`` works in two steps. It first checks the desk and the whole decisions document and
works out everything it will write, naming every problem at once and writing nothing on a
refusal. Then it writes, in an order that a second call with the same decisions can resume
if the first is interrupted: ``finishing.json`` (the document's digest and the ID of the
ratification it mints), the ratification, the desk's resolved records, the decision record (appended
once, as one batch), and ``finished.json``, which holds the digest and the outcome, so the
same decisions sent again return the same outcome and write nothing (R5.6). The digest is
taken over the document as sent, so decisions that differ only in a note's spacing count
as different decisions.

A desk job (kind ``desk``) holds in its payload ``stage``, ``title``, ``cards`` and
``card_checksum``; a rulings desk also holds ``codes``, ``exclusive``, ``blind_first``, the
``ratification_id`` in force, and ``agreed``, the number of chunks both passes coded alike.
A codebook desk holds its source records as the artifact ``codebook.json``.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from ai_anthro_toolkit.crosslens import codebook_checksum
from ai_anthro_toolkit.desk import apply as transforms
from ai_anthro_toolkit.desk import cards as desk_cards
from ai_anthro_toolkit.desk import decisions as desk_decisions
from ai_anthro_toolkit.desk import record
from ai_anthro_toolkit.jobs import JobStore

__all__ = ["SURFACES", "apply", "check_save", "load_desk", "next_version", "problem_lines"]

SURFACES = ("app", "page", "chat")
Outcome = dict[str, Any]
_NEXT = "pass ratification_id to start_coding_job"
_NEEDS = {
    "codebook": ("cards", "card_checksum"),
    "rulings": ("cards", "card_checksum", "codes", "exclusive", "ratification_id", "agreed"),
}


@dataclass
class _Plan:
    """Everything a finish writes, worked out before anything is written."""

    outcome: Outcome
    entries: list[dict[str, Any]]
    mint: list[dict[str, Any]] | None = None  # the codebook a new ratification holds
    held: dict[str, Any] = field(default_factory=dict)  # its ratification record, less checksum, codes and note
    in_force: str | None = None  # the ratification that stays in force when none is minted
    resolved: list[dict[str, Any]] | None = None  # a rulings desk's resolved records


def next_version(version: str) -> str:
    """The next minor version: 1.0 gives 1.1, and 1.9 gives 1.10."""
    major, _, minor = str(version).partition(".")
    if not (major.isdigit() and minor.isdigit()):
        raise ValueError(f"{version!r} is not a codebook version.")
    return f"{int(major)}.{int(minor) + 1}"


def _json(store: JobStore, job_id: str, name: str) -> Any:
    text = store.load_artifact(job_id, name)
    return json.loads(text) if text else None


def load_desk(store: JobStore, desk_id: str) -> dict[str, Any]:
    """The desk job's payload with its ``desk_id``, as ``a2ui`` and ``decisions`` take a
    desk. Refuses an ID that is not a desk, a desk lacking what its stage needs, and cards
    that no longer match their checksum."""
    job = store.read(desk_id)  # refuses an ID the store did not issue (R5.1)
    if job.get("kind") != "desk":
        raise ValueError(f"{desk_id} is not a desk.")
    desk = dict(job["payload"], desk_id=desk_id)
    if desk.get("stage") not in _NEEDS:
        raise ValueError(f"{desk_id} is neither a codebook desk nor a rulings desk; build the desk again.")
    lacking = [name for name in _NEEDS[desk["stage"]] if name not in desk]
    if lacking:
        raise ValueError(f"{desk_id} lacks {', '.join(lacking)}; build the desk again.")
    if desk_cards.checksum(desk["cards"]) != desk["card_checksum"]:
        raise ValueError(f"The cards stored with {desk_id} no longer match their checksum; build the desk again.")
    return desk


def _digest(chosen: desk_decisions.Decisions) -> str:
    return hashlib.sha256(json.dumps(asdict(chosen), sort_keys=True).encode()).hexdigest()


def problem_lines(heading: str, problems: list[desk_decisions.Problem]) -> str:
    """``heading``, then one line per problem, each naming its card unless the message
    already does or the problem is the document's or the exclusivity question's."""
    lines = [
        p.message if p.card_id in ("desk", "exclusivity") or p.message.startswith(p.card_id) else f"{p.card_id}: {p.message}"
        for p in problems
    ]
    return heading + "\n" + "\n".join(f"- {line}" for line in lines)


_SAVE = "This decision cannot be saved:"


def check_save(desk: Mapping[str, Any], saved: Mapping[str, Any], codebook: list[dict[str, Any]] | None) -> None:
    """Refuse what a desk would hold after one more decision is saved (``saved``: its
    ``decisions`` and ``exclusive``), as ``desk_sync`` saves it. Every saved decision is
    checked, not only the newest, since a save can break another (a merge into a code this
    save deletes). On a codebook desk the actions are then applied to ``codebook`` with
    the undecided codes adopted, so a label two decisions both bring is refused when it is
    saved. The standalone page runs the same checks (``desk/app/src/local.js``).
    """
    chosen = desk_decisions.Decisions(
        desk_id=desk["desk_id"], card_checksum=desk_cards.checksum(desk["cards"]),
        exclusive=saved["exclusive"], decisions=saved["decisions"],
    )
    problems = desk_decisions.validate(desk, chosen, complete=False)
    if problems:
        raise ValueError(problem_lines(_SAVE, problems))
    if desk["stage"] == "codebook":
        every = {card["card_id"]: saved["decisions"].get(card["card_id"], {"action": "adopt"}) for card in desk["cards"]}
        source = codebook if codebook is not None else [{"code_label": card["code_label"]} for card in desk["cards"]]
        try:
            transforms.apply_actions(source, desk["cards"], every)
        except ValueError as exc:
            raise ValueError(f"{_SAVE}\n- {exc}") from exc


def _refusal(problems: list[desk_decisions.Problem]) -> ValueError:
    return ValueError(problem_lines("These decisions cannot be applied:", problems))


def _unchecked(count: int, amendments: int, prior: str) -> str:
    chunks = f"{count} chunk both passes agreed on was" if count == 1 else f"{count} chunks both passes agreed on were"
    have = "has" if count == 1 else "have"
    against = "the amendment" if amendments == 1 else f"the {amendments} amendments"
    return f"{chunks} coded under version {prior} and {have} not been rechecked against {against}."


def finishing_with(store: JobStore, desk_id: str, doc: Any) -> bool:
    """Whether an interrupted finish of the desk was started with these decisions."""
    pending = _json(store, desk_id, "finishing.json")
    return bool(pending) and pending["digest"] == _digest(desk_decisions.parse(doc))


def apply(store: JobStore, desk_id: str, doc: Any, surface: str) -> Outcome:
    """Apply a decisions document (``aat/desk-decisions@1``) to a desk, made on ``surface``
    (``app``, ``page`` or ``chat``), and return the outcome. Refuses, writing nothing, a
    desk it did not issue, a document for another desk or desk version, and any document
    that does not decide every card (R2.6, R5.1–R5.4)."""
    desk = load_desk(store, desk_id)
    if surface not in SURFACES:
        raise ValueError(f"Decisions reach a desk from the app, page or chat, not {surface!r}.")
    chosen = desk_decisions.parse(doc)
    digest = _digest(chosen)
    finished = _json(store, desk_id, "finished.json")
    if finished:
        if finished["digest"] == digest:
            stored: Outcome = finished["outcome"]
            return stored
        raise ValueError(
            f"{desk_id} is already finished, as {finished['outcome']['ratification_id']}, with other decisions. "
            "To decide again, build a new desk."
        )
    pending = _json(store, desk_id, "finishing.json")
    if pending and pending["digest"] != digest:
        raise ValueError(f"Finishing {desk_id} with other decisions was interrupted; send those decisions again to complete it.")
    problems = desk_decisions.validate(desk, chosen, complete=True)
    if problems:
        raise _refusal(problems)
    plan = _plan_codebook(store, desk, chosen) if desk["stage"] == "codebook" else _plan_rulings(store, desk, chosen)
    return _commit(store, desk_id, plan, digest, pending, surface)


def _commit(store: JobStore, desk_id: str, plan: _Plan, digest: str, pending: Any, surface: str) -> Outcome:
    if pending:
        rid = pending["ratification_id"]
    else:
        rid = store.new_id("ratification") if plan.mint is not None else str(plan.in_force)
        store.save_artifact(desk_id, "finishing.json", json.dumps({"digest": digest, "ratification_id": rid}))
    if plan.mint is not None:
        # Made only once finishing.json names it, so an interrupted finish leaves no
        # ratification job that nothing names; sent again, it makes the one named.
        store.create("ratification", {"codes": len(plan.mint)}, job_id=rid)
        held = {"checksum": plan.outcome["checksum"], "codes": len(plan.mint), "note": "", **plan.held}
        with store.locked(rid):
            # Sent again after an interruption: the ratification was already usable, and a
            # rulings desk an earlier release built on it since then stays on its list (this
            # release lists its own in desks.json, which this write leaves alone).
            earlier = _json(store, rid, "ratification.json")
            if earlier and earlier.get("desks"):
                held["desks"] = earlier["desks"]
            store.save_artifact(rid, "result.json", json.dumps(plan.mint))
            store.save_artifact(rid, "ratification.json", json.dumps(held))
            store.complete(rid)
    if plan.resolved is not None:
        store.save_artifact(desk_id, "result.json", json.dumps(plan.resolved))
    plan.entries[-1]["detail"]["ratification_id"] = rid
    if not any(entry["action"] == "ratify" for entry in record.read(store, desk_id)):
        record.append(store, desk_id, [dict(entry, surface=surface, decided_by="researcher") for entry in plan.entries])
    outcome = dict(plan.outcome, ratification_id=rid)
    store.save_artifact(desk_id, "finished.json", json.dumps({"digest": digest, "outcome": outcome}))
    store.complete(desk_id)
    return outcome


def _decided(card_id: str, action: str, decision: Mapping[str, Any], detail: dict[str, Any]) -> dict[str, Any]:
    return {"card_id": card_id, "action": action, "detail": detail, "note": str(decision.get("note") or "").strip()}


def _plan_codebook(store: JobStore, desk: dict[str, Any], chosen: desk_decisions.Decisions) -> _Plan:
    source = _json(store, desk["desk_id"], "codebook.json")
    if not source:
        raise ValueError(f"{desk['desk_id']} holds no codebook to ratify; build the desk again.")
    result = transforms.apply_actions(source, desk["cards"], chosen.decisions)
    entries = []
    for card in desk["cards"]:
        decision = chosen.decisions[card["card_id"]]
        detail = {k: v for k, v in decision.items() if k not in ("action", "note")}
        entries.append(_decided(card["card_id"], decision["action"], decision, detail))
    entries.append(_decided("exclusivity", "answer_exclusive", {}, {"exclusive": chosen.exclusive}))
    entries.append(_decided("desk", "ratify", {}, {"ratification_id": None, "version": "1.0", "parent": None, "amendments": 0}))
    outcome = {"desk_id": desk["desk_id"], "stage": "codebook", "ratification_id": None, "version": "1.0",
               "checksum": codebook_checksum(result), "codes": len(result), "next": _NEXT}
    held = {"method": "desk", "version": "1.0", "parent": None, "desk_id": desk["desk_id"],
            "exclusive": chosen.exclusive, "amendments": [], "desks": []}
    return _Plan(outcome=outcome, entries=entries, mint=result, held=held)


def _ruling_detail(card: Mapping[str, Any], decision: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    if "exclude" in decision:
        return "exclude", {"reason": str(decision["exclude"]["reason"]).strip()}
    detail: dict[str, Any] = {"none_apply": True} if decision.get("none_apply") else {"codes": list(decision["codes"])}
    detail["departs"] = desk_decisions.differs(card, decision)
    if "is_rule" in decision:
        detail["is_rule"] = decision["is_rule"]
    if decision.get("is_rule") is True:
        detail["rule_text"] = str(decision["rule_text"]).strip()
    return "ruling", detail


def _plan_rulings(store: JobStore, desk: dict[str, Any], chosen: desk_decisions.Decisions) -> _Plan:
    desk_id, in_force = desk["desk_id"], desk["ratification_id"]
    held = _json(store, in_force, "ratification.json")
    codebook = _json(store, in_force, "result.json")
    if not held or not codebook:
        raise ValueError(f"The ratification in force, {in_force}, holds no codebook; the rulings cannot be applied.")
    prior = held.get("version", "1.0")
    agreed = int(desk["agreed"])
    resolved, rules = transforms.resolve(desk["cards"], chosen.decisions)
    entries = []
    for card in desk["cards"]:
        decision = chosen.decisions[card["card_id"]]
        action, detail = _ruling_detail(card, decision)
        entries.append(_decided(card["card_id"], action, decision, detail))
    outcome: Outcome = {"desk_id": desk_id, "stage": "rulings", "resolved": len(resolved), "amendments": len(rules)}
    if not rules:
        entries.append(_decided("desk", "ratify", {}, {"ratification_id": None, "version": prior, "parent": held.get("parent"), "amendments": 0}))
        return _Plan(outcome={**outcome, "ratification_id": None, "version": prior}, entries=entries, in_force=in_force, resolved=resolved)
    version = next_version(prior)
    amendments = [
        {"amendment_id": f"{version}-{n}", "from_version": prior, "to_version": version, "rule_text": rule["rule_text"],
         "source_card": rule["source_card"], "desk_id": desk_id, "codes": rule["codes"]}
        for n, rule in enumerate(rules, start=1)
    ]
    amended = transforms.amend(codebook, amendments)
    entries.append(_decided("desk", "ratify", {}, {
        "ratification_id": None, "version": version, "parent": in_force, "amendments": len(amendments), "agreed_unchecked": agreed,
    }))
    outcome = {
        **outcome, "ratification_id": None, "version": version, "parent": in_force, "checksum": codebook_checksum(amended),
        "codes": len(amended), "agreed_unchecked": agreed, "unchecked": _unchecked(agreed, len(amendments), prior), "next": _NEXT,
    }
    held_now = {"method": "amendment", "version": version, "parent": in_force, "desk_id": desk_id,
                "exclusive": bool(desk["exclusive"]), "amendments": amendments, "desks": []}
    return _Plan(outcome=outcome, entries=entries, mint=amended, held=held_now, resolved=resolved)
