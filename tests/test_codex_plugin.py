"""Structural and drift tests for the repo-local Codex plugin.

These tests deliberately check both directions of each invariant. Inventory
parity alone cannot detect content drift, and documentation coverage alone
cannot detect a skill that names a tool the server never registered.
"""

import ast
import json
import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
SOURCE_SKILLS = REPO / "skills"
PLUGIN = REPO / "plugins" / "ai-anthropology"
PLUGIN_SKILLS = PLUGIN / "skills"
ENTRY_SKILL = "ai-anthropology"
SERVER = REPO / "src" / "ai_anthro_toolkit" / "mcp" / "server.py"
TOOL_REFERENCE = (
    PLUGIN_SKILLS / ENTRY_SKILL / "references" / "tool-reference.md"
)

TOOL_LIKE = re.compile(
    r"^((?:toolkit|search|get|list|format|chunk|extract|start|ratify|"
    r"submit|build|compare|view|export|analyze)_[a-z0-9_]+)$"
)

# Snake-case identifiers that share a registered tool's verb prefix but are
# data fields, not callable surface. Keep this list small and explain every
# exception; an unexplained exclusion would recreate the blind spot this test
# exists to prevent.
NON_TOOL_IDENTIFIERS = {
    "chunk_id": "identifier field on a transcript chunk record",
    "mcp__": "documented namespace prefix, not a callable tool name",
}


def _skill_dirs(root):
    return {
        path.name: path
        for path in root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def _registered_tools():
    """Derive MCP tool names from source decorators, not a prose count."""
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))
    names = set()
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "tool"
                and isinstance(func.value, ast.Name)
                and func.value.id == "mcp"
            ):
                continue
            explicit = None
            for keyword in decorator.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    explicit = keyword.value.value
            names.add(explicit or node.name)
    return names


def _documented_tool_like_names():
    names = set()
    for path in PLUGIN_SKILLS.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for name in re.findall(r"`([a-z][a-z0-9_]+)`", text):
            if TOOL_LIKE.fullmatch(name) and name not in NON_TOOL_IDENTIFIERS:
                names.add(name)
        # A newly invented verb would evade the known-prefix heuristic above.
        # Treat an underscored identifier explicitly presented as a callable
        # as a tool regardless of its prefix.
        for name in re.findall(
            r"\b(?:call|invoke|run|use|with)\s+`([a-z][a-z0-9_]*_[a-z0-9_]+)`",
            text,
            flags=re.IGNORECASE,
        ):
            if name not in NON_TOOL_IDENTIFIERS:
                names.add(name)
    return names


class TestCodexPluginStructure(unittest.TestCase):
    def test_manifest_and_marketplace_resolve(self):
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "ai-anthropology")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["mcpServers"], "./.mcp.json")
        self.assertTrue((PLUGIN / manifest["skills"]).is_dir())
        self.assertTrue((PLUGIN / manifest["mcpServers"]).is_file())

        marketplace_path = REPO / ".agents" / "plugins" / "marketplace.json"
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        entries = {entry["name"]: entry for entry in marketplace["plugins"]}
        entry = entries["ai-anthropology"]
        self.assertEqual(entry["source"]["path"], "./plugins/ai-anthropology")
        self.assertTrue((REPO / entry["source"]["path"]).is_dir())
        self.assertIn("installation", entry["policy"])
        self.assertIn("authentication", entry["policy"])
        self.assertIn("category", entry)

    def test_mcp_config_is_byte_identical_to_the_release_pin(self):
        self.assertEqual(
            (PLUGIN / ".mcp.json").read_bytes(),
            (REPO / ".mcp.json").read_bytes(),
            "the plugin MCP command drifted from the repository release pin",
        )


class TestCodexSkillParity(unittest.TestCase):
    def test_inventory_is_source_skills_plus_one_classified_entry_skill(self):
        source = set(_skill_dirs(SOURCE_SKILLS))
        plugin = set(_skill_dirs(PLUGIN_SKILLS))
        self.assertEqual(plugin - source, {ENTRY_SKILL})
        self.assertEqual(source - plugin, set())

    def test_every_mirrored_skill_is_byte_identical(self):
        for name, source_dir in _skill_dirs(SOURCE_SKILLS).items():
            plugin_dir = PLUGIN_SKILLS / name
            source_files = {
                path.relative_to(source_dir): path
                for path in source_dir.rglob("*") if path.is_file()
            }
            plugin_files = {
                path.relative_to(plugin_dir): path
                for path in plugin_dir.rglob("*") if path.is_file()
            }
            with self.subTest(skill=name, check="inventory"):
                self.assertEqual(set(source_files), set(plugin_files))
            for relative, source_path in source_files.items():
                with self.subTest(skill=name, file=str(relative)):
                    self.assertEqual(
                        source_path.read_bytes(),
                        plugin_files[relative].read_bytes(),
                        f"{name}/{relative} drifted; classify an intentional "
                        "adaptation instead of weakening parity",
                    )


class TestCodexToolDocumentation(unittest.TestCase):
    def test_tool_reference_documents_every_registered_tool(self):
        registered = _registered_tools()
        reference = set(
            name for name in re.findall(
                r"`([a-z][a-z0-9_]+)`",
                TOOL_REFERENCE.read_text(encoding="utf-8"),
            )
            if TOOL_LIKE.fullmatch(name)
        )
        self.assertEqual(registered - reference, set(),
                         "registered MCP tools missing from the plugin reference")
        self.assertEqual(reference - registered, set(),
                         "plugin reference names MCP tools that do not exist")

    def test_no_plugin_skill_names_a_tool_that_does_not_exist(self):
        registered = _registered_tools()
        documented = _documented_tool_like_names()
        self.assertEqual(
            documented - registered,
            set(),
            "a plugin skill names a phantom MCP tool",
        )


if __name__ == "__main__":
    unittest.main()
