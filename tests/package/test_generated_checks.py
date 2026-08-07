"""Turning the researcher's Stage 4 answers into standing checks.

    python3.12 -m unittest tests.package.test_generated_checks -v

Stage 4 already asks the researcher to settle five commitments about what
their instrument should do. Those answers go into the specification and then
nothing enforces them. This turns each answered commitment into a check that
runs whenever they point the checker at their data.

Two things this must not do, and both are tested.

**It must not invent a commitment the researcher did not state.** An answer
absent from the spec generates nothing. Silence is not consent to a default.

**It must not generate a check for an answer that cannot be checked.** Some
answers describe what the instrument should do rather than a property its
output must have, and ordering is the clear case: whether source order was
preserved cannot be read off a single artifact. Those are reported as
declared-but-unenforceable rather than quietly skipped, because a researcher
who answered five and got three checks should be told which two and why.
"""

import json
import unittest

from ai_anthro_toolkit.checks import generated
from ai_anthro_toolkit.checks import registry


RECORDS = [
    {"case_id": "1904-A", "decided": "1904-03-11"},
    {"case_id": "1904-B", "decided": "1904-05-02"},
]


class TheAnswerVocabulary(unittest.TestCase):
    """Answers come from a fixed vocabulary so the generator never has to
    interpret prose. Free text would put the machine back in the business of
    deciding what the researcher meant."""

    def test_every_commitment_has_answers(self):
        self.assertEqual(
            set(generated.ANSWERS),
            {"emptiness", "duplication", "partial-presence", "unparseable",
             "ordering"},
        )

    def test_each_commitment_offers_at_least_two_answers(self):
        for name, answers in generated.ANSWERS.items():
            with self.subTest(commitment=name):
                self.assertGreaterEqual(len(answers), 2)

    def test_every_answer_says_whether_it_can_be_checked(self):
        for name, answers in generated.ANSWERS.items():
            for answer, spec in answers.items():
                with self.subTest(commitment=name, answer=answer):
                    self.assertIn("checkable", spec)
                    self.assertTrue(spec["means"].strip())

    def test_ordering_is_declared_unenforceable(self):
        # Whether source order was preserved cannot be read off one artifact.
        for spec in generated.ANSWERS["ordering"].values():
            self.assertFalse(spec["checkable"])


class GeneratingFromAnswers(unittest.TestCase):
    def test_an_answer_that_can_be_checked_produces_a_check(self):
        out = generated.from_answers({"emptiness": "failure"}, artifact="cases")
        self.assertEqual(len(out.checks), 1)
        self.assertEqual(out.checks[0].artifact_class, "cases")

    def test_an_answer_that_cannot_be_checked_is_reported_not_dropped(self):
        out = generated.from_answers({"ordering": "meaningful"},
                                     artifact="cases")
        self.assertEqual(out.checks, [])
        self.assertEqual([u.commitment for u in out.unenforceable], ["ordering"])
        self.assertTrue(out.unenforceable[0].why.strip())

    def test_an_unanswered_commitment_generates_nothing(self):
        # Silence is not consent to a default.
        out = generated.from_answers({}, artifact="cases")
        self.assertEqual(out.checks, [])
        self.assertEqual(out.unenforceable, [])

    def test_an_answer_outside_the_vocabulary_is_refused(self):
        with self.assertRaises(ValueError):
            generated.from_answers({"emptiness": "whatever"}, artifact="cases")

    def test_a_field_answer_carries_its_field(self):
        out = generated.from_answers(
            {"partial-presence": "required"}, artifact="cases",
            fields={"partial-presence": "decided"})
        self.assertIn("decided", out.checks[0].summary)

    def test_a_field_answer_without_a_field_is_refused(self):
        with self.assertRaises(ValueError):
            generated.from_answers({"partial-presence": "required"},
                                   artifact="cases")

    def test_every_generated_check_carries_a_mutator(self):
        out = generated.from_answers(
            {"emptiness": "failure", "duplication": "error"},
            artifact="cases", fields={"duplication": "case_id"})
        for check in out.checks:
            with self.subTest(check=check.name):
                self.assertTrue(callable(check.break_artifact))

    def test_generated_checks_are_surprise_capable_with_a_hypothesis(self):
        out = generated.from_answers({"emptiness": "failure"}, artifact="cases")
        check = out.checks[0]
        self.assertEqual(check.mark, registry.MARK_SURPRISE)
        self.assertTrue(check.hypothesis.strip())


