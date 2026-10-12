"""Calibration and behaviour of the lexical similarity fallback.

    python3.12 -m unittest tests.package.test_lexical_similarity -v

When sentence-transformers is not installed (the plugin does not install it),
codebook refinement compares definitions and examples with TF-IDF instead
(ai_anthro_toolkit.lexical). TF-IDF sees shared words, not meaning, so its
duplicate threshold cannot be the embedding threshold (0.85). The fixture
below is three invented field codebooks plus one built to be hard: pairs a
researcher would merge (MERGE) and pairs they would keep apart (DISTINCT),
including a broad code with a narrower one and two codes of opposite stance.

What the calibration found, and what the tests hold:

- At 0.45, seven of the eight true duplicates score at or above the line,
  and three of the fifteen distinct pairs do too.
- No threshold below 0.75 avoids a false merge, and the pair that forces it
  ("trust in institutions" against "distrust of institutions", 0.75) scores
  above most true duplicates. Word overlap cannot see that two definitions
  disagree.

So the fallback never merges on its own. It lists pairs at or above
SUGGEST_THRESHOLD (0.45) as merge suggestions for the researcher, which is
the same path auto_merge=False takes, and the result says which method ran.
"""

import json
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from ai_anthro_toolkit import codebook as cb
from ai_anthro_toolkit import lexical
from ai_anthro_toolkit.models import CodeEntry

# Fixture codebooks, {label: definition}. MERGE and DISTINCT are labelled pairs.
CODEBOOKS = {
 "market_traders": {
  "MUTUAL_AID": "Pooling money or labor among households so that members can meet shared obligations.",
  "RESOURCE_POOLING": "Households pooling money and labor to meet shared obligations of members.",
  "STATE_ABSENCE": "Perceived withdrawal or failure of government services in everyday life.",
  "GOVERNMENT_RETREAT": "Everyday experience of government services withdrawing or failing.",
  "RECIPROCAL_EXCHANGE": "Recurring exchange of goods between traders grounded in trust rather than money.",
  "CREDIT_RELATIONS": "Lending money between traders on trust, with repayment expected later.",
  "KIN_OBLIGATION": "Duties owed to relatives that shape how traders spend money and time.",
  "MARKET_REGULATION": "Rules imposed by market authorities on stall placement, fees, and trading hours.",
  "STALL_FEES": "Fees charged by market authorities for stall placement and trading space.",
  "PRICE_NEGOTIATION": "Bargaining between buyer and seller over the price of goods.",
 },
 "hospital_ward": {
  "ALGORITHMIC_OPACITY": "The decision logic of the triage system is hidden from the nurses it governs.",
  "SYSTEM_OPACITY": "Nurses cannot see the decision logic of the triage system that governs their work.",
  "EXPERTISE_DISPLACEMENT": "Clinical judgment of nurses is overridden or sidelined by the automated triage system.",
  "OVERRIDDEN_JUDGMENT": "Automated triage overriding the clinical judgment of nurses.",
  "WORKLOAD_PRESSURE": "Nurses describe too many patients and too little time on a shift.",
  "STAFF_SHORTAGE": "Too few nurses rostered on a shift for the number of patients on the ward.",
  "CARE_WORK": "Everyday practices of caring labor nurses perform for patients on the ward.",
  "EMOTIONAL_LABOR": "Managing feelings, their own and patients', as part of nursing work.",
  "MANAGERIAL_FRAMING": "Managers describing the triage system as a neutral efficiency gain.",
  "CONTESTED_FRAMING": "Frontline staff disputing how managers characterize the triage system.",
 },
 "migration": {
  "REMITTANCES": "Money sent home by migrants to support family members.",
  "SENDING_MONEY_HOME": "Migrants sending money home to support their family members.",
  "DOCUMENT_PRECARITY": "Uncertainty and fear arising from missing or expiring legal documents.",
  "LEGAL_STATUS_ANXIETY": "Anxiety about expiring or missing legal documents and residence status.",
  "LANGUAGE_BARRIER": "Difficulty communicating with officials or employers in the host language.",
  "EMPLOYER_EXPLOITATION": "Employers withholding wages or demanding unpaid hours from migrant workers.",
  "WAGE_THEFT": "Wages withheld from migrant workers by employers.",
  "HOMELAND_NOSTALGIA": "Longing for the places, food, and people of home.",
  "COMMUNITY_ASSOCIATIONS": "Migrant-run associations that organize mutual support and events.",
  "RETURN_PLANS": "Intentions and plans to return home permanently in the future.",
 },
}
MERGE = [
 ("market_traders","MUTUAL_AID","RESOURCE_POOLING"),
 ("market_traders","STATE_ABSENCE","GOVERNMENT_RETREAT"),
 ("market_traders","MARKET_REGULATION","STALL_FEES"),
 ("hospital_ward","ALGORITHMIC_OPACITY","SYSTEM_OPACITY"),
 ("hospital_ward","EXPERTISE_DISPLACEMENT","OVERRIDDEN_JUDGMENT"),
 ("migration","REMITTANCES","SENDING_MONEY_HOME"),
 ("migration","DOCUMENT_PRECARITY","LEGAL_STATUS_ANXIETY"),
 ("migration","EMPLOYER_EXPLOITATION","WAGE_THEFT"),
]
# Same domain, overlapping words, different concepts.
DISTINCT = [
 ("market_traders","RECIPROCAL_EXCHANGE","CREDIT_RELATIONS"),
 ("market_traders","KIN_OBLIGATION","MUTUAL_AID"),
 ("market_traders","PRICE_NEGOTIATION","RECIPROCAL_EXCHANGE"),
 ("market_traders","STALL_FEES","PRICE_NEGOTIATION"),
 ("hospital_ward","WORKLOAD_PRESSURE","STAFF_SHORTAGE"),
 ("hospital_ward","CARE_WORK","EMOTIONAL_LABOR"),
 ("hospital_ward","MANAGERIAL_FRAMING","CONTESTED_FRAMING"),
 ("hospital_ward","ALGORITHMIC_OPACITY","EXPERTISE_DISPLACEMENT"),
 ("migration","REMITTANCES","COMMUNITY_ASSOCIATIONS"),
 ("migration","HOMELAND_NOSTALGIA","RETURN_PLANS"),
 ("migration","LANGUAGE_BARRIER","EMPLOYER_EXPLOITATION"),
]
CODEBOOKS["civic_trust"] = {
 "INSTITUTIONAL_TRUST": "Expressions of trust in public institutions such as courts and councils.",
 "INSTITUTIONAL_DISTRUST": "Expressions of distrust of public institutions such as courts and councils.",
 "TRUST_IN_INSTITUTIONS": "Statements expressing trust in courts, councils, and other public institutions.",
 "VOLUNTEERING": "Unpaid work residents do for neighborhood organizations.",
 "NEIGHBORHOOD_ORGANIZING": "Residents organizing neighborhood campaigns and meetings.",
 "LOCAL_ELECTIONS": "Talk about voting and candidates in council elections.",
 "PROTEST": "Taking part in demonstrations against council decisions.",
 "RUMOR": "Unverified stories about council decisions circulating among residents.",
}
MERGE.append(("civic_trust","INSTITUTIONAL_TRUST","TRUST_IN_INSTITUTIONS"))
MERGE.remove(("market_traders","MARKET_REGULATION","STALL_FEES"))
DISTINCT += [
 ("market_traders","MARKET_REGULATION","STALL_FEES"),   # broader code and a narrower one
 ("civic_trust","INSTITUTIONAL_TRUST","INSTITUTIONAL_DISTRUST"),  # opposite stances
 ("civic_trust","VOLUNTEERING","NEIGHBORHOOD_ORGANIZING"),
 ("civic_trust","PROTEST","RUMOR"),
]


