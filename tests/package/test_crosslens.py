"""Acceptance checks for the cross-lens comparison overhaul.

    python3.12 -m unittest tests.package.test_crosslens -v

Written from the ratified specification (2026-08-12) before the implementation
existed, and seen to fail. The specification corrects eight verified defects
in `compare_lenses`; each guarded behavior below names the defect it guards.

The superseded semantics pinned by tests/package/test_coding.py (corpus-level
consensus, NaN for a record-present-but-empty chunk) are revised in the
implementation phase as a spec-sanctioned change; these checks pin the
ratified semantics.

Ratified emptiness rule: a record that is present with no codes is a reading
(it counts: 0 against a non-empty set, 1.0 against another empty set); an
absent record means the lens was never asked, and that chunk's pairs
involving the lens are excluded rather than scored.
"""

import json
import math
import shutil
import tempfile
import unittest

from ai_anthro_toolkit import crosslens
from ai_anthro_toolkit.jobs import JobStore
from ai_anthro_toolkit.mcp import server


def rec(chunk_id, ded="", ind="", text=None, **extra):
    record = {"chunk_id": chunk_id, "Deductive_Codes": ded,
              "Inductive_Codes": ind}
    if text is not None:
        record["text"] = text
    record.update(extra)
    return record


CODEBOOK_SHARED = [
    {"code_label": "MUTUAL_AID",
     "definition": "Pooling resources or labor to support one another"},
    {"code_label": "STATE_ABSENCE",
     "definition": "Perceived withdrawal of government services"},
    {"code_label": "RECIPROCITY",
     "definition": "Recurring non-monetary exchange based on trust"},
]

CODEBOOK_CRITICAL = [
    {"code_label": "POWER_ASYMMETRY",
     "definition": "Unequal capacity to set the terms of exchange"},
    {"code_label": "EXTRACTED_LABOR",
     "definition": "Work rendered without recognition or return"},
]


class TestConsensusRequiresColocation(unittest.TestCase):
    """Defect 1: same label on disjoint chunks is not consensus."""

    def test_disjoint_application_is_shared_vocabulary_not_consensus(self):
        result = crosslens.compare_lenses({
            "interpretive": [rec("c1", "MUTUAL_AID"), rec("c2", "")],
            "critical": [rec("c1", ""), rec("c2", "MUTUAL_AID")],
        })
        self.assertNotIn("MUTUAL_AID", result["consensus_codes"])
        self.assertIn("MUTUAL_AID", result["shared_vocabulary_codes"])

    def test_colocated_application_is_consensus_with_counts(self):
        result = crosslens.compare_lenses({
            "interpretive": [rec("c1", "MUTUAL_AID"), rec("c2", "MUTUAL_AID")],
            "critical": [rec("c1", "MUTUAL_AID"), rec("c2", "")],
        })
        self.assertIn("MUTUAL_AID", result["consensus_codes"])
        # The evidence travels with the claim: the chunks where every lens
        # applied the code.
        self.assertEqual(result["consensus_co_applied_chunks"]["MUTUAL_AID"],
                         ["c1"])

    def test_three_lens_consensus_requires_all_lenses_on_one_chunk(self):
        # A and B co-apply on c1; C applies the same label only on c9.
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID"), rec("c9", "")],
            "b": [rec("c1", "MUTUAL_AID"), rec("c9", "")],
            "c": [rec("c1", ""), rec("c9", "MUTUAL_AID")],
        })
        self.assertNotIn("MUTUAL_AID", result["consensus_codes"])
        self.assertIn("MUTUAL_AID", result["shared_vocabulary_codes"])

    def test_tiers_partition_the_deductive_label_space(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID,RECIPROCITY"), rec("c2", "STATE_ABSENCE")],
            "b": [rec("c1", "MUTUAL_AID"), rec("c2", "RECIPROCITY,ONLY_B")],
            "c": [rec("c1", "MUTUAL_AID"), rec("c2", "")],
        })
        consensus = set(result["consensus_codes"])
        shared = set(result["shared_vocabulary_codes"])
        partial = set(result["partial_overlap"])
        divergent = set()
        for codes in result["divergent_codes"].values():
            divergent |= set(codes)
        tiers = [consensus, shared, partial, divergent]
        # Disjoint...
        for i in range(len(tiers)):
            for j in range(i + 1, len(tiers)):
                self.assertEqual(tiers[i] & tiers[j], set(),
                                 f"tiers {i} and {j} overlap")
        # ...and exhaustive over every deductive label any lens applied.
        all_labels = {"MUTUAL_AID", "RECIPROCITY", "STATE_ABSENCE", "ONLY_B"}
        self.assertEqual(consensus | shared | partial | divergent, all_labels)


