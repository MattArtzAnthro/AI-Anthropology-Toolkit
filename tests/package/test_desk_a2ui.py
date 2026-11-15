"""The desk's A2UI messages: the pinned v1.0 schema and the two catalogs they draw on."""

import copy
import json
import os
import re
import shutil
import subprocess  # nosec B404 - runs node on the repository's own renderer harness
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
DESK = REPO / "src" / "ai_anthro_toolkit" / "desk"
APP = DESK / "app"
NODE_SCHEMAS = APP / "node_modules" / "@a2ui" / "web_core" / "src" / "v1_0" / "schemas"

# Catalog identifiers as the design states them (specs/ratification-desk/design.md).
CATALOG_ID = "https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/catalogs/desk/v1"
BASIC_CATALOG_ID = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"

# The design system's components the toolkit catalog carries (design.md, "The catalog").
TOOLKIT_COMPONENTS = {
    "DecisionCard", "Passage", "Provenance", "ChoiceGroup", "Step", "Status",
    "CodeTag", "Progress", "Notice", "Tally", "TextField", "Byline",
}


def _surface(*components: dict, catalog: str = CATALOG_ID) -> list[dict]:
    """A createSurface and an updateComponents for one surface holding these components."""
    return [
        {"version": "v1.0", "createSurface": {"surfaceId": "desk", "catalogId": catalog}},
        {"version": "v1.0", "updateComponents": {"surfaceId": "desk", "components": list(components)}},
    ]


ROOT = {"id": "root", "component": "Column", "catalogId": BASIC_CATALOG_ID, "children": ["p"]}
PASSAGE = {"id": "p", "component": "Passage", "text": "We kept the seed in the rafters.", "source": "Interview 3"}


def _validate(messages, **kw):
    from ai_anthro_toolkit.desk import a2ui

    return a2ui.validate(messages, **kw)


