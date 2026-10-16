"""The compliance check, rules C1 to C7 (data-model.md), and the two example runs."""

import json
import os
import unittest

from support import REPO, RepoCase, run_check, snapshot

OUT_OF_DATE = (
    "C7 tdd-evidence.md: the Summary is out of date: it differs from the view regenerated from plan.md and the tables"
)
COMPLIANT_RUN = os.path.join("examples", "runs", "compliant")
TESTS_ONLY_RUN = os.path.join("examples", "runs", "tests-only")
FRONTEND_RUN = os.path.join("examples", "runs", "frontend-planned")


class ComplianceCase(RepoCase):
    def compliance(self, fixture, *extra):
        root = self.repo(fixture)
        return self.check(["compliance"] + list(extra), root)

    def assert_compliant(self, fixture):
        result = self.compliance(fixture)
        self.assertEqual((result.code, result.out, result.err), (0, "COMPLIANT\n", ""), result)

    def assert_non_compliant(self, fixture, *findings, only=True):
        result = self.compliance(fixture)
        self.assertEqual(result.code, 1, result)
        lines = result.out.splitlines()
        self.assertEqual(lines[0], "NON-COMPLIANT")
        for finding in findings:
            self.assertIn(finding, lines)
        if only:
            self.assertEqual(lines[1:], list(findings))
        return lines


class RuleTests(ComplianceCase):
    def test_every_passing_case_is_compliant(self):
        for rule in ("c1", "c2", "c3", "c4", "c5", "c6", "c7"):
            self.assert_compliant(f"compliance-{rule}-pass")

    def test_c1_requirement_without_obligation_or_exemption(self):
        self.assert_non_compliant("compliance-c1-fail", "C1 FR-001: no obligation and no exemption")

    def test_c1_missing_verification_plan(self):
        lines = self.assert_non_compliant("plan-no-section", only=False)
        self.assertIn(
            "PLAN plan.md: no Verification Plan section: a gap to resolve in planning, by the plan stage", lines
        )

    def test_c2_obligation_without_a_behaviour_task(self):
        self.assert_non_compliant(
            "compliance-c2-fail", "C2 VO-002: named by a test task (T013) but by no behaviour task"
        )

    def test_c3_behaviour_before_test(self):
        self.assert_non_compliant(
            "compliance-c3-fail",
            "C3 VO-002: its first task T012 is a behaviour task, so no test task comes before it",
            only=False,
        )

    def test_c4_hand_edited_record_row(self):
        self.assert_non_compliant(
            "compliance-c4-fail",
            "C4 #3: the check value does not match the row: the record was changed after it was written",
        )

    def test_c5_completed_task_that_fails_its_gate(self):
        self.assert_non_compliant("compliance-c5-fail", "C5 T012 #3: G9: command 'adhoc' is not declared in the plan")

    def test_c5_applies_every_gate_rule_to_completed_tasks(self):
        lines = self.assert_non_compliant("gate-all-fail", only=False)
        self.assertIn("C5 T014 VO-002: G3: no valid failing-first record and no exception", lines)
        self.assertIn("C5 T014 VO-002: G4: no valid passing record after its failing-first record", lines)

    def test_c6_no_checkpoint(self):
        self.assert_non_compliant("compliance-c6-fail-no-checkpoint", "C6 tdd-evidence.md: no checkpoint record")

    def test_c6_latest_checkpoint_failed_where_the_baseline_passed(self):
        self.assert_non_compliant(
            "compliance-c6-fail-checkpoint", "C6 #7: the latest checkpoint failed and the baseline of suite passed"
        )

    def test_c6_failing_checkpoint_is_accepted_when_pre_existing_and_reported(self):
        self.assert_compliant("compliance-c6-pass-preexisting")

    def test_c6_failing_checkpoint_not_reported_as_pre_existing(self):
        self.assert_non_compliant(
            "compliance-c6-fail-not-reported",
            "C6 #6: the latest checkpoint failed as the baseline of suite did, and the Summary does not report the "
            "failure as pre-existing",
            OUT_OF_DATE,
        )

    def test_c6_first_record_is_not_a_baseline(self):
        self.assert_non_compliant("compliance-c6-fail-first-record", "C6 #1: the first record is not a baseline")

    def test_c6_no_evidence_at_all(self):
        root = self.repo("compliance-c6-pass")
        os.remove(os.path.join(self.feature(root), "tdd-evidence.md"))
        result = self.check(["compliance"], root)
        self.assertEqual(result.code, 1)
        self.assertIn("C6 tdd-evidence.md: no baseline record", result.out.splitlines())

    def test_c7_planned_obligation_fails_however_it_is_reported(self):
        self.assert_non_compliant("compliance-c7-fail-planned", "C7 VO-002: status is planned")

    def test_c7_in_progress_obligation_fails_however_it_is_reported(self):
        self.assert_non_compliant("compliance-c7-fail-in-progress", "C7 VO-002: status is in progress")

    def test_c7_failed_obligation_reported_as_failed_is_compliant(self):
        self.assert_compliant("compliance-c7-pass-failed")

    def test_c7_failed_obligation_not_reported_in_the_summary(self):
        self.assert_non_compliant("compliance-c7-fail-failed-not-reported", OUT_OF_DATE)

    def test_c7_blocked_obligation_reported_as_blocked_is_compliant(self):
        self.assert_compliant("compliance-c7-pass-blocked")

    def test_c7_blocked_obligation_not_reported_in_the_summary(self):
        self.assert_non_compliant("compliance-c7-fail-blocked-not-reported", OUT_OF_DATE)

    def test_c7_summary_left_out_of_date_by_a_plan_change(self):
        self.assert_non_compliant("compliance-c7-fail-stale-plan", "C7 VO-003: status is planned", OUT_OF_DATE)

    def test_c7_a_recording_run_brings_the_summary_up_to_date(self):
        root = self.repo("compliance-c7-fail-stale-plan")
        self.assertIn(OUT_OF_DATE, self.check(["compliance"], root).out)
        recorded = self.check(["run", "--phase", "checkpoint", "--command", "suite"], root)
        self.assertEqual(recorded.code, 0, recorded)
        lines = self.check(["compliance"], root).out.splitlines()
        self.assertEqual(lines, ["NON-COMPLIANT", "C7 VO-003: status is planned"])


