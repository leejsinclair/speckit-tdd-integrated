"""The task gate, rules G1 to G9 (data-model.md, The task gate)."""

import json
import os
import unittest

from support import RepoCase, load_payload, snapshot


class GateCase(RepoCase):
    def gate(self, fixture, *args):
        root = self.repo(fixture)
        return self.check(["gate"] + list(args), root)

    def assert_passes(self, fixture, task):
        result = self.gate(fixture, "--task", task)
        self.assertEqual((result.code, result.out, result.err), (0, f"gate {task}: passed\n", ""), result)

    def assert_fails(self, fixture, task, *findings):
        result = self.gate(fixture, "--task", task)
        self.assertEqual(result.code, 1, result)
        lines = result.out.splitlines()
        noun = "finding" if len(findings) == 1 else "findings"
        self.assertEqual(lines, [f"gate {task}: failed, {len(findings)} {noun}"] + list(findings))


class FirstRulesTests(GateCase):
    """G1, G3, G4 and G9, one failing and one passing fixture each."""

    def test_g1_fails_for_a_task_without_a_label(self):
        self.assert_fails("gate-g1-fail", "T015", "G1 T015: no [VO-nnn] or [NT: reason] label")

    def test_g1_passes_for_a_no_test_task(self):
        self.assert_passes("gate-g1-pass", "T015")

    def test_g3_fails_without_a_valid_failing_first_record(self):
        self.assert_fails("gate-g3-fail", "T011", "G3 T011 VO-001: no valid failing-first record and no exception")

    def test_g3_fails_with_no_evidence_document_at_all(self):
        root = self.repo("gate-g3-pass")
        os.remove(os.path.join(self.feature(root), "tdd-evidence.md"))
        result = self.check(["gate", "--task", "T011"], root)
        self.assertEqual(result.code, 1)
        self.assertIn("G3 T011 VO-001: no valid failing-first record and no exception", result.out)

    def test_a_test_task_passes_with_a_valid_red_record_alone(self):
        self.assert_passes("gate-g3-pass", "T011")

    def test_g4_fails_without_a_passing_record_after_the_failing_first_record(self):
        self.assert_fails(
            "gate-g4-fail", "T012", "G4 T012 VO-001: no valid passing record after its failing-first record"
        )

    def test_a_behaviour_task_with_no_evidence_fails_g3_and_g4(self):
        self.assert_fails(
            "gate-g4-pass",
            "T014",
            "G3 T014 VO-002: no valid failing-first record and no exception",
            "G4 T014 VO-002: no valid passing record after its failing-first record",
        )

    def test_g4_passes_with_red_then_green(self):
        self.assert_passes("gate-g4-pass", "T012")

    def test_g9_fails_for_a_record_made_with_an_undeclared_command(self):
        self.assert_fails("gate-g9-fail", "T012", "G9 T012 #3: command 'adhoc' is not declared in the plan")

    def test_g9_passes_when_every_record_used_a_declared_command(self):
        self.assert_passes("gate-g9-pass", "T012")

    def test_a_no_test_task_passes_g3_and_g4(self):
        self.assert_passes("gate-all-fail", "T015")


