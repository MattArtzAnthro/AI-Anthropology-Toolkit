"""The standalone desk page with no server behind it: it reads each action into a
decision, and moves the desk, exactly as the server does for its MCP App view (R7.2)."""

import json
import unicodedata
import unittest

from ai_anthro_toolkit.desk import a2ui, cards, decisions, gate
from tests.package.desk_helpers import codebook_desk, load, rulings_desk
from tests.package.test_desk_a2ui import _node, _node_or_skip

CODEBOOK = codebook_desk()
RULINGS = rulings_desk()
OPEN_RULINGS = rulings_desk(blind_first=False)
EXCLUSIVE_RULINGS = rulings_desk(exclusive=True)
# A rulings desk whose second card has no proposal: nothing for its ruling to depart from.
UNPROPOSED = rulings_desk(cards=[dict(c, proposal=None) if n == 1 else c for n, c in enumerate(RULINGS["cards"])])


def _save(card_id, **decision):
    return ("save_decision", {"card_id": card_id, "decision": decision})


# Actions as the renderer sends them, each with its card's fields resolved: the ones a
# desk records and the ones it refuses, with the server's own wording.
CODEBOOK_ACTIONS = [
    _save("code-01", action=["adopt"], label="", definition="", target=[], parts="", note=""),
    _save("code-01", action=["adopt"], note="  Kept as drafted.  "),
    _save("code-02", action=["reword"], label=" Seed keeping ", definition=" Saving seed for next year. "),
    _save("code-02", action=["reword"], label="  ", definition="Saving seed."),
    _save("code-02", action=["merge"], target=["Land tenure"]),
    _save("code-02", action=["merge"], target=[]),
    _save("code-03", action=["split"], parts="Seed saving: keeping seed\n\n  Seed swapping : trading seed  \r\nSeed lore:"),
    _save("code-03", action=["split"], parts="Seed saving keeping seed"),
    _save("code-03", action=["split"], parts=": no label"),
    _save("code-03", action=["split"], parts="It's: fine\nit's broken"),
    _save("code-03", action=["split"], parts="Seed\xa0saving keeping seed"),
    _save("code-03", action=["split"], parts="\x1f: no label\nSeed lore: stories"),
    _save("code-03", action=["split"], parts="\ufeff: a label\nSeed lore: stories"),
    _save("code-03", action=["split"], parts="\x1fSeed saving\x85: keeping\x1c Seed swapping: trading\u2028x:\ufeff"),
    _save("code-02", action=["reword"], label="\ufeffSeed keeping\x1f", definition="\x85 Saving seed.\u3000"),
    _save("code-01", action=["adopt"], note="   "),
    _save("code-01", action=["it's\xa0"]),
    _save("code-01", action=[]),
    _save("code-01"),
    ("save_decision", {"card_id": "code-01", "decision": "adopt"}),
    _save("code-99", action=["adopt"]),
    ("save_decision", {"decision": {"action": ["adopt"]}}),
    ("save_decision", {"card_id": "  code-01 ", "decision": {"action": ["adopt"]}}),
    ("answer_exclusive", {"exclusive": ["yes"]}),
    ("answer_exclusive", {"exclusive": ["no"]}),
    ("answer_exclusive", {"exclusive": []}),
    ("answer_exclusive", {"exclusive": ["maybe"]}),
    ("answer_exclusive", {}),
    ("exclude_chunk", {"card_id": "code-01", "reason": "Off topic."}),
    ("finish", {"desk_id": "desk-0a1b2c3d"}),
    ("it's", {}),
]

