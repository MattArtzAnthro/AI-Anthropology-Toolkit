"""Environment doctor: tells a sandboxed agent which sources work from here.

The doctor exists for coding-agent sandboxes (Claude Cowork, Codex CLI,
Gemini CLI) where the MCP server is absent and the agent pip-installs the
package instead: run it first, collect only from reachable sources, and
route blocked ones to local execution or Colab honestly.

    python3.12 -m unittest tests.package.test_doctor -v
"""

import io
import unittest
from contextlib import redirect_stdout

from ai_anthro_toolkit import doctor


def all_ok(url, timeout):
    return 200


def all_blocked(url, timeout):
    raise OSError("connection refused by network policy")


def google_blocked(url, timeout):
    if "google.com" in url or "youtube.com" in url:
        return 403
    return 200


class TestEnvironmentReport(unittest.TestCase):
    def test_covers_all_eleven_sources(self):
        report = doctor.environment_report(fetch=all_ok)
        self.assertEqual(len(report["sources"]), 11)
        names = {s["name"] for s in report["sources"]}
        for expected in ("OpenAlex", "CrossRef", "PubMed", "Google Trends",
                         "Google Scholar", "YouTube transcripts"):
            self.assertIn(expected, names)
        self.assertTrue(all(s["reachable"] for s in report["sources"]))

    def test_network_failures_marked_unreachable_not_raised(self):
        report = doctor.environment_report(fetch=all_blocked)
        self.assertTrue(all(not s["reachable"] for s in report["sources"]))

    def test_sandbox_pattern_yields_split_verdict_and_colab_fallback(self):
        report = doctor.environment_report(fetch=google_blocked)
        by_name = {s["name"]: s for s in report["sources"]}
        self.assertTrue(by_name["OpenAlex"]["reachable"])
        self.assertTrue(by_name["CrossRef"]["reachable"])
        self.assertFalse(by_name["Google Trends"]["reachable"])
        self.assertIn("colab", by_name["Google Trends"]["fallback"].lower())

    def test_reports_extras_installed(self):
        report = doctor.environment_report(fetch=all_ok)
        self.assertIn("data", report["extras"])
        self.assertIn("chunking", report["extras"])
        self.assertIsInstance(report["extras"]["data"], bool)

    def test_scraper_sources_carry_honest_caveat(self):
        report = doctor.environment_report(fetch=all_ok)
        trends = next(s for s in report["sources"]
                      if s["name"] == "Google Trends")
        self.assertIn("block", trends["note"].lower())

    def test_main_prints_human_readable_summary(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            doctor.main(fetch=google_blocked)
        out = buf.getvalue()
        self.assertIn("OpenAlex", out)
        self.assertIn("unreachable", out.lower())
        self.assertIn("pip install", out)


if __name__ == "__main__":
    unittest.main()
