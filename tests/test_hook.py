"""The runtime event handler (contracts/check-cli.md, section hook)."""

import json
import os
import re
import shutil
import unittest

from support import FEATURES, SCRIPT, RepoCase, load_payload, read, snapshot, write

PLAN_WITH_SECTION = "# Plan\n\n## Verification Plan\n\n### Verification commands\n"
OTHER_AGENT_NAMES = ["copilot", "cursor", "gemini", "codex", "windsurf"]


def script_source():
    if not os.path.isfile(SCRIPT):
        raise AssertionError("check script not found: scripts/python/tdd_check.py")
    with open(SCRIPT) as handle:
        return handle.read()


class HookPathTests(RepoCase):
    def setUp(self):
        self.root = self.repo()
        write(self.root, ["specs", "001-demo", "plan.md"], PLAN_WITH_SECTION)
        write(self.root, ["specs", "001-demo", "tdd-evidence.md"], "# TDD Evidence: 001-demo\n")

    def hook(self, payload_name, extra=()):
        return self.check(["hook"] + list(extra), self.root, stdin=load_payload(payload_name, self.root))

    def test_unguarded_file_is_allowed_silently(self):
        result = self.hook("edit-unrelated.json")
        self.assertEqual(result.code, 0)
        self.assertEqual(result.err, "")

    def test_evidence_file_is_refused(self):
        result = self.hook("edit-evidence.json")
        self.assertEqual(result.code, 2)
        self.assertIn("Evidence is written only by the check script", result.err)
        self.assertIn("tdd_check.py run", result.err)

    def test_evidence_file_outside_the_process_is_allowed(self):
        os.remove(os.path.join(self.root, "specs", "001-demo", "plan.md"))
        result = self.hook("edit-evidence.json")
        self.assertEqual(result.code, 0)
        self.assertEqual(result.err, "")

    def test_evidence_file_with_a_plan_lacking_the_section_is_allowed(self):
        write(self.root, ["specs", "001-demo", "plan.md"], "# Plan\n\n## Summary\n")
        result = self.hook("edit-evidence.json")
        self.assertEqual(result.code, 0)
        self.assertEqual(result.err, "")

    def test_default_agent_can_be_named(self):
        mapping = re.search(r"^PAYLOAD_ADAPTERS = \{\s*\"([a-z]+)\"", script_source(), re.MULTILINE)
        self.assertIsNotNone(mapping, "no PAYLOAD_ADAPTERS mapping")
        result = self.hook("edit-evidence.json", ["--agent", mapping.group(1)])
        self.assertEqual(result.code, 2)
        self.assertIn("Evidence is written only by the check script", result.err)

    def test_unknown_agent_exits_2(self):
        result = self.hook("edit-unrelated.json", ["--agent", "nobody"])
        self.assertEqual(result.code, 2)
        self.assertIn("--agent", result.err)


G3_T014 = "G3 T014 VO-002: no valid failing-first record and no exception"
G4_T014 = "G4 T014 VO-002: no valid passing record after its failing-first record"
T014_OPEN = "- [ ] T014 [US1] [VO-002] Implement the sum of item prices in src/cart.py"
T014_DONE = "- [X] T014 [US1] [VO-002] Implement the sum of item prices in src/cart.py"


class SituationCase(RepoCase):
    """The situation table, driven with the recorded payloads.

    ``valid-minimal`` holds a baseline, a valid red record for VO-001 on T011 and a
    valid green record on T012, and nothing for VO-002. So T011, T012 and T015 pass
    the gate and T013 and T014 do not.
    """

    fixture = "valid-minimal"

    def setUp(self):
        self.root = self.repo(self.fixture)
        self.tasks_path = os.path.join(self.feature(self.root), "tasks.md")

    def payload(self, name, **tool_input):
        """A recorded payload with fields of its tool_input replaced."""
        data = json.loads(load_payload(name, self.root))
        data["tool_input"].update(tool_input)
        return json.dumps(data)

    def hook(self, payload):
        return self.check(["hook"], self.root, stdin=payload)

    def edit(self, old, new, **more):
        return self.hook(self.payload("edit-tasks.json", old_string=old, new_string=new, **more))

    def write_tasks(self, content):
        return self.hook(self.payload("write-tasks.json", content=content))

    def multiedit(self, *pairs):
        edits = [{"old_string": old, "new_string": new, "replace_all": False} for old, new in pairs]
        return self.hook(self.payload("multiedit-tasks.json", edits=edits))

    def tasks_text(self):
        return read(self.tasks_path)

    def assert_allowed(self, result):
        self.assertEqual((result.code, result.err, result.out), (0, "", ""), result)

    def assert_refused(self, result, *findings):
        self.assertEqual(result.code, 2, result)
        self.assertEqual(result.out, "")
        for finding in findings:
            self.assertIn(finding, result.err.splitlines())