_RULING_ID = RULINGS["cards"][0]["card_id"]
_CODES = RULINGS["codes"]
RULINGS_ACTIONS = [
    _save(_RULING_ID, codes=[_CODES[0]], is_rule=[], rule_text="", reason="", note=""),
    _save(_RULING_ID, codes=_CODES[:2], is_rule=["yes"], rule_text="  Selling below cost counts. ", note=" n "),
    _save(_RULING_ID, codes=[_CODES[0]], is_rule=["no"]),
    _save(_RULING_ID, codes=[_CODES[0]], is_rule=["maybe"]),
    _save(_RULING_ID, codes=[_CODES[0]], is_rule=["yes", "no"]),
    _save(_RULING_ID, codes=[_CODES[0]], is_rule=["\u200bmaybe\xad"]),
    _save(_RULING_ID, codes=[_CODES[0]], rule_text="   ", note="\x1f"),
    _save(_RULING_ID, codes=[a2ui.NO_CODE]),
    _save(_RULING_ID, codes=[a2ui.NO_CODE, _CODES[0]]),
    _save(_RULING_ID, codes=[]),
    _save(_RULING_ID),
    ("exclude_chunk", {"card_id": _RULING_ID, "reason": "  Interviewer talking. "}),
    ("exclude_chunk", {"card_id": _RULING_ID}),
    ("exclude_chunk", {"card_id": "chunk-nope", "reason": "x"}),
    ("answer_exclusive", {"exclusive": ["yes"]}),
]


def _py(fn):
    """A server function's answer as the node harness prints it: its JSON value, or its refusal."""
    try:
        return {"ok": json.loads(json.dumps(fn()))}
    except ValueError as exc:
        return {"error": str(exc)}


def _codebook_states(exclusive=True):
    """Saved states of a codebook desk as decisions are made, changed, and answered, each
    with the card just saved: the order wraps round, and one decision changes."""
    ids = [card["card_id"] for card in CODEBOOK["cards"]]
    order = [ids[1], ids[3 % len(ids)], ids[0], "exclusivity", *ids[2:], ids[1]]
    choices = [{"action": "adopt"}, {"action": "merge", "target": "Land tenure"}, {"action": "delete"},
               {"action": "split", "parts": [{"label": "A", "definition": "a"}, {"label": "B", "definition": "b"}]},
               {"action": "reword", "definition": "New."}]
    saved, states = {"decisions": {}, "exclusive": None}, []
    for n, card_id in enumerate(order):
        if card_id == "exclusivity":
            saved = dict(saved, exclusive=exclusive)
        else:
            saved = dict(saved, decisions={**saved["decisions"], card_id: choices[n % len(choices)]})
        states.append((json.loads(json.dumps(saved)), card_id))
    return states


def _rulings_states(desk):
    """Saved states of a rulings desk: a departing ruling before and after its rule answer, an
    agreeing ruling, no code, and an exclusion."""
    first, *rest = desk["cards"]
    other = next(code for code in desk["codes"] if code not in first["proposal"]["codes"])
    steps = [
        (first["card_id"], {"codes": [other]}),
        (first["card_id"], {"codes": [other], "is_rule": True, "rule_text": "A rule."}),
        (rest[0]["card_id"], {"codes": list(rest[0]["proposal"]["codes"]) if rest[0]["proposal"] else [desk["codes"][0]]}),
        (rest[1]["card_id"], {"none_apply": True, "is_rule": False}),
        (rest[2]["card_id"], {"exclude": {"reason": "Off topic."}}),
    ]
    saved, states = {"decisions": {}, "exclusive": None}, []
    for card_id, decision in steps:
        saved = dict(saved, decisions={**saved["decisions"], card_id: decision})
        states.append((json.loads(json.dumps(saved)), card_id))
    return states


