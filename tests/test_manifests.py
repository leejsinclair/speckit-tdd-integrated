"""Structural validation of the extension and preset packages.

The manifests are read with regular expressions because the standard library
has no YAML parser. Loading by Spec Kit itself is proved by the installation
tests recorded in specs/001-integrated-tdd/research.md.
"""

import os
import re
import unittest

from support import REPO, load_script

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
        self.assertEqual(len(entries), 4)
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


CHECKLIST_TEMPLATE = os.path.join("templates", "behaviour-checklist-template.md")
CHECKLIST_TEMPLATE_PATH = ".specify/extensions/integrated-tdd/templates/behaviour-checklist-template.md"
CHECKLIST_LINK_LINE = "Behaviour items are in [tests/behaviour-checklist.md](tests/behaviour-checklist.md)."


def flat(text):
    """Text with every run of white space made one space, so a phrase can span a line break."""
    return " ".join(text.split())


class BehaviourChecklistTemplateTests(unittest.TestCase):
    def test_extension_provides_the_template(self):
        provides = top_level_block(read_repo("extension.yml"), "provides")
        self.assertRegex(provides, r'(?m)^\s+- name:\s*"behaviour-checklist-template"\s*$')
        self.assertIn('file: "templates/behaviour-checklist-template.md"', provides)
        self.assertTrue(os.path.isfile(repo_path(CHECKLIST_TEMPLATE)))

    def test_template_entry_follows_the_evidence_template_and_is_described(self):
        text = read_repo("extension.yml")
        self.assertLess(text.index('name: "tdd-evidence-template"'), text.index('name: "behaviour-checklist-template"'))
        self.assertIn('description: "Starting content of a feature\'s tests/behaviour-checklist.md"', text)

    def test_template_parses_into_one_scenario_section_and_one_other_section(self):
        result = load_script().parse_checklist(read_repo(CHECKLIST_TEMPLATE))
        self.assertEqual(result.findings, [])
        self.assertEqual([section.kind for section in result.sections], ["scenario", "other"])
        self.assertGreaterEqual(len(result.items), 2)

    def test_template_holds_the_title_placeholder_and_the_explanatory_comment(self):
        text = read_repo(CHECKLIST_TEMPLATE)
        self.assertEqual(text.splitlines()[0], "# Behaviour Checklist: <feature directory name>")
        comment = flat(text[text.index("<!--") : text.index("-->")])
        for phrase in (
            "Written by the plan stage",
            "Read by tdd_check.py",
            'One "## USn-ASm" section per acceptance scenario',
            "word for word",
            'One "## Other behaviours" section',
            "They name no file, module, function, class, table, endpoint or screen component",
            "No checkboxes and no status",
        ):
            self.assertIn(phrase, comment)

    def test_template_links_the_three_documents(self):
        text = read_repo(CHECKLIST_TEMPLATE)
        for link in ("[spec.md](../spec.md)", "[plan.md](../plan.md#verification-plan)", "[tasks.md](../tasks.md)"):
            self.assertIn(link, text)


class BehaviourChecklistAddendumTests(unittest.TestCase):
    def lines(self):
        return [line.rstrip() for line in read_repo("preset", "templates", "plan-addendum.md").splitlines()]

    def test_sub_heading_follows_the_exemptions_and_precedes_any_second_level_heading(self):
        lines = self.lines()
        self.assertIn("### Behaviour checklist", lines)
        position = lines.index("### Behaviour checklist")
        self.assertGreater(position, lines.index("### Verification exemptions"))
        self.assertEqual([line for line in lines[position:] if line.startswith("## ")], [])
        self.assertEqual(lines.count("### Behaviour checklist"), 1)

    def test_sub_heading_is_followed_by_the_fixed_link_line(self):
        text = read_repo("preset", "templates", "plan-addendum.md")
        after = text.split("### Behaviour checklist", 1)[1]
        self.assertIn(CHECKLIST_LINK_LINE, after)
        self.assertIn("must be kept", flat(after))


