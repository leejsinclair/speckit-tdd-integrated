"""The runtime event handler (contracts/check-cli.md, section hook)."""

import os
import re
import unittest

from support import SCRIPT, RepoCase, load_payload, write

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
