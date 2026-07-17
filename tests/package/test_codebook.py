"""Tests for the codebook generation core (ai_anthro_toolkit.codebook).

    python3.12 -m unittest tests.package.test_codebook -v
"""

import json
import unittest

import numpy as np

from ai_anthro_toolkit import codebook as cb
from ai_anthro_toolkit.llm import DelegatedLLM, WorkPacket
from ai_anthro_toolkit.models import CodeEntry


DOCUMENTS = {
    "interview_1.txt": (
        "The nurses described the new triage system as opaque. "
        "They said the algorithm overrode their clinical judgment. "
        "Several felt their expertise was being displaced by the tool."
    ),
    "interview_2.txt": (
        "Managers framed the algorithm as a neutral efficiency gain. "
        "Frontline staff disputed this framing repeatedly. "
        "The opacity of the system was raised again in the meeting."
    ),
}

CANNED_EXTRACTION = json.dumps([
    {
        "label": "algorithmic opacity",
        "definition": "The system's decision logic is hidden from the workers it governs.",
        "extraction_type": "emergent",
        "example": "described the new triage system as opaque",
        "inclusion": "Use when opacity of automated decisions is at issue",
        "exclusion": "Not for general distrust of technology",
        "code_group": "Technology and Power",
    },
    {
        "label": "EXPERTISE_DISPLACEMENT",
        "definition": "Professional judgment is overridden or devalued by automated systems.",
        "extraction_type": "theoretical",
        "example": "expertise was being displaced by the tool",
        "inclusion": "Use when professional authority is displaced",
        "exclusion": "Not for routine task automation",
        "code_group": "Labor",
    },
    {
        "label": "CONTESTED_FRAMING",
        "definition": "Actors dispute how the technology and its effects are characterized.",
        "extraction_type": "emergent",
        "example": "Frontline staff disputed this framing repeatedly",
        "inclusion": "Use when framings of the system are contested",
        "exclusion": "Not for uncontested descriptions",
        "code_group": "Discourse",
    },
])


class FakeLLM:
    """LLM stub returning canned responses routed by prompt substring."""

    def __init__(self, routes=None, default="[]"):
        self.routes = routes or []  # list of (substring, response)
        self.default = default
        self.calls = []

    def __call__(self, prompt, *, system=None, temperature=0.3, max_tokens=4096):
        self.calls.append(prompt)
        for substring, response in self.routes:
            if substring in prompt:
                return response
        return self.default


class StubEmbedder:
    """Deterministic embedder: explicit vectors, one-hot fallback per text."""

    def __init__(self, mapping=None, dim=16):
        self.mapping = dict(mapping or {})
        self.dim = dim
        self._assigned = {}

    def _vector(self, text):
        if text in self.mapping:
            return np.asarray(self.mapping[text], dtype=float)
        if text not in self._assigned:
            index = len(self._assigned)
            if index >= self.dim:
                raise ValueError("StubEmbedder dimension exhausted")
            self._assigned[text] = index
        vec = np.zeros(self.dim)
        vec[self._assigned[text]] = 1.0
        return vec

    def __call__(self, texts):
        return np.array([self._vector(t) for t in texts])


def make_entry(label, definition, frequency=1, examples=None, sources=None,
               inclusion=None, exclusion=None, group="General",
               extraction_type="emergent", stance="critical"):
    return CodeEntry(
        label=label,
        definition=definition,
        inclusion_criteria=list(inclusion or []),
        exclusion_criteria=list(exclusion or []),
        examples=[dict(ex) for ex in (examples or [])],
        extraction_type=extraction_type,
        code_group=group,
        stance=stance,
        frequency=frequency,
        source_documents=list(sources or []),
    )


