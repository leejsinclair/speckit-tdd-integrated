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


RULES_PATH = ".specify/extensions/integrated-tdd/templates/tdd-process-rules.md"
SCRIPT_PATH = ".specify/extensions/integrated-tdd/scripts/python/tdd_check.py"
# Names no wrapper or addendum may require of a project: test frameworks, CI systems, linters.
TOOL_NAMES = [
    "pytest", "unittest", "jest", "vitest", "mocha", "junit", "rspec", "phpunit", "go test", "cargo test",
    "github actions", "gitlab", "jenkins", "circleci", "eslint", "ruff", "flake8", "pylint", "rubocop",
]  # fmt: skip


def wrapper_parts(stage):
    text = read_repo("preset", "commands", f"speckit.{stage}.md")
    above, _token, below = text.partition("{CORE_TEMPLATE}")
    return text, above, below


class WrapperRules:
    """Rules every wrapper meets. Mixed into a TestCase that sets ``stage`` and ``subcommands``."""

    stage = None
    subcommands = ()
    handles_missing_plan = True

    def test_wrapper_names_the_rules_file_in_full(self):
        _text, above, _below = wrapper_parts(self.stage)
        self.assertIn(RULES_PATH, above)

    def test_wrapper_begins_with_the_missing_extension_check(self):
        _text, above, _below = wrapper_parts(self.stage)
        self.assertIn(SCRIPT_PATH, above)
        self.assertLess(above.index(SCRIPT_PATH), above.index(RULES_PATH))
        self.assertIn("as core Spec Kit", above)
        self.assertIn("does not exist", above)

    def test_wrapper_has_text_above_and_below_the_core_template(self):
        _text, above, below = wrapper_parts(self.stage)
        self.assertGreater(len(above.split()), 40)
        self.assertGreater(len(below.split()), 40)

    def test_wrapper_names_the_subcommands_it_runs(self):
        text, _above, _below = wrapper_parts(self.stage)
        for subcommand in self.subcommands:
            self.assertRegex(text, r"tdd_check\.py " + subcommand + r"\b")

    def test_wrapper_says_what_to_do_without_a_verification_plan(self):
        text, _above, _below = wrapper_parts(self.stage)
        if self.handles_missing_plan:
            self.assertIn("no Verification Plan", text)
            self.assertIn("__SPECKIT_COMMAND_PLAN__", text)

    def test_wrapper_requires_no_particular_tool(self):
        text, _above, _below = wrapper_parts(self.stage)
        for name in TOOL_NAMES + AGENT_NAMES:
            self.assertNotIn(name, text.lower())


class PlanWrapperTests(WrapperRules, unittest.TestCase):
    stage = "plan"
    subcommands = ("plan",)
    handles_missing_plan = False


class TasksWrapperTests(WrapperRules, unittest.TestCase):
    stage = "tasks"
    subcommands = ("tasks",)


class AnalyzeWrapperTests(WrapperRules, unittest.TestCase):
    stage = "analyze"
    subcommands = ("plan", "tasks")


class ImplementWrapperTests(WrapperRules, unittest.TestCase):
    stage = "implement"
    subcommands = ("plan", "tasks", "run", "gate")

    def test_wrapper_says_evidence_is_never_edited_directly(self):
        text, _above, _below = wrapper_parts(self.stage)
        self.assertIn("never edit `tdd-evidence.md`", text.replace("\n", " "))

    def test_wrapper_names_baseline_checkpoint_and_the_end_of_stage_gate(self):
        text, _above, below = wrapper_parts(self.stage)
        self.assertIn("--phase baseline", below)
        self.assertIn("--phase checkpoint", below)
        self.assertIn("gate --task", below)
        self.assertIn("gate --all", below)


class EvidenceTemplateTests(unittest.TestCase):
    HEADINGS = {
        "## Summary": None,
        "## Baseline": "| Seq | Command | Result | Pre-existing failures |",
        "## Test execution records": (
            "| Seq | Time | Task | Obligations | Phase | Command | Selector | Result | Valid | Classification "
            "| Files | Fingerprint | Note | Check |"
        ),
        "## Exceptions": (
            "| ID | Time | Task | Obligations | Kind | Rationale | Alternative verification | Needs approval "
            "| Approved by |"
        ),
        "## Expectation changes": (
            "| ID | Time | Task | Files | Requirements | Justification | Alters behaviour | Approved by "
            "| New fingerprint |"
        ),
        "## Decisions": "| ID | Opened | Question | Tasks | Status | Answer | Decided by | Resolved |",
    }

    def lines(self):
        return read_repo("templates", "tdd-evidence-template.md").splitlines()

    def test_template_holds_the_title_and_the_do_not_edit_comment(self):
        lines = self.lines()
        self.assertEqual(lines[0], "# TDD Evidence: <feature directory name>")
        self.assertIn("<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->", lines)

    def test_template_holds_the_six_sections_in_order(self):
        headings = [line for line in self.lines() if line.startswith("## ")]
        self.assertEqual(headings, list(self.HEADINGS))

    def test_template_holds_the_header_rows_and_no_data_rows(self):
        lines = self.lines()
        for heading, header in self.HEADINGS.items():
            if header is None:
                continue
            self.assertIn(heading, lines)
            start = lines.index(heading) + 1
            table = []
            for line in lines[start:]:
                if line.startswith("## "):
                    break
                if line.startswith("|"):
                    table.append(line)
            self.assertEqual(len(table), 2, heading)
            self.assertEqual(table[0], header, heading)
            self.assertRegex(table[1], r"^\|[-|]+\|$", heading)


class AddendumTests(unittest.TestCase):
    def test_plan_addendum_holds_the_section_as_the_contract_defines_it(self):
        lines = [line.rstrip() for line in read_repo("preset", "templates", "plan-addendum.md").splitlines()]
        for expected in (
            "## Verification Plan",
            "### Verification commands",
            "| ID | Command | Scope | Source |",
            "### Verification obligations",
            "| ID | Requirements | Scenario | Expected outcome | Level | Origin |",
            "### Verification exemptions",
            "| Requirement | Reason | Alternative verification |",
        ):
            self.assertIn(expected, lines)

    def test_plan_addendum_says_the_section_holds_no_status(self):
        self.assertIn("no status", read_repo("preset", "templates", "plan-addendum.md"))

    def test_tasks_addendum_describes_both_labels(self):
        text = read_repo("preset", "templates", "tasks-addendum.md")
        self.assertIn("[VO-nnn]", text)
        self.assertIn("[NT: reason]", text)

    def test_addenda_require_no_particular_tool(self):
        for name in ("plan-addendum.md", "tasks-addendum.md"):
            text = read_repo("preset", "templates", name).lower()
            for tool in TOOL_NAMES + AGENT_NAMES:
                self.assertNotIn(tool, text, name)


if __name__ == "__main__":
    unittest.main()
