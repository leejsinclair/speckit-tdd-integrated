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


class NoToolingStatusTests(StatusCase):
    """While the plan records no test tooling every obligation is deferred for that reason (FR-006, FR-012)."""

    EXPECTED = [
        *HEADER,
        f"| VO-001 | {REQS_1} | deferred | - | - |",
        f"| VO-002 | {REQS_2} | deferred | - | - |",
        "",
        "No test tooling: nothing is verified by tests",
        "",
        "Not verified by tests",
        "",
        "- VO-001 deferred: no test tooling",
        "- VO-002 deferred: no test tooling",
        "",
        "Counts: verified 0, deferred 2",
        "",
        not_verified((1, "deferred"), (2, "deferred")),
        "",
        NONE_LINE,
        "",
        NO_FAILURES,
    ]

    def test_the_view_states_the_no_tooling_state_the_reason_and_the_counts(self):
        self.assert_view("no-tooling-complete", "\n".join(self.EXPECTED) + "\n")

    def test_no_obligation_is_shown_as_verified(self):
        out = self.status("no-tooling-complete").out
        rows = [line for line in out.splitlines() if line.startswith("| VO-")]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertIn("| deferred |", row)
        self.assertNotIn("verified |", out)

    def test_the_stored_summary_is_the_view(self):
        root = self.repo("no-tooling-all-deferred")
        self.assertEqual(summary_body(read(self.feature(root), "tdd-evidence.md")), self.check(["status"], root).out)

    def test_json_carries_the_same_content(self):
        data = json.loads(self.status("no-tooling-complete", "--json").out)
        self.assertEqual((data["exit_code"], data["no_tooling"]), (0, True))
        self.assertEqual([row["status"] for row in data["obligations"]], ["deferred", "deferred"])
        self.assertEqual(
            data["not_verified_by_tests"],
            [
                {"id": "VO-001", "state": "deferred", "reason": "no test tooling"},
                {"id": "VO-002", "state": "deferred", "reason": "no test tooling"},
            ],
        )
        self.assertEqual(data["counts"], {"verified": 0, "deferred": 2})

    def test_a_plan_with_commands_has_none_of_the_added_lines_or_keys(self):
        result = self.status("valid-minimal")
        for words in ("No test tooling", "Not verified by tests", "Counts:"):
            self.assertNotIn(words, result.out)
        data = json.loads(self.status("valid-minimal", "--json").out)
        for key in ("no_tooling", "not_verified_by_tests", "counts"):
            self.assertNotIn(key, data)

    def test_a_deferred_obligation_does_not_appear_as_open_work_on_a_feature_with_runs(self):
        # The recorded baseline does not change the state: nothing is verified by tests.
        out = self.status("no-tooling-with-runs").out
        self.assertIn("Counts: verified 0, deferred 2", out.splitlines())

    def test_status_writes_nothing(self):
        root = self.repo("no-tooling-complete")
        before = snapshot(root)
        self.check(["status"], root)
        self.check(["status", "--json"], root)
        self.assertEqual(snapshot(root), before)


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


ITEM_HEADER = [
    "| Behaviour item | Scenario | Obligations | Status | Tests |",
    "|----------------|----------|-------------|--------|-------|",
]
ITEM_NONE = "**Item changes**: none."


def item_view(row_1, row_2, items, unverified, extra_unverified=(), middle=NONE_LINE, changes=ITEM_NONE,
              failures=NO_FAILURES):  # fmt: skip
    """The Review Evidence view of a feature with a behaviour checklist, built from its parts."""
    rows = [f"| VO-001 | {REQS_1} | {row_1} |", f"| VO-002 | {REQS_2} | {row_2} |"]
    line = unverified[:-1] + "".join(", " + entry for entry in extra_unverified) + "."
    lines = HEADER + rows + [""] + ITEM_HEADER + [f"| {entry} |" for entry in items]
    return "\n".join(lines + ["", line, "", middle, "", changes, "", failures]) + "\n"


