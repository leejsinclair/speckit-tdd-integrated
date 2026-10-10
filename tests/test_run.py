"""The command runner and the evidence ledger (contracts/check-cli.md, run)."""

import calendar
import os
import re
import time
import unittest

from fixtures.make_features import check_value, fingerprint
from support import EVIDENCE_REL, RunCase, evidence_text, records, snapshot, table_rows, write

BROKEN = "| broken | `sh tests/fixtures/bin/fake_test.sh assert` | broad | tests/fixtures/bin |"
OTHER_TOOL = (
    "| other | `python3 -c \"import sys; print('boom: total was None'); "
    "sys.exit(3 if '{select}' == 'bad' else 0)\"` | focused | a second tool |"
)


class BaselineFirstTests(RunCase):
    def assert_refused(self, result):
        self.assertEqual(result.code, 2, result)
        self.assertIn("record a baseline with a broad command first", result.err)
        self.assertFalse(self.has_evidence())

    def test_red_is_refused_without_a_baseline(self):
        self.assert_refused(self.red())

    def test_green_is_refused_without_a_baseline(self):
        self.assert_refused(self.green())

    def test_refactor_is_refused_without_a_baseline(self):
        self.assert_refused(
            self.run_phase("refactor", "unit", "--select", "pass", "--task", "T012", "--vo", "VO-001")
        )

    def test_checkpoint_is_refused_without_a_baseline(self):
        self.assert_refused(self.run_phase("checkpoint", "suite"))


class PhaseTableTests(RunCase):
    """Each row of the contract's phase table."""

    def last(self):
        return records(self.root)[-1]

    def test_passing_baseline_is_valid(self):
        self.assertEqual(self.run_phase("baseline", "suite").code, 0)
        row = self.last()
        self.assertEqual((row["Phase"], row["Result"], row["Valid"]), ("baseline", "pass", "yes"))

    def test_failing_baseline_is_valid_and_exits_0(self):
        self.assertEqual(self.run_phase("baseline", "unit", "--select", "assert").code, 0)
        row = self.last()
        self.assertEqual((row["Phase"], row["Result"], row["Valid"]), ("baseline", "fail", "yes"))

    def test_red_is_valid_on_a_failure_with_the_expected_text(self):
        self.baseline()
        result = self.red()
        self.assertEqual(result.code, 0, result)
        row = self.last()
        self.assertEqual((row["Phase"], row["Result"], row["Valid"]), ("red", "fail", "yes"))

    def test_red_that_passes_is_recorded_invalid(self):
        self.baseline()
        result = self.red(select="pass")
        self.assertEqual(result.code, 1, result)
        row = self.last()
        self.assertEqual((row["Result"], row["Valid"]), ("pass", "no"))
        self.assertEqual(row["Note"], "passed on first run: investigate")

    def test_red_failing_without_the_expected_text_is_recorded_invalid(self):
        self.baseline()
        result = self.red(select="import")
        self.assertEqual(result.code, 1, result)
        row = self.last()
        self.assertEqual((row["Result"], row["Valid"]), ("fail", "no"))
        self.assertEqual(row["Note"], "failed for a different reason")

    def test_green_is_valid_only_on_zero_exit(self):
        self.baseline()
        self.assertEqual(self.green().code, 0)
        self.assertEqual((self.last()["Result"], self.last()["Valid"]), ("pass", "yes"))
        self.assertEqual(self.green(select="assert").code, 1)
        self.assertEqual((self.last()["Result"], self.last()["Valid"]), ("fail", "no"))

    def test_refactor_is_valid_only_on_zero_exit(self):
        self.baseline()
        args = ["--task", "T012", "--vo", "VO-001"]
        self.assertEqual(self.run_phase("refactor", "unit", "--select", "pass", *args).code, 0)
        self.assertEqual((self.last()["Phase"], self.last()["Valid"]), ("refactor", "yes"))
        self.assertEqual(self.run_phase("refactor", "unit", "--select", "import", *args).code, 1)
        self.assertEqual((self.last()["Result"], self.last()["Valid"]), ("fail", "no"))

    def test_checkpoint_is_valid_for_a_broad_command_that_passes(self):
        self.baseline()
        self.assertEqual(self.run_phase("checkpoint", "suite").code, 0)
        row = self.last()
        self.assertEqual((row["Phase"], row["Result"], row["Valid"], row["Task"]), ("checkpoint", "pass", "yes", "-"))

    def test_checkpoint_with_a_focused_command_is_not_valid(self):
        self.baseline()
        result = self.run_phase("checkpoint", "unit", "--select", "pass")
        self.assertEqual(result.code, 1, result)
        row = self.last()
        self.assertEqual((row["Result"], row["Valid"]), ("pass", "no"))
        self.assertEqual(row["Note"], "command scope is not broad")

    def test_checkpoint_that_fails_is_not_valid(self):
        self.add_command(BROKEN)
        self.baseline()
        self.assertEqual(self.run_phase("checkpoint", "broken").code, 1)
        self.assertEqual((self.last()["Result"], self.last()["Valid"]), ("fail", "no"))