class TestValidate(unittest.TestCase):
    def test_r1_8_unknown_component_fails_validation(self):
        """R1.8: a component that is in neither catalog fails, and the problem names it."""
        problems = _validate(_surface(ROOT, {"id": "p", "component": "Gauge", "value": 3}))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'Gauge'", problems[0])
        self.assertIn("'p'", problems[0])

    def test_r1_8_a_desk_of_both_catalogs_validates(self):
        self.assertEqual(_validate(_surface(ROOT, PASSAGE)), [])

    def test_r1_8_a_component_is_checked_against_the_catalog_it_names(self):
        """A toolkit component claimed under the basic catalog is not in that catalog."""
        passage = dict(PASSAGE, catalogId=BASIC_CATALOG_ID)
        problems = _validate(_surface(ROOT, passage))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'Passage'", problems[0])
        self.assertIn(BASIC_CATALOG_ID, problems[0])

    def test_r1_8_the_surface_catalog_is_the_default(self):
        """Without its own catalogId a component belongs to its surface's catalog."""
        bare_column = {k: v for k, v in ROOT.items() if k != "catalogId"}
        toolkit_passage = dict(PASSAGE, catalogId=CATALOG_ID)
        self.assertEqual(_validate(_surface(bare_column, toolkit_passage, catalog=BASIC_CATALOG_ID)), [])
        problems = _validate(_surface(bare_column, PASSAGE))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'Column'", problems[0])

    def test_r1_8_an_unknown_catalog_fails(self):
        problems = _validate(_surface(ROOT, dict(PASSAGE, catalogId="https://example.org/other")))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("https://example.org/other", problems[0])

    def test_r1_8_a_missing_required_property_fails(self):
        problems = _validate(_surface(ROOT, {"id": "p", "component": "Passage"}))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'text'", problems[0])

    def test_r1_8_an_undeclared_property_fails(self):
        problems = _validate(_surface(ROOT, dict(PASSAGE, colour="#ff0000")))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("colour", problems[0])

    def test_r1_8_a_wrongly_typed_property_fails(self):
        tally = {"id": "t", "component": "Tally", "left": "three", "total": 12}
        problems = _validate(_surface(dict(ROOT, children=["t"]), tally))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'t'", problems[0])
        self.assertIn("left", problems[0])

    def test_r1_8_basic_components_are_checked_too(self):
        problems = _validate(_surface({"id": "root", "component": "Column", "catalogId": BASIC_CATALOG_ID}))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'children'", problems[0])

    def test_r1_8_the_envelope_is_checked(self):
        """A message without the version, of the wrong version, or of no known kind fails."""
        good = _surface(ROOT, PASSAGE)
        for broken in (
            [{k: v for k, v in good[0].items() if k != "version"}] + good[1:],
            [dict(good[0], version="v0.9")] + good[1:],
            [good[0], {"version": "v1.0", "replaceEverything": {}}],
        ):
            with self.subTest(broken=broken):
                problems = _validate(broken)
                self.assertTrue(problems)
                self.assertTrue(all(p.startswith("message ") for p in problems), problems)

    def test_r1_8_components_inside_create_surface_are_checked(self):
        msg = {"version": "v1.0", "createSurface": {"surfaceId": "s", "catalogId": CATALOG_ID,
                                                     "components": [{"id": "root", "component": "Gauge"}]}}
        problems = _validate([msg])
        self.assertEqual(problems, [f"message 0, component 'root': 'Gauge' is not in the catalog {CATALOG_ID}"])
        rootless = {"version": "v1.0", "createSurface": {"surfaceId": "s", "catalogId": CATALOG_ID,
                                                          "components": [PASSAGE]}}
        self.assertEqual(_validate([rootless]), ["message 0: surface 's' has no component 'root'"])

    def test_r1_8_an_update_needs_its_surface_created_first(self):
        """As in the renderer, an update for a surface the messages never created fails."""
        problems = _validate(_surface(ROOT, PASSAGE)[1:])
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'desk'", problems[0])

    def test_r1_8_a_component_with_no_catalog_fails(self):
        """A surface created without a catalogId gives its components none; each must name one."""
        msg = {"version": "v1.0", "createSurface": {"surfaceId": "s", "components": [ROOT, PASSAGE]}}
        problems = _validate([msg])
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'p'", problems[0])
        self.assertIn("no catalog", problems[0])

    def test_r1_8_messages_without_components_are_checked_by_the_envelope_alone(self):
        data = {"version": "v1.0", "updateDataModel": {"surfaceId": "desk", "path": "/note", "value": "x"}}
        self.assertEqual(_validate([*_surface(ROOT, PASSAGE), data]), [])
        self.assertTrue(_validate([dict(data, updateDataModel={"value": "x", "colour": 1})]))

    def test_r1_8_a_nested_problem_says_where(self):
        """A problem inside a component names the path to it; a top-level one names none."""
        choices = {"id": "c", "component": "ChoiceGroup", "legend": "Keep?", "value": [],
                   "options": [{"value": "keep", "label": "Keep"}, {"value": "drop"}]}
        problems = _validate(_surface(ROOT, choices))
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("(at options/1)", problems[0])
        missing = _validate(_surface(ROOT, {"id": "p", "component": "Passage"}))
        self.assertNotIn("(at", missing[0])

    def test_r1_8_every_message_is_checked_after_a_bad_one(self):
        """One bad message does not stop the check: each later one is reported too."""
        good = _surface(ROOT, PASSAGE)
        data = {"version": "v1.0", "updateDataModel": {"surfaceId": "desk", "path": "/n", "value": 1}}
        orphan = {"version": "v1.0", "updateComponents": {"surfaceId": "other", "components": [PASSAGE]}}
        gauge = {"version": "v1.0", "updateComponents": {
            "surfaceId": "desk", "components": [{"id": "g", "component": "Gauge"}]}}
        inline_gauge = {"version": "v1.0", "createSurface": {"surfaceId": "s2", "catalogId": CATALOG_ID,
                                                              "components": [{"id": "root", "component": "Gauge"}]}}
        problems = _validate([{"createSurface": {"surfaceId": "x"}}, good[0], data, orphan, good[1], gauge,
                              good[0], inline_gauge])
        self.assertEqual([p.split(":")[0].split(",")[0] for p in problems],
                         ["message 0", "message 3", "message 5", "message 6", "message 7"])

    def test_r1_8_component_ids_are_identifiers(self):
        """The renderer takes only UAX #31 identifiers as component IDs."""
        for bad in ("p-1", "1p", "p 1", ""):
            with self.subTest(id=bad):
                problems = _validate(_surface(dict(ROOT, children=[bad]), dict(PASSAGE, id=bad)))
                self.assertTrue(any(repr(bad) in p and "identifier" in p for p in problems), problems)
        self.assertEqual(_validate(_surface(dict(ROOT, children=["passage_1"]), dict(PASSAGE, id="passage_1"))), [])

    def test_r1_8_every_component_of_an_update_is_checked(self):
        """One bad component does not hide the next: each is reported."""
        problems = _validate(_surface(ROOT, dict(PASSAGE, id="p-1"), dict(PASSAGE, id="q", colour="red"),
                                      PASSAGE, PASSAGE, {"id": "g", "component": "Gauge"}))
        self.assertEqual(
            [p.split(":")[0] for p in problems],
            ["message 1, component 'p-1'", "message 1, component 'q'", "message 1, component 'p'",
             "message 1, component 'g'"],
        )

    def test_r1_8_references_form_no_cycle(self):
        """As in the renderer, a component may be shared but never contain itself."""
        b = BASIC_CATALOG_ID
        col = lambda cid, children: {"id": cid, "component": "Column", "catalogId": b, "children": children}  # noqa: E731
        text = {"id": "x", "component": "Text", "catalogId": b, "text": "shared"}
        self.assertEqual(_validate(_surface(col("root", ["a", "c"]), col("a", ["x"]), col("c", ["x"]), text)), [])
        self.assertEqual(_validate(_surface(col("root", ["a"]), col("a", ["root"]))),
                         ["message 1, component 'root': is part of a cycle of references"])
        self.assertEqual(_validate(_surface(col("root", ["a"]), col("a", ["a"]))),
                         ["message 1, component 'a': is part of a cycle of references"])

    def test_r1_8_an_id_appears_once_per_update(self):
        problems = _validate(_surface(ROOT, PASSAGE, PASSAGE))
        self.assertEqual(problems, ["message 1, component 'p': appears twice in one update"])

    def test_r1_8_a_surface_has_a_root(self):
        problems = _validate(_surface(PASSAGE))
        self.assertEqual(problems, ["message 1: surface 'desk' has no component 'root'"])

    def test_r1_8_every_reference_names_a_component(self):
        problems = _validate(_surface(dict(ROOT, children=["p", "zzz"]), PASSAGE))
        self.assertEqual(problems, ["message 1, component 'root': refers to 'zzz', which does not exist"])

    def test_r1_8_every_component_hangs_from_the_root(self):
        loose = dict(PASSAGE, id="loose")
        problems = _validate(_surface(ROOT, PASSAGE, loose))
        self.assertEqual(problems, ["message 1, component 'loose': is not reachable from 'root'"])

    def test_r1_8_references_inside_containers_count(self):
        """A Card's child, a Button's child and a template's componentId are references too."""
        b = BASIC_CATALOG_ID
        components = [
            {"id": "root", "component": "Column", "catalogId": b, "children": ["card", "list"]},
            {"id": "card", "component": "Card", "catalogId": b, "child": "go"},
            {"id": "go", "component": "Button", "catalogId": b, "child": "label", "action": {"event": {"name": "go"}}},
            {"id": "label", "component": "Text", "catalogId": b, "text": "Go"},
            {"id": "list", "component": "List", "catalogId": b,
             "children": {"componentId": "row", "path": "/rows"}},
            {"id": "row", "component": "Text", "catalogId": b, "text": {"@path": "name"}},
        ]
        self.assertEqual(_validate(_surface(*components)), [])
        self.assertTrue(_validate(_surface(*components[:3], *components[4:])))  # the label is gone

    def test_r1_8_an_absent_optional_reference_is_fine(self):
        """A Notice need not carry controls: no children, nothing to resolve."""
        notice = {"id": "n", "component": "Notice", "title": "Saved."}
        self.assertEqual(_validate(_surface(dict(ROOT, children=["n"]), notice)), [])

    def test_r1_8_references_inside_lists_of_objects_count(self):
        """A Tabs component's tabs each name a child; only that key is a reference."""
        tabs = {"id": "root", "component": "Tabs", "catalogId": BASIC_CATALOG_ID,
                "tabs": [{"title": "One", "child": "p"}, {"title": "q", "child": "q"}]}
        q = dict(PASSAGE, id="q")
        self.assertEqual(_validate(_surface(tabs, PASSAGE, q)), [])
        tabs["tabs"][1]["child"] = "zzz"
        self.assertEqual(
            _validate(_surface(tabs, PASSAGE)),
            ["message 1, component 'root': refers to 'zzz', which does not exist"],
        )

    def test_r1_8_only_the_messages_a_desk_sends(self):
        """A desk creates, updates and deletes surfaces; a function call is refused."""
        call = {"version": "v1.0", "agentFunctionResponse": {"functionCallId": "c1", "value": 1}}
        problems = _validate([*_surface(ROOT, PASSAGE), call])
        self.assertEqual(problems, ["message 2: agentFunctionResponse is not a message the desk sends"])

    def test_r1_8_updates_build_on_the_surface(self):
        """A later update may refer to components an earlier one sent, and replaces by ID."""
        first = _surface(dict(ROOT, children=["p", "q"]), PASSAGE, dict(PASSAGE, id="q"))
        later = {"version": "v1.0", "updateComponents": {"surfaceId": "desk", "components": [
            dict(PASSAGE, text="Revised.")]}}
        self.assertEqual(_validate([*first, later]), [])
        cut = {"version": "v1.0", "updateComponents": {"surfaceId": "desk", "components": [
            dict(ROOT, children=["p"])]}}
        self.assertEqual(_validate([*first, cut]), ["message 2, component 'q': is not reachable from 'root'"])

    def test_r1_8_surfaces_are_created_once_and_end_when_deleted(self):
        good = _surface(ROOT, PASSAGE)
        self.assertEqual(_validate([good[0], *good]), ["message 1: surface 'desk' already exists"])
        delete = {"version": "v1.0", "deleteSurface": {"surfaceId": "desk"}}
        problems = _validate([*good, delete, good[1]])
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("message 3: surface 'desk'", problems[0])
        self.assertEqual(_validate([*good, delete, *good]), [])
        self.assertEqual(_validate([*good, dict(delete, deleteSurface={"surfaceId": "other"})]), [])

    def test_r1_8_schemas_are_never_fetched(self):
        """Every schema resolves from the package; a reference to anything else is
        refused, never fetched over the network."""
        from referencing.exceptions import Unresolvable

        from ai_anthro_toolkit.desk import a2ui

        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("fetched")) as urlopen:
            self.assertEqual(_validate(_surface(ROOT, PASSAGE)), [])
            resolver = a2ui._registry({"$defs": {}}).resolver()  # noqa: SLF001 - the one place refs resolve
            with self.assertRaises(Unresolvable):
                resolver.lookup("https://example.org/remote.json")
        urlopen.assert_not_called()

    def test_r1_8_problems_name_the_message(self):
        problems = _validate(_surface(ROOT, {"id": "p", "component": "Gauge"}))
        self.assertTrue(problems[0].startswith("message 1, component 'p'"), problems)

    def test_r1_8_validate_does_not_change_the_messages(self):
        messages = _surface(ROOT, PASSAGE)
        before = copy.deepcopy(messages)
        _validate(messages)
        self.assertEqual(messages, before)


