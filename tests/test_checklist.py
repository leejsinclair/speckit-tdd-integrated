"""Rules CHECKLIST and B1 to B7 (contracts/behaviour-checklist.md section 4).

Each fixture gives exactly its findings, in the form ``<rule id> <subject>: <reason>``, with exit 1;
a passing fixture gives ``plan: passed``. The output is the same on ten consecutive runs (SC-002).
"""

import json
import os
import unittest

from support import FEATURE_REL, RepoCase, fixture_text, read

FILE = "tests/behaviour-checklist.md"
NO_ITEM = "no behaviour item expresses it"
NOT_NAMED = "no behaviour item names it in Verified by"
IN_SPEC = "which spec.md does not hold"
PREFIXES = "FR-, SC-, USn-ASm or EC-"


def line_of(case, text):
    """The 1-based line of ``text`` in the case's checklist."""
    lines = fixture_text(case, FILE).splitlines()
    return lines.index(text) + 1


def path_shaped(token):
    return f"B5 BI-001: `{token}` is a path-shaped token that spec.md does not name"


def code_shaped(token):
    return f"B5 BI-001: `{token}` is a code-shaped token that plan.md or tasks.md names and spec.md does not"


EXPECTED = {
    "checklist-by-file": [f"B1 FR-003: {NO_ITEM}"],
    "checklist-missing": [f"CHECKLIST {FILE}: the file does not exist or cannot be read"],
    "b1-fr": [f"B1 FR-003: {NO_ITEM}"],
    "b1-scenario": [f"B1 US1-AS2: {NO_ITEM}"],
    "b2-no-link": ["B2 BI-003: Verified by is empty"],
    "b2-unknown-vo": ["B2 BI-001: VO-099 is not in the Verification obligations table"],
    "b2-unknown-exemption": ["B2 BI-003: exemption FR-099 is not a row of the Verification exemptions table"],
    "b3-unnamed": [f"B3 VO-002: {NOT_NAMED}"],
    "b4-bad-id": ["B4 BI-1: the id must be BI- and three or more digits"],
    "b4-duplicate-id": ["B4 BI-001: the id is used more than once"],
    "b4-empty-expresses": [f"B1 FR-003: {NO_ITEM}", "B4 BI-003: the Expresses list is empty"],
    "b4-missing-then": ["B4 BI-002: Then is missing"],
    "b4-repeated-when": ["B4 BI-002: When is repeated"],
    "b4-out-of-order": [
        "B4 BI-002: When is out of order: Given, When, Then",
        "B4 BI-002: Given is out of order: Given, When, Then",
    ],
    "b4-outside-section": ["B4 BI-009: the item is outside a recognised section"],
    "b4-unknown-heading": [f"B4 line {line_of('b4-unknown-heading', '## Notes')}: 'Notes' is not a recognised section"],
    "b4-empty-section": [f"B1 US1-AS2: {NO_ITEM}", "B4 US1-AS2: the scenario section has no items"],
    "b4-checkbox": [
        f"B4 line {line_of('b4-checkbox', '- [ ] reviewed')}: a task-list checkbox: the checklist holds no status"
    ],
    "b4-status": [f"B4 line {line_of('b4-status', 'Status: draft')}: a status line: the checklist holds no status"],
    "b5-path": [path_shaped("src/cart.py")],
    "b5-identifier": [code_shaped("cart_total()")],
    "b5-backticked": [code_shaped("subtotal")],
    "b5-call-form": [code_shaped("item_count()")],
    "b6-unknown-fr": [f"B6 BI-001: Expresses FR-099, {IN_SPEC}"],
    "b6-unknown-ec": [f"B6 BI-001: Expresses EC-99, {IN_SPEC}"],
    "b6-unknown-prefix": [f"B6 BI-001: Expresses XY-001, which has no recognised prefix ({PREFIXES})"],
    "b6-unknown-section": ["B6 US9-AS9: the scenario is not in spec.md", f"B6 BI-004: Expresses US9-AS9, {IN_SPEC}"],
    "b6-duplicate-section": ["B6 US1-AS1: the scenario has more than one section"],
    "b6-no-quote": ["B6 US1-AS1: the section has no quote"],
    "b6-quote-differs": ["B6 US1-AS1: the quote differs from the scenario text in spec.md"],
    "b6-wrong-scenario": [
        f"B1 US1-AS1: {NO_ITEM}",
        "B6 BI-001: the item is in section US1-AS1 and does not name US1-AS1",
        "B6 BI-001: the item is in section US1-AS1 and names US1-AS2",
    ],
    "b6-two-scenarios": ["B6 BI-001: the item is in section US1-AS1 and names US1-AS2"],
    "b6-other-names-scenario": ["B6 BI-003: the item is in Other behaviours and names US1-AS1"],
    "checklist-and-plan-findings": [
        "PLAN VO-002: requirement FR-077 is not in spec.md",
        f"B1 FR-003: {NO_ITEM}",
    ],
}
PASSING = [
    "checklist-valid",
    "b5-spec-names-path",
    "b5-identifier-not-in-design",
    "b6-quote-emphasis-only",
    "b5-call-form-in-spec",
]
B7_CASE = "b7-untraced-test-task"
B7_FINDING = "B7 T011: names only obligations that no behaviour item names"