class TestParseJsonResponse(unittest.TestCase):
    def test_clean_array(self):
        self.assertEqual(cb.parse_json_response('[{"label": "A"}]'), [{"label": "A"}])

    def test_fenced_json(self):
        raw = '```json\n[{"label": "A"}]\n```'
        self.assertEqual(cb.parse_json_response(raw), [{"label": "A"}])

    def test_fenced_without_language(self):
        raw = '```\n[{"label": "A"}]\n```'
        self.assertEqual(cb.parse_json_response(raw), [{"label": "A"}])

    def test_single_object_wrapped(self):
        self.assertEqual(cb.parse_json_response('{"label": "A"}'), [{"label": "A"}])

    def test_truncated_array_recovers_complete_objects(self):
        raw = '[{"label": "A", "definition": "x"}, {"label": "B", "defin'
        self.assertEqual(cb.parse_json_response(raw),
                         [{"label": "A", "definition": "x"}])

    def test_garbage_returns_empty(self):
        self.assertEqual(cb.parse_json_response("no json here"), [])


class TestNormalizeExtractionType(unittest.TestCase):
    def test_exact_and_case(self):
        self.assertEqual(cb.normalize_extraction_type("theoretical"), "theoretical")
        self.assertEqual(cb.normalize_extraction_type("Methodological"), "methodological")

    def test_prefix_tolerance(self):
        self.assertEqual(cb.normalize_extraction_type("theo"), "theoretical")
        self.assertEqual(cb.normalize_extraction_type("emergent concept"), "emergent")

    def test_defaults_to_emergent(self):
        self.assertEqual(cb.normalize_extraction_type(""), "emergent")
        self.assertEqual(cb.normalize_extraction_type(None), "emergent")
        self.assertEqual(cb.normalize_extraction_type("banana"), "emergent")


class TestSanitizeCodeLabel(unittest.TestCase):
    def test_spaces_and_case(self):
        self.assertEqual(cb.sanitize_code_label("Actor Network Theory"),
                         "ACTOR_NETWORK_THEORY")

    def test_camel_case_split(self):
        self.assertEqual(cb.sanitize_code_label("algorithmicOpacity"),
                         "ALGORITHMIC_OPACITY")

    def test_length_cap(self):
        self.assertLessEqual(len(cb.sanitize_code_label("X" * 60)), 25)

    def test_special_characters(self):
        self.assertEqual(cb.sanitize_code_label("power/knowledge!"),
                         "POWER_KNOWLEDGE")


class TestChunkText(unittest.TestCase):
    def test_chunks_and_overlap(self):
        sentences = [f"Sentence number {i} has exactly seven words here." for i in range(40)]
        text = " ".join(sentences)
        chunks = cb.chunk_text(text, chunk_size=100, overlap=20)
        self.assertGreater(len(chunks), 1)
        # Overlap: the tail sentence of chunk 0 reappears at the start of chunk 1.
        tail_sentence = chunks[0].split(". ")[-1]
        self.assertIn(tail_sentence.rstrip("."), chunks[1])

    def test_short_text_single_chunk(self):
        chunks = cb.chunk_text("One short sentence.", chunk_size=400, overlap=50)
        self.assertEqual(chunks, ["One short sentence."])


class TestRenderExtractionPrompt(unittest.TestCase):
    def test_lens_and_focus_injection(self):
        rendered = cb.render_extraction_prompt("sts_actor_network", ["theoretical"], 6)
        self.assertIn("STS / Actor-Network analytical framework", rendered)
        self.assertIn("Heterogeneous networks of human and non-human actants", rendered)
        self.assertIn("Extract at most 6", rendered)
        self.assertIn("**Theoretical Constructs**", rendered)
        self.assertNotIn("**Methodological Approaches**", rendered)
        self.assertNotIn("**Emergent Concepts**", rendered)

    def test_ready_for_text_format(self):
        rendered = cb.render_extraction_prompt("critical", ["theoretical", "emergent"], 6)
        self.assertIn("{text}", rendered)
        final = rendered.format(text="CHUNK_MARKER")
        self.assertIn("CHUNK_MARKER", final)
        # JSON example braces survive both format stages.
        self.assertIn('[{"label": "CODE_NAME"', final)