class ComplianceBehaviourTests(ComplianceCase):
    def test_json_carries_the_verdict_and_the_findings(self):
        data = json.loads(self.compliance("compliance-c1-fail", "--json").out)
        self.assertEqual(data["verdict"], "NON-COMPLIANT")
        self.assertEqual(data["exit_code"], 1)
        self.assertEqual(data["findings"][0]["rule"], "C1")
        data = json.loads(self.compliance("compliance-c1-pass", "--json").out)
        self.assertEqual((data["verdict"], data["exit_code"], data["findings"]), ("COMPLIANT", 0, []))

    def test_output_is_identical_on_two_runs(self):
        for fixture in ("compliance-c6-fail-not-reported", "compliance-c1-pass"):
            root = self.repo(fixture)
            first = self.check(["compliance"], root)
            second = self.check(["compliance"], root)
            self.assertEqual((first.code, first.out, first.err), (second.code, second.out, second.err))

    def test_compliance_writes_nothing(self):
        for fixture in ("compliance-c7-fail-stale-plan", "compliance-c1-pass"):
            root = self.repo(fixture)
            before = snapshot(root)
            self.check(["compliance"], root)
            self.assertEqual(snapshot(root), before)

    def test_missing_spec_is_a_usage_error(self):
        root = self.repo("compliance-c1-pass")
        os.remove(os.path.join(self.feature(root), "spec.md"))
        result = self.check(["compliance"], root)
        self.assertEqual(result.code, 2)
        self.assertIn("spec.md", result.err)