class TasksEditTests(SituationCase):
    def test_recorded_edit_ticking_a_task_that_passes_is_allowed(self):
        self.assert_allowed(self.hook(load_payload("edit-tasks.json", self.root)))

    def test_newly_completed_behaviour_task_that_passes_is_allowed(self):
        self.assert_allowed(self.edit("- [ ] T012", "- [X] T012"))

    def test_no_test_task_is_allowed(self):
        self.assert_allowed(self.edit("- [ ] T015", "- [X] T015"))

    def test_newly_completed_task_that_fails_the_gate_is_refused(self):
        self.assert_refused(self.edit("- [ ] T014", "- [X] T014"), G3_T014, G4_T014)

    def test_refusal_gives_the_findings_and_the_two_ways_forward(self):
        result = self.edit("- [ ] T014", "- [X] T014")
        self.assertIn("T014 cannot be marked complete", result.err)
        self.assertIn("Two ways forward", result.err)
        self.assertIn("1. Meet the rule", result.err)
        self.assertIn("2. Record an exception with a rationale", result.err)
        self.assertIn("tdd_check.py exception --task T014", result.err)
        self.assertIn("tdd_check.py run", result.err)

    def test_edit_with_no_task_completed_is_allowed(self):
        self.assert_allowed(self.edit("Implement the sum of item prices", "Implement the sum of the item prices"))

    def test_unticking_a_task_is_allowed(self):
        write(self.root, ["specs", "001-demo", "tasks.md"], self.tasks_text().replace(T014_OPEN, T014_DONE))
        self.assert_allowed(self.edit("- [X] T014", "- [ ] T014"))

    def test_editing_a_task_that_is_already_complete_is_allowed(self):
        write(self.root, ["specs", "001-demo", "tasks.md"], self.tasks_text().replace(T014_OPEN, T014_DONE))
        self.assert_allowed(self.edit("Implement the sum of item prices", "Implement the sum of the item prices"))

    def test_lowercase_x_counts_as_complete(self):
        self.assert_refused(self.edit("- [ ] T014", "- [x] T014"), G3_T014)

    def test_replace_all_ticking_several_tasks_is_refused_for_those_that_fail(self):
        result = self.edit("- [ ] ", "- [X] ", replace_all=True)
        self.assert_refused(result, "G3 T013 VO-002: no valid failing-first record and no exception", G3_T014, G4_T014)
        self.assertNotIn("T011 VO-001", result.err)
        self.assertNotIn("T012 VO-001", result.err)
        self.assertIn("T013, T014 cannot be marked complete", result.err)

    def test_without_replace_all_only_the_first_match_changes(self):
        self.assert_allowed(self.edit("- [ ] ", "- [X] ", replace_all=False))

    def test_edit_whose_old_string_is_absent_is_left_to_the_tool(self):
        self.assert_allowed(self.edit("- [ ] T999", "- [X] T999"))

    def test_multiedit_applies_its_edits_in_order(self):
        result = self.multiedit(("- [ ] T014", "- [ ] T014 [P]"), ("- [ ] T014 [P]", "- [X] T014 [P]"))
        self.assert_refused(result, G3_T014)

    def test_multiedit_that_completes_nothing_is_allowed(self):
        self.assert_allowed(self.multiedit(("- [ ] T014", "- [ ] T014 [P]"), ("item prices", "the item prices")))

    def test_recorded_multiedit_shape_ticking_a_passing_task_is_allowed(self):
        self.assert_allowed(self.hook(load_payload("multiedit-tasks.json", self.root)))

    def test_write_with_a_failing_task_ticked_is_refused(self):
        self.assert_refused(self.write_tasks(self.tasks_text().replace(T014_OPEN, T014_DONE)), G3_T014, G4_T014)

    def test_write_with_only_passing_tasks_ticked_is_allowed(self):
        content = self.tasks_text().replace("- [ ] T011", "- [X] T011").replace("- [ ] T012", "- [x] T012")
        self.assert_allowed(self.write_tasks(content))

    def test_write_of_unchanged_content_is_allowed(self):
        self.assert_allowed(self.write_tasks(self.tasks_text()))

    def test_a_task_added_already_complete_is_gated(self):
        """Removing a line and adding it back ticked must not get round the gate."""
        write(self.root, ["specs", "001-demo", "tasks.md"], self.tasks_text().replace(T014_OPEN + "\n", ""))
        self.assert_refused(self.edit("- [ ] T015", T014_DONE + "\n- [ ] T015"), G3_T014)

    def test_write_creating_tasks_md_with_a_failing_task_ticked_is_refused(self):
        content = self.tasks_text().replace(T014_OPEN, T014_DONE)
        os.remove(self.tasks_path)
        self.assert_refused(self.write_tasks(content), G3_T014)

    def test_relative_file_path_is_accepted(self):
        payload = self.payload(
            "edit-tasks.json", file_path="specs/001-demo/tasks.md", old_string="- [ ] T014", new_string="- [X] T014"
        )
        self.assert_refused(self.hook(payload), G3_T014)

    def test_the_hook_changes_no_file(self):
        before = snapshot(self.root)
        self.edit("- [ ] T014", "- [X] T014")
        self.edit("- [ ] T012", "- [X] T012")
        self.assertEqual(snapshot(self.root), before)


