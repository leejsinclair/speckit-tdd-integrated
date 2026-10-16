"""The artefact parser (contracts/artefact-formats.md).

Malformed input is reported as findings and never raises.
"""

import unittest

from support import fixture_text, load_script


def parser_function(name):
    module = load_script()
    function = getattr(module, name, None)
    if function is None:
        raise AssertionError("the check script has no parser function " + name)
    return function


def parse(name, case, filename):
    return parser_function(name)(fixture_text(case, filename))


def reasons(findings):
    return [str(finding) for finding in findings]


class TableTests(unittest.TestCase):
    TEXT = (
        "## Things\n\nSome prose.\n\n"
        "|  ID | Name  |\n|-----|-------|\n|  a  |  one, two ,three |\n| b | - |\n| c | `x | y` |\n\n"
        "After.\n\n## Other\n\n| ID | Name |\n|----|------|\n| z | last |\n"
    )

    def test_table_is_found_by_heading_then_header_row(self):
        rows, problem = parser_function("find_table")(self.TEXT, "## Things", ["ID", "Name"])
        self.assertIsNone(problem)
        self.assertEqual([row[0] for row in rows], ["a", "b", "c"])

    def test_cells_are_trimmed(self):
        rows, _problem = parser_function("find_table")(self.TEXT, "## Things", ["ID", "Name"])
        self.assertEqual(rows[0], ["a", "one, two ,three"])

    def test_a_bar_inside_backticks_does_not_split_the_cell(self):
        rows, _problem = parser_function("find_table")(self.TEXT, "## Things", ["ID", "Name"])
        self.assertEqual(rows[2], ["c", "`x | y`"])

    def test_comma_lists_split_and_a_lone_dash_is_empty(self):
        split_list = parser_function("split_list")
        self.assertEqual(split_list("one, two ,three"), ["one", "two", "three"])
        self.assertEqual(split_list("-"), [])
        self.assertEqual(split_list(""), [])

    def test_missing_heading_is_a_problem_not_an_error(self):
        rows, problem = parser_function("find_table")(self.TEXT, "## Absent", ["ID", "Name"])
        self.assertIsNone(rows)
        self.assertIn("## Absent", problem)

    def test_wrong_header_row_is_a_problem(self):
        rows, problem = parser_function("find_table")(self.TEXT, "## Things", ["ID", "Title"])
        self.assertIsNone(rows)
        self.assertIn("header row", problem)

    def test_a_table_under_a_later_heading_is_not_taken(self):
        text = "## Things\n\nNo table here.\n\n## Other\n\n| ID | Name |\n|----|------|\n| z | last |\n"
        rows, problem = parser_function("find_table")(text, "## Things", ["ID", "Name"])
        self.assertIsNone(rows)
        self.assertIn("no table", problem)


class SpecTests(unittest.TestCase):
    def test_requirement_ids_are_collected(self):
        spec = parse("parse_spec", "valid-minimal", "spec.md")
        self.assertEqual(spec.fr_ids, ["FR-001", "FR-002", "FR-003"])
        self.assertEqual(spec.sc_ids, ["SC-001"])

    def test_scenario_ids_are_derived_from_story_and_position(self):
        spec = parse("parse_spec", "valid-minimal", "spec.md")
        self.assertEqual(spec.scenario_ids, ["US1-AS1", "US1-AS2"])

    def test_scenarios_of_several_stories(self):
        text = (
            "### User Story 1 - First (Priority: P1)\n\n**Acceptance Scenarios**:\n\n"
            "1. **Given** a, **When** b, **Then** c.\n1. **Given** d, **When** e, **Then** f.\n\n---\n\n"
            "### User Story 2 - Second (Priority: P2)\n\nProse with 1. a number.\n\n"
            "**Acceptance Scenarios**:\n\n1. **Given** g, **When** h, **Then** i.\n\n"
            "### Edge Cases\n\n1. Not a scenario.\n"
        )
        spec = parser_function("parse_spec")(text)
        self.assertEqual(spec.scenario_ids, ["US1-AS1", "US1-AS2", "US2-AS1"])

    def test_an_id_only_mentioned_in_prose_is_not_a_requirement(self):
        text = "- **FR-001**: The system MUST do a thing, as FR-009 once said.\n"
        self.assertEqual(parser_function("parse_spec")(text).fr_ids, ["FR-001"])