class ItemViewTests(RepoCase):
    def status(self, case, *args):
        return self.check(["status", *args], self.repo(case))

    def assert_view(self, case, expected):
        result = self.status(case)
        self.assertEqual((result.code, result.err), (0, ""))
        self.assertEqual(result.out, expected)

    def test_every_item_verified(self):
        self.assert_view(
            "items-status-verified",
            item_view(
                "verified | assert, pass | pass (#3)", "verified | assert, pass | pass (#5)",
                ["BI-001 | US1-AS1 | VO-001 | verified | assert, pass",
                 "BI-002 | US1-AS2 | VO-002 | verified | assert, pass",
                 "BI-003 | - | exemption FR-003 | exempt | -",
                 "BI-004 | - | VO-002 | verified | assert, pass",
                 "BI-005 | - | VO-001, VO-002 | verified | assert, pass"],
                not_verified(),
            ),
        )  # fmt: skip

    def test_one_obligation_verified_and_one_planned_leaves_no_item_verified_that_names_both(self):
        self.assert_view(
            "items-status-partial",
            item_view(
                "verified | assert, pass | pass (#3)", "planned | - | -",
                ["BI-001 | US1-AS1 | VO-001 | verified | assert, pass",
                 "BI-002 | US1-AS2 | VO-002 | planned | -",
                 "BI-003 | - | exemption FR-003 | exempt | -",
                 "BI-004 | - | VO-002 | planned | -",
                 "BI-005 | - | VO-001, VO-002 | in progress | assert, pass"],
                not_verified((2, "planned")),
                ["BI-002 (planned)", "BI-004 (planned)", "BI-005 (in progress)"],
            ),
        )  # fmt: skip

    def test_an_item_that_names_exemptions_only_is_exempt_and_the_rest_are_planned(self):
        result = self.status("items-status-exempt")
        lines = result.out.splitlines()
        self.assertIn("| BI-003 | - | exemption FR-003 | exempt | - |", lines)
        self.assertIn("| BI-001 | US1-AS1 | VO-001 | planned | - |", lines)
        self.assertNotIn("BI-003 (", result.out.split("**Not verified**")[1].split("\n")[0])

    def test_a_failed_obligation_fails_every_item_that_names_it(self):
        self.assert_view(
            "items-status-failed",
            item_view(
                "failed | assert | fail (#3)", "planned | - | -",
                ["BI-001 | US1-AS1 | VO-001 | failed | assert",
                 "BI-002 | US1-AS2 | VO-002 | planned | -",
                 "BI-003 | - | exemption FR-003 | exempt | -",
                 "BI-004 | - | VO-002 | planned | -",
                 "BI-005 | - | VO-001, VO-002 | failed | assert"],
                not_verified((1, "failed"), (2, "planned")),
                ["BI-001 (failed)", "BI-002 (planned)", "BI-004 (planned)", "BI-005 (failed)"],
            ),
        )  # fmt: skip

    def test_a_blocked_obligation_blocks_every_item_that_names_it(self):
        self.assert_view(
            "items-status-blocked",
            item_view(
                "verified | assert, pass | pass (#3)", "blocked | assert | fail (#4)",
                ["BI-001 | US1-AS1 | VO-001 | verified | assert, pass",
                 "BI-002 | US1-AS2 | VO-002 | blocked | assert",
                 "BI-003 | - | exemption FR-003 | exempt | -",
                 "BI-004 | - | VO-002 | blocked | assert",
                 "BI-005 | - | VO-001, VO-002 | blocked | assert, pass"],
                not_verified((2, "blocked")),
                ["BI-002 (blocked)", "BI-004 (blocked)", "BI-005 (blocked)"],
                "**Open decisions**: DN-01 holds T014 (Should an empty cart raise or return zero?). "
                "**Exceptions**: none. **Expectation changes**: none.",
            ),
        )  # fmt: skip

    def test_an_item_with_obligations_and_an_exemption_is_judged_on_the_obligations(self):
        result = self.status("items-status-mixed-exemption")
        self.assertIn(
            "| BI-006 | - | VO-001, exemption FR-003 | verified | assert, pass |", result.out.splitlines()
        )

    def test_no_item_is_verified_while_an_obligation_it_names_is_not(self):
        for case in ("items-status-partial", "items-status-failed", "items-status-blocked", "items-status-exempt"):
            with self.subTest(case=case):
                rows = [line for line in self.status(case).out.splitlines() if line.startswith("| BI-005 |")]
                self.assertEqual(len(rows), 1)
                self.assertNotIn("| verified |", rows[0])

    def test_item_changes_are_listed_with_their_state(self):
        expected = {
            "items-baseline": "**Item changes**: none.",
            "item-changed": "**Item changes**: BI-002 changed, not recorded.",
            "item-removed": "**Item changes**: BI-004 removed, not recorded.",
            "item-change-recorded": "**Item changes**: BX-01 on BI-002 (recorded).",
            "item-change-awaiting-approval": "**Item changes**: BX-01 on BI-002, alters behaviour (awaiting approval).",
            "item-change-approved": (
                "**Item changes**: BX-01 on BI-002, alters behaviour (approved by Lee Sinclair)."
            ),
            "item-removal-recorded": "**Item changes**: BX-01 on BI-004, removed (recorded).",
            "item-id-reused": "**Item changes**: BX-01 on BI-004, removed (recorded); BI-004 id reused.",
        }
        for case, line in expected.items():
            with self.subTest(case=case):
                self.assertIn(line, self.status(case).out.splitlines())

    def test_json_carries_items_and_item_changes(self):
        data = json.loads(self.status("item-change-recorded", "--json").out)
        statuses = {item["id"]: item["status"] for item in data["items"]}
        expected = {"BI-001": "verified", "BI-002": "verified", "BI-003": "exempt", "BI-004": "verified"}
        self.assertEqual(statuses, expected)
        self.assertEqual(data["items"][0]["obligations"], ["VO-001"])
        self.assertEqual(data["items"][0]["scenario"], "US1-AS1")
        self.assertEqual(
            [(change["id"], change["item"], change["state"]) for change in data["item_changes"]],
            [("BX-01", "BI-002", "recorded")],
        )

    def test_scenarios_view_shows_each_items_status_once_items_are_fixed(self):
        out = self.status("items-status-partial", "--scenarios").out
        self.assertIn("  BI-001 | Expresses: FR-001, US1-AS1 | Verified by: VO-001 | Status: verified\n", out)
        self.assertIn("  BI-002 | Expresses: FR-002, US1-AS2, SC-001 | Verified by: VO-002 | Status: planned\n", out)
        self.assertIn("Status: in progress\n", out)
        self.assertIn("Status: exempt\n", out)

    def test_the_summary_written_by_run_holds_the_same_table(self):
        root = self.repo("items-baseline")
        result = self.check(["run", "--phase", "checkpoint", "--command", "suite"], root)
        self.assertEqual(result.code, 0, result)
        stored = summary_body(read(self.feature(root), "tdd-evidence.md"))
        self.assertEqual(stored, self.check(["status"], root).out)
        self.assertIn("| Behaviour item | Scenario | Obligations | Status | Tests |", stored)

    def test_an_older_feature_has_no_item_table(self):
        out = self.status("status-verified").out
        self.assertNotIn("Behaviour item", out)
        self.assertNotIn("Item changes", out)


