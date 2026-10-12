"""The plugin's install must cover what the MCP server's tools import.

    python3.12 -m unittest tests.package.test_install_extras -v

The plugin starts the server with `uvx --from ai-anthropology-toolkit[...]`,
and the suite runs against a development environment that has every extra
installed, so a module missing from the plugin's extras passes every other
test and fails only for the people using the plugin. That happened with nltk:
codebook jobs imported it, and `[data]` did not carry it.

The static check reads every import in the package, including the ones made
inside functions at call time, and requires each third-party module to be a
base dependency or in an extra the plugin's .mcp.json installs. The extras are
read from .mcp.json rather than written here, so changing the plugin's install
target re-checks against the new one. Modules deliberately left out of the
plugin install (sentence-transformers, anthropic) are listed in OPTIONAL and
must fail with a message that names their extra.

Two opt-in tests perform a real install in an isolated environment (network,
and a minute or two):

    AAT_RUN_INSTALL_CHECK=1            the working tree with the plugin's extras
    AAT_RUN_PUBLISHED_INSTALL_CHECK=1  the exact published spec in .mcp.json
"""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "src" / "ai_anthro_toolkit"

# Deliberately not installed by the plugin. Each maps to the extra its
# actionable error names. (anthropic is installed through [api] now; its
# error still names the extra for pip users who left it out.)
OPTIONAL = {"sentence_transformers": "chunking"}

# Import name -> distribution name, where they differ beyond _ and -.
DISTRIBUTION = {"yaml": "pyyaml", "docx": "python-docx", "PIL": "pillow"}


def plugin_spec(path=REPO / "plugins" / "ai-anthropology" / ".mcp.json"):
    """The `--from` requirement the plugin hands to uvx."""
    server = json.loads(path.read_text(encoding="utf-8"))["mcpServers"]["ai-anthropology"]
    args = server["args"]
    return args[args.index("--from") + 1]


def plugin_extras(spec):
    match = re.search(r"\[([^\]]+)\]", spec)
    return [e.strip() for e in match.group(1).split(",")] if match else []


def _requirement_names(lines):
    return {re.split(r"[<>=!~;\[ ]", line, maxsplit=1)[0].strip().lower().replace("_", "-")
            for line in lines}


def installed_requirements(extras):
    """Base dependencies plus the named extras, as normalized names."""
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")

    def array(body):
        return re.findall(r'"([^"]+)"', re.sub(r"#.*", "", body))

    deps = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.M | re.S)
    names = _requirement_names(array(deps.group(1)))
    section = text.split("[project.optional-dependencies]", 1)[1].split("\n[", 1)[0]
    for extra in extras:
        body = re.search(rf"^{re.escape(extra)}\s*=\s*\[(.*?)\]", section, re.M | re.S)
        if body is None:
            raise AssertionError(f"pyproject.toml defines no [{extra}] extra")
        names |= _requirement_names(array(body.group(1)))
    return names


def third_party_imports(root=PACKAGE):
    """{module: [file:line, ...]} for every non-stdlib, non-package import."""
    found = {}
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top in sys.stdlib_module_names or top == "ai_anthro_toolkit":
                    continue
                found.setdefault(top, []).append(
                    f"{path.relative_to(root.parent)}:{node.lineno}")
    return found


def uncovered(imports, requirements):
    return sorted(m for m in imports
                  if m not in OPTIONAL
                  and DISTRIBUTION.get(m, m).lower().replace("_", "-") not in requirements)


class TestPluginExtrasCoverToolImports(unittest.TestCase):
    def test_plugin_spec_is_read_from_mcp_json(self):
        spec = plugin_spec()
        self.assertTrue(spec.startswith("ai-anthropology-toolkit["), spec)
        self.assertEqual(plugin_spec(REPO / ".mcp.json"), spec)
        self.assertIn("data", plugin_extras(spec))
        self.assertIn("api", plugin_extras(spec))

    def test_every_tool_import_is_installed_by_the_plugin(self):
        imports = third_party_imports()
        requirements = installed_requirements(plugin_extras(plugin_spec()))
        missing = uncovered(imports, requirements)
        self.assertEqual(missing, [], "imported by the package but not installed by "
                         f"the plugin ({plugin_spec()}): "
                         + "; ".join(f"{m} at {imports[m][0]}" for m in missing))

    def test_the_tripwire_fires_on_a_module_the_plugin_lacks(self):
        imports = {"nltk": ["codebook.py:183"], "gnews": ["googlenews.py:62"]}
        self.assertEqual(uncovered(imports, {"gnews"}), ["nltk"])

    def test_optional_modules_are_really_optional(self):
        requirements = installed_requirements(plugin_extras(plugin_spec()))
        for module, extra in OPTIONAL.items():
            with self.subTest(module=module):
                self.assertNotIn(module.replace("_", "-"), requirements)
                self.assertIn(module.replace("_", "-"),
                              installed_requirements([extra]))


