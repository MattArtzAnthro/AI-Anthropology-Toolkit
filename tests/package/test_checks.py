"""Tests for the standing checks registry (ai_anthro_toolkit.checks).

    python3.12 -m unittest tests.package.test_checks -v

Written from the ratified specification before the implementation existed,
and seen to fail. The registry-completeness and mutation tests below are the
structural half of that discipline: a check registered without a mutator is
a test failure, so the guarantee does not depend on anyone remembering.
"""

import json
import unittest

from ai_anthro_toolkit import checks


# ── Canonical-good artifacts ────────────────────────────────────────────────
#
# One per class. Every red case in this file is produced by applying a
# registry-declared mutator to one of these, never by hand-authoring a second
# broken fixture that can drift away from the check it exercises.

GOOD_CODEBOOK = [
    {
        "code_label": "algorithmic_opacity",
        "definition": "The system's decision logic is hidden from the workers it governs.",
        "extraction_type": "emergent",
        "code_group": "Technology and Power",
        "stance": "Critical",
        "stance_key": "critical",
        "inclusion_criteria": "Use when opacity of automated decisions is at issue",
        "exclusion_criteria": "Not for general distrust of technology",
        "example_1": "described the new triage system as opaque",
        "example_2": "",
        "example_3": "",
        "frequency": 4,
        "source_documents": "interview_1.txt",
    },
    {
        "code_label": "expertise_displacement",
        "definition": "Clinical judgment is overridden or sidelined by an automated process.",
        "extraction_type": "emergent",
        "code_group": "Technology and Power",
        "stance": "Critical",
        "stance_key": "critical",
        "inclusion_criteria": "Use when professional judgment is displaced",
        "exclusion_criteria": "Not for ordinary workload complaints",
        "example_1": "their expertise was being displaced by the tool",
        "example_2": "",
        "example_3": "",
        "frequency": 3,
        "source_documents": "interview_1.txt",
    },
]

GOOD_CODED_DATA = [
    {
        "chunk_id": 0,
        "text": "The nurses described the new triage system as opaque.",
        "Deductive_Codes": "algorithmic_opacity",
        "Inductive_Codes": "",
        "All_Codes": "algorithmic_opacity",
        "Coding_Status": "Deductive_Only",
    },
    {
        "chunk_id": 1,
        "text": "They said the algorithm overrode their clinical judgment.",
        "Deductive_Codes": "expertise_displacement",
        "Inductive_Codes": "",
        "All_Codes": "expertise_displacement",
        "Coding_Status": "Deductive_Only",
    },
]


def codebook_labels():
    return [row["code_label"] for row in GOOD_CODEBOOK]


def coded_with_provenance():
    """A coded dataset carrying the stanza its checks need."""
    stanza = checks.provenance_stanza(
        produced_by="test",
        codebook_labels=codebook_labels(),
    )
    return {checks.PROVENANCE_KEY: stanza, "records": list(GOOD_CODED_DATA)}


class RegistryStructure(unittest.TestCase):
    """The registry is the thing that makes the guarantee structural."""

    def test_registry_is_not_empty(self):
        self.assertTrue(checks.REGISTRY)

    def test_every_check_declares_a_mutator(self):
        # A check with no mutator cannot be shown to fire, so it is evidence
        # about nothing. Registering one without a mutator fails here rather
        # than passing quietly.
        for check in checks.REGISTRY:
            with self.subTest(check=check.name):
                self.assertTrue(
                    callable(getattr(check, "break_artifact", None)),
                    f"{check.name} declares no mutator",
                )

    def test_every_check_carries_a_known_mark(self):
        known = {checks.MARK_MIRROR, checks.MARK_SURPRISE, checks.MARK_STANCE}
        for check in checks.REGISTRY:
            with self.subTest(check=check.name):
                self.assertIn(check.mark, known)

    def test_every_surprise_capable_check_states_its_hypothesis(self):
        # The stated hypothesis about which unstated commitment a firing
        # would reveal is the whole product of a surprise-capable check.
        for check in checks.REGISTRY:
            if check.mark == checks.MARK_MIRROR:
                continue
            with self.subTest(check=check.name):
                self.assertTrue(
                    check.hypothesis.strip(),
                    f"{check.name} is not a mirror check but states no hypothesis",
                )

    def test_every_check_names_an_artifact_class(self):
        known = {checks.CLASS_CODEBOOK, checks.CLASS_CODED}
        for check in checks.REGISTRY:
            with self.subTest(check=check.name):
                self.assertIn(check.artifact_class, known)