class TestLocal(unittest.TestCase):
    def test_r7_2_local_carries_what_the_page_needs(self):
        local = a2ui.local(CODEBOOK)
        self.assertEqual(local["card_checksum"], cards.checksum(CODEBOOK["cards"]))
        self.assertEqual((local["desk_id"], local["stage"], local["release"]), (CODEBOOK["desk_id"], "codebook", {}))
        self.assertEqual(local["cards"], [{"card_id": c["card_id"], "code_label": c["code_label"], "proposal": None}
                                          for c in CODEBOOK["cards"]])

    def test_r7_2_a_rulings_desk_carries_each_card_as_drawn_after_its_ruling(self):
        local = a2ui.local(RULINGS)
        with_proposal = [c for c in RULINGS["cards"] if c["proposal"] is not None]
        self.assertTrue(with_proposal)
        self.assertEqual(set(local["release"]), {c["card_id"] for c in with_proposal})
        for card in with_proposal:
            plain, rule = local["release"][card["card_id"]]["plain"], local["release"][card["card_id"]]["rule"]
            self.assertIn(card["proposal"]["rationale"], json.dumps(plain))
            self.assertNotIn("Does this ruling state a rule?", json.dumps(plain))
            self.assertIn("Does this ruling state a rule?", json.dumps(rule))
        self.assertEqual([c["proposal"] for c in local["cards"]],
                         [None if c["proposal"] is None else c["proposal"]["codes"] for c in RULINGS["cards"]])

    def test_a_desk_of_another_stage_is_refused(self):
        with self.assertRaisesRegex(ValueError, "codebook or rulings"):
            a2ui.local(dict(CODEBOOK, stage="themes"))


class TestLocalParity(unittest.TestCase):
    """R7.2: the page's own reading, run in node, gives what the server gives."""

    def run_local(self, desk, cases):
        node = _node_or_skip(self)
        out = _node(node, ["scripts/local-parity.mjs"], json.dumps({"local": a2ui.local(desk), "cases": cases}))
        return json.loads(out)

    def test_r7_2_actions_read_into_the_same_decisions(self):
        for desk, actions in ((CODEBOOK, CODEBOOK_ACTIONS), (RULINGS, RULINGS_ACTIONS)):
            got = self.run_local(desk, [{"op": "action", "name": n, "context": c} for n, c in actions])
            for (name, context), answer in zip(actions, got, strict=True):
                with self.subTest(stage=desk["stage"], name=name, context=context):
                    self.assertEqual(answer, _py(lambda: a2ui.decision_from_action(desk, name, context)))

    def test_r7_2_the_corpus_has_decisions_and_refusals(self):
        for desk, actions in ((CODEBOOK, CODEBOOK_ACTIONS), (RULINGS, RULINGS_ACTIONS)):
            kinds = {next(iter(_py(lambda n=n, c=c: a2ui.decision_from_action(desk, n, c)))) for n, c in actions}
            self.assertEqual(kinds, {"ok", "error"}, desk["stage"])

    def test_r7_2_each_save_moves_the_desk_as_the_server_does(self):
        for desk, states in ((CODEBOOK, _codebook_states()), (CODEBOOK, _codebook_states(exclusive=False)),
                             (RULINGS, _rulings_states(RULINGS)), (OPEN_RULINGS, _rulings_states(OPEN_RULINGS)),
                             (UNPROPOSED, _rulings_states(UNPROPOSED))):
            got = self.run_local(desk, [{"op": "after", "saved": s, "card_id": c} for s, c in states])
            for (saved, card_id), answer in zip(states, got, strict=True):
                with self.subTest(stage=desk["stage"], card_id=card_id, saved=saved):
                    self.assertEqual(answer, _py(lambda: a2ui.after_decision(desk, saved, card_id)))

    def test_r7_2_a_save_the_server_would_refuse_is_refused(self):
        empty = {"decisions": {}, "exclusive": None}
        cases = [(CODEBOOK, empty, "exclusivity"), (CODEBOOK, empty, "code-01"), (CODEBOOK, empty, "code-99"),
                 (RULINGS, empty, _RULING_ID)]
        stray = {"decisions": {"code-99": {"action": "adopt"}}, "exclusive": None}
        [answer] = self.run_local(CODEBOOK, [{"op": "restore", "saved": stray}])
        expected = _py(lambda: a2ui.restore(CODEBOOK, stray))
        self.assertIn("error", expected)
        self.assertEqual(answer, expected)
        for desk, saved, card_id in cases:
            [answer] = self.run_local(desk, [{"op": "after", "saved": saved, "card_id": card_id}])
            with self.subTest(card_id=card_id):
                expected = _py(lambda: a2ui.after_decision(desk, saved, card_id))
                self.assertIn("error", expected)
                self.assertEqual(answer, expected)

    def test_r7_2_reopening_restores_as_the_server_does(self):
        for desk, states in ((CODEBOOK, _codebook_states()), (CODEBOOK, _codebook_states(exclusive=False)),
                             (RULINGS, _rulings_states(RULINGS)), (UNPROPOSED, _rulings_states(UNPROPOSED))):
            saves = [s for s, _ in states] + [{"decisions": {}, "exclusive": None}]
            got = self.run_local(desk, [{"op": "restore", "saved": s} for s in saves])
            for saved, answer in zip(saves, got, strict=True):
                with self.subTest(stage=desk["stage"], saved=saved):
                    # The page already holds the surface; it applies what follows it.
                    self.assertEqual(answer, _py(lambda: a2ui.restore(desk, saved)[3:]))


