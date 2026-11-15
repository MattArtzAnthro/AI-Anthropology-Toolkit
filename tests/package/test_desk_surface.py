"""A desk as A2UI v1.0 messages: what each card shows, what it offers, and what it leaves unset."""

import json
import re
import unittest

from ai_anthro_toolkit import __version__
from ai_anthro_toolkit.desk import a2ui, cards
from tests.package.desk_helpers import codebook_desk, rulings_desk
from tests.package.desk_helpers import load as _load

CODE_ACTIONS = ["adopt", "reword", "merge", "split", "delete"]


def components(messages) -> dict[str, dict]:
    """Every component the messages define, by ID; a later definition replaces an earlier one."""
    found: dict[str, dict] = {}
    for message in messages:
        body = message.get("updateComponents") or message.get("createSurface") or {}
        for component in body.get("components", []):
            found[component["id"]] = component
    return found


def apply_data(data: dict, messages) -> dict:
    """The data model after the messages' updates land on ``data``, as a renderer keeps
    what the researcher has filled in while the server updates other paths."""
    data = json.loads(json.dumps(data))
    for message in messages:
        update = message.get("updateDataModel")
        if update is None:
            continue
        path = update.get("path", "/")
        if path in ("", "/"):
            data = json.loads(json.dumps(update["value"]))
        else:
            set_path(data, path, json.loads(json.dumps(update["value"])))
    return data


def data_model(messages) -> dict:
    """The data model after the messages."""
    return apply_data({}, messages)


def set_path(data: dict, path: str, value) -> None:
    """Set what a JSON pointer names, as a renderer does when a field changes."""
    keys = path.strip("/").split("/")
    target = data
    for key in keys[:-1]:
        target = target[int(key)] if isinstance(target, list) else target[key]
    if isinstance(target, list):
        target[int(keys[-1])] = value
    else:
        target[keys[-1]] = value


def resolve(value, data):
    """A property's value: a literal, or what its {"@path": ...} binding points at."""
    if isinstance(value, dict) and "@path" in value:
        target = data
        for key in value["@path"].strip("/").split("/"):
            target = target[int(key)] if isinstance(target, list) else target[key]
        return target
    return value


def children(component) -> list[str]:
    kids = component.get("children", [])
    kids = list(kids) if isinstance(kids, list) else []
    if "child" in component:
        kids.append(component["child"])
    return kids


def subtree(found, root_id) -> list[str]:
    """The IDs under a component, itself included, in document order."""
    order, todo = [], [root_id]
    while todo:
        cid = todo.pop(0)
        order.append(cid)
        todo[0:0] = children(found[cid])
    return order


def texts(found, root_id, data) -> list[str]:
    """Every string a reader sees in a subtree: titles, text, legends, labels, options."""
    seen = []
    for cid in subtree(found, root_id):
        component = found[cid]
        for key in ("title", "text", "source", "legend", "label", "hint"):
            if key in component:
                seen.append(resolve(component[key], data))
        for option in component.get("options", []):
            seen.append(option["label"])
    return seen


def card_component(found, card_id) -> str:
    """The ID of the DecisionCard whose save action names this card."""
    for cid, component in found.items():
        if component["component"] != "DecisionCard":
            continue
        for kid in subtree(found, cid):
            action = found[kid].get("action", {}).get("event", {})
            if action.get("name") == "save_decision" and action["context"]["card_id"] == card_id:
                return cid
    raise AssertionError(f"no card saves {card_id}")


def bindings(value):
    """Every data model path a component's properties bind to."""
    if isinstance(value, dict):
        if "@path" in value:
            yield value["@path"]
        for item in value.values():
            yield from bindings(item)
    elif isinstance(value, list):
        for item in value:
            yield from bindings(item)


def unresolved(found, data) -> list[str]:
    """Bindings that point at nothing in the data model."""
    missing = []
    for cid, component in found.items():
        for path in bindings(component):
            try:
                resolve({"@path": path}, data)
            except (KeyError, IndexError, TypeError, ValueError):
                missing.append(f"{cid}: {path}")
    return missing


def button(found, card, name) -> str:
    """The ID of the button in a card whose action is ``name``."""
    return next(
        kid for kid in subtree(found, card)
        if found[kid].get("action", {}).get("event", {}).get("name") == name
    )


def fire(found, data, cid):
    """The action a button sends: its name and its context with every binding resolved."""
    event = found[cid]["action"]["event"]
    context = {key: json.loads(json.dumps(resolve(value, data))) for key, value in event.get("context", {}).items()}
    return event["name"], context


