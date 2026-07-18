"""Live micro-tests for the YouTube datasources.

YouTube blocks automated requests from datacenter/cloud IPs frequently, so a
RuntimeError that reports a block or rate limit counts as a pass (skip); a
silent empty result fails.

    python3.12 -m unittest tests.package.test_datasources_youtube -v
"""

import os
import re
import unittest

if os.environ.get("AAT_SKIP_LIVE_SCRAPERS"):
    raise unittest.SkipTest(
        "AAT_SKIP_LIVE_SCRAPERS set — skipping live YouTube queries")

from ai_anthro_toolkit.datasources import get_youtube_transcript, search_youtube
from ai_anthro_toolkit.datasources.youtube import _parse_video_id

try:
    import scrapetube  # noqa: F401
    HAVE_SCRAPETUBE = True
except ImportError:
    HAVE_SCRAPETUBE = False

try:
    import youtube_transcript_api  # noqa: F401
    HAVE_TRANSCRIPT_API = True
except ImportError:
    HAVE_TRANSCRIPT_API = False

_BLOCKED = re.compile(r"block|rate", re.IGNORECASE)

# Sir Ken Robinson, "Do schools kill creativity?" (TED) — stable, captioned.
TED_TALK_ID = "iG9CE55wbtY"


class TestParseVideoId(unittest.TestCase):
    def test_full_watch_url(self):
        self.assertEqual(
            _parse_video_id("https://www.youtube.com/watch?v=iG9CE55wbtY"),
            "iG9CE55wbtY")

    def test_youtu_be_url(self):
        self.assertEqual(_parse_video_id("https://youtu.be/iG9CE55wbtY"),
                         "iG9CE55wbtY")

    def test_bare_id(self):
        self.assertEqual(_parse_video_id("iG9CE55wbtY"), "iG9CE55wbtY")

    def test_unparseable_raises(self):
        with self.assertRaises(ValueError):
            _parse_video_id("not a video id")


@unittest.skipUnless(HAVE_SCRAPETUBE, "scrapetube not installed")
class TestSearchYouTubeLive(unittest.TestCase):
    def test_search_micro_run(self):
        try:
            records = search_youtube("ethnographic methods", limit=5)
        except RuntimeError as exc:
            if _BLOCKED.search(str(exc)):
                self.skipTest(f"YouTube blocked or rate-limited the request: {exc}")
            raise
        self.assertGreaterEqual(len(records), 3)
        for rec in records:
            for field in ("video_id", "title", "channel", "views",
                          "duration", "url"):
                self.assertIn(field, rec)
            self.assertRegex(
                rec["url"], r"^https://www\.youtube\.com/watch\?v=[\w-]{11}$")
            self.assertTrue(rec["title"])


@unittest.skipUnless(HAVE_TRANSCRIPT_API, "youtube-transcript-api not installed")
class TestGetYouTubeTranscriptLive(unittest.TestCase):
    def test_ted_talk_transcript(self):
        try:
            result = get_youtube_transcript(TED_TALK_ID)
        except RuntimeError as exc:
            if _BLOCKED.search(str(exc)):
                self.skipTest(f"YouTube blocked or rate-limited the request: {exc}")
            raise
        self.assertEqual(result["video_id"], TED_TALK_ID)
        self.assertIsInstance(result["auto_generated"], bool)
        self.assertTrue(result["language"])
        self.assertGreaterEqual(len(result["segments"]), 100)
        for seg in result["segments"][:5]:
            for field in ("start", "duration", "text"):
                self.assertIn(field, seg)
        self.assertTrue(result["text"])

    def test_invalid_video_id_raises(self):
        with self.assertRaises(RuntimeError):
            get_youtube_transcript("zzzzzzzzzzz")