class DeferredStatusTests(StatusCase):
    """A standing deferral reads deferred with its reason, and never verified (FR-010, FR-011, D5)."""

    BLOCK = [
        "Not verified by tests",
        "",
        "- VO-002 deferred: needs queue (DF-01)",
        "",
        "Counts: verified 1, deferred 1",
    ]

    def row(self, fixture):
        out = self.status(fixture).out
        return [line for line in out.splitlines() if line.startswith("| VO-002")][0], out.splitlines()

    def test_an_obligation_with_a_standing_deferral_reads_deferred_with_its_reason_and_id(self):
        row, lines = self.row("deferred-standing")
        self.assertEqual(row, f"| VO-002 | {REQS_2} | deferred | assert | fail (#4) |")
        start = lines.index(self.BLOCK[0])
        self.assertEqual(lines[start : start + len(self.BLOCK)], self.BLOCK)
        self.assertNotIn("No test tooling: nothing is verified by tests", lines)

    def test_it_is_deferred_after_an_environment_failure_rather_than_blocked(self):
        row, _lines = self.row("deferred-standing")
        self.assertIn("| deferred |", row)
        self.assertNotIn("blocked", row)

    def test_the_requirements_it_serves_are_listed_as_not_verified(self):
        out = self.status("deferred-standing").out
        self.assertIn("FR-002 (VO-002 deferred)", out)

    def test_a_deferral_that_waits_for_approval_does_not_count_as_deferred(self):
        row, lines = self.row("deferred-waiting")
        self.assertIn("| blocked |", row)
        self.assertNotIn("Not verified by tests", lines)

    def test_an_approved_deferral_counts_as_deferred(self):
        row, lines = self.row("deferred-approved")
        self.assertIn("| deferred |", row)
        self.assertIn("- VO-002 deferred: too slow (DF-01)", lines)

    def test_a_later_passing_run_makes_it_verified_and_drops_it_from_the_list(self):
        row, lines = self.row("deferred-then-verified")
        self.assertIn("| verified |", row)
        self.assertNotIn("Not verified by tests", lines)
        self.assertFalse([line for line in lines if line.startswith("Counts:")])

    def test_a_standing_deferral_and_an_environment_blocked_exception_read_deferred(self):
        row, _lines = self.row("deferred-and-blocked-exception")
        self.assertIn("| deferred |", row)

    def test_a_defect_failure_followed_by_an_approved_deferral_reads_deferred(self):
        row, _lines = self.row("deferred-after-failure")
        self.assertIn("| deferred |", row)

    def test_json_carries_the_deferral_and_the_counts(self):
        data = json.loads(self.status("deferred-standing", "--json").out)
        self.assertEqual(
            data["not_verified_by_tests"],
            [{"id": "VO-002", "state": "deferred", "reason": "needs queue", "deferral": "DF-01"}],
        )
        self.assertEqual(data["counts"], {"verified": 1, "deferred": 1})
        self.assertNotIn("no_tooling", data)

    def test_the_stored_summary_is_the_view(self):
        root = self.repo("deferred-compliant")
        self.assertEqual(summary_body(read(self.feature(root), "tdd-evidence.md")), self.check(["status"], root).out)