class TestInductiveContainment(unittest.TestCase):
    """Defect 6: inductive discoveries are per-lens; string identity across
    lenses is a fact about naming, not vocabulary-governed agreement."""

    def test_inductive_never_matches_deductive_across_lenses(self):
        # Lens A discovered TRUST inductively; lens B has TRUST as a
        # deductive code. Under the old math these counted as agreement.
        result = crosslens.compare_lenses({
            "a": [rec("c1", "", ind="TRUST")],
            "b": [rec("c1", "TRUST")],
        })
        self.assertEqual(result["per_chunk_agreement"]["c1"], 0.0)

    def test_inductive_excluded_from_agreement_between_lenses(self):
        # Identical inductive discoveries do not lift the score either.
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", ind="TRUST")],
            "b": [rec("c1", "MUTUAL_AID", ind="TRUST")],
        })
        self.assertEqual(result["per_chunk_agreement"]["c1"], 1.0)
        result2 = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", ind="TRUST")],
            "b": [rec("c1", "MUTUAL_AID", ind="CARE")],
        })
        self.assertEqual(result2["per_chunk_agreement"]["c1"], 1.0,
                         "differing inductive discoveries must not depress "
                         "deductive agreement")

    def test_inductive_codes_reported_per_lens_with_counts(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", ind="TRUST"),
                  rec("c2", "", ind="TRUST")],
            "b": [rec("c1", "MUTUAL_AID"), rec("c2", "")],
        })
        self.assertEqual(result["inductive_codes_by_lens"]["a"]["TRUST"], 2)
        self.assertEqual(result["inductive_codes_by_lens"].get("b", {}), {})

    def test_inductive_codes_absent_from_all_tiers(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", ind="TRUST")],
            "b": [rec("c1", "MUTUAL_AID", ind="TRUST")],
        })
        for tier_key in ("consensus_codes", "shared_vocabulary_codes",
                         "partial_overlap"):
            for label in result[tier_key]:
                self.assertNotIn("TRUST", label)
        for codes in result["divergent_codes"].values():
            for label in codes:
                self.assertNotIn("TRUST", label)


class TestEmptinessAndCoverage(unittest.TestCase):
    """Defect 5: an absent record is not a reading of nothing."""

    def test_missing_record_excluded_from_pairwise(self):
        # Lens B was never run on c3. Its silence there is not disagreement.
        with_b_absent = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID"), rec("c2", "MUTUAL_AID"),
                  rec("c3", "MUTUAL_AID")],
            "b": [rec("c1", "MUTUAL_AID"), rec("c2", "MUTUAL_AID")],
        })
        self.assertEqual(with_b_absent["agreement_matrix"]["a"]["b"], 1.0)
        self.assertTrue(math.isnan(with_b_absent["per_chunk_agreement"]["c3"]))

    def test_coverage_reported_per_lens(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID"), rec("c2", ""), rec("c3", "X")],
            "b": [rec("c1", "MUTUAL_AID"), rec("c2", "")],
        })
        self.assertEqual(result["coverage"], {"a": 3, "b": 2})

    def test_chunk_universe_counts_reported(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID"), rec("c2", ""), rec("c3", "X")],
            "b": [rec("c1", "MUTUAL_AID"), rec("c2", "")],
        })
        self.assertEqual(result["chunks"]["total"], 3)
        self.assertEqual(result["chunks"]["compared"], 2)
        self.assertEqual(result["chunks"]["uncompared"], 1)

    def test_present_but_empty_record_is_a_reading(self):
        # Both lenses were asked; one saw nothing. That is divergence, not
        # a gap in the data.
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID")],
            "b": [rec("c1", "")],
        })
        self.assertEqual(result["per_chunk_agreement"]["c1"], 0.0)

    def test_two_empty_readings_agree(self):
        # Ratified: mutual "nothing applies here" is agreement (D3).
        result = crosslens.compare_lenses({
            "a": [rec("c1", "")],
            "b": [rec("c1", "")],
        })
        self.assertEqual(result["per_chunk_agreement"]["c1"], 1.0)