class TestToolkitCatalog(unittest.TestCase):
    def _catalog(self) -> dict:
        return json.loads((DESK / "catalog.json").read_text(encoding="utf-8"))

    def test_r1_8_catalog_is_a_valid_catalog_definition(self):
        from ai_anthro_toolkit.desk import a2ui

        self.assertEqual(a2ui.catalog_problems(self._catalog()), [])

    def test_r1_8_catalog_definition_check_can_fail(self):
        from ai_anthro_toolkit.desk import a2ui

        broken = self._catalog()
        del broken["catalogId"]
        self.assertTrue(a2ui.catalog_problems(broken))
        broken = self._catalog()
        broken["components"]["Surface"] = {"type": "object"}
        self.assertTrue(a2ui.catalog_problems(broken))

    def test_r1_8_catalog_names_the_design_system_components(self):
        catalog = self._catalog()
        self.assertEqual(catalog["catalogId"], CATALOG_ID)
        self.assertEqual(set(catalog["components"]), TOOLKIT_COMPONENTS)
        refs = {one["$ref"] for one in catalog["$defs"]["anyComponent"]["oneOf"]}
        self.assertEqual(refs, {f"#/components/{name}" for name in TOOLKIT_COMPONENTS})

    def test_r1_8_each_component_names_itself(self):
        for name, schema in self._catalog()["components"].items():
            with self.subTest(component=name):
                body = next(s for s in [schema, *schema.get("allOf", [])] if "properties" in s)
                self.assertEqual(body["properties"]["component"], {"const": name})
                self.assertIn("component", body["required"])

    def test_r1_8_catalog_ids_match_the_package(self):
        from ai_anthro_toolkit import desk

        self.assertEqual(desk.CATALOG_ID, CATALOG_ID)
        self.assertEqual(desk.BASIC_CATALOG_ID, BASIC_CATALOG_ID)


