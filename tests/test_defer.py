"""The defer subcommand and the approval of a deferral (contracts/check-cli-changes.md, data-model.md)."""

import json
import os
import re
import unittest

from fixtures.make_features import DEFERRAL_CHAINED, check_over
from support import RepoCase, read, snapshot, table_rows

TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class DeferCase(RepoCase):
    def defer(self, root, *args):
        return self.check(["defer"] + list(args), root)

    def evidence_path(self, root):
        for parts in (("tests", "tdd-evidence.md"), ("tdd-evidence.md",)):
            path = os.path.join(self.feature(root), *parts)
            if os.path.isfile(path):
                return path
        raise AssertionError("no evidence document was written")

    def rows(self, root):
        with open(self.evidence_path(root)) as handle:
            return table_rows(handle.read(), "## Deferrals")

    def assert_nothing_recorded(self, root, result, message):
        self.assertEqual(result.code, 2, result)
        self.assertIn(message, result.err)
        self.assertIn("nothing was recorded", result.err)
        self.assertEqual(result.out, "")


class DeferRecordTests(DeferCase):
    def test_a_deferral_on_an_environment_failure_stands_without_approval(self):
        root = self.repo("defer-env-failure")
        result = self.defer(root, "--vo", "VO-002", "--reason", "needs queue")
        self.assertEqual(
            (result.code, result.out, result.err), (0, "deferred VO-002 as DF-01 (environment failure #4)\n", "")
        )
        row = self.rows(root)[0]
        self.assertEqual(
            (row["ID"], row["Obligations"], row["Reason"], row["Basis"], row["Needs approval"], row["Approved by"]),
            ("DF-01", "VO-002", "needs queue", "environment failure #4", "no", "-"),
        )
        self.assertRegex(row["Time"], TIME)

    def test_a_deferral_with_no_such_failure_waits_for_approval(self):
        root = self.repo("defer-no-failure")
        result = self.defer(root, "--vo", "VO-002", "--reason", "needs queue")
        self.assertEqual(
            (result.code, result.out, result.err), (0, "deferred VO-002 as DF-01 (needs approval: other)\n", "")
        )
        row = self.rows(root)[0]
        self.assertEqual((row["Basis"], row["Needs approval"], row["Approved by"]), ("other", "yes", "-"))

    def test_a_failure_of_another_obligation_is_not_a_basis(self):
        root = self.repo("defer-env-failure")
        result = self.defer(root, "--vo", "VO-001", "--reason", "needs queue")
        self.assertEqual(result.out, "deferred VO-001 as DF-01 (needs approval: other)\n")

    def test_several_obligations_have_an_environment_basis_only_if_each_has_its_own_failure(self):
        root = self.repo("defer-two-obligations")
        result = self.defer(root, "--vo", "VO-001", "VO-002", "--reason", "needs queue")
        self.assertEqual(result.out, "deferred VO-001, VO-002 as DF-01 (environment failure #4, #5)\n")
        self.assertEqual(self.rows(root)[0]["Needs approval"], "no")
        root = self.repo("defer-env-failure")
        result = self.defer(root, "--vo", "VO-001", "VO-002", "--reason", "needs queue")
        self.assertEqual(result.out, "deferred VO-001, VO-002 as DF-01 (needs approval: other)\n")
        self.assertEqual(self.rows(root)[0]["Needs approval"], "yes")

    def test_an_unclassified_failure_is_not_an_environment_failure(self):
        root = self.repo("defer-env-failure")
        path = self.evidence_path(root)
        with open(path) as handle:
            text = handle.read()
        self.assertIn("| fail | yes | environment |", text)
        with open(path, "w") as handle:
            handle.write(text.replace("| fail | yes | environment |", "| fail | yes | unclassified |"))
        result = self.defer(root, "--vo", "VO-002", "--reason", "needs queue")
        self.assertEqual(result.out, "deferred VO-002 as DF-01 (needs approval: other)\n")

    def test_the_latest_environment_failure_is_named(self):
        root = self.repo("defer-two-obligations")
        result = self.defer(root, "--vo", "VO-002", "--reason", "needs queue")
        self.assertEqual(result.out, "deferred VO-002 as DF-01 (environment failure #5)\n")

    def test_a_second_deferral_gets_the_next_id(self):
        root = self.repo("defer-env-failure")
        self.defer(root, "--vo", "VO-002", "--reason", "needs queue")
        result = self.defer(root, "--vo", "VO-001", "--reason", "too slow")
        self.assertEqual(result.out, "deferred VO-001 as DF-02 (needs approval: other)\n")
        self.assertEqual([row["ID"] for row in self.rows(root)], ["DF-01", "DF-02"])

    def test_the_new_rows_chain_verifies_and_is_independent_of_the_records(self):
        root = self.repo("defer-env-failure")
        self.defer(root, "--vo", "VO-002", "--reason", "needs queue")
        self.defer(root, "--vo", "VO-001", "--reason", "too slow")
        previous = ""
        for row in self.rows(root):
            self.assertEqual(row["Check"], check_over(previous, row, DEFERRAL_CHAINED))
            previous = row["Check"]

    def test_json_carries_the_same_data(self):
        root = self.repo("defer-env-failure")
        result = self.defer(root, "--vo", "VO-002", "--reason", "needs queue", "--json")
        data = json.loads(result.out)
        self.assertEqual(data["exit_code"], 0)
        self.assertEqual(data["id"], "DF-01")
        self.assertEqual(data["obligations"], ["VO-002"])
        self.assertEqual((data["basis"], data["needs_approval"]), ("environment failure #4", False))

    def test_a_reason_is_written_as_one_cell(self):
        root = self.repo("defer-no-failure")
        self.defer(root, "--vo", "VO-002", "--reason", "needs a queue | which\nis down")
        self.assertEqual(self.rows(root)[0]["Reason"], "needs a queue which is down")

    def test_the_first_deferral_creates_the_evidence_document_and_its_table(self):
        root = self.repo("defer-no-failure")
        self.assertFalse(os.path.exists(os.path.join(self.feature(root), "tdd-evidence.md")))
        self.defer(root, "--vo", "VO-002", "--reason", "needs queue")
        text = read(self.feature(root), "tests", "tdd-evidence.md")
        self.assertIn("## Deferrals", text.splitlines())
        self.assertNotIn("## Manual results", text.splitlines())

    def test_the_records_and_the_other_tables_are_untouched(self):
        root = self.repo("defer-env-failure")
        before = table_rows(read(self.feature(root), "tdd-evidence.md"), "## Test execution records")
        self.defer(root, "--vo", "VO-002", "--reason", "needs queue")
        after = table_rows(read(self.feature(root), "tdd-evidence.md"), "## Test execution records")
        self.assertEqual(after, before)