class TestWarnings(unittest.TestCase):
    """Commitments C1-C3 and the text-mismatch regime check."""

    def _warning_types(self, result):
        return {w["type"] for w in result["warnings"]}

    def test_missing_chunk_id_warns_and_excludes(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID"),
                  {"Deductive_Codes": "STATE_ABSENCE", "Inductive_Codes": ""}],
            "b": [rec("c1", "MUTUAL_AID")],
        })
        self.assertIn("missing_chunk_id", self._warning_types(result))
        # The id-less record does not become a phantom chunk.
        self.assertEqual(set(result["per_chunk_agreement"]), {"c1"})

    def test_duplicate_chunk_id_warns_last_wins(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID"), rec("c1", "STATE_ABSENCE")],
            "b": [rec("c1", "STATE_ABSENCE")],
        })
        self.assertIn("duplicate_chunk_id", self._warning_types(result))
        self.assertEqual(result["per_chunk_agreement"]["c1"], 1.0,
                         "last record wins per C2")

    def test_text_mismatch_across_lenses_warns(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", text="We pool money every month.")],
            "b": [rec("c1", "MUTUAL_AID", text="A different transcript line.")],
        })
        self.assertIn("text_mismatch", self._warning_types(result))

    def test_blank_text_does_not_mismatch(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", text="We pool money every month.")],
            "b": [rec("c1", "MUTUAL_AID", text="")],
        })
        self.assertNotIn("text_mismatch", self._warning_types(result))


class TestFrictionPayload(unittest.TestCase):
    """Defects 2 and 3: the adjudicator gets what the call requires, and
    nothing is truncated silently."""

    def test_friction_point_carries_chunk_text(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", text="We pool money every month.")],
            "b": [rec("c1", "STATE_ABSENCE", text="We pool money every month.")],
        })
        point = result["friction_points"][0]
        self.assertEqual(point["text"], "We pool money every month.")
        self.assertFalse(point["text_truncated"])

    def test_long_text_capped_with_flag(self):
        long_text = "word " * 200  # ~1000 chars
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", text=long_text)],
            "b": [rec("c1", "STATE_ABSENCE", text=long_text)],
        })
        point = result["friction_points"][0]
        self.assertEqual(len(point["text"]), 500)
        self.assertTrue(point["text_truncated"])

    def test_friction_payload_shows_inductive_codes_suffixed(self):
        # Excluded from the score, visible to the adjudicator, marked.
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", ind="TRUST")],
            "b": [rec("c1", "STATE_ABSENCE")],
        })
        point = result["friction_points"][0]
        self.assertIn("TRUST_IND", point["codes_by_lens"]["a"])
        self.assertIn("MUTUAL_AID", point["codes_by_lens"]["a"])

    def test_truncation_disclosed(self):
        lens_a = [rec(f"c{i:02d}", "MUTUAL_AID") for i in range(30)]
        lens_b = [rec(f"c{i:02d}", "STATE_ABSENCE") for i in range(30)]
        result = crosslens.compare_lenses({"a": lens_a, "b": lens_b})
        self.assertEqual(result["friction_total"], 30)
        self.assertEqual(len(result["friction_points"]), 20)

    def test_params_echoed_and_configurable(self):
        lens_a = [rec("c1", "MUTUAL_AID"), rec("c2", "MUTUAL_AID,RECIPROCITY")]
        lens_b = [rec("c1", "STATE_ABSENCE"), rec("c2", "MUTUAL_AID")]
        default = crosslens.compare_lenses({"a": lens_a, "b": lens_b})
        self.assertEqual(default["params"]["friction_threshold"], 0.3)
        self.assertEqual(default["params"]["top_n"], 20)
        # c2 scores 0.5 — inside a raised threshold, outside the default.
        raised = crosslens.compare_lenses({"a": lens_a, "b": lens_b},
                                          friction_threshold=0.6)
        self.assertEqual(raised["params"]["friction_threshold"], 0.6)
        self.assertEqual({p["chunk_id"] for p in raised["friction_points"]},
                         {"c1", "c2"})
        self.assertEqual({p["chunk_id"] for p in default["friction_points"]},
                         {"c1"})

    def test_tie_order_deterministic_and_documented(self):
        lens_a = [rec(f"c{i:02d}", "MUTUAL_AID") for i in range(5)]
        lens_b = [rec(f"c{i:02d}", "STATE_ABSENCE") for i in range(5)]
        result = crosslens.compare_lenses({"a": lens_a, "b": lens_b}, top_n=3)
        ids = [p["chunk_id"] for p in result["friction_points"]]
        self.assertEqual(ids, ["c00", "c01", "c02"],
                         "ties break lexicographically by chunk_id per C5")


