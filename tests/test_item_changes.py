"""Fixing behaviour items at the baseline, item change records, and gate rules G10 and G11.

Contracts: check-cli-changes.md sections 3 and 4, data-model.md (Item Baseline, Item Change Record).
"""

import json
import os
import unittest

from fixtures.make_features import CHANGED_FP, CL_ITEM_1, CL_ITEM_2, CL_ITEM_3, CL_ITEM_5, item_fp
from support import (
    EVIDENCE_REL,
    FEATURE_REL,
    RepoCase,
    RunCase,
    load_payload,
    read,
    snapshot,
    table_rows,
    write,
)

BASELINE_HEADING = "## Behaviour items at baseline"
CHANGES_HEADING = "## Behaviour item changes"
TASKS_REL = [FEATURE_REL, "tasks.md"]
JUSTIFY = ["--justification", "The expected total was mistyped"]
G10_CHANGED = "G10 T014 BI-002: changed since the baseline and no change is recorded"
G10_REMOVED = "G10 T014 BI-004: removed since the baseline and no removal is recorded"
G10_AWAITING = "G10 T014 BI-002: change BX-01 alters behaviour and awaits approval"
G10_REUSED = "G10 T014 BI-004: removed since the baseline and its id is reused"
G11_B1 = "G11 T014 FR-004: B1: no behaviour item expresses it"
G11_B5 = "G11 T014 BI-001: B5: `src/cart.py` is a path-shaped token that spec.md does not name"


def item_lines(out):
    return [line for line in out.splitlines() if line.startswith(("G10 ", "G11 "))]


def evidence_of(root):
    for rel in (EVIDENCE_REL, os.path.join(FEATURE_REL, "tdd-evidence.md")):
        if os.path.isfile(os.path.join(root, rel)):
            return read(root, rel)
    raise AssertionError("no evidence document")


class ItemBaselineRowsTests(RunCase):
    fixture = "checklist-valid"

    def test_the_first_run_writes_a_row_per_item_with_that_records_sequence_number(self):
        self.baseline()
        rows = table_rows(evidence_text_of(self.root), BASELINE_HEADING)
        self.assertEqual([row["Item"] for row in rows], ["BI-001", "BI-002", "BI-003"])
        self.assertEqual({row["Seq"] for row in rows}, {"1"})
        self.assertEqual(
            [(row["Verified by"], row["Fingerprint"]) for row in rows],
            [("VO-001", item_fp(CL_ITEM_1)), ("VO-002", item_fp(CL_ITEM_2)), ("exemption FR-003", item_fp(CL_ITEM_3))],
        )

    def test_the_change_table_is_written_empty_beside_it(self):
        self.baseline()
        self.assertEqual(table_rows(evidence_text_of(self.root), CHANGES_HEADING), [])

    def test_a_later_run_adds_a_row_only_for_an_item_added_since(self):
        self.baseline()
        before = table_rows(evidence_text_of(self.root), BASELINE_HEADING)
        checklist = os.path.join(self.root, FEATURE_REL, "tests", "behaviour-checklist.md")
        text = read(self.root, FEATURE_REL, "tests", "behaviour-checklist.md")
        write(self.root, [FEATURE_REL, "tests", "behaviour-checklist.md"], text + _extra_item())
        self.assertTrue(os.path.isfile(checklist))
        result = self.run_phase("checkpoint", "suite")
        self.assertEqual(result.code, 0, result)
        after = table_rows(evidence_text_of(self.root), BASELINE_HEADING)
        self.assertEqual(after[: len(before)], before)
        self.assertEqual([row["Item"] for row in after[len(before) :]], ["BI-009"])
        self.assertEqual(after[-1]["Seq"], "2")

    def test_an_existing_row_is_never_changed_by_a_later_run(self):
        self.baseline()
        write(self.root, [FEATURE_REL, "tests", "behaviour-checklist.md"], _reword(self.root))
        before = table_rows(evidence_text_of(self.root), BASELINE_HEADING)
        self.run_phase("checkpoint", "suite")
        self.assertEqual(table_rows(evidence_text_of(self.root), BASELINE_HEADING), before)


class OlderFeatureEvidenceTests(RunCase):
    fixture = "valid-minimal"

    def test_an_older_features_evidence_gains_neither_table(self):
        self.baseline()
        text = evidence_text_of(self.root)
        self.assertNotIn(BASELINE_HEADING, text)
        self.assertNotIn(CHANGES_HEADING, text)
        self.assertEqual(
            [line for line in text.splitlines() if line.startswith("## ")],
            ["## Summary", "## Baseline", "## Test execution records", "## Exceptions", "## Expectation changes",
             "## Decisions"],
        )  # fmt: skip