def pair_score(book, a, b):
    """Cosine of two definitions, IDF taken over the whole codebook as in use."""
    labels = list(CODEBOOKS[book])
    vectors = lexical.tfidf_embed([CODEBOOKS[book][label] for label in labels])
    return float(vectors[labels.index(a)] @ vectors[labels.index(b)])


def no_sentence_transformers():
    return mock.patch.dict(sys.modules, {"sentence_transformers": None})


class TestCalibration(unittest.TestCase):
    def setUp(self):
        self.merge = [pair_score(*p) for p in MERGE]
        self.distinct = [pair_score(*p) for p in DISTINCT]

    def test_the_suggestion_threshold_catches_most_true_duplicates(self):
        caught = sum(s >= lexical.SUGGEST_THRESHOLD for s in self.merge)
        self.assertGreaterEqual(caught, 7, sorted(self.merge))

    def test_the_suggestion_threshold_keeps_most_distinct_pairs_out(self):
        flagged = sum(s >= lexical.SUGGEST_THRESHOLD for s in self.distinct)
        self.assertLessEqual(flagged, 3, sorted(self.distinct))

    def test_no_useful_threshold_is_safe_to_merge_on(self):
        """The finding that makes the fallback suggest rather than merge: the
        worst distinct pair outscores the median true duplicate."""
        worst_distinct = max(self.distinct)
        median_merge = sorted(self.merge)[len(self.merge) // 2]
        self.assertGreater(worst_distinct, median_merge)
        self.assertGreater(pair_score("civic_trust", "INSTITUTIONAL_TRUST",
                                      "INSTITUTIONAL_DISTRUST"), 0.7)

    def test_the_embedding_threshold_would_miss_almost_everything(self):
        self.assertLessEqual(sum(s >= 0.85 for s in self.merge), 1)


class TestLexicalEmbedding(unittest.TestCase):
    def test_identical_and_unrelated_texts(self):
        v = lexical.tfidf_embed(["Pooling money among households.",
                                 "Pooling money among households.",
                                 "Rumors about the council."])
        self.assertAlmostEqual(float(v[0] @ v[1]), 1.0)
        self.assertAlmostEqual(float(v[0] @ v[2]), 0.0)

    def test_inflections_and_stopwords_do_not_split_terms(self):
        self.assertEqual(lexical.tokens("The households were pooling"),
                         lexical.tokens("household pooled")[:1] + ["pool"])

    def test_empty_text_is_a_zero_vector(self):
        v = lexical.tfidf_embed(["", "the of and"])
        self.assertEqual(float(abs(v).sum()), 0.0)
        self.assertEqual(cb._cosine_similarity(v[0], v[1]), 0.0)

    def test_vectors_from_separate_calls_are_comparable(self):
        a = lexical.tfidf_embed(["rotating savings groups"])
        b = lexical.tfidf_embed(["savings groups that rotate", "court rulings"])
        self.assertEqual(a.shape[1], b.shape[1])
        self.assertGreater(cb._cosine_similarity(a[0], b[0]),
                           cb._cosine_similarity(a[0], b[1]))


def entries(book, frequency=2):
    return {label: CodeEntry(label=label, definition=definition, frequency=frequency,
                             examples=[{"text": f"example for {label}", "source": "d"}])
            for label, definition in CODEBOOKS[book].items()}


class TestRefinementFallback(unittest.TestCase):
    def test_without_sentence_transformers_duplicates_are_suggested_not_merged(self):
        messages = []
        with no_sentence_transformers():
            refined, report = cb.refine_codebook(entries("market_traders"), "critical",
                                                 llm=None, min_frequency=1,
                                                 progress=messages.append)
        self.assertEqual(set(refined), set(CODEBOOKS["market_traders"]))
        self.assertEqual(report["similarity_method"], "lexical-fallback")
        self.assertEqual(report["similarity_threshold"], lexical.SUGGEST_THRESHOLD)
        pairs = {frozenset((s["code_a"], s["code_b"])) for s in report["merge_suggestions"]}
        self.assertIn(frozenset(("MUTUAL_AID", "RESOURCE_POOLING")), pairs)
        self.assertTrue(any("lexical" in m for m in messages))

    def test_example_diversity_runs_on_the_fallback(self):
        examples = [{"text": t, "source": "d"} for t in (
            "we pool money every month", "we pool money every single month",
            "the clinic closed last spring", "vegetables traded for fish weekly")]
        book = {"MUTUAL_AID": CodeEntry(label="MUTUAL_AID", definition="Pooling money.",
                                        frequency=3, examples=examples)}
        with no_sentence_transformers():
            refined, _ = cb.refine_codebook(book, "critical", llm=None, min_frequency=1,
                                            max_examples=3)
        kept = [e["text"] for e in refined["MUTUAL_AID"].examples]
        self.assertNotIn("we pool money every single month", kept)
        self.assertEqual(len(kept), 3)

    def test_sentence_transformers_stays_the_default_when_installed(self):
        calls = []

        def fake_embedder(texts):
            calls.append(list(texts))
            return lexical.tfidf_embed(texts)

        fake_module = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"sentence_transformers": fake_module}),                 mock.patch.object(cb, "_default_embedder", fake_embedder):
            _, report = cb.refine_codebook(entries("hospital_ward"), "critical",
                                           llm=None, min_frequency=1)
        self.assertEqual(report["similarity_method"], "sentence-transformers")
        self.assertEqual(report["similarity_threshold"], 0.85)
        self.assertTrue(calls)

    def test_a_caller_supplied_embedder_is_reported_as_such(self):
        _, report = cb.refine_codebook(entries("migration"), "critical", llm=None,
                                       min_frequency=1, embedder=lexical.tfidf_embed)
        self.assertEqual(report["similarity_method"], "caller-supplied")