class TestExtractCodes(unittest.TestCase):
    def test_assembles_code_entries_with_frequency_and_sources(self):
        llm = FakeLLM(default=CANNED_EXTRACTION)
        messages = []
        codebook = cb.extract_codes(DOCUMENTS, "critical", llm=llm,
                                    progress=messages.append)

        # Both short documents yield one chunk each: one LLM call per chunk.
        self.assertEqual(len(llm.calls), 2)
        # Labels are sanitised ("algorithmic opacity" -> ALGORITHMIC_OPACITY).
        self.assertEqual(set(codebook), {"ALGORITHMIC_OPACITY",
                                         "EXPERTISE_DISPLACEMENT",
                                         "CONTESTED_FRAMING"})
        code = codebook["ALGORITHMIC_OPACITY"]
        self.assertIsInstance(code, CodeEntry)
        self.assertEqual(code.frequency, 2)
        self.assertEqual(code.source_documents,
                         ["interview_1.txt", "interview_2.txt"])
        self.assertEqual(len(code.examples), 2)
        self.assertEqual(code.examples[0]["source"], "interview_1.txt")
        # Duplicate criteria are not re-appended.
        self.assertEqual(len(code.inclusion_criteria), 1)
        self.assertEqual(code.stance, "critical")
        self.assertEqual(code.extraction_type, "emergent")
        self.assertTrue(any("Extraction complete" in m for m in messages))

    def test_unparseable_chunk_is_skipped(self):
        llm = FakeLLM(default="not json at all")
        codebook = cb.extract_codes(DOCUMENTS, "critical", llm=llm)
        self.assertEqual(codebook, {})

    def test_delegated_mode_raises_work_packet(self):
        with self.assertRaises(WorkPacket) as ctx:
            cb.extract_codes(DOCUMENTS, "critical", llm=DelegatedLLM())
        prompt = ctx.exception.prompt
        self.assertIn("You are a qualitative research assistant working within "
                      "a Critical analytical framework", prompt)
        self.assertIn("CODE TYPES TO EXTRACT:", prompt)
        # The chunk text is embedded in the delegated prompt.
        self.assertIn("The nurses described the new triage system", prompt)


class TestSemanticDeduplication(unittest.TestCase):
    def _codebook(self):
        shared_def = "Power shapes how clinical work is organized and valued."
        return {
            "POWER_A": make_entry("POWER_A", shared_def, frequency=3,
                                  sources=["d1.txt"],
                                  inclusion=["Use for power dynamics"],
                                  examples=[{"text": "quote one", "source": "d1.txt"}]),
            "POWER_B": make_entry("POWER_B", shared_def, frequency=1,
                                  sources=["d2.txt"],
                                  inclusion=["Use for institutional power"],
                                  examples=[{"text": "quote two", "source": "d2.txt"}]),
            "CARE_WORK": make_entry(
                "CARE_WORK", "Everyday practices of caring labor within the ward.",
                frequency=2, sources=["d1.txt"]),
        }

    def test_auto_merge_true_merges_identical_definitions(self):
        refined, report = cb.refine_codebook(
            self._codebook(), "critical", llm=FakeLLM(),
            min_frequency=1, auto_merge=True, embedder=StubEmbedder())

        self.assertNotIn("POWER_B", refined)
        merged = refined["POWER_A"]  # higher-frequency label kept
        self.assertEqual(merged.frequency, 4)
        self.assertEqual(merged.source_documents, ["d1.txt", "d2.txt"])
        self.assertEqual(merged.inclusion_criteria,
                         ["Use for power dynamics", "Use for institutional power"])
        self.assertEqual(len(merged.examples), 2)
        self.assertEqual(report["merge_suggestions"], [])
        self.assertEqual(report["validation"]["final_count"], 2)

    def test_auto_merge_false_returns_suggestions_only(self):
        refined, report = cb.refine_codebook(
            self._codebook(), "critical", llm=FakeLLM(),
            min_frequency=1, auto_merge=False, embedder=StubEmbedder())

        self.assertEqual(set(refined), {"POWER_A", "POWER_B", "CARE_WORK"})
        self.assertEqual(len(report["merge_suggestions"]), 1)
        suggestion = report["merge_suggestions"][0]
        self.assertEqual({suggestion["code_a"], suggestion["code_b"]},
                         {"POWER_A", "POWER_B"})
        self.assertGreaterEqual(suggestion["similarity"], 0.85)


