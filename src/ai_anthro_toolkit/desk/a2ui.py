"""The desk as A2UI v1.0 messages, checked against the pinned schema and catalogs.

The schemas in ``a2ui_schema/`` are copied unchanged from the pinned
``@a2ui/web_core`` release (see ``VENDORED.md``). A2UI's message schema checks
every component against one catalog; a desk draws on two, so ``validate``
checks each message's envelope first, then each component against the catalog
it names (its own ``catalogId``, else its surface's). It then applies the checks
the bundled renderer makes in strict mode (``STRICT_VALIDATION`` in
``@a2ui/web_core``), so a message the server passes is one the desk view draws:
component IDs are identifiers, an update names each ID once, and after every
update the surface has a ``root`` from which every component is reachable and
every reference resolves. ``tests/package/test_desk_a2ui.py`` runs the
renderer's own check under node and requires the two to agree.
"""

import json
from collections.abc import Iterator, Mapping, Sequence
from functools import cache
from importlib import resources
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from ai_anthro_toolkit import __version__
from ai_anthro_toolkit.desk import BASIC_CATALOG_ID, CATALOG_ID
from ai_anthro_toolkit.desk.decisions import differs

__all__ = ["NO_CODE", "after_decision", "catalog_problems", "decision_from_action", "surface", "validate"]

_BASE = "https://a2ui.org/specification/v1_0/"
# Where the message schema looks for "the" catalog. Each check loads one catalog here.
_CATALOG_URI = _BASE + "catalog.json"

# Stands in for a catalog while the envelope is checked: any component passes,
# because each one is checked against its own catalog afterwards.
_ANY_CATALOG = {
    "$defs": {
        "anyComponent": {"type": "object", "required": ["component"], "additionalProperties": True},
        "anyFunction": {"type": "object", "additionalProperties": True},
    }
}


def _load(name: str) -> dict[str, Any]:
    root = resources.files("ai_anthro_toolkit.desk")
    data: dict[str, Any] = json.loads(root.joinpath(name).read_text(encoding="utf-8"))
    return data


@cache
def _catalogs() -> dict[str, dict[str, Any]]:
    """The catalogs a desk may use, by catalog ID."""
    return {
        BASIC_CATALOG_ID: _load("a2ui_schema/catalogs/basic/catalog.json"),
        CATALOG_ID: _load("catalog.json"),
    }


def _registry(catalog: Mapping[str, Any]) -> Registry:
    """The A2UI schemas, with ``catalog`` where the message schema expects its catalog.

    Each schema is registered under its own ``$id``. A catalog's refs
    (``common_types.json#...``) are relative, so it is loaded at the
    specification's base URI whatever its ``$id``.
    """
    bodies = [
        _load("a2ui_schema/agent_to_renderer.json"),
        _load("a2ui_schema/common_types.json"),
        _load("a2ui_schema/catalog_definition.json"),
        dict(catalog, **{"$id": _CATALOG_URI}),
    ]
    # A Registry without a retrieve function refuses any schema it does not hold, so
    # nothing is fetched; a validator given no registry at all would fetch, so every
    # validator here is given one.
    return Registry().with_resources((body["$id"], DRAFT202012.create_resource(body)) for body in bodies)


@cache
def _envelope() -> Draft202012Validator:
    return Draft202012Validator({"$ref": _BASE + "agent_to_renderer.json"}, registry=_registry(_ANY_CATALOG))


@cache
def _catalog_registry(catalog_id: str) -> Registry:
    return _registry(_catalogs()[catalog_id])


def _first_error(validator: Draft202012Validator, instance: Any) -> str | None:
    """The most telling error, or None. When a subschema fails, its properties count as
    unevaluated too; an unevaluated-property error is reported only when it stands alone."""
    errors = list(validator.iter_errors(instance))
    direct = [e for e in errors if e.validator != "unevaluatedProperties"]
    error = best_match(direct or errors)
    if error is None:
        return None
    where = "/".join(str(p) for p in error.absolute_path)
    return f"{error.message} (at {where})" if where else error.message