def evidence_text_of(root):
    with open(os.path.join(root, EVIDENCE_REL)) as handle:
        return handle.read()


def _extra_item():
    return (
        "\n- **BI-009** Expresses: FR-001. Verified by: VO-001.\n"
        "  - **Given** a cart with one item\n  - **When** the shopper asks for the total\n"
        "  - **Then** the total is that item's price\n"
    )


def _reword(root):
    text = read(root, FEATURE_REL, "tests", "behaviour-checklist.md")
    return text.replace("the total is 7", "the total is 8")


class ExpectationItemTests(RepoCase):
    def item_change(self, fixture, item, *extra, requirements=("FR-002", "US1-AS2")):
        root = self.repo(fixture)
        result = self.check(
            ["expectation", "--item", item, "--requirement", *requirements, *JUSTIFY, *extra], root
        )  # fmt: skip
        return root, result

    def test_a_changed_item_is_recorded_with_its_current_fingerprint(self):
        root, result = self.item_change("item-changed", "BI-002")
        self.assertEqual(result.code, 0, result)
        self.assertIn("BX-01", result.out)
        row = table_rows(read(root, FEATURE_REL, "tdd-evidence.md"), CHANGES_HEADING)[0]
        self.assertEqual(
            (row["ID"], row["Item"], row["Requirements"], row["Alters behaviour"], row["Approved by"]),
            ("BX-01", "BI-002", "FR-002, US1-AS2", "no", "-"),
        )
        self.assertEqual(row["New fingerprint"], CHANGED_FP)
        self.assertEqual(row["Justification"], "The expected total was mistyped")

    def test_a_removed_item_is_recorded_as_removed(self):
        root, result = self.item_change("item-removed", "BI-004", requirements=("SC-001",))
        self.assertEqual(result.code, 0, result)
        row = table_rows(read(root, FEATURE_REL, "tdd-evidence.md"), CHANGES_HEADING)[0]
        self.assertEqual((row["Item"], row["New fingerprint"]), ("BI-004", "removed"))

    def test_alters_behaviour_is_recorded_and_the_record_can_be_approved(self):
        root, result = self.item_change("item-changed", "BI-002", "--alters-behaviour")
        self.assertEqual(result.code, 0, result)
        row = table_rows(read(root, FEATURE_REL, "tdd-evidence.md"), CHANGES_HEADING)[0]
        self.assertEqual((row["Alters behaviour"], row["Approved by"]), ("yes", "-"))
        approved = self.check(["approve", "--id", "BX-01", "--by", "Lee Sinclair"], root)
        self.assertEqual(approved.code, 0, approved)
        row = table_rows(read(root, FEATURE_REL, "tdd-evidence.md"), CHANGES_HEADING)[0]
        self.assertEqual(row["Approved by"], "Lee Sinclair")

    def test_the_next_record_takes_the_next_id(self):
        root = self.repo("item-change-recorded")
        path = [FEATURE_REL, "tests", "behaviour-checklist.md"]
        text = read(root, *path)
        start = text.index("- **BI-004**")
        write(root, path, text[:start].rstrip("\n") + "\n")
        result = self.check(["expectation", "--item", "BI-004", "--requirement", "SC-001", *JUSTIFY], root)
        self.assertEqual(result.code, 0, result)
        self.assertIn("BX-02", result.out)
        rows = table_rows(read(root, FEATURE_REL, "tdd-evidence.md"), CHANGES_HEADING)
        self.assertEqual([row["ID"] for row in rows], ["BX-01", "BX-02"])

    def test_an_item_with_no_baseline_row_is_refused(self):
        root, result = self.item_change("item-added-after-baseline", "BI-005")
        self.assertEqual(result.code, 2, result)
        self.assertIn("BI-005", result.err)
        self.assertEqual(table_rows(read(root, FEATURE_REL, "tdd-evidence.md"), CHANGES_HEADING), [])

    def test_an_unchanged_item_is_refused(self):
        root, result = self.item_change("items-baseline", "BI-001", requirements=("FR-001",))
        self.assertEqual(result.code, 2, result)
        self.assertIn("unchanged", result.err)

    def test_an_item_that_does_not_exist_is_refused(self):
        _root, result = self.item_change("items-baseline", "BI-099", requirements=("FR-001",))
        self.assertEqual(result.code, 2, result)

    def test_a_reused_id_is_refused_and_nothing_is_recorded(self):
        root = self.repo("item-id-reused")
        before = snapshot(root)
        result = self.check(["expectation", "--item", "BI-004", "--requirement", "SC-001", *JUSTIFY], root)
        self.assertEqual(result.code, 2, result)
        self.assertIn("reused", result.err)
        self.assertEqual(snapshot(root), before)

    def test_item_cannot_be_combined_with_task_or_tests(self):
        root = self.repo("item-changed")
        before = snapshot(root)
        for extra in (["--task", "T012"], ["--tests", "tests/test_cart.py"]):
            result = self.check(["expectation", "--item", "BI-002", "--requirement", "FR-002", *JUSTIFY, *extra], root)
            self.assertEqual(result.code, 2, extra)
        self.assertEqual(snapshot(root), before)

    def test_requirement_and_justification_are_required(self):
        root = self.repo("item-changed")
        self.assertEqual(self.check(["expectation", "--item", "BI-002", *JUSTIFY], root).code, 2)
        self.assertEqual(self.check(["expectation", "--item", "BI-002", "--requirement", "FR-002"], root).code, 2)

    def test_the_task_form_still_needs_its_task_and_tests(self):
        root = self.repo("item-changed")
        result = self.check(["expectation", "--requirement", "FR-002", *JUSTIFY], root)
        self.assertEqual(result.code, 2)
        self.assertIn("usage:", result.err)