def _node_or_skip(test: unittest.TestCase) -> str:
    """node, with the renderer's packages installed; a skip, or a failure where required."""
    node = shutil.which("node")
    reason = None if node else "node is not installed"
    if node and not (APP / "node_modules" / "@a2ui" / "web_core").is_dir():
        reason = "the renderer's packages are not installed (npm ci in desk/app)"
    if reason:
        if os.environ.get("AAT_REQUIRE_BROWSER") == "1":
            test.fail(f"AAT_REQUIRE_BROWSER is set and {reason}")
        test.skipTest(reason)
    assert node is not None
    return node


def _node(node: str, script: list[str], stdin: str = "") -> str:
    return subprocess.run(  # nosec B603 - fixed arguments, no shell
        [node, *script], input=stdin, capture_output=True, text=True, timeout=60, check=True, cwd=APP,
    ).stdout


_B = BASIC_CATALOG_ID
_DELETE = {"version": "v1.0", "deleteSurface": {"surfaceId": "desk"}}
_THEMED = [
    {"id": "root", "component": "Column", "catalogId": _B, "children": ["t", "c", "b", "card", "field", "pick", "p"]},
    {"id": "pick", "component": "ChoicePicker", "catalogId": _B, "options": [{"label": "Keep", "value": "keep"}],
     "value": {"@path": "/pick"}},
    {"id": "t", "component": "Text", "catalogId": _B, "text": "Plain text"},
    {"id": "c", "component": "Text", "catalogId": _B, "text": "A caption", "variant": "caption"},
    {"id": "bl", "component": "Text", "catalogId": _B, "text": "Go"},
    {"id": "b", "component": "Button", "catalogId": _B, "child": "bl", "variant": "primary",
     "action": {"event": {"name": "go"}}},
    {"id": "card", "component": "Card", "catalogId": _B, "child": "ct"},
    {"id": "ct", "component": "Text", "catalogId": _B, "text": "Inside a card"},
    {"id": "field", "component": "TextField", "catalogId": _B, "label": "A note", "value": {"@path": "/note"}},
    PASSAGE,
]