class TestIntegrityTests(GateCase):
    """G5 and G8: a test changed between its Red and Green runs."""

    G5 = (
        "G5 T012 VO-001: test files changed between the failing-first record (#2) and the passing record (#3) "
        "with no expectation change"
    )

    def test_g5_fails_when_the_green_fingerprint_differs_from_the_red_one(self):
        self.assert_fails("gate-g5-fail", "T012", self.G5)

    def test_g5_passes_when_an_expectation_change_for_the_task_carries_the_new_fingerprint(self):
        self.assert_passes("gate-g5-pass", "T012")

    def test_g5_is_not_met_by_an_expectation_change_for_another_task(self):
        self.assert_fails("gate-g5-other-task", "T012", self.G5)

    def test_g5_does_not_apply_without_a_valid_red_record(self):
        result = self.gate("gate-g5-no-red", "--task", "T012")
        self.assertEqual(result.code, 1)
        self.assertIn("G3 T012 VO-001: no valid failing-first record and no exception", result.out)
        self.assertNotIn("G5", result.out)

    def test_a_test_task_is_not_subject_to_g5(self):
        self.assert_passes("gate-g5-fail", "T011")

    def test_g8_fails_when_an_expectation_change_names_no_requirement(self):
        self.assert_fails("gate-g8-fail-no-requirement", "T012", "G8 T012 XC-01: names no requirement")

    def test_g8_fails_when_a_change_alters_behaviour_without_approval(self):
        self.assert_fails("gate-g8-fail-no-approval", "T012", "G8 T012 XC-01: alters behaviour and has no approval")

    def test_g8_passes_once_approved(self):
        self.assert_passes("gate-g8-pass", "T012")

    def test_g8_applies_only_to_the_task_the_change_was_recorded_for(self):
        self.assert_passes("gate-g8-fail-no-approval", "T011")


class DecisionGateTests(GateCase):
    def test_g2_fails_for_a_task_on_an_open_decision(self):
        self.assert_fails("gate-g2-fail", "T014", "G2 T014 DN-01: an open decision holds this task")
        self.assert_fails("gate-g2-fail", "T013", "G2 T013 DN-01: an open decision holds this task")

    def test_g2_passes_for_a_task_the_decision_does_not_list(self):
        self.assert_passes("gate-g2-fail", "T012")
        self.assert_passes("gate-g2-fail", "T015")

    def test_g2_passes_after_resolution(self):
        self.assert_passes("gate-g2-pass", "T014")


class FailureGateTests(GateCase):
    def test_g6_fails_when_the_latest_record_for_the_task_is_a_failure(self):
        self.assert_fails("gate-g6-fail-latest", "T012", "G6 T012 #4: the latest record for the task is a failure")

    def test_g6_fails_while_any_failure_record_for_the_task_is_unclassified(self):
        self.assert_fails("gate-g6-fail-unclassified", "T012", "G6 T012 #3: failure record is unclassified")

    def test_g6_passes_for_a_classified_failure_followed_by_a_pass(self):
        self.assert_passes("gate-g6-pass", "T012")

    def test_g6_passes_for_a_test_task_whose_latest_record_is_its_valid_red_record(self):
        self.assert_passes("gate-g6-pass", "T011")

    def test_an_unreliable_record_never_counts_for_g3_or_g4(self):
        self.assert_fails(
            "gate-unreliable",
            "T011",
            "G3 T011 VO-001: no valid failing-first record and no exception",
            "G6 T011 #2: the latest record for the task is a failure",
        )
        result = self.gate("gate-unreliable", "--task", "T012")
        self.assertIn("G3 T012 VO-001: no valid failing-first record and no exception", result.out)
        self.assertIn("G4 T012 VO-001: no valid passing record after its failing-first record", result.out)