class G10Tests(RepoCase):
    def gate(self, fixture, task="T014", *extra):
        root = self.repo(fixture)
        return root, self.check(["gate", "--task", task, *extra], root)

    def assert_item_findings(self, fixture, *expected, task="T014"):
        _root, result = self.gate(fixture, task)
        self.assertEqual(item_lines(result.out), list(expected), result.out)
        self.assertEqual(result.code, 1 if expected else 0, result)

    def test_a_changed_item_with_no_record_holds_its_tasks(self):
        self.assert_item_findings("item-changed", G10_CHANGED)

    def test_a_removed_item_with_no_record_holds_its_tasks(self):
        self.assert_item_findings("item-removed", G10_REMOVED)

    def test_a_change_that_alters_behaviour_awaits_approval(self):
        self.assert_item_findings("item-change-awaiting-approval", G10_AWAITING)

    def test_a_reused_id_holds_its_tasks(self):
        self.assert_item_findings("item-id-reused", G10_REUSED)

    def test_a_task_that_names_no_obligation_of_the_item_is_not_held(self):
        self.assert_item_findings("item-changed", task="T012")

    def test_accepted_changes_and_unchanged_items_pass(self):
        for fixture in (
            "items-baseline",
            "item-change-recorded",
            "item-change-approved",
            "item-removal-recorded",
            "item-added-after-baseline",
            "item-relinked",
        ):
            with self.subTest(fixture=fixture):
                root, result = self.gate(fixture)
                self.assertEqual((result.code, result.out), (0, "gate T014: passed\n"), result)
                self.assertEqual(snapshot(root), snapshot(root))

    def test_gate_all_reports_g10_for_completed_tasks(self):
        root = self.repo("item-changed")
        text = read(root, FEATURE_REL, "tasks.md")
        write(root, TASKS_REL, text.replace("- [ ] T013", "- [X] T013").replace("- [ ] T014", "- [X] T014"))
        result = self.check(["gate", "--all"], root)
        self.assertEqual(result.code, 1, result)
        earlier = G10_CHANGED.replace("T014", "T013")
        self.assertEqual(item_lines(result.out), [earlier, G10_CHANGED])

    def test_the_hook_refuses_to_mark_complete_a_task_held_by_g10(self):
        root = self.repo("item-changed")
        payload = json.loads(load_payload("edit-tasks.json", root))
        payload["tool_input"].update(old_string="- [ ] T014", new_string="- [X] T014")
        result = self.check(["hook"], root, stdin=json.dumps(payload))
        self.assertEqual(result.code, 2, result)
        self.assertIn(G10_CHANGED, result.err.splitlines())

    def test_the_gate_changes_no_file(self):
        root = self.repo("item-changed")
        before = snapshot(root)
        self.check(["gate", "--task", "T014"], root)
        self.assertEqual(snapshot(root), before)

    def test_json_carries_the_finding(self):
        _root, result = self.gate("item-changed", "T014", "--json")
        data = json.loads(result.out)
        self.assertIn(
            ("G10", "T014 BI-002", "changed since the baseline and no change is recorded"),
            [(f["rule"], f["subject"], f["reason"]) for f in data["findings"]],
        )


class FixedItemListTests(unittest.TestCase):
    def test_the_added_item_fixture_holds_a_fifth_item(self):
        self.assertEqual(CL_ITEM_5["id"], "BI-005")


if __name__ == "__main__":
    unittest.main()
