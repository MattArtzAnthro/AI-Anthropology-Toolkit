"""Tests for the LLM wrappers (ai_anthro_toolkit.llm).

The Anthropic client is replaced at the import boundary with a fake module,
so these run offline and never spend money.

    python3.12 -m unittest tests.package.test_llm -v
"""

import sys
import types
import unittest
from unittest import mock

from ai_anthro_toolkit import llm as llm_mod


class _Block:
    def __init__(self, text):
        self.text = text


class _Response:
    def __init__(self, text):
        self.content = [_Block(text)]


class FakeMessages:
    """Scripted messages.create: each item is a reply string or an exception."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, BaseException):
            raise item
        return _Response(item)


def fake_anthropic(script):
    """A stand-in `anthropic` module whose client replays `script`."""
    messages = FakeMessages(script)
    module = types.ModuleType("anthropic")

    class Anthropic:
        def __init__(self, api_key):
            self.api_key = api_key
            self.messages = messages

    module.Anthropic = Anthropic
    return module, messages


class TestClaudeLLM(unittest.TestCase):
    def _llm(self, script, **kwargs):
        module, messages = fake_anthropic(script)
        with mock.patch.dict(sys.modules, {"anthropic": module}):
            llm = llm_mod.ClaudeLLM(api_key="sk-test", **kwargs)
        return llm, messages

    def test_returns_first_text_block_and_sends_the_request_shape(self):
        llm, messages = self._llm(["coded: MUTUAL_AID"], model="claude-test")
        self.assertEqual(llm.client.api_key, "sk-test")
        out = llm("Code this chunk.", system="You are a coder.",
                  temperature=0.0, max_tokens=64)
        self.assertEqual(out, "coded: MUTUAL_AID")
        sent = messages.calls[0]
        self.assertEqual(sent["model"], "claude-test")
        self.assertEqual(sent["max_tokens"], 64)
        self.assertEqual(sent["temperature"], 0.0)
        self.assertEqual(sent["system"], "You are a coder.")
        self.assertEqual(sent["messages"],
                         [{"role": "user", "content": "Code this chunk."}])

    def test_no_system_key_when_system_is_empty(self):
        llm, messages = self._llm(["ok"])
        llm("prompt")
        self.assertNotIn("system", messages.calls[0])

    def test_retries_transient_errors_with_backoff(self):
        llm, messages = self._llm([ConnectionError("reset"),
                                   TimeoutError("slow"), "third time"])
        with mock.patch.object(llm_mod.time, "sleep") as sleep:
            self.assertEqual(llm("p"), "third time")
        self.assertEqual(len(messages.calls), 3)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2])

    def test_exhausted_retries_raise_the_last_real_error(self):
        llm, messages = self._llm([ConnectionError("first"),
                                   ConnectionError("second")], max_retries=2)
        with mock.patch.object(llm_mod.time, "sleep") as sleep:
            with self.assertRaises(ConnectionError) as ctx:
                llm("p")
        self.assertEqual(str(ctx.exception), "second")
        self.assertEqual(len(messages.calls), 2)
        # No sleep after the final attempt.
        self.assertEqual(sleep.call_count, 1)

    def test_single_attempt_raises_without_sleeping(self):
        llm, _ = self._llm([RuntimeError("overloaded")], max_retries=1)
        with mock.patch.object(llm_mod.time, "sleep") as sleep:
            with self.assertRaises(RuntimeError):
                llm("p")
        sleep.assert_not_called()

    def test_zero_retries_is_refused_with_a_clear_error(self):
        # Before the fix this constructed fine and then raised `None`
        # (TypeError: exceptions must derive from BaseException) on first use.
        for bad in (0, -1):
            with self.assertRaises(ValueError) as ctx:
                self._llm([], max_retries=bad)
            self.assertIn("max_retries", str(ctx.exception))


class TestMakeLLM(unittest.TestCase):
    def test_delegated_mode_raises_work_packet(self):
        llm = llm_mod.make_llm("delegated")
        with self.assertRaises(llm_mod.WorkPacket) as ctx:
            llm("Build themes.", system="sys")
        self.assertEqual(ctx.exception.prompt, "Build themes.")
        self.assertEqual(ctx.exception.system, "sys")
        self.assertEqual(ctx.exception.purpose, "completion")

    def test_api_mode_without_key_says_what_to_do(self):
        with self.assertRaises(ValueError) as ctx:
            llm_mod.make_llm("api", api_key=None)
        self.assertIn("delegated", str(ctx.exception))

    def test_api_mode_with_key_builds_claude_llm(self):
        module, _ = fake_anthropic([])
        with mock.patch.dict(sys.modules, {"anthropic": module}):
            llm = llm_mod.make_llm("api", api_key="sk-test", model="claude-x")
        self.assertIsInstance(llm, llm_mod.ClaudeLLM)
        self.assertEqual(llm.model, "claude-x")


if __name__ == "__main__":
    unittest.main()