class DeferRefusalTests(DeferCase):
    def test_an_obligation_the_plan_does_not_hold_is_refused(self):
        root = self.repo("defer-env-failure")
        before = snapshot(root)
        result = self.defer(root, "--vo", "VO-009", "--reason", "needs queue")
        self.assert_nothing_recorded(root, result, "obligation VO-009 is not in the plan")
        self.assertEqual(snapshot(root), before)

    def test_one_unknown_obligation_among_several_records_nothing(self):
        root = self.repo("defer-env-failure")
        before = snapshot(root)
        result = self.defer(root, "--vo", "VO-002", "VO-009", "--reason", "needs queue")
        self.assert_nothing_recorded(root, result, "obligation VO-009 is not in the plan")
        self.assertEqual(snapshot(root), before)

    def test_an_empty_reason_is_refused(self):
        for reason in ("", "   ", "-"):
            with self.subTest(reason=reason):
                root = self.repo("defer-env-failure")
                before = snapshot(root)
                result = self.defer(root, "--vo", "VO-002", "--reason", reason)
                self.assert_nothing_recorded(root, result, "--reason must say why the obligation is deferred")
                self.assertEqual(snapshot(root), before)

    def test_a_feature_with_no_verification_plan_is_refused(self):
        root = self.repo("plan-no-section")
        result = self.defer(root, "--vo", "VO-001", "--reason", "needs queue")
        self.assertEqual(result.code, 2, result)
        self.assertIn("no Verification Plan", result.err)

    def test_no_tooling_mode_refuses_with_the_reason_and_records_nothing(self):
        root = self.repo("defer-no-tooling")
        before = snapshot(root)
        result = self.defer(root, "--vo", "VO-002", "--reason", "needs queue")
        self.assert_nothing_recorded(
            root, result, "every obligation is already deferred: the plan records no test tooling"
        )
        self.assertEqual(snapshot(root), before)

    def test_at_least_one_obligation_and_a_reason_are_required(self):
        root = self.repo("defer-env-failure")
        result = self.defer(root, "--reason", "needs queue")
        self.assertEqual(result.code, 2)
        self.assertIn("--vo", result.err)
        result = self.defer(root, "--vo", "VO-002")
        self.assertEqual(result.code, 2)
        self.assertIn("--reason", result.err)


class ApproveDeferralTests(DeferCase):
    def approve(self, root, ident, *extra):
        return self.check(["approve", "--id", ident, "--by", "A Person"] + list(extra), root)

    def setUp(self):
        self.root = self.repo("defer-env-failure")
        self.defer(self.root, "--vo", "VO-002", "--reason", "needs queue")
        self.defer(self.root, "--vo", "VO-001", "--reason", "too slow")

    def test_a_deferral_that_needs_approval_can_be_approved(self):
        result = self.approve(self.root, "DF-02")
        self.assertEqual((result.code, result.out, result.err), (0, "recorded approval of DF-02 by A Person\n", ""))
        self.assertEqual([row["Approved by"] for row in self.rows(self.root)], ["-", "A Person"])

    def test_approval_does_not_break_the_chain(self):
        self.approve(self.root, "DF-02")
        previous = ""
        for row in self.rows(self.root):
            self.assertEqual(row["Check"], check_over(previous, row, DEFERRAL_CHAINED))
            previous = row["Check"]

    def test_a_deferral_on_an_environment_failure_does_not_need_approval(self):
        before = snapshot(self.root)
        result = self.approve(self.root, "DF-01")
        self.assert_nothing_recorded(self.root, result, "DF-01 does not need approval")
        self.assertEqual(snapshot(self.root), before)

    def test_an_unknown_deferral_is_refused(self):
        result = self.approve(self.root, "DF-09")
        self.assert_nothing_recorded(self.root, result, "no entry DF-09")

    def test_a_deferral_is_not_approved_twice(self):
        self.approve(self.root, "DF-02")
        result = self.approve(self.root, "DF-02")
        self.assert_nothing_recorded(self.root, result, "DF-02 is already approved by A Person")


if __name__ == "__main__":
    unittest.main()