class TestOptionalModulesFailWithTheirExtra(unittest.TestCase):
    """Each OPTIONAL module, absent, yields an error naming its extra."""

    def assert_names_extra(self, ctx, extra):
        message = str(ctx.exception)
        self.assertIn(f"ai-anthropology-toolkit[{extra}]", message)
        self.assertIn(".mcp.json", message)

    def test_codebook_refinement_without_sentence_transformers(self):
        from ai_anthro_toolkit import codebook

        with mock.patch.dict(sys.modules, {"sentence_transformers": None}), \
                mock.patch.object(codebook, "_embedding_model", None):
            with self.assertRaises(ImportError) as ctx:
                codebook._default_embedder(["a", "b"])
        self.assert_names_extra(ctx, "chunking")

    def test_codebook_jobs_fall_back_instead_of_failing(self):
        # Refinement no longer needs sentence-transformers: without it a job
        # completes on the lexical fallback and says so (covered in
        # test_lexical_similarity). Only a direct call to the embedder
        # still names the extra, as tested above.
        from ai_anthro_toolkit import codebook

        with mock.patch.dict(sys.modules, {"sentence_transformers": None}):
            self.assertFalse(codebook._sentence_transformers_installed())

    def test_chunk_transcript_without_sentence_transformers(self):
        from ai_anthro_toolkit import chunking

        with mock.patch.dict(sys.modules, {"sentence_transformers": None}), \
                mock.patch.object(chunking, "_default_embedder", None):
            with self.assertRaises(ImportError) as ctx:
                chunking._get_default_embedder()
        self.assert_names_extra(ctx, "chunking")

    def test_api_mode_without_anthropic(self):
        from ai_anthro_toolkit import llm

        with mock.patch.dict(sys.modules, {"anthropic": None}):
            with self.assertRaises(ImportError) as ctx:
                llm.ClaudeLLM(api_key="sk-test")
        self.assert_names_extra(ctx, "api")

    def test_standing_checks_report_cannot_tell_instead_of_failing(self):
        from ai_anthro_toolkit.checks import cli

        with mock.patch.dict(sys.modules, {"sentence_transformers": None}):
            self.assertIsNone(cli._embedder())


# Imports every data-source library the tools load at call time, then runs
# the nltk path that failed for plugin users, and confirms the optional
# embedder fails with its extra rather than a bare ModuleNotFoundError.
PROBE = """
import gnews, pytrends.request, scholarly, scrapetube, youtube_transcript_api, feedparser, nltk
import anthropic
from ai_anthro_toolkit.mcp import server
from ai_anthro_toolkit.codebook import chunk_text, _default_embedder
assert chunk_text("Members pool money. The clinic closed.")
try:
    _default_embedder(["a"])
except ImportError as e:
    assert "[chunking]" in str(e), e
print("probe ok")
"""


def _isolated_run(requirement):
    uv = shutil.which("uv")
    if uv is None:
        raise unittest.SkipTest("uv is not installed")
    return subprocess.run(
        [uv, "run", "--no-project", "--isolated", "--with", requirement,
         "python", "-c", PROBE],
        capture_output=True, text=True, timeout=900, cwd="/")


@unittest.skipUnless(os.environ.get("AAT_RUN_INSTALL_CHECK") == "1",
                     "network install; set AAT_RUN_INSTALL_CHECK=1")
class TestWorkingTreeInstall(unittest.TestCase):
    def test_working_tree_with_the_plugin_extras_runs_the_tools(self):
        extras = ",".join(plugin_extras(plugin_spec()))
        result = _isolated_run(f"ai-anthropology-toolkit[{extras}] @ {REPO.as_uri()}")
        self.assertEqual(result.returncode, 0, result.stderr[-3000:])
        self.assertIn("probe ok", result.stdout)


@unittest.skipUnless(os.environ.get("AAT_RUN_PUBLISHED_INSTALL_CHECK") == "1",
                     "network install of the published package; "
                     "set AAT_RUN_PUBLISHED_INSTALL_CHECK=1")
class TestPublishedPluginInstall(unittest.TestCase):
    def test_the_exact_plugin_spec_runs_the_tools(self):
        result = _isolated_run(plugin_spec())
        self.assertEqual(result.returncode, 0, result.stderr[-3000:])
        self.assertIn("probe ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
