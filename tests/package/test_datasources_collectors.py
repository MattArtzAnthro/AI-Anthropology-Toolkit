"""Live micro-tests for the ngram, podcast, and patents data sources, plus
offline coverage of the OpenAlex refusal path.

    python3.12 -m unittest tests.package.test_datasources_collectors -v
"""

import os
import unittest

# CI sets AAT_SKIP_LIVE_SCRAPERS. Classes below whose names end in "Live" call
# a third-party service, so they can fail for reasons that have nothing to do
# with this code — a slow endpoint, a brief outage, a rate-limited runner. A
# red build nobody trusts is worse than a check that runs at release time, so
# these skip in CI and still run locally. The offline classes stay in CI,
# because those are the ones that can catch a bug here.
SKIP_LIVE = unittest.skipIf(
    os.environ.get("AAT_SKIP_LIVE_SCRAPERS"),
    "AAT_SKIP_LIVE_SCRAPERS set — skipping live third-party queries",
)

from ai_anthro_toolkit.datasources import (
    get_ngram_frequencies,
    get_podcast_episodes,
    search_google_patents,
)
from ai_anthro_toolkit.datasources import openalex

NPR_FEED = "https://feeds.npr.org/510289/podcast.xml"


@SKIP_LIVE
class TestNgramLive(unittest.TestCase):
    def test_single_term(self):
        rows = get_ngram_frequencies("culture", year_from=1950, year_to=2000)
        self.assertGreaterEqual(len(rows), 40)
        for row in rows:
            self.assertEqual(row["term"], "culture")
            self.assertIn(row["year"], range(1950, 2001))
            self.assertIsInstance(row["frequency"], float)

    def test_case_insensitive_returns_more_series(self):
        sensitive = get_ngram_frequencies("culture", 1950, 2000)
        insensitive = get_ngram_frequencies("culture", 1950, 2000,
                                            case_insensitive=True)
        n_sensitive = len({r["term"] for r in sensitive})
        n_insensitive = len({r["term"] for r in insensitive})
        self.assertGreaterEqual(n_insensitive, n_sensitive)


@SKIP_LIVE
class TestPodcastLive(unittest.TestCase):
    def test_npr_feed(self):
        try:
            import feedparser  # noqa: F401
        except ImportError:
            self.skipTest("feedparser not installed")
        episodes = get_podcast_episodes(NPR_FEED, limit=20)
        self.assertGreaterEqual(len(episodes), 5)
        for ep in episodes[:5]:
            for field in ("title", "published", "duration", "audio_url",
                          "description", "link"):
                self.assertIn(field, ep)
            self.assertTrue(ep["title"])
            self.assertLessEqual(len(ep["description"]), 500)


@SKIP_LIVE
class TestPatentsLive(unittest.TestCase):
    def test_search_or_honest_block_error(self):
        """A live call must either return records or raise the block message —
        it must never return silently empty on a 503/429."""
        try:
            records = search_google_patents("machine learning ethnography",
                                            limit=10)
        except RuntimeError as e:
            msg = str(e).lower()
            self.assertTrue("block" in msg or "rate" in msg, msg)
        else:
            self.assertGreaterEqual(len(records), 1)
            for field in ("title", "patent_id", "inventors", "assignee",
                          "filing_date", "publication_date", "url"):
                self.assertIn(field, records[0])


class _FakeResponse:
    def __init__(self, status_code, text="", url=""):
        self.status_code = status_code
        self.text = text
        self.request = type("R", (), {"url": url})()


class TestOpenAlexRefusal(unittest.TestCase):
    """OpenAlex answers an exhausted request budget with the same 429 it uses
    for ordinary rate limiting, so the body is the only thing that tells them
    apart. Discarding it leaves a researcher retrying against a budget that
    will not refill until midnight UTC.
    """

    BUDGET = ('{"error":"Rate limit exceeded","message":"Insufficient budget. '
              'This request costs $0.001 but you only have $0 remaining. '
              'Resets at midnight UTC."}')

    def test_a_429_carries_the_servers_own_explanation(self):
        with self.assertRaises(RuntimeError) as caught:
            openalex._check_refused(_FakeResponse(429, self.BUDGET))
        message = str(caught.exception)
        self.assertIn("Insufficient budget", message)
        self.assertIn("midnight UTC", message)

    def test_a_429_says_retrying_may_not_help(self):
        """The distinction is the whole point: rate limiting resolves by
        waiting and an exhausted budget does not."""
        with self.assertRaises(RuntimeError) as caught:
            openalex._check_refused(_FakeResponse(429, self.BUDGET))
        self.assertIn("which it does not", str(caught.exception))

    def test_the_polite_pool_is_named_only_when_it_was_not_used(self):
        """Telling someone to pass `mailto` when they already did is noise."""
        without = _FakeResponse(429, self.BUDGET, url="https://api.openalex.org/works?search=x")
        with self.assertRaises(RuntimeError) as caught:
            openalex._check_refused(without)
        self.assertIn("polite pool", str(caught.exception))

        with_mailto = _FakeResponse(
            429, self.BUDGET,
            url="https://api.openalex.org/works?search=x&mailto=a@b.c")
        with self.assertRaises(RuntimeError) as caught:
            openalex._check_refused(with_mailto)
        self.assertNotIn("polite pool", str(caught.exception))

    def test_a_429_with_no_body_still_raises_something_readable(self):
        with self.assertRaises(RuntimeError) as caught:
            openalex._check_refused(_FakeResponse(429, ""))
        self.assertIn("no detail returned", str(caught.exception))

    def test_other_statuses_are_left_to_raise_for_status(self):
        """This guard exists to add detail a 429 carries, not to take over
        error handling for every status the API can return."""
        for status in (200, 404, 500, 503):
            with self.subTest(status=status):
                self.assertIsNone(
                    openalex._check_refused(_FakeResponse(status, "x")))