class OutsideTheProcessTests(SituationCase):
    def test_unguarded_file_is_allowed_before_any_artefact_is_read(self):
        """plan.md cannot be read as text here, and the edit is still allowed silently."""
        with open(os.path.join(self.feature(self.root), "plan.md"), "wb") as handle:
            handle.write(b"\xff\xfe not text \xff")
        payload = self.payload("edit-tasks.json", file_path=self.root + "/specs/001-demo/notes.md")
        self.assert_allowed(self.hook(payload))
        self.assert_allowed(self.hook(load_payload("edit-unrelated.json", self.root)))

    def test_a_file_that_only_ends_with_a_guarded_name_is_not_guarded(self):
        payload = self.payload("edit-tasks.json", file_path=self.root + "/specs/001-demo/old-tasks.md")
        self.assert_allowed(self.hook(payload))

    def test_feature_without_a_verification_plan_is_not_guarded(self):
        shutil.rmtree(self.feature(self.root))
        shutil.copytree(os.path.join(FEATURES, "plan-no-section"), self.feature(self.root))
        self.assert_allowed(self.edit("- [ ] T014", "- [X] T014"))

    def test_feature_without_a_plan_is_not_guarded(self):
        os.remove(os.path.join(self.feature(self.root), "plan.md"))
        self.assert_allowed(self.edit("- [ ] T014", "- [X] T014"))


class OtherFeatureTests(RepoCase):
    def test_a_feature_other_than_the_active_one_is_guarded_all_the_same(self):
        root = self.repo("valid-minimal", feature_rel=os.path.join("specs", "002-other"), point_feature_json=False)
        write(root, [".specify", "feature.json"], json.dumps({"feature_directory": "specs/001-demo"}))
        os.makedirs(os.path.join(root, "specs", "001-demo"))
        data = json.loads(load_payload("edit-tasks.json", root))
        data["tool_input"].update(
            file_path=root + "/specs/002-other/tasks.md", old_string="- [ ] T014", new_string="- [X] T014"
        )
        result = self.check(["hook"], root, stdin=json.dumps(data))
        self.assertEqual(result.code, 2, result)
        self.assertIn(G3_T014, result.err)
        data["tool_input"]["file_path"] = root + "/specs/002-other/tdd-evidence.md"
        result = self.check(["hook"], root, stdin=json.dumps(data))
        self.assertEqual(result.code, 2, result)
        self.assertIn("Evidence is written only by the check script", result.err)


