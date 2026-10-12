"""The release script's contract, tested without building or uploading.

Four consecutive releases shipped version pins ahead of the upload that would
satisfy them, including the commit that added RELEASING.md. A document does
not enforce an order. These tests pin the parts of `scripts/release.py` that
can be checked without a network call, which is most of what went wrong:
which files carry a pin, that the resolve check is extras-qualified, and that
the upload cannot happen before verification or after the push signal.

    python3 -m unittest tests.test_release -v
"""

import contextlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
             "AGENTS.md", "GEMINI.md", "README.md", ".gemini/settings.json"},
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
        self.assertIn("[data", release.resolve_spec("9.9.9"))

    def test_the_resolve_check_uses_the_plugins_exact_extras(self):
        """Resolving a different extras set from the one the plugin installs
        checks a spec nobody runs. It is read from the plugin's .mcp.json."""
        mcp = json.loads((REPO / "plugins" / "ai-anthropology" / ".mcp.json")
                         .read_text(encoding="utf-8"))
        args = mcp["mcpServers"]["ai-anthropology"]["args"]
        spec = args[args.index("--from") + 1]
        version = release.read_version(REPO)
        self.assertEqual(release.resolve_spec(version), spec)
        self.assertEqual(release.resolve_spec("9.9.9"),
                         spec.replace(f"=={version}", "==9.9.9"))

    def test_a_pin_site_with_the_right_version_but_wrong_extras_disagrees(self):
        version = release.read_version(REPO)
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        for site in release.PIN_SITES:
            (tmp / site).parent.mkdir(parents=True, exist_ok=True)
            (tmp / site).write_text((REPO / site).read_text(encoding="utf-8"),
                                    encoding="utf-8")
        (tmp / "README.md").write_text(
            f'uvx --from "ai-anthropology-toolkit[data]=={version}" ai-anthro-mcp',
            encoding="utf-8")
        with mock.patch.object(release, "REPO", tmp):
            self.assertEqual(release.disagreeing_pins(tmp, version), ["README.md"])

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


