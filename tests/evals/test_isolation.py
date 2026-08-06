"""The subject run's isolation contract, tested without calling a model.

An eval that runs `claude -p` inside this repository is not measuring the
skill body it passes. The repo's own CLAUDE.md restates the gates, the intact
SKILL.md is readable from disk, `.mcp.json` registers a server that enforces
codebook ratification server-side, and the plugin is installed. Any of those
can carry a gate that the system prompt does not.

That does not merely weaken a result — it makes the planned ablation and
null-floor arms meaningless, because the thing being removed is still
reachable by four other routes.

These tests pin what the subject invocation must carry. They cost nothing and
run in CI; whether isolation changes the verdicts is a separate, measured
question.
"""

import unittest
from pathlib import Path

from tests.evals import judge

REPO = Path(__file__).resolve().parent.parent.parent


class SubjectInvocation(unittest.TestCase):
    def argv(self):
        return judge.subject_argv("a user message", "SKILL BODY HERE",
                                  model="test-model")

    def test_the_skill_is_passed_as_a_system_prompt(self):
        argv = self.argv()
        self.assertIn("--system-prompt", argv)
        self.assertEqual(argv[argv.index("--system-prompt") + 1],
                         "SKILL BODY HERE")

    def test_the_skill_is_not_smuggled_into_the_user_turn(self):
        # It was previously wrapped in <system> XML inside the prompt, which
        # is a user message wearing a costume.
        argv = self.argv()
        prompt = argv[argv.index("-p") + 1]
        self.assertNotIn("SKILL BODY HERE", prompt)
        self.assertNotIn("<system>", prompt)

    def test_mcp_servers_are_excluded(self):
        # .mcp.json registers a server whose start_coding_job refuses an
        # unratified codebook. With it loaded, that gate holds regardless of
        # what the skill body says.
        self.assertIn("--strict-mcp-config", self.argv())

    def test_file_reading_tools_are_denied(self):
        argv = self.argv()
        self.assertIn("--disallowedTools", argv)
        denied = set(judge.DISALLOWED_TOOLS)
        for tool in ("Read", "Glob", "Grep", "Bash", "Task"):
            with self.subTest(tool=tool):
                self.assertIn(tool, denied)

    def test_the_model_is_passed_explicitly(self):
        argv = self.argv()
        self.assertEqual(argv[argv.index("--model") + 1], "test-model")


class WorkingDirectory(unittest.TestCase):
    """`claude -p` inherits the working directory's CLAUDE.md."""

    def test_the_run_directory_is_outside_the_repository(self):
        run_dir = Path(judge.isolated_cwd()).resolve()
        self.assertFalse(
            str(run_dir).startswith(str(REPO)),
            f"subject would run inside the repo at {run_dir}, inheriting "
            f"its CLAUDE.md",
        )

    def test_the_run_directory_carries_no_claude_md(self):
        self.assertFalse((Path(judge.isolated_cwd()) / "CLAUDE.md").exists())

    def test_the_run_directory_carries_no_mcp_config(self):
        self.assertFalse((Path(judge.isolated_cwd()) / ".mcp.json").exists())


class TheGateEvalsUseIt(unittest.TestCase):
    """Six of thirteen verdicts changed when the leak was closed, so an eval
    that quietly reverts to the unisolated path is not measuring the skill."""

    def source(self):
        return (REPO / "tests" / "evals" / "test_gate_holding.py").read_text(
            encoding="utf-8")

    def test_the_subject_runs_through_the_isolated_runner(self):
        self.assertIn("run_subject", self.source())

    def test_the_skill_is_not_wrapped_in_system_xml_anywhere(self):
        self.assertNotIn("<system>", self.source())

    def test_the_evals_do_not_shell_out_to_claude_directly(self):
        # A direct subprocess call would bypass every isolation measure.
        self.assertNotIn('"claude", "-p"', self.source())


class LeakInventory(unittest.TestCase):
    """The routes by which a gate reaches the subject other than the system
    prompt. Enumerated so that a new one added to the repo is a decision
    rather than a surprise."""

    def test_every_known_leak_is_named_with_its_countermeasure(self):
        self.assertEqual(
            set(judge.LEAKS),
            {"repo-claude-md", "on-disk-skill", "mcp-server", "installed-plugin"},
        )

    def test_each_leak_states_how_it_is_closed(self):
        for name, how in judge.LEAKS.items():
            with self.subTest(leak=name):
                self.assertTrue(how.strip())


if __name__ == "__main__":
    unittest.main()
