"""Live micro-tests for the ngram, podcast, and patents data sources.

    python3.12 -m unittest tests.package.test_datasources_collectors -v
"""

import unittest

from ai_anthro_toolkit.datasources import (
    get_ngram_frequencies,
    get_podcast_episodes,
    search_google_patents,
)

NPR_FEED = "https://feeds.npr.org/510289/podcast.xml"


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