class ExceptionGateTests(GateCase):
    PRESERVING = (
        "G4 T014 VO-002: EX-01 is behaviour-preserving and needs a passing baseline or green record before the "
        "change and a passing refactor record after it, on the same selector"
    )

    def test_one_exception_covers_the_test_task_and_the_behaviour_task(self):
        self.assert_passes("gate-exception-pass", "T013")
        self.assert_passes("gate-exception-pass", "T014")

    def test_g4_still_requires_a_passing_record(self):
        self.assert_passes("gate-exception-no-green", "T013")
        self.assert_fails(
            "gate-exception-no-green", "T014", "G4 T014 VO-002: no valid passing record after its exception"
        )

    def test_g4_requires_the_passing_record_to_be_later_than_the_exception(self):
        self.assert_fails(
            "gate-exception-green-before", "T014", "G4 T014 VO-002: no valid passing record after its exception"
        )

    def test_an_exception_naming_no_obligation_covers_only_its_own_task(self):
        self.assert_passes("gate-exception-task-only", "T013")
        self.assert_fails(
            "gate-exception-task-only", "T014", "G3 T014 VO-002: no valid failing-first record and no exception"
        )

    def test_an_exception_does_not_cover_another_obligation(self):
        self.assert_fails(
            "gate-exception-pass", "T011", "G3 T011 VO-001: no valid failing-first record and no exception"
        )

    def test_behaviour_preserving_needs_a_pass_before_and_a_refactor_pass_after_on_the_same_selector(self):
        self.assert_passes("gate-exception-preserving-pass", "T014")
        self.assert_passes("gate-exception-preserving-pass", "T013")
        self.assert_fails("gate-exception-preserving-fail", "T014", self.PRESERVING)
        self.assert_fails("gate-exception-preserving-no-refactor", "T014", self.PRESERVING)

    def test_environment_blocked_lets_no_task_naming_the_obligation_pass(self):
        blocked = "EX-01 is environment-blocked and replaces no evidence: the obligation is blocked"
        self.assert_fails("gate-exception-blocked", "T013", f"G3 T013 VO-002: {blocked}")
        result = self.gate("gate-exception-blocked", "--task", "T014")
        self.assertEqual(result.code, 1)
        self.assertIn(f"G3 T014 VO-002: {blocked}", result.out.splitlines())

    def test_g7_fails_without_a_rationale_for_every_task_the_exception_covers(self):
        for task in ("T013", "T014"):
            self.assert_fails("gate-g7-fail-no-rationale", task, f"G7 {task} EX-01: has no rationale")

    def test_g7_fails_without_an_alternative_where_one_is_required(self):
        for task in ("T013", "T014"):
            self.assert_fails("gate-g7-fail-no-alternative", task, f"G7 {task} EX-01: has no alternative verification")

    def test_g7_fails_when_flagged_and_not_approved(self):
        for task in ("T013", "T014"):
            self.assert_fails("gate-g7-fail-flagged", task, f"G7 {task} EX-01: needs approval and has no approver")

    def test_g7_fails_for_a_kind_beyond_the_agents_authority_even_when_not_flagged(self):
        self.assert_fails("gate-g7-fail-kind", "T014", "G7 T014 EX-01: needs approval and has no approver")

    def test_g7_fails_for_an_alternative_of_none_even_when_not_flagged(self):
        self.assert_fails("gate-g7-fail-none", "T014", "G7 T014 EX-01: needs approval and has no approver")

    def test_g7_passes_once_approved(self):
        self.assert_passes("gate-g7-pass", "T013")
        self.assert_passes("gate-g7-pass", "T014")

    def test_g7_does_not_apply_to_a_task_the_exception_does_not_cover(self):
        self.assert_passes("gate-g7-fail-flagged", "T015")
        result = self.gate("gate-g7-fail-flagged", "--task", "T011")
        self.assertNotIn("G7", result.out)

    def test_environment_blocked_needs_no_alternative(self):
        result = self.gate("gate-exception-blocked", "--task", "T013")
        self.assertNotIn("G7", result.out)


class GateUsageTests(GateCase):
    def test_unknown_task_is_a_usage_error(self):
        result = self.gate("gate-g4-pass", "--task", "T099")
        self.assertEqual(result.code, 2)
        self.assertIn("task T099 is not in tasks.md", result.err)

    def test_a_feature_without_a_verification_plan_fails_with_the_gap(self):
        result = self.gate("plan-no-section", "--task", "T011")
        self.assertEqual(result.code, 1)
        self.assertIn("PLAN plan.md: no Verification Plan section", result.out)

    def test_malformed_evidence_fails_the_gate(self):
        result = self.gate("parse-evidence-wrong-header", "--task", "T012")
        self.assertEqual(result.code, 1)
        self.assertIn("EVIDENCE tdd-evidence.md: header row under '## Test execution records'", result.out)

    def test_json_carries_the_findings(self):
        result = self.gate("gate-g4-fail", "--task", "T012", "--json")
        data = json.loads(result.out)
        self.assertEqual(data["exit_code"], 1)
        self.assertEqual(
            data["findings"],
            [
                {
                    "rule": "G4",
                    "subject": "T012 VO-001",
                    "reason": "no valid passing record after its failing-first record",
                }
            ],
        )

    def test_output_is_identical_on_two_runs(self):
        root = self.repo("gate-all-fail")
        first = self.check(["gate", "--all"], root)
        second = self.check(["gate", "--all"], root)
        self.assertEqual((first.code, first.out, first.err), (second.code, second.out, second.err))

    def test_gate_creates_or_changes_no_file(self):
        root = self.repo("gate-all-fail")
        before = snapshot(root)
        self.check(["gate", "--all"], root)
        self.check(["gate", "--task", "T012"], root)
        self.assertEqual(snapshot(root), before)