# Batches the renderer and the validator must judge alike: (name, messages).
CORPUS = [
    ("a desk of both catalogs", _surface(ROOT, PASSAGE)),
    ("basic components with references", _surface(*_THEMED)),
    ("tabs naming their children", _surface(
        {"id": "root", "component": "Tabs", "catalogId": _B, "tabs": [{"title": "One", "child": "p"}]}, PASSAGE)),
    ("a tab naming a missing child", _surface(
        {"id": "root", "component": "Tabs", "catalogId": _B, "tabs": [{"title": "One", "child": "zzz"}]}, PASSAGE)),
    ("a child shared by two parents", _surface(
        dict(ROOT, children=["a", "c"]), {"id": "a", "component": "Column", "catalogId": _B, "children": ["p"]},
        {"id": "c", "component": "Column", "catalogId": _B, "children": ["p"]}, PASSAGE)),
    ("a cycle", _surface(dict(ROOT, children=["a"]),
                         {"id": "a", "component": "Column", "catalogId": _B, "children": ["root"]})),
    ("a component containing itself", _surface(dict(ROOT, children=["root"]))),
    ("deleting a surface that was never made", [*_surface(ROOT, PASSAGE),
                                                {"version": "v1.0", "deleteSurface": {"surfaceId": "other"}}]),
    ("a list template", _surface(dict(ROOT, children=["l"]), {"id": "l", "component": "List", "catalogId": _B,
                                 "children": {"componentId": "p", "path": "/rows"}}, PASSAGE)),
    ("a data model update", [*_surface(ROOT, PASSAGE),
                             {"version": "v1.0", "updateDataModel": {"surfaceId": "desk", "path": "/n", "value": 1}}]),
    ("a later update replacing a component", [*_surface(ROOT, PASSAGE), _surface(dict(PASSAGE, text="New."))[1]]),
    ("a surface deleted and made again", [*_surface(ROOT, PASSAGE), _DELETE, *_surface(ROOT, PASSAGE)]),
    ("an unknown component", _surface(ROOT, {"id": "p", "component": "Gauge"})),
    ("a toolkit component in the basic catalog", _surface(ROOT, dict(PASSAGE, catalogId=_B))),
    ("a basic component in the toolkit catalog", _surface({k: v for k, v in ROOT.items() if k != "catalogId"}, PASSAGE)),
    ("a missing required property", _surface(ROOT, {"id": "p", "component": "Passage"})),
    ("an undeclared property", _surface(ROOT, dict(PASSAGE, colour="red"))),
    ("a layout weight on a toolkit component", _surface(ROOT, dict(PASSAGE, weight=1))),
    ("a wrongly typed property", _surface(ROOT, dict(PASSAGE, text=7))),
    ("a hyphenated id", _surface(dict(ROOT, children=["p-1"]), dict(PASSAGE, id="p-1"))),
    ("an id starting with a digit", _surface(dict(ROOT, children=["1p"]), dict(PASSAGE, id="1p"))),
    ("a duplicate id", _surface(ROOT, PASSAGE, PASSAGE)),
    ("no root", _surface(PASSAGE)),
    ("a dangling child", _surface(dict(ROOT, children=["p", "zzz"]), PASSAGE)),
    ("an orphan", _surface(ROOT, PASSAGE, dict(PASSAGE, id="loose"))),
    ("an update after delete", [*_surface(ROOT, PASSAGE), _DELETE, _surface(ROOT, PASSAGE)[1]]),
    ("a surface created twice", [_surface(ROOT)[0], *_surface(ROOT, PASSAGE)]),
    ("an update with no surface", _surface(ROOT, PASSAGE)[1:]),
    ("a message of the wrong version", [dict(_surface(ROOT)[0], version="v0.9")]),
]


