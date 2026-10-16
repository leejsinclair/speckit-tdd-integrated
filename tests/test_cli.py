"""Common behaviour of the check script (contracts/check-cli.md)."""

import ast
import json
import os
import unittest

from support import SCRIPT, RepoCase, write

SUBCOMMANDS = [
    "plan",
    "tasks",
    "gate",
    "status",
    "compliance",
    "run",
    "classify",
    "exception",
    "expectation",
    "decision",
    "approve",
    "hook",
]
ALLOWED_IMPORTS = {"argparse", "datetime", "hashlib", "json", "os", "re", "subprocess", "sys"}
FORBIDDEN_IMPORTS = {"socket", "urllib", "http", "requests"}


def script_imports():
    if not os.path.isfile(SCRIPT):
        raise AssertionError("check script not found: scripts/python/tdd_check.py")
    with open(SCRIPT) as handle:
        tree = ast.parse(handle.read())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    return names


class FeatureDirectoryTests(RepoCase):
    """--feature-dir, then SPECIFY_FEATURE_DIRECTORY, then .specify/feature.json."""

    def setUp(self):
        self.root = self.repo()
        write(self.root, [".specify", "feature.json"], json.dumps({"feature_directory": "specs/from-json"}))

    def test_option_wins_over_environment_and_feature_json(self):
        result = self.check(
            ["plan", "--feature-dir", "specs/from-option"],
            self.root,
            env={"SPECIFY_FEATURE_DIRECTORY": "specs/from-env"},
        )
        self.assertEqual(result.code, 2)
        self.assertIn("feature directory not found: specs/from-option", result.err)

    def test_environment_wins_over_feature_json(self):
        result = self.check(["plan"], self.root, env={"SPECIFY_FEATURE_DIRECTORY": "specs/from-env"})
        self.assertEqual(result.code, 2)
        self.assertIn("feature directory not found: specs/from-env", result.err)

    def test_feature_json_is_used_last(self):
        result = self.check(["plan"], self.root)
        self.assertEqual(result.code, 2)
        self.assertIn("feature directory not found: specs/from-json", result.err)

    def test_no_source_is_a_usage_error(self):
        os.remove(os.path.join(self.root, ".specify", "feature.json"))
        result = self.check(["plan"], self.root)
        self.assertEqual(result.code, 2)
        self.assertIn("no feature directory", result.err)

    def test_an_existing_directory_is_accepted(self):
        os.makedirs(os.path.join(self.root, "specs", "from-json"))
        result = self.check(["plan"], self.root)
        self.assertNotIn("feature directory not found", result.err)
        self.assertNotIn("no feature directory", result.err)


class UsageTests(RepoCase):
    def setUp(self):
        self.root = self.repo()

    def test_unknown_subcommand_exits_2(self):
        result = self.check(["bogus"], self.root)
        self.assertEqual(result.code, 2)
        self.assertIn("invalid choice", result.err)

    def test_no_subcommand_exits_2(self):
        self.assertEqual(self.check([], self.root).code, 2)

    def test_missing_required_option_exits_2(self):
        cases = [
            ["gate"],
            ["run", "--command", "unit"],
            ["run", "--phase", "green"],
            ["classify", "--seq", "1"],
            ["exception", "--task", "T001", "--kind", "legacy"],
            ["expectation", "--task", "T001"],
            ["decision"],
            ["decision", "open", "--question", "which?"],
            ["decision", "resolve", "--id", "DN-01"],
            ["approve", "--id", "EX-01"],
        ]
        for args in cases:
            result = self.check(args, self.root)
            self.assertEqual(result.code, 2, args)
            self.assertIn("usage:", result.err, args)

    def test_out_of_range_choice_exits_2(self):
        for args in (
            ["run", "--phase", "purple", "--command", "unit"],
            ["classify", "--seq", "1", "--as", "flaky"],
            ["exception", "--task", "T001", "--kind", "lazy", "--rationale", "r"],
        ):
            self.assertEqual(self.check(args, self.root).code, 2, args)

    def test_all_twelve_subcommands_are_registered(self):
        for name in SUBCOMMANDS:
            result = self.check([name, "--help"], self.root)
            self.assertEqual(result.code, 0, name)
            self.assertIn("usage:", result.out, name)

    def test_json_prints_one_json_object(self):
        result = self.check(["plan", "--json", "--feature-dir", "specs/absent"], self.root)
        self.assertEqual(result.code, 2)
        data = json.loads(result.out)
        self.assertIsInstance(data, dict)
        self.assertEqual(data["exit_code"], 2)
        self.assertIn("feature directory not found: specs/absent", data["error"])

    def test_status_accepts_the_scenarios_option_and_no_other_subcommand_does(self):
        result = self.check(["status", "--help"], self.root)
        self.assertEqual(result.code, 0)
        self.assertIn("--scenarios", result.out)
        for name in ("plan", "tasks", "compliance"):
            self.assertNotIn("--scenarios", self.check([name, "--help"], self.root).out, name)


class SourceTests(unittest.TestCase):
    def test_script_imports_only_allowed_standard_library_modules(self):
        names = script_imports()
        self.assertTrue(names)
        self.assertEqual(names - ALLOWED_IMPORTS, set())

    def test_script_imports_no_network_module(self):
        self.assertEqual(script_imports() & FORBIDDEN_IMPORTS, set())


if __name__ == "__main__":
    unittest.main()
