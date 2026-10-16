"""Derived obligation status and the Review Evidence view (data-model.md)."""

import json
import os
import unittest

from support import FEATURE_REL, RepoCase, RunCase, evidence_text, read, snapshot, write

HEADER = [
    "| Obligation | Requirements | Status | Tests | Latest result |",
    "|------------|--------------|--------|-------|---------------|",
]
REQS_1 = "FR-001, US1-AS1"
REQS_2 = "FR-002, US1-AS2, SC-001, DC-01, EC-01"
EXEMPT = "FR-003 (exempt: see plan)"
NONE_LINE = "**Open decisions**: none. **Exceptions**: none. **Expectation changes**: none."
NO_FAILURES = "**Pre-existing failures**: none."


def not_verified(*pairs):
    """The Not verified line for obligations that are not verified, as (number, status) pairs."""
    parts = []
    for number, status in pairs:
        requirements = REQS_1 if number == 1 else REQS_2
        parts.extend(f"{ident} (VO-00{number} {status})" for ident in requirements.split(", "))
    return "**Not verified**: " + ", ".join(parts + [EXEMPT]) + "."


def view(row_1, row_2, unverified, middle=NONE_LINE, failures=NO_FAILURES):
    rows = [f"| VO-001 | {REQS_1} | {row_1} |", f"| VO-002 | {REQS_2} | {row_2} |"]
    return "\n".join(HEADER + rows + ["", unverified, "", middle, "", failures]) + "\n"


def summary_body(text):
    """The stored Summary below its generated-on line."""
    section = text.split("## Summary\n\n", 1)[1].split("\n## Baseline", 1)[0]
    first, _blank, rest = section.partition("\n\n")
    if not first.startswith("_Generated from the tables below on "):
        raise AssertionError("the Summary has no generated-on line")
    return rest


class StatusCase(RepoCase):
    def status(self, fixture, *extra):
        root = self.repo(fixture)
        return self.check(["status"] + list(extra), root)

    def assert_view(self, fixture, expected):
        result = self.status(fixture)
        self.assertEqual((result.code, result.err), (0, ""), result)
        self.assertEqual(result.out, expected)


