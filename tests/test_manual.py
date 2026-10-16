"""The Manual verification table of the plan: rules M1 and M2 (data-model.md, research D6)."""

import json
import unittest

from support import RepoCase, read, snapshot, write


class ManualPlanCase(RepoCase):
    def plan(self, fixture, *extra):
        root = self.repo(fixture)
        return self.check(["plan"] + list(extra), root)

    def assert_only_finding(self, fixture, finding):
        result = self.plan(fixture)
        self.assertEqual(result.code, 1, result)
        self.assertEqual(result.out.splitlines(), ["plan: failed, 1 finding", finding])


class RuleM1Tests(ManualPlanCase):
    def test_a_row_without_steps_is_reported(self):
        self.assert_only_finding("m1-missing-steps", "M1 MV-001: steps is empty")

    def test_a_row_without_an_expected_result_is_reported(self):
        self.assert_only_finding("m1-missing-expected", "M1 MV-001: expected result is empty")

    def test_a_row_without_a_reason_it_is_not_automated_is_reported(self):
        self.assert_only_finding("m1-missing-why", "M1 MV-001: why not automated is empty")

    def test_a_row_that_covers_nothing_is_reported(self):
        root = self.repo("manual-valid")
        plan = read(self.feature(root), "plan.md").replace("| MV-001 | FR-003 |", "| MV-001 | - |")
        write(self.feature(root), ["plan.md"], plan)
        result = self.check(["plan"], root)
        self.assertEqual(result.code, 1)
        self.assertEqual(result.out.splitlines(), ["plan: failed, 1 finding", "M1 MV-001: covers is empty"])

    def test_an_id_that_is_not_mv_and_three_digits_is_reported(self):
        self.assert_only_finding("m1-bad-id", "M1 MV-1: manual check id must be MV- and three or more digits")

    def test_a_duplicate_id_is_reported(self):
        self.assert_only_finding("m1-duplicate-id", "M1 MV-001: manual check id is used more than once")

    def test_every_missing_field_of_a_row_is_reported(self):
        root = self.repo("manual-valid")
        plan = read(self.feature(root), "plan.md")
        plan = plan.replace("| Open the cart page and compare it with the design |", "| - |", 1)
        plan = plan.replace("| The layout matches the design |", "| - |", 1)
        write(self.feature(root), ["plan.md"], plan)
        result = self.check(["plan"], root)
        self.assertEqual(
            result.out.splitlines(),
            ["plan: failed, 2 findings", "M1 MV-001: steps is empty", "M1 MV-001: expected result is empty"],
        )


class RuleM2Tests(ManualPlanCase):
    def test_a_requirement_the_specification_lacks_is_reported(self):
        self.assert_only_finding("m2-unknown-requirement", "M2 MV-001: covers FR-099 is not in spec.md")

    def test_an_obligation_the_plan_lacks_is_reported(self):
        self.assert_only_finding("m2-unknown-obligation", "M2 MV-001: covers VO-009 is not in the plan")

    def test_an_unknown_prefix_is_reported_as_for_an_obligation(self):
        root = self.repo("manual-valid")
        plan = read(self.feature(root), "plan.md").replace("| MV-001 | FR-003 |", "| MV-001 | XX-01 |")
        write(self.feature(root), ["plan.md"], plan)
        result = self.check(["plan"], root)
        self.assertEqual(
            result.out.splitlines(),
            [
                "plan: failed, 1 finding",
                "M2 MV-001: covers XX-01 has an unknown prefix (expected FR-, SC-, USn-ASm, DC- or EC-)",
            ],
        )

    def test_scenarios_design_constraints_and_edge_cases_are_accepted(self):
        root = self.repo("manual-valid")
        plan = read(self.feature(root), "plan.md").replace("| MV-001 | FR-003 |", "| MV-001 | US1-AS1, DC-01, EC-01 |")
        write(self.feature(root), ["plan.md"], plan)
        self.assertEqual(self.check(["plan"], root).code, 0)


class ValidManualTableTests(ManualPlanCase):
    def test_a_table_of_valid_rows_passes_even_for_a_requirement_that_is_also_exempted(self):
        result = self.plan("manual-valid")
        self.assertEqual((result.code, result.out, result.err), (0, "plan: passed\n", ""))

    def test_a_single_none_row_passes(self):
        result = self.plan("manual-none")
        self.assertEqual((result.code, result.out, result.err), (0, "plan: passed\n", ""))

    def test_a_plan_without_the_sub_heading_passes_and_says_nothing_about_it(self):
        result = self.plan("valid-minimal")
        self.assertEqual((result.code, result.out, result.err), (0, "plan: passed\n", ""))

    def test_a_wrong_header_is_one_finding_naming_the_heading(self):
        result = self.plan("parse-manual-wrong-header")
        lines = result.out.splitlines()
        self.assertEqual((result.code, lines[0]), (1, "plan: failed, 1 finding"))
        self.assertTrue(lines[1].startswith("PLAN plan.md: header row under '### Manual verification'"), lines)

    def test_the_rules_apply_in_no_tooling_mode(self):
        root = self.repo("no-tooling-valid")
        plan = read(self.feature(root), "plan.md")
        write(
            self.feature(root),
            ["plan.md"],
            plan.replace(
                "\n## Project Structure",
                "\n### Manual verification\n\n| ID | Covers | Steps | Expected result | Why not automated |\n"
                "|----|--------|-------|-----------------|-------------------|\n"
                "| MV-001 | FR-099 | Look | It is fine | Visual |\n\n## Project Structure",
            ),
        )
        result = self.check(["plan"], root)
        self.assertEqual(result.out.splitlines()[1:], ["M2 MV-001: covers FR-099 is not in spec.md"])

    def test_json_carries_the_findings(self):
        data = json.loads(self.plan("m1-missing-steps", "--json").out)
        self.assertEqual(data["findings"], [{"rule": "M1", "subject": "MV-001", "reason": "steps is empty"}])

    def test_compliance_reports_the_same_findings(self):
        root = self.repo("m2-unknown-requirement")
        result = self.check(["compliance"], root)
        self.assertEqual(result.code, 1)
        self.assertIn("M2 MV-001: covers FR-099 is not in spec.md", result.out.splitlines())

    def test_the_check_writes_nothing(self):
        root = self.repo("m1-bad-id")
        before = snapshot(root)
        self.check(["plan"], root)
        self.assertEqual(snapshot(root), before)


if __name__ == "__main__":
    unittest.main()
