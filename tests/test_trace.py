"""The plan and tasks checks (contracts/check-cli.md, checking subcommands)."""

import json
import os
import unittest

from support import RepoCase, read, snapshot, write

PLAN_PASSED = "plan: passed\n"
TASKS_PASSED = "tasks: passed\n"


class TraceCase(RepoCase):
    subcommand = None

    def run_on(self, fixture, extra=()):
        root = self.repo(fixture)
        return root, self.check([self.subcommand] + list(extra), root)

    def assert_fails_with(self, fixture, *findings):
        _root, result = self.run_on(fixture)
        self.assertEqual(result.code, 1, result)
        lines = result.out.splitlines()
        for finding in findings:
            self.assertIn(finding, lines)
        return lines

    def assert_only_finding(self, fixture, finding):
        lines = self.assert_fails_with(fixture, finding)
        self.assertEqual(lines, [f"{self.subcommand}: failed, 1 finding", finding])


class PlanCheckTests(TraceCase):
    subcommand = "plan"

    def test_valid_plan_passes(self):
        _root, result = self.run_on("valid-minimal")
        self.assertEqual((result.code, result.out, result.err), (0, PLAN_PASSED, ""))

    def test_missing_section_is_a_gap_to_resolve_in_planning(self):
        self.assert_only_finding(
            "plan-no-section",
            "PLAN plan.md: no Verification Plan section: a gap to resolve in planning, by the plan stage",
        )

    def test_missing_plan_file_is_the_same_gap(self):
        root = self.repo("valid-minimal")
        os.remove(os.path.join(self.feature(root), "plan.md"))
        result = self.check(["plan"], root)
        self.assertEqual(result.code, 1)
        self.assertIn("PLAN plan.md: no Verification Plan section", result.out)

    def test_empty_commands_table_is_a_gap_to_resolve_in_planning(self):
        self.assert_only_finding(
            "plan-no-commands",
            "PLAN plan.md: no verification command is declared: a gap to resolve in planning",
        )

    def test_missing_commands_table_is_reported(self):
        lines = self.assert_fails_with("parse-wrong-header")
        self.assertTrue(any("### Verification commands" in line for line in lines), lines)

    def test_requirement_without_obligation_or_exemption_fails_c1(self):
        self.assert_only_finding("plan-uncovered-fr", "C1 FR-001: no obligation and no exemption")

    def test_scenario_without_obligation_or_exemption_fails_c1(self):
        self.assert_only_finding("plan-uncovered-scenario", "C1 US1-AS2: no obligation and no exemption")

    def test_an_exemption_covers_a_scenario(self):
        root = self.repo("plan-uncovered-scenario")
        plan = read(self.feature(root), "plan.md").replace(
            "\n## Project Structure", "| US1-AS2 | Covered by hand | Checked at review |\n\n## Project Structure"
        )
        write(self.feature(root), ["plan.md"], plan)
        self.assertEqual(self.check(["plan"], root).code, 0)

    def test_empty_expected_outcome_fails(self):
        self.assert_only_finding("plan-empty-outcome", "PLAN VO-001: expected outcome is empty")

    def test_empty_scenario_and_level_fail(self):
        root = self.repo("valid-minimal")
        plan = read(self.feature(root), "plan.md")
        plan = plan.replace("| An empty cart is totalled |", "| - |").replace("| integration | planned |", "| | planned |")
        write(self.feature(root), ["plan.md"], plan)
        result = self.check(["plan"], root)
        self.assertEqual(result.code, 1)
        self.assertIn("PLAN VO-001: scenario is empty", result.out)
        self.assertIn("PLAN VO-002: level is empty", result.out)

    def test_obligation_naming_no_requirement_fails(self):
        root = self.repo("valid-minimal")
        plan = read(self.feature(root), "plan.md").replace("| VO-001 | FR-001, US1-AS1 |", "| VO-001 | - |")
        write(self.feature(root), ["plan.md"], plan)
        result = self.check(["plan"], root)
        self.assertEqual(result.code, 1)
        self.assertIn("PLAN VO-001: names no requirement", result.out)

    def test_empty_exemption_reason_fails(self):
        self.assert_only_finding("plan-empty-exemption-reason", "PLAN FR-003: exemption reason is empty")

    def test_requirement_id_not_in_spec_fails(self):
        self.assert_only_finding("plan-unknown-requirement", "PLAN VO-001: requirement FR-099 is not in spec.md")

    def test_success_criterion_and_scenario_ids_are_looked_up(self):
        root = self.repo("valid-minimal")
        plan = read(self.feature(root), "plan.md").replace("SC-001, DC-01", "SC-009, US3-AS1, DC-01")
        write(self.feature(root), ["plan.md"], plan)
        result = self.check(["plan"], root)
        self.assertIn("PLAN VO-002: requirement SC-009 is not in spec.md", result.out)
        self.assertIn("PLAN VO-002: requirement US3-AS1 is not in spec.md", result.out)

    def test_exemption_for_an_unknown_requirement_fails(self):
        root = self.repo("valid-minimal")
        plan = read(self.feature(root), "plan.md").replace("| FR-003 | Visual", "| FR-033 | Visual")
        write(self.feature(root), ["plan.md"], plan)
        result = self.check(["plan"], root)
        self.assertIn("PLAN FR-033: exempted requirement is not in spec.md", result.out)
        self.assertIn("C1 FR-003: no obligation and no exemption", result.out)

    def test_unknown_prefix_fails(self):
        self.assert_only_finding(
            "plan-unknown-prefix",
            "PLAN VO-001: requirement XX-01 has an unknown prefix (expected FR-, SC-, USn-ASm, DC- or EC-)",
        )

    def test_design_constraint_and_edge_case_ids_are_accepted_without_lookup(self):
        root = self.repo("valid-minimal")
        self.assertNotIn("DC-01", read(self.feature(root), "spec.md"))
        self.assertNotIn("EC-01", read(self.feature(root), "spec.md"))
        self.assertIn("DC-01, EC-01", read(self.feature(root), "plan.md"))
        self.assertEqual(self.check(["plan"], root).code, 0)

    def test_malformed_elements_fail_the_check(self):
        lines = self.assert_fails_with("parse-bad-enum")
        self.assertIn("PLAN unit: scope 'wide' is not one of focused, broad", lines)

    def test_missing_spec_is_a_usage_error(self):
        root = self.repo("valid-minimal")
        os.remove(os.path.join(self.feature(root), "spec.md"))
        result = self.check(["plan"], root)
        self.assertEqual(result.code, 2)
        self.assertIn("spec.md", result.err)

    def test_json_carries_the_findings(self):
        _root, result = self.run_on("plan-uncovered-fr", ["--json"])
        data = json.loads(result.out)
        self.assertEqual(data["exit_code"], 1)
        self.assertEqual(
            data["findings"], [{"rule": "C1", "subject": "FR-001", "reason": "no obligation and no exemption"}]
        )

    def test_output_is_identical_on_two_runs(self):
        root = self.repo("parse-bad-ids")
        first = self.check(["plan"], root)
        second = self.check(["plan"], root)
        self.assertEqual((first.code, first.out, first.err), (second.code, second.out, second.err))
        self.assertEqual(first.code, 1)

    def test_plan_creates_or_changes_no_file(self):
        for fixture in ("valid-minimal", "plan-uncovered-fr"):
            root = self.repo(fixture)
            before = snapshot(root)
            self.check(["plan"], root)
            self.assertEqual(snapshot(root), before)


