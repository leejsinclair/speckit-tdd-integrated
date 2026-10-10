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