class TestCodebookSurface(unittest.TestCase):
    def setUp(self):
        self.desk = codebook_desk()
        self.messages = a2ui.surface(self.desk)
        self.found = components(self.messages)
        self.data = data_model(self.messages)

    def test_r1_8_codebook_surface_validates(self):
        self.assertEqual(a2ui.validate(self.messages), [])
        self.assertEqual(self.messages[0]["createSurface"]["surfaceId"], "desk-0a1b2c3d")

    def test_r2_1_code_card_carries_definition_criteria_and_cases(self):
        card = card_component(self.found, "code-03")
        self.assertEqual(self.found[card]["title"], "Land tenure")
        shown = texts(self.found, card, self.data)
        for expected in (
            "Who holds the plot and on what terms.",
            "Include when: Leases, permissions, ownership, eviction.",
            "Exclude when: Where plants are placed within the plot.",
            "The lease runs out in March and nobody has said a word.",
            "We moved the beds back from the fence after the survey.",
        ):
            self.assertIn(expected, shown)

    def test_r2_1_typical_and_borderline_cases_are_grouped_apart(self):
        card = card_component(self.found, "code-03")
        groups = {}
        for cid in subtree(self.found, card):
            passages = [
                self.found[kid]["text"] for kid in children(self.found[cid]) if self.found[kid]["component"] == "Passage"
            ]
            if passages:
                heading = [self.found[kid] for kid in children(self.found[cid]) if self.found[kid]["component"] == "Text"]
                self.assertEqual(heading[0]["variant"], "caption")
                groups[heading[0]["text"]] = passages
        self.assertEqual(groups, {
            "Typical cases": ["The lease runs out in March and nobody has said a word."],
            "Borderline cases": ["We moved the beds back from the fence after the survey."],
        })

    def test_r2_1_a_code_without_borderline_cases_shows_no_empty_group(self):
        card = card_component(self.found, "code-02")
        self.assertNotIn("Borderline cases", texts(self.found, card, self.data))

    def test_r2_1_cases_carry_their_source(self):
        card = card_component(self.found, "code-03")
        sources = [self.found[cid].get("source") for cid in subtree(self.found, card) if self.found[cid]["component"] == "Passage"]
        self.assertEqual(sources, ["Interview 03", "Field notes, May"])

    def test_r2_2_code_card_offers_exactly_five_actions(self):
        for card in self.desk["cards"]:
            cid = card_component(self.found, card["card_id"])
            groups = [
                self.found[kid] for kid in subtree(self.found, cid)
                if self.found[kid]["component"] == "ChoiceGroup" and [o["value"] for o in self.found[kid]["options"]] == CODE_ACTIONS
            ]
            self.assertEqual(len(groups), 1, card["card_id"])
            self.assertFalse(groups[0].get("multiple", False))

    def test_r2_3_initial_data_model_has_no_choice_set(self):
        choice_groups = [c for c in self.found.values() if c["component"] == "ChoiceGroup"]
        self.assertTrue(choice_groups)
        for group in choice_groups:
            self.assertIn("@path", group["value"], f"{group['id']} has a literal value")
            self.assertEqual(resolve(group["value"], self.data), [], group["id"])
        for field in (c for c in self.found.values() if c["component"] == "TextField"):
            self.assertIn("@path", field["value"], f"{field['id']} has a literal value")
            self.assertEqual(resolve(field["value"], self.data), "", field["id"])

    def test_r2_4_one_exclusivity_question(self):
        asked = [
            c for c in self.found.values()
            if c["component"] == "ChoiceGroup" and "mutually exclusive" in str(c.get("legend", ""))
        ]
        self.assertEqual(len(asked), 1)
        self.assertEqual([o["value"] for o in asked[0]["options"]], ["yes", "no"])
        inside_cards = {kid for card in self.desk["cards"] for kid in subtree(self.found, card_component(self.found, card["card_id"]))}
        self.assertNotIn(asked[0]["id"], inside_cards)

    def test_one_card_is_open_and_none_is_done(self):
        cards_ = [c for c in self.found.values() if c["component"] == "DecisionCard"]
        self.assertEqual(len(cards_), len(self.desk["cards"]) + 1)  # the codes and the exclusivity question
        opened = [c["id"] for c in cards_ if resolve(c["open"], self.data)]
        self.assertEqual(opened, [card_component(self.found, "code-01")])
        self.assertFalse(any(resolve(c["done"], self.data) for c in cards_))

    def test_each_save_names_its_own_card_and_data(self):
        for n, card in enumerate(self.desk["cards"]):
            cid = card_component(self.found, card["card_id"])
            saves = [
                self.found[kid]["action"]["event"] for kid in subtree(self.found, cid)
                if self.found[kid].get("action", {}).get("event", {}).get("name") == "save_decision"
            ]
            self.assertEqual(saves, [{"name": "save_decision", "context": {"card_id": card["card_id"], "decision": {"@path": f"/cards/{n}"}}}])
            self.assertEqual(self.data["cards"][n]["card_id"], card["card_id"])

    def test_merge_offers_every_other_code(self):
        card = card_component(self.found, "code-01")
        merge = [
            self.found[kid] for kid in subtree(self.found, card)
            if self.found[kid]["component"] == "ChoiceGroup" and self.found[kid]["value"] == {"@path": "/cards/0/target"}
        ]
        self.assertEqual([o["value"] for o in merge[0]["options"]], [c["code_label"] for c in self.desk["cards"][1:]])

    def test_progress_and_tally_count_every_decision(self):
        progress = [c for c in self.found.values() if c["component"] == "Progress"]
        tally = [c for c in self.found.values() if c["component"] == "Tally"]
        self.assertEqual((len(progress), len(tally)), (1, 1))
        self.assertEqual(resolve(progress[0]["total"], self.data), 7)
        self.assertEqual(resolve(progress[0]["done"], self.data), 0)
        self.assertEqual((resolve(tally[0]["left"], self.data), resolve(tally[0]["total"], self.data)), (7, 7))

    def test_ratify_and_copy_act_on_the_whole_desk(self):
        events = {
            c["action"]["event"]["name"]: c["action"]["event"].get("context", {})
            for c in self.found.values() if "action" in c
        }
        self.assertEqual(events["finish"], {"desk_id": "desk-0a1b2c3d"})
        self.assertEqual(events["copy_json"], {"desk_id": "desk-0a1b2c3d"})
        labels = [resolve(self.found[c["child"]]["text"], self.data) for c in self.found.values() if c["component"] == "Button"]
        self.assertIn("Ratify the codebook", labels)
        self.assertIn("Copy decisions as JSON", labels)

    def test_the_desk_ends_with_the_colophon(self):
        root = self.found["root"]
        self.assertEqual(self.found[root["children"][-1]], {"id": "byline", "component": "Byline", "version": __version__, "full": True})

    def test_the_title_travels_in_the_data_model(self):
        self.assertEqual(self.data["title"], "Community garden interviews")
        self.assertEqual(data_model(a2ui.surface(codebook_desk(title="")))["title"], "")

    def test_a_desk_with_one_code_offers_no_merge(self):
        desk = codebook_desk(cards=codebook_desk()["cards"][:1])
        messages = a2ui.surface(desk)
        self.assertEqual(a2ui.validate(messages), [])
        legends = [str(c.get("legend")) for c in components(messages).values() if c["component"] == "ChoiceGroup"]
        self.assertFalse(any("Merge" in legend for legend in legends))

    def test_unknown_stage_is_refused(self):
        with self.assertRaisesRegex(ValueError, r"stage is codebook or rulings, not 'themes'"):
            a2ui.surface(codebook_desk(stage="themes"))

    def test_r2_2_actions_read_as_the_method_names_them(self):
        group = self.found[card_component(self.found, "code-01") + "_action"]
        self.assertEqual([o["label"] for o in group["options"]], ["Adopt", "Reword", "Merge", "Split", "Delete"])

    def test_r2_4_the_question_and_its_answers_say_what_they_mean(self):
        question = next(c for c in self.found.values() if c["component"] == "ChoiceGroup" and c["value"] == {"@path": "/exclusivity/answer"})
        self.assertEqual(question["legend"], "Are the codes mutually exclusive?")
        self.assertEqual(
            [(o["label"], o["description"]) for o in question["options"]],
            [("Yes", "A passage takes one code at most."), ("No", "A passage can take several codes.")],
        )

    def test_r2_4_the_answer_is_saved_from_the_question(self):
        saves = [c["action"]["event"] for c in self.found.values() if c.get("action", {}).get("event", {}).get("name") == "answer_exclusive"]
        self.assertEqual(saves, [{"name": "answer_exclusive", "context": {"exclusive": {"@path": "/exclusivity/answer"}}}])
        save_ids = [c["id"] for c in self.found.values() if c.get("action", {}).get("event", {}).get("name") == "answer_exclusive"]
        self.assertIn(save_ids[0], subtree(self.found, "exclusivity"))

    def test_every_card_is_queued_unset_and_changeable(self):
        for cid, card in self.found.items():
            if card["component"] != "DecisionCard":
                continue
            card_id = resolve(card["eyebrow"], self.data)
            self.assertEqual(card["state"], "needs", cid)
            self.assertTrue(card["statusLabel"], cid)
            self.assertEqual(resolve(card["result"], self.data), "", cid)
            self.assertEqual(card["change"], {"event": {"name": "change_decision", "context": {"card_id": card_id}}}, cid)
        self.assertEqual(self.found["exclusivity"]["eyebrow"], "exclusivity")
        self.assertEqual(
            self.found["exclusivity"]["change"]["event"]["context"], {"card_id": "exclusivity"},
        )

    def test_long_answers_get_room(self):
        card = card_component(self.found, "code-01")
        fields = {self.found[kid]["value"]["@path"].rsplit("/", 1)[1]: self.found[kid] for kid in subtree(self.found, card) if self.found[kid]["component"] == "TextField"}
        self.assertEqual({k for k, f in fields.items() if f.get("multiline")}, {"definition", "parts", "note"})
        self.assertIn("colon", fields["parts"]["hint"])

    def test_the_queue_is_counted_from_the_first_card(self):
        progress = next(c for c in self.found.values() if c["component"] == "Progress")
        self.assertEqual(resolve(progress["current"], self.data), 0)
        tally = next(c for c in self.found.values() if c["component"] == "Tally")
        self.assertTrue(tally["sticky"])
        self.assertEqual(tally["noun"], "decisions")

    def test_the_main_actions_stand_out(self):
        variants = {c["action"]["event"]["name"]: c["variant"] for c in self.found.values() if c["component"] == "Button"}
        self.assertEqual(variants["finish"], "primary")
        self.assertEqual(variants["save_decision"], "primary")
        self.assertEqual(variants["answer_exclusive"], "primary")
        self.assertEqual(variants["copy_json"], "default")

    def test_a_case_without_a_source_shows_none(self):
        cases = _load("cases")
        cases["Food access"][0]["source"] = ""
        desk = codebook_desk(cards=cards.codebook_cards(_load("codebook"), cases))
        found = components(a2ui.surface(desk))
        passages = [found[cid] for cid in subtree(found, card_component(found, "code-04")) if found[cid]["component"] == "Passage"]
        self.assertNotIn("source", passages[0])

    def test_the_data_model_names_its_desk(self):
        self.assertEqual(self.data["desk_id"], "desk-0a1b2c3d")
        desk = codebook_desk()
        del desk["title"]
        self.assertEqual(data_model(a2ui.surface(desk))["title"], "")

    def test_a_desk_with_no_codes_opens_on_the_question(self):
        messages = a2ui.surface(codebook_desk(cards=[]))
        self.assertEqual(a2ui.validate(messages), [])
        data = data_model(messages)
        self.assertTrue(data["status"]["exclusivity"]["open"])
        self.assertEqual(data["status"]["progress"]["left"], 1)


