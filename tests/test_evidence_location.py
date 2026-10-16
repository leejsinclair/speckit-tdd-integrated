"""Where the evidence document lives (contracts/check-cli-changes.md section 2, research D10, FR-041)."""

import json
import os
import unittest

from support import FEATURE_REL, RepoCase, load_payload, read, snapshot, write

TWO_PLACES = "evidence is in two places: tdd-evidence.md and tests/tdd-evidence.md; keep one and remove the other"
TOP = os.path.join(FEATURE_REL, "tdd-evidence.md")
TESTS = os.path.join(FEATURE_REL, "tests", "tdd-evidence.md")

# One invocation of every subcommand that reads or writes the evidence document.
EVIDENCE_COMMANDS = {
    "run": ["run", "--phase", "checkpoint", "--command", "suite"],
    "classify": ["classify", "--seq", "1", "--as", "assertion"],
    "exception": [
        "exception", "--task", "T014", "--kind", "legacy", "--rationale", "No seam", "--alternative", "Reviewed",
    ],  # fmt: skip
    "expectation": [
        "expectation", "--task", "T012", "--tests", "tests/test_cart.py", "--requirement", "FR-001",
        "--justification", "Mistyped",
    ],  # fmt: skip
    "decision": ["decision", "open", "--question", "Zero or raise?", "--tasks", "T012"],
    "approve": ["approve", "--id", "EX-01", "--by", "Sam"],
    "gate": ["gate", "--all"],
    "status": ["status"],
    "compliance": ["compliance"],
}


def exists(root, rel):
    return os.path.exists(os.path.join(root, rel))


class SingleLocationTests(RepoCase):
    def test_top_level_document_is_read_and_appended_to_there(self):
        root = self.repo("evidence-top")
        before = snapshot(root)
        result = self.check(["run", "--phase", "checkpoint", "--command", "suite"], root)
        self.assertEqual(result.code, 0, result)
        after = snapshot(root)
        self.assertEqual({name for name in after if before.get(name) != after[name]}, {TOP})
        self.assertFalse(exists(root, os.path.join(FEATURE_REL, "tests")))
        self.assertIn("| checkpoint |", read(root, TOP))

    def test_tests_document_is_read_and_appended_to_there(self):
        root = self.repo("evidence-tests")
        before = snapshot(root)
        result = self.check(["run", "--phase", "checkpoint", "--command", "suite"], root)
        self.assertEqual(result.code, 0, result)
        after = snapshot(root)
        self.assertEqual({name for name in after if before.get(name) != after[name]}, {TESTS})
        self.assertFalse(exists(root, TOP))
        self.assertIn("| checkpoint |", read(root, TESTS))

    def test_neither_document_creates_tests_and_the_document_there(self):
        root = self.repo("evidence-top")
        os.remove(os.path.join(root, TOP))
        result = self.check(["run", "--phase", "baseline", "--command", "suite"], root)
        self.assertEqual(result.code, 0, result)
        self.assertTrue(exists(root, TESTS))
        self.assertFalse(exists(root, TOP))
        self.assertIn("| baseline |", read(root, TESTS))

    def test_status_is_the_same_wherever_the_document_is(self):
        top = self.check(["status"], self.repo("evidence-top"))
        tests = self.check(["status"], self.repo("evidence-tests"))
        self.assertEqual(top.code, 0, top)
        self.assertEqual((tests.code, tests.out), (top.code, top.out))

    def test_gate_all_is_the_same_wherever_the_document_is(self):
        top = self.check(["gate", "--all"], self.repo("evidence-top"))
        tests = self.check(["gate", "--all"], self.repo("evidence-tests"))
        self.assertEqual((tests.code, tests.out), (top.code, top.out))


class SubjectTests(RepoCase):
    def test_top_level_document_keeps_its_0_1_0_subject(self):
        result = self.check(["compliance"], self.repo("evidence-top"))
        self.assertIn("C6 tdd-evidence.md: no checkpoint record", result.out.splitlines())

    def test_document_in_tests_is_named_with_its_folder(self):
        result = self.check(["compliance"], self.repo("evidence-tests"))
        self.assertIn("C6 tests/tdd-evidence.md: no checkpoint record", result.out.splitlines())
        self.assertNotIn("C6 tdd-evidence.md: no checkpoint record", result.out.splitlines())

    def test_malformed_document_in_tests_is_named_with_its_folder(self):
        root = self.repo("evidence-tests")
        text = read(root, TESTS).replace("| Seq | Time |", "| Number | Time |", 1)
        write(root, TESTS.split(os.sep), text)
        result = self.check(["gate", "--all"], root)
        self.assertEqual(result.code, 1, result)
        self.assertIn("EVIDENCE tests/tdd-evidence.md:", result.out)


class BothLocationsTests(RepoCase):
    def test_every_subcommand_refuses_and_changes_nothing(self):
        for name, args in sorted(EVIDENCE_COMMANDS.items()):
            with self.subTest(subcommand=name):
                root = self.repo("evidence-both")
                before = snapshot(root)
                result = self.check(args, root)
                self.assertEqual(result.code, 2, result)
                self.assertIn(TWO_PLACES, result.err)
                self.assertEqual(snapshot(root), before)

    def test_json_form_carries_the_message(self):
        result = self.check(["status", "--json"], self.repo("evidence-both"))
        self.assertEqual(result.code, 2, result)
        self.assertEqual(json.loads(result.out)["error"], TWO_PLACES)


class HookTests(RepoCase):
    def test_edit_of_evidence_in_tests_is_refused(self):
        root = self.repo("evidence-tests")
        result = self.check(["hook"], root, stdin=load_payload("edit-evidence-in-tests.json", root))
        self.assertEqual(result.code, 2, result)
        self.assertIn("Evidence is written only by the check script", result.err)

    def test_edit_of_evidence_in_tests_of_a_feature_with_no_plan_section_is_allowed(self):
        root = self.repo("evidence-tests")
        write(root, [FEATURE_REL, "plan.md"], "# Plan\n\n## Summary\n")
        result = self.check(["hook"], root, stdin=load_payload("edit-evidence-in-tests.json", root))
        self.assertEqual((result.code, result.err), (0, ""), result)

    def test_marking_a_task_complete_is_refused_when_evidence_is_in_both_places(self):
        root = self.repo("evidence-both")
        before = snapshot(root)
        payload = json.loads(load_payload("edit-tasks.json", root))
        payload["tool_input"].update(old_string="- [ ] T012", new_string="- [X] T012")
        result = self.check(["hook"], root, stdin=json.dumps(payload))
        self.assertEqual(result.code, 2, result)
        self.assertIn(TWO_PLACES, result.err)
        self.assertEqual(snapshot(root), before)


if __name__ == "__main__":
    unittest.main()