class TheChecksActuallyFire(unittest.TestCase):
    """A generated check that cannot fire is worse than none: it reports
    green over an instrument nobody verified."""

    def fire(self, answers, artifact_data, **kw):
        out = generated.from_answers(answers, artifact="cases", **kw)
        check = out.checks[0]
        good = check.run(artifact_data)
        broken = check.run(check.break_artifact(artifact_data))
        return good.verdict, broken.verdict

    def test_emptiness_as_failure(self):
        good, broken = self.fire({"emptiness": "failure"}, RECORDS)
        self.assertEqual(good, registry.OK)
        self.assertEqual(broken, registry.FIRED)

    def test_duplication_as_error(self):
        good, broken = self.fire({"duplication": "error"}, RECORDS,
                                 fields={"duplication": "case_id"})
        self.assertEqual(good, registry.OK)
        self.assertEqual(broken, registry.FIRED)

    def test_partial_presence_as_required(self):
        good, broken = self.fire({"partial-presence": "required"}, RECORDS,
                                 fields={"partial-presence": "decided"})
        self.assertEqual(good, registry.OK)
        self.assertEqual(broken, registry.FIRED)

    def test_unparseable_as_stop(self):
        good, broken = self.fire({"unparseable": "stop"}, RECORDS,
                                 fields={"unparseable": "decided"})
        self.assertEqual(good, registry.OK)
        self.assertEqual(broken, registry.FIRED)

    def test_a_fired_check_names_the_commitment_the_researcher_answered(self):
        out = generated.from_answers({"emptiness": "failure"}, artifact="cases")
        check = out.checks[0]
        result = check.run(check.break_artifact(RECORDS))
        self.assertIn("empty", result.message.lower())


class PersistingAndLoading(unittest.TestCase):
    """Generated checks live beside the researcher's project as data, never
    as code. Nothing here imports anything from a project directory."""

    def payload(self):
        return generated.to_document(
            {"emptiness": "failure", "partial-presence": "required",
             "ordering": "meaningful"},
            artifact="cases", fields={"partial-presence": "decided"},
            instrument="case-file collector")

    def test_the_document_round_trips(self):
        doc = json.loads(json.dumps(self.payload()))
        out = generated.from_document(doc)
        self.assertEqual(len(out.checks), 2)
        self.assertEqual([u.commitment for u in out.unenforceable], ["ordering"])

    def test_the_document_records_what_it_could_not_enforce(self):
        self.assertIn("ordering", json.dumps(self.payload()))

    def test_the_document_names_the_instrument_and_artifact(self):
        doc = self.payload()
        self.assertEqual(doc["artifact"], "cases")
        self.assertEqual(doc["instrument"], "case-file collector")

    def test_loading_never_executes_project_code(self):
        # The names below are asserted ABSENT from the module. A checks file
        # sits in a researcher's project directory, and a loader that could
        # execute what it finds there would turn "run the checks" into "run
        # whatever is in that folder".
        source = generated.__file__
        with open(source, encoding="utf-8") as handle:
            text = handle.read()
        for forbidden in ("exec(", "eval(", "importlib", "__import__"):
            self.assertNotIn(forbidden, text)

    def test_a_document_with_an_unknown_answer_is_refused(self):
        doc = self.payload()
        doc["answers"]["emptiness"] = "whatever"
        with self.assertRaises(ValueError):
            generated.from_document(doc)


if __name__ == "__main__":
    unittest.main()
