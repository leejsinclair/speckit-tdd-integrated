#!/usr/bin/env python3
"""Writes tests/fixtures/golden_0_1_0.json, the outputs of the 0.1.0 check script.

The script is taken from tag ``v0.1.0`` with ``git show`` into a temporary directory
and run, with ``--json``, on every fixture feature that ``make_features.py`` generated
at that tag. Fixtures added later are never included, so the file guards the 0.1.0
behaviour that FR-002 and SC-006 require to stay the same. Run from anywhere:

    python3 -B tests/fixtures/make_golden.py
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
TAG = "v0.1.0"
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


def names_at_tag():
    out = subprocess.run(
        ["git", "ls-tree", "-d", "--name-only", TAG, "tests/fixtures/features/"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    return sorted(os.path.basename(line) for line in out.split())


def main():
    source = subprocess.run(
        ["git", "show", TAG + ":scripts/python/tdd_check.py"], cwd=REPO, capture_output=True, check=True
    ).stdout
    golden = {}
    with tempfile.TemporaryDirectory() as folder:
        script = os.path.join(folder, "tdd_check.py")
        with open(script, "wb") as handle:
            handle.write(source)
        for name in names_at_tag():
            for command in COMMANDS:
                code, out = run_script(script, os.path.join(FEATURES, name), command)
                golden[name + " " + " ".join(command)] = {"code": code, "out": out}
    with open(GOLDEN, "w", encoding="utf-8") as handle:
        json.dump(golden, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"wrote {len(golden)} outputs to {os.path.relpath(GOLDEN, REPO)}")


if __name__ == "__main__":
    main()