class PlanTests(unittest.TestCase):
    def test_commands_are_read(self):
        plan = parse("parse_plan", "valid-minimal", "plan.md")
        self.assertTrue(plan.has_section)
        self.assertEqual(plan.findings, [])
        self.assertEqual([command.id for command in plan.commands], ["unit", "suite"])
        unit = plan.commands[0]
        self.assertEqual(unit.command, "sh tests/fixtures/bin/fake_test.sh {select}")
        self.assertEqual(unit.scope, "focused")
        self.assertEqual(unit.source, "tests/fixtures/bin")
        self.assertEqual(plan.commands[1].scope, "broad")

    def test_obligations_are_read(self):
        plan = parse("parse_plan", "valid-minimal", "plan.md")
        self.assertEqual([item.id for item in plan.obligations], ["VO-001", "VO-002"])
        second = plan.obligations[1]
        self.assertEqual(second.requirements, ["FR-002", "US1-AS2", "SC-001", "DC-01", "EC-01"])
        self.assertEqual(second.scenario, "A cart with a zero-priced item is totalled through the public interface")
        self.assertEqual(second.outcome, "The total is the sum of the prices")
        self.assertEqual(second.level, "integration")
        self.assertEqual(second.origin, "planned")

    def test_exemptions_are_read(self):
        plan = parse("parse_plan", "valid-minimal", "plan.md")
        self.assertEqual(len(plan.exemptions), 1)
        exemption = plan.exemptions[0]
        self.assertEqual(exemption.requirement, "FR-003")
        self.assertIn("Visual layout", exemption.reason)
        self.assertIn("code review", exemption.alternative)

    def test_a_none_row_means_no_exemptions(self):
        plan = parse("parse_plan", "parse-no-exemptions", "plan.md")
        self.assertEqual(plan.exemptions, [])
        self.assertEqual(plan.findings, [])

    def test_missing_section_is_a_finding(self):
        plan = parse("parse_plan", "parse-no-section", "plan.md")
        self.assertFalse(plan.has_section)
        self.assertEqual(plan.commands, [])
        self.assertEqual(len(plan.findings), 1)
        self.assertIn("no Verification Plan section", str(plan.findings[0]))

    def test_wrong_header_row_is_a_finding(self):
        plan = parse("parse_plan", "parse-wrong-header", "plan.md")
        self.assertTrue(plan.has_section)
        self.assertEqual(plan.commands, [])
        found = reasons(plan.findings)
        self.assertEqual(len(found), 1)
        self.assertIn("### Verification commands", found[0])
        self.assertIn("header row", found[0])
        self.assertEqual(len(plan.obligations), 2)

    def test_out_of_range_enums_are_findings(self):
        plan = parse("parse_plan", "parse-bad-enum", "plan.md")
        found = "\n".join(reasons(plan.findings))
        self.assertIn("unit: scope 'wide' is not one of focused, broad", found)
        self.assertIn("VO-001: level 'smoke' is not one of unit, integration, contract, end-to-end, other", found)
        self.assertIn("VO-002: origin 'guessed' is not one of planned, discovered", found)
        self.assertEqual(len(plan.findings), 3)

    def test_id_and_command_rules_are_findings(self):
        plan = parse("parse_plan", "parse-bad-ids", "plan.md")
        found = "\n".join(reasons(plan.findings))
        self.assertIn("Unit_1: command id must be lowercase letters, digits and hyphens", found)
        self.assertIn("suite: command holds more than one {select}", found)
        self.assertIn("VO-001: obligation id is used more than once", found)
        self.assertIn("VO-3: obligation id must be VO- and three or more digits", found)

    def test_a_command_outside_backticks_is_a_finding(self):
        plan = parse("parse_plan", "parse-unquoted-command", "plan.md")
        self.assertIn("suite: command must be written in backticks", "\n".join(reasons(plan.findings)))

    def test_findings_use_the_plan_rule_id(self):
        plan = parse("parse_plan", "parse-bad-enum", "plan.md")
        self.assertTrue(all(str(finding).startswith("PLAN ") for finding in plan.findings))


