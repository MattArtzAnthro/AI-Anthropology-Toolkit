"""Tests for the commitment mutations (ai_anthro_toolkit.checks.mutate).

    python3.12 -m unittest tests.package.test_mutations -v

Stage 4 of tool-building asks the researcher to settle five recurring
commitments: what an empty result means, whether a duplicate identifier is an
error or a fact about the source, whether a partly present field is required,
what an unparseable value does, and whether source order carries meaning.

These mutations are the executable form of those five. Each one produces the
input that would violate a commitment, so an instrument can be shown to
behave the way its researcher said it should — not merely asserted to.

Written from the specification before the implementation existed, and seen to
fail.
"""

import json
import unittest

from ai_anthro_toolkit.checks import mutate


RECORDS = [
    {"case_id": "1904-A", "decided": "1904-03-11", "judge": "Okonkwo"},
    {"case_id": "1904-B", "decided": "1904-05-02", "judge": "Bello"},
    {"case_id": "1905-A", "decided": "1905-01-19", "judge": "Okonkwo"},
]


class TheFiveCommitments(unittest.TestCase):
    """One mutation per commitment the Stage 4 table settles."""

    def test_every_commitment_has_a_mutation(self):
        # The table and the harness must not drift apart: a commitment with
        # no mutation cannot be verified, and a mutation with no commitment
        # is testing something nobody agreed to.
        self.assertEqual(
            set(mutate.COMMITMENTS),
            {"emptiness", "duplication", "partial-presence",
             "unparseable", "ordering"},
        )

    def test_each_commitment_names_the_question_it_settles(self):
        for name, entry in mutate.COMMITMENTS.items():
            with self.subTest(commitment=name):
                self.assertTrue(entry.question.strip())
                self.assertTrue(callable(entry.mutation))

    def test_emptiness_produces_no_records(self):
        self.assertEqual(mutate.empty(RECORDS), [])

    def test_duplication_repeats_a_record_without_changing_the_others(self):
        out = mutate.duplicate_record(RECORDS)
        self.assertEqual(len(out), len(RECORDS) + 1)
        self.assertEqual(out[0], out[1])
        self.assertEqual(out[2:], RECORDS[1:])

    def test_partial_presence_drops_one_field_from_one_record(self):
        out = mutate.drop_field(RECORDS, "decided")
        self.assertNotIn("decided", out[0])
        self.assertIn("decided", out[1], "only the first record should lose it")

    def test_unparseable_corrupts_a_value_without_removing_the_key(self):
        out = mutate.corrupt_value(RECORDS, "decided")
        self.assertIn("decided", out[0])
        self.assertNotEqual(out[0]["decided"], RECORDS[0]["decided"])

    def test_ordering_reverses_without_changing_membership(self):
        out = mutate.reorder(RECORDS)
        self.assertNotEqual(out, RECORDS)
        self.assertEqual(sorted(map(json.dumps, out)),
                         sorted(map(json.dumps, RECORDS)))


class EveryCommitmentIsWiredToItsOwnMutation(unittest.TestCase):
    """Testing the mutations as bare functions leaves the registry untested:
    a commitment wired to the wrong function would still pass. So each one is
    exercised through the harness, against a check written to detect exactly
    that violation and nothing else."""

    GUARDS = {
        "emptiness":
            lambda rs: len(rs) > 0,
        "duplication":
            lambda rs: len({r["case_id"] for r in rs}) == len(rs),
        "partial-presence":
            lambda rs: all("decided" in r for r in rs),
        "unparseable":
            lambda rs: all(str(r.get("decided", "")).startswith("19")
                           for r in rs),
        "ordering":
            lambda rs: ([r["case_id"] for r in rs]
                        == sorted(r["case_id"] for r in rs)),
    }

    def test_each_commitment_violates_exactly_what_it_names(self):
        for name, guard in self.GUARDS.items():
            with self.subTest(commitment=name):
                result = mutate.confirm_fires(
                    guard, RECORDS, name, field="decided")
                self.assertTrue(
                    result.quiet_on_good,
                    f"{name}: the guard objects to the good records",
                )
                self.assertTrue(
                    result.fired_on_mutation,
                    f"{name}: the mutation did not produce the violation it "
                    f"names, so this commitment is wired to the wrong thing",
                )

    def test_confirm_all_covers_every_commitment_once(self):
        results = mutate.confirm_all(
            self.GUARDS["partial-presence"], RECORDS, field="decided")
        self.assertEqual([r.commitment for r in results],
                         list(mutate.COMMITMENTS))

    def test_a_narrow_check_guards_one_commitment_and_not_the_rest(self):
        # This is the ordinary case and must not read as a failure: most
        # checks cover one question and are correctly silent on the others.
        results = mutate.confirm_all(
            self.GUARDS["partial-presence"], RECORDS, field="decided")
        guarded = [r.commitment for r in results if r.guards]
        self.assertIn("partial-presence", guarded)
        self.assertLess(len(guarded), len(mutate.COMMITMENTS))