def _component_problem(component: Mapping[str, Any], catalog_id: str) -> str | None:
    """Checks one component against its catalog entry, as the message schema's Component
    does, but against that entry alone so a problem names the component's properties."""
    if catalog_id not in _catalogs():
        return f"catalog {catalog_id} is not the basic catalog or the toolkit catalog"
    name = component.get("component")
    if name not in _catalogs()[catalog_id]["components"]:
        return f"{name!r} is not in the catalog {catalog_id}"
    schema = {
        "allOf": [
            {"$ref": _BASE + "common_types.json#/$defs/ComponentCommon"},
            {"$ref": f"{_CATALOG_URI}#/components/{name}"},
        ],
        "unevaluatedProperties": False,
    }
    return _first_error(Draft202012Validator(schema, registry=_catalog_registry(catalog_id)), component)


# The common types whose values name other components.
_SINGLE_REFS = ("/Child", "/ComponentId")
_LIST_REFS = ("/ChildList",)


@cache
def _reference_fields(catalog_id: str, name: str) -> dict[str, frozenset[str] | None]:
    """The properties of a component that name other components, as the renderer reads
    them from the catalog: a Child, ChildList or ComponentId property, or an array of
    objects some of whose keys are (the set of those keys)."""
    entry = _catalogs()[catalog_id]["components"][name]
    fields: dict[str, frozenset[str] | None] = {}
    for part in [entry, *entry.get("allOf", [])]:
        for prop, schema in part.get("properties", {}).items():
            if schema.get("$ref", "").endswith(_SINGLE_REFS + _LIST_REFS):
                fields[prop] = None
            elif schema.get("type") == "array" and isinstance(schema.get("items"), dict):
                nested = frozenset(
                    key for key, sub in schema["items"].get("properties", {}).items()
                    if sub.get("$ref", "").endswith(_SINGLE_REFS)
                )
                if nested:
                    fields[prop] = nested
    return fields


