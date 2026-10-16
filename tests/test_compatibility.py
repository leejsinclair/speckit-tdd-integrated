"""The 0.1.0 and 0.2.0 outputs are unchanged on every fixture that existed then (FR-002, FR-022, SC-006, D5).

``tests/fixtures/golden_0_1_0.json`` holds the exit code and standard output of the
0.1.0 script for ``plan``, ``tasks``, ``gate --all``, ``status`` and ``compliance``. The
current script must give the same on the same fixtures. ``tests/fixtures/golden_0_2_0.json``
holds the same for the 0.2.0 script (commit ``542368c``). These tests guard existing
behaviour, so they pass when written.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures"))

import make_golden  # noqa: E402
from support import FEATURES, SCRIPT  # noqa: E402

GOLDEN = os.environ.get("TDD_GOLDEN_FILE", make_golden.GOLDEN)
GOLDEN_0_2_0 = os.environ.get("TDD_GOLDEN_0_2_0_FILE", make_golden.GOLDEN_0_2_0)


def mismatches_against(path):
    with open(path, encoding="utf-8") as handle:
        golden = json.load(handle)
    found = []
    for key, expected in sorted(golden.items()):
        name, _, command = key.partition(" ")
        code, out = make_golden.run_script(SCRIPT, os.path.join(FEATURES, name), command.split())
        if (code, out) != (expected["code"], expected["out"]):
            found.append(f"{key}: expected {expected['code']} {expected['out']!r}, got {code} {out!r}")
    return len(golden), found


class CompatibilityTests(unittest.TestCase):
    def test_current_script_matches_0_1_0_outputs(self):
        with open(GOLDEN, encoding="utf-8") as handle:
            golden = json.load(handle)
        self.assertGreater(len(golden), 0)
        mismatches = []
        for key, expected in sorted(golden.items()):
            name, _, command = key.partition(" ")
            code, out = make_golden.run_script(SCRIPT, os.path.join(FEATURES, name), command.split())
            if (code, out) != (expected["code"], expected["out"]):
                mismatches.append(f"{key}: expected {expected['code']} {expected['out']!r}, got {code} {out!r}")
        self.assertEqual(mismatches, [])

    def test_current_script_matches_0_2_0_outputs(self):
        count, mismatches = mismatches_against(GOLDEN_0_2_0)
        self.assertGreater(count, 0)
        self.assertEqual(mismatches, [])


if __name__ == "__main__":
    unittest.main()