class TestRendererAgrees(unittest.TestCase):
    """R1.8: the server's check and the bundled renderer's own strict check agree."""

    def test_r1_8_validator_and_renderer_agree(self):
        node = _node_or_skip(self)
        verdicts = json.loads(_node(node, ["scripts/check-messages.mjs"], json.dumps([b for _, b in CORPUS])))
        for (name, batch), renderer_error in zip(CORPUS, verdicts, strict=True):
            with self.subTest(case=name):
                problems = _validate(batch)
                self.assertEqual(
                    problems == [], renderer_error is None,
                    f"validator: {problems or 'valid'}; renderer: {renderer_error or 'valid'}",
                )

    def test_r1_8_the_corpus_has_both_verdicts(self):
        """The agreement check proves something only if some batches fail and some pass."""
        outcomes = {_validate(batch) == [] for _, batch in CORPUS}
        self.assertEqual(outcomes, {True, False})

    def test_r1_8_catalog_matches_the_renderer_schemas(self):
        """Each toolkit component the renderer knows takes exactly the properties
        catalog.json declares, with the same ones required."""
        node = _node_or_skip(self)
        shapes = json.loads(_node(node, ["--input-type=module", "-e", _API_SHAPES]))
        catalog = json.loads((DESK / "catalog.json").read_text(encoding="utf-8"))
        self.assertTrue(shapes)
        for name, shape in shapes.items():
            with self.subTest(component=name):
                entry = catalog["components"][name]
                props: dict = {}
                required: set = set()
                for part in [entry, *entry.get("allOf", [])]:
                    props.update(part.get("properties", {}))
                    required.update(part.get("required", []))
                props.pop("component")
                required.discard("component")
                self.assertEqual(set(props), set(shape["properties"]))
                self.assertEqual(required, set(shape["required"]))


# Prints each toolkit API's property names and required ones, from its zod schema.
_API_SHAPES = """
import { TOOLKIT_APIS } from './src/apis.js';
const out = {};
for (const api of TOOLKIT_APIS) {
  const shape = api.schema.shape;
  out[api.name] = {
    properties: Object.keys(shape),
    required: Object.keys(shape).filter((k) => !shape[k].isOptional()),
  };
}
console.log(JSON.stringify(out));
"""