def _saved(exclusive=None, **chosen):
    return {"decisions": chosen, "exclusive": exclusive}


def _adopt():
    return {"action": "adopt"}


def _split(*labels, definition="d"):
    return {"action": "split", "parts": [{"label": label, "definition": definition} for label in labels]}


# Saved states of a codebook desk (code-01 Shared labour, code-02 Charity framing, code-03
# Land tenure, code-04 Food access, ...): ones the server keeps and ones it refuses at save.
CODEBOOK_SAVES = [
    _saved(),
    _saved(True, **{"code-01": _adopt()}),
    _saved(False, **{"code-01": {"action": "reword", "definition": "New.", "label": "Shared labour"}}),
    _saved(**{"code-01": {"action": "reword", "definition": ""}}),
    _saved(**{"code-01": {"action": "reword", "definition": " \x1f\x85"}}),
    _saved(**{"code-01": {"action": "reword", "definition": "\ufeff"}}),
    _saved(**{"code-01": {"action": "reword", "definition": "New.", "label": "Charity framing"}}),
    _saved(**{"code-01": {"action": "reword", "definition": "New.", "label": "Charity framing\x1f"}}),
    _saved(**{"code-01": {"action": "reword", "definition": "New.", "label": "\ufeffCharity framing"}}),
    _saved(**{"code-01": {"action": "reword", "definition": "New.", "label": "Charity framing"}, "code-02": {"action": "delete"}}),
    _saved(**{"code-01": {"action": "merge", "target": ""}}),
    _saved(**{"code-01": {"action": "merge", "target": "Shared labour"}}),
    _saved(**{"code-01": {"action": "merge", "target": "Land\xa0tenure"}}),
    _saved(**{"code-01": {"action": "merge", "target": "It's \u200b\x80\U0001f331"}}),
    _saved(**{"code-01": {"action": "merge", "target": "Land tenure"}}),
    _saved(**{"code-01": {"action": "merge", "target": "Land tenure"}, "code-03": {"action": "delete"}}),
    _saved(**{"code-01": {"action": "merge", "target": "Land tenure"}, "code-03": {"action": "merge", "target": "Food access"}}),
    _saved(**{"code-01": {"action": "merge", "target": "Land tenure"}, "code-03": _split("A", "B")}),
    _saved(**{"code-01": _split("A")}),
    _saved(**{"code-01": {"action": "split", "parts": []}}),
    _saved(**{"code-01": _split("A", "A")}),
    _saved(**{"code-01": _split("A", "B", definition="")}),
    _saved(**{"code-01": _split("A", " ")}),
    _saved(**{"code-01": _split("A", "Food access")}),
    _saved(**{"code-01": _split("A", "B"), "code-02": _split("B", "C")}),
    _saved(**{"code-01": _split("A", "B"), "code-04": {"action": "delete"}}),
    _saved(**{"code-01": {"action": "it's"}}),
    _saved(**{"code-01": {}}),
    _saved(**{"code-99": _adopt()}),
    _saved(**{"code-01": {"action": "reword", "definition": ""}, "code-02": _split("A"),
              "code-03": {"action": "merge", "target": "Nope"}}),
]