class TaskTests(unittest.TestCase):
    def tasks(self):
        return {task.id: task for task in parse("parse_tasks", "parse-task-labels", "tasks.md")}

    def test_task_lines_yield_id_and_order(self):
        tasks = parse("parse_tasks", "parse-task-labels", "tasks.md")
        self.assertEqual([task.id for task in tasks], [f"T00{n}" for n in range(1, 9)])

    def test_checkbox_states(self):
        tasks = self.tasks()
        self.assertFalse(tasks["T001"].complete)
        self.assertTrue(tasks["T002"].complete)
        self.assertTrue(tasks["T003"].complete)

    def test_labels_are_read_from_the_run_before_the_description(self):
        tasks = self.tasks()
        self.assertEqual(tasks["T002"].obligations, ["VO-001", "VO-002"])
        self.assertEqual(tasks["T008"].obligations, ["VO-001"])
        self.assertEqual(tasks["T007"].no_test_reason, "configuration with no observable effect")
        self.assertEqual(tasks["T007"].obligations, [])

    def test_kind_follows_labels_and_position(self):
        tasks = self.tasks()
        self.assertIsNone(tasks["T001"].kind)
        self.assertEqual(tasks["T002"].kind, "test")
        self.assertEqual(tasks["T003"].kind, "behaviour")
        self.assertEqual(tasks["T005"].kind, "behaviour")
        self.assertEqual(tasks["T007"].kind, "no-test")
        self.assertEqual(tasks["T008"].kind, "behaviour")

    def test_several_obligations_first_to_name_only_some_is_behaviour(self):
        self.assertEqual(self.tasks()["T004"].kind, "behaviour")

    def test_an_empty_no_test_reason_is_no_label(self):
        task = self.tasks()["T006"]
        self.assertIsNone(task.kind)
        self.assertEqual(task.no_test_reason, "")

    def test_task_lines_inside_a_fenced_code_block_are_not_tasks(self):
        text = (
            "- [ ] T001 [NT: setup] Real task\n\n## Verification labels\n\n"
            "```markdown\n- [ ] T011 [VO-001] An example line in the conventions\n```\n\n"
            "~~~\n- [X] T012 [VO-001] Another example\n~~~\n\n- [ ] T002 [NT: docs] Real task after the block\n"
        )
        tasks = parser_function("parse_tasks")(text)
        self.assertEqual([task.id for task in tasks], ["T001", "T002"])

    def test_valid_minimal_kinds(self):
        tasks = parse("parse_tasks", "valid-minimal", "tasks.md")
        self.assertEqual(
            [(task.id, task.kind) for task in tasks],
            [("T011", "test"), ("T012", "behaviour"), ("T013", "test"), ("T014", "behaviour"), ("T015", "no-test")],
        )


