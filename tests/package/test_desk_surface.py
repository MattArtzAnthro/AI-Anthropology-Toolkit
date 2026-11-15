"""A desk as A2UI v1.0 messages: what each card shows, what it offers, and what it leaves unset."""

import json
import unittest
from pathlib import Path

from ai_anthro_toolkit import __version__
from ai_anthro_toolkit.desk import a2ui, cards

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "desk"
CODE_ACTIONS = ["adopt", "reword", "merge", "split", "delete"]


def _load(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def codebook_desk(**changes):
    desk = {
        "desk_id": "desk-0a1b2c3d",
        "stage": "codebook",
        "title": "Community garden interviews",
        "cards": cards.codebook_cards(_load("codebook"), _load("cases")),
    }
    desk.update(changes)
    return desk


def components(messages) -> dict[str, dict]:
    """Every component the messages define, by ID; a later definition replaces an earlier one."""
    found: dict[str, dict] = {}
    for message in messages:
        body = message.get("updateComponents") or message.get("createSurface") or {}
        for component in body.get("components", []):
            found[component["id"]] = component
    return found


def data_model(messages) -> dict:
    """The data model after the messages, for updates that set the root or a top-level key."""
    data: dict = {}
    for message in messages:
        update = message.get("updateDataModel")
        if update is None:
            continue
        path = update.get("path", "/")
        if path in ("", "/"):
            data = json.loads(json.dumps(update["value"]))
        else:
            keys = path.strip("/").split("/")
            target = data
            for key in keys[:-1]:
                target = target[int(key)] if isinstance(target, list) else target[key]
            last = keys[-1]
            if isinstance(target, list):
                target[int(last)] = update["value"]
            else:
                target[last] = update["value"]
    return data


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
        self.assertTrue(data["exclusivity"]["open"])
        self.assertEqual(data["progress"]["left"], 1)


if __name__ == "__main__":
    unittest.main()