def _pointers(value: Any, nested: frozenset[str] | None = None) -> Iterator[str]:
    """Component IDs in one reference property's value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _pointers(item, nested)
    elif isinstance(value, dict):
        if "componentId" in value:  # a template over a data model list: {componentId, path}
            yield value["componentId"]
        elif nested:  # an item of a list of objects, such as one of a Tabs component's tabs
            for key in nested:
                if key in value:
                    yield from _pointers(value[key])


def _references(component: Mapping[str, Any], catalog_id: str) -> Iterator[str]:
    for prop, nested in _reference_fields(catalog_id, component["component"]).items():
        if prop in component:
            yield from _pointers(component[prop], nested)


def _topology(i: int, surface_id: str, components: Mapping[str, tuple[Mapping[str, Any], str]]) -> list[str]:
    """A surface's components after an update: a root, references that resolve, no
    cycle of references, and every component reachable from the root."""
    if "root" not in components:
        return [f"message {i}: surface {surface_id!r} has no component 'root'"]
    problems = []
    children: dict[str, list[str]] = {}
    for cid, (component, catalog_id) in components.items():
        children[cid] = list(_references(component, catalog_id))
        problems += [
            f"message {i}, component {cid!r}: refers to {ref!r}, which does not exist"
            for ref in children[cid] if ref not in components
        ]
    problems += [f"message {i}, component {cid!r}: is part of a cycle of references" for cid in _cycles(children)]
    reached, todo = {"root"}, ["root"]
    while todo:
        for ref in children[todo.pop()]:
            if ref in components and ref not in reached:
                reached.add(ref)
                todo.append(ref)
    problems += [f"message {i}, component {cid!r}: is not reachable from 'root'" for cid in components if cid not in reached]
    return problems


def _cycles(children: Mapping[str, list[str]]) -> list[str]:
    """The component each cycle of references closes on, in the order they are found."""
    state: dict[str, str] = {}  # "open" while its references are walked, then "done"
    closes: list[str] = []

    def walk(cid: str) -> None:
        state[cid] = "open"
        for ref in children.get(cid, []):
            if state.get(ref) == "open":
                closes.append(ref)
            elif ref not in state:
                walk(ref)
        state[cid] = "done"

    for cid in children:
        if cid not in state:
            walk(cid)
    return closes


def _update(i: int, surface_id: str, surface: dict[str, Any], components: Sequence[Mapping[str, Any]]) -> list[str]:
    """Checks an update and, when it passes, applies it to the surface, as the renderer
    does: an update that fails changes nothing."""
    problems: list[str] = []
    seen: set[str] = set()
    candidate = dict(surface["components"])
    for component in components:
        cid = component.get("id")
        where = f"message {i}, component {cid!r}"
        if not isinstance(cid, str) or not cid.isidentifier():
            problems.append(f"{where}: is not a UAX #31 identifier")
            continue
        if cid in seen:
            problems.append(f"{where}: appears twice in one update")
            continue
        seen.add(cid)
        catalog_id = component.get("catalogId") or surface["catalog"]
        problem = (
            "names no catalog, and its surface has none" if catalog_id is None
            else _component_problem(component, catalog_id)
        )
        if problem is not None:
            problems.append(f"{where}: {problem}")
            continue
        candidate[cid] = (component, catalog_id)
    if problems:
        return problems
    problems = _topology(i, surface_id, candidate)
    if not problems:
        surface["components"] = candidate
    return problems


def validate(messages: Sequence[Mapping[str, Any]]) -> list[str]:
    """Problems with this sequence of A2UI v1.0 messages, sent in order to a renderer
    that starts empty; an empty list means the desk view would draw them all (R1.8).

    A desk sends only createSurface, updateComponents, updateDataModel and
    deleteSurface. Each message must match the pinned message schema, and each component its entry
    in the basic or the toolkit catalog: the one its ``catalogId`` names, else its
    surface's. A surface is created once before it is used and is gone once deleted.
    After each update the surface must hold a ``root`` from which every component is
    reachable, and every reference must name a component.
    """
    surfaces: dict[str, dict[str, Any]] = {}
    problems: list[str] = []
    for i, message in enumerate(messages):
        envelope = _first_error(_envelope(), message)
        if envelope is not None:
            problems.append(f"message {i}: {envelope}")
            continue
        kind, body = next(iter((k, v) for k, v in message.items() if k != "version"))
        surface_id = body.get("surfaceId")
        if kind == "createSurface":
            if surface_id in surfaces:
                problems.append(f"message {i}: surface {surface_id!r} already exists")
                continue
            surfaces[surface_id] = {"catalog": body.get("catalogId"), "components": {}}
            if body.get("components"):
                problems += _update(i, surface_id, surfaces[surface_id], body["components"])
        elif kind == "deleteSurface":
            surfaces.pop(surface_id, None)
        elif kind not in ("updateComponents", "updateDataModel"):
            problems.append(f"message {i}: {kind} is not a message the desk sends")
        elif surface_id not in surfaces:
            problems.append(f"message {i}: surface {surface_id!r} is not created in these messages")
        elif kind == "updateComponents":
            problems += _update(i, surface_id, surfaces[surface_id], body["components"])
    return problems


def catalog_problems(catalog: Mapping[str, Any]) -> list[str]:
    """Problems with a catalog as an A2UI v1.0 catalog definition; empty when valid."""
    validator = Draft202012Validator(
        {"$ref": _BASE + "catalog_definition.json"}, registry=_registry(_ANY_CATALOG)
    )
    return [e.message for e in validator.iter_errors(catalog)]


# ── Describing a desk ──────────────────────────────────────────────────────────
#
# A desk is one surface. Its components hold what the desk shows; what changes as the
# researcher works lives in the data model. The fields they fill sit under /cards (and
# /exclusivity), and which card is open, which are done and how far the queue has got
# sit under /status, so the server restates the queue in one update without touching a
# field the researcher is still filling. Every choice and field starts unset (R2.3).
# Component IDs are built from positions, which are identifiers whatever a card or
# chunk is called; card IDs travel as data.

_VERSION = "v1.0"
Component = dict[str, Any]
Message = dict[str, Any]

NO_CODE = "(no code applies)"
"""The ruling choice for "No code applies"; a code may not be called this."""

_CODE_ACTIONS = [
    ("adopt", "Adopt", "Keep the code as it is."),
    ("reword", "Reword", "Change its definition, and its label if you like."),
    ("merge", "Merge", "Fold it into another code."),
    ("split", "Split", "Divide it into two or more codes."),
    ("delete", "Delete", "Drop it from the codebook."),
]
_CODE_RESULTS = {"adopt": "Adopted", "reword": "Reworded", "delete": "Deleted"}


def _bind(path: str) -> dict[str, str]:
    return {"@path": path}


def _basic(cid: str, component: str, **props: Any) -> Component:
    return {"id": cid, "component": component, "catalogId": BASIC_CATALOG_ID, **props}


def _toolkit(cid: str, component: str, **props: Any) -> Component:
    return {"id": cid, "component": component, **props}


def _button(cid: str, label: str, name: str, context: Mapping[str, Any], variant: str = "default") -> list[Component]:
    return [
        _basic(cid, "Button", child=f"{cid}_label", variant=variant, action={"event": {"name": name, "context": dict(context)}}),
        _basic(f"{cid}_label", "Text", text=label),
    ]


def _decision_card(cid: str, status: str, title: str, card_id: str, status_label: str, kids: list[str]) -> Component:
    """A queued DecisionCard whose open, done and result live at ``status``."""
    return _toolkit(
        cid, "DecisionCard", title=title, eyebrow=card_id, state="needs", statusLabel=status_label,
        open=_bind(f"{status}/open"), done=_bind(f"{status}/done"), result=_bind(f"{status}/result"),
        change={"event": {"name": "change_decision", "context": {"card_id": card_id}}}, children=kids,
    )


def _group(cid: str, heading: str, items: list[Component], parts: list[Component] | None = None) -> list[Component]:
    """A captioned column of ``items``; ``parts`` are components the items hold, such as
    a button's label, which travel with the group but are not its children."""
    return [
        _basic(cid, "Column", children=[f"{cid}_heading", *(item["id"] for item in items)]),
        _basic(f"{cid}_heading", "Text", text=heading, variant="caption"),
        *items,
        *(parts or []),
    ]