class EvidenceTests(unittest.TestCase):
    def test_records_are_read(self):
        evidence = parse("parse_evidence", "valid-minimal", "tdd-evidence.md")
        self.assertEqual(evidence.findings, [])
        self.assertEqual([record.seq for record in evidence.records], [1, 2, 3])
        red = evidence.records[1]
        self.assertEqual(red.task, "T011")
        self.assertEqual(red.obligations, ["VO-001"])
        self.assertEqual(red.phase, "red")
        self.assertEqual(red.command, "unit")
        self.assertEqual(red.selector, "assert")
        self.assertEqual(red.result, "fail")
        self.assertTrue(red.valid)
        self.assertEqual(red.classification, "assertion")
        self.assertEqual(red.files, ["tests/test_cart.py"])
        self.assertEqual(len(red.fingerprint), 6)
        self.assertEqual(red.note, "expected: AssertionError")
        self.assertEqual(len(red.check), 6)

    def test_empty_cells_are_empty_values(self):
        first = parse("parse_evidence", "valid-minimal", "tdd-evidence.md").records[0]
        self.assertEqual(first.task, "")
        self.assertEqual(first.obligations, [])
        self.assertEqual(first.selector, "")
        self.assertEqual(first.classification, "")
        self.assertEqual(first.files, [])
        self.assertEqual(first.fingerprint, "")
        self.assertEqual(first.note, "")

    def test_every_evidence_table_is_read(self):
        evidence = parse("parse_evidence", "parse-evidence-full", "tdd-evidence.md")
        self.assertEqual(evidence.findings, [])
        self.assertEqual(len(evidence.records), 4)
        self.assertFalse(evidence.records[3].valid)
        self.assertEqual(len(evidence.baseline), 1)
        exception = evidence.exceptions[0]
        self.assertEqual(
            (exception.id, exception.task, exception.obligations, exception.kind),
            ("EX-01", "T013", ["VO-002"], "legacy"),
        )
        self.assertTrue(exception.needs_approval)
        self.assertEqual(exception.approved_by, "Lee Sinclair")
        self.assertEqual(exception.alternative, "Existing suite run before and after")
        change = evidence.expectations[0]
        self.assertEqual((change.id, change.task, change.requirements), ("XC-01", "T012", ["FR-001", "US1-AS1"]))
        self.assertTrue(change.alters_behaviour)
        self.assertEqual(len(change.new_fingerprint), 6)
        self.assertEqual([item.id for item in evidence.decisions], ["DN-01", "DN-02"])
        self.assertEqual(evidence.decisions[0].tasks, ["T013", "T014"])
        self.assertEqual(evidence.decisions[0].status, "open")
        self.assertEqual(evidence.decisions[1].decided_by, "Lee")

    def test_wrong_header_row_is_a_finding(self):
        evidence = parse("parse_evidence", "parse-evidence-wrong-header", "tdd-evidence.md")
        self.assertEqual(evidence.records, [])
        found = reasons(evidence.findings)
        self.assertEqual(len(found), 1)
        self.assertIn("## Test execution records", found[0])
        self.assertTrue(found[0].startswith("EVIDENCE "))

    def test_bad_cells_are_findings(self):
        evidence = parse("parse_evidence", "parse-evidence-bad-row", "tdd-evidence.md")
        found = "\n".join(reasons(evidence.findings))
        self.assertIn("phase 'purple' is not one of baseline, red, green, refactor, checkpoint", found)
        self.assertIn("Seq 'three' is not a number", found)

    def test_malformed_text_never_raises(self):
        for name in ("parse_spec", "parse_plan", "parse_tasks", "parse_evidence"):
            function = parser_function(name)
            for text in ("", "|", "## Verification Plan", "| a |\n|---|\n| b | c | d |\n", "- [ ] T001 [NT: unclosed"):
                function(text)

    def test_a_row_with_the_wrong_number_of_cells_is_a_finding(self):
        text = fixture_text("valid-minimal", "plan.md").replace("| broad | tests/fixtures/bin |", "| broad |")
        plan = parser_function("parse_plan")(text)
        self.assertIn("has 3 cells, expected 4", "\n".join(reasons(plan.findings)))
        self.assertEqual([command.id for command in plan.commands], ["unit"])


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# The behaviour checklist (contracts/behaviour-checklist.md sections 2 and 3)
# ---------------------------------------------------------------------------

import hashlib  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import tempfile  # noqa: E402

from support import FEATURES  # noqa: E402

SCENARIO_2_TEXT = "Given a cart with two items, When it is totalled, Then the total is their sum."


def checklist(case):
    return parse("parse_checklist", case, os.path.join("tests", "behaviour-checklist.md"))


def independent_fingerprint(clauses):
    """First six hex characters of SHA-256 over '<keyword> <text>' per clause, joined by line breaks."""
    text = "\n".join(f"{keyword} {words}" for keyword, words in clauses)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:6]


