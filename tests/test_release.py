"""The release script's contract, tested without building or uploading.

Four consecutive releases shipped version pins ahead of the upload that would
satisfy them, including the commit that added RELEASING.md. A document does
not enforce an order. These tests pin the parts of `scripts/release.py` that
can be checked without a network call, which is most of what went wrong:
which files carry a pin, that the resolve check is extras-qualified, and that
the upload cannot happen before verification or after the push signal.

    python3 -m unittest tests.test_release -v
"""

import unittest
from pathlib import Path

from scripts import release

REPO = Path(__file__).resolve().parent.parent


class PinSites(unittest.TestCase):
    """A release breaks when one pin site is missed. They are enumerated
    here so a new one added to the repo fails a test rather than a release."""

    def test_every_known_pin_site_is_listed(self):
        self.assertEqual(
            set(release.PIN_SITES),
            {"pyproject.toml", "src/ai_anthro_toolkit/__init__.py",
             ".mcp.json", "plugins/ai-anthropology/.mcp.json",
             "AGENTS.md", "GEMINI.md"},
        )

    def test_all_pin_sites_exist_in_the_repo(self):
        for name in release.PIN_SITES:
            with self.subTest(site=name):
                self.assertTrue((REPO / name).is_file())

    def test_reads_the_version_from_pyproject(self):
        self.assertRegex(release.read_version(REPO), r"^\d+\.\d+\.\d+$")

    def test_disagreeing_pins_are_reported(self):
        bad = release.disagreeing_pins(REPO, "0.0.0-nonexistent")
        self.assertEqual(set(bad), set(release.PIN_SITES),
                         "a version no file carries must flag every site")

    def test_agreeing_pins_report_nothing(self):
        self.assertEqual(
            release.disagreeing_pins(REPO, release.read_version(REPO)), [])


class ResolveSpec(unittest.TestCase):
    """A bare `==X` resolves minutes before `[data]==X` does, so checking the
    simplified form gives a false all-clear on the thing still broken."""

    def test_the_resolve_check_is_extras_qualified(self):
        self.assertIn("[data]", release.resolve_spec("9.9.9"))

    def test_the_resolve_check_pins_the_exact_version(self):
        self.assertIn("==9.9.9", release.resolve_spec("9.9.9"))


class StepOrder(unittest.TestCase):
    """The ordering is the whole point. If it can be reordered silently, the
    script is a longer version of the checklist that already failed."""

    def index(self, name):
        return [s.name for s in release.STEPS].index(name)

    def test_upload_comes_after_clean_venv_verification(self):
        self.assertLess(self.index("verify"), self.index("upload"))

    def test_upload_comes_after_metadata_check(self):
        self.assertLess(self.index("twine-check"), self.index("upload"))

    def test_the_push_signal_comes_after_the_resolve_confirmation(self):
        self.assertLess(self.index("await-resolve"), self.index("safe-to-push"))

    def test_the_resolve_confirmation_comes_after_the_upload(self):
        self.assertLess(self.index("upload"), self.index("await-resolve"))

    def test_safe_to_push_is_last(self):
        self.assertEqual(release.STEPS[-1].name, "safe-to-push")

    def test_preflight_is_first(self):
        self.assertEqual(release.STEPS[0].name, "preflight")

    def test_every_step_states_what_it_would_break(self):
        # A step whose failure mode is unstated gets skipped under pressure.
        for step in release.STEPS:
            with self.subTest(step=step.name):
                self.assertTrue(step.why.strip())


class NegativeResolveIsNotFailure(unittest.TestCase):
    """Both PyPI read paths are CDN-cached. Re-uploading on a negative
    resolve is the wrong reflex and the version cannot be reclaimed."""

    def test_a_negative_resolve_is_classified_as_not_yet_visible(self):
        self.assertEqual(
            release.classify_resolve(succeeded=False, elapsed=30,
                                     budget=release.RESOLVE_BUDGET),
            release.NOT_YET_VISIBLE)

    def test_a_negative_resolve_past_the_budget_is_escalated_not_retried(self):
        self.assertEqual(
            release.classify_resolve(succeeded=False,
                                     elapsed=release.RESOLVE_BUDGET + 1,
                                     budget=release.RESOLVE_BUDGET),
            release.UNRESOLVED)

    def test_a_positive_resolve_is_confirmation(self):
        self.assertEqual(
            release.classify_resolve(succeeded=True, elapsed=1,
                                     budget=release.RESOLVE_BUDGET),
            release.VISIBLE)

    def test_nothing_in_the_module_re_uploads(self):
        source = (REPO / "scripts" / "release.py").read_text(encoding="utf-8")
        self.assertNotIn("retry_upload", source)
        self.assertIn("cannot be reclaimed", source,
                      "the module must state why an upload is not retried")


class LiveTestsReportRatherThanBlock(unittest.TestCase):
    """Tests that reach a network service or the `claude` CLI fail
    intermittently under a long suite run and pass in isolation. A gate that
    cries wolf gets routed around, which is the gate that becomes a form. So
    a live failure is re-run, and only a repeat failure blocks."""

    def test_known_live_tests_are_enumerated(self):
        self.assertTrue(release.LIVE_TESTS)

    def test_the_flaky_cli_job_test_is_listed(self):
        self.assertTrue(
            any("TestApiModeLiveViaCli" in t for t in release.LIVE_TESTS))

    def test_the_live_datasource_tests_are_listed(self):
        self.assertTrue(
            any("TestDataSourcesLive" in t for t in release.LIVE_TESTS))

    def test_a_live_failure_is_classified_as_live(self):
        self.assertTrue(release.is_live(
            "test_api_mode_coding_job_live "
            "(tests.package.test_server_pipeline.TestApiModeLiveViaCli...)"))

    def test_an_ordinary_failure_is_not_classified_as_live(self):
        self.assertFalse(release.is_live(
            "test_codes_resolve (tests.package.test_checks.MutationRound)"))

    def test_a_live_failure_never_blocks_even_when_it_repeats(self):
        # Measured 2026-08-06: OpenAlex returned 429 on every attempt,
        # including in isolation. That is someone else's rate limiter, not a
        # defect in this package, and it is indistinguishable from a real
        # outage from here. RELEASING.md already rules that these are not a
        # release gate; blocking on a repeat would contradict it and teach
        # the maintainer to bypass preflight.
        self.assertFalse(release.blocks(is_live_test=True, repeated=True))

    def test_a_repeated_live_failure_is_still_reported(self):
        self.assertTrue(release.reports(is_live_test=True, repeated=True))

    def test_a_live_failure_that_clears_on_rerun_does_not_block(self):
        self.assertFalse(release.blocks(is_live_test=True, repeated=False))

    def test_an_ordinary_failure_blocks_without_a_rerun(self):
        self.assertTrue(release.blocks(is_live_test=False, repeated=False))


class ChangelogGate(unittest.TestCase):
    def test_missing_changelog_entry_is_caught(self):
        self.assertFalse(release.changelog_has_entry(REPO, "0.0.0"))

    def test_present_changelog_entry_is_found(self):
        self.assertTrue(
            release.changelog_has_entry(REPO, release.read_version(REPO)))


if __name__ == "__main__":
    unittest.main()