class MutationsNeverTouchTheOriginal(unittest.TestCase):
    """A mutation that edits the researcher's data in place has corrupted the
    thing it was meant to test."""

    def test_no_mutation_modifies_its_input(self):
        for name, entry in mutate.COMMITMENTS.items():
            with self.subTest(commitment=name):
                before = json.dumps(RECORDS, sort_keys=True)
                entry.mutation(RECORDS)
                self.assertEqual(json.dumps(RECORDS, sort_keys=True), before)

    def test_a_mutation_on_empty_input_does_not_raise(self):
        # An instrument handed nothing is exactly the case the emptiness
        # commitment is about; the harness must survive reaching it.
        for name, entry in mutate.COMMITMENTS.items():
            with self.subTest(commitment=name):
                entry.mutation([])


class ConfirmFires(unittest.TestCase):
    """The harness itself: run a check against a mutation and report whether
    it noticed. Stage 7 already requires that guarded things be broken on
    purpose; this makes that requirement executable."""

    @staticmethod
    def notices_missing_dates(records):
        return all(r.get("decided") for r in records)

    @staticmethod
    def notices_nothing(records):
        return True

    def test_reports_a_check_that_notices(self):
        result = mutate.confirm_fires(
            self.notices_missing_dates, RECORDS, "partial-presence",
            field="decided")
        self.assertTrue(result.quiet_on_good)
        self.assertTrue(result.fired_on_mutation)
        self.assertTrue(result.guards)

    def test_reports_a_check_that_guards_nothing(self):
        result = mutate.confirm_fires(
            self.notices_nothing, RECORDS, "partial-presence",
            field="decided")
        self.assertTrue(result.quiet_on_good)
        self.assertFalse(result.fired_on_mutation)
        self.assertFalse(result.guards)

    def test_a_check_that_fires_on_everything_guards_nothing_either(self):
        result = mutate.confirm_fires(
            lambda records: False, RECORDS, "emptiness")
        self.assertFalse(result.quiet_on_good)
        self.assertFalse(result.guards)

    def test_result_says_which_commitment_was_tested(self):
        result = mutate.confirm_fires(
            self.notices_missing_dates, RECORDS, "partial-presence",
            field="decided")
        self.assertEqual(result.commitment, "partial-presence")
        self.assertIn("?", result.question)

    def test_unknown_commitment_is_refused_rather_than_guessed(self):
        with self.assertRaises(KeyError):
            mutate.confirm_fires(self.notices_nothing, RECORDS, "vibes")

    def test_a_check_that_raises_counts_as_firing(self):
        # An instrument that crashes on a duplicate has noticed it, however
        # rudely. That is a behaviour worth distinguishing from silence.
        def strict(records):
            ids = [r["case_id"] for r in records]
            if len(set(ids)) != len(ids):
                raise ValueError("duplicate case_id")
            return True

        result = mutate.confirm_fires(strict, RECORDS, "duplication")
        self.assertTrue(result.fired_on_mutation)
        self.assertTrue(result.guards)
        self.assertIn("ValueError", result.detail)

    def test_no_mutation_makes_a_network_call(self):
        # Mutating a live collector and re-running it is an unsandboxed
        # adversarial run against someone else's endpoint, and it can get a
        # researcher blocked from the archive they are studying.
        import ai_anthro_toolkit.checks.mutate as m
        source = __import__("inspect").getsource(m)
        for forbidden in ("requests", "urllib", "http", "socket"):
            self.assertNotIn(
                f"import {forbidden}", source,
                "the mutation harness must never reach the network",
            )


if __name__ == "__main__":
    unittest.main()
