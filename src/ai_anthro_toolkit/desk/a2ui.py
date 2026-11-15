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

from ai_anthro_toolkit.desk import BASIC_CATALOG_ID, CATALOG_ID

__all__ = ["catalog_problems", "validate"]

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