class TestServerReportsTheMethod(unittest.TestCase):
    def test_delegated_codebook_job_says_it_used_the_fallback(self):
        from ai_anthro_toolkit.jobs import JobStore
        from ai_anthro_toolkit.mcp import server

        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        with mock.patch.object(server, "_jobs", JobStore(tmp)), no_sentence_transformers():
            start = server.start_codebook_job(
                {"notes.txt": "Members pool money. The clinic closed."},
                "interpretive", llm_mode="delegated", min_frequency=1)
            batch = server.get_next_batch(start["job_id"], batch_size=10)
            two = json.dumps([
                {"label": "pooling", "definition": "Households pooling money to meet needs."},
                {"label": "resource pooling",
                 "definition": "Pooling money among households to meet needs."}])
            server.submit_batch(start["job_id"], [
                {"id": p["id"], "response": two} for p in batch["packets"]])
            result = server.get_job_result(start["job_id"])
            sidecar = json.loads(server._jobs.load_artifact(
                start["job_id"], server._checks.PROVENANCE_SIDECAR))
        self.assertTrue(result["ready"])
        self.assertEqual(result["similarity_method"], "lexical-fallback")
        self.assertEqual(result["quality_report"]["similarity_method"], "lexical-fallback")
        self.assertEqual(sidecar["similarity_method"], "lexical-fallback")
        self.assertEqual(len(result["records"]), 2)  # suggested, not merged
        self.assertTrue(result["quality_report"]["merge_suggestions"])


if __name__ == "__main__":
    unittest.main()