# How a design-system prop (index.d.ts) becomes a catalog property: React-only props
# drop out, event handlers become A2UI actions, and children become text or child lists.
_REACT_ONLY = {"onChange", "onSelect", "id", "name", "defaultValue", "className"}
_RENAMED = {"onNext": "next"}
_CHILDREN_AS = {
    "Passage": "text", "Provenance": "text", "Status": "text", "CodeTag": "text", "Notice": "children",
    "Step": "children", "DecisionCard": "children", "Tally": None,
}
_ADDED = {"DecisionCard": {"change"}, "TextField": {"value"}, "ChoiceGroup": set(), "Notice": {"text"}}


class TestCatalogFollowsTheDesignSystem(unittest.TestCase):
    def test_r1_8_catalog_props_follow_index_d_ts(self):
        """Each catalog component carries its design-system component's props, renamed
        for A2UI as the table above states; a prop added to or dropped from either fails."""
        dts = (REPO / "design" / "system" / "components" / "index.d.ts").read_text(encoding="utf-8")
        catalog = json.loads((DESK / "catalog.json").read_text(encoding="utf-8"))
        for name in sorted(TOOLKIT_COMPONENTS):
            with self.subTest(component=name):
                m = re.search(rf"export interface {name}Props(?: extends [^{{]+)? \{{(.*?)\}}\n", dts, re.S)
                self.assertIsNotNone(m, f"no {name}Props in index.d.ts")
                assert m is not None
                body = re.sub(r"/\*\*.*?\*/", "", m.group(1), flags=re.S)
                expected = set()
                for prop in re.findall(r"(\w+)\??:", body):
                    if prop in _REACT_ONLY:
                        continue
                    if prop == "children":
                        if _CHILDREN_AS.get(name):
                            expected.add(_CHILDREN_AS[name])
                        continue
                    expected.add(_RENAMED.get(prop, prop))
                expected |= _ADDED.get(name, set())
                entry = catalog["components"][name]
                props: set = set()
                for part in [entry, *entry.get("allOf", [])]:
                    props |= set(part.get("properties", {}))
                self.assertEqual(props - {"component"}, expected)


class TestVendoredSchemas(unittest.TestCase):
    FILES = ("agent_to_renderer.json", "common_types.json", "catalog_definition.json", "catalogs/basic/catalog.json")

    def test_r1_8_vendored_schemas_are_the_pinned_release(self):
        """The schemas shipped with the package are the ones in the pinned @a2ui/web_core."""
        lock = json.loads((DESK / "app" / "package-lock.json").read_text(encoding="utf-8"))
        pinned = lock["packages"]["node_modules/@a2ui/web_core"]["version"]
        vendored = (DESK / "VENDORED.md").read_text(encoding="utf-8")
        self.assertIn(f"| @a2ui/web_core | {pinned} | Apache-2.0 |", vendored)
        self.assertTrue((DESK / "a2ui_schema" / "LICENSE").is_file())
        if not NODE_SCHEMAS.is_dir():
            self.skipTest("node_modules not installed (npm ci in desk/app)")
        for name in self.FILES:
            with self.subTest(file=name):
                self.assertEqual(
                    (DESK / "a2ui_schema" / name).read_bytes(), (NODE_SCHEMAS / name).read_bytes()
                )

    def test_r1_8_schemas_ship_as_package_data(self):
        from importlib import resources

        root = resources.files("ai_anthro_toolkit.desk")
        for name in ("catalog.json", *(f"a2ui_schema/{f}" for f in self.FILES)):
            with self.subTest(file=name):
                self.assertTrue(root.joinpath(name).is_file())
        try:
            import tomllib
        except ImportError:  # pragma: no cover - Python 3.10
            self.skipTest("tomllib needs Python 3.11")
        data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        globs = data["tool"]["setuptools"]["package-data"]["ai_anthro_toolkit.desk"]
        shipped = [DESK / "catalog.json", DESK / "VENDORED.md", *(DESK / "a2ui_schema").rglob("*")]
        for path in (p for p in shipped if p.is_file()):
            rel = path.relative_to(DESK).as_posix()
            with self.subTest(file=rel):
                self.assertTrue(any(PurePosixPath(rel).match(g) for g in globs), f"{rel} is not package data")


if __name__ == "__main__":
    unittest.main()
