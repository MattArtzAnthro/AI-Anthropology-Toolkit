"""Boundaries a mutation run showed no test held.

A 2026-11-09 mutmut pass over crosslens.py and coding.py left these mutants
alive: the checksum ignoring one field, the mean of pairwise Jaccard turned
into a product, friction and convergence thresholds shifted by one
comparison, and prefix recovery accepting or refusing at the wrong length.
Each test below kills at least one of them.

    python3.12 -m unittest tests.package.test_mutation_gaps -v
"""

import unittest

from ai_anthro_toolkit import coding, crosslens


def rec(chunk_id, ded=""):
    return {"chunk_id": chunk_id, "Deductive_Codes": ded, "Inductive_Codes": "",
            "text": f"chunk {chunk_id}"}


class TestChecksumBinding(unittest.TestCase):
    BASE = [{"code_label": "mutual_aid", "definition": "Pooling resources"}]

    def test_each_field_alone_changes_the_checksum(self):
        base = crosslens.codebook_checksum(self.BASE)
        relabeled = [{"code_label": "mutual_help", "definition": "Pooling resources"}]
        redefined = [{"code_label": "mutual_aid", "definition": "Pooling labor"}]
        self.assertNotEqual(crosslens.codebook_checksum(relabeled), base)
        self.assertNotEqual(crosslens.codebook_checksum(redefined), base)

    def test_missing_fields_hash_as_empty(self):
        self.assertEqual(
            crosslens.codebook_checksum([{"code_label": "x"}]),
            crosslens.codebook_checksum([{"code_label": "x", "definition": ""}]))
        self.assertEqual(
            crosslens.codebook_checksum([{"definition": "d"}]),
            crosslens.codebook_checksum([{"code_label": "", "definition": "d"}]))

    def test_label_key_is_an_alias_for_code_label(self):
        self.assertEqual(
            crosslens.codebook_checksum([{"label": "mutual_aid",
                                          "definition": "Pooling resources"}]),
            crosslens.codebook_checksum(self.BASE))

    def test_checksum_is_pinned(self):
        # Pinned so that a change to the algorithm (encoding, length, field
        # set) is a deliberate decision: every stored ratification depends on it.
        value = crosslens.codebook_checksum(
            [{"code_label": "café", "definition": "Kaffeehaus"}])
        self.assertEqual(len(value), 16)
        self.assertEqual(value, "6ddd6e876e74ea4d")


class TestAgreementMath(unittest.TestCase):
    def test_three_lens_agreement_is_the_mean_of_pairwise_jaccard(self):
        out = crosslens.compare_lenses({
            "A": [rec("1", "x, y")], "B": [rec("1", "x")], "C": [rec("1", "y")]})
        # A-B 1/2, A-C 1/2, B-C 0/2.
        self.assertAlmostEqual(out["per_chunk_agreement"]["1"], (0.5 + 0.5 + 0.0) / 3)

    def test_matrix_cell_is_zero_when_no_chunk_has_codes(self):
        out = crosslens.compare_lenses({"A": [rec("1")], "B": [rec("1")]})
        self.assertEqual(out["agreement_matrix"]["A"]["B"], 0)


class TestFrictionConvergenceBoundaries(unittest.TestCase):
    def setUp(self):
        self.out = crosslens.compare_lenses({
            "A": [rec("a", "x, y"), rec("b", "x"), rec("c", "x"), rec("d", "x")],
            "B": [rec("a", "x"), rec("b", "y"), rec("c", "y"), rec("d", "x")],
        }, friction_threshold=0.5)

    def test_a_chunk_exactly_at_threshold_is_convergence_not_friction(self):
        friction = [p["chunk_id"] for p in self.out["friction_points"]]
        convergence = [p["chunk_id"] for p in self.out["convergence_points"]]
        self.assertNotIn("a", friction)
        self.assertIn("a", convergence)

    def test_ordering_and_tie_break(self):
        self.assertEqual([p["chunk_id"] for p in self.out["friction_points"]], ["b", "c"])
        self.assertEqual([p["chunk_id"] for p in self.out["convergence_points"]], ["d", "a"])
        self.assertEqual([p["agreement"] for p in self.out["convergence_points"]], [1.0, 0.5])
        self.assertEqual((self.out["friction_total"], self.out["convergence_total"]), (2, 2))

    def test_friction_sorts_by_agreement_before_chunk_id(self):
        # The lower-agreement chunk has the later id, so sorting by id alone fails.
        out = crosslens.compare_lenses({
            "A": [rec("c1", "x, y, z, w, v"), rec("c2", "x")],
            "B": [rec("c1", "x"), rec("c2", "y")]}, friction_threshold=0.5)
        self.assertEqual([p["chunk_id"] for p in out["friction_points"]], ["c2", "c1"])
        self.assertEqual([p["agreement"] for p in out["friction_points"]], [0.0, 0.2])

    def test_one_coding_lens_is_never_convergence(self):
        out = crosslens.compare_lenses({"A": [rec("e", "x")], "B": [rec("e")]},
                                       friction_threshold=0.0)
        self.assertEqual(out["convergence_points"], [])


class TestVocabularyRegime(unittest.TestCase):
    def test_codebooks_for_only_some_lenses_leave_the_regime_unknown(self):
        cb = [{"code_label": "x", "definition": "d"}]
        out = crosslens.compare_lenses(
            {"A": [rec("1", "x")], "B": [rec("1", "x")], "C": [rec("1", "x")]},
            codebooks_by_lens={"A": cb, "B": cb})
        self.assertEqual(out["vocabulary"]["regime"], "unknown")


class TestPrefixRecovery(unittest.TestCase):
    LONG = "abcdefghij_klmnopqrstuvwxyz123"   # 30 characters
    SHORT = "kinship_ritual_"                  # 15 characters

    def test_ten_character_prefix_recovers_a_long_code(self):
        self.assertEqual(coding.match_code_to_list(self.LONG[:10], [self.LONG]), self.LONG)

    def test_short_prefix_under_sixty_percent_is_refused(self):
        self.assertIsNone(coding.match_code_to_list(self.LONG[:9], [self.LONG]))

    def test_sixty_percent_boundary(self):
        self.assertEqual(coding.match_code_to_list(self.SHORT[:9], [self.SHORT]), self.SHORT)
        self.assertIsNone(coding.match_code_to_list(self.SHORT[:8], [self.SHORT]))


if __name__ == "__main__":
    unittest.main()