NO_CODE = "(no code applies)"


def _ruling_group(found, card):
    return next(
        found[kid] for kid in subtree(found, card)
        if found[kid]["component"] == "ChoiceGroup" and found[kid]["value"]["@path"].endswith("/codes")
    )


class TestRulingsSurface(unittest.TestCase):
    def setUp(self):
        self.desk = rulings_desk()
        self.messages = a2ui.surface(self.desk)
        self.found = components(self.messages)
        self.data = data_model(self.messages)

    def test_r1_8_rulings_surface_validates(self):
        self.assertEqual(a2ui.validate(self.messages), [])
        self.assertEqual(a2ui.validate(a2ui.surface(rulings_desk(blind_first=False, exclusive=True))), [])

    def test_r3_1_rulings_card_carries_text_codes_and_entries(self):
        card = card_component(self.found, "chunk-9")
        shown = texts(self.found, card, self.data)
        self.assertIn("The council said the permit covers the shed but not the tunnel.", shown)
        self.assertIn("Land tenure: Who holds the plot and on what terms.", shown)
        self.assertIn("Municipal relations: Dealings with the city or its staff.", shown)
        coders = {}
        for cid in subtree(self.found, card):
            kids = children(self.found[cid])
            heads = [self.found[k]["text"] for k in kids if self.found[k]["component"] == "Text" and "coding pass" in self.found[k]["text"]]
            if heads:
                coders[heads[0]] = [self.found[k]["text"] for k in kids if self.found[k]["component"] in ("CodeTag", "Text")][1:]
        self.assertEqual(coders, {
            "First coding pass": ["Land tenure", "Municipal relations"],
            "Second coding pass": ["Municipal relations"],
        })

    def test_r3_1_a_pass_with_no_code_says_so(self):
        card = card_component(self.found, "chunk-12")
        self.assertIn("No code", texts(self.found, card, self.data))

    def test_r3_2_no_initial_message_carries_a_proposal(self):
        sent = json.dumps(self.messages)
        for proposal in _load("proposals").values():
            self.assertNotIn(proposal["rationale"], sent)
        self.assertFalse([c for c in self.found.values() if c["component"] == "Provenance"])

    def test_r3_2_without_blind_first_the_proposal_shows_from_the_start(self):
        found = components(a2ui.surface(rulings_desk(blind_first=False)))
        provenance = [found[kid] for kid in subtree(found, card_component(found, "chunk-7")) if found[kid]["component"] == "Provenance"]
        self.assertEqual(len(provenance), 1)
        self.assertEqual(provenance[0]["by"], "model")
        self.assertIn("Charity framing", provenance[0]["text"])
        self.assertIn("Giving the harvest away is the point of the passage.", provenance[0]["text"])

    def test_r3_3_exclusive_desk_is_single_select(self):
        found = components(a2ui.surface(rulings_desk(exclusive=True)))
        group = _ruling_group(found, card_component(found, "chunk-7"))
        self.assertFalse(group.get("multiple", False))
        self.assertEqual([o["value"] for o in group["options"]], self.desk["codes"])

    def test_r3_3_otherwise_several_codes_or_none(self):
        group = _ruling_group(self.found, card_component(self.found, "chunk-7"))
        self.assertTrue(group["multiple"])
        self.assertEqual([o["value"] for o in group["options"]], [*self.desk["codes"], NO_CODE])
        self.assertEqual(group["options"][-1]["label"], "No code applies")
        self.assertEqual(resolve(group["value"], self.data), [])

    def test_r3_3_a_code_named_like_no_code_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no code applies"):
            a2ui.surface(rulings_desk(codes=[*self.desk["codes"], NO_CODE]))

    def test_r3_4_exclude_requires_reason(self):
        card = card_component(self.found, "chunk-7")
        excludes = [self.found[kid] for kid in subtree(self.found, card) if self.found[kid].get("action", {}).get("event", {}).get("name") == "exclude_chunk"]
        self.assertEqual(len(excludes), 1)
        context = excludes[0]["action"]["event"]["context"]
        self.assertEqual(context["card_id"], "chunk-7")
        reason = next(self.found[kid] for kid in subtree(self.found, card) if self.found[kid]["component"] == "TextField" and self.found[kid]["value"] == context["reason"])
        self.assertTrue(reason["required"])
        self.assertEqual(resolve(reason["value"], self.data), "")

    def test_r3_5_no_action_carries_two_card_ids(self):
        rebuilt = a2ui.after_decision(self.desk, {"decisions": {"chunk-7": {"codes": ["Shared labour"]}}}, "chunk-7")
        for messages in (self.messages, [*self.messages, *rebuilt], a2ui.surface(codebook_desk())):
            ids = [card["card_id"] for card in data_model(messages)["cards"]]
            for component in components(messages).values():
                for action in (component.get("action"), component.get("change")):
                    if not action:
                        continue
                    context = action["event"].get("context", {})
                    paths = list(bindings(context))
                    # A context binds one card's fields, or the codebook question's, and nothing wider.
                    for path in paths:
                        self.assertRegex(path, r"^/(cards/\d+|exclusivity)(/|$)", component["id"])
                    named = set(re.findall(r'"card_id": "([^"]+)"', json.dumps(context)))
                    named |= {ids[int(n)] for n in re.findall(r"^/cards/(\d+)", "\n".join(paths), re.M)}
                    self.assertLessEqual(len(named), 1, component["id"])

    def test_the_rule_question_waits_for_a_differing_ruling(self):
        self.assertFalse([p for c in self.found.values() for p in bindings(c) if p.endswith(("/is_rule", "/rule_text"))])

    def test_r2_3_a_rulings_desk_starts_with_nothing_chosen_and_the_first_card_open(self):
        for blind_first in (True, False):
            data = data_model(a2ui.surface(rulings_desk(blind_first=blind_first)))
            for card in data["cards"]:
                self.assertEqual(
                    {k: v for k, v in card.items() if k != "card_id"},
                    {"codes": [], "is_rule": [], "rule_text": "", "reason": "", "note": ""},
                )
            self.assertEqual([c["open"] for c in data["status"]["cards"]], [True, False, False, False])
            self.assertFalse(any(c["done"] or c["result"] for c in data["status"]["cards"]))
            self.assertEqual(data["status"]["progress"], {"done": 0, "current": 0, "left": 4})

    def test_r3_2_blind_first_is_the_default(self):
        desk = rulings_desk()
        del desk["blind_first"]
        messages = a2ui.surface(desk)
        self.assertFalse([c for c in components(messages).values() if c["component"] == "Provenance"])
        for proposal in _load("proposals").values():
            self.assertNotIn(proposal["rationale"], json.dumps(messages))

    def test_every_binding_points_into_the_data_model(self):
        for desk in (codebook_desk(), rulings_desk(), rulings_desk(blind_first=False, exclusive=True)):
            messages = a2ui.surface(desk)
            self.assertEqual(unresolved(components(messages), data_model(messages)), [], desk["stage"])
        asked = [*self.messages, *a2ui.after_decision(self.desk, {"decisions": {"chunk-7": {"codes": ["Shared labour"]}}}, "chunk-7")]
        self.assertEqual(unresolved(components(asked), data_model(asked)), [])

    def test_r3_1_entries_cover_the_codes_of_both_passes(self):
        shown = texts(self.found, card_component(self.found, "chunk-7"), self.data)
        for label in ("Shared labour", "Charity framing", "Food access"):
            self.assertTrue([s for s in shown if s.startswith(f"{label}: ")], label)
        self.assertFalse([s for s in shown if s.startswith("Land tenure: ")])

    def test_r3_1_the_chunk_shows_where_it_comes_from(self):
        card = card_component(self.found, "chunk-7")
        passage = next(self.found[kid] for kid in subtree(self.found, card) if self.found[kid]["component"] == "Passage")
        self.assertEqual(passage["source"], "interview-02.txt")
        unsourced = rulings_desk(cards=[{**c, "source": ""} for c in self.desk["cards"]])
        found = components(a2ui.surface(unsourced))
        passage = next(found[kid] for kid in subtree(found, card_component(found, "chunk-7")) if found[kid]["component"] == "Passage")
        self.assertNotIn("source", passage)

    def test_each_card_says_where_it_sits_in_the_queue(self):
        titles = [self.found[card_component(self.found, c["card_id"])]["title"] for c in self.desk["cards"]]
        self.assertEqual(titles, [f"Disagreement {n} of 4" for n in range(1, 5)])

    def test_a_proposal_without_a_rationale_shows_its_codes(self):
        bare = [{**c, "proposal": {**c["proposal"], "rationale": ""}} for c in self.desk["cards"]]
        found = components(a2ui.surface(rulings_desk(cards=bare, blind_first=False)))
        provenance = next(found[kid] for kid in subtree(found, card_component(found, "chunk-7")) if found[kid]["component"] == "Provenance")
        self.assertEqual(provenance["text"], "Charity framing.")

    def test_a_proposal_names_its_codes_or_that_none_applies(self):
        none = [{**c, "proposal": {"codes": [], "rationale": "Nothing fits."}} if c["card_id"] == "chunk-7" else c for c in self.desk["cards"]]
        found = components(a2ui.surface(rulings_desk(cards=none, blind_first=False)))
        shown = {cid: found[kid]["text"] for cid in ("chunk-7", "chunk-9") for kid in subtree(found, card_component(found, cid)) if found[kid]["component"] == "Provenance"}
        self.assertEqual(shown["chunk-7"], "No code applies. Nothing fits.")
        self.assertEqual(shown["chunk-9"], "Land tenure, Municipal relations. The permit sets what the garden may build on the plot.")

    def test_a_proposal_outside_the_desk_codes_is_refused(self):
        odd = [{**c, "proposal": {"codes": ["Volunteer burnout"], "rationale": ""}} if c["card_id"] == "chunk-9" else c for c in self.desk["cards"]]
        with self.assertRaisesRegex(ValueError, "chunk-9 carries 'Volunteer burnout'"):
            a2ui.surface(rulings_desk(cards=odd, codes=[c for c in self.desk["codes"] if c != "Volunteer burnout"]))

    def test_a_desk_whose_cards_carry_a_code_outside_its_codes_is_refused(self):
        with self.assertRaisesRegex(ValueError, "chunk-7.*Food access"):
            a2ui.surface(rulings_desk(codes=["Shared labour", "Charity framing", "Land tenure", "Municipal relations"]))

    def test_ratify_records_the_rulings(self):
        labels = [resolve(self.found[c["child"]]["text"], self.data) for c in self.found.values() if c["component"] == "Button"]
        self.assertIn("Record the rulings", labels)
        progress = next(c for c in self.found.values() if c["component"] == "Progress")
        self.assertEqual(progress["total"], 4)