class EvidenceEditTests(SituationCase):
    def test_every_edit_tool_is_refused_on_the_evidence_document(self):
        for name in ("edit-evidence.json", "write-evidence.json", "multiedit-evidence.json"):
            result = self.hook(load_payload(name, self.root))
            self.assertEqual(result.code, 2, name)
            self.assertIn("Evidence is written only by the check script", result.err, name)


class PlanGuardTests(SituationCase):
    """An edit that would remove a heading the checks read is refused (check-cli-changes.md section 5)."""

    fixture = "checklist-valid"
    HEADING_MESSAGE = (
        "The Verification Plan and its Behaviour checklist sub-heading are read by the checks "
        "and cannot be removed through the agent's edit tools"
    )

    def plan_text(self):
        return read(self.feature(self.root), "plan.md")

    def edit_plan(self, old, new):
        return self.hook(self.payload("edit-plan.json", old_string=old, new_string=new))

    def assert_heading_refused(self, result, heading):
        self.assertEqual(result.code, 2, result)
        self.assertEqual(result.out, "")
        self.assertIn(self.HEADING_MESSAGE, " ".join(result.err.split()))
        self.assertIn(heading, result.err)

    def test_an_edit_removing_the_checklist_heading_is_refused(self):
        result = self.edit_plan("### Behaviour checklist", "### Notes")
        self.assert_heading_refused(result, "### Behaviour checklist")

    def test_a_write_removing_the_checklist_heading_is_refused(self):
        content = self.plan_text().replace("### Behaviour checklist", "### Notes")
        result = self.hook(self.payload("write-plan.json", content=content))
        self.assert_heading_refused(result, "### Behaviour checklist")

    def test_a_multiedit_removing_the_checklist_heading_is_refused(self):
        edits = [{"old_string": "### Behaviour checklist", "new_string": "### Notes", "replace_all": False}]
        result = self.hook(self.payload("multiedit-plan.json", edits=edits))
        self.assert_heading_refused(result, "### Behaviour checklist")

    def test_an_edit_removing_the_verification_plan_heading_is_refused(self):
        result = self.edit_plan("## Verification Plan", "## Testing notes")
        self.assert_heading_refused(result, "## Verification Plan")

    def test_recorded_edit_removing_the_checklist_heading_is_refused(self):
        result = self.hook(load_payload("edit-plan-remove-checklist-heading.json", self.root))
        self.assert_heading_refused(result, "### Behaviour checklist")

    def test_recorded_edit_removing_the_verification_plan_heading_is_refused(self):
        result = self.hook(load_payload("edit-plan-remove-verification-plan.json", self.root))
        self.assert_heading_refused(result, "## Verification Plan")

    def test_an_edit_that_rewords_text_and_keeps_both_headings_is_allowed(self):
        self.assert_allowed(self.edit_plan("Add a cart total.", "Add the cart total."))
        self.assert_allowed(self.hook(load_payload("edit-plan.json", self.root)))

    def test_a_write_that_keeps_both_headings_is_allowed(self):
        content = self.plan_text().replace("Add a cart total.", "Add the cart total.")
        self.assert_allowed(self.hook(self.payload("write-plan.json", content=content)))

    def test_adding_the_checklist_heading_to_a_plan_that_lacks_it_is_allowed(self):
        write(self.root, ["specs", "001-demo", "plan.md"], PLAN_WITH_SECTION)
        content = PLAN_WITH_SECTION + "\n### Behaviour checklist\n"
        self.assert_allowed(self.hook(self.payload("write-plan.json", content=content)))

    def test_an_older_plan_with_neither_heading_is_not_guarded(self):
        write(self.root, ["specs", "001-demo", "plan.md"], "# Plan\n\n## Summary\n\nAdd a cart total.\n")
        self.assert_allowed(self.edit_plan("Add a cart total.", "Add the cart total."))

    def test_an_older_plan_with_the_verification_plan_cannot_lose_it_either(self):
        write(self.root, ["specs", "001-demo", "plan.md"], PLAN_WITH_SECTION)
        result = self.edit_plan("## Verification Plan", "## Testing notes")
        self.assert_heading_refused(result, "## Verification Plan")

    def test_an_edit_to_the_checklist_is_allowed_without_reading_any_artefact(self):
        with open(os.path.join(self.feature(self.root), "plan.md"), "wb") as handle:
            handle.write(b"\xff\xfe not text \xff")
        self.assert_allowed(self.hook(load_payload("edit-checklist.json", self.root)))

    def test_a_relative_path_is_guarded_too(self):
        payload = self.payload(
            "edit-plan.json", file_path="specs/001-demo/plan.md", old_string="### Behaviour checklist", new_string="x"
        )
        self.assert_heading_refused(self.hook(payload), "### Behaviour checklist")

    def test_the_hook_changes_no_file(self):
        before = snapshot(self.root)
        self.edit_plan("### Behaviour checklist", "### Notes")
        self.assertEqual(snapshot(self.root), before)


