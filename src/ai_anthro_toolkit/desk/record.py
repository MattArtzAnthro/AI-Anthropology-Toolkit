"""The decision record: every decision made at a desk, and what the machine put in front of
the researcher, kept append-only as ``record.jsonl`` in the desk's job.

An entry is ``{desk_id, card_id, action, detail, note, time, surface, decided_by}``. Its
``action`` comes from one vocabulary, which the methods paragraph reads:

- by the machine, when a desk is built: ``build`` (card ``desk``; detail ``stage``,
  ``cards``, and for a rulings desk ``blind_first`` and the ``ratification_id`` in force),
  ``draft`` (one per code a model drafted; detail ``label``) and ``propose`` (one per
  proposal; detail ``codes``, ``rationale``); later, ``sweep`` (card ``desk``; detail
  ``rechecked``) when agreed chunks are rechecked against amendments;
- by the researcher: ``adopt``, ``reword``, ``merge``, ``split`` and ``delete`` (the
  decision's fields as detail), ``answer_exclusive`` (card ``exclusivity``; detail
  ``exclusive``), ``ruling`` (detail ``codes`` or ``none_apply``, ``departs``, and
  ``is_rule`` and ``rule_text`` when given), ``exclude`` (detail ``reason``), and
  ``ratify`` (card ``desk``; detail ``ratification_id``, ``version``, ``parent``,
  ``amendments`` and, when there are amendments, ``agreed_unchecked``).

A card decided more than once keeps every entry; the latest is the decision in force.
"""

import json
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from ai_anthro_toolkit.jobs import JobStore

__all__ = ["ACTIONS", "DESKS", "SURFACES", "add_desk", "append", "desks", "read", "read_lineage"]

# The rulings desks this release builds on a ratification. Earlier releases listed them under
# "desks" in ratification.json, which they read, change and write without a lock; this file
# they never open, so a desk listed here cannot be dropped by one of them.
DESKS = "desks.json"

Entry = dict[str, Any]
RECORD = "record.jsonl"
MACHINE_ACTIONS = ("build", "draft", "propose", "sweep")
RESEARCHER_ACTIONS = ("adopt", "reword", "merge", "split", "delete", "answer_exclusive", "ruling", "exclude", "ratify")
ACTIONS = MACHINE_ACTIONS + RESEARCHER_ACTIONS
SURFACES = ("app", "page", "chat", "table", "server")
_FIELDS = {"card_id", "action", "detail", "note", "surface", "decided_by"}


def _utc(now: Callable[[], datetime]) -> str:
    return now().astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _checked(entry: Mapping[str, Any]) -> list[str]:
    """What is wrong with an entry, as a list of complaints."""
    found = [f"an entry does not take {key}" for key in sorted(set(entry) - _FIELDS)]
    if not isinstance(entry.get("card_id"), str) or not entry["card_id"].strip():
        found.append("an entry names its card_id")
    if entry.get("decided_by") not in ("researcher", "machine"):
        found.append(f"decided_by is researcher or machine, not {entry.get('decided_by')!r}")
    elif entry.get("action") not in (RESEARCHER_ACTIONS if entry["decided_by"] == "researcher" else MACHINE_ACTIONS):
        found.append(f"{entry.get('action')!r} is not an action the {entry['decided_by']} records")
    if entry.get("surface") not in SURFACES:
        found.append(f"surface is one of {', '.join(SURFACES)}, not {entry.get('surface')!r}")
    if not isinstance(entry.get("detail", {}), Mapping):
        found.append("detail is an object")
    if not isinstance(entry.get("note", ""), str):
        found.append("note is text")
    return found


def read(store: JobStore, desk_id: str) -> list[Entry]:
    """Every entry in a desk's record, oldest first."""
    text = store.load_artifact(desk_id, RECORD) or ""
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def append(
    store: JobStore,
    desk_id: str,
    entries: Sequence[Mapping[str, Any]],
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> list[Entry]:
    """Append ``entries`` to the desk's record, all stamped with one UTC time, and return
    them as written. Refuses the whole batch, writing nothing, if any entry breaks the
    vocabulary."""
    for n, entry in enumerate(entries, start=1):
        complaints = _checked(entry)
        if complaints:
            raise ValueError(f"Record entry {n} for {desk_id} is refused: {'; '.join(complaints)}.")
    time = _utc(now)
    written = [
        {
            "desk_id": desk_id, "card_id": entry["card_id"], "action": entry["action"],
            "detail": dict(entry.get("detail", {})), "note": entry.get("note", ""),
            "time": time, "surface": entry["surface"], "decided_by": entry["decided_by"],
        }
        for entry in entries
    ]
    lines = "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in written)
    store.save_artifact(desk_id, RECORD, (store.load_artifact(desk_id, RECORD) or "") + lines)
    return written


def _desk_list(ratification_id: str, name: str, value: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(d, str) for d in value):
        raise ValueError(f"{ratification_id}'s list of desks is damaged: {name} must hold a list "
                         "of desk IDs. Restore it from a copy, or ratify the codebook again and "
                         "code under the new ratification_id.")
    return value


def _own_desks(store: JobStore, ratification_id: str) -> list[str]:
    text = store.load_artifact(ratification_id, DESKS)
    try:
        value = json.loads(text) if text is not None else []
    except json.JSONDecodeError:
        value = None
    return _desk_list(ratification_id, DESKS, value)


def desks(store: JobStore, ratification_id: str) -> list[str]:
    """The rulings desks built on a ratification: those an earlier release listed in
    ratification.json, then those listed in desks.json, each once."""
    held = json.loads(store.load_artifact(ratification_id, "ratification.json") or "{}")
    listed = [*_desk_list(ratification_id, "ratification.json", held.get("desks", [])),
              *_own_desks(store, ratification_id)]
    return list(dict.fromkeys(listed))


def add_desk(store: JobStore, ratification_id: str, desk_id: str) -> None:
    """List a rulings desk under its ratification. Hold the ratification's lock."""
    desks(store, ratification_id)  # refuses a damaged list
    store.save_artifact(ratification_id, DESKS,
                        json.dumps([*_own_desks(store, ratification_id), desk_id]))


def _ratification(store: JobStore, ratification_id: str) -> dict[str, Any]:
    text = store.load_artifact(ratification_id, "ratification.json")
    if text is None:
        raise ValueError(f"{ratification_id} has no ratification record.")
    loaded: dict[str, Any] = json.loads(text)
    return loaded


def read_lineage(store: JobStore, ratification_id: str) -> list[Entry]:
    """The entries behind a ratification: from the first ratification in its chain to this
    one, each one's desk and then the rulings desks built under it, each desk read once.
    A ratification made from a table, with no desk, contributes nothing."""
    chain: list[tuple[str, dict[str, Any]]] = []
    current: str | None = ratification_id
    while current:
        if current in (rid for rid, _ in chain):
            raise ValueError(f"The ratification chain behind {ratification_id} loops at {current}.")
        record = _ratification(store, current)
        chain.append((current, record))
        current = record.get("parent")
    behind: list[str] = []
    for rid, record in reversed(chain):
        for desk_id in [record.get("desk_id"), *desks(store, rid)]:
            if desk_id and desk_id not in behind:
                behind.append(desk_id)
    return [entry for desk_id in behind for entry in read(store, desk_id)]