def _cases(prefix: str, heading: str, cases: list[Mapping[str, Any]]) -> list[Component]:
    """A captioned group of case passages, or nothing when there are none."""
    if not cases:
        return []
    passages = [
        _toolkit(f"{prefix}_{n}", "Passage", text=case["text"], **({"source": case["source"]} if case["source"] else {}))
        for n, case in enumerate(cases, start=1)
    ]
    return _group(prefix, heading, passages)


def _code_card(n: int, card: Mapping[str, Any], labels: list[str]) -> list[Component]:
    """One code: its definition and criteria, its cases, and the five actions (R2.1, R2.2)."""
    cid, data = f"card{n + 1}", f"/cards/{n}"
    body: list[Component] = [_basic(f"{cid}_definition", "Text", text=card["definition"])]
    if card["inclusion"]:
        body.append(_basic(f"{cid}_include", "Text", text=f"Include when: {card['inclusion']}"))
    if card["exclusion"]:
        body.append(_basic(f"{cid}_exclude", "Text", text=f"Exclude when: {card['exclusion']}"))
    typical = [c for c in card["cases"] if c["kind"] == "typical"]
    borderline = [c for c in card["cases"] if c["kind"] == "borderline"]
    groups = _cases(f"{cid}_typical", "Typical cases", typical) + _cases(f"{cid}_borderline", "Borderline cases", borderline)
    fields: list[Component] = [
        _toolkit(
            f"{cid}_action", "ChoiceGroup", legend="Your decision on this code", value=_bind(f"{data}/action"),
            options=[{"value": v, "label": label, "description": d} for v, label, d in _CODE_ACTIONS],
        ),
        _toolkit(f"{cid}_label", "TextField", label="New label (if rewording; optional)", value=_bind(f"{data}/label")),
        _toolkit(f"{cid}_reword", "TextField", label="New definition (if rewording)", multiline=True, value=_bind(f"{data}/definition")),
    ]
    others = [label for label in labels if label != card["code_label"]]
    if others:
        fields.append(_toolkit(
            f"{cid}_merge", "ChoiceGroup", legend="Merge into (if merging)", value=_bind(f"{data}/target"),
            options=[{"value": label, "label": label} for label in others],
        ))
    fields += [
        _toolkit(
            f"{cid}_split", "TextField", label="Parts (if splitting)", multiline=True, value=_bind(f"{data}/parts"),
            hint="One part per line: its label, a colon, then its definition.",
        ),
        _toolkit(f"{cid}_note", "TextField", label="Note (optional)", multiline=True, value=_bind(f"{data}/note")),
    ]
    save = _button(f"{cid}_save", "Save decision", "save_decision", {"card_id": card["card_id"], "decision": _bind(data)}, "primary")
    kids = [c["id"] for c in body] + [g["id"] for g in groups if g["component"] == "Column"] + [f["id"] for f in fields] + [save[0]["id"]]
    card_ = _decision_card(cid, f"/status/cards/{n}", card["code_label"], card["card_id"], "Needs your decision", kids)
    return [card_, *body, *groups, *fields, *save]