class FailClosedTests(SituationCase):
    """The stop fails closed, for the two guarded files only."""

    def test_unreadable_payload_naming_a_guarded_file_is_refused(self):
        result = self.hook('{"tool_name": "Edit", "tool_input": {"file_path": "specs/001-demo/tasks.md", ')
        self.assertEqual(result.code, 2)
        self.assertIn("cannot read the tool call payload", result.err)

    def test_unreadable_payload_naming_no_guarded_file_is_allowed(self):
        self.assert_allowed(self.hook('{"tool_name": "Edit", "tool_input": {"file_path": "src/notes.txt", '))
        self.assert_allowed(self.hook(""))

    def test_payload_without_the_edit_fields_is_refused_for_a_guarded_file(self):
        data = json.loads(load_payload("edit-tasks.json", self.root))
        del data["tool_input"]["old_string"]
        result = self.hook(json.dumps(data))
        self.assertEqual(result.code, 2)
        self.assertIn("cannot read the tool call payload", result.err)

    def test_unknown_tool_on_a_guarded_file_is_refused(self):
        data = json.loads(load_payload("edit-tasks.json", self.root))
        data["tool_name"] = "Patch"
        result = self.hook(json.dumps(data))
        self.assertEqual(result.code, 2)
        self.assertIn("Patch", result.err)

    def test_unreadable_plan_is_refused_for_a_guarded_file(self):
        with open(os.path.join(self.feature(self.root), "plan.md"), "wb") as handle:
            handle.write(b"\xff\xfe not text \xff")
        result = self.edit("- [ ] T014", "- [X] T014")
        self.assertEqual(result.code, 2)
        self.assertIn("cannot read plan.md", result.err)

    def test_malformed_evidence_is_refused_when_a_task_is_completed(self):
        shutil.rmtree(self.feature(self.root))
        shutil.copytree(os.path.join(FEATURES, "parse-evidence-wrong-header"), self.feature(self.root))
        result = self.edit("- [ ] T012", "- [X] T012")
        self.assertEqual(result.code, 2)
        self.assertIn("EVIDENCE tdd-evidence.md: header row under '## Test execution records'", result.err)

    def test_malformed_evidence_does_not_stop_an_edit_that_completes_nothing(self):
        shutil.rmtree(self.feature(self.root))
        shutil.copytree(os.path.join(FEATURES, "parse-evidence-wrong-header"), self.feature(self.root))
        self.assert_allowed(self.edit("Implement the sum of item prices", "Implement the sum of the item prices"))


class AgentNeutralityTests(unittest.TestCase):
    """FR-061: reading the payload is the only agent-specific code."""

    def test_adapters_are_held_in_one_mapping_keyed_by_agent_name(self):
        source = script_source()
        found = re.search(r"^PAYLOAD_ADAPTERS = \{(.*?)^\}", source, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(found, "no PAYLOAD_ADAPTERS mapping")
        self.assertRegex(found.group(1), r'"claude":')

    def test_no_agent_name_appears_outside_the_mapping(self):
        source = script_source()
        found = re.search(r"^PAYLOAD_ADAPTERS = \{(.*?)^\}", source, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(found, "no PAYLOAD_ADAPTERS mapping")
        outside = (source[: found.start()] + source[found.end() :]).lower()
        self.assertNotIn("claude", outside)
        for name in OTHER_AGENT_NAMES:
            self.assertNotIn(name, source.lower())


if __name__ == "__main__":
    unittest.main()