_FIRST, _SECOND = (card["card_id"] for card in RULINGS["cards"][:2])
_A, _B = RULINGS["codes"][:2]
# Saved states of a rulings desk, the same way.
RULINGS_SAVES = [
    _saved(),
    _saved(**{_FIRST: {"codes": [_A]}}),
    _saved(**{_FIRST: {"codes": [_A, _B], "is_rule": True, "rule_text": "A rule."}}),
    _saved(**{_FIRST: {"none_apply": True, "is_rule": False}}),
    _saved(**{_FIRST: {"exclude": {"reason": "Off topic."}}}),
    _saved(**{_FIRST: {"exclude": {"reason": ""}}}),
    _saved(**{_FIRST: {"exclude": {"reason": "\x1f\x85"}}}),
    _saved(**{_FIRST: {"exclude": {"reason": "\ufeff"}}}),
    _saved(**{_FIRST: {"exclude": {"reason": "x"}, "is_rule": False}}),
    _saved(**{_FIRST: {"exclude": "x"}}),
    _saved(**{_FIRST: {"codes": [_A], "is_rule": True}}),
    _saved(**{_FIRST: {"codes": [_A], "is_rule": True, "rule_text": " \u3000"}}),
    _saved(**{_FIRST: {"codes": [_A], "is_rule": "yes"}}),
    _saved(**{_FIRST: {"codes": ["Nope", "It's\xa0"]}}),
    _saved(**{_FIRST: {"codes": [_A, _A]}}),
    _saved(**{_FIRST: {"codes": []}}),
    _saved(**{_FIRST: {"codes": _A}}),
    _saved(**{_FIRST: {"codes": [_A], "none_apply": True}}),
    _saved(**{_FIRST: {}}),
    _saved(**{_FIRST: {"none_apply": False}}),
    _saved(**{_FIRST: {"codes": [_A], "rule_text": 3}}),
    _saved(**{_FIRST: {"codes": [_A], "reason": "x"}}),
    _saved(True, **{_FIRST: {"codes": [_A]}}),
    _saved(**{"chunk-nope": {"codes": [_A]}}),
    _saved(**{_FIRST: {"codes": [_A], "is_rule": True}, _SECOND: {"exclude": {"reason": ""}}}),
]
# On a desk whose codes are mutually exclusive.
EXCLUSIVE_SAVES = [
    _saved(**{_FIRST: {"codes": [_A]}}),
    _saved(**{_FIRST: {"codes": [_A, _B]}}),
    _saved(**{_FIRST: {"none_apply": True}}),
    _saved(False, **{_FIRST: {"codes": [_A]}}),
]
SAVES = ((CODEBOOK, CODEBOOK_SAVES), (RULINGS, RULINGS_SAVES), (EXCLUSIVE_RULINGS, EXCLUSIVE_SAVES),
         (UNPROPOSED, [_saved(**{_SECOND: {"codes": [_A]}})]))


def _server_check(desk, saved):
    return _py(lambda: gate.check_save(desk, saved, load("codebook")))