class GateAllTests(GateCase):
    def test_all_applies_the_rules_to_completed_tasks(self):
        result = self.gate("gate-all-fail", "--all")
        self.assertEqual(result.code, 1, result)
        lines = result.out.splitlines()
        self.assertEqual(
            lines[:3],
            [
                "gate: failed, 2 findings",
                "G3 T014 VO-002: no valid failing-first record and no exception",
                "G4 T014 VO-002: no valid passing record after its failing-first record",
            ],
        )

    def test_all_passes_when_every_completed_task_passes(self):
        result = self.gate("gate-all-pass", "--all")
        self.assertEqual(result.code, 0, result)
        self.assertEqual(result.out.splitlines()[0], "gate: passed, 3 completed tasks")

    def test_all_reports_incomplete_tasks_without_failing_on_them(self):
        result = self.gate("gate-all-pass", "--all")
        self.assertEqual(result.code, 0, result)
        self.assertEqual(
            result.out.splitlines()[1:],
            [
                "Incomplete tasks:",
                "T013 would not pass: G3 T013 VO-002: no valid failing-first record and no exception",
                "T014 would not pass: G3 T014 VO-002: no valid failing-first record and no exception; "
                "G4 T014 VO-002: no valid passing record after its failing-first record",
            ],
        )

    def test_an_incomplete_task_that_would_pass_is_reported_as_such(self):
        result = self.gate("gate-g4-fail", "--all")
        self.assertIn("T015 would pass", result.out.splitlines())

    def test_all_json_lists_incomplete_tasks(self):
        result = self.gate("gate-all-pass", "--all", "--json")
        data = json.loads(result.out)
        self.assertEqual(data["exit_code"], 0)
        self.assertEqual([item["task"] for item in data["incomplete"]], ["T013", "T014"])
        self.assertFalse(data["incomplete"][0]["would_pass"])
        self.assertEqual(data["incomplete"][0]["findings"][0]["rule"], "G3")