def _exclusivity_card() -> list[Component]:
    """The one question about the codebook as a whole (R2.4)."""
    question = _toolkit(
        "exclusivity_answer", "ChoiceGroup", legend="Are the codes mutually exclusive?", value=_bind("/exclusivity/answer"),
        options=[
            {"value": "yes", "label": "Yes", "description": "A passage takes one code at most."},
            {"value": "no", "label": "No", "description": "A passage can take several codes."},
        ],
    )
    save = _button("exclusivity_save", "Save answer", "answer_exclusive", {"exclusive": _bind("/exclusivity/answer")}, "primary")
    card = _decision_card(
        "exclusivity", "/status/exclusivity", "The codebook as a whole", "exclusivity", "Needs your answer",
        [question["id"], save[0]["id"]],
    )
    return [card, question, *save]


def _proposal_text(proposal: Mapping[str, Any]) -> str:
    codes = ", ".join(proposal["codes"]) or "No code applies"
    return f"{codes}. {proposal['rationale']}".strip()


def _coder(cid: str, heading: str, labels: list[str], codes: list[str]) -> list[Component]:
    tags = [
        _toolkit(f"{cid}_{m}", "CodeTag", text=label, tone=codes.index(label) % 6 + 1)
        for m, label in enumerate(labels, start=1)
    ] or [_basic(f"{cid}_none", "Text", text="No code")]
    return _group(cid, heading, tags)


def _ruling_card(n: int, card: Mapping[str, Any], desk: Mapping[str, Any], *, proposal: bool, rule: bool) -> list[Component]:
    """One disagreement: the chunk, each pass's codes and their entries (R3.1), the ruling
    (R3.3), an exclusion with its reason (R3.4), and, once released, the proposal and the
    rule question (R3.2, R3.6)."""
    cid, data, codes = f"card{n + 1}", f"/cards/{n}", desk["codes"]
    exclusive = bool(desk["exclusive"])
    sections: list[list[Component]] = []  # each section's first component is a child of the card
    sections.append([_toolkit(f"{cid}_chunk", "Passage", text=card["text"], **({"source": card["source"]} if card["source"] else {}))])
    sections.append(
        [_basic(f"{cid}_coders", "Row", children=[f"{cid}_a", f"{cid}_b"])]
        + _coder(f"{cid}_a", "First coding pass", card["coder_a"], codes)
        + _coder(f"{cid}_b", "Second coding pass", card["coder_b"], codes)
    )
    sections.append(_group(f"{cid}_entries", "Codebook entries", [
        _basic(f"{cid}_entry_{m}", "Text", text=f"{label}: {definition}")
        for m, (label, definition) in enumerate(card["entries"].items(), start=1)
    ]))
    if proposal and card["proposal"] is not None:
        sections.append([_toolkit(f"{cid}_proposal", "Provenance", by="model", label="Proposed resolution", text=_proposal_text(card["proposal"]))])
    options = [{"value": code, "label": code} for code in codes]
    if not exclusive:
        options.append({"value": NO_CODE, "label": "No code applies"})
    sections.append([_toolkit(
        f"{cid}_ruling", "ChoiceGroup", legend="Your ruling", multiple=not exclusive, options=options, value=_bind(f"{data}/codes"),
        hint="Choose one code." if exclusive else "Choose every code that applies, or No code applies.",
    )])
    if rule:
        sections.append([_toolkit(
            f"{cid}_rule", "ChoiceGroup", legend="Does this ruling state a rule?", value=_bind(f"{data}/is_rule"),
            hint="A rule becomes an amendment to the codebook, and later coding follows it.",
            options=[{"value": "yes", "label": "Yes"}, {"value": "no", "label": "No"}],
        )])
        sections.append([_toolkit(f"{cid}_rule_text", "TextField", label="The rule (if it states one)", multiline=True, value=_bind(f"{data}/rule_text"))])
    sections.append([_toolkit(f"{cid}_note", "TextField", label="Note (optional)", multiline=True, value=_bind(f"{data}/note"))])
    sections.append(_button(f"{cid}_save", "Save ruling", "save_decision", {"card_id": card["card_id"], "decision": _bind(data)}, "primary"))
    button = _button(f"{cid}_exclude_button", "Exclude this chunk", "exclude_chunk", {"card_id": card["card_id"], "reason": _bind(f"{data}/reason")})
    sections.append(_group(
        f"{cid}_exclude", "Or exclude this chunk from the analysis",
        [_toolkit(f"{cid}_reason", "TextField", label="Reason for excluding", required=True, value=_bind(f"{data}/reason")), button[0]],
        button[1:],
    ))
    title = f"Disagreement {n + 1} of {len(desk['cards'])}"
    card_ = _decision_card(cid, f"/status/cards/{n}", title, card["card_id"], "Needs your ruling", [s[0]["id"] for s in sections])
    return [card_, *(c for section in sections for c in section)]