class LiveClassConvention(unittest.TestCase):
    """Every live class in the package suite must be recognized as live, or
    one rate-limited endpoint blocks a release preflight."""

    def test_every_live_class_in_the_suite_is_classified_live(self):
        names = set()
        for path in (REPO / "tests" / "package").glob("test_*.py"):
            names.update(re.findall(r"^class (\w*Live\w*)\(", path.read_text(encoding="utf-8"),
                                    re.M))
        self.assertGreater(len(names), 5)
        for name in sorted(names):
            with self.subTest(name=name):
                self.assertTrue(release.is_live(
                    f"test_x (tests.package.test_mod.{name}.test_x)"))

    def test_a_lowercase_live_in_a_method_name_is_not_enough(self):
        self.assertFalse(release.is_live(
            "test_reload_live_values (tests.package.test_mod.TestCache.test_reload_live_values)"))


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class _FakeRepo(unittest.TestCase):
    """A throwaway repository carrying every pin site at one version."""

    VERSION = "9.9.9"

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo, True)
        spec = f"ai-anthropology-toolkit[data,api]=={self.VERSION}"
        for site in release.PIN_SITES:
            path = self.repo / site
            path.parent.mkdir(parents=True, exist_ok=True)
            if site.endswith(".mcp.json"):
                path.write_text(json.dumps({"mcpServers": {"ai-anthropology": {
                    "command": "uvx", "args": ["--from", spec, "ai-anthro-mcp"]}}}),
                    encoding="utf-8")
            else:
                path.write_text(f'version = "{self.VERSION}"\n', encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text(f"### {self.VERSION} - today\n",
                                                encoding="utf-8")
        patcher = mock.patch.object(release, "REPO", self.repo)
        patcher.start()
        self.addCleanup(patcher.stop)

    def quiet(self):
        return contextlib.redirect_stdout(io.StringIO())


class PreflightGate(_FakeRepo):
    def test_disagreeing_pins_stop_the_release(self):
        (self.repo / "GEMINI.md").write_text("pinned to 1.0.0", encoding="utf-8")
        with mock.patch.object(release, "_run") as run:
            with self.assertRaises(SystemExit) as ctx:
                release.preflight(self.VERSION)
        self.assertIn("GEMINI.md", str(ctx.exception))
        run.assert_not_called()

    def test_missing_changelog_entry_stops_the_release(self):
        (self.repo / "CHANGELOG.md").write_text("### 1.0.0\n", encoding="utf-8")
        with self.assertRaises(SystemExit) as ctx:
            release.preflight(self.VERSION)
        self.assertIn("CHANGELOG", str(ctx.exception))

    def test_green_suite_passes_with_src_on_the_path(self):
        with mock.patch.object(release, "_run", return_value=_completed()) as run:
            release.preflight(self.VERSION)
        env = run.call_args.kwargs["env"]
        self.assertTrue(env["PYTHONPATH"].startswith(str(self.repo / "src")))

    def test_an_ordinary_failure_blocks(self):
        out = "FAIL: test_codes (tests.package.test_checks.MutationRound.test_codes)\n"
        with mock.patch.object(release, "_run", return_value=_completed(1, stderr=out)):
            with self.assertRaises(SystemExit) as ctx:
                release.preflight(self.VERSION)
        self.assertIn("not green", str(ctx.exception))

    def test_a_crash_with_no_failure_lines_blocks(self):
        with mock.patch.object(release, "_run",
                               return_value=_completed(1, stderr="ImportError: boom")):
            with self.assertRaises(SystemExit):
                release.preflight(self.VERSION)

    def test_live_only_failures_are_rerun_and_reported_not_blocking(self):
        out = ("FAIL: test_a (tests.package.test_datasources_collectors.TestNgramLive.test_a)\n"
               "ERROR: test_b (tests.package.test_package.TestDataSourcesLive.test_b)\n")
        results = [_completed(1, stderr=out), _completed(0), _completed(1)]
        with mock.patch.object(release, "_run", side_effect=results) as run, \
                self.quiet() as printed:
            release.preflight(self.VERSION)
        self.assertEqual(run.call_count, 3)
        rerun_target = run.call_args_list[1].args[0][-1]
        self.assertEqual(rerun_target,
                         "tests.package.test_datasources_collectors.TestNgramLive.test_a")
        self.assertIn("NOT blocking", printed.getvalue())
        self.assertIn("passed on re-run", printed.getvalue())


class BuildVerifyPublish(_FakeRepo):
    def test_build_failure_stops(self):
        with mock.patch.object(release, "_run", return_value=_completed(1, stderr="bad")):
            with self.assertRaises(SystemExit) as ctx:
                release.build(self.repo / "dist")
        self.assertIn("build failed", str(ctx.exception))

    def _verify(self, results, scripts=("ai-anthro-mcp", "ai-anthro-doctor",
                                        "ai-anthro-check")):
        dist = self.repo / "dist"
        dist.mkdir()
        (dist / "pkg-9.9.9-py3-none-any.whl").write_text("", encoding="utf-8")
        venv = self.repo / "venv"

        def fake_run(cmd, **kw):
            if cmd[1:3] == ["-m", "venv"]:
                (venv / "bin").mkdir(parents=True)
                for name in scripts:
                    (venv / "bin" / name).write_text("", encoding="utf-8")
            return results.pop(0)

        with mock.patch.object(release, "_run", side_effect=fake_run):
            release.verify(dist, self.VERSION, venv)

    def test_verify_passes_on_a_clean_install(self):
        self._verify([_completed(), _completed(), _completed(stdout="9.9.9\n")])

    def test_verify_catches_a_failed_install(self):
        with self.assertRaises(SystemExit) as ctx:
            self._verify([_completed(), _completed(1)])
        self.assertIn("install failed", str(ctx.exception))

    def test_verify_catches_a_version_mismatch(self):
        with self.assertRaises(SystemExit) as ctx:
            self._verify([_completed(), _completed(), _completed(stdout="9.9.8\n")])
        self.assertIn("probe failed", str(ctx.exception))

    def test_verify_catches_a_missing_console_script(self):
        with self.assertRaises(SystemExit) as ctx:
            self._verify([_completed(), _completed(), _completed(stdout="9.9.9")],
                         scripts=("ai-anthro-mcp",))
        self.assertIn("ai-anthro-check", str(ctx.exception))

    def test_twine_missing_names_the_install_command(self):
        with mock.patch.object(release, "_run", return_value=_completed(1)):
            with self.assertRaises(SystemExit) as ctx:
                release.twine_check(self.repo)
        self.assertIn("pip install twine", str(ctx.exception))

    def test_twine_check_reports_both_streams(self):
        results = [_completed(), _completed(0, stdout="Checking x: FAILED", stderr="why")]
        with mock.patch.object(release, "_run", side_effect=results):
            with self.assertRaises(SystemExit) as ctx:
                release.twine_check(self.repo)
        self.assertIn("FAILED", str(ctx.exception))
        self.assertIn("why", str(ctx.exception))
        with mock.patch.object(release, "_run", side_effect=[_completed(), _completed()]):
            release.twine_check(self.repo)

    def test_upload_failure_stops(self):
        with mock.patch.object(release, "_run", side_effect=[_completed(), _completed(1)]):
            with self.assertRaises(SystemExit) as ctx:
                release.upload(self.repo)
        self.assertIn("upload failed", str(ctx.exception))
        with mock.patch.object(release, "_run", side_effect=[_completed(), _completed()]):
            release.upload(self.repo)


class AwaitResolve(unittest.TestCase):
    def test_waits_until_visible_without_re_uploading(self):
        runs = [_completed(1), _completed(0)]
        with mock.patch.object(release, "_run", side_effect=runs) as run, \
                mock.patch.object(release.time, "sleep") as sleep, \
                mock.patch.object(release.time, "monotonic", side_effect=[0, 10, 40]), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(release.await_resolve("9.9.9", budget=900), release.VISIBLE)
        self.assertEqual(sleep.call_count, 1)
        for call in run.call_args_list:
            self.assertNotIn("upload", call.args[0])
            self.assertIn(release.resolve_spec("9.9.9"), call.args[0])

    def test_gives_up_to_a_human_after_the_budget(self):
        with mock.patch.object(release, "_run", return_value=_completed(1)), \
                mock.patch.object(release.time, "sleep"), \
                mock.patch.object(release.time, "monotonic", side_effect=[0, 1000]):
            self.assertEqual(release.await_resolve("9.9.9", budget=900), release.UNRESOLVED)


class MainSequence(_FakeRepo):
    def _patch_steps(self, resolve=release.VISIBLE):
        calls = []
        patches = [mock.patch.object(release, name, side_effect=lambda *a, n=name, **k:
                                     calls.append(n))
                   for name in ("preflight", "build", "verify", "twine_check", "upload")]
        patches.append(mock.patch.object(release, "await_resolve",
                                         side_effect=lambda v: calls.append("await") or resolve))
        return calls, patches

    def _main(self, argv, resolve=release.VISIBLE):
        calls, patches = self._patch_steps(resolve)
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            printed = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            code = release.main(argv)
        return code, calls, printed.getvalue()

    def test_dry_run_stops_before_the_upload(self):
        code, calls, out = self._main(["--dry-run"])
        self.assertEqual(code, 0)
        self.assertEqual(calls, ["preflight", "build", "verify", "twine_check"])
        self.assertIn("Nothing was published", out)

    def test_full_run_ends_with_the_push_signal(self):
        code, calls, out = self._main([])
        self.assertEqual(code, 0)
        self.assertEqual(calls[-2:], ["upload", "await"])
        self.assertIn("Safe to push", out)

    def test_unresolved_upload_says_do_not_re_upload(self):
        code, _, out = self._main([], resolve=release.UNRESOLVED)
        self.assertEqual(code, 1)
        self.assertIn("Do NOT re-upload", out)
        self.assertNotIn("Safe to push", out)

    def test_version_is_read_from_pyproject(self):
        (self.repo / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            release.read_version(self.repo)


class ChangelogGate(unittest.TestCase):
    def test_missing_changelog_entry_is_caught(self):
        self.assertFalse(release.changelog_has_entry(REPO, "0.0.0"))

    def test_present_changelog_entry_is_found(self):
        self.assertTrue(
            release.changelog_has_entry(REPO, release.read_version(REPO)))


if __name__ == "__main__":
    unittest.main()