class DerivedStatusTests(StatusCase):
    """Each fixture gives the status of the data model's table."""

    def test_planned(self):
        self.assert_view(
            "status-planned",
            view("planned | - | -", "planned | - | -", not_verified((1, "planned"), (2, "planned"))),
        )

    def test_in_progress(self):
        self.assert_view(
            "status-in-progress",
            view(
                "in progress | assert | fail (#2)",
                "planned | - | -",
                not_verified((1, "in progress"), (2, "planned")),
            ),
        )

    def test_verified(self):
        self.assert_view(
            "status-verified",
            view("verified | assert, pass | pass (#3)", "planned | - | -", not_verified((2, "planned"))),
        )

    def test_verified_by_exception(self):
        self.assert_view(
            "status-verified-by-exception",
            view(
                "verified | assert, pass | pass (#3)",
                "verified | pass | pass (#4)",
                not_verified(),
                "**Open decisions**: none. **Exceptions**: EX-01 legacy on T013 for VO-002 (approved by Lee Sinclair). "
                "**Expectation changes**: none.",
            ),
        )

    def test_an_exception_awaiting_approval_does_not_verify(self):
        result = self.status("gate-g7-fail-flagged")
        self.assertIn(f"| VO-002 | {REQS_2} | in progress | pass | pass (#2) |", result.out.splitlines())
        self.assertIn("**Exceptions**: EX-01 migration on T013 for VO-002 (awaiting approval).", result.out)

    def test_blocked_by_an_environment_failure(self):
        self.assert_view(
            "status-blocked-environment",
            view(
                "verified | assert, pass | pass (#3)",
                "blocked | assert, import | fail (#5)",
                not_verified((2, "blocked")),
            ),
        )

    def test_blocked_by_an_environment_blocked_exception(self):
        result = self.status("gate-exception-blocked")
        self.assertIn(f"| VO-002 | {REQS_2} | blocked | pass | pass (#2) |", result.out.splitlines())

    def test_blocked_by_an_open_decision(self):
        self.assert_view(
            "status-blocked-decision",
            view(
                "verified | assert, pass | pass (#3)",
                "blocked | assert | fail (#4)",
                not_verified((2, "blocked")),
                "**Open decisions**: DN-01 holds T014 (Should an empty cart raise or return zero?). "
                "**Exceptions**: none. **Expectation changes**: none.",
            ),
        )

    def test_failed(self):
        self.assert_view(
            "status-failed",
            view("failed | assert | fail (#3)", "planned | - | -", not_verified((1, "failed"), (2, "planned"))),
        )

    def test_pre_existing_failures_and_expectation_changes_are_listed(self):
        self.assert_view(
            "status-preexisting-failure",
            view(
                "verified | assert, pass | pass (#3)",
                "verified | assert, pass | pass (#5)",
                not_verified(),
                "**Open decisions**: none. **Exceptions**: none. **Expectation changes**: XC-01 on T012 for FR-001, "
                "alters behaviour (approved by Lee Sinclair).",
                "**Pre-existing failures**: #1 suite: test_old_total fails.",
            ),
        )

    def test_an_unrecorded_test_change_is_not_verified(self):
        result = self.status("gate-g5-fail")
        self.assertIn(f"| VO-001 | {REQS_1} | in progress | assert, pass | pass (#3) |", result.out.splitlines())

    def test_a_passing_run_with_no_failing_first_record_is_not_verified(self):
        result = self.status("gate-g5-no-red")
        self.assertIn(f"| VO-001 | {REQS_1} | in progress | pass | pass (#2) |", result.out.splitlines())

    def test_unreliable_records_count_in_neither_direction(self):
        result = self.status("gate-unreliable")
        self.assertIn(f"| VO-001 | {REQS_1} | planned | assert | fail (#3) |", result.out.splitlines())

    def test_a_failure_after_verification_is_failed(self):
        result = self.status("gate-g6-fail-latest")
        self.assertIn(f"| VO-001 | {REQS_1} | failed | assert, pass | fail (#4) |", result.out.splitlines())

    def test_a_new_failing_first_record_after_verification_is_in_progress(self):
        root = self.repo("status-verified")
        text = read(self.feature(root), "tdd-evidence.md")
        self.assertIn("| 3 | 2026-10-10T13:03:00Z | T012 | VO-001 | green |", text)
        text = text.replace("| T012 | VO-001 | green |", "| T011 | VO-001 | red |")
        write(self.feature(root), ["tdd-evidence.md"], text)
        row = self.check(["status"], root).out.splitlines()[2]
        self.assertTrue(row.startswith(f"| VO-001 | {REQS_1} | in progress |"), row)

    def test_a_discovered_obligation_is_shown_like_any_other(self):
        root = self.repo("status-verified")
        plan = read(self.feature(root), "plan.md").replace(
            "\n### Verification exemptions",
            "| VO-003 | EC-02 | A cart of 10,000 items is totalled | The total is returned | unit | discovered |\n"
            "\n### Verification exemptions",
        )
        write(self.feature(root), ["plan.md"], plan)
        result = self.check(["status"], root)
        self.assertIn("| VO-003 | EC-02 | planned | - | - |", result.out.splitlines())
        self.assertIn("EC-02 (VO-003 planned)", result.out)

    def test_a_requirement_with_several_obligations_names_those_not_verified(self):
        root = self.repo("status-verified")
        plan = read(self.feature(root), "plan.md").replace("| VO-002 | FR-002,", "| VO-002 | FR-001, FR-002,")
        write(self.feature(root), ["plan.md"], plan)
        result = self.check(["status"], root)
        self.assertIn("**Not verified**: FR-001 (VO-002 planned), FR-002 (VO-002 planned)", result.out)