def _apply(messages, more):
    """The messages a renderer holds after more arrive."""
    return [*messages, *more]


class TestAfterDecision(unittest.TestCase):
    def setUp(self):
        self.desk = rulings_desk()
        self.start = a2ui.surface(self.desk)

    def _after(self, saved, card_id, desk=None, start=None):
        desk = desk or self.desk
        more = a2ui.after_decision(desk, {"decisions": saved}, card_id)
        messages = _apply(start or self.start, more)
        self.assertEqual(a2ui.validate(messages), [])
        return more, components(messages), data_model(messages)

    def test_r3_2_the_proposal_arrives_with_the_saved_ruling(self):
        more, found, _ = self._after({"chunk-7": {"codes": ["Charity framing"]}}, "chunk-7")
        provenance = [found[kid] for kid in subtree(found, card_component(found, "chunk-7")) if found[kid]["component"] == "Provenance"]
        self.assertEqual(len(provenance), 1)
        self.assertIn("Giving the harvest away is the point of the passage.", provenance[0]["text"])
        # Only that card's proposal.
        self.assertNotIn("The permit sets what the garden may build on the plot.", json.dumps(more))

    def test_r3_9_saving_one_card_releases_no_other_proposal(self):
        more, _, _ = self._after({"chunk-7": {"codes": ["Charity framing"]}}, "chunk-7")
        sent = json.dumps(more)
        for chunk_id, proposal in _load("proposals").items():
            if chunk_id != "7":
                self.assertNotIn(proposal["rationale"], sent)

    def test_a_ruling_that_matches_the_proposal_closes_the_card_and_opens_the_next(self):
        _, found, data = self._after({"chunk-7": {"codes": ["Charity framing"]}}, "chunk-7")
        self.assertEqual((data["status"]["cards"][0]["done"], data["status"]["cards"][0]["open"]), (True, False))
        self.assertEqual(data["status"]["cards"][0]["result"], "Charity framing")
        self.assertTrue(data["status"]["cards"][1]["open"])
        self.assertEqual(data["status"]["progress"], {"done": 1, "current": 1, "left": 3})

    def test_r3_6_a_differing_ruling_asks_whether_it_states_a_rule(self):
        _, found, data = self._after({"chunk-7": {"codes": ["Shared labour"]}}, "chunk-7")
        card = card_component(found, "chunk-7")
        rule = [found[kid] for kid in subtree(found, card) if found[kid]["component"] == "ChoiceGroup" and found[kid]["value"] == {"@path": "/cards/0/is_rule"}]
        self.assertEqual(len(rule), 1)
        self.assertEqual(rule[0]["legend"], "Does this ruling state a rule?")
        self.assertEqual(resolve(rule[0]["value"], data), [])
        rule_text = [found[kid] for kid in subtree(found, card) if found[kid]["component"] == "TextField" and found[kid]["value"] == {"@path": "/cards/0/rule_text"}]
        self.assertEqual(len(rule_text), 1)
        # The card stays open until the question is answered.
        self.assertEqual((data["status"]["cards"][0]["done"], data["status"]["cards"][0]["open"]), (False, True))
        self.assertEqual(data["status"]["progress"]["done"], 0)

    def test_r3_6_answering_the_rule_question_closes_the_card(self):
        saved = {"chunk-7": {"codes": ["Shared labour"], "is_rule": True, "rule_text": "Shared work outweighs giving."}}
        _, _, data = self._after(saved, "chunk-7")
        self.assertTrue(data["status"]["cards"][0]["done"])
        self.assertEqual(data["status"]["cards"][0]["result"], "Shared labour · states a rule")
        saved["chunk-7"]["is_rule"] = False
        _, _, data = self._after(saved, "chunk-7")
        self.assertEqual(data["status"]["cards"][0]["result"], "Shared labour")

    def test_no_code_applies_differs_from_a_proposed_code(self):
        # chunk 12's proposal is Shared labour, so "no code applies" departs from it.
        _, _, data = self._after({"chunk-12": {"none_apply": True}}, "chunk-12")
        self.assertFalse(data["status"]["cards"][3]["done"])
        _, _, data = self._after({"chunk-12": {"none_apply": True, "is_rule": False}}, "chunk-12")
        self.assertEqual((data["status"]["cards"][3]["done"], data["status"]["cards"][3]["result"]), (True, "No code applies"))

    def test_an_exclusion_closes_the_card_without_a_rule_question(self):
        _, found, data = self._after({"chunk-12": {"exclude": {"reason": "Off topic."}}}, "chunk-12")
        self.assertEqual((data["status"]["cards"][3]["done"], data["status"]["cards"][3]["result"]), (True, "Excluded"))
        self.assertNotIn("chunk4_rule", found)

    def test_a_card_without_a_proposal_never_asks_about_a_rule(self):
        desk = rulings_desk(cards=cards.rulings_cards(_load("coding_a"), _load("coding_b"), _load("codebook"), None))
        _, _, data = self._after({"chunk-7": {"codes": ["Shared labour"]}}, "chunk-7", desk, a2ui.surface(desk))
        self.assertTrue(data["status"]["cards"][0]["done"])

    def test_the_next_card_is_the_next_undecided_one(self):
        saved = {"chunk-9": {"codes": ["Municipal relations", "Land tenure"]}, "chunk-11": {"codes": ["Food access"]}}
        _, _, data = self._after(saved, "chunk-11")
        self.assertEqual([c["open"] for c in data["status"]["cards"]], [False, False, False, True])
        saved["chunk-12"] = {"codes": ["Shared labour"]}
        _, _, data = self._after(saved, "chunk-12")
        self.assertEqual([c["open"] for c in data["status"]["cards"]], [True, False, False, False])

    def test_when_every_card_is_decided_none_is_open(self):
        saved = {
            "chunk-7": {"codes": ["Charity framing"]}, "chunk-9": {"codes": ["Municipal relations", "Land tenure"]},
            "chunk-11": {"codes": ["Food access"]}, "chunk-12": {"codes": ["Shared labour"]},
        }
        _, _, data = self._after(saved, "chunk-12")
        self.assertFalse(any(c["open"] for c in data["status"]["cards"]))
        self.assertEqual(data["status"]["progress"], {"done": 4, "current": 4, "left": 0})

    def test_codebook_decisions_close_their_card(self):
        desk = codebook_desk()
        start = a2ui.surface(desk)
        results = {
            "adopt": ({"action": "adopt"}, "Adopted"),
            "reword": ({"action": "reword", "definition": "New."}, "Reworded"),
            "merge": ({"action": "merge", "target": "Charity framing"}, "Merged into Charity framing"),
            "split": ({"action": "split", "parts": [{"label": "A", "definition": "a"}, {"label": "B", "definition": "b"}]}, "Split into 2 codes"),
            "delete": ({"action": "delete"}, "Deleted"),
        }
        for name, (decision, result) in results.items():
            _, _, data = self._after({"code-01": decision}, "code-01", desk, start)
            self.assertEqual(data["status"]["cards"][0]["result"], result, name)
            self.assertTrue(data["status"]["cards"][1]["open"], name)

    def test_the_exclusivity_answer_closes_the_question(self):
        desk = codebook_desk()
        start = a2ui.surface(desk)
        decided = {c["card_id"]: {"action": "adopt"} for c in desk["cards"]}
        more = a2ui.after_decision(desk, {"decisions": decided, "exclusive": True}, "exclusivity")
        messages = [*start, *more]
        self.assertEqual(a2ui.validate(messages), [])
        data = data_model(messages)
        self.assertEqual((data["status"]["exclusivity"]["done"], data["status"]["exclusivity"]["result"]), (True, "Mutually exclusive"))
        self.assertEqual(data["status"]["progress"], {"done": 7, "current": 7, "left": 0})
        more = a2ui.after_decision(desk, {"decisions": {}, "exclusive": False}, "exclusivity")
        data = data_model([*start, *more])
        self.assertEqual(data["status"]["exclusivity"]["result"], "Not mutually exclusive")
        self.assertTrue(data["status"]["cards"][0]["open"])

    def test_after_the_last_code_the_question_opens(self):
        desk = codebook_desk()
        decided = {c["card_id"]: {"action": "adopt"} for c in desk["cards"]}
        data = data_model([*a2ui.surface(desk), *a2ui.after_decision(desk, {"decisions": decided}, "code-06")])
        self.assertTrue(data["status"]["exclusivity"]["open"])
        self.assertEqual(data["status"]["progress"], {"done": 6, "current": 6, "left": 1})

    def test_an_unknown_card_is_refused(self):
        with self.assertRaisesRegex(ValueError, "chunk-99"):
            a2ui.after_decision(self.desk, {"decisions": {"chunk-99": {"codes": []}}}, "chunk-99")

    def test_a_card_with_no_saved_decision_is_refused(self):
        with self.assertRaisesRegex(ValueError, "chunk-7.*no saved decision"):
            a2ui.after_decision(self.desk, {"decisions": {}}, "chunk-7")


    def test_a_matching_ruling_asks_no_rule_question(self):
        more, _, _ = self._after({"chunk-7": {"codes": ["Charity framing"]}}, "chunk-7")
        self.assertFalse([p for m in more for c in m.get("updateComponents", {}).get("components", []) for p in bindings(c) if p.endswith("/is_rule")])

    def test_a_ruling_is_compared_with_the_proposal_whatever_its_order(self):
        _, _, data = self._after({"chunk-9": {"codes": ["Municipal relations", "Land tenure"]}}, "chunk-9")
        self.assertTrue(data["status"]["cards"][1]["done"])

    def test_a_card_awaiting_the_rule_question_shows_no_result(self):
        _, _, data = self._after({"chunk-7": {"codes": ["Shared labour"]}}, "chunk-7")
        self.assertEqual(data["status"]["cards"][0]["result"], "")

    def test_the_next_card_can_come_before_the_one_just_decided(self):
        saved = {"chunk-7": {"codes": ["Charity framing"]}, "chunk-12": {"codes": ["Shared labour"]}, "chunk-11": {"codes": ["Food access"]}}
        _, _, data = self._after(saved, "chunk-11")
        self.assertEqual([c["open"] for c in data["status"]["cards"]], [False, True, False, False])

    def test_an_exclusion_releases_the_proposal(self):
        more, _, _ = self._after({"chunk-12": {"exclude": {"reason": "Off topic."}}}, "chunk-12")
        self.assertIn("Deciding together is part of the shared work.", json.dumps(more))

    def test_a_save_with_no_decisions_is_refused(self):
        with self.assertRaisesRegex(ValueError, "chunk-7 has no saved decision"):
            a2ui.after_decision(self.desk, {}, "chunk-7")

    def test_the_exclusivity_answer_needs_no_code_decisions(self):
        desk = codebook_desk()
        data = data_model([*a2ui.surface(desk), *a2ui.after_decision(desk, {"exclusive": True}, "exclusivity")])
        self.assertTrue(data["status"]["exclusivity"]["done"])
        self.assertTrue(data["status"]["cards"][0]["open"])

    def test_an_unanswered_exclusivity_question_is_refused(self):
        with self.assertRaisesRegex(ValueError, "exclusivity question has no saved answer"):
            a2ui.after_decision(codebook_desk(), {"decisions": {}, "exclusive": None}, "exclusivity")

    def test_a_code_without_criteria_shows_no_empty_criteria(self):
        codebook = [{**entry, "inclusion_criteria": "", "exclusion_criteria": ""} for entry in _load("codebook")]
        desk = codebook_desk(cards=cards.codebook_cards(codebook, _load("cases")))
        messages = a2ui.surface(desk)
        self.assertEqual(a2ui.validate(messages), [])
        found, data = components(messages), data_model(messages)
        shown = texts(found, card_component(found, "code-03"), data)
        self.assertFalse([s for s in shown if s.startswith(("Include when", "Exclude when"))])
        self.assertIn("Who holds the plot and on what terms.", shown)

