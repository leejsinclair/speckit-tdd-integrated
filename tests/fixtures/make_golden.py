#!/usr/bin/env python3
"""Writes tests/fixtures/golden_0_1_0.json and golden_0_2_0.json, the outputs of two earlier check scripts.

The 0.1.0 script is taken from tag ``v0.1.0``, and the 0.2.0 script from commit ``542368c``
(the last commit of 0.2.0 behaviour; no ``v0.2.0`` tag exists). Each is extracted with
``git show`` into a temporary directory and run, with ``--json``, on every fixture feature
that ``make_features.py`` generated at that revision. Fixtures added later are never
included, so each file guards the behaviour that FR-002, FR-022 and SC-006 require to stay
the same. Run from anywhere:

    python3 -B tests/fixtures/make_golden.py [0.1.0] [0.2.0]

With no argument both files are written.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
FEATURES = os.path.join(HERE, "features")
GOLDEN = os.path.join(HERE, "golden_0_1_0.json")
GOLDEN_0_2_0 = os.path.join(HERE, "golden_0_2_0.json")
TAG = "v0.1.0"
REV_0_2_0 = "542368c"
FEATURE_REL = "specs/001-demo"
COMMANDS = [["plan"], ["tasks"], ["gate", "--all"], ["status"], ["compliance"]]


def run_script(script, fixture_dir, command):
    """Run ``command`` of ``script`` on a copy of ``fixture_dir``; return (code, stdout)."""
    root = tempfile.mkdtemp(prefix="tdd-golden-")
    try:
        bin_dir = os.path.join(root, "tests", "fixtures", "bin")
        os.makedirs(bin_dir)
        shutil.copy(os.path.join(HERE, "bin", "fake_test.sh"), bin_dir)
        shutil.copytree(fixture_dir, os.path.join(root, FEATURE_REL))
        args = command + ["--json", "--feature-dir", FEATURE_REL]
        proc = subprocess.run(
            [sys.executable, "-B", script] + args, cwd=root, capture_output=True, text=True, check=False
        )
        return proc.returncode, proc.stdout
    finally:
        shutil.rmtree(root, True)


def names_at_tag(revision=TAG):
    out = subprocess.run(
        ["git", "ls-tree", "-d", "--name-only", revision, "tests/fixtures/features/"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    return sorted(os.path.basename(line) for line in out.split())


def write_golden(revision, path):
    source = subprocess.run(
        ["git", "show", revision + ":scripts/python/tdd_check.py"], cwd=REPO, capture_output=True, check=True
    ).stdout
    golden = {}
    with tempfile.TemporaryDirectory() as folder:
        script = os.path.join(folder, "tdd_check.py")
        with open(script, "wb") as handle:
            handle.write(source)
        for name in names_at_tag(revision):
            for command in COMMANDS:
                code, out = run_script(script, os.path.join(FEATURES, name), command)
                golden[name + " " + " ".join(command)] = {"code": code, "out": out}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(golden, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"wrote {len(golden)} outputs to {os.path.relpath(path, REPO)}")


def main(which=()):
    targets = {"0.1.0": (TAG, GOLDEN), "0.2.0": (REV_0_2_0, GOLDEN_0_2_0)}
    for version in which or sorted(targets):
        write_golden(*targets[version])


if __name__ == "__main__":
    main(sys.argv[1:])
