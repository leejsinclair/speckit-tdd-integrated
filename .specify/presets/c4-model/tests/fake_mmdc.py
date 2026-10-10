#!/usr/bin/env python3
"""Stand-in for the Mermaid CLI in tests: fake_mmdc.py FIXTURE_DIR -i IN -o OUT.

Copies the pre-rendered SVG with the same name as IN from FIXTURE_DIR, so the
tests exercise rendering code paths without Node or a browser.
"""
import shutil
import sys
from pathlib import Path

fixtures, args = Path(sys.argv[1]), sys.argv[2:]
source, target = Path(args[args.index("-i") + 1]), Path(args[args.index("-o") + 1])
svg = fixtures / f"{source.stem}.svg"
if not svg.exists():
    sys.exit(f"Parse error: no fixture for {source.name}")
if target.suffix == ".svg":
    shutil.copy(svg, target)
else:
    target.write_bytes(b"fake image")
