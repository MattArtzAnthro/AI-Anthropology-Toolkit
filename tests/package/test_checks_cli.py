"""The `ai-anthro-check` command, driven through its real entry points.

    python3.12 -m unittest tests.package.test_checks_cli -v

`main(argv)` is the function the installed console script calls; one test
also runs `python -m ai_anthro_toolkit.checks` as a subprocess so the module
entry point is exercised exactly as a researcher would type it.
"""

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ai_anthro_toolkit.checks import cli, generated, registry

from .test_checks import GOOD_CODEBOOK, GOOD_CODED_DATA

REPO = Path(__file__).resolve().parents[2]


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main([str(a) for a in argv])
    return code, out.getvalue(), err.getvalue()


class CliBase(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self._registry = registry.REGISTRY

    def tearDown(self):
        registry.REGISTRY = self._registry
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, name, payload):
        path = self.dir / name
        path.write_text(payload if isinstance(payload, str) else json.dumps(payload),
                        encoding="utf-8")
        return path


class TestEntryPoints(CliBase):
    def test_console_script_points_at_main(self):
        text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('ai-anthro-check = "ai_anthro_toolkit.checks.cli:main"', text)

    def test_module_entry_point_runs_and_reports(self):
        path = self.write("codebook.json", GOOD_CODEBOOK)
        env = dict(os.environ, PYTHONPATH=str(REPO / "src"))
        proc = subprocess.run(
            [sys.executable, "-m", "ai_anthro_toolkit.checks", str(path),
             "--kind", "codebook"],
            capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("codebook:", proc.stdout)

    def test_module_entry_point_fails_on_a_missing_file(self):
        env = dict(os.environ, PYTHONPATH=str(REPO / "src"))
        proc = subprocess.run(
            [sys.executable, "-m", "ai_anthro_toolkit.checks",
             str(self.dir / "absent.json")],
            capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("does not exist", proc.stderr)


class TestRunningChecks(CliBase):
    def test_clean_codebook_says_what_could_not_be_run(self):
        code, out, err = run_cli(self.write("codebook.json", GOOD_CODEBOOK),
                                 "--kind", "codebook")
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("codebook: "))
        # Without --distinct-codes the exclusivity check is unrun, and the
        # report says so rather than reading as a pass.
        self.assertIn("could not be run", out)
        self.assertIn("[?]", out)

    def test_coded_data_against_a_codebook_reports_an_unknown_code(self):
        coded = [dict(GOOD_CODED_DATA[0]),
                 dict(GOOD_CODED_DATA[1], Deductive_Codes="invented_code",
                      All_Codes="invented_code")]
        code, out, err = run_cli(self.write("result.json", coded),
                                 "--kind", "coded_data",
                                 "--codebook", self.write("codebook.json", GOOD_CODEBOOK))
        self.assertEqual(code, 0, err)
        self.assertIn("[!]", out)
        self.assertIn("invented_code", out)
        self.assertIn("linters", out)  # the teaching note follows a finding

    def test_job_directory_is_read_through_its_result(self):
        self.write("result.json", GOOD_CODEBOOK)
        code, out, _ = run_cli(self.dir, "--kind", "codebook", "--overlapping-codes")
        self.assertEqual(code, 0)
        self.assertIn("codebook:", out)

    def test_csv_artifact(self):
        header = list(GOOD_CODEBOOK[0])
        lines = [",".join(header)] + [",".join(f'"{row[k]}"' for k in header)
                                      for row in GOOD_CODEBOOK]
        code, out, err = run_cli(self.write("codebook.csv", "\n".join(lines) + "\n"),
                                 "--kind", "codebook")
        self.assertEqual(code, 0, err)
        self.assertIn("codebook: ", out)


class TestRefusals(CliBase):
    def test_ambiguous_artifact_asks_for_kind(self):
        code, _, err = run_cli(self.write("data.json", [{"chunk_id": 0, "code_label": "x"}]))
        self.assertEqual(code, 2)
        self.assertIn("--kind", err)

    def test_undetectable_artifact_is_refused(self):
        code, _, err = run_cli(self.write("data.json", [{"anything": 1}]))
        self.assertEqual(code, 2)
        self.assertIn("cannot tell", err)

    def test_unreadable_formats_and_empty_directories(self):
        code, _, err = run_cli(self.write("notes.txt", "hello"))
        self.assertEqual(code, 2)
        self.assertIn("only .csv and .json", err)
        empty = self.dir / "job"
        empty.mkdir()
        code, _, err = run_cli(empty)
        self.assertEqual(code, 2)
        self.assertIn("holds no artifact", err)

    def test_malformed_json_is_a_clean_refusal_not_a_traceback(self):
        # Before the fix this escaped as an uncaught JSONDecodeError.
        code, _, err = run_cli(self.write("result.json", '[{"chunk_id": 0,'))
        self.assertEqual(code, 2)
        self.assertIn("could not be read", err)

    def test_non_utf8_csv_is_a_clean_refusal(self):
        path = self.dir / "codebook.csv"
        path.write_bytes("code_label,definition\nÉTAT,défini\n".encode("latin-1"))
        code, _, err = run_cli(path)
        self.assertEqual(code, 2)
        self.assertIn("could not be read", err)

    def test_mutually_exclusive_exclusivity_flags(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                cli.main([str(self.write("codebook.json", GOOD_CODEBOOK)),
                          "--distinct-codes", "--overlapping-codes"])
        self.assertEqual(ctx.exception.code, 2)


class TestProjectChecks(CliBase):
    RECORDS = [{"case_id": "1904-A", "decided": "1904-03-11"},
               {"case_id": "1904-B", "decided": ""}]

    def document(self):
        return generated.to_document(
            {"partial-presence": "required", "ordering": "meaningful"},
            artifact="cases", fields={"partial-presence": "decided"},
            instrument="case-file collector")

    def test_project_checks_beside_a_file_run_and_report_unenforceable(self):
        self.write(cli.PROJECT_CHECKS, self.document())
        code, out, err = run_cli(self.write("cases.json", self.RECORDS))
        self.assertEqual(code, 0, err)
        self.assertIn("cannot be checked from the data alone", out)
        self.assertIn("ordering", out)
        self.assertIn("cases: ", out)
        self.assertIn("[!]", out)  # the missing decision date fires

    def test_project_checks_inside_a_job_directory_are_found(self):
        # Before the fix, pointing at the directory looked for the checks
        # file in the directory's parent and silently ran none of them.
        self.write("result.json", self.RECORDS)
        self.write(cli.PROJECT_CHECKS, self.document())
        code, out, err = run_cli(self.dir)
        self.assertEqual(code, 0, err)
        self.assertIn("cases: ", out)
        self.assertIn("[!]", out)

    def test_a_corrupt_checks_file_is_refused(self):
        self.write(cli.PROJECT_CHECKS, "{not json")
        code, _, err = run_cli(self.write("cases.json", self.RECORDS))
        self.assertEqual(code, 2)
        self.assertIn(cli.PROJECT_CHECKS, err)

    def test_a_checks_file_with_an_unknown_answer_is_refused(self):
        doc = self.document()
        doc["answers"]["partial-presence"] = "whatever"
        self.write(cli.PROJECT_CHECKS, doc)
        code, _, err = run_cli(self.write("cases.json", self.RECORDS))
        self.assertEqual(code, 2)
        self.assertIn(cli.PROJECT_CHECKS, err)


class TestSidecarEdgeCases(CliBase):
    def test_unreadable_or_non_object_sidecar_is_ignored(self):
        path = self.write("result.json", GOOD_CODED_DATA)
        self.write(registry.PROVENANCE_SIDECAR, "not json")
        self.assertIsInstance(cli.load_artifact(path), list)
        self.write(registry.PROVENANCE_SIDECAR, [1, 2])
        self.assertIsInstance(cli.load_artifact(path), list)

    def test_legacy_sidecar_attaches_only_to_producer_names(self):
        stanza = registry.provenance_stanza(produced_by="t", codebook_labels=["a"])
        self.write(registry.PROVENANCE_SIDECAR, stanza)
        self.assertIsInstance(cli.load_artifact(self.write("result.json", [])), dict)
        self.assertIsInstance(cli.load_artifact(self.write("mine.json", [])), list)


if __name__ == "__main__":
    unittest.main()