def _frame(desk: Mapping[str, Any], queue: list[str], total: int, finish: str, counted: str) -> list[Component]:
    """What every desk has around its queue: progress, the actions, the tally, the colophon."""
    return [
        _basic("root", "Column", children=["progress", "queue", "actions", "tally", "byline"]),
        _toolkit(
            "progress", "Progress", total=total, done=_bind("/status/progress/done"),
            current=_bind("/status/progress/current"), label=counted,
        ),
        _basic("queue", "Column", children=queue),
        _basic("actions", "Row", children=["ratify", "copy"]),
        *_button("ratify", finish, "finish", {"desk_id": desk["desk_id"]}, "primary"),
        *_button("copy", "Copy decisions as JSON", "copy_json", {"desk_id": desk["desk_id"]}),
        _toolkit(
            "tally", "Tally", left=_bind("/status/progress/left"), total=total, noun="decisions", sticky=True,
            doneText="Every decision is made. Ratify when you are ready.",
        ),
        _toolkit("byline", "Byline", version=__version__, full=True),
    ]


def _rulings_codes(desk: Mapping[str, Any]) -> list[str]:
    """The codes a rulings desk rules with, refusing cards that carry a code outside them."""
    codes = list(desk["codes"])
    if NO_CODE in codes:
        raise ValueError(f"A code may not be called {NO_CODE!r}: the desk offers it as the ruling that no code applies.")
    for card in desk["cards"]:
        proposed = card["proposal"]["codes"] if card["proposal"] is not None else []
        outside = [label for label in dict.fromkeys([*card["coder_a"], *card["coder_b"], *proposed]) if label not in codes]
        if outside:
            raise ValueError(f"{card['card_id']} carries {', '.join(map(repr, outside))}, which is not among the desk's codes.")
    return codes


def _components(desk: Mapping[str, Any]) -> tuple[list[Component], dict[str, Any]]:
    """Every component of a desk, and the fields its data model starts with."""
    cards_ = desk["cards"]
    queue: list[Component] = []
    if desk["stage"] == "codebook":
        labels = [card["code_label"] for card in cards_]
        for n, card in enumerate(cards_):
            queue += _code_card(n, card, labels)
        queue += _exclusivity_card()
        fields = {
            "cards": [
                {"card_id": c["card_id"], "action": [], "label": "", "definition": "", "target": [], "parts": "", "note": ""}
                for c in cards_
            ],
            "exclusivity": {"answer": []},
        }
        finish, counted = "Ratify the codebook", "Decisions"
    else:
        _rulings_codes(desk)
        release = not desk.get("blind_first", True)
        for n, card in enumerate(cards_):
            queue += _ruling_card(n, card, desk, proposal=release, rule=False)
        fields = {
            "cards": [
                {"card_id": c["card_id"], "codes": [], "is_rule": [], "rule_text": "", "reason": "", "note": ""}
                for c in cards_
            ],
        }
        finish, counted = "Record the rulings", "Rulings"
    queue_ids = [c["id"] for c in queue if c["component"] == "DecisionCard"]
    return _frame(desk, queue_ids, len(queue_ids), finish, counted) + queue, fields


def _check_stage(desk: Mapping[str, Any]) -> None:
    if desk.get("stage") not in ("codebook", "rulings"):
        raise ValueError(f"A desk's stage is codebook or rulings, not {desk.get('stage')!r}.")


def _result(desk: Mapping[str, Any], decision: Mapping[str, Any]) -> str:
    """A decided card's one-line result."""
    if desk["stage"] == "codebook":
        action = decision.get("action", "")
        if action == "merge":
            return f"Merged into {decision.get('target', '')}"
        if action == "split":
            return f"Split into {len(decision.get('parts', []))} codes"
        return _CODE_RESULTS.get(action, str(action))
    if "exclude" in decision:
        return "Excluded"
    ruled = "No code applies" if decision.get("none_apply") else ", ".join(decision.get("codes", []))
    return f"{ruled} · states a rule" if decision.get("is_rule") else ruled