class MutationRound(unittest.TestCase):
    """The generic red/green pass over every registered check."""

    def artifact_for(self, check):
        if check.artifact_class == checks.CLASS_CODEBOOK:
            return json.loads(json.dumps(GOOD_CODEBOOK))
        return json.loads(json.dumps(coded_with_provenance()))

    def context_for(self, check):
        return {"expect_distinct_codes": True, "embedder": _StubEmbedder()}

    def test_no_check_fires_on_the_canonical_good_artifact(self):
        for check in checks.REGISTRY:
            with self.subTest(check=check.name):
                result = check.run(self.artifact_for(check), **self.context_for(check))
                self.assertNotEqual(
                    result.verdict, checks.FIRED,
                    f"{check.name} fired on a good artifact: {result.message}",
                )

    def test_every_check_fires_on_its_own_mutation(self):
        for check in checks.REGISTRY:
            with self.subTest(check=check.name):
                broken = check.break_artifact(self.artifact_for(check))
                result = check.run(broken, **self.context_for(check))
                self.assertEqual(
                    result.verdict, checks.FIRED,
                    f"{check.name} stayed quiet over its own mutation",
                )

    def test_a_fired_check_always_carries_a_message(self):
        for check in checks.REGISTRY:
            with self.subTest(check=check.name):
                broken = check.break_artifact(self.artifact_for(check))
                result = check.run(broken, **self.context_for(check))
                self.assertTrue(result.message.strip())


class SurpriseCapableMessages(unittest.TestCase):
    """Mutation shows a check fires. It does not show it fires for the right
    reason, and for these checks the message is the entire product."""

    def fired_message(self, name):
        check = checks.by_name(name)
        artifact = (json.loads(json.dumps(GOOD_CODEBOOK))
                    if check.artifact_class == checks.CLASS_CODEBOOK
                    else json.loads(json.dumps(coded_with_provenance())))
        result = check.run(check.break_artifact(artifact),
                           expect_distinct_codes=True, embedder=_StubEmbedder())
        return result.message

    def test_surprise_capable_messages_ask_rather_than_assert(self):
        for check in checks.REGISTRY:
            if check.mark == checks.MARK_MIRROR:
                continue
            with self.subTest(check=check.name):
                message = self.fired_message(check.name)
                self.assertIn(
                    "?", message,
                    f"{check.name} asserts a commitment instead of asking whether "
                    f"it is the researcher's",
                )

    def test_no_message_claims_an_all_clear(self):
        # No check may report a clean bill on a question it cannot settle.
        forbidden = ("clean", "verified", "guaranteed", "no issues", "all clear")
        for check in checks.REGISTRY:
            with self.subTest(check=check.name):
                artifact = (json.loads(json.dumps(GOOD_CODEBOOK))
                            if check.artifact_class == checks.CLASS_CODEBOOK
                            else json.loads(json.dumps(coded_with_provenance())))
                result = check.run(artifact, expect_distinct_codes=True,
                                   embedder=_StubEmbedder())
                lowered = result.message.lower()
                for word in forbidden:
                    self.assertNotIn(word, lowered)


class InductiveCodesAreNotMissingCodes(unittest.TestCase):
    """coding.py composes All_Codes as deductive + [c + '_IND' for c in
    inductive]. A resolve check that does not know this reports failure on
    every hybrid and inductive run, which is most of them."""

    def hybrid_dataset(self):
        payload = json.loads(json.dumps(coded_with_provenance()))
        payload["records"].append({
            "chunk_id": 2,
            "text": "Managers framed the algorithm as a neutral efficiency gain.",
            "Deductive_Codes": "algorithmic_opacity",
            "Inductive_Codes": "managerial_framing",
            "All_Codes": "algorithmic_opacity, managerial_framing_IND",
            "Coding_Status": "Both_Deductive_Inductive",
        })
        return payload

    def test_resolve_check_does_not_fire_on_a_hybrid_run(self):
        result = checks.by_name("coded.codes-resolve").run(
            self.hybrid_dataset(), expect_distinct_codes=True)
        self.assertNotEqual(result.verdict, checks.FIRED, result.message)

    def test_unfolded_inductive_codes_are_surfaced_separately(self):
        result = checks.by_name("coded.inductive-unfolded").run(
            self.hybrid_dataset(), expect_distinct_codes=True)
        self.assertEqual(result.verdict, checks.FIRED)
        self.assertIn("managerial_framing", result.message)