class TestConvergencePoints(unittest.TestCase):
    """Defect 8: agreement gets the same scrutiny divergence gets."""

    def test_convergence_points_top_n_descending(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID"), rec("c2", "MUTUAL_AID,RECIPROCITY"),
                  rec("c3", "MUTUAL_AID")],
            "b": [rec("c1", "MUTUAL_AID"), rec("c2", "MUTUAL_AID"),
                  rec("c3", "STATE_ABSENCE")],
        })
        points = result["convergence_points"]
        self.assertGreaterEqual(len(points), 2)
        scores = [p["agreement"] for p in points]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(points[0]["chunk_id"], "c1")

    def test_convergence_point_carries_text_and_code_count(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID", text="We pool money every month.")],
            "b": [rec("c1", "MUTUAL_AID", text="We pool money every month.")],
        })
        point = result["convergence_points"][0]
        self.assertEqual(point["text"], "We pool money every month.")
        self.assertEqual(point["code_count"], 1,
                         "the adjudicator sees how thin the agreement is")

    def test_convergence_and_friction_never_overlap(self):
        # A chunk flagged as friction cannot also be surfaced as
        # convergence: the two lists partition attention at the same
        # disclosed threshold. (Added 2026-08-12 after the old design
        # returned the worst friction chunk inside convergence_points
        # on small corpora.)
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID"), rec("c2", "MUTUAL_AID"),
                  rec("c3", "RECIPROCITY")],
            "b": [rec("c1", "MUTUAL_AID"), rec("c2", "MUTUAL_AID"),
                  rec("c3", "STATE_ABSENCE")],
        })
        friction_ids = {p["chunk_id"] for p in result["friction_points"]}
        convergence_ids = {p["chunk_id"] for p in result["convergence_points"]}
        self.assertEqual(friction_ids & convergence_ids, set())
        self.assertIn("c3", friction_ids)
        self.assertNotIn("c3", convergence_ids)

    def test_convergence_requires_two_lenses_with_codes(self):
        # Mutual silence is not surfaced as consensus-to-inspect.
        result = crosslens.compare_lenses({
            "a": [rec("c1", ""), rec("c2", "MUTUAL_AID")],
            "b": [rec("c1", ""), rec("c2", "MUTUAL_AID")],
        })
        ids = {p["chunk_id"] for p in result["convergence_points"]}
        self.assertEqual(ids, {"c2"})


class TestDefinitionsAndRegime(unittest.TestCase):
    """Defect 4: the comparison states what produced it."""

    def test_code_definitions_resolved_when_codebooks_supplied(self):
        result = crosslens.compare_lenses(
            {"a": [rec("c1", "MUTUAL_AID")],
             "b": [rec("c1", "STATE_ABSENCE")]},
            codebooks_by_lens={"a": CODEBOOK_SHARED, "b": CODEBOOK_SHARED},
        )
        defs = result["code_definitions"]
        self.assertIn("MUTUAL_AID", defs["a"])
        self.assertIn("STATE_ABSENCE", defs["b"])
        # Normalized: only labels that appear in surfaced payloads.
        self.assertNotIn("RECIPROCITY", defs["a"])

    def test_regime_shared_when_checksums_match(self):
        result = crosslens.compare_lenses(
            {"a": [rec("c1", "MUTUAL_AID")],
             "b": [rec("c1", "MUTUAL_AID")]},
            codebooks_by_lens={"a": CODEBOOK_SHARED, "b": CODEBOOK_SHARED},
        )
        self.assertEqual(result["vocabulary"]["regime"], "shared")

    def test_regime_divergent_when_codebooks_differ(self):
        result = crosslens.compare_lenses(
            {"a": [rec("c1", "MUTUAL_AID")],
             "b": [rec("c1", "POWER_ASYMMETRY")]},
            codebooks_by_lens={"a": CODEBOOK_SHARED, "b": CODEBOOK_CRITICAL},
        )
        self.assertEqual(result["vocabulary"]["regime"], "divergent")

    def test_regime_unknown_without_codebooks_never_guessed(self):
        # Identical label sets are not evidence of a shared codebook.
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID")],
            "b": [rec("c1", "MUTUAL_AID")],
        })
        self.assertEqual(result["vocabulary"]["regime"], "unknown")