class StatusBehaviourTests(StatusCase):
    def test_status_exits_0_whatever_the_state(self):
        for fixture in ("status-planned", "status-failed", "gate-all-fail", "status-blocked-decision"):
            self.assertEqual(self.status(fixture).code, 0, fixture)

    def test_status_with_no_evidence_document(self):
        root = self.repo("status-planned")
        os.remove(os.path.join(self.feature(root), "tdd-evidence.md"))
        result = self.check(["status"], root)
        self.assertEqual(result.code, 0)
        self.assertIn(f"| VO-001 | {REQS_1} | planned | - | - |", result.out)

    def test_status_cannot_read_a_feature_outside_the_process(self):
        result = self.status("plan-no-section")
        self.assertEqual(result.code, 2)
        self.assertIn("no Verification Plan", result.err)

    def test_status_cannot_read_malformed_evidence(self):
        result = self.status("parse-evidence-wrong-header")
        self.assertEqual(result.code, 2)
        self.assertIn("tdd-evidence.md", result.err)

    def test_json_carries_the_same_content(self):
        data = json.loads(self.status("status-blocked-decision", "--json").out)
        self.assertEqual(data["exit_code"], 0)
        self.assertEqual(
            data["obligations"],
            [
                {
                    "id": "VO-001",
                    "requirements": ["FR-001", "US1-AS1"],
                    "status": "verified",
                    "tests": ["assert", "pass"],
                    "latest_result": "pass (#3)",
                },
                {
                    "id": "VO-002",
                    "requirements": ["FR-002", "US1-AS2", "SC-001", "DC-01", "EC-01"],
                    "status": "blocked",
                    "tests": ["assert"],
                    "latest_result": "fail (#4)",
                },
            ],
        )
        self.assertEqual(data["not_verified"][0], {"requirement": "FR-002", "reason": "VO-002 blocked"})
        self.assertEqual(data["not_verified"][-1], {"requirement": "FR-003", "reason": "exempt: see plan"})
        self.assertEqual(data["open_decisions"], ["DN-01 holds T014 (Should an empty cart raise or return zero?)"])
        self.assertEqual(data["exceptions"], [])
        self.assertEqual(data["expectation_changes"], [])
        self.assertEqual(data["pre_existing_failures"], [])

    def test_output_is_identical_on_two_runs(self):
        root = self.repo("status-preexisting-failure")
        first = self.check(["status"], root)
        second = self.check(["status"], root)
        self.assertEqual((first.code, first.out, first.err), (second.code, second.out, second.err))
        self.assertTrue(first.out)

    def test_status_creates_or_changes_no_file(self):
        root = self.repo("status-preexisting-failure")
        before = snapshot(root)
        self.check(["status"], root)
        self.check(["status", "--json"], root)
        self.assertEqual(snapshot(root), before)

    def test_status_needs_only_the_plan_the_tasks_and_the_evidence(self):
        """The view holds nothing that is not derivable from the tables and plan.md."""
        root = self.repo("status-preexisting-failure")
        expected = self.check(["status"], root).out
        os.remove(os.path.join(self.feature(root), "spec.md"))
        self.assertEqual(self.check(["status"], root).out, expected)

    def test_the_stored_summary_of_valid_minimal_is_the_view(self):
        root = self.repo("valid-minimal")
        self.assertEqual(summary_body(read(self.feature(root), "tdd-evidence.md")), self.check(["status"], root).out)


class SummaryWriterTests(RunCase):
    """After any recording subcommand the Summary shows what status shows."""

    def assert_summary_is_the_view(self):
        expected = self.check(["status"], self.root)
        self.assertEqual(expected.code, 0, expected)
        self.assertTrue(expected.out.startswith(HEADER[0]), expected.out)
        self.assertEqual(summary_body(evidence_text(self.root)), expected.out)

    def test_summary_after_each_run(self):
        self.baseline()
        self.assert_summary_is_the_view()
        self.red()
        self.assert_summary_is_the_view()
        self.assertIn(f"| VO-001 | {REQS_1} | in progress | assert | fail (#2) |", evidence_text(self.root))
        self.green()
        self.assert_summary_is_the_view()
        self.assertIn(f"| VO-001 | {REQS_1} | verified | assert, pass | pass (#3) |", evidence_text(self.root))

    def test_summary_after_the_other_recording_subcommands(self):
        self.baseline()
        self.check(["decision", "open", "--question", "Raise or return zero?", "--tasks", "T014"], self.root)
        self.assert_summary_is_the_view()
        self.assertIn("**Open decisions**: DN-01 holds T014 (Raise or return zero?).", evidence_text(self.root))
        self.check(
            ["exception", "--task", "T013", "--vo", "VO-002", "--kind", "legacy", "--rationale", "No seam",
             "--alternative", "Characterisation run"],
            self.root,
        )  # fmt: skip
        self.assert_summary_is_the_view()
        self.assertIn("EX-01 legacy on T013 for VO-002 (awaiting approval)", evidence_text(self.root))
        self.check(["approve", "--id", "EX-01", "--by", "Lee"], self.root)
        self.assert_summary_is_the_view()
        self.assertIn("EX-01 legacy on T013 for VO-002 (approved by Lee)", evidence_text(self.root))

    def test_summary_follows_the_plan_at_the_next_write(self):
        self.baseline()
        plan = read(self.root, FEATURE_REL, "plan.md").replace(
            "\n### Verification exemptions",
            "| VO-003 | EC-02 | A very large cart is totalled | The total is returned | unit | discovered |\n"
            "\n### Verification exemptions",
        )
        write(self.root, [FEATURE_REL, "plan.md"], plan)
        self.assertNotIn("VO-003", evidence_text(self.root))
        self.red()
        self.assertIn("| VO-003 | EC-02 | planned | - | - |", evidence_text(self.root))
        self.assert_summary_is_the_view()