class TestDecisionFromAction(unittest.TestCase):
    """What the view sends, read into the decisions document's shape, end to end."""

    def setUp(self):
        self.desk = rulings_desk()
        self.messages = a2ui.surface(self.desk)
        self.found = components(self.messages)
        self.data = data_model(self.messages)

    def _save(self, card_id, **fields):
        """Fill a card's fields through its own bindings and press Save, as the researcher does."""
        card = card_component(self.found, card_id)
        n = next(i for i, c in enumerate(self.data["cards"]) if c["card_id"] == card_id)
        for key, value in fields.items():
            set_path(self.data, f"/cards/{n}/{key}", value)
        return a2ui.decision_from_action(self.desk, *fire(self.found, self.data, button(self.found, card, "save_decision")))

    def _option(self, card_id, suffix, label):
        card = card_component(self.found, card_id)
        group = next(
            self.found[kid] for kid in subtree(self.found, card)
            if self.found[kid]["component"] == "ChoiceGroup" and self.found[kid]["value"]["@path"].endswith(suffix)
        )
        return next(o["value"] for o in group["options"] if o["label"] == label)

    def _step(self, saved, card_id):
        more = a2ui.after_decision(self.desk, {"decisions": saved}, card_id)
        self.messages = [*self.messages, *more]
        self.assertEqual(a2ui.validate(self.messages), [])
        self.found = components(self.messages)
        self.data = apply_data(self.data, more)

    def test_r3_6_a_differing_ruling_saved_in_the_view_asks_the_rule_question(self):
        card_id, decision = self._save("chunk-7", codes=[self._option("chunk-7", "/codes", "Shared labour")])
        self.assertEqual((card_id, decision), ("chunk-7", {"codes": ["Shared labour"]}))
        self._step({card_id: decision}, card_id)
        self.assertEqual((self.data["status"]["cards"][0]["open"], self.data["status"]["cards"][0]["done"]), (True, False))
        # The researcher answers in the view, and saves again.
        yes = self._option("chunk-7", "/is_rule", "Yes")
        card_id, decision = self._save("chunk-7", is_rule=[yes], rule_text=" Shared work outweighs giving. ")
        self.assertEqual(decision, {"codes": ["Shared labour"], "is_rule": True, "rule_text": "Shared work outweighs giving."})
        self._step({card_id: decision}, card_id)
        self.assertEqual(self.data["status"]["cards"][0]["result"], "Shared labour · states a rule")
        self.assertTrue(self.data["status"]["cards"][1]["open"])

    def test_r3_6_answering_no_records_a_ruling_without_a_rule(self):
        card_id, decision = self._save("chunk-7", codes=["Shared labour"])
        self._step({card_id: decision}, card_id)
        card_id, decision = self._save("chunk-7", is_rule=[self._option("chunk-7", "/is_rule", "No")])
        self.assertIs(decision["is_rule"], False)
        self._step({card_id: decision}, card_id)
        self.assertEqual((self.data["status"]["cards"][0]["done"], self.data["status"]["cards"][0]["result"]), (True, "Shared labour"))

    def test_r3_3_no_code_applies_in_the_view_is_none_apply(self):
        card_id, decision = self._save("chunk-12", codes=[self._option("chunk-12", "/codes", "No code applies")])
        self.assertEqual(decision, {"none_apply": True})
        self._step({card_id: decision}, card_id)
        self.assertFalse(self.data["status"]["cards"][3]["done"])  # it departs from the proposal

    def test_r3_3_no_code_applies_cannot_join_a_code(self):
        with self.assertRaisesRegex(ValueError, "chunk-7.*No code applies"):
            self._save("chunk-7", codes=["Shared labour", NO_CODE])

    def test_a_ruling_needs_a_choice(self):
        with self.assertRaisesRegex(ValueError, "Choose a ruling for chunk-7"):
            self._save("chunk-7")

    def test_a_note_travels_only_when_written(self):
        self.assertEqual(self._save("chunk-7", codes=["Food access"], note="  ")[1], {"codes": ["Food access"]})
        self.assertEqual(self._save("chunk-7", codes=["Food access"], note=" Close call. ")[1], {"codes": ["Food access"], "note": "Close call."})

    def test_r3_4_the_exclude_button_sends_its_reason(self):
        card = card_component(self.found, "chunk-11")
        set_path(self.data, "/cards/2/reason", " Not about the garden. ")
        decided = a2ui.decision_from_action(self.desk, *fire(self.found, self.data, button(self.found, card, "exclude_chunk")))
        self.assertEqual(decided, ("chunk-11", {"exclude": {"reason": "Not about the garden."}}))

    def test_the_exclusivity_answer(self):
        desk = codebook_desk()
        found = components(a2ui.surface(desk))
        data = data_model(a2ui.surface(desk))
        group = found["exclusivity_answer"]
        for label, expected in (("Yes", True), ("No", False)):
            data["exclusivity"]["answer"] = [next(o["value"] for o in group["options"] if o["label"].startswith(label))]
            decided = a2ui.decision_from_action(desk, *fire(found, data, button(found, "exclusivity", "answer_exclusive")))
            self.assertEqual(decided, ("exclusivity", {"exclusive": expected}))
        data["exclusivity"]["answer"] = []
        with self.assertRaisesRegex(ValueError, "Choose an answer"):
            a2ui.decision_from_action(desk, *fire(found, data, button(found, "exclusivity", "answer_exclusive")))

    def test_codebook_decisions_from_the_view(self):
        desk = codebook_desk()
        messages = a2ui.surface(desk)
        found = components(messages)
        card = card_component(found, "code-01")
        cases = {
            "adopt": ({"action": ["adopt"], "definition": "stray", "label": "stray", "target": ["Land tenure"], "parts": "x: y"}, {"action": "adopt"}),
            "reword": ({"action": ["reword"], "definition": " Work done together. ", "label": " "}, {"action": "reword", "definition": "Work done together."}),
            "relabel": ({"action": ["reword"], "definition": "Work.", "label": "Joint work"}, {"action": "reword", "definition": "Work.", "label": "Joint work"}),
            "merge": ({"action": ["merge"], "target": ["Charity framing"]}, {"action": "merge", "target": "Charity framing"}),
            "split": (
                {"action": ["split"], "parts": "Rosters: Who works when.\n\n Workdays : Days the members work together.\n"},
                {"action": "split", "parts": [{"label": "Rosters", "definition": "Who works when."}, {"label": "Workdays", "definition": "Days the members work together."}]},
            ),
            "delete": ({"action": ["delete"], "note": "Never used."}, {"action": "delete", "note": "Never used."}),
        }
        for name, (fields, expected) in cases.items():
            data = data_model(messages)
            data["cards"][0].update(fields)
            self.assertEqual(a2ui.decision_from_action(desk, *fire(found, data, button(found, card, "save_decision"))), ("code-01", expected), name)
        data = data_model(messages)
        with self.assertRaisesRegex(ValueError, "Choose what to do with code-01"):
            a2ui.decision_from_action(desk, *fire(found, data, button(found, card, "save_decision")))
        data["cards"][0].update({"action": ["split"], "parts": "Rosters: Who works when.\nWorkdays"})
        with self.assertRaisesRegex(ValueError, "code-01.*'Workdays'"):
            a2ui.decision_from_action(desk, *fire(found, data, button(found, card, "save_decision")))

    def test_the_view_offers_every_choice_the_conversion_reads(self):
        # Every option value the codebook action group offers is one decision_from_action knows.
        desk = codebook_desk()
        found = components(a2ui.surface(desk))
        offered = [o["value"] for o in found[next(k for k in subtree(found, card_component(found, "code-01")) if k.endswith("_action"))]["options"]]
        for action in offered:
            context = {"card_id": "code-01", "decision": {"card_id": "code-01", "action": [action], "definition": "d", "label": "", "target": ["Land tenure"], "parts": "A: a\nB: b", "note": ""}}
            self.assertEqual(a2ui.decision_from_action(desk, "save_decision", context)[1]["action"], action)

    def test_malformed_views_are_read_as_nothing_chosen(self):
        self.assertEqual(
            a2ui.decision_from_action(self.desk, "exclude_chunk", {"card_id": "chunk-7"}),
            ("chunk-7", {"exclude": {"reason": ""}}),
        )
        with self.assertRaisesRegex(ValueError, "Choose a ruling for chunk-7"):
            a2ui.decision_from_action(self.desk, "save_decision", {"card_id": "chunk-7", "decision": None})
        with self.assertRaisesRegex(ValueError, "Choose a ruling for chunk-7"):
            a2ui.decision_from_action(self.desk, "save_decision", {"card_id": "chunk-7", "decision": {"codes": "Food access"}})
        desk = codebook_desk()
        merged = a2ui.decision_from_action(desk, "save_decision", {"card_id": "code-01", "decision": {"action": ["merge"], "target": []}})
        self.assertEqual(merged, ("code-01", {"action": "merge", "target": ""}))
        split = a2ui.decision_from_action(desk, "save_decision", {"card_id": "code-01", "decision": {"action": ["split"], "parts": "Rosters: Who works: and when.\nWorkdays: Days."}})
        self.assertEqual(split[1]["parts"][0], {"label": "Rosters", "definition": "Who works: and when."})

    def test_actions_that_record_nothing_or_name_no_card_are_refused(self):
        with self.assertRaisesRegex(ValueError, "'finish' is not an action that records a decision"):
            a2ui.decision_from_action(self.desk, "finish", {"card_id": "chunk-7"})
        with self.assertRaisesRegex(ValueError, "chunk-99 is not a card on this desk"):
            a2ui.decision_from_action(self.desk, "save_decision", {"card_id": "chunk-99", "decision": {"codes": ["Food access"]}})
        with self.assertRaisesRegex(ValueError, "'exclude_chunk' is not an action that records a decision on a codebook desk"):
            a2ui.decision_from_action(codebook_desk(), "exclude_chunk", {"card_id": "code-01", "reason": "x"})
        with self.assertRaisesRegex(ValueError, "'answer_exclusive' is not an action that records a decision on a rulings desk"):
            a2ui.decision_from_action(self.desk, "answer_exclusive", {"exclusive": ["yes"]})
        with self.assertRaisesRegex(ValueError, "^Whether a ruling states a rule is answered yes or no, not 'maybe'"):
            self._save("chunk-7", codes=["Food access"], is_rule=["maybe"])
        with self.assertRaisesRegex(ValueError, "^Whether the codes are mutually exclusive is answered yes or no"):
            a2ui.decision_from_action(codebook_desk(), "answer_exclusive", {"exclusive": ["maybe"]})

if __name__ == "__main__":
    unittest.main()