class UsageTests(RunCase):
    def setUp(self):
        super().setUp()
        self.baseline()
        self.before = records(self.root)

    def assert_nothing_recorded(self, result, message):
        self.assertEqual(result.code, 2, result)
        self.assertIn(message, result.err)
        self.assertEqual(records(self.root), self.before)

    def test_undeclared_command_records_nothing(self):
        result = self.run_phase("green", "adhoc", "--task", "T012", "--vo", "VO-001")
        self.assert_nothing_recorded(result, "command 'adhoc' is not declared in the plan")

    def test_select_on_a_command_without_the_placeholder(self):
        result = self.run_phase("checkpoint", "suite", "--select", "pass")
        self.assert_nothing_recorded(result, "command 'suite' has no {select}")

    def test_a_command_with_the_placeholder_needs_select(self):
        result = self.run_phase("green", "unit", "--task", "T012", "--vo", "VO-001")
        self.assert_nothing_recorded(result, "command 'unit' needs --select")

    def test_task_and_obligation_are_required_for_the_cycle_phases(self):
        for phase in ("red", "green", "refactor"):
            extra = ["--tests", "tests/test_cart.py", "--expect", "AssertionError"] if phase == "red" else []
            result = self.run_phase(phase, "unit", "--select", "pass", "--vo", "VO-001", *extra)
            self.assert_nothing_recorded(result, f"--task is required for {phase}")
            result = self.run_phase(phase, "unit", "--select", "pass", "--task", "T012", *extra)
            self.assert_nothing_recorded(result, f"--vo is required for {phase}")

    def test_tests_and_expect_are_required_for_red(self):
        base = ["--select", "assert", "--task", "T011", "--vo", "VO-001"]
        result = self.run_phase("red", "unit", *base, "--expect", "AssertionError")
        self.assert_nothing_recorded(result, "--tests is required for red")
        result = self.run_phase("red", "unit", *base, "--tests", "tests/test_cart.py")
        self.assert_nothing_recorded(result, "--expect is required for red")

    def test_the_obligations_must_be_on_the_task(self):
        result = self.green(task="T012", vo="VO-002")
        self.assert_nothing_recorded(result, "obligation VO-002 is not on task T012")

    def test_the_task_must_exist(self):
        result = self.green(task="T099")
        self.assert_nothing_recorded(result, "task T099 is not in tasks.md")

    def test_task_and_obligation_do_not_apply_to_a_checkpoint(self):
        result = self.run_phase("checkpoint", "suite", "--task", "T012")
        self.assert_nothing_recorded(result, "--task and --vo do not apply to checkpoint")


class OutputTests(RunCase):
    def setUp(self):
        super().setUp()
        self.baseline()

    def test_a_run_past_the_timeout_is_a_failure_noted_timed_out(self):
        started = time.time()
        result = self.green(select="slow", extra=["--timeout", "1"])
        self.assertLess(time.time() - started, 4)
        self.assertEqual(result.code, 1, result)
        row = records(self.root)[-1]
        self.assertEqual((row["Result"], row["Valid"], row["Note"]), ("fail", "no", "timed out"))

    def test_only_the_last_40_lines_of_output_are_shown(self):
        result = self.green(select="long")
        shown = result.out.splitlines()
        self.assertIn("line 60", shown)
        self.assertIn("line 21", shown)
        self.assertNotIn("line 20", shown)

    def test_the_outcome_is_stated_after_the_output(self):
        result = self.red()
        self.assertIn("AssertionError: expected 0 got None", result.out.splitlines())
        self.assertEqual(result.out.splitlines()[-1], "recorded #2: red unit: fail, valid")
        result = self.green(select="assert")
        self.assertEqual(result.out.splitlines()[-1], "recorded #3: green unit: fail, not valid for green")

    def test_a_command_in_a_different_tool_is_judged_the_same_way(self):
        """FR-048: exit status and expected text, whatever the tool."""
        self.add_command(OTHER_TOOL)
        args = ["--task", "T011", "--vo", "VO-001"]
        red = self.run_phase(
            "red", "other", "--select", "bad", *args, "--tests", "tests/test_cart.py", "--expect", "boom: total was"
        )
        self.assertEqual(red.code, 0, red)
        row = records(self.root)[-1]
        self.assertEqual((row["Command"], row["Result"], row["Valid"]), ("other", "fail", "yes"))
        wrong = self.run_phase(
            "red", "other", "--select", "bad", *args, "--tests", "tests/test_cart.py", "--expect", "AssertionError"
        )
        self.assertEqual(wrong.code, 1)
        self.assertEqual(records(self.root)[-1]["Note"], "failed for a different reason")
        green = self.run_phase("green", "other", "--select", "good", "--task", "T012", "--vo", "VO-001")
        self.assertEqual(green.code, 0, green)
        self.assertEqual(records(self.root)[-1]["Valid"], "yes")