class PlanRuleTests(RepoCase):
    def plan(self, case, *extra):
        return self.check(["plan"] + list(extra), self.repo(case))

    def assert_findings(self, case):
        result = self.plan(case)
        expected = EXPECTED[case]
        noun = "finding" if len(expected) == 1 else "findings"
        self.assertEqual(result.code, 1, result)
        self.assertEqual(result.err, "")
        self.assertEqual(result.out.splitlines(), [f"plan: failed, {len(expected)} {noun}"] + expected)

    def test_every_failing_fixture_gives_exactly_its_findings(self):
        for case in sorted(EXPECTED):
            with self.subTest(case=case):
                self.assert_findings(case)

    def test_every_passing_fixture_passes(self):
        for case in PASSING:
            with self.subTest(case=case):
                result = self.plan(case)
                self.assertEqual((result.code, result.out, result.err), (0, "plan: passed\n", ""))

    def test_a_missing_checklist_gives_only_the_checklist_finding(self):
        result = self.plan("checklist-missing")
        self.assertEqual(result.out.splitlines()[1:], EXPECTED["checklist-missing"])

    def test_the_file_alone_switches_the_rules_on(self):
        self.assertEqual(self.plan("checklist-by-file").code, 1)

    def test_the_0_1_0_finding_is_listed_before_the_checklist_finding(self):
        found = self.plan("checklist-and-plan-findings").out.splitlines()[1:]
        self.assertTrue(found[0].startswith("PLAN "), found)
        self.assertTrue(found[1].startswith("B1 "), found)

    def test_json_carries_the_same_findings(self):
        result = self.plan("b6-wrong-scenario", "--json")
        data = json.loads(result.out)
        self.assertEqual(data["exit_code"], 1)
        shown = [f"{item['rule']} {item['subject']}: {item['reason']}" for item in data["findings"]]
        self.assertEqual(shown, EXPECTED["b6-wrong-scenario"])

    def test_a_feature_with_neither_marker_nor_file_gets_no_checklist_rule(self):
        self.assertEqual(self.plan("valid-minimal").out, "plan: passed\n")

    def test_b7_is_not_reported_by_plan(self):
        found = self.plan(B7_CASE).out.splitlines()[1:]
        self.assertEqual(found, [f"B3 VO-001: {NOT_NAMED}"])

    def test_the_checklist_is_not_written(self):
        root = self.repo("b6-wrong-scenario")
        parts = [FEATURE_REL, "tests", "behaviour-checklist.md"]
        before = read(root, *parts)
        self.check(["plan"], root)
        self.assertEqual(read(root, *parts), before)


