"""Skill routing evals: descriptions must win the prompts they exist for.

Skill activation is driven by the description field in each SKILL.md. With
16 skills sharing anthropological vocabulary, two failure modes matter:
a description that no longer wins its own typical user prompts, and two
descriptions drifting close enough to collide. Both are checked here
deterministically (tf-idf cosine over description text — no model calls),
so CI catches routing regressions whenever a description changes.

    python3 -m unittest tests.test_skill_routing -v
"""

import math
import re
import unittest
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO / "skills"

# Two realistic user prompts per skill. Each must rank its own skill first
# across all 16 descriptions.
TRIGGER_PROMPTS = {
    "research-question": [
        "help me formulate my research question about migration and belonging",
        "is my research question too broad for an ethnographic study",
    ],
    "methodology-selection": [
        "which methods should I choose for my study of healing rituals",
        "help me select a methodology that fits an interpretivist stance",
    ],
    "research-plan": [
        "help me build a research plan for my two year fieldwork project",
        "draft the timeline and feasibility sections of my research plan",
    ],
    "irb-protocol": [
        "I need to write my IRB protocol for fieldwork with refugees",
        "help me with the risk assessment section of my ethics protocol",
    ],
    "informed-consent": [
        "design a verbal consent process for participants who cannot read",
        "write an informed consent form for my interview participants",
    ],
    "grant-proposal": [
        "help me write my NSF DDRIG grant proposal",
        "draft the budget justification for my Wenner-Gren application",
    ],
    "dissertation-prospectus": [
        "structure my dissertation prospectus before my defense",
        "my committee wants a 25 page prospectus draft next month",
    ],
    "research-writing": [
        "help me write the methods chapter of my dissertation",
        "structure a journal article about my ethnographic findings",
    ],
    "academic-review": [
        "how do I respond to reviewer 2 in my revise and resubmit",
        "help me write a peer review report for a manuscript",
    ],
    "conference-materials": [
        "write my AAA abstract for the annual meeting",
        "design the poster and slides for my conference presentation",
    ],
    "public-engagement": [
        "turn my research into an op-ed for a general audience",
        "prepare a policy brief from my findings for city officials",
    ],
    "job-materials": [
        "tailor my academic CV and cover letter for a tenure track job",
        "prepare my application package for a faculty position",
    ],
    "career-statements": [
        "write my teaching statement and research statement",
        "draft a diversity statement for my tenure file",
    ],
    "teaching-materials": [
        "design a syllabus for introduction to cultural anthropology",
        "create lesson plans and assignments for my seminar",
    ],
    "fieldwork-methods": [
        "create an interview guide for my upcoming fieldwork",
        "design an observation protocol and field note system",
    ],
    "qualitative-analysis": [
        "code my interview transcripts and build themes",
        "help me construct a codebook for thematic analysis",
    ],
    "digital-computational-methods": [
        "help me design a digital ethnography of an online community",
        "which computational text analysis method fits my forum corpus",
    ],
    "literature-review": [
        "help me do the literature review for my dissertation",
        "build an annotated bibliography and literature matrix from my sources",
    ],
}

STOPWORDS = frozenset(
    ("a an and are as at be but by for from has have how i in into is it my "
     "of on or should that the this to use used when whether which will "
     "with you your").split())


def _stem(token: str) -> str:
    for suffix in ("ing", "es", "ed", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[:len(token) - len(suffix)]
    return token


def _tokens(text: str) -> list[str]:
    return [_stem(t) for t in re.findall(r"[a-z]+(?:-[a-z]+)*", text.lower())
            if t not in STOPWORDS and len(t) > 2]


def _description(skill: str) -> str:
    text = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^description:\s*>?\s*\n?(.*?)^---", text,
                      re.DOTALL | re.MULTILINE)
    if not match:
        raise AssertionError(f"{skill}: cannot parse description frontmatter")
    return match.group(1)


def _load_vectors() -> dict[str, Counter]:
    docs = {skill: Counter(_tokens(_description(skill)))
            for skill in TRIGGER_PROMPTS}
    n = len(docs)
    df = Counter()
    for counts in docs.values():
        df.update(counts.keys())
    idf = {t: math.log(n / df[t]) + 1.0 for t in df}
    return {skill: Counter({t: c * idf[t] for t, c in counts.items()})
            for skill, counts in docs.items()}, idf


def _cosine(a: Counter, b: Counter) -> float:
    dot = sum(a[t] * b[t] for t in a.keys() & b.keys())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


class TestSkillRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors, cls.idf = _load_vectors()

    def _rank(self, prompt: str) -> list[tuple[float, str]]:
        q = Counter({t: c * self.idf.get(t, 1.0)
                     for t, c in Counter(_tokens(prompt)).items()})
        return sorted(((_cosine(q, vec), skill)
                       for skill, vec in self.vectors.items()), reverse=True)

    def test_prompts_cover_every_skill(self):
        on_disk = {p.name for p in SKILLS_DIR.iterdir()
                   if (p / "SKILL.md").exists()}
        self.assertEqual(on_disk, set(TRIGGER_PROMPTS),
                         "trigger prompts out of sync with skills/")

    def test_each_prompt_routes_to_its_own_skill(self):
        failures = []
        for skill, prompts in TRIGGER_PROMPTS.items():
            for prompt in prompts:
                ranked = self._rank(prompt)
                if ranked[0][1] != skill:
                    failures.append(
                        f"{prompt!r} -> {ranked[0][1]} (wanted {skill}; "
                        f"top3: {[(s, round(v, 3)) for v, s in ranked[:3]]})")
        self.assertEqual(failures, [],
                         "prompts misrouted:\n" + "\n".join(failures))

    def test_no_two_descriptions_near_collide(self):
        skills = sorted(self.vectors)
        for i, a in enumerate(skills):
            for b in skills[i + 1:]:
                sim = _cosine(self.vectors[a], self.vectors[b])
                self.assertLess(
                    sim, 0.55,
                    f"descriptions of {a} and {b} are converging "
                    f"(cosine {sim:.2f}) — routing between them is at risk")


if __name__ == "__main__":
    unittest.main()