class LedgerTests(RunCase):
    """The evidence document as contracts/artefact-formats.md section 3 defines it."""

    def test_first_write_creates_the_document_from_the_template(self):
        self.assertFalse(self.has_evidence())
        self.baseline()
        text = evidence_text(self.root)
        lines = text.splitlines()
        self.assertEqual(lines[0], "# TDD Evidence: 001-demo")
        self.assertIn("<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->", lines)
        headings = [line for line in lines if line.startswith("## ")]
        self.assertEqual(
            headings,
            [
                "## Summary",
                "## Baseline",
                "## Test execution records",
                "## Exceptions",
                "## Expectation changes",
                "## Decisions",
            ],
        )
        for heading in ("## Exceptions", "## Expectation changes", "## Decisions"):
            self.assertEqual(table_rows(text, heading), [])

    def test_summary_carries_the_generated_on_line(self):
        self.baseline()
        self.assertRegex(
            evidence_text(self.root),
            r"## Summary\n\n_Generated from the tables below on \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\._\n",
        )

    def test_seq_is_contiguous_from_1(self):
        self.baseline()
        self.red()
        self.green()
        self.green(select="assert")
        self.assertEqual([row["Seq"] for row in records(self.root)], ["1", "2", "3", "4"])

    def test_row_cells_match_the_contract(self):
        self.baseline()
        self.red()
        self.green()
        first, second, third = records(self.root)
        stamp = r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$"
        self.assertRegex(first["Time"], stamp)
        expected_first = {
            "Seq": "1", "Task": "-", "Obligations": "-", "Phase": "baseline", "Command": "suite", "Selector": "-",
            "Result": "pass", "Valid": "yes", "Classification": "-", "Files": "-", "Fingerprint": "-", "Note": "-",
        }  # fmt: skip
        self.assertEqual({key: first[key] for key in expected_first}, expected_first)
        expected_second = {
            "Seq": "2", "Task": "T011", "Obligations": "VO-001", "Phase": "red", "Command": "unit",
            "Selector": "assert", "Result": "fail", "Valid": "yes", "Classification": "assertion",
            "Files": "tests/test_cart.py", "Note": "expected: AssertionError: expected 0",
        }  # fmt: skip
        self.assertEqual({key: second[key] for key in expected_second}, expected_second)
        self.assertEqual((third["Task"], third["Phase"]), ("T012", "green"))
        self.assertEqual((third["Classification"], third["Note"]), ("-", "-"))
        for row in (first, second, third):
            self.assertRegex(row["Check"], r"^[0-9a-f]{6}$")

    def test_several_obligations_are_listed(self):
        tasks = "- [ ] T001 [VO-001] [VO-002] Write both tests\n- [ ] T002 [VO-001] [VO-002] Implement both\n"
        write(self.feature(self.root), ["tasks.md"], tasks)
        self.baseline()
        self.run_phase(
            "red", "unit", "--select", "assert", "--task", "T001", "--vo", "VO-001", "VO-002",
            "--tests", "tests/test_cart.py", "--expect", "AssertionError"
        )  # fmt: skip
        self.assertEqual(records(self.root)[-1]["Obligations"], "VO-001, VO-002")

    def test_files_are_relative_sorted_and_comma_separated(self):
        write(self.root, ["tests", "a_test.py"], "assert True\n")
        self.baseline()
        absolute = os.path.join(self.root, "tests", "a_test.py")
        result = self.run_phase(
            "red", "unit", "--select", "assert", "--task", "T011", "--vo", "VO-001",
            "--tests", "tests/test_cart.py", absolute, "--expect", "AssertionError"
        )  # fmt: skip
        self.assertEqual(result.code, 0, result)
        self.assertEqual(records(self.root)[-1]["Files"], "tests/a_test.py, tests/test_cart.py")

    def test_fingerprint_is_the_contract_hash_of_paths_and_contents(self):
        write(self.root, ["tests", "a_test.py"], "assert True\n")
        self.baseline()
        self.run_phase(
            "red", "unit", "--select", "assert", "--task", "T011", "--vo", "VO-001",
            "--tests", "tests/test_cart.py", "tests/a_test.py", "tests/gone.py", "--expect", "AssertionError"
        )  # fmt: skip
        row = records(self.root)[-1]
        self.assertEqual(row["Files"], "tests/a_test.py, tests/gone.py, tests/test_cart.py")
        expected = fingerprint(
            {
                "tests/test_cart.py": b"assert total([]) == 0\n",
                "tests/a_test.py": b"assert True\n",
                "tests/gone.py": None,
            }
        )
        self.assertEqual(row["Fingerprint"], expected)

    def test_no_files_gives_a_dash_for_files_and_fingerprint(self):
        self.baseline()
        self.green()
        row = records(self.root)[-1]
        self.assertEqual((row["Files"], row["Fingerprint"]), ("-", "-"))

    def test_check_chains_from_the_previous_row(self):
        self.baseline()
        self.red()
        self.green(select="assert")
        self.run_phase("checkpoint", "suite", "--note", "end of phase")
        previous = ""
        rows = records(self.root)
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertEqual(row["Check"], check_value(previous, row), row["Seq"])
            previous = row["Check"]

    def test_valid_red_is_classified_assertion_and_other_failures_unclassified(self):
        self.baseline()
        self.red()
        self.red(select="import")
        self.green(select="assert")
        self.red(select="pass")
        rows = records(self.root)
        found = [row["Classification"] for row in rows]
        self.assertEqual(found, ["-", "assertion", "unclassified", "unclassified", "-"])
        self.assertTrue(rows[1]["Note"].startswith("expected:"))

    def test_a_bar_or_line_break_in_supplied_text_becomes_a_space(self):
        self.baseline()
        self.green(extra=["--note", "first|second\nthird"])
        self.assertEqual(records(self.root)[-1]["Note"], "first second third")

    def test_a_note_is_kept_after_the_reason_the_script_gives(self):
        self.baseline()
        self.red(extra=["--note", "first attempt"])
        self.assertEqual(records(self.root)[-1]["Note"], "expected: AssertionError: expected 0; first attempt")

    def test_no_test_output_beyond_the_matched_text_is_stored(self):
        self.baseline()
        self.green(select="long")
        self.red()
        text = evidence_text(self.root)
        self.assertNotIn("line 59", text)
        self.assertNotIn("got None", text)

    def test_baseline_table_lists_pre_existing_failures(self):
        self.run_phase("baseline", "suite")
        self.run_phase("baseline", "unit", "--select", "assert")
        self.run_phase("baseline", "unit", "--select", "assert", "--note", "test_old_total fails")
        rows = table_rows(evidence_text(self.root), "## Baseline")
        self.assertEqual(
            [(row["Seq"], row["Command"], row["Result"], row["Pre-existing failures"]) for row in rows],
            [
                ("1", "suite", "pass", "-"),
                ("2", "unit", "fail", "failing before work began"),
                ("3", "unit", "fail", "test_old_total fails"),
            ],
        )

    def test_only_the_evidence_document_is_created_or_changed(self):
        before = snapshot(self.root)
        self.baseline()
        self.red()
        self.green()
        after = snapshot(self.root)
        changed = {name for name in after if before.get(name) != after[name]}
        self.assertEqual(changed, {EVIDENCE_REL})
        self.assertEqual(set(before) - set(after), set())

    def test_a_malformed_evidence_document_is_not_written_to(self):
        self.baseline()
        path = os.path.join(self.root, EVIDENCE_REL)
        broken = evidence_text(self.root).replace("| Seq | Time | Task |", "| Seq | When | Task |")
        with open(path, "w") as handle:
            handle.write(broken)
        result = self.green()
        self.assertEqual(result.code, 2, result)
        self.assertIn("tdd-evidence.md", result.err)
        self.assertEqual(evidence_text(self.root), broken)

    def test_time_is_utc_now(self):
        self.baseline()
        stamp = records(self.root)[0]["Time"]
        self.assertTrue(re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$", stamp))
        recorded = calendar.timegm(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ"))
        self.assertLess(abs(time.time() - recorded), 120)


XC_HEADING = "## Expectation changes"
TWO_OBLIGATION_TASKS = (
    "- [ ] T001 [VO-001] Write the first test\n"
    "- [ ] T002 [VO-002] Write the second test\n"
    "- [ ] T003 [VO-001] [VO-002] Implement both\n"
)


class FingerprintReuseTests(RunCase):
    """green and refactor read the test files back from the obligation's failing-first record."""

    def setUp(self):
        super().setUp()
        self.baseline()
        self.assertEqual(self.red().code, 0)
        self.red_row = records(self.root)[-1]

    def test_green_takes_files_from_the_red_record_made_on_the_test_task(self):
        self.assertEqual(self.red_row["Task"], "T011")
        self.assertEqual(self.green().code, 0)
        row = records(self.root)[-1]
        self.assertEqual(row["Task"], "T012")
        self.assertEqual(row["Files"], "tests/test_cart.py")
        self.assertEqual(row["Fingerprint"], self.red_row["Fingerprint"])

    def test_refactor_takes_files_from_the_red_record(self):
        self.green()
        self.run_phase("refactor", "unit", "--select", "pass", "--task", "T012", "--vo", "VO-001")
        row = records(self.root)[-1]
        self.assertEqual((row["Phase"], row["Files"]), ("refactor", "tests/test_cart.py"))
        self.assertEqual(row["Fingerprint"], self.red_row["Fingerprint"])

    def test_a_changed_test_file_gives_a_different_fingerprint_on_the_green_row(self):
        write(self.root, ["tests", "test_cart.py"], "assert True\n")
        self.green()
        row = records(self.root)[-1]
        self.assertEqual(row["Files"], "tests/test_cart.py")
        self.assertNotEqual(row["Fingerprint"], self.red_row["Fingerprint"])
        self.assertEqual(row["Fingerprint"], fingerprint({"tests/test_cart.py": b"assert True\n"}))

    def test_a_deleted_test_file_gives_a_different_fingerprint_on_the_green_row(self):
        os.remove(os.path.join(self.root, "tests", "test_cart.py"))
        self.green()
        row = records(self.root)[-1]
        self.assertEqual(row["Fingerprint"], fingerprint({"tests/test_cart.py": None}))
        self.assertNotEqual(row["Fingerprint"], self.red_row["Fingerprint"])

    def test_the_latest_valid_red_record_is_the_one_used(self):
        write(self.root, ["tests", "test_other.py"], "assert False\n")
        self.run_phase(
            "red", "unit", "--select", "assert", "--task", "T011", "--vo", "VO-001",
            "--tests", "tests/test_other.py", "--expect", "AssertionError"
        )  # fmt: skip
        self.red(select="pass")  # recorded, not valid, so it is not the one used
        self.green()
        self.assertEqual(records(self.root)[-1]["Files"], "tests/test_other.py")

    def test_tests_given_to_green_are_used_as_given(self):
        write(self.root, ["tests", "test_other.py"], "assert False\n")
        self.green(extra=["--tests", "tests/test_other.py"])
        self.assertEqual(records(self.root)[-1]["Files"], "tests/test_other.py")

    def test_with_no_valid_red_record_nothing_is_fingerprinted(self):
        self.run_phase("green", "unit", "--select", "pass", "--task", "T014", "--vo", "VO-002")
        row = records(self.root)[-1]
        self.assertEqual((row["Files"], row["Fingerprint"]), ("-", "-"))


class SeveralObligationsTests(RunCase):
    def setUp(self):
        super().setUp()
        write(self.feature(self.root), ["tasks.md"], TWO_OBLIGATION_TASKS)
        write(self.root, ["tests", "test_other.py"], "assert False\n")
        self.baseline()

    def red_for(self, task, vo, path):
        result = self.run_phase(
            "red", "unit", "--select", "assert", "--task", task, "--vo", vo,
            "--tests", path, "--expect", "AssertionError"
        )  # fmt: skip
        self.assertEqual(result.code, 0, result)

    def green_both(self):
        return self.run_phase("green", "unit", "--select", "pass", "--task", "T003", "--vo", "VO-001", "VO-002")

    def test_obligations_whose_red_records_list_different_files_are_refused(self):
        self.red_for("T001", "VO-001", "tests/test_cart.py")
        self.red_for("T002", "VO-002", "tests/test_other.py")
        before = records(self.root)
        result = self.green_both()
        self.assertEqual(result.code, 2, result)
        self.assertIn("list different files", result.err)
        self.assertIn("run them separately", result.err)
        self.assertEqual(records(self.root), before)

    def test_obligations_whose_red_records_list_the_same_files_are_accepted(self):
        self.red_for("T001", "VO-001", "tests/test_cart.py")
        self.red_for("T002", "VO-002", "tests/test_cart.py")
        self.assertEqual(self.green_both().code, 0)
        self.assertEqual(records(self.root)[-1]["Files"], "tests/test_cart.py")

    def test_an_obligation_without_a_red_record_does_not_conflict(self):
        self.red_for("T001", "VO-001", "tests/test_cart.py")
        self.assertEqual(self.green_both().code, 0)
        self.assertEqual(records(self.root)[-1]["Files"], "tests/test_cart.py")


class ExpectationTests(RunCase):
    def setUp(self):
        super().setUp()
        self.baseline()
        self.red()
        write(self.root, ["tests", "test_cart.py"], "assert total([]) == 0.0\n")

    def expectation(self, *extra, task="T012"):
        return self.check(
            ["expectation", "--task", task, "--tests", "tests/test_cart.py", "--justification", "The total is a float"]
            + list(extra),
            self.root,
        )

    def changes(self):
        return table_rows(evidence_text(self.root), XC_HEADING)

    def test_expectation_appends_a_row(self):
        result = self.expectation("--requirement", "FR-001", "US1-AS1")
        self.assertEqual((result.code, result.out), (0, "recorded XC-01 for T012\n"), result)
        (row,) = self.changes()
        self.assertRegex(row["Time"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        del row["Time"]
        self.assertEqual(
            row,
            {
                "ID": "XC-01",
                "Task": "T012",
                "Files": "tests/test_cart.py",
                "Requirements": "FR-001, US1-AS1",
                "Justification": "The total is a float",
                "Alters behaviour": "no",
                "Approved by": "-",
                "New fingerprint": fingerprint({"tests/test_cart.py": b"assert total([]) == 0.0\n"}),
            },
        )

    def test_ids_count_up_and_flags_are_recorded(self):
        self.expectation("--requirement", "FR-001")
        self.expectation("--requirement", "FR-001", "--alters-behaviour", "--approved-by", "Lee Sinclair")
        rows = self.changes()
        self.assertEqual([row["ID"] for row in rows], ["XC-01", "XC-02"])
        self.assertEqual((rows[1]["Alters behaviour"], rows[1]["Approved by"]), ("yes", "Lee Sinclair"))

    def test_expectation_without_a_requirement_exits_2(self):
        result = self.expectation()
        self.assertEqual(result.code, 2)
        self.assertIn("--requirement", result.err)
        self.assertEqual(self.changes(), [])

    def test_expectation_for_an_unknown_task_exits_2(self):
        result = self.expectation("--requirement", "FR-001", task="T099")
        self.assertEqual(result.code, 2)
        self.assertIn("task T099 is not in tasks.md", result.err)
        self.assertEqual(self.changes(), [])

    def test_approve_fills_approved_by(self):
        self.expectation("--requirement", "FR-001", "--alters-behaviour")
        result = self.check(["approve", "--id", "XC-01", "--by", "Lee Sinclair"], self.root)
        self.assertEqual((result.code, result.out), (0, "recorded approval of XC-01 by Lee Sinclair\n"), result)
        self.assertEqual(self.changes()[0]["Approved by"], "Lee Sinclair")

    def test_approve_for_an_unknown_id_exits_2(self):
        self.expectation("--requirement", "FR-001")
        before = evidence_text(self.root)
        for ident in ("XC-09", "ZZ-01"):
            result = self.check(["approve", "--id", ident, "--by", "Lee"], self.root)
            self.assertEqual(result.code, 2, ident)
            self.assertIn(f"no entry {ident}", result.err)
        self.assertEqual(evidence_text(self.root), before)

    def test_records_are_untouched_by_expectation_and_approve(self):
        before = records(self.root)
        self.expectation("--requirement", "FR-001", "--alters-behaviour")
        self.check(["approve", "--id", "XC-01", "--by", "Lee"], self.root)
        self.assertEqual(records(self.root), before)

    def test_only_the_evidence_document_is_created_or_changed(self):
        before = snapshot(self.root)
        self.expectation("--requirement", "FR-001", "--alters-behaviour")
        self.check(["approve", "--id", "XC-01", "--by", "Lee"], self.root)
        after = snapshot(self.root)
        self.assertEqual({name for name in after if before.get(name) != after[name]}, {EVIDENCE_REL})
        self.assertEqual(set(before) - set(after), set())


EX_HEADING = "## Exceptions"
DN_HEADING = "## Decisions"
ALL_KINDS = [
    "no-meaningful-red", "behaviour-preserving", "legacy", "external-system", "generated-code", "migration",
    "infrastructure", "exploratory", "environment-blocked", "other",
]  # fmt: skip
ALWAYS_APPROVED_KINDS = ("legacy", "exploratory", "other")


class RecordingCase(RunCase):
    def setUp(self):
        super().setUp()
        self.baseline()

    def rows(self, heading):
        return table_rows(evidence_text(self.root), heading)

    def assert_only_evidence_changed(self, before):
        after = snapshot(self.root)
        self.assertEqual({name for name in after if before.get(name) != after[name]}, {EVIDENCE_REL})
        self.assertEqual(set(before) - set(after), set())


class ClassifyTests(RecordingCase):
    def setUp(self):
        super().setUp()
        self.red()
        self.green(select="import")  # 3: an unclassified failure
        self.green()  # 4: a pass

    def classify(self, seq, kind, *extra):
        return self.check(["classify", "--seq", str(seq), "--as", kind] + list(extra), self.root)

    def test_classify_sets_each_classification(self):
        for kind in ("assertion", "defect", "environment", "unreliable"):
            self.green(select="import")
            seq = len(records(self.root))
            result = self.classify(seq, kind)
            self.assertEqual((result.code, result.out), (0, f"classified #{seq} as {kind}\n"), result)
            self.assertEqual(records(self.root)[-1]["Classification"], kind)

    def test_classify_leaves_the_check_value_and_every_other_cell_unchanged(self):
        before = records(self.root)
        self.classify(3, "environment")
        after = records(self.root)
        self.assertEqual(after[2]["Check"], before[2]["Check"])
        self.assertEqual(after[2]["Check"], check_value(after[1]["Check"], after[2]))
        before[2]["Classification"] = "environment"
        self.assertEqual(after, before)

    def test_classify_may_extend_the_note(self):
        self.classify(3, "environment", "--note", "the package index was unreachable")
        self.assertEqual(records(self.root)[2]["Note"], "the package index was unreachable")
        self.red(select="import")
        seq = len(records(self.root))
        self.classify(seq, "defect", "--note", "a typo|in the test")
        self.assertEqual(records(self.root)[-1]["Note"], "failed for a different reason; a typo in the test")

    def test_classify_refuses_a_pass(self):
        result = self.classify(4, "defect")
        self.assertEqual(result.code, 2)
        self.assertIn("record #4 is a pass", result.err)

    def test_classify_refuses_a_record_already_classified(self):
        result = self.classify(2, "defect")
        self.assertEqual(result.code, 2)
        self.assertIn("record #2 is already classified as assertion", result.err)
        self.classify(3, "defect")
        self.assertEqual(self.classify(3, "environment").code, 2)
        self.assertEqual(records(self.root)[2]["Classification"], "defect")

    def test_classify_refuses_an_unknown_record(self):
        result = self.classify(99, "defect")
        self.assertEqual(result.code, 2)
        self.assertIn("no record #99", result.err)

    def test_only_the_evidence_document_is_changed(self):
        before = snapshot(self.root)
        self.classify(3, "environment")
        self.assert_only_evidence_changed(before)


class ExceptionTests(RecordingCase):
    def exception(self, kind, *extra, task="T013", vo=("VO-002",), rationale="No seam to test through"):
        args = ["exception", "--task", task, "--kind", kind, "--rationale", rationale]
        if vo:
            args += ["--vo"] + list(vo)
        return self.check(args + list(extra), self.root)

    def test_exception_appends_a_row(self):
        result = self.exception("generated-code", "--alternative", "Generator's own tests run in CI")
        self.assertEqual((result.code, result.out), (0, "recorded EX-01 for T013\n"), result)
        (row,) = self.rows(EX_HEADING)
        self.assertRegex(row.pop("Time"), r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(
            row,
            {
                "ID": "EX-01",
                "Task": "T013",
                "Obligations": "VO-002",
                "Kind": "generated-code",
                "Rationale": "No seam to test through",
                "Alternative verification": "Generator's own tests run in CI",
                "Needs approval": "no",
                "Approved by": "-",
            },
        )

    def test_every_kind_in_the_data_model_is_accepted(self):
        for kind in ALL_KINDS:
            result = self.exception(kind, "--alternative", "Reviewed by hand")
            self.assertEqual(result.code, 0, kind)
        rows = self.rows(EX_HEADING)
        self.assertEqual([row["Kind"] for row in rows], ALL_KINDS)
        self.assertEqual([row["ID"] for row in rows], [f"EX-{n:02d}" for n in range(1, 11)])

    def test_exception_without_a_rationale_exits_2(self):
        result = self.check(["exception", "--task", "T013", "--kind", "migration", "--alternative", "x"], self.root)
        self.assertEqual(result.code, 2)
        self.assertIn("--rationale", result.err)
        result = self.exception("migration", "--alternative", "x", rationale="  ")
        self.assertEqual(result.code, 2)
        self.assertIn("--rationale", result.err)
        self.assertEqual(self.rows(EX_HEADING), [])

    def test_alternative_is_required_for_every_kind_except_environment_blocked(self):
        for kind in ALL_KINDS:
            result = self.exception(kind)
            if kind == "environment-blocked":
                self.assertEqual(result.code, 0, kind)
            else:
                self.assertEqual(result.code, 2, kind)
                self.assertIn(f"--alternative is required for {kind}", result.err)
        rows = self.rows(EX_HEADING)
        found = [(row["Kind"], row["Alternative verification"]) for row in rows]
        self.assertEqual(found, [("environment-blocked", "-")])

    def test_needs_approval_is_always_yes_for_the_kinds_beyond_the_agents_authority(self):
        for kind in ALL_KINDS:
            self.exception(kind, "--alternative", "Reviewed by hand")
        for row in self.rows(EX_HEADING):
            expected = "yes" if row["Kind"] in ALWAYS_APPROVED_KINDS else "no"
            self.assertEqual(row["Needs approval"], expected, row["Kind"])

    def test_needs_approval_is_yes_for_an_alternative_of_none(self):
        self.exception("migration", "--alternative", "none")
        self.exception("migration", "--alternative", "None: the data cannot be reproduced")
        self.exception("migration", "--alternative", "Nonexistent rows are checked by hand")
        self.assertEqual([row["Needs approval"] for row in self.rows(EX_HEADING)], ["yes", "yes", "no"])

    def test_needs_approval_is_yes_when_flagged_for_any_other_kind(self):
        self.exception("migration", "--alternative", "Dry run on a copy", "--needs-approval")
        self.assertEqual(self.rows(EX_HEADING)[0]["Needs approval"], "yes")

    def test_approved_by_can_be_given_at_once(self):
        self.exception("legacy", "--alternative", "Characterisation run", "--approved-by", "Lee Sinclair")
        self.assertEqual(self.rows(EX_HEADING)[0]["Approved by"], "Lee Sinclair")

    def test_an_exception_with_no_obligation_is_recorded_for_the_task_alone(self):
        self.assertEqual(self.exception("infrastructure", "--alternative", "Smoke run", task="T015", vo=()).code, 0)
        row = self.rows(EX_HEADING)[0]
        self.assertEqual((row["Task"], row["Obligations"]), ("T015", "-"))

    def test_the_task_must_exist_and_carry_the_obligations(self):
        result = self.exception("migration", "--alternative", "x", task="T099")
        self.assertEqual(result.code, 2)
        self.assertIn("task T099 is not in tasks.md", result.err)
        result = self.exception("migration", "--alternative", "x", vo=("VO-001",))
        self.assertEqual(result.code, 2)
        self.assertIn("obligation VO-001 is not on task T013", result.err)
        self.assertEqual(self.rows(EX_HEADING), [])

    def test_approve_fills_approved_by_on_an_exception(self):
        self.exception("legacy", "--alternative", "Characterisation run")
        result = self.check(["approve", "--id", "EX-01", "--by", "Lee Sinclair"], self.root)
        self.assertEqual((result.code, result.out), (0, "recorded approval of EX-01 by Lee Sinclair\n"), result)
        self.assertEqual(self.rows(EX_HEADING)[0]["Approved by"], "Lee Sinclair")
        self.assertEqual(self.check(["approve", "--id", "EX-02", "--by", "Lee"], self.root).code, 2)

    def test_only_the_evidence_document_is_changed(self):
        before = snapshot(self.root)
        self.exception("legacy", "--alternative", "Characterisation run")
        self.check(["approve", "--id", "EX-01", "--by", "Lee"], self.root)
        self.assert_only_evidence_changed(before)


class DecisionTests(RecordingCase):
    def open(self, *tasks):
        args = ["decision", "open", "--question", "Should an empty cart raise or return zero?", "--tasks"]
        return self.check(args + list(tasks), self.root)

    def test_decision_open_appends_an_open_decision_with_its_tasks(self):
        result = self.open("T013", "T014")
        self.assertEqual((result.code, result.out), (0, "recorded DN-01, holding T013, T014\n"), result)
        (row,) = self.rows(DN_HEADING)
        self.assertRegex(row.pop("Opened"), r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(
            row,
            {
                "ID": "DN-01",
                "Question": "Should an empty cart raise or return zero?",
                "Tasks": "T013, T014",
                "Status": "open",
                "Answer": "-",
                "Decided by": "-",
                "Resolved": "-",
            },
        )

    def test_decision_open_refuses_an_unknown_task(self):
        result = self.open("T013", "T099")
        self.assertEqual(result.code, 2)
        self.assertIn("task T099 is not in tasks.md", result.err)
        self.assertEqual(self.rows(DN_HEADING), [])

    def test_decision_resolve_records_the_answer_and_who_gave_it(self):
        self.open("T013")
        self.open("T014")
        result = self.check(
            ["decision", "resolve", "--id", "DN-02", "--answer", "Return zero", "--by", "Lee Sinclair"], self.root
        )
        self.assertEqual((result.code, result.out), (0, "recorded DN-02 as resolved by Lee Sinclair\n"), result)
        first, second = self.rows(DN_HEADING)
        self.assertEqual(first["Status"], "open")
        found = (second["Status"], second["Answer"], second["Decided by"])
        self.assertEqual(found, ("resolved", "Return zero", "Lee Sinclair"))
        self.assertRegex(second["Resolved"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")

    def test_decision_resolve_requires_answer_and_by(self):
        self.open("T013")
        for args in (["--answer", "Return zero"], ["--by", "Lee"]):
            result = self.check(["decision", "resolve", "--id", "DN-01"] + args, self.root)
            self.assertEqual(result.code, 2, args)
        self.assertEqual(self.rows(DN_HEADING)[0]["Status"], "open")

    def test_decision_resolve_refuses_an_unknown_or_resolved_decision(self):
        self.open("T013")
        resolve = ["decision", "resolve", "--answer", "Return zero", "--by", "Lee", "--id"]
        result = self.check(resolve + ["DN-09"], self.root)
        self.assertEqual(result.code, 2)
        self.assertIn("no decision DN-09", result.err)
        self.assertEqual(self.check(resolve + ["DN-01"], self.root).code, 0)
        result = self.check(resolve + ["DN-01"], self.root)
        self.assertEqual(result.code, 2)
        self.assertIn("DN-01 is already resolved", result.err)

    def test_only_the_evidence_document_is_changed(self):
        before = snapshot(self.root)
        self.open("T013")
        self.check(["decision", "resolve", "--id", "DN-01", "--answer", "Zero", "--by", "Lee"], self.root)
        self.assert_only_evidence_changed(before)


if __name__ == "__main__":
    unittest.main()
