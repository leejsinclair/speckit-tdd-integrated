#!/usr/bin/env python3
"""Regenerate the fixtures under tests/fixtures. Needs a Mermaid CLI.

    python3 tests/make_fixtures.py "npx -y @mermaid-js/mermaid-cli"

Each fixture directory holds one diagram as baseline.mmd. This script rewrites the
candidate orderings, renders every candidate to SVG and records the measurements in
expected.json. Review the diff before committing: a change means either the script's
behaviour or the Mermaid renderer's output changed.
"""
import json
import re
import shlex
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "python"))
import c4_layout  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
KEYS = ("name", "N", "O", "X", "T", "L", "long", "canvas_ratio", "score", "same_geometry_as_baseline")


def main():
    cmd = shlex.split(sys.argv[1] if len(sys.argv) > 1 else "mmdc")
    for folder in sorted(p for p in FIXTURES.iterdir() if p.is_dir()):
        lines = (folder / "baseline.mmd").read_text(encoding="utf-8").splitlines()
        for old in folder.iterdir():
            if old.name != "baseline.mmd":
                old.unlink()
        rendered = []
        for name, candidate in c4_layout.make_candidates(lines):
            source = folder / f"{name}.mmd"
            source.write_text("\n".join(candidate) + "\n", encoding="utf-8")
            svg = source.with_suffix(".svg")
            error = c4_layout.render(cmd, source, svg)
            if error:
                sys.exit(f"{source}: {error[0]}")
            # The stylesheet is most of the file and the measurements do not read it.
            svg.write_text(re.sub(r"<style>.*?</style>", "", svg.read_text(encoding="utf-8"), flags=re.S),
                           encoding="utf-8")
            rendered.append((name, svg))
        rows = [{k: row[k] for k in KEYS} for row in c4_layout.score_files(rendered)]
        (folder / "expected.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        print(folder.name, [(r["name"], r["score"]) for r in rows])


if __name__ == "__main__":
    main()
