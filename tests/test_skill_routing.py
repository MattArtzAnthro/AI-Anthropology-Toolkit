"""Skill routing evals: descriptions must win the prompts they exist for.

Skill activation is driven by the description field in each SKILL.md. With
this many skills sharing anthropological vocabulary, two failure modes matter:
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

# Two or three realistic user prompts per skill. Each must rank its own
# skill first across every description in the library.
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
        "prepare an anonymous version of my manuscript for blind peer review",
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
    "applied-practice": [
        "write a statement of work for a client research engagement",
        "turn my findings into a stakeholder readout for the product team",
    ],
    "paper-planning": [
        "I have all my material but I cannot tell what the paper argues",
        "what is my contribution and how should I order the argument",
    ],
    "tool-building": [
        "help me build a scraper for the archive my fieldsite uses",
        "I want to make my own research tool but I have never written a spec",
        "walk me through specifying an MCP server before any code gets written",
        "my scraper broke and I need to repair it without wrecking anything",
    ],
    "manuscript-markup": [
        "my editor sent the chapter back with comments in the document",
        "work through the tracked changes and comments in this docx",
        "read the marked up file my advisor returned",
        "draft the letter to my editor saying what I changed",
    ],
    "proof-review": [
        "my page proofs arrived from the publisher",
        "compare the typeset pdf proof against the manuscript I submitted",
        "what corrections should I send the press about these proofs",
        "is this proof safe to approve or did the compositor break something",
    ],
    "repeated-work": [
        "I keep doing this same cleanup by hand every week",
        "there must be a better way to do this than doing it manually",
        "this is the third time I have written the same thing out",
        "should I automate this or just keep doing it",
    ],
    "ethnographic-generalization": [
        "can I generalize from one fieldsite to a broader insight",
        "what kind of generalization can my ethnography support",
        "help me set scope conditions and transferability for my findings",
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

    def test_every_prompt_wins_by_a_margin(self):
        """Winning is not enough; a one-vote win is a coin flip next release.

        test_each_prompt_routes_to_its_own_skill checks rank, which is a
        boolean over a population-relative metric: every added description
        shifts every IDF weight, so a prompt can keep its rank while its
        margin collapses. That is not hypothetical. The 20th skill pushed
        applied-practice off its own prompt by 0.009, and the 21st arrived
        holding two siblings' prompts by 0.036 and 0.047 while the suite
        reported green.

        MARGIN_FLOOR is a ratchet. The tightest margin in the corpus at the
        time of writing was 0.007 (public-engagement vs
        dissertation-prospectus), which is pre-existing and marginal. Lower
        this constant only with a stated reason; raising it is free once the
        weak pairs are repaired.
        """
        MARGIN_FLOOR = 0.005
        thin = []
        for skill, prompts in TRIGGER_PROMPTS.items():
            for prompt in prompts:
                ranked = self._rank(prompt)
                margin = ranked[0][0] - ranked[1][0]
                if margin < MARGIN_FLOOR:
                    thin.append(
                        (margin, f"{margin:+.4f}  {skill} holds its own prompt "
                                 f"over {ranked[1][1]} by almost nothing: "
                                 f"{prompt!r}"))
        self.assertEqual(
            [], [m for m, _ in thin],
            "margins below the floor; repair the weaker description, which is "
            "usually not the newest one:\n"
            + "\n".join(msg for _, msg in sorted(thin)))


if __name__ == "__main__":
    unittest.main()