class NoToolingComplianceTests(ComplianceCase):
    """No test tooling gives notices, never a failure (FR-020, EC-04, EC-06, SC-003)."""

    NOTICES = [
        "notice: no test tooling is recorded: nothing is verified by tests",
        "notice: VO-001 deferred: no test tooling",
        "notice: VO-002 deferred: no test tooling",
    ]

    def test_a_complete_feature_is_compliant_with_notices_and_exit_0(self):
        result = self.compliance("no-tooling-complete")
        self.assertEqual((result.code, result.err), (0, ""), result)
        self.assertEqual(result.out.splitlines(), ["COMPLIANT"] + self.NOTICES)

    def test_every_obligation_deferred_with_an_evidence_document_is_compliant_and_c7_holds(self):
        result = self.compliance("no-tooling-all-deferred")
        self.assertEqual((result.code, result.out.splitlines()), (0, ["COMPLIANT"] + self.NOTICES), result)

    def test_json_carries_the_notices_and_the_verdict(self):
        data = json.loads(self.compliance("no-tooling-complete", "--json").out)
        self.assertEqual((data["verdict"], data["exit_code"], data["findings"]), ("COMPLIANT", 0, []))
        self.assertEqual([f"notice: {text}" for text in data["notices"]], self.NOTICES)

    def test_a_feature_with_a_command_has_no_notices_and_no_key(self):
        self.assert_compliant("compliance-c1-pass")
        self.assertNotIn("notices", json.loads(self.compliance("compliance-c1-pass", "--json").out))

    def test_a_baseline_beside_the_none_row_is_c9(self):
        result = self.compliance("no-tooling-with-runs")
        self.assertEqual(result.code, 1, result)
        self.assertEqual(
            result.out.splitlines(),
            [
                "NON-COMPLIANT",
                "C9 tdd-evidence.md: the plan records no test tooling but the evidence holds a baseline or runs",
            ]
            + self.NOTICES,
        )

    def test_a_declared_command_beside_the_none_row_is_c9_as_well_as_a_plan_finding(self):
        lines = self.compliance("no-tooling-with-command").out.splitlines()
        self.assertEqual(lines[0], "NON-COMPLIANT")
        self.assertIn(
            "PLAN None: the commands table records no test tooling and also declares a command: keep one", lines
        )
        self.assertIn("C9 plan.md: the plan records no test tooling and also declares a command", lines)

    def test_compliance_writes_nothing(self):
        for fixture in ("no-tooling-complete", "no-tooling-with-runs"):
            root = self.repo(fixture)
            before = snapshot(root)
            self.check(["compliance"], root)
            self.assertEqual(snapshot(root), before)


class RuleC8Tests(ComplianceCase):
    """C8: the checklist rules, and every item changed or removed without an accepted record."""

    def test_a_finished_feature_with_a_sound_checklist_is_compliant(self):
        self.assert_compliant("compliance-c8-pass")

    def test_a_missing_checklist_is_reported(self):
        self.assert_non_compliant(
            "compliance-c8-missing-checklist",
            "C8 tests/behaviour-checklist.md: CHECKLIST: the file does not exist or cannot be read",
            only=False,
        )

    def test_a_failing_checklist_rule_is_reported_with_its_rule_id(self):
        self.assert_non_compliant(
            "compliance-c8-rule-fails", "C8 FR-003: B1: no behaviour item expresses it", only=False
        )

    def test_an_item_changed_without_a_record_is_reported(self):
        self.assert_non_compliant(
            "compliance-c8-unrecorded-change",
            "C8 BI-002: changed since the baseline and no change is recorded",
            only=False,
        )

    def test_a_reused_id_is_reported(self):
        self.assert_non_compliant(
            "compliance-c8-id-reused", "C8 BI-004: removed since the baseline and its id is reused", only=False
        )

    def test_a_stored_summary_that_shows_an_item_verified_without_the_records_is_out_of_date(self):
        self.assert_non_compliant("compliance-c7-item-stale", OUT_OF_DATE, only=False)

    def test_an_accepted_change_record_clears_the_finding(self):
        for fixture in ("item-change-recorded", "item-change-approved", "item-removal-recorded"):
            with self.subTest(fixture=fixture):
                lines = self.compliance(fixture).out.splitlines()
                self.assertFalse([line for line in lines if line.startswith("C8 ")], lines)

    def test_a_change_awaiting_approval_is_reported(self):
        lines = self.compliance("item-change-awaiting-approval").out.splitlines()
        self.assertIn("C8 BI-002: change BX-01 alters behaviour and awaits approval", lines)

    def test_a_feature_without_a_checklist_gets_no_c8_finding(self):
        lines = self.compliance("compliance-c1-pass").out.splitlines()
        self.assertEqual(lines, ["COMPLIANT"])

    def test_compliance_writes_nothing_for_a_feature_with_items(self):
        root = self.repo("compliance-c8-unrecorded-change")
        before = snapshot(root)
        self.check(["compliance"], root)
        self.assertEqual(snapshot(root), before)


