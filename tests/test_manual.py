"""The Manual verification table of the plan: rules M1 and M2 (data-model.md, research D6)."""

import json
import os
import re
import unittest

from fixtures.make_features import MANUAL_RESULT_CHAINED, check_over
from support import RepoCase, read, snapshot, table_rows, write

TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


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


class ManualCommandTests(RepoCase):
    """The manual subcommand records a person's result and never blocks anything (FR-016)."""

    def setUp(self):
        self.root = self.repo("manual-open")

    def manual(self, *args):
        return self.check(["manual"] + list(args), self.root)

    def record(self, check="MV-001", result="pass", by="A Person", *extra):
        return self.manual("--check", check, "--result", result, "--by", by, *extra)

    def rows(self):
        return table_rows(read(self.feature(self.root), "tdd-evidence.md"), "## Manual results")

    def test_a_result_is_recorded_under_a_name(self):
        result = self.record()
        self.assertEqual((result.code, result.out, result.err), (0, "recorded MR-01: MV-001 pass by A Person\n", ""))
        row = self.rows()[0]
        self.assertEqual(
            (row["ID"], row["Check"], row["Result"], row["Recorded by"], row["Note"]),
            ("MR-01", "MV-001", "pass", "A Person", "-"),
        )
        self.assertRegex(row["Time"], TIME)

    def test_a_note_is_stored(self):
        self.record("MV-001", "fail", "A Person", "--note", "the header | overlaps")
        self.assertEqual(self.rows()[0]["Note"], "the header overlaps")

    def test_each_result_is_a_new_row_in_a_chain_of_its_own(self):
        self.record("MV-001", "fail")
        self.record("MV-001", "pass")
        rows = self.rows()
        self.assertEqual([row["ID"] for row in rows], ["MR-01", "MR-02"])
        previous = ""
        for row in rows:
            self.assertEqual(row["Check value"], check_over(previous, row, MANUAL_RESULT_CHAINED))
            previous = row["Check value"]

    def test_the_latest_result_for_a_check_is_its_state(self):
        self.record("MV-001", "fail")
        self.assertIn("- MV-001 manual: fail by A Person", self.check(["status"], self.root).out.splitlines())
        self.record("MV-001", "pass", "Someone Else")
        self.assertIn("- MV-001 manual: pass by Someone Else", self.check(["status"], self.root).out.splitlines())

    def test_json_carries_the_same_data(self):
        data = json.loads(self.manual("--check", "MV-001", "--result", "fail", "--by", "A Person", "--json").out)
        self.assertEqual(
            (data["exit_code"], data["id"], data["check"], data["result"], data["recorded_by"]),
            (0, "MR-01", "MV-001", "fail", "A Person"),
        )

    def test_an_unknown_check_is_refused_and_nothing_is_recorded(self):
        before = snapshot(self.root)
        result = self.record("MV-099")
        self.assertEqual(result.code, 2, result)
        self.assertIn("manual check MV-099 is not in the plan; nothing was recorded", result.err)
        self.assertEqual(snapshot(self.root), before)

    def test_a_result_other_than_pass_or_fail_is_refused_and_nothing_is_recorded(self):
        before = snapshot(self.root)
        result = self.record("MV-001", "maybe")
        self.assertEqual(result.code, 2, result)
        self.assertIn("invalid choice", result.err)
        self.assertEqual(snapshot(self.root), before)

    def test_an_empty_name_is_refused_and_nothing_is_recorded(self):
        for name in ("", "   ", "-"):
            with self.subTest(name=name):
                before = snapshot(self.root)
                result = self.record("MV-001", "pass", name)
                self.assertEqual(result.code, 2, result)
                self.assertIn("--by must name the person who did the check; nothing was recorded", result.err)
                self.assertEqual(snapshot(self.root), before)

    def test_a_feature_with_no_verification_plan_is_refused(self):
        root = self.repo("plan-no-section")
        result = self.check(["manual", "--check", "MV-001", "--result", "pass", "--by", "A Person"], root)
        self.assertEqual(result.code, 2, result)
        self.assertIn("no Verification Plan", result.err)

    def test_the_first_result_creates_the_table_and_no_gate_needs_it(self):
        self.assertNotIn("## Manual results", read(self.feature(self.root), "tdd-evidence.md"))
        self.assertEqual(self.check(["gate", "--all"], self.root).code, 0)
        self.record()
        self.assertIn("## Manual results", read(self.feature(self.root), "tdd-evidence.md").splitlines())
        self.assertEqual(self.check(["gate", "--all"], self.root).code, 0)

    def test_a_result_is_recorded_in_no_tooling_mode_too(self):
        root = self.repo("no-tooling-complete")
        plan = os.path.join(self.feature(root), "plan.md")
        with open(plan) as handle:
            text = handle.read()
        table = (
            "\n### Manual verification\n\n| ID | Covers | Steps | Expected result | Why not automated |\n"
            "|----|--------|-------|-----------------|-------------------|\n"
            "| MV-001 | FR-003 | Look at it | It matches | Visual |\n"
        )
        with open(plan, "w") as handle:
            handle.write(text.replace("\n## Project Structure", table + "\n## Project Structure"))
        result = self.check(["manual", "--check", "MV-001", "--result", "pass", "--by", "A Person"], root)
        self.assertEqual((result.code, result.out), (0, "recorded MR-01: MV-001 pass by A Person\n"), result)


if __name__ == "__main__":
    unittest.main()