class ManualStatusTests(StatusCase):
    """Each manual check is shown open, or done with its result and name (FR-017, FR-019)."""

    def lines(self, fixture):
        return self.status(fixture).out.splitlines()

    def test_an_open_check_is_listed_as_not_verified_by_tests(self):
        lines = self.lines("manual-open")
        self.assertIn("- MV-001 manual: open", lines)
        self.assertIn("Counts: verified 2, deferred 0, manual checks 1 open", lines)

    def test_a_done_check_shows_its_result_and_name(self):
        lines = self.lines("manual-pass")
        self.assertIn("- MV-001 manual: pass by A Person", lines)
        self.assertIn("Counts: verified 2, deferred 0, manual checks 0 open, 1 passed", lines)

    def test_a_failed_check_is_shown_with_its_name_and_counted(self):
        lines = self.lines("manual-fail")
        self.assertIn("- MV-001 manual: fail by A Person", lines)
        self.assertIn("Counts: verified 2, deferred 0, manual checks 0 open, 1 failed", lines)

    def test_status_exits_0_in_every_case(self):
        for fixture in ("manual-open", "manual-pass", "manual-fail"):
            self.assertEqual(self.status(fixture).code, 0, fixture)

    def test_the_stored_summary_is_the_view(self):
        for fixture in ("manual-open", "manual-pass", "manual-fail"):
            with self.subTest(fixture=fixture):
                root = self.repo(fixture)
                self.assertEqual(
                    summary_body(read(self.feature(root), "tdd-evidence.md")), self.check(["status"], root).out
                )

    def test_no_obligation_is_changed_by_a_manual_check(self):
        out = self.status("manual-pass").out
        self.assertIn("| VO-001 | FR-001, US1-AS1 | verified |", out)
        self.assertNotIn("No test tooling", out)

    def test_json_carries_the_checks_and_the_counts(self):
        data = json.loads(self.status("manual-fail", "--json").out)
        self.assertEqual(
            data["not_verified_by_tests"],
            [{"id": "MV-001", "state": "manual", "reason": "fail by A Person", "result": "fail"}],
        )
        self.assertEqual(
            data["counts"],
            {"verified": 2, "deferred": 0, "manual_open": 0, "manual_failed": 1, "manual_passed": 0},
        )

    def test_a_failed_check_is_listed_before_an_open_one(self):
        root = self.repo("manual-open")
        plan = os.path.join(self.feature(root), "plan.md")
        with open(plan) as handle:
            text = handle.read()
        row = "| MV-002 | FR-001 | Do it | It works | Manual only |\n"
        with open(plan, "w") as handle:
            handle.write(text.replace("\n## Project Structure", row + "\n## Project Structure", 1))
        self.check(["manual", "--check", "MV-002", "--result", "fail", "--by", "A Person"], root)
        lines = self.check(["status"], root).out.splitlines()
        self.assertLess(lines.index("- MV-002 manual: fail by A Person"), lines.index("- MV-001 manual: open"))


if __name__ == "__main__":
    unittest.main()