class StanceGating(unittest.TestCase):
    """A class-level invariant may assert formal properties of an artifact and
    may never assert a methodological commitment about its use."""

    def test_distinctness_does_not_run_when_no_commitment_established(self):
        result = checks.by_name("codebook.distinctness").run(
            json.loads(json.dumps(GOOD_CODEBOOK)),
            expect_distinct_codes=None, embedder=_StubEmbedder())
        self.assertEqual(result.verdict, checks.CANNOT_TELL)

    def test_distinctness_stays_quiet_when_the_researcher_holds_overlap(self):
        # Grounded theory and several interpretive traditions hold
        # overlapping codes deliberately. That is not a finding.
        near_duplicates = json.loads(json.dumps(GOOD_CODEBOOK))
        near_duplicates[1]["definition"] = GOOD_CODEBOOK[0]["definition"]
        result = checks.by_name("codebook.distinctness").run(
            near_duplicates, expect_distinct_codes=False, embedder=_StubEmbedder())
        self.assertNotEqual(result.verdict, checks.FIRED)

    def test_distinctness_cannot_tell_without_an_embedder(self):
        # sentence-transformers lives behind the optional chunking extra and
        # CI does not install it. Absent it the check says so; it never
        # passes silently.
        result = checks.by_name("codebook.distinctness").run(
            json.loads(json.dumps(GOOD_CODEBOOK)),
            expect_distinct_codes=True, embedder=None)
        self.assertEqual(result.verdict, checks.CANNOT_TELL)
        self.assertIn("cannot", result.message.lower())


class ProvenanceStanza(unittest.TestCase):
    """Detection stops being format sniffing and becomes reading a field."""

    def test_stanza_round_trips(self):
        stanza = checks.provenance_stanza(
            produced_by="test", codebook_labels=codebook_labels())
        self.assertEqual(stanza["codebook_labels"], codebook_labels())
        self.assertTrue(stanza["codebook_checksum"])
        self.assertEqual(stanza["produced_by"], "test")

    def test_checksum_is_order_independent(self):
        a = checks.provenance_stanza(produced_by="t", codebook_labels=["x", "y"])
        b = checks.provenance_stanza(produced_by="t", codebook_labels=["y", "x"])
        self.assertEqual(a["codebook_checksum"], b["codebook_checksum"])

    def test_absent_stanza_is_cannot_tell_and_never_a_failure(self):
        # The datasets this check exists for are exactly the ones that
        # arrived by other routes and carry no stanza. Firing on all of them
        # is how a gate becomes a form.
        bare = {"records": list(GOOD_CODED_DATA)}
        result = checks.by_name("coded.codebook-provenance").run(bare)
        self.assertEqual(result.verdict, checks.CANNOT_TELL)

    def test_checksum_mismatch_fires(self):
        payload = json.loads(json.dumps(coded_with_provenance()))
        payload[checks.PROVENANCE_KEY]["codebook_checksum"] = "0" * 16
        result = checks.by_name("coded.codebook-provenance").run(payload)
        self.assertEqual(result.verdict, checks.FIRED)


class ArtifactDetection(unittest.TestCase):
    """A misdetection produces a false all-clear, which this design forbids.
    So detection refuses rather than guesses."""

    def test_detects_a_codebook(self):
        self.assertEqual(
            checks.detect_artifact_class(GOOD_CODEBOOK), checks.CLASS_CODEBOOK)

    def test_detects_a_coded_dataset(self):
        self.assertEqual(
            checks.detect_artifact_class(coded_with_provenance()),
            checks.CLASS_CODED)

    def test_stanza_beats_sniffing(self):
        stanza = checks.provenance_stanza(
            produced_by="test", codebook_labels=codebook_labels(),
            artifact_class=checks.CLASS_CODED)
        payload = {checks.PROVENANCE_KEY: stanza, "records": []}
        self.assertEqual(
            checks.detect_artifact_class(payload), checks.CLASS_CODED)

    def test_ambiguous_payload_refuses_and_names_the_candidates(self):
        with self.assertRaises(checks.AmbiguousArtifact) as caught:
            checks.detect_artifact_class([{"chunk_id": 0, "code_label": "x"}])
        self.assertTrue(caught.exception.candidates)

    def test_unrecognised_payload_returns_none_rather_than_guessing(self):
        self.assertIsNone(checks.detect_artifact_class({"unrelated": True}))