class TestExampleDiversity(unittest.TestCase):
    def test_farthest_point_keeps_distinct_examples(self):
        examples = [
            {"text": "the ward was silent at night", "source": "d1.txt"},
            {"text": "the ward was silent at nighttime", "source": "d1.txt"},
            {"text": "budget meetings decided staffing levels", "source": "d2.txt"},
            {"text": "families negotiated visits with the charge nurse", "source": "d2.txt"},
        ]
        mapping = {
            examples[0]["text"]: [1.0, 0.0, 0.0],
            examples[1]["text"]: [0.999, 0.045, 0.0],  # near-duplicate of the first
            examples[2]["text"]: [0.0, 1.0, 0.0],
            examples[3]["text"]: [0.0, 0.0, 1.0],
        }
        codebook = {
            "WARD_LIFE": make_entry(
                "WARD_LIFE", "Daily institutional rhythms of the hospital ward.",
                frequency=1, examples=examples),
        }
        refined, _ = cb.refine_codebook(
            codebook, "critical", llm=FakeLLM(), min_frequency=1,
            max_examples=3, embedder=StubEmbedder(mapping))

        kept = [ex["text"] for ex in refined["WARD_LIFE"].examples]
        self.assertEqual(kept, [examples[0]["text"], examples[2]["text"],
                                examples[3]["text"]])


class TestRecordsContract(unittest.TestCase):
    EXPECTED_COLUMNS = [
        "code_label", "definition", "extraction_type", "code_group",
        "stance", "stance_key", "inclusion_criteria", "exclusion_criteria",
        "example_1", "example_2", "example_3", "frequency", "source_documents",
    ]

    def test_columns_order_and_stance_fields(self):
        codebook = {
            "CODE_ONE": make_entry(
                "CODE_ONE", "First definition of sufficient length here.",
                frequency=1, sources=["a.txt"],
                inclusion=["inc one", "inc two"],
                examples=[{"text": "only example", "source": "a.txt"}]),
            "CODE_TWO": make_entry(
                "CODE_TWO", "Second definition of sufficient length here.",
                frequency=5, sources=["a.txt", "b.txt"],
                examples=[{"text": "ex one", "source": "a.txt"},
                          {"text": "ex two", "source": "b.txt"}]),
        }
        records = cb.codebook_to_records(codebook, "critical_race")

        for record in records:
            self.assertEqual(list(record.keys()), self.EXPECTED_COLUMNS)
        columns = list(records[0].keys())
        self.assertEqual(columns.index("stance_key"), columns.index("stance") + 1)

        # Sorted by descending frequency.
        self.assertEqual([r["code_label"] for r in records],
                         ["CODE_TWO", "CODE_ONE"])
        top = records[0]
        self.assertEqual(top["stance"], "Critical Race")
        self.assertEqual(top["stance_key"], "critical_race")
        self.assertEqual(top["example_1"], "ex one")
        self.assertEqual(top["example_2"], "ex two")
        self.assertEqual(top["example_3"], "")
        self.assertEqual(top["source_documents"], "a.txt; b.txt")
        self.assertEqual(records[1]["inclusion_criteria"], "inc one; inc two")


class TestBuildCodebook(unittest.TestCase):
    def test_extract_then_refine_end_to_end(self):
        llm = FakeLLM(routes=[
            ("Extract codes from the text below", CANNED_EXTRACTION),
            ("You are refining code definitions", "[]"),
        ])
        refined, report = cb.build_codebook(
            DOCUMENTS, "critical", llm=llm,
            min_frequency=2, embedder=StubEmbedder())

        self.assertEqual(len(refined), 3)
        self.assertEqual(report["validation"]["final_count"], 3)
        self.assertEqual(report["validation"]["stance"], "critical")
        self.assertEqual(report["validation"]["quality_score"], 1.0)
        # Definition synthesis was invoked for the multi-occurrence codes.
        self.assertTrue(any("You are refining code definitions" in call
                            for call in llm.calls))

    def test_unknown_option_rejected(self):
        with self.assertRaises(TypeError):
            cb.build_codebook(DOCUMENTS, "critical", llm=FakeLLM(),
                              bogus_option=True)


if __name__ == "__main__":
    unittest.main()