class ScenarioTextTests(unittest.TestCase):
    def test_scenario_text_is_read_from_the_specification(self):
        spec = parse("parse_spec", "parse-checklist-full", "spec.md")
        normalise = parser_function("normalise")
        self.assertEqual(
            normalise(spec.scenario_text["US1-AS1"]),
            "Given an empty cart, When it is totalled, Then the total is zero.",
        )

    def test_indented_continuation_lines_are_part_of_the_text(self):
        spec = parse("parse_spec", "parse-checklist-full", "spec.md")
        self.assertEqual(parser_function("normalise")(spec.scenario_text["US1-AS2"]), SCENARIO_2_TEXT)

    def test_the_list_number_is_not_part_of_the_text(self):
        spec = parse("parse_spec", "valid-minimal", "spec.md")
        self.assertFalse(spec.scenario_text["US1-AS1"].lstrip().startswith("1."))
        self.assertEqual(sorted(spec.scenario_text), ["US1-AS1", "US1-AS2"])

    def test_ids_are_unchanged(self):
        spec = parse("parse_spec", "parse-checklist-full", "spec.md")
        self.assertEqual(spec.scenario_ids, ["US1-AS1", "US1-AS2"])


class NormaliseTests(unittest.TestCase):
    def test_emphasis_quote_marks_and_line_breaks_are_removed(self):
        normalise = parser_function("normalise")
        text = "> **Given** a __cart__,\n> **When** it\n>   is totalled"
        self.assertEqual(normalise(text), "Given a cart, When it is totalled")

    def test_case_punctuation_and_wording_are_kept(self):
        normalise = parser_function("normalise")
        self.assertNotEqual(normalise("Total is zero."), normalise("total is zero."))
        self.assertNotEqual(normalise("Total is zero."), normalise("Total is zero"))

    def test_a_quote_and_its_scenario_that_differ_only_in_emphasis_and_breaks_normalise_alike(self):
        spec = parse("parse_spec", "parse-checklist-full", "spec.md")
        result = checklist("parse-checklist-quote-emphasis")
        normalise = parser_function("normalise")
        self.assertEqual(normalise(result.sections[0].quote), normalise(spec.scenario_text["US1-AS1"]))


class ChecklistReadingTests(unittest.TestCase):
    def setUp(self):
        self.result = checklist("parse-checklist-full")

    def test_nothing_is_reported_for_a_well_formed_checklist(self):
        self.assertEqual(reasons(self.result.findings), [])

    def test_sections_are_read_in_order(self):
        self.assertEqual(
            [(section.kind, section.heading) for section in self.result.sections],
            [("scenario", "US1-AS1"), ("scenario", "US1-AS2"), ("other", "Other behaviours")],
        )

    def test_a_scenario_heading_with_a_colon_suffix_has_the_id_before_the_colon(self):
        self.assertEqual(self.result.sections[0].heading, "US1-AS1")

    def test_the_quote_is_the_block_quote_under_the_heading(self):
        self.assertIn("empty cart", self.result.sections[0].quote)
        self.assertEqual(self.result.sections[2].quote, "")

    def test_item_lines_are_read_with_both_lists(self):
        items = {item.id: item for item in self.result.items}
        self.assertEqual(sorted(items), ["BI-001", "BI-002", "BI-003"])
        self.assertEqual(items["BI-001"].expresses, ["FR-001", "US1-AS1"])
        self.assertEqual(items["BI-001"].verified_by, ["VO-001"])
        self.assertEqual(items["BI-003"].expresses, ["FR-003", "EC-01"])
        self.assertEqual(items["BI-003"].verified_by, ["VO-002", "exemption FR-003"])

    def test_clauses_attach_to_the_nearest_item_above(self):
        items = {item.id: item for item in self.result.items}
        self.assertEqual(
            items["BI-001"].clauses,
            [
                ("Given", "an empty cart"),
                ("When", "the shopper asks for the total"),
                ("Then", "the total is zero"),
                ("And", "no error is shown"),
            ],
        )
        self.assertEqual([keyword for keyword, _text in items["BI-002"].clauses], ["Given", "When", "Then"])

    def test_items_know_their_section(self):
        sections = {item.id: item.section for item in self.result.items}
        self.assertEqual(sections, {"BI-001": "US1-AS1", "BI-002": "US1-AS2", "BI-003": "Other behaviours"})

    def test_lines_inside_a_fenced_code_block_are_ignored(self):
        self.assertNotIn("BI-099", [item.id for item in self.result.items])
        self.assertEqual(reasons(self.result.findings), [])

    def test_malformed_input_becomes_findings_and_never_raises(self):
        result = checklist("parse-checklist-malformed")
        found = reasons(result.findings)
        self.assertGreater(len(found), 0)
        self.assertTrue(all(line.startswith("B4 ") for line in found), found)
        function = parser_function("parse_checklist")
        texts = ("", "#", "## ", "- **BI-001**", "  - **Given** x", "> quote", "```\n")
        for text in texts + ("## US1-AS1\n> a\n- **BI-001** Expresses",):
            function(text)


