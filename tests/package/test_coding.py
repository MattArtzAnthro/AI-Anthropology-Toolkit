"""Tests for the coding, themes, and crosslens modules.

    python3.12 -m unittest tests.package.test_coding -v
"""

import math
import unittest

from ai_anthro_toolkit import coding, crosslens, themes
from ai_anthro_toolkit.llm import DelegatedLLM, WorkPacket
from ai_anthro_toolkit.models import CodeEntry, Theme

CODEBOOK_RECORDS = [
    {"code_label": "TRUST_BUILDING",
     "definition": "Building trust between patients and providers",
     "inclusion_criteria": "Mentions of trust or confidence",
     "exclusion_criteria": "Generic politeness",
     "example_1": "I trust my doctor"},
    {"code_label": "CARE_ACCESS",
     "definition": "Ability to reach and use care services",
     "inclusion_criteria": "Mentions of reaching or using services",
     "exclusion_criteria": "",
     "example_1": "The clinic is far away"},
    {"code_label": "COST_BARRIERS",
     "definition": "Financial obstacles to care",
     "inclusion_criteria": "Mentions of cost or affordability",
     "exclusion_criteria": "",
     "example_1": "I could not afford it"},
]

VALID_CODES = [r["code_label"] for r in CODEBOOK_RECORDS]

CHUNKS = [
    {"chunk_id": 1, "text": "I trust my doctor completely.", "speaker": "P1"},
    {"chunk_id": 2, "text": "The weather was nice that day.", "speaker": "P2"},
    {"chunk_id": 3, "text": "I could not afford the visit and the clinic was far.",
     "speaker": "P3"},
]

INDUCTIVE_GENERATION_REPLY = """**INDUCTIVE CODE: DIGITAL_DIVIDE**
Definition: Technology gaps shape access to care
Rationale: Recurs across interviews
Example: "I don't have internet at home"
When to Apply: Mentions of technology barriers
"""


class FakeLLM:
    """Scripted LLM double keyed on the pipeline's prompt shapes."""

    def __init__(self, deductive=None, retry=None, generation="", application=None):
        self.deductive = deductive or {}
        self.retry = retry or {}
        self.generation = generation
        self.application = application or {}
        self.calls = []

    def __call__(self, prompt, *, system=None, temperature=0.3, max_tokens=4096):
        self.calls.append({"prompt": prompt, "system": system,
                           "temperature": temperature, "max_tokens": max_tokens})
        if "NOT in the valid codebook" in prompt:
            text = prompt.split("Text to code: ", 1)[1].split("\n", 1)[0]
            return self.retry[text]
        if system and "deductive coding" in system:
            return self.deductive[prompt.removeprefix("Code this text: ")]
        if "INDUCTIVE CODING on interview transcripts" in prompt:
            return self.generation
        if system and system.startswith("Apply these INDUCTIVE CODES"):
            return self.application[prompt.removeprefix("Text: ")]
        raise AssertionError(f"unexpected prompt: {prompt[:80]!r}")


