"""Structural validation of the extension and preset packages.

The manifests are read with regular expressions because the standard library
has no YAML parser. Loading by Spec Kit itself is proved by the installation
tests recorded in specs/001-integrated-tdd/research.md.
"""

import os
import re
import unittest

from support import REPO

GATE_COMMAND = "speckit.integrated-tdd.gate"
RULES_FILE = os.path.join("templates", "tdd-process-rules.md")
IGNORED_PATHS = [
    "preset/",
    "preset.yml",
    "tests/",
    "examples/",
    "docs/",
    "specs/",
    "stories/",
    ".specify/",
    ".claude/",
]
AGENT_NAMES = ["claude", "copilot", "cursor", "gemini", "codex", "windsurf"]


def repo_path(*parts):
    return os.path.join(REPO, *parts)


def read_repo(*parts):
    path = repo_path(*parts)
    if not os.path.isfile(path):
        raise AssertionError("missing file: " + os.path.join(*parts))
    with open(path) as handle:
        return handle.read()


def file_entries(manifest_text):
    return re.findall(r'^\s*file:\s*"?([^"\n]+?)"?\s*$', manifest_text, re.MULTILINE)


def version_of(manifest_text):
    found = re.search(r'^\s+version:\s*"([^"]+)"', manifest_text, re.MULTILINE)
    return found.group(1) if found else None


def top_level_block(manifest_text, key):
    """Return the indented lines under a top-level ``key:``, or None."""
    found = re.search(r"^" + re.escape(key) + r":\s*\n((?:[ \t]+.*\n|\s*\n)*)", manifest_text, re.MULTILINE)
    return found.group(1) if found else None


def frontmatter(text):
    found = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    return found.group(1) if found else None


class ExtensionManifestTests(unittest.TestCase):
    def test_extension_manifest_exists(self):
        self.assertIn('id: "integrated-tdd"', read_repo("extension.yml"))

    def test_every_extension_file_exists(self):
        entries = file_entries(read_repo("extension.yml"))
        self.assertEqual(len(entries), 3)
        for entry in entries:
            self.assertTrue(os.path.isfile(repo_path(entry)), "missing file: " + entry)

    def test_extension_registers_no_command(self):
        provides = top_level_block(read_repo("extension.yml"), "provides")
        self.assertIsNotNone(provides)
        self.assertIsNone(re.search(r"^\s+commands:", provides, re.MULTILINE))

    def test_extension_has_no_lifecycle_hooks(self):
        self.assertIsNone(re.search(r"^hooks:", read_repo("extension.yml"), re.MULTILINE))

    def test_pre_tool_use_event_is_declared(self):
        events = top_level_block(read_repo("extension.yml"), "events")
        self.assertIsNotNone(events, "no events: block")
        self.assertRegex(events, r"(?m)^  pre_tool_use:\s*$")
        self.assertRegex(events, r'(?m)^    command:\s*"' + re.escape(GATE_COMMAND) + r'"\s*$')
        self.assertRegex(events, r'(?m)^    matcher:\s*"Edit\|Write\|MultiEdit"\s*$')
        self.assertRegex(events, r"(?m)^    timeout:\s*30\s*$")

    def test_gate_command_file_declares_only_the_python_hook(self):
        front = frontmatter(read_repo("commands", GATE_COMMAND + ".md"))
        self.assertIsNotNone(front, "no frontmatter")
        found = re.search(r"^scripts:\s*\n((?:[ \t]+.*\n?)*)", front, re.MULTILINE)
        self.assertIsNotNone(found, "no scripts: block")
        entries = [line.strip() for line in found.group(1).splitlines() if line.strip()]
        self.assertEqual(entries, ["py: scripts/python/tdd_check.py hook"])

    def test_extensionignore_lists_every_contract_path(self):
        lines = [line.strip() for line in read_repo(".extensionignore").splitlines()]
        for path in IGNORED_PATHS:
            self.assertIn(path, lines)


class PresetManifestTests(unittest.TestCase):
    def test_preset_manifest_exists(self):
        self.assertIn('id: "integrated-tdd"', read_repo("preset.yml"))

    def test_every_preset_file_exists(self):
        entries = file_entries(read_repo("preset.yml"))
        self.assertEqual(len(entries), 6)
        for entry in entries:
            self.assertTrue(os.path.isfile(repo_path(entry)), "missing file: " + entry)

    def test_both_manifests_carry_the_same_version(self):
        extension = version_of(read_repo("extension.yml"))
        preset = version_of(read_repo("preset.yml"))
        self.assertIsNotNone(extension)
        self.assertEqual(extension, preset)

    def test_every_wrapper_contains_the_core_template_once(self):
        folder = repo_path("preset", "commands")
        found = os.listdir(folder) if os.path.isdir(folder) else []
        names = sorted(name for name in found if name.endswith(".md"))
        self.assertEqual(
            names,
            ["speckit.analyze.md", "speckit.implement.md", "speckit.plan.md", "speckit.tasks.md"],
        )
        for name in names:
            text = read_repo("preset", "commands", name)
            self.assertEqual(text.count("{CORE_TEMPLATE}"), 1, name)


class ProcessRulesTests(unittest.TestCase):
    def test_rules_file_exists_and_names_no_coding_agent(self):
        text = read_repo(RULES_FILE).lower()
        for name in AGENT_NAMES:
            self.assertNotIn(name, text)


if __name__ == "__main__":
    unittest.main()
