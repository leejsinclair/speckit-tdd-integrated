"""Helpers shared by the test suite.

Tests drive ``scripts/python/tdd_check.py`` as a subprocess and assert on its
exit code, standard output and standard error, as the check script contract
defines them.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "python", "tdd_check.py")
FIXTURES = os.path.join(REPO, "tests", "fixtures")
FEATURES = os.path.join(FIXTURES, "features")
PAYLOADS = os.path.join(FIXTURES, "payloads")
FAKE_TEST = os.path.join(FIXTURES, "bin", "fake_test.sh")

# Where a fixture feature directory lands inside the temporary repository.
FEATURE_REL = os.path.join("specs", "001-demo")


class Result:
    """Outcome of one run of the check script."""

    def __init__(self, code, out, err):
        self.code = code
        self.out = out
        self.err = err

    def __repr__(self):
        return f"Result(code={self.code!r}, out={self.out!r}, err={self.err!r})"


def make_repo(fixture=None, feature_rel=FEATURE_REL, point_feature_json=True):
    """Create a temporary repository root and return its path.

    ``fixture`` names a directory under ``tests/fixtures/features``; it is
    copied to ``feature_rel`` inside the new root. ``.specify/feature.json``
    points at it, and the stand-in test command is copied to the same relative
    path it has in this repository, so fixture plans can declare it.
    """
    root = tempfile.mkdtemp(prefix="tdd-check-")
    bin_dir = os.path.join(root, "tests", "fixtures", "bin")
    os.makedirs(bin_dir)
    shutil.copy(FAKE_TEST, bin_dir)
    if fixture is not None:
        shutil.copytree(os.path.join(FEATURES, fixture), os.path.join(root, feature_rel))
    else:
        os.makedirs(os.path.join(root, feature_rel))
    if point_feature_json:
        os.makedirs(os.path.join(root, ".specify"))
        with open(os.path.join(root, ".specify", "feature.json"), "w") as handle:
            json.dump({"feature_directory": feature_rel.replace(os.sep, "/")}, handle)
    return root


def run_check(args, cwd, stdin=None, env=None):
    """Run the check script with ``args`` from ``cwd`` and return a Result."""
    if not os.path.isfile(SCRIPT):
        # Python exits 2 for a missing script, which a usage-error test would
        # mistake for the behaviour it expects.
        raise AssertionError("check script not found: scripts/python/tdd_check.py")
    full_env = dict(os.environ)
    full_env.pop("SPECIFY_FEATURE_DIRECTORY", None)
    if env:
        full_env.update(env)
    proc = subprocess.run(
        [sys.executable, "-B", SCRIPT] + list(args),
        cwd=cwd,
        input=stdin,
        env=full_env,
        capture_output=True,
        check=False,
        text=True,
    )
    return Result(proc.returncode, proc.stdout, proc.stderr)


def read(root, *parts):
    with open(os.path.join(root, *parts)) as handle:
        return handle.read()


def write(root, parts, text):
    path = os.path.join(root, *parts)
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    with open(path, "w") as handle:
        handle.write(text)
    return path


def snapshot(root):
    """Map every file under ``root`` to its content, for no-write assertions."""
    found = {}
    for folder, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(folder, name)
            with open(path, "rb") as handle:
                found[os.path.relpath(path, root)] = handle.read()
    return found


def load_payload(name, root):
    """Read a payload fixture, replacing the ``{ROOT}`` token with ``root``."""
    with open(os.path.join(PAYLOADS, name)) as handle:
        return handle.read().replace("{ROOT}", root.replace("\\", "/"))


class RepoCase(unittest.TestCase):
    """A test case that builds temporary repositories and removes them."""

    def repo(self, fixture=None, **kwargs):
        root = make_repo(fixture, **kwargs)
        self.addCleanup(shutil.rmtree, root, True)
        return root

    def feature(self, root):
        return os.path.join(root, FEATURE_REL)

    def check(self, args, root, **kwargs):
        return run_check(args, root, **kwargs)


def load_script():
    """Import the check script as a module, for tests of its parsing functions.

    The parser has no subcommand of its own, so its tests call it directly.
    Every other test drives the script as a subprocess.
    """
    import importlib.util  # noqa: PLC0415

    if not os.path.isfile(SCRIPT):
        raise AssertionError("check script not found: scripts/python/tdd_check.py")
    spec = importlib.util.spec_from_file_location("tdd_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_text(case, name):
    with open(os.path.join(FEATURES, case, name)) as handle:
        return handle.read()


def table_rows(text, heading):
    """Rows of the table under ``heading`` as dicts keyed by the header row.

    A plain reader for the evidence document, independent of the script's own
    parser. Evidence cells never hold a vertical bar: the script replaces them.
    """
    lines = text.splitlines()
    if heading not in lines:
        raise AssertionError("no heading " + heading)
    index = lines.index(heading) + 1
    while index < len(lines) and not lines[index].startswith("|"):
        if lines[index].startswith("#"):
            raise AssertionError("no table under " + heading)
        index += 1
    table = []
    while index < len(lines) and lines[index].startswith("|"):
        table.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
        index += 1
    if not table:
        raise AssertionError("no table under " + heading)
    return [dict(zip(table[0], cells)) for cells in table[2:]]


EVIDENCE_REL = os.path.join(FEATURE_REL, "tdd-evidence.md")
CHECKLIST_REL = os.path.join(FEATURE_REL, "tests", "behaviour-checklist.md")


def write_checklist(root, text):
    """Write ``tests/behaviour-checklist.md`` into the feature directory of ``root``."""
    return write(root, CHECKLIST_REL.split(os.sep), text)


def evidence_text(root):
    path = os.path.join(root, EVIDENCE_REL)
    if not os.path.isfile(path):
        raise AssertionError("no tdd-evidence.md was written")
    with open(path) as handle:
        return handle.read()


def records(root):
    return table_rows(evidence_text(root), "## Test execution records")


class RunCase(RepoCase):
    """A repository holding valid-minimal with no evidence yet, and helpers to record runs."""

    fixture = "valid-minimal"

    def setUp(self):
        self.root = self.repo(self.fixture)
        evidence = os.path.join(self.root, EVIDENCE_REL)
        if os.path.isfile(evidence):
            os.remove(evidence)
        write(self.root, ["tests", "test_cart.py"], "assert total([]) == 0\n")

    def run_phase(self, phase, command, *extra, **kwargs):
        return self.check(["run", "--phase", phase, "--command", command] + list(extra), self.root, **kwargs)

    def baseline(self):
        result = self.run_phase("baseline", "suite")
        self.assertEqual(result.code, 0, result)
        return result

    def red(self, task="T011", vo="VO-001", select="assert", expect="AssertionError: expected 0", extra=()):
        return self.run_phase(
            "red", "unit", "--select", select, "--task", task, "--vo", vo,
            "--tests", "tests/test_cart.py", "--expect", expect, *extra
        )  # fmt: skip

    def green(self, task="T012", vo="VO-001", select="pass", extra=()):
        return self.run_phase("green", "unit", "--select", select, "--task", task, "--vo", vo, *extra)

    def has_evidence(self):
        return os.path.isfile(os.path.join(self.root, EVIDENCE_REL))

    def add_command(self, row):
        """Add a row to the plan's Verification commands table."""
        plan = read(self.root, FEATURE_REL, "plan.md")
        anchor = "| suite | `sh tests/fixtures/bin/fake_test.sh pass` | broad | tests/fixtures/bin |\n"
        if anchor not in plan:
            raise AssertionError("fixture plan has no suite row")
        write(self.root, [FEATURE_REL, "plan.md"], plan.replace(anchor, anchor + row + "\n"))