class TasksCheckTests(TraceCase):
    subcommand = "tasks"

    def test_valid_tasks_pass(self):
        _root, result = self.run_on("valid-minimal")
        self.assertEqual((result.code, result.out, result.err), (0, TASKS_PASSED, ""))

    def test_unlabelled_task_fails_g1(self):
        self.assert_only_finding("tasks-unlabelled", "G1 T015: no [VO-nnn] or [NT: reason] label")

    def test_no_test_label_without_a_reason_fails_g1(self):
        root = self.repo("valid-minimal")
        tasks = read(self.feature(root), "tasks.md").replace("[NT: README wording only]", "[NT: ]")
        write(self.feature(root), ["tasks.md"], tasks)
        result = self.check(["tasks"], root)
        self.assertEqual(result.code, 1)
        self.assertIn("G1 T015: no [VO-nnn] or [NT: reason] label", result.out)

    def test_label_naming_an_unknown_obligation_fails(self):
        self.assert_only_finding("tasks-unknown-obligation", "TASKS T015: obligation VO-009 is not in the plan")

    def test_obligation_named_by_no_task_fails_c2(self):
        self.assert_only_finding("tasks-obligation-without-task", "C2 VO-002: no task names it")

    def test_obligation_without_a_behaviour_task_fails_c2(self):
        self.assert_only_finding(
            "tasks-obligation-without-behaviour",
            "C2 VO-002: named by a test task (T013) but by no behaviour task",
        )

    def test_behaviour_before_test_fails_c3(self):
        self.assert_only_finding(
            "tasks-behaviour-before-test",
            "C3 VO-002: its first task T012 is a behaviour task, so no test task comes before it",
        )

    def test_plan_without_the_section_is_reported_as_the_gap(self):
        root = self.repo("plan-no-section")
        result = self.check(["tasks"], root)
        self.assertEqual(result.code, 1)
        self.assertIn("PLAN plan.md: no Verification Plan section", result.out)

    def test_missing_tasks_file_is_a_usage_error(self):
        root = self.repo("valid-minimal")
        os.remove(os.path.join(self.feature(root), "tasks.md"))
        result = self.check(["tasks"], root)
        self.assertEqual(result.code, 2)
        self.assertIn("tasks.md", result.err)

    def test_json_carries_the_findings(self):
        _root, result = self.run_on("tasks-unlabelled", ["--json"])
        data = json.loads(result.out)
        self.assertEqual(data["exit_code"], 1)
        self.assertEqual(data["findings"][0]["rule"], "G1")
        self.assertEqual(data["findings"][0]["subject"], "T015")

    def test_output_is_identical_on_two_runs(self):
        root = self.repo("tasks-behaviour-before-test")
        first = self.check(["tasks"], root)
        second = self.check(["tasks"], root)
        self.assertEqual((first.code, first.out, first.err), (second.code, second.out, second.err))
        self.assertEqual(first.code, 1)

    def test_tasks_creates_or_changes_no_file(self):
        for fixture in ("valid-minimal", "tasks-unlabelled"):
            root = self.repo(fixture)
            before = snapshot(root)
            self.check(["tasks"], root)
            self.assertEqual(snapshot(root), before)


if __name__ == "__main__":
    unittest.main()
