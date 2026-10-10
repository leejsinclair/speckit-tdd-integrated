"""The command runner and the evidence ledger (contracts/check-cli.md, run)."""

import time
import unittest

from support import RunCase, records

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


if __name__ == "__main__":
    unittest.main()
