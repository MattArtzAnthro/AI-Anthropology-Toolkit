"""Live micro-queries for the scraper-based datasources (Google News, Google
Trends, Google Scholar).

These sources have no official APIs; the underlying libraries scrape public
endpoints and get rate-limited or blocked, especially from datacenter/cloud
IPs. Each test therefore passes on either real data with the expected fields
OR a RuntimeError that carries block/rate-limit guidance, and fails on silent
empty success or unexpected exception types.

    python3.12 -m unittest tests.package.test_datasources_scrapers -v
"""

import importlib.util
import unittest


def _lib_missing(name: str) -> bool:
    return importlib.util.find_spec(name) is None


def _is_block_error(e: RuntimeError) -> bool:
    text = str(e).lower()
    return any(marker in text for marker in ("rate-limit", "rate limit", "block"))


class TestGoogleNewsLive(unittest.TestCase):
    def test_search_google_news(self):
        if _lib_missing("gnews"):
            self.skipTest("gnews not installed")
        from ai_anthro_toolkit.datasources import search_google_news
        try:
            records = search_google_news("anthropology", limit=5)
        except RuntimeError as e:
            self.assertTrue(_is_block_error(e),
                            f"RuntimeError without block guidance: {e}")
            return
        self.assertGreaterEqual(len(records), 1,
                                "empty success should have raised RuntimeError")
        first = records[0]
        for field in ("title", "publisher", "published", "url", "description"):
            self.assertIn(field, first)
        self.assertTrue(first["title"])


class TestGoogleTrendsLive(unittest.TestCase):
    def test_get_google_trends(self):
        if _lib_missing("pytrends"):
            self.skipTest("pytrends not installed")
        from ai_anthro_toolkit.datasources import get_google_trends
        try:
            data = get_google_trends("anthropology", timeframe="today 3-m")
        except RuntimeError as e:
            self.assertTrue(_is_block_error(e),
                            f"RuntimeError without block guidance: {e}")
            return
        for key in ("interest_over_time", "interest_by_region", "related_queries"):
            self.assertIn(key, data)
        # All-empty must surface as RuntimeError, never as empty success.
        self.assertTrue(data["interest_over_time"] or data["interest_by_region"],
                        "all-empty success should have raised RuntimeError")
        if data["interest_over_time"]:
            first = data["interest_over_time"][0]
            self.assertIn("date", first)
            self.assertIn("anthropology", first)
        self.assertIn("anthropology", data["related_queries"])
        for kind in ("top", "rising"):
            self.assertIn(kind, data["related_queries"]["anthropology"])


class TestGoogleScholarLive(unittest.TestCase):
    def test_search_google_scholar(self):
        if _lib_missing("scholarly"):
            self.skipTest("scholarly not installed")
        from ai_anthro_toolkit.datasources import search_google_scholar
        try:
            records = search_google_scholar("digital ethnography", limit=3)
        except RuntimeError as e:
            self.assertTrue(_is_block_error(e),
                            f"RuntimeError without block guidance: {e}")
            return
        self.assertGreaterEqual(len(records), 1,
                                "empty success should have raised RuntimeError")
        first = records[0]
        for field in ("title", "authors", "year", "venue", "cited_by_count", "url"):
            self.assertIn(field, first)
        self.assertTrue(first["title"])
        self.assertIsInstance(first["authors"], list)


if __name__ == "__main__":
    unittest.main()