def _status(desk: Mapping[str, Any], saved: Mapping[str, Any], after: str | None) -> dict[str, Any]:
    """Which items are done, with their results, and which one is open: the first undecided
    item after ``after``, wrapping round, or the first when nothing has been decided."""
    decisions = saved.get("decisions", {})
    cards_ = desk["cards"]
    items: list[tuple[str, bool, str]] = []  # (id, done, result)
    for card in cards_:
        decision = decisions.get(card["card_id"])
        complete = decision is not None and (not differs(card, decision) or "is_rule" in decision)
        items.append((card["card_id"], complete, _result(desk, decision) if complete and decision is not None else ""))
    if desk["stage"] == "codebook":
        exclusive = saved.get("exclusive")
        answer = "" if exclusive is None else ("Mutually exclusive" if exclusive else "Not mutually exclusive")
        items.append(("exclusivity", exclusive is not None, answer))
    ids = [item[0] for item in items]
    start = ids.index(after) if after in ids else -1
    if after is not None and after in ids and not items[start][1]:
        current = start  # the decided item still needs an answer, so it stays open
    else:
        order = list(range(start + 1, len(items))) + list(range(0, start + 1))
        current = next((k for k in order if not items[k][1]), len(items))
    flags = [{"open": k == current, "done": done, "result": result} for k, (_, done, result) in enumerate(items)]
    done = sum(1 for item in items if item[1])
    status: dict[str, Any] = {"cards": flags[: len(cards_)], "progress": {"done": done, "current": current, "left": len(items) - done}}
    if desk["stage"] == "codebook":
        status["exclusivity"] = flags[-1]
    return status


def surface(desk: Mapping[str, Any]) -> list[Message]:
    """The desk as A2UI v1.0 messages for a renderer that starts empty: the surface, its
    components, and its initial data model, in which nothing is chosen (R1.8, R2.3).

    ``desk`` holds ``desk_id``, ``stage`` (``codebook`` or ``rulings``), ``title`` and
    ``cards`` as ``desk.cards`` builds them; a rulings desk also holds ``codes`` (the
    codebook in force), ``exclusive`` and ``blind_first``. Under blind-first no message
    carries a proposal (R3.2). The title travels in the data model for the page or app
    shell to show as its header.
    """
    _check_stage(desk)
    found, fields = _components(desk)
    sid = desk["desk_id"]
    value = {"desk_id": sid, "title": desk.get("title", ""), **fields, "status": _status(desk, {}, None)}
    return [
        {"version": _VERSION, "createSurface": {"surfaceId": sid, "catalogId": CATALOG_ID}},
        {"version": _VERSION, "updateComponents": {"surfaceId": sid, "components": found}},
        {"version": _VERSION, "updateDataModel": {"surfaceId": sid, "path": "/", "value": value}},
    ]


def after_decision(desk: Mapping[str, Any], saved: Mapping[str, Any], card_id: str) -> list[Message]:
    """The messages that follow saving the decision on ``card_id``: its card marked done
    with its result and the next undecided card opened, or, when a ruling departs from its
    proposal and the rule question is unanswered, the card kept open with the question
    (R3.6). Saving a ruling releases that card's proposal and no other (R3.9).

    ``saved`` is ``{"decisions": {card_id: decision}, "exclusive": bool | None}``, in the
    shape of the decisions document; ``card_id`` is ``exclusivity`` for the codebook's
    question.
    """
    _check_stage(desk)
    sid = desk["desk_id"]
    decisions = saved.get("decisions", {})
    by_id = {card["card_id"]: n for n, card in enumerate(desk["cards"])}
    messages: list[Message] = []
    if desk["stage"] == "codebook" and card_id == "exclusivity":
        if saved.get("exclusive") is None:
            raise ValueError("The exclusivity question has no saved answer.")
    elif card_id not in by_id:
        raise ValueError(f"{card_id} is not a card on this desk.")
    elif card_id not in decisions:
        raise ValueError(f"{card_id} has no saved decision.")
    elif desk["stage"] == "rulings":
        _rulings_codes(desk)
        n = by_id[card_id]
        card = desk["cards"][n]
        if card["proposal"] is not None:
            rebuilt = _ruling_card(n, card, desk, proposal=True, rule=differs(card, decisions[card_id]))
            messages.append({"version": _VERSION, "updateComponents": {"surfaceId": sid, "components": rebuilt}})
    status = _status(desk, saved, card_id)
    messages.append({"version": _VERSION, "updateDataModel": {"surfaceId": sid, "path": "/status", "value": status}})
    return messages