class TestMatchCodeToList(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(coding.match_code_to_list("CARE_ACCESS", VALID_CODES),
                         "CARE_ACCESS")

    def test_case_insensitive_match(self):
        self.assertEqual(coding.match_code_to_list("care_access", VALID_CODES),
                         "CARE_ACCESS")

    def test_truncated_prefix_recovered(self):
        valid = VALID_CODES + ["VALUE_BASED_CARE_TRANSFORMATION"]
        self.assertEqual(
            coding.match_code_to_list("VALUE_BASED_CARE_TRANSFOR", valid),
            "VALUE_BASED_CARE_TRANSFORMATION")

    def test_short_prefix_rejected(self):
        # 4 chars: below the 10-char floor and below 60% of the full code.
        self.assertIsNone(coding.match_code_to_list("CARE", VALID_CODES))

    def test_keyword_overlap_rejected(self):
        # Shares a word with CARE_ACCESS but is not a prefix of it.
        self.assertIsNone(coding.match_code_to_list("ACCESS", VALID_CODES))

    def test_ambiguous_prefix_rejected(self):
        valid = ["CARE_ACCESS_PRIMARY", "CARE_ACCESS_SPECIALTY"]
        self.assertIsNone(coding.match_code_to_list("CARE_ACCESS_", valid))


class TestBuildLensContext(unittest.TestCase):
    CONTEXT = {"project_name": "Trust Pilot",
               "research_question": "How do patients build trust?",
               "study_description": "Interviews at two clinics"}

    def test_includes_evaluation_modifier_and_research_context(self):
        result = coding.build_lens_context("evaluation", self.CONTEXT)
        self.assertIn("RESEARCH CONTEXT:", result)
        self.assertIn("Project: Trust Pilot", result)
        self.assertIn("Research Question: How do patients build trust?", result)
        self.assertIn("Study Context: Interviews at two clinics", result)
        self.assertIn("ANALYTICAL FRAMEWORK (Evaluation):", result)
        self.assertIn("Adopt an EVALUATION analytical lens", result)
        self.assertIn("Apply codes with attention to these analytical priorities.",
                      result)

    def test_resolves_display_name(self):
        result = coding.build_lens_context("Evaluation")
        self.assertIn("ANALYTICAL FRAMEWORK (Evaluation):", result)
        self.assertIn("Adopt an EVALUATION analytical lens", result)

    def test_unresolvable_lens_returns_generic_framing(self):
        result = coding.build_lens_context("quantum vibes")
        self.assertIn("ANALYTICAL FRAMEWORK (quantum vibes):", result)
        self.assertIn("Analytical lens: quantum vibes. "
                      "Apply codes through this analytical framework.", result)

    def test_empty_inputs_yield_empty_string(self):
        self.assertEqual(coding.build_lens_context(), "")


class TestRenderAndParse(unittest.TestCase):
    def test_render_coding_prompt(self):
        prompt = coding.render_coding_prompt("Some chunk text.", CODEBOOK_RECORDS, "")
        self.assertIn("CRITICAL: You may ONLY use codes from the VALID CODES list "
                      "below. Do NOT invent, modify, or abbreviate code names.", prompt)
        self.assertIn("VALID CODES (use ONLY these exact codes):\n"
                      "TRUST_BUILDING, CARE_ACCESS, COST_BARRIERS", prompt)
        self.assertIn("CODE: TRUST_BUILDING", prompt)
        self.assertIn("Include when: Mentions of trust or confidence", prompt)
        self.assertIn("Exclude when: Generic politeness", prompt)
        self.assertTrue(prompt.endswith("Code this text: Some chunk text."))

    def test_render_coding_prompt_injects_lens_context(self):
        lens_context = coding.build_lens_context("evaluation")
        prompt = coding.render_coding_prompt("Text.", CODEBOOK_RECORDS, lens_context)
        self.assertIn("ANALYTICAL FRAMEWORK (Evaluation):", prompt)

    def test_parse_valid_response(self):
        self.assertEqual(
            coding.parse_coding_response("TRUST_BUILDING, care_access", VALID_CODES),
            ["TRUST_BUILDING", "CARE_ACCESS"])

    def test_parse_rejects_hallucinated_code(self):
        self.assertEqual(
            coding.parse_coding_response("TRUST_BUILDING, FAKE_CODE", VALID_CODES),
            ["TRUST_BUILDING"])

    def test_parse_no_codes_and_empty(self):
        self.assertEqual(coding.parse_coding_response("NO_CODES", VALID_CODES), [])
        self.assertEqual(coding.parse_coding_response("no_codes", VALID_CODES), [])
        self.assertEqual(coding.parse_coding_response("  ", VALID_CODES), [])


class TestCodeChunks(unittest.TestCase):
    def _make_llm(self):
        return FakeLLM(
            deductive={
                CHUNKS[0]["text"]: "TRUST_BUILDING",
                CHUNKS[1]["text"]: "NO_CODES",
                CHUNKS[2]["text"]: "CARE_ACCESS, MADE_UP_CODE",
            },
            retry={
                CHUNKS[2]["text"]: "CARE_ACCESS, COST_BARRIERS",
            },
            generation=INDUCTIVE_GENERATION_REPLY,
            application={
                CHUNKS[0]["text"]: "DIGITAL_DIVIDE, HALLUCINATED_X",
                CHUNKS[1]["text"]: "none",
                CHUNKS[2]["text"]: "NONE",
            },
        )

    def test_hybrid_end_to_end(self):
        llm = self._make_llm()
        progress_events = []
        checkpoints = []
        records = coding.code_chunks(
            CHUNKS, CODEBOOK_RECORDS, llm=llm, approach="hybrid",
            progress=lambda stage, done, total: progress_events.append((stage, done, total)),
            checkpoint=lambda processed, recs: checkpoints.append(processed))

        self.assertEqual(len(records), 3)

        self.assertEqual(records[0]["Deductive_Codes"], "TRUST_BUILDING")
        self.assertEqual(records[0]["Inductive_Codes"], "DIGITAL_DIVIDE")
        self.assertEqual(records[0]["All_Codes"], "TRUST_BUILDING, DIGITAL_DIVIDE_IND")
        self.assertEqual(records[0]["Coding_Status"], "Both_Deductive_Inductive")

        self.assertEqual(records[1]["Deductive_Codes"], "")
        self.assertEqual(records[1]["Inductive_Codes"], "")
        self.assertEqual(records[1]["All_Codes"], "")
        self.assertEqual(records[1]["Coding_Status"], "No_Codes")

        self.assertEqual(records[2]["Deductive_Codes"], "CARE_ACCESS,COST_BARRIERS")
        self.assertEqual(records[2]["Inductive_Codes"], "")
        self.assertEqual(records[2]["All_Codes"], "CARE_ACCESS, COST_BARRIERS")
        self.assertEqual(records[2]["Coding_Status"], "Deductive_Only")

        # Input fields are preserved.
        self.assertEqual(records[0]["speaker"], "P1")
        self.assertEqual(records[2]["chunk_id"], 3)

        # The invalid-code retry ran at temperature 0.0 with the system prompt.
        retries = [c for c in llm.calls if "NOT in the valid codebook" in c["prompt"]]
        self.assertEqual(len(retries), 1)
        self.assertEqual(retries[0]["temperature"], 0.0)
        self.assertIn("CRITICAL: You may ONLY use codes", retries[0]["system"])
        self.assertIn("['MADE_UP_CODE']", retries[0]["prompt"])

        # Progress covered both phases; the final checkpoint fired.
        self.assertIn(("deductive", 3, 3), progress_events)
        self.assertIn(("inductive", 3, 3), progress_events)
        self.assertEqual(checkpoints[-1], 3)

    def test_delegated_mode_raises_work_packet_with_deductive_prompt(self):
        codebook = {
            r["code_label"]: CodeEntry(
                label=r["code_label"], definition=r["definition"],
                inclusion_criteria=[r["inclusion_criteria"]] if r["inclusion_criteria"] else [],
                exclusion_criteria=[r["exclusion_criteria"]] if r["exclusion_criteria"] else [],
                examples=[{"text": r["example_1"], "source": "doc"}])
            for r in CODEBOOK_RECORDS
        }
        with self.assertRaises(WorkPacket) as ctx:
            coding.code_chunks(CHUNKS, codebook, llm=DelegatedLLM(),
                               approach="deductive")
        packet = ctx.exception
        self.assertEqual(packet.prompt, "Code this text: I trust my doctor completely.")
        self.assertIn("CRITICAL: You may ONLY use codes from the VALID CODES list below.",
                      packet.system)
        self.assertIn("CODE: TRUST_BUILDING", packet.system)
        self.assertIn("Include when: Mentions of trust or confidence", packet.system)


THEME_REPLY = """THEME 1: Trust as Foundation
Core Concept: Trust shapes every interaction between patients and providers. It develops slowly and erodes quickly.
Sub-themes:
  a) Provider Trust: Trust in individual providers
  b) System Trust: Trust in institutions and processes
Key Finding: Trust is central to care engagement, supported by TRUST_BUILDING and DIGITAL_DIVIDE_IND
Supporting Codes: TRUST_BUILDING, DIGITAL_DIVIDE_IND
Evidence Strength: Strong (12 combined code applications: TRUST_BUILDING=8, DIGITAL_DIVIDE_IND=4)
Lens Convergence: CONVERGENT: supported by Critical, Feminist lenses

THEME 2: Access Barriers
Core Concept: Cost and logistics restrict who can reach care at all.
Sub-themes:
  a) Cost Barriers: Direct and indirect costs of care
  b) Logistics: Transportation and scheduling constraints
Key Finding: Access is constrained, supported by CARE_ACCESS and COST_BARRIERS
Supporting Codes: CARE_ACCESS, COST_BARRIERS
Evidence Strength: Moderate (6 combined code applications: CARE_ACCESS=4, COST_BARRIERS=2)
Lens Convergence: LENS-SPECIFIC: primarily from Critical lens
"""

CODED_RECORDS = [
    {"chunk_id": 1, "text": "I trust my doctor completely.",
     "Deductive_Codes": "TRUST_BUILDING", "Inductive_Codes": "DIGITAL_DIVIDE",
     "All_Codes": "TRUST_BUILDING, DIGITAL_DIVIDE_IND",
     "Coding_Status": "Both_Deductive_Inductive"},
    {"chunk_id": 2, "text": "The weather was nice that day.",
     "Deductive_Codes": "", "Inductive_Codes": "", "All_Codes": "",
     "Coding_Status": "No_Codes"},
    {"chunk_id": 3, "text": "I could not afford the visit and the clinic was far.",
     "Deductive_Codes": "CARE_ACCESS,COST_BARRIERS", "Inductive_Codes": "",
     "All_Codes": "CARE_ACCESS, COST_BARRIERS", "Coding_Status": "Deductive_Only"},
]


class ThemeFakeLLM:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def __call__(self, prompt, *, system=None, temperature=0.3, max_tokens=4096):
        self.calls.append({"prompt": prompt, "system": system,
                           "temperature": temperature, "max_tokens": max_tokens})
        return self.reply


class TestBuildThemes(unittest.TestCase):
    def test_parses_canned_reply_into_theme_objects(self):
        llm = ThemeFakeLLM(THEME_REPLY)
        result = themes.build_themes(CODED_RECORDS, llm=llm)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(isinstance(t, Theme) for t in result))

        first = result[0]
        self.assertEqual(first.name, "Theme 1: Trust as Foundation")
        self.assertTrue(first.definition.startswith("Trust shapes every interaction"))
        self.assertEqual(first.codes, ["DIGITAL_DIVIDE_IND", "TRUST_BUILDING"])
        self.assertEqual([s["name"] for s in first.sub_themes],
                         ["Provider Trust", "System Trust"])
        self.assertEqual([e["chunk_id"] for e in first.evidence], [1])
        self.assertEqual(first.convergence_tag, "")  # single-lens run

        second = result[1]
        self.assertEqual(second.name, "Theme 2: Access Barriers")
        self.assertEqual(second.codes, ["CARE_ACCESS", "COST_BARRIERS"])
        self.assertEqual([e["chunk_id"] for e in second.evidence], [3])

        prompt = llm.calls[0]["prompt"]
        self.assertIn("TOP DEDUCTIVE CODES:", prompt)
        self.assertIn("• TRUST_BUILDING: 1 occurrences", prompt)
        self.assertIn("• DIGITAL_DIVIDE_IND: 1 occurrences", prompt)
        self.assertNotIn("Lens Convergence", prompt)
        self.assertNotIn("CROSS-LENS ANALYSIS", prompt)

    def test_convergence_tags_with_convergence_info(self):
        llm = ThemeFakeLLM(THEME_REPLY)
        result = themes.build_themes(
            CODED_RECORDS, llm=llm,
            convergence_info={"summary": "Two lenses, mean agreement 0.4"})

        self.assertEqual(result[0].convergence_tag, "CONVERGENT")
        self.assertEqual(result[1].convergence_tag, "LENS-SPECIFIC")
        # Tag keywords never leak into the code lists.
        self.assertEqual(result[0].codes, ["DIGITAL_DIVIDE_IND", "TRUST_BUILDING"])
        self.assertEqual(result[1].codes, ["CARE_ACCESS", "COST_BARRIERS"])

        prompt = llm.calls[0]["prompt"]
        self.assertIn("CROSS-LENS ANALYSIS:\nTwo lenses, mean agreement 0.4", prompt)
        self.assertIn(themes.THEME_CONVERGENCE_TASK_LINE, prompt)
        self.assertIn(themes.THEME_CONVERGENCE_FORMAT_LINE, prompt)

    def test_code_patterns_frequencies_and_cooccurrence(self):
        patterns = themes.code_patterns(CODED_RECORDS)
        self.assertEqual(patterns["total_code_applications"], 4)
        self.assertEqual(patterns["unique_codes"], 4)
        self.assertEqual(patterns["all_codes_frequency"]["TRUST_BUILDING"], 1)
        self.assertEqual(patterns["deductive_frequency"],
                         {"TRUST_BUILDING": 1, "CARE_ACCESS": 1, "COST_BARRIERS": 1})
        self.assertEqual(patterns["inductive_frequency"], {"DIGITAL_DIVIDE_IND": 1})
        cooc = patterns["cooccurrence"]
        self.assertEqual(cooc["TRUST_BUILDING"]["DIGITAL_DIVIDE_IND"], 1)
        self.assertEqual(cooc["DIGITAL_DIVIDE_IND"]["TRUST_BUILDING"], 1)
        self.assertEqual(cooc["TRUST_BUILDING"]["TRUST_BUILDING"], 0)  # no self-pairs
        self.assertEqual(cooc["CARE_ACCESS"]["COST_BARRIERS"], 1)