class G11Tests(GateCase):
    """G11: the checklist rules, applied to every task once the baseline is recorded."""

    B1 = "G11 {task} FR-004: B1: no behaviour item expresses it"
    B5 = "G11 {task} BI-001: B5: `src/cart.py` is a path-shaped token that spec.md does not name"

    def item_lines(self, fixture, *args):
        result = self.gate(fixture, *args)
        return result, [line for line in result.out.splitlines() if line.startswith(("G10 ", "G11 "))]

    def test_a_requirement_added_after_the_baseline_holds_every_task(self):
        for task in ("T014", "T015"):
            with self.subTest(task=task):
                result, lines = self.item_lines("g11-requirement-added", "--task", task)
                self.assertEqual(lines, [self.B1.format(task=task)])
                self.assertEqual(result.code, 1, result)

    def test_a_broken_item_holds_every_task_including_a_no_test_task(self):
        for task in ("T014", "T015"):
            with self.subTest(task=task):
                result, lines = self.item_lines("g11-item-broken", "--task", task)
                self.assertEqual(lines, [self.B5.format(task=task)])

    def test_nothing_is_reported_before_the_baseline(self):
        result, lines = self.item_lines("g11-before-baseline", "--task", "T014")
        self.assertEqual(lines, [], result.out)

    def test_nothing_is_reported_for_a_passing_checklist(self):
        result, lines = self.item_lines("items-baseline", "--task", "T014")
        self.assertEqual((lines, result.code), ([], 0))

    def test_gate_all_reports_g11_for_completed_tasks(self):
        root = self.repo("g11-requirement-added")
        path = os.path.join(root, "specs", "001-demo", "tasks.md")
        with open(path) as handle:
            text = handle.read()
        with open(path, "w") as handle:
            handle.write(text.replace("- [ ] T015", "- [X] T015"))
        result = self.check(["gate", "--all"], root)
        self.assertEqual(result.code, 1, result)
        self.assertIn(self.B1.format(task="T015"), result.out.splitlines())

    def test_the_refusal_names_the_way_forward_for_a_checklist_finding(self):
        root = self.repo("g11-requirement-added")
        payload = json.loads(load_payload("edit-tasks.json", root))
        payload["tool_input"].update(old_string="- [ ] T015", new_string="- [X] T015")
        err = " ".join(self.check(["hook"], root, stdin=json.dumps(payload)).err.split())
        self.assertIn("return to the plan stage", err)
        self.assertIn("specification or the Verification Plan first and then the checklist", err)

    def test_the_hook_refuses_to_mark_complete_a_task_held_by_g11(self):
        root = self.repo("g11-requirement-added")
        payload = json.loads(load_payload("edit-tasks.json", root))
        payload["tool_input"].update(old_string="- [ ] T015", new_string="- [X] T015")
        result = self.check(["hook"], root, stdin=json.dumps(payload))
        self.assertEqual(result.code, 2, result)
        self.assertIn(self.B1.format(task="T015"), result.err.splitlines())


class NoToolingGateTests(GateCase):
    """In no-tooling mode no rule needs a run (research D2, D4; FR-003, FR-005, SC-004)."""

    def test_gate_all_passes_with_every_task_complete_and_no_evidence(self):
        result = self.gate("no-tooling-complete", "--all")
        self.assertEqual((result.code, result.out, result.err), (0, "gate: passed, 5 completed tasks\n", ""))

    def test_every_test_and_behaviour_task_passes_on_its_own(self):
        for task in ("T011", "T012", "T013", "T014", "T015"):
            with self.subTest(task=task):
                self.assert_passes("no-tooling-complete", task)

    def test_an_open_decision_still_holds_a_task(self):
        self.assert_fails("no-tooling-open-decision", "T013", "G2 T013 DN-01: an open decision holds this task")

    def test_a_task_the_decision_does_not_list_still_passes(self):
        self.assert_passes("no-tooling-open-decision", "T012")

    def test_a_failing_checklist_holds_a_task_with_no_baseline_recorded(self):
        for task in ("T014", "T015"):
            with self.subTest(task=task):
                self.assert_fails(
                    "no-tooling-checklist-changed", task, f"G11 {task} FR-004: B1: no behaviour item expresses it"
                )

    def test_a_passing_checklist_holds_nothing(self):
        root = self.repo("no-tooling-complete")
        self.assertEqual(self.check(["gate", "--task", "T014"], root).code, 0)

    def test_the_same_feature_with_a_command_declared_holds_the_same_tasks(self):
        root = self.repo("no-tooling-complete")
        path = os.path.join(self.feature(root), "plan.md")
        with open(path) as handle:
            text = handle.read()
        commands = (
            "| unit | `sh tests/fixtures/bin/fake_test.sh {select}` | focused | tests/fixtures/bin |\n"
            "| suite | `sh tests/fixtures/bin/fake_test.sh pass` | broad | tests/fixtures/bin |\n"
        )
        self.assertIn("| None | - | - | - |\n", text)
        with open(path, "w") as handle:
            handle.write(text.replace("| None | - | - | - |\n", commands))
        result = self.check(["gate", "--all"], root)
        self.assertEqual(result.code, 1, result)
        lines = result.out.splitlines()
        for finding in (
            "G3 T011 VO-001: no valid failing-first record and no exception",
            "G3 T012 VO-001: no valid failing-first record and no exception",
            "G4 T012 VO-001: no valid passing record after its failing-first record",
            "G3 T013 VO-002: no valid failing-first record and no exception",
            "G3 T014 VO-002: no valid failing-first record and no exception",
            "G4 T014 VO-002: no valid passing record after its failing-first record",
        ):
            self.assertIn(finding, lines)

    def test_gate_creates_or_changes_no_file(self):
        root = self.repo("no-tooling-complete")
        before = snapshot(root)
        self.check(["gate", "--all"], root)
        self.assertEqual(snapshot(root), before)