class TestCompatibilityAndScale(unittest.TestCase):
    def test_unchanged_keys_retain_names_and_types(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID")],
            "b": [rec("c1", "MUTUAL_AID")],
        })
        self.assertIsInstance(result["lenses"], list)
        self.assertIsInstance(result["per_chunk_agreement"], dict)
        self.assertIsInstance(result["mean_agreement"], float)
        self.assertIsInstance(result["agreement_matrix"], dict)
        self.assertIsInstance(result["friction_points"], list)
        self.assertIsInstance(result["divergent_codes"], dict)
        self.assertIsInstance(result["partial_overlap"], list)

    def test_matrix_properties_hold(self):
        result = crosslens.compare_lenses({
            "a": [rec("c1", "MUTUAL_AID,RECIPROCITY"), rec("c2", "X")],
            "b": [rec("c1", "MUTUAL_AID"), rec("c2", "Y")],
            "c": [rec("c1", "RECIPROCITY"), rec("c2", "X,Y")],
        })
        matrix = result["agreement_matrix"]
        for a in matrix:
            self.assertEqual(matrix[a][a], 1.0)
            for b in matrix[a]:
                self.assertEqual(matrix[a][b], matrix[b][a])
                self.assertGreaterEqual(matrix[a][b], 0.0)
                self.assertLessEqual(matrix[a][b], 1.0)

    def test_scale_smoke(self):
        lenses = {
            name: [rec(f"c{i:04d}", f"CODE_{(i + offset) % 7}")
                   for i in range(500)]
            for offset, name in enumerate(("a", "b", "c"))
        }
        result = crosslens.compare_lenses(lenses)
        self.assertEqual(result["chunks"]["total"], 500)
        self.assertEqual(len(result["friction_points"]), 20)
        self.assertEqual(result["friction_total"], 500)


class TestServerSeam(unittest.TestCase):
    """The MCP layer attaches what the pure module cannot know."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old_jobs = server._jobs
        server._jobs = JobStore(self._tmp)

    def tearDown(self):
        server._jobs = self._old_jobs
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _fake_coding_job(self, lens_key, records, codebook,
                         ratification_id=""):
        job_id = server._jobs.create("coding", {
            "lens_key": lens_key, "mode": "delegated",
            "approach": "deductive",
            "valid_codes": [r["code_label"] for r in codebook],
            "ratification_id": ratification_id,
        })
        server._jobs.save_artifact(job_id, "result.json", json.dumps(records))
        server._jobs.save_artifact(job_id, "codebook.json", json.dumps(codebook))
        return job_id

    def test_job_ids_path_attaches_definitions_and_regime(self):
        job_a = self._fake_coding_job(
            "interpretive",
            [rec("c1", "MUTUAL_AID", text="We pool money every month.")],
            CODEBOOK_SHARED, ratification_id="rat_a")
        job_b = self._fake_coding_job(
            "critical",
            [rec("c1", "STATE_ABSENCE", text="We pool money every month.")],
            CODEBOOK_SHARED, ratification_id="rat_a")
        out = server.compare_lenses(job_ids={"interpretive": job_a,
                                             "critical": job_b})
        self.assertEqual(out["vocabulary"]["regime"], "shared")
        self.assertIn("MUTUAL_AID", out["code_definitions"]["interpretive"])
        self.assertEqual(out["vocabulary"]["ratification_ids"],
                         {"interpretive": "rat_a", "critical": "rat_a"})

    def test_results_only_path_reports_regime_unknown(self):
        out = server.compare_lenses(results_by_lens={
            "a": [rec("c1", "MUTUAL_AID")],
            "b": [rec("c1", "MUTUAL_AID")],
        })
        self.assertEqual(out["vocabulary"]["regime"], "unknown")

    def test_start_coding_job_stores_ratification_id(self):
        ratified = server.ratify_codebook(
            codebook=CODEBOOK_SHARED,
            note="confirmed for acceptance-check run")
        rat_id = ratified["ratification_id"]
        job = server.start_coding_job(
            chunks=[{"chunk_id": "c1", "text": "We pool money."}],
            codebook=CODEBOOK_SHARED,
            ratification_id=rat_id,
            lens_key="interpretive",
            llm_mode="delegated")
        state = server._jobs.read(job["job_id"])
        self.assertEqual(state["payload"].get("ratification_id"), rat_id)


class TestNotebookDriftGuard(unittest.TestCase):
    """Parity by construction: the notebook imports the package's cross-lens
    math instead of re-implementing it. Red until the notebook is updated."""

    def test_notebook_has_no_independent_crosslens_implementation(self):
        import pathlib
        repo_root = pathlib.Path(__file__).resolve().parents[2]
        notebook = repo_root / "notebooks" / "Coding_and_Thematic_Analysis.ipynb"
        if not notebook.exists():
            self.skipTest("notebook not present in this checkout")
        source = notebook.read_text(encoding="utf-8")
        for redefined in ("def calculate_agreement_scores",
                          "def identify_consensus_and_divergent",
                          "len(a & b) / len(union)"):
            self.assertNotIn(
                redefined, source,
                f"{redefined!r} re-implements ai_anthro_toolkit.crosslens; "
                "the notebook must import the package so the two surfaces "
                "cannot drift")


if __name__ == "__main__":
    unittest.main()