class TasksRuleTests(RepoCase):
    def tasks(self, case):
        return self.check(["tasks"], self.repo(case))

    def test_an_untraced_test_task_is_reported(self):
        result = self.tasks(B7_CASE)
        self.assertEqual(result.code, 1, result)
        self.assertEqual(result.out.splitlines(), ["tasks: failed, 1 finding", B7_FINDING])

    def test_a_traced_feature_passes(self):
        result = self.tasks("checklist-valid")
        self.assertEqual((result.code, result.out), (0, "tasks: passed\n"))

    def test_a_missing_checklist_is_reported(self):
        result = self.tasks("checklist-missing")
        self.assertEqual(result.code, 1)
        self.assertEqual(result.out.splitlines()[1:], EXPECTED["checklist-missing"])

    def test_a_feature_with_neither_marker_nor_file_is_unchanged(self):
        self.assertEqual(self.tasks("valid-minimal").out, "tasks: passed\n")


class RepeatabilityTests(RepoCase):
    def test_every_fixture_gives_identical_output_on_ten_runs(self):
        cases = sorted(EXPECTED) + PASSING
        for case in cases:
            with self.subTest(case=case):
                root = self.repo(case)
                first = self.check(["plan"], root)
                for _run in range(9):
                    again = self.check(["plan"], root)
                    self.assertEqual((again.code, again.out, again.err), (first.code, first.out, first.err))

    def test_the_tasks_check_gives_identical_output_on_ten_runs(self):
        root = self.repo(B7_CASE)
        first = self.check(["tasks"], root)
        for _run in range(9):
            again = self.check(["tasks"], root)
            self.assertEqual((again.code, again.out), (first.code, first.out))


class ManualItemTests(RepoCase):
    """A behaviour item may name a manual check and is never verified by tests (FR-018, D8)."""

    ROW = "| BI-003 | - | MV-001 | {status} | - |"

    def run_in(self, fixture, args):
        root = self.repo(fixture)
        return root, self.check(args, root)

    def test_an_item_naming_a_manual_check_the_plan_holds_passes_b2(self):
        _root, result = self.run_in("manual-item", ["plan"])
        self.assertEqual((result.code, result.out), (0, "plan: passed\n"), result)

    def test_an_item_naming_a_manual_check_the_plan_lacks_is_a_b2_finding(self):
        _root, result = self.run_in("manual-item-unknown", ["plan"])
        self.assertEqual(result.code, 1, result)
        self.assertEqual(
            result.out.splitlines(),
            ["plan: failed, 1 finding", "B2 BI-003: MV-099 is not in the Manual verification table"],
        )

    def test_the_item_reads_manual_open_and_is_listed_as_not_verified_by_tests(self):
        _root, result = self.run_in("manual-item", ["status"])
        self.assertIn(self.ROW.format(status="manual (open)"), result.out.splitlines())
        self.assertIn("- MV-001 manual: open", result.out.splitlines())

    def test_the_item_shows_the_recorded_result_and_is_never_verified(self):
        root, _result = self.run_in("manual-item", ["status"])
        for outcome in ("pass", "fail"):
            self.check(["manual", "--check", "MV-001", "--result", outcome, "--by", "A Person"], root)
            out = self.check(["status"], root).out
            self.assertIn(self.ROW.format(status=f"manual ({outcome})"), out.splitlines())
            self.assertNotIn("| BI-003 | - | MV-001 | verified", out)

    def test_an_item_naming_an_obligation_and_a_manual_check_is_judged_on_the_obligation(self):
        root = self.repo("manual-item")
        path = os.path.join(self.feature(root), "tests", "behaviour-checklist.md")
        with open(path) as handle:
            text = handle.read()
        with open(path, "w") as handle:
            handle.write(text.replace("Verified by: MV-001.", "Verified by: VO-001, MV-001."))
        out = self.check(["status"], root).out
        self.assertIn("| BI-003 | - | VO-001, MV-001 | verified | assert, pass |", out.splitlines())


if __name__ == "__main__":
    unittest.main()