class FingerprintTests(unittest.TestCase):
    def fingerprint(self, case):
        result = checklist(case)
        return parser_function("item_fingerprint")(result.items[0])

    def test_fingerprint_is_six_hex_characters_over_the_normalised_clauses(self):
        clauses = [
            ("Given", "an empty cart"),
            ("When", "the shopper asks for the total"),
            ("Then", "the total is zero"),
            ("And", "no error is shown"),
        ]
        value = self.fingerprint("parse-checklist-same")
        self.assertRegex(value, r"^[0-9a-f]{6}$")
        self.assertEqual(value, independent_fingerprint(clauses))

    def test_it_is_unchanged_when_the_verified_by_list_changes(self):
        self.assertEqual(self.fingerprint("parse-checklist-same"), self.fingerprint("parse-checklist-relinked"))

    def test_it_changes_when_one_word_of_a_clause_changes(self):
        self.assertNotEqual(self.fingerprint("parse-checklist-same"), self.fingerprint("parse-checklist-reworded"))


class ApplicabilityTests(unittest.TestCase):
    def applies(self, case):
        applies = parser_function("checklist_applies")
        return applies(os.path.join(FEATURES, case))

    def test_the_marker_alone_switches_the_rules_on(self):
        self.assertTrue(self.applies("parse-checklist-marker-only"))

    def test_the_file_alone_switches_the_rules_on(self):
        self.assertTrue(self.applies("parse-checklist-file-only"))

    def test_neither_leaves_them_off(self):
        self.assertFalse(self.applies("valid-minimal"))

    def test_a_missing_directory_leaves_them_off(self):
        folder = tempfile.mkdtemp(prefix="tdd-parse-")
        self.addCleanup(shutil.rmtree, folder, True)
        self.assertFalse(parser_function("checklist_applies")(os.path.join(folder, "absent")))

    def test_the_plan_parser_notes_the_marker(self):
        self.assertTrue(parse("parse_plan", "parse-checklist-marker-only", "plan.md").has_checklist_marker)
        self.assertFalse(parse("parse_plan", "valid-minimal", "plan.md").has_checklist_marker)


class ItemEvidenceTests(unittest.TestCase):
    def test_item_baseline_rows_are_read(self):
        evidence = parse("parse_evidence", "parse-checklist-evidence", "tdd-evidence.md")
        self.assertEqual(reasons(evidence.findings), [])
        row = evidence.item_baseline[0]
        self.assertEqual((row.item, row.verified_by, row.fingerprint, row.seq), ("BI-001", ["VO-001"], "a1b2c3", 1))

    def test_item_change_records_are_read(self):
        evidence = parse("parse_evidence", "parse-checklist-evidence", "tdd-evidence.md")
        change = evidence.item_changes[0]
        self.assertEqual((change.id, change.item, change.requirements), ("BX-01", "BI-001", ["FR-001", "US1-AS1"]))
        self.assertTrue(change.alters_behaviour)
        self.assertEqual((change.approved_by, change.new_fingerprint), ("Lee", "d4e5f6"))

    def test_the_tables_are_empty_when_absent(self):
        evidence = parse("parse_evidence", "valid-minimal", "tdd-evidence.md")
        self.assertEqual(reasons(evidence.findings), [])
        self.assertEqual((evidence.item_baseline, evidence.item_changes), ([], []))