# ── Reading what the view sends ────────────────────────────────────────────────
#
# A save button's action carries its card's fields as the view holds them: choices as
# lists, text as typed. decision_from_action reads them into the decisions document's
# shape, which every surface sends and after_decision reads. It refuses only what has no
# shape there; whether a decision is complete and allowed is the decisions document's
# own check.

_YES_NO = {"yes": True, "no": False}


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _chosen(value: Any) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _yes_no(value: str, what: str) -> bool:
    if value not in _YES_NO:
        raise ValueError(f"{what} is answered yes or no, not {value!r}.")
    return _YES_NO[value]


def _split_parts(text: Any, card_id: str) -> list[dict[str, str]]:
    parts = []
    for line in _clean(text).splitlines():
        if not line.strip():
            continue
        label, colon, definition = line.partition(":")
        if not colon or not label.strip():
            raise ValueError(
                f"Each part of a split takes one line: its label, a colon, then its definition. "
                f"A part of {card_id} reads {line.strip()!r}."
            )
        parts.append({"label": label.strip(), "definition": definition.strip()})
    return parts


def _code_decision(view: Mapping[str, Any], card_id: str) -> dict[str, Any]:
    chosen = _chosen(view.get("action"))
    if not chosen:
        raise ValueError(f"Choose what to do with {card_id} before saving.")
    decision: dict[str, Any] = {"action": chosen[0]}
    if chosen[0] == "reword":
        decision["definition"] = _clean(view.get("definition"))
        if _clean(view.get("label")):
            decision["label"] = _clean(view.get("label"))
    elif chosen[0] == "merge":
        targets = _chosen(view.get("target"))
        decision["target"] = targets[0] if targets else ""
    elif chosen[0] == "split":
        decision["parts"] = _split_parts(view.get("parts"), card_id)
    return decision


def _ruling_decision(view: Mapping[str, Any], card_id: str) -> dict[str, Any]:
    codes = _chosen(view.get("codes"))
    if not codes:
        raise ValueError(f"Choose a ruling for {card_id} before saving, or exclude the chunk.")
    if NO_CODE in codes:
        if len(codes) > 1:
            raise ValueError(f"The ruling on {card_id} chooses No code applies alongside a code; choose one or the other.")
        decision: dict[str, Any] = {"none_apply": True}
    else:
        decision = {"codes": codes}
    answer = _chosen(view.get("is_rule"))
    if answer:
        decision["is_rule"] = _yes_no(answer[0], "Whether a ruling states a rule")
    if _clean(view.get("rule_text")):
        decision["rule_text"] = _clean(view.get("rule_text"))
    return decision


def decision_from_action(desk: Mapping[str, Any], name: str, context: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    """The card and decision an action from the desk's view records, in the decisions
    document's shape: ``save_decision`` on any card, ``exclude_chunk`` on a rulings card,
    and ``answer_exclusive`` for the codebook's question (card ``exclusivity``, decision
    ``{"exclusive": bool}``). ``context`` is the action's context as the renderer sends
    it, with its bindings resolved.
    """
    _check_stage(desk)
    stage = desk["stage"]
    if name == "answer_exclusive" and stage == "codebook":
        answer = _chosen(context.get("exclusive"))
        if not answer:
            raise ValueError("Choose an answer to whether the codes are mutually exclusive before saving.")
        return "exclusivity", {"exclusive": _yes_no(answer[0], "Whether the codes are mutually exclusive")}
    if name not in ("save_decision", "exclude_chunk") or (name == "exclude_chunk" and stage != "rulings"):
        raise ValueError(f"{name!r} is not an action that records a decision on a {stage} desk.")
    card_id = _clean(context.get("card_id"))
    if card_id not in {card["card_id"] for card in desk["cards"]}:
        raise ValueError(f"{card_id} is not a card on this desk.")
    if name == "exclude_chunk":
        return card_id, {"exclude": {"reason": _clean(context.get("reason"))}}
    view = context.get("decision")
    view = view if isinstance(view, Mapping) else {}
    decision = _code_decision(view, card_id) if stage == "codebook" else _ruling_decision(view, card_id)
    if _clean(view.get("note")):
        decision["note"] = _clean(view.get("note"))
    return card_id, decision