class BehaviourChecklistPlanWrapperTests(unittest.TestCase):
    def step(self):
        _text, _above, below = wrapper_parts("plan")
        heading = re.search(r"(?m)^\d+\. \*\*Behaviour checklist\*\*", below)
        self.assertIsNotNone(heading, "no Behaviour checklist step")
        return flat(below[heading.start() :])

    def test_step_follows_the_verification_plan_steps_and_precedes_the_check(self):
        _text, _above, below = wrapper_parts("plan")
        self.assertLess(below.index("**Verification exemptions**"), below.index("**Behaviour checklist**"))
        self.assertLess(below.index("**Behaviour checklist**"), below.index("**Check**"))

    def test_step_names_the_template_and_where_the_checklist_goes(self):
        step = self.step()
        self.assertIn(CHECKLIST_TEMPLATE_PATH, step)
        self.assertIn("tests/behaviour-checklist.md", step)
        self.assertIn("FEATURE_DIR", step)

    def test_step_adds_the_sub_heading_when_the_plan_lacks_it(self):
        step = self.step()
        self.assertIn("### Behaviour checklist", step)
        self.assertRegex(step, r"has no `### Behaviour checklist` sub-heading")

    def test_step_follows_the_process_rules_section(self):
        self.assertIn('"Behaviour checklist" in the process rules', self.step())

    def test_the_check_is_the_plan_check_and_covers_the_checklist(self):
        _text, _above, below = wrapper_parts("plan")
        check = flat(below[below.index("**Check**") :])
        self.assertRegex(check, r"tdd_check\.py plan")
        self.assertIn("checklist", check)

    def test_the_note_at_the_top_names_the_checklist_as_a_phase_1_output(self):
        _text, above, _below = wrapper_parts("plan")
        note = flat(above)
        self.assertIn("behaviour checklist", note.lower())
        self.assertIn("Phase 1 output", note)

    def test_completion_report_names_the_location_and_asks_for_review_without_approval(self):
        _text, _above, below = wrapper_parts("plan")
        report = flat(below[below.rindex("In the Completion Report") :]).lower()
        self.assertIn("tests/behaviour-checklist.md", report)
        self.assertIn("number of sections and items", report)
        self.assertIn("ask for the checklist to be reviewed against the specification", report)
        self.assertIn("no approval is requested", report)
        self.assertIn("nothing waits for one", report)


class BehaviourChecklistRulesTests(unittest.TestCase):
    def headings(self):
        return [line for line in read_repo(RULES_FILE).splitlines() if line.startswith("## ")]

    def section(self):
        text = read_repo(RULES_FILE)
        start = text.index("\n## Behaviour checklist\n")
        end = text.index("\n## The Red, Green, Refactor cycle")
        return flat(text[start:end])

    def test_section_sits_between_verification_intent_and_the_cycle(self):
        headings = self.headings()
        self.assertIn("## Behaviour checklist", headings)
        position = headings.index("## Behaviour checklist")
        self.assertEqual(headings[position - 1], "## Verification intent")
        self.assertEqual(headings[position + 1], "## The Red, Green, Refactor cycle")

    def test_section_says_when_where_and_what(self):
        section = self.section()
        for phrase in (
            "plan stage",
            "tests/behaviour-checklist.md",
            "never in `checklists/`",
            "one section per acceptance scenario",
            "word for word",
            "Other behaviours",
            "Given, When, Then",
            "no checkbox",
            "no status",
        ):
            self.assertIn(phrase, section)

    def test_rules_name_both_evidence_locations_and_which_features_use_each(self):
        text = flat(read_repo(RULES_FILE))
        self.assertIn("`tdd-evidence.md`", text)
        self.assertIn("`tests/tdd-evidence.md`", text)
        self.assertIn("planned before", text)


if __name__ == "__main__":
    unittest.main()