SCENARIOS_VIEW = """US1-AS1
  > **Given** an empty cart, **When** it is totalled, **Then** the total is zero.
  BI-001 | Expresses: FR-001, US1-AS1 | Verified by: VO-001
    Given an empty cart
    When the shopper asks for the total
    Then the total is zero

US1-AS2
  > **Given** a cart with two items, **When** it is totalled, **Then** the total is their sum.
  BI-002 | Expresses: FR-002, US1-AS2, SC-001 | Verified by: VO-002
    Given a cart with two items priced 3 and 4
    When the shopper asks for the total
    Then the total is 7

Other behaviours
  BI-003 | Expresses: FR-003 | Verified by: exemption FR-003
    Given the cart page is shown
    When the shopper looks at it
    Then it follows the shop's visual layout
"""


class ScenariosViewTests(RepoCase):
    """``status --scenarios`` puts the specification's wording beside the items (FR-017)."""

    def test_each_scenario_section_prints_its_quote_above_its_items_then_the_other_behaviours(self):
        root = self.repo("checklist-valid")
        result = self.check(["status", "--scenarios"], root)
        self.assertEqual((result.code, result.err), (0, ""))
        self.assertEqual(result.out, SCENARIOS_VIEW)

    def test_it_needs_no_evidence(self):
        root = self.repo("checklist-valid")
        os.remove(os.path.join(self.feature(root), "tdd-evidence.md"))
        before = snapshot(root)
        result = self.check(["status", "--scenarios"], root)
        self.assertEqual((result.code, result.out), (0, SCENARIOS_VIEW))
        self.assertEqual(snapshot(root), before)

    def test_the_option_is_accepted_with_json_and_carries_the_sections(self):
        root = self.repo("checklist-valid")
        result = self.check(["status", "--scenarios", "--json"], root)
        self.assertEqual(result.code, 0, result)
        data = json.loads(result.out)
        self.assertEqual([item["heading"] for item in data["scenarios"]], ["US1-AS1", "US1-AS2", "Other behaviours"])
        self.assertEqual(data["scenarios"][0]["items"][0]["id"], "BI-001")

    def test_the_view_without_the_option_is_unchanged(self):
        root = self.repo("checklist-valid")
        plain = self.check(["status"], root)
        self.assertEqual(plain.code, 0)
        self.assertNotIn("US1-AS1\n  >", plain.out)

    def test_an_older_feature_prints_exactly_what_status_prints(self):
        root = self.repo("valid-minimal")
        plain = self.check(["status"], root)
        scenarios = self.check(["status", "--scenarios"], root)
        self.assertEqual((scenarios.code, scenarios.out, scenarios.err), (plain.code, plain.out, plain.err))

    def test_a_missing_checklist_is_a_usage_error(self):
        root = self.repo("checklist-missing")
        result = self.check(["status", "--scenarios"], root)
        self.assertEqual(result.code, 2, result)
        self.assertIn("cannot read tests/behaviour-checklist.md", result.err)


if __name__ == "__main__":
    unittest.main()
