"""Time limits at 200 tasks and 1,000 evidence records (plan.md, Performance Goals).

These tests measure code that already exists, so they are expected to pass on their first
run (plan.md, Constitution Check IV, second recorded exception). Each limit was shown to
be reachable by running the same test against a larger generated feature: set
``TDD_PERF_SCALE`` to multiply the feature's size, for example ``TDD_PERF_SCALE=20``. The
runs are recorded in specs/001-integrated-tdd/quickstart.md, Validation results.
"""

import json
import os
import shutil
import tempfile
import time
import unittest

from fixtures.make_features import PLAN, baseline, chain, checkpoint, evidence, green, rec, red
from support import FEATURE_REL, run_check, write

SCALE = max(1, int(os.environ.get("TDD_PERF_SCALE", "1")))
OBLIGATIONS = 100 * SCALE  # two tasks each: 200 tasks at scale 1
RECORDS = 1000 * SCALE

HOOK_LIMIT = 1.0
CHECK_LIMIT = 2.0


def build_feature(root):
    """A feature with OBLIGATIONS obligations, twice as many tasks and about RECORDS records."""
    ids = [f"VO-{n:03d}" for n in range(1, OBLIGATIONS + 1)]
    spec = "# Feature Specification: Performance\n\n## Requirements\n\n### Functional Requirements\n\n"
    spec += "".join(f"- **FR-{n:03d}**: The system MUST do thing {n}.\n" for n in range(1, OBLIGATIONS + 1))
    head = PLAN.split("### Verification obligations")[0]
    rows = "".join(
        f"| {ident} | FR-{n:03d} | Scenario {n} | Outcome {n} | unit | planned |\n"
        for n, ident in enumerate(ids, 1)
    )
    plan = (
        head
        + "### Verification obligations\n\n| ID | Requirements | Scenario | Expected outcome | Level | Origin |\n"
        "|----|--------------|----------|------------------|-------|--------|\n"
        + rows
        + "\n### Verification exemptions\n\n| Requirement | Reason | Alternative verification |\n"
        "|-------------|--------|--------------------------|\n| None | - | - |\n"
    )
    lines = ["# Tasks\n\n"]
    records = [baseline()]
    extra = max(0, -(-(RECORDS - 2 - 2 * OBLIGATIONS) // OBLIGATIONS))
    for n, ident in enumerate(ids, 1):
        test_task, behaviour_task = f"T{2 * n - 1:03d}", f"T{2 * n:03d}"
        lines.append(f"- [X] {test_task} [US1] [{ident}] Write the failing test {n} in tests/test_{n}.py\n")
        lines.append(f"- [X] {behaviour_task} [US1] [{ident}] Implement behaviour {n} in src/b{n}.py\n")
        records.append(red(test_task, ident))
        records.append(green(behaviour_task, ident))
        for _ in range(extra):
            same = records[-1]["Fingerprint"]
            files = "tests/test_cart.py"
            records.append(rec(behaviour_task, ident, "refactor", "unit", "pass", "pass", "yes", "-", files, same))
    records.append(checkpoint())
    write(root, [FEATURE_REL, "spec.md"], spec)
    write(root, [FEATURE_REL, "plan.md"], plan)
    write(root, [FEATURE_REL, "tasks.md"], "".join(lines))
    write(root, [FEATURE_REL, "tdd-evidence.md"], evidence(records))
    return len(chain(records))


class PerformanceCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="tdd-perf-")
        cls.addClassCleanup(shutil.rmtree, cls.root, True)
        cls.record_count = build_feature(cls.root)
        write(cls.root, [".specify", "feature.json"], json.dumps({"feature_directory": FEATURE_REL}))

    def timed(self, args, stdin=None):
        started = time.perf_counter()
        result = run_check(args, self.root, stdin=stdin)
        return time.perf_counter() - started, result

    def test_the_generated_feature_has_the_stated_size(self):
        self.assertGreaterEqual(self.record_count, RECORDS)
        with open(os.path.join(self.root, FEATURE_REL, "tasks.md")) as handle:
            self.assertEqual(sum(1 for line in handle if line.startswith("- [")), 2 * OBLIGATIONS)

    def assert_within(self, args, limit, codes=(0,)):
        elapsed, result = self.timed(args)
        self.assertIn(result.code, codes, result.err or result.out[:300])
        self.assertLess(elapsed, limit, f"{' '.join(args)} took {elapsed:.2f}s, limit {limit}s")

    def test_plan_is_within_the_limit(self):
        self.assert_within(["plan"], CHECK_LIMIT)

    def test_tasks_is_within_the_limit(self):
        self.assert_within(["tasks"], CHECK_LIMIT)

    def test_gate_all_is_within_the_limit(self):
        self.assert_within(["gate", "--all"], CHECK_LIMIT)

    def test_status_is_within_the_limit(self):
        self.assert_within(["status"], CHECK_LIMIT)

    def test_compliance_is_within_the_limit(self):
        self.assert_within(["compliance"], CHECK_LIMIT, codes=(0, 1))

    def payload(self, file_path, old, new):
        return json.dumps(
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": file_path, "old_string": old, "new_string": new, "replace_all": False},
            }
        )

    def test_hook_on_a_task_completion_decides_within_the_limit(self):
        tasks = os.path.join(self.root, FEATURE_REL, "tasks.md")
        last = f"T{2 * OBLIGATIONS:03d}"
        with open(tasks) as handle:
            text = handle.read()
        write(self.root, [FEATURE_REL, "tasks.md"], text.replace(f"- [X] {last} ", f"- [ ] {last} "))
        self.addCleanup(write, self.root, [FEATURE_REL, "tasks.md"], text)
        elapsed, result = self.timed(["hook"], self.payload(tasks, f"- [ ] {last} ", f"- [X] {last} "))
        self.assertEqual((result.code, result.err), (0, ""), result)
        self.assertLess(elapsed, HOOK_LIMIT, f"hook took {elapsed:.2f}s, limit {HOOK_LIMIT}s")

    def test_hook_on_an_unguarded_file_returns_without_opening_any_artefact(self):
        """An unreadable plan.md would fail a hook that opened it: this one does not."""
        scratch = tempfile.mkdtemp(prefix="tdd-perf-")
        self.addCleanup(shutil.rmtree, scratch, True)
        with open(os.path.join(scratch, "plan.md"), "wb") as handle:
            handle.write(b"\xff\xfe")
        started = time.perf_counter()
        result = run_check(
            ["hook"], scratch, stdin=self.payload(os.path.join(scratch, "notes.txt"), "a", "b")
        )
        elapsed = time.perf_counter() - started
        self.assertEqual((result.code, result.err), (0, ""), result)
        self.assertLess(elapsed, HOOK_LIMIT)


if __name__ == "__main__":
    unittest.main()
