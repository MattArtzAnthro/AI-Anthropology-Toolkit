"""Synthetic desks for the desk tests: a codebook desk and a rulings desk built from the
community-garden fixtures."""

import json
from pathlib import Path

from ai_anthro_toolkit.desk import cards

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "desk"


def load(name):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def codebook_desk(**changes):
    desk = {
        "desk_id": "desk-0a1b2c3d",
        "stage": "codebook",
        "title": "Community garden interviews",
        "cards": cards.codebook_cards(load("codebook"), load("cases")),
    }
    desk.update(changes)
    return desk


def rulings_desk(**changes):
    codebook = load("codebook")
    desk = {
        "desk_id": "desk-9f8e7d6c",
        "stage": "rulings",
        "title": "Community garden interviews",
        "cards": cards.rulings_cards(load("coding_a"), load("coding_b"), codebook, load("proposals")),
        "codes": [r["code_label"] for r in codebook],
        "exclusive": False,
        "blind_first": True,
    }
    desk.update(changes)
    return desk