class TestSaveChecks(unittest.TestCase):
    """R7.2: the page keeps only what desk_sync would keep, refusing the rest in its words."""

    def run_local(self, desk, cases):
        node = _node_or_skip(self)
        out = _node(node, ["scripts/local-parity.mjs"], json.dumps({"local": a2ui.local(desk), "cases": cases}))
        return json.loads(out)

    def test_r7_2_the_page_refuses_a_save_as_the_server_does(self):
        for desk, saves in SAVES:
            got = self.run_local(desk, [{"op": "check", "saved": s} for s in saves])
            for saved, answer in zip(saves, got, strict=True):
                with self.subTest(stage=desk["stage"], saved=saved):
                    self.assertEqual(answer, _server_check(desk, saved))

    def test_the_save_corpus_has_saves_and_refusals(self):
        for desk, saves in SAVES[:3]:
            kinds = {next(iter(_server_check(desk, s))) for s in saves}
            self.assertEqual(kinds, {"ok", "error"}, desk["stage"])

    def test_r7_2_a_finished_page_hands_over_decisions_the_gate_accepts(self):
        """With every save checked as the server checks it, a page with nothing left open
        holds a document the import gate's full check accepts."""
        every = {card["card_id"]: _adopt() for card in CODEBOOK["cards"]}
        ruled = {card["card_id"]: {"codes": [_A], "is_rule": False} for card in RULINGS["cards"]}
        finished = [
            (CODEBOOK, _saved(True, **every)),
            (CODEBOOK, _saved(False, **dict(every, **{"code-01": {"action": "merge", "target": "Land tenure"},
                                                      "code-02": _split("A", "B")}))),
            (RULINGS, _saved(**ruled)),
            (RULINGS, _saved(**dict(ruled, **{_FIRST: {"exclude": {"reason": "Off topic."}}}))),
            (UNPROPOSED, _saved(**{c["card_id"]: {"codes": [_B]} if c["proposal"] is None else ruled[c["card_id"]]
                                  for c in UNPROPOSED["cards"]})),
        ]
        for desk, saved in finished:
            with self.subTest(stage=desk["stage"], saved=saved):
                self.assertEqual(_server_check(desk, saved), {"ok": None})
                self.assertEqual(a2ui._status(desk, saved, None)["progress"]["left"], 0)
                doc = decisions.Decisions(desk["desk_id"], cards.checksum(desk["cards"]), saved["exclusive"], saved["decisions"])
                self.assertEqual(decisions.validate(desk, doc, complete=True), [])

    def test_r7_2_a_desk_without_a_codebook_check_refuses_nothing_more(self):
        """The page carries no codebook records: the label check reads only the cards."""
        clash = _saved(**{"code-01": _split("A", "Food access")})
        self.assertEqual(_server_check(CODEBOOK, clash), _py(lambda: gate.check_save(CODEBOOK, clash, None)))


def _swept():
    """One character from each code point in the ranges most text uses and in the astral
    planes' symbols and tags, skipping those unassigned in Python's Unicode database: which
    are assigned changes with the Unicode version each runtime ships."""
    points = [*range(0x3100), *range(0xFE00, 0x10000), *range(0x1F300, 0x1F400), *range(0xE0000, 0xE0080)]
    return [chr(n) for n in points if unicodedata.category(chr(n)) not in ("Cn", "Cs")]


def _lines(text):
    """str.splitlines(), with the empty line after a last break that the page's split keeps."""
    ends = text.splitlines(keepends=True)
    return text.splitlines() + ([""] if ends and ends[-1] != text.splitlines()[-1] else [])


class TestText(unittest.TestCase):
    def test_r7_2_strip_repr_and_lines_are_pythons(self):
        """The page trims, quotes and splits text as the server does, character by character."""
        node = _node_or_skip(self)
        texts = [f"{c}x{c}" for c in _swept()] + [f"a{c}b" for c in _swept()] + ["it's", "say \"it's\"", "a\r\nb"]
        out = _node(node, ["scripts/local-parity.mjs"],
                    json.dumps({"local": a2ui.local(CODEBOOK), "cases": [{"op": "text", "texts": texts}]}))
        [answer] = json.loads(out)
        expected = [[s.strip(), repr(s), _lines(s)] for s in texts]
        for text, got, want in zip(texts, answer["ok"], expected, strict=True):
            with self.subTest(text=text):
                self.assertEqual(got, want)


class TestLocalCarriesTheChecks(unittest.TestCase):
    def test_r7_2_local_carries_what_the_save_checks_read(self):
        local = a2ui.local(CODEBOOK)
        self.assertEqual([c["code_label"] for c in local["cards"]], [c["code_label"] for c in CODEBOOK["cards"]])
        local = a2ui.local(EXCLUSIVE_RULINGS)
        self.assertEqual((local["codes"], local["exclusive"]), (RULINGS["codes"], True))


if __name__ == "__main__":
    unittest.main()