class Reporting(unittest.TestCase):
    """A green run of mirror checks is not evidence of understanding, and the
    record must not let it read as one."""

    def test_report_marks_a_mirror_only_run(self):
        report = checks.run_checks(
            json.loads(json.dumps(GOOD_CODEBOOK)),
            artifact_class=checks.CLASS_CODEBOOK,
            expect_distinct_codes=None, embedder=None)
        self.assertTrue(report.mirror_only)

    def test_report_is_not_mirror_only_when_a_surprise_check_ran(self):
        report = checks.run_checks(
            json.loads(json.dumps(coded_with_provenance())),
            artifact_class=checks.CLASS_CODED)
        self.assertFalse(report.mirror_only)

    def test_report_separates_cannot_tell_from_ok(self):
        report = checks.run_checks(
            json.loads(json.dumps(GOOD_CODEBOOK)),
            artifact_class=checks.CLASS_CODEBOOK,
            expect_distinct_codes=None, embedder=None)
        self.assertTrue(report.undetermined)
        self.assertNotIn(checks.CANNOT_TELL, [r.verdict for r in report.passed])

    def test_checks_never_write_to_the_artifact(self):
        payload = json.loads(json.dumps(GOOD_CODEBOOK))
        before = json.dumps(payload, sort_keys=True)
        checks.run_checks(payload, artifact_class=checks.CLASS_CODEBOOK,
                          expect_distinct_codes=True, embedder=_StubEmbedder())
        self.assertEqual(json.dumps(payload, sort_keys=True), before)


class SidecarScope(unittest.TestCase):
    """A provenance sidecar describes one artifact, not every file that
    happens to sit beside it. Folding it into an unrelated artifact would
    have the checks report on one thing using another thing's provenance,
    which is the false-confidence outcome this design exists to refuse."""

    def setUp(self):
        import tempfile
        from pathlib import Path

        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "result.json").write_text(json.dumps(GOOD_CODED_DATA))
        stanza = checks.provenance_stanza(
            produced_by="test", codebook_labels=codebook_labels(),
            artifact_class=checks.CLASS_CODED, artifact_file="result.json")
        (self.dir / checks.PROVENANCE_SIDECAR).write_text(json.dumps(stanza))
        (self.dir / "unrelated.json").write_text(
            json.dumps([{"chunk_id": 0, "code_label": "x"}]))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_sidecar_attaches_to_the_artifact_it_names(self):
        from ai_anthro_toolkit.checks import cli

        loaded = cli.load_artifact(self.dir / "result.json")
        self.assertIsNotNone(checks.stanza_of(loaded))

    def test_sidecar_does_not_attach_to_an_unrelated_neighbour(self):
        from ai_anthro_toolkit.checks import cli

        loaded = cli.load_artifact(self.dir / "unrelated.json")
        self.assertIsNone(
            checks.stanza_of(loaded),
            "a neighbouring artifact borrowed provenance that was not its own")

    def test_the_unrelated_neighbour_is_still_refused_as_ambiguous(self):
        from ai_anthro_toolkit.checks import cli

        loaded = cli.load_artifact(self.dir / "unrelated.json")
        with self.assertRaises(checks.AmbiguousArtifact):
            checks.detect_artifact_class(loaded)


class _StubEmbedder:
    """Deterministic stand-in for sentence-transformers, which CI does not
    install. Encodes on token overlap so identical definitions collide and
    distinct ones do not."""

    def __call__(self, texts):
        import numpy as np
        vocab = sorted({w for t in texts for w in t.lower().split()})
        rows = []
        for text in texts:
            words = set(text.lower().split())
            rows.append([1.0 if w in words else 0.0 for w in vocab])
        return np.array(rows)


if __name__ == "__main__":
    unittest.main()