class ExampleRunTests(unittest.TestCase):
    """The two artefact sets shipped for evaluation (FR-057, SC-011)."""

    def require(self, feature_dir):
        """The run's artefacts must be there. An empty directory is not a run: git does not track one."""
        for name in ("spec.md", "plan.md", "tasks.md"):
            if not os.path.isfile(os.path.join(REPO, feature_dir, name)):
                raise AssertionError(f"missing example run artefact: {feature_dir}/{name}")
        found = [
            os.path.join(REPO, feature_dir, *parts) for parts in (["tdd-evidence.md"], ["tests", "tdd-evidence.md"])
        ]
        if not any(os.path.isfile(path) for path in found):
            raise AssertionError(f"missing example run artefact: {feature_dir}/tdd-evidence.md")

    def run_on(self, feature_dir):
        self.require(feature_dir)
        return run_check(["compliance", "--feature-dir", feature_dir], REPO)

    def test_the_run_that_followed_the_process_is_compliant(self):
        result = self.run_on(COMPLIANT_RUN)
        self.assertEqual((result.code, result.out), (0, "COMPLIANT\n"), result)

    def test_the_run_that_only_added_tests_is_non_compliant(self):
        result = self.run_on(TESTS_ONLY_RUN)
        self.assertEqual(result.code, 1, result)
        lines = result.out.splitlines()
        self.assertEqual(lines[0], "NON-COMPLIANT")
        self.assertTrue(any("G3: no valid failing-first record and no exception" in line for line in lines), lines)
        self.assertFalse(any(line.startswith("C4 ") for line in lines), lines)

    def test_the_compliant_run_keeps_its_checklist_and_evidence_in_tests(self):
        self.require(COMPLIANT_RUN)
        base = os.path.join(REPO, COMPLIANT_RUN)
        self.assertTrue(os.path.isfile(os.path.join(base, "tests", "behaviour-checklist.md")))
        self.assertTrue(os.path.isfile(os.path.join(base, "tests", "tdd-evidence.md")))
        self.assertFalse(os.path.exists(os.path.join(base, "tdd-evidence.md")))

    def test_the_frontend_example_passes_the_plan_check_and_has_a_scenario_section(self):
        base = os.path.join(REPO, FRONTEND_RUN)
        for name in ("spec.md", "plan.md", os.path.join("tests", "behaviour-checklist.md")):
            if not os.path.isfile(os.path.join(base, name)):
                raise AssertionError(f"missing example artefact: {FRONTEND_RUN}/{name}")
        result = run_check(["plan", "--feature-dir", FRONTEND_RUN], REPO)
        self.assertEqual((result.code, result.out), (0, "plan: passed\n"), result)
        with open(os.path.join(base, "tests", "behaviour-checklist.md")) as handle:
            sections = [line for line in handle if line.startswith("## US")]
        self.assertGreaterEqual(len(sections), 1)

    def test_story_08_exists_and_expects_b5_and_b1(self):
        path = os.path.join(REPO, "examples", "stories", "08-behaviours-from-the-code.md")
        if not os.path.isfile(path):
            raise AssertionError("missing story: examples/stories/08-behaviours-from-the-code.md")
        with open(path) as handle:
            text = handle.read()
        expected = text.split("## Expected behaviour", 1)[1]
        self.assertIn("B5", expected)
        self.assertIn("B1", expected)

    def test_two_runs_give_byte_identical_output(self):
        for feature_dir in (COMPLIANT_RUN, TESTS_ONLY_RUN):
            first = self.run_on(feature_dir)
            second = self.run_on(feature_dir)
            self.assertEqual((first.code, first.out, first.err), (second.code, second.out, second.err))

    def test_compliance_writes_nothing_to_the_example_runs(self):
        for feature_dir in (COMPLIANT_RUN, TESTS_ONLY_RUN):
            self.require(feature_dir)
            before = snapshot(os.path.join(REPO, feature_dir))
            self.run_on(feature_dir)
            self.assertEqual(snapshot(os.path.join(REPO, feature_dir)), before)


if __name__ == "__main__":
    unittest.main()