class DeferredGateTests(GateCase):
    """A standing deferral never holds a task; one waiting for approval does, by G12 (FR-008A, FR-009, D4)."""

    G12 = "G12 {task} DF-01: needs approval and has no approver"
    G3 = "G3 {task} VO-002: no valid failing-first record and no exception"

    def lines(self, fixture, task):
        result = self.gate(fixture, "--task", task)
        return result, result.out.splitlines()

    def test_a_standing_deferral_on_an_environment_failure_holds_neither_task(self):
        for task in ("T013", "T014"):
            with self.subTest(task=task):
                self.assert_passes("deferred-standing", task)

    def test_without_the_deferral_the_same_failure_holds_the_tasks(self):
        root = self.repo("deferred-standing")
        path = os.path.join(self.feature(root), "tdd-evidence.md")
        with open(path) as handle:
            text = handle.read()
        with open(path, "w") as handle:
            handle.write(text.split("\n## Deferrals")[0])
        result = self.check(["gate", "--task", "T013"], root)
        self.assertEqual(result.code, 1, result)
        self.assertIn(self.G3.format(task="T013"), result.out.splitlines())
        self.assertIn("G6 T013 #4: the latest record for the task is a failure", result.out.splitlines())

    def test_a_deferral_that_needs_approval_holds_every_task_that_names_the_obligation(self):
        for task in ("T013", "T014"):
            with self.subTest(task=task):
                result, lines = self.lines("deferred-waiting", task)
                self.assertEqual(result.code, 1, result)
                self.assertIn(self.G12.format(task=task), lines)

    def test_a_deferral_that_waits_does_not_stand_so_the_evidence_rules_still_apply(self):
        _result, lines = self.lines("deferred-waiting", "T013")
        self.assertIn(self.G3.format(task="T013"), lines)

    def test_a_task_that_does_not_name_the_obligation_is_not_held_by_g12(self):
        self.assert_passes("deferred-waiting", "T011")

    def test_approval_releases_the_tasks(self):
        for task in ("T013", "T014"):
            with self.subTest(task=task):
                self.assert_passes("deferred-approved", task)

    def test_approving_with_the_script_releases_the_tasks(self):
        root = self.repo("deferred-waiting")
        self.assertEqual(self.check(["gate", "--task", "T013"], root).code, 1)
        approved = self.check(["approve", "--id", "DF-01", "--by", "A Person"], root)
        self.assertEqual(approved.code, 0, approved)
        self.assertEqual(self.check(["gate", "--task", "T013"], root).out, "gate T013: passed\n")
        self.assertEqual(self.check(["gate", "--task", "T014"], root).out, "gate T014: passed\n")

    def test_an_approved_deferral_holds_nothing_after_a_defect_failure_either(self):
        for task in ("T013", "T014"):
            with self.subTest(task=task):
                self.assert_passes("deferred-after-failure", task)

    def test_a_later_passing_run_needs_no_deferral_and_the_tasks_pass(self):
        for task in ("T013", "T014"):
            with self.subTest(task=task):
                self.assert_passes("deferred-then-verified", task)

    def test_a_standing_deferral_beside_an_environment_blocked_exception_holds_nothing(self):
        for task in ("T013", "T014"):
            with self.subTest(task=task):
                self.assert_passes("deferred-and-blocked-exception", task)

    def test_gate_all_passes_when_every_task_is_complete(self):
        result = self.gate("deferred-compliant", "--all")
        self.assertEqual((result.code, result.out), (0, "gate: passed, 5 completed tasks\n"), result)


if __name__ == "__main__":
    unittest.main()