class TestCompareLenses(unittest.TestCase):
    LENS_A = [
        {"chunk_id": 1, "Deductive_Codes": "X,Y", "Inductive_Codes": "",
         "All_Codes": "X, Y"},
        {"chunk_id": 2, "Deductive_Codes": "X", "Inductive_Codes": "Q",
         "All_Codes": "X, Q_IND"},
        {"chunk_id": 3, "Deductive_Codes": "", "Inductive_Codes": "",
         "All_Codes": ""},
    ]
    LENS_B = [
        {"chunk_id": 1, "Deductive_Codes": "X,Z", "Inductive_Codes": "",
         "All_Codes": "X, Z"},
        {"chunk_id": 2, "Deductive_Codes": "W", "Inductive_Codes": "",
         "All_Codes": "W"},
        {"chunk_id": 3, "Deductive_Codes": "X", "Inductive_Codes": "",
         "All_Codes": "X"},
    ]

    def test_hand_computed_jaccard_values(self):
        result = crosslens.compare_lenses({"A": self.LENS_A, "B": self.LENS_B})

        per_chunk = result["per_chunk_agreement"]
        # Chunk 1: {X,Y} vs {X,Z} -> |{X}| / |{X,Y,Z}| = 1/3.
        self.assertAlmostEqual(per_chunk["1"], 1 / 3)
        # Chunk 2: {X,Q} vs {W} -> 0/3 = 0.
        self.assertAlmostEqual(per_chunk["2"], 0.0)
        # Chunk 3: only one lens applied codes -> NaN.
        self.assertTrue(math.isnan(per_chunk["3"]))

        # Matrix averages over chunks with a non-empty union (all three here):
        # (1/3 + 0 + 0) / 3 = 0.111.
        self.assertEqual(result["agreement_matrix"]["A"]["B"], 0.111)
        self.assertEqual(result["agreement_matrix"]["B"]["A"], 0.111)
        self.assertEqual(result["agreement_matrix"]["A"]["A"], 1.0)

        # Mean over non-NaN per-chunk scores: (1/3 + 0) / 2 = 1/6.
        self.assertAlmostEqual(result["mean_agreement"], 1 / 6)

    def test_friction_point_detected(self):
        result = crosslens.compare_lenses({"A": self.LENS_A, "B": self.LENS_B})
        friction = result["friction_points"]
        self.assertEqual(len(friction), 1)  # only chunk 2 is < 0.3; NaN excluded
        self.assertEqual(friction[0]["chunk_id"], "2")
        self.assertAlmostEqual(friction[0]["agreement"], 0.0)
        self.assertEqual(friction[0]["codes_by_lens"], {"A": ["Q", "X"], "B": ["W"]})

    def test_consensus_and_divergent_codes(self):
        result = crosslens.compare_lenses({"A": self.LENS_A, "B": self.LENS_B})
        self.assertEqual(result["consensus_codes"], ["X"])
        self.assertEqual(result["divergent_codes"],
                         {"A": ["Q_IND", "Y"], "B": ["W", "Z"]})
        self.assertEqual(result["partial_overlap"], [])


if __name__ == "__main__":
    unittest.main()
