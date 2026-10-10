#!/usr/bin/env python3
"""Layout helper for Mermaid C4 diagrams. Python 3 standard library only.

Mermaid's C4 renderer places elements in declaration order, so the only layout
control is the order of element lines. This script does the mechanical parts of
choosing that order; see "Layout optimisation" in templates/c4-conventions.md.

  inventory FILE                 elements and relationships of each C4 block (JSON)
  check BEFORE AFTER             exit 1 unless both describe the same architecture
  candidates FILE --out DIR      write baseline.mmd and reordered candidates
  score SVG...                   measure rendered SVGs (the first is the baseline)
  optimise FILE --out DIR        candidates + render + score + ranking

FILE is a Markdown file (use --block N to pick the Nth C4 block, default 1) or a
file holding one Mermaid diagram. Candidates only move whole element lines within
their peer group; relationships and boundary membership are never changed.
"""
import argparse
import json
import math
import re
import shlex
import shutil

# Mermaid is invoked as an argument list without a shell.
import subprocess  # nosec B404
import sys

# Only locally generated Mermaid SVGs are parsed.
import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path

MACRO = re.compile(r"^\s*([A-Za-z_]+)\s*\((.*)\)\s*(\{)?\s*$")
ARG = re.compile(r'\s*(?:"([^"]*)"|([^,]*))\s*(?:,|$)')
NUM = re.compile(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?")
CHAR_W, LINE_H = 6.0, 17.0  # relationship label glyph size in Mermaid's default theme
ROWS = 'UpdateLayoutConfig($c4ShapeInRow="{}", $c4BoundaryInRow="1")'


# ---------- Mermaid source ----------

def c4_blocks(path):
    """Return the C4 diagrams in a file, each as a list of lines."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not any(line.strip().startswith("```") for line in lines):
        blocks = [lines]
    else:
        blocks, current = [], None
        for line in lines:
            if current is None and line.strip().startswith("```mermaid"):
                current = []
            elif current is not None and line.strip().startswith("```"):
                blocks.append(current)
                current = None
            elif current is not None:
                current.append(line)
    return [block for block in blocks
            if next((line for line in block if line.strip()), "").strip().startswith("C4")]


def load_block(path, number):
    blocks = c4_blocks(path)
    if not 1 <= number <= len(blocks):
        sys.exit(f"{path}: C4 block {number} not found ({len(blocks)} C4 block(s) in file)")
    return blocks[number - 1]


def split_args(text):
    return [m.group(1) if m.group(1) is not None else m.group(2).strip()
            for m in ARG.finditer(text) if m.group(0)]


def parse(lines):
    """Parse a block into a tree. Items are dicts with kind elem, bound or other."""
    root = {"kind": "bound", "alias": None, "items": []}
    stack = [root]
    for line in lines:
        m = MACRO.match(line)
        if line.strip() == "}" and len(stack) > 1:
            stack.pop()["close"] = line
            continue
        if not m or m.group(1).startswith(("Rel", "BiRel", "Update", "Add")):
            item = {"kind": "other", "line": line}
            if m and m.group(1).startswith(("Rel", "BiRel")):
                item["rel"] = [m.group(1)] + split_args(m.group(2))
            stack[-1]["items"].append(item)
            continue
        args = split_args(m.group(2))
        item = {"kind": "bound" if m.group(3) else "elem", "line": line,
                "macro": m.group(1), "alias": args[0] if args else "", "args": args}
        stack[-1]["items"].append(item)
        if m.group(3):
            item["items"] = []
            stack.append(item)
    if len(stack) > 1:
        sys.exit("unbalanced boundary braces")
    return root


def emit(node):
    out = []
    for item in node["items"]:
        out.append(item["line"])
        if item["kind"] == "bound":
            out += emit(item) + [item.get("close", "}")]
    return out


def walk(node):
    for item in node["items"]:
        yield node, item
        if item["kind"] == "bound":
            yield from walk(item)


def inventory(lines):
    tree = parse(lines)
    elements, rels = [], []
    for parent, item in walk(tree):
        if item["kind"] in ("elem", "bound"):
            elements.append({"alias": item["alias"], "macro": item["macro"],
                             "args": item["args"][1:], "boundary": parent["alias"]})
        elif "rel" in item:
            rels.append(item["rel"])
    return {"type": next(line for line in lines if line.strip()).strip(),
            "elements": elements, "relationships": rels}


def differences(a, b):
    """Describe how two inventories differ, ignoring declaration order."""
    out = []
    if a["type"] != b["type"]:
        out.append(f"diagram type {a['type']} -> {b['type']}")
    ea, eb = ({e["alias"]: e for e in x["elements"]} for x in (a, b))
    for alias in sorted(set(ea) | set(eb)):
        if alias not in eb:
            out.append(f"element removed: {alias}")
        elif alias not in ea:
            out.append(f"element added: {alias}")
        elif ea[alias] != eb[alias]:
            out.append(f"element changed: {alias}")
    ra, rb = (sorted(map(tuple, x["relationships"])) for x in (a, b))
    out += [f"relationship removed: {r}" for r in ra if ra.count(r) > rb.count(r)]
    out += [f"relationship added: {r}" for r in rb if rb.count(r) > ra.count(r)]
    return sorted(set(out))


# ---------- candidate orderings ----------

def group_kind(item):
    if item["kind"] == "bound":
        return "boundary"
    if item["macro"].startswith("Person"):
        return "person"
    return "external" if item["macro"].endswith("_Ext") else "element"


def aliases_of(item):
    found = {item["alias"]}
    for _, child in walk(item) if item["kind"] == "bound" else ():
        found.add(child.get("alias"))
    return found


def reorder(node, key, depth=0):
    """Reorder each run of same-kind siblings with key(run, depth); other lines stay put."""
    slots = [i for i, it in enumerate(node["items"]) if it["kind"] != "other"]
    runs = []
    for i in slots:
        item = node["items"][i]
        if runs and group_kind(node["items"][runs[-1][-1]]) == group_kind(item):
            runs[-1].append(i)
        else:
            runs.append([i])
        if item["kind"] == "bound":
            reorder(item, key, depth + 1)
    for run in runs:
        ordered = key([node["items"][i] for i in run], depth)
        for i, item in zip(run, ordered):
            node["items"][i] = item


def graph(tree):
    rels = [it["rel"][1:3] for _, it in walk(tree) if "rel" in it and len(it["rel"]) > 2]
    links = {}
    for a, b in rels:
        links.setdefault(a, set()).add(b)
        links.setdefault(b, set()).add(a)
    return rels, links


def connected_order(links):
    def key(run, depth):
        members = [aliases_of(it) for it in run]

        def touch(index, others):
            return sum(len(links.get(alias, set()) & others) for alias in members[index])

        degree = [sum(len(links.get(a, ())) for a in m) for m in members]
        left, placed, seen = list(range(len(run))), [], set()
        while left:
            best = max(left, key=lambda i: (touch(i, seen), degree[i], -i))
            left.remove(best)
            placed.append(run[best])
            seen |= members[best]
        return placed
    return key


def path_order(tree, rels):
    people = [it["alias"] for _, it in walk(tree)
              if it["kind"] == "elem" and it["macro"].startswith("Person")]
    queue = people or [r[0] for r in rels[:1]]
    rank = {}
    while queue:
        alias = queue.pop(0)
        if alias not in rank:
            rank[alias] = len(rank)
            queue += [b for a, b in rels if a == alias]
    return lambda run, depth: sorted(
        run, key=lambda it: min(rank.get(a, math.inf) for a in aliases_of(it)))


def with_rows(lines):
    """Baseline plus a row-width setting; its effect depends on the renderer version."""
    current = next((line for line in lines if "UpdateLayoutConfig" in line), None)
    if current:
        width = "2" if '$c4ShapeInRow="3"' in current else "3"
        return [ROWS.format(width).join(re.split(r"UpdateLayoutConfig\(.*\)", line))
                if line is current else line for line in lines]
    last = max(index for index, line in enumerate(lines) if line.strip())
    indent = re.match(r"\s*", lines[last]).group(0)
    return lines[:last + 1] + [indent + ROWS.format("3")] + lines[last + 1:]


def make_candidates(lines):
    """Return [(name, lines)], baseline first, without duplicates."""
    def variant(key):
        tree = parse(lines)
        reorder(tree, key)
        return emit(tree)

    rels, links = graph(parse(lines))
    def reverse_at(level):
        def reverse(run, depth):
            return run[::-1] if (depth == 0) == level else run
        return reverse

    reversed_peers = variant(reverse_at(True))
    if reversed_peers == lines:
        reversed_peers = variant(reverse_at(False))
    out = [("baseline", lines)]
    for name, cand in (("connected", variant(connected_order(links))),
                       ("primary-path", variant(path_order(parse(lines), rels))),
                       ("reversed-peers", reversed_peers),
                       ("rows", with_rows(lines))):
        if all(cand != seen for _, seen in out):
            out.append((name, cand))
    return out


def declaration_distance(lines):
    """Graph-only estimate: how far apart related elements are declared."""
    tree = parse(lines)
    order = [it["alias"] for _, it in walk(tree) if it["kind"] == "elem"]
    pos = {a: i for i, a in enumerate(order)}
    return sum(abs(pos[a] - pos[b]) for a, b in graph(tree)[0] if a in pos and b in pos)


# ---------- SVG measurement ----------

def tag(el):
    return el.tag.rsplit("}", 1)[-1]


def translate(el):
    m = re.search(r"translate\(([^)]*)\)", el.get("transform", ""))
    nums = [float(v) for v in NUM.findall(m.group(1))] if m else []
    return (nums[0], nums[1] if len(nums) > 1 else 0.0) if nums else (0.0, 0.0)


def shape_box(el, ox, oy):
    """Bounding box of a node's outline (rect, person head, or cylinder path)."""
    xs, ys = [], []
    for child in el.iter():
        if child.get("class") == "label":
            break
        cls = child.get("class", "")
        if tag(child) == "rect" and child.get("width"):
            x, y = float(child.get("x", 0)), float(child.get("y", 0))
            xs += [x, x + float(child.get("width"))]
            ys += [y, y + float(child.get("height"))]
        elif tag(child) == "circle":
            cx, cy, r = (float(child.get(k, 0)) for k in ("cx", "cy", "r"))
            xs += [cx - r, cx + r]
            ys += [cy - r, cy + r]
        elif tag(child) == "path" and "label-container" in cls:
            tx, ty = translate(child)
            x = y = 0.0
            pad = []
            for cmd, body in re.findall(r"([MmLlAa])([^MmLlAaZz]*)", child.get("d", "")):
                n = [float(v) for v in NUM.findall(body)]
                if len(n) < 2:
                    continue
                if cmd in "Aa":
                    pad.append(min(n[0], n[1]))
                x, y = (n[-2], n[-1]) if cmd.isupper() else (x + n[-2], y + n[-1])
                xs.append(x + tx)
                ys.append(y + ty)
            p = min(pad, default=0.0)
            xs += [min(xs) - p, max(xs) + p]
            ys += [min(ys) - p, max(ys) + p]
    if not xs:
        return None
    return (ox + min(xs), oy + min(ys), ox + max(xs), oy + max(ys))


def route_points(el):
    if tag(el) == "line":
        return [(float(el.get("x1")), float(el.get("y1"))), (float(el.get("x2")), float(el.get("y2")))]
    n = [float(v) for v in NUM.findall(el.get("d", ""))]
    pts = list(zip(n[0::2], n[1::2]))
    if len(pts) in (3, 4) and re.search(r"[QC]", el.get("d", "")):
        steps, out = 16, []
        for i in range(steps + 1):
            t = i / steps
            w = ([(1 - t) ** 2, 2 * t * (1 - t), t * t] if len(pts) == 3 else
                 [(1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3])
            out.append((sum(a * p[0] for a, p in zip(w, pts)), sum(a * p[1] for a, p in zip(w, pts))))
        return out
    return pts


def read_svg(path):
    # Mermaid CLI generated this local SVG; accepting arbitrary XML is outside this tool's boundary.
    root = ET.parse(path).getroot()  # nosec B314
    prefix = root.get("id", "") + "-"
    view = [float(v) for v in root.get("viewBox", "0 0 0 0").split()]
    nodes, edges, titles = {}, [], []

    def visit(el, ox, oy):
        tx, ty = translate(el)
        ox, oy = ox + tx, oy + ty
        if "c4-shape" in el.get("class", ""):
            box = shape_box(el, ox, oy)
            if box:
                name = el.get("id", "")
                nodes[name[len(prefix):] if name.startswith(prefix) else name] = box
            return
        edge = None
        boundary = any(child.get("stroke-dasharray") for child in el)
        for child in el:
            if tag(child) in ("line", "path") and (child.get("marker-end") or child.get("marker-start")):
                pts = [(x + ox, y + oy) for x, y in route_points(child)]
                edge = {"points": pts, "texts": []}
                edges.append(edge)
            elif tag(child) == "text" and (edge is not None or boundary):
                text = "".join(child.itertext()).strip()
                x, y = float(child.get("x", 0)) + ox, float(child.get("y", 0)) + oy
                half = len(text) * CHAR_W / 2
                box = (x - half, y - LINE_H / 2, x + half, y + LINE_H / 2)
                (edge["texts"] if edge is not None else titles).append(box)
            else:
                visit(child, ox, oy)

    visit(root, 0.0, 0.0)
    for e in edges:
        t = e.pop("texts")
        e["label"] = (min(b[0] for b in t), min(b[1] for b in t),
                      max(b[2] for b in t), max(b[3] for b in t)) if t else None
        e["ends"] = {nearest(nodes, e["points"][0]), nearest(nodes, e["points"][-1])}
    return {"nodes": nodes, "edges": edges, "titles": titles, "area": view[2] * view[3]}


def nearest(nodes, p):
    def dist(box):
        dx = max(box[0] - p[0], 0, p[0] - box[2])
        dy = max(box[1] - p[1], 0, p[1] - box[3])
        return math.hypot(dx, dy)
    return min(nodes, key=lambda n: dist(nodes[n]), default=None)


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def segments_cross(p, q, r, s):
    """Point where two segments properly cross, else None."""
    d1, d2, d3, d4 = cross(r, s, p), cross(r, s, q), cross(p, q, r), cross(p, q, s)
    if d1 * d2 < 0 and d3 * d4 < 0:
        t = d1 / (d1 - d2)
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
    return None


def inside(box, p, margin=0.0):
    return box[0] - margin <= p[0] <= box[2] + margin and box[1] - margin <= p[1] <= box[3] + margin


def route_hits(points, box, shrink=2.0):
    b = (box[0] + shrink, box[1] + shrink, box[2] - shrink, box[3] - shrink)
    corners = [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]
    for p, q in zip(points, points[1:]):
        if inside(b, p) or inside(b, q):
            return True
        if any(segments_cross(p, q, corners[i], corners[(i + 1) % 4]) for i in range(4)):
            return True
    return False


def boxes_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def measure(svg):
    """Count readability defects in one rendered C4 diagram."""
    nodes, edges = svg["nodes"], svg["edges"]
    widths = sorted(b[2] - b[0] for b in nodes.values()) or [1.0]
    unit = widths[len(widths) // 2]
    n = o = x = t = long_edges = 0
    total = 0.0
    for i, e in enumerate(edges):
        length = sum(math.dist(p, q) for p, q in zip(e["points"], e["points"][1:]))
        total += length
        long_edges += length > 3 * unit
        o += sum(bool(e["label"]) and boxes_overlap(e["label"], box) for box in svg["titles"])
        for name, box in nodes.items():
            if name not in e["ends"]:
                n += route_hits(e["points"], box)
                o += bool(e["label"]) and boxes_overlap(e["label"], box)
        for j, f in enumerate(edges):
            if i == j:
                continue
            t += bool(f["label"]) and route_hits(e["points"], f["label"], 0.0)
            if j < i:
                continue
            o += bool(e["label"] and f["label"]) and boxes_overlap(e["label"], f["label"])
            shared = [nodes[k] for k in e["ends"] & f["ends"] if k in nodes]
            hit = next((pt for a, b in zip(e["points"], e["points"][1:])
                        for c, d in zip(f["points"], f["points"][1:])
                        for pt in [segments_cross(a, b, c, d)] if pt), None)
            x += bool(hit) and not any(inside(box, hit, 10.0) for box in shared)
    return {"N": n, "O": o, "X": x, "T": t, "L": round(total / unit, 2), "long": long_edges}


def penalty(m, area_ratio):
    """Penalty table from the conventions; lower is better."""
    return (5 * m["X"] + 6 * (m["N"] + m["O"]) + 2 * m["T"] + 2 * m["long"]
            + (3 if area_ratio > 1.5 else 0))


def geometry(svg):
    return (sorted(svg["nodes"].items()), [e["points"] for e in svg["edges"]])


def score_files(named_svgs):
    """Measure [(name, svg path)]; the first entry is the baseline."""
    rows, base = [], None
    for name, path in named_svgs:
        svg = read_svg(path)
        base = base or svg
        m = measure(svg)
        ratio = svg["area"] / base["area"] if base["area"] else 1.0
        rows.append({"name": name, "svg": str(path), **m, "canvas_ratio": round(ratio, 2),
                     "score": penalty(m, ratio),
                     "same_geometry_as_baseline": svg is not base and geometry(svg) == geometry(base)})
    return rows


# ---------- commands ----------

NOTE = ("N routes through unrelated elements, O relationship labels overlapping an unrelated "
        "element, label or boundary title, X crossings, T routes through "
        "unrelated labels, L route length in element widths, long = routes over 3 widths. "
        "score = 5X + 6(N+O) + 2T + 2*long + 3 if canvas_ratio > 1.5. Label sizes are estimated "
        "from character counts, so O and T are approximate; confirm in the image.")


def render(cmd, source, target):
    extra = ["-b", "white"] if str(target).endswith(".png") else []
    # argv comes from the user's configured Mermaid command and is never passed to a shell.
    run = subprocess.run(  # nosec B603
        cmd + ["-i", str(source), "-o", str(target)] + extra,
        capture_output=True, text=True)
    if run.returncode != 0 or not Path(target).exists():
        return (run.stderr or run.stdout).strip().splitlines()[-1:] or ["render failed"]
    return None


def cmd_inventory(args):
    print(json.dumps([inventory(b) for b in c4_blocks(args.file)], indent=2))


def cmd_check(args):
    before, after = c4_blocks(args.before), c4_blocks(args.after)
    if args.block:
        before, after = [load_block(args.before, args.block)], [load_block(args.after, args.block)]
    problems = [] if len(before) == len(after) else [
        f"number of C4 blocks {len(before)} -> {len(after)}"]
    for i, (a, b) in enumerate(zip(before, after), 1):
        problems += [f"block {args.block or i}: {d}" for d in differences(inventory(a), inventory(b))]
    print("\n".join(problems) or "same elements, boundaries and relationships")
    sys.exit(1 if problems else 0)


def write_candidates(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for name, lines in make_candidates(load_block(args.file, args.block)):
        path = out / f"{name}.mmd"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        files.append((name, path, lines))
    return files


def cmd_candidates(args):
    print(json.dumps([{"name": n, "source": str(p)} for n, p, _ in write_candidates(args)], indent=2))


def cmd_score(args):
    print(json.dumps({"measured": True, "note": NOTE,
                      "diagrams": score_files([(Path(s).stem, s) for s in args.svg])}, indent=2))


def cmd_optimise(args):
    files = write_candidates(args)
    cmd = shlex.split(args.mmdc or "mmdc")
    if not shutil.which(cmd[0]):
        print(json.dumps({
            "measured": False, "selected": "baseline",
            "note": f"Mermaid renderer '{cmd[0]}' not found (pass --mmdc). Nothing was rendered; keep the "
                    "existing order and report the layout as not checked. declaration_distance "
                    "is a graph-only estimate, not a measurement.",
            "candidates": [{"name": name, "source": str(path),
                            "declaration_distance": declaration_distance(lines)}
                           for name, path, lines in files]}, indent=2))
        return

    result = {"measured": True, "renderer": " ".join(cmd), "note": NOTE}
    failed, rendered = [], []
    for i, (name, path, _) in enumerate(files):
        error = render(cmd, path, path.with_suffix(".svg"))
        if error and i == 0:
            sys.exit(f"baseline does not render: {error[0]}")
        if error:
            failed.append({"name": name, "source": str(path), "error": error[0]})
        else:
            rendered.append((name, path.with_suffix(".svg")))
        if i == 0:
            base = score_files(rendered)[0]
            if not (base["N"] or base["O"] or base["X"]) and not args.force:
                for _, extra, _ in files[1:]:
                    extra.unlink()
                render(cmd, path, path.with_suffix(".png"))
                result.update(baseline_sufficient=True, selected="baseline",
                              selected_source=str(path), images=[str(path.with_suffix(".png"))],
                              candidates=[base])
                print(json.dumps(result, indent=2))
                return

    rows = score_files(rendered)
    for row in rows:
        row["source"] = str(Path(row["svg"]).with_suffix(".mmd"))
    best = min(rows, key=lambda r: r["score"])  # min keeps the first on a tie: the baseline
    images = []
    for name in dict.fromkeys(["baseline", best["name"]]):
        png = Path(args.out) / f"{name}.png"
        if not render(cmd, png.with_suffix(".mmd"), png):
            images.append(str(png))
    result.update(baseline_sufficient=False, selected=best["name"], selected_source=best["source"],
                  images=images, candidates=sorted(rows, key=lambda r: r["score"]), failed=failed)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inventory")
    p.add_argument("file")
    p.set_defaults(func=cmd_inventory)

    p = sub.add_parser("check")
    p.add_argument("before")
    p.add_argument("after")
    p.add_argument("--block", type=int, help="compare only this C4 block (default: all)")
    p.set_defaults(func=cmd_check)

    for name, func in (("candidates", cmd_candidates), ("optimise", cmd_optimise)):
        p = sub.add_parser(name)
        p.add_argument("file")
        p.add_argument("--block", type=int, default=1, help="which C4 block of a Markdown file")
        p.add_argument("--out", required=True, help="directory for candidates and renders")
        p.set_defaults(func=func)
    p.add_argument("--mmdc", help='Mermaid CLI command, e.g. "npx -y @mermaid-js/mermaid-cli"')
    p.add_argument("--force", action="store_true", help="compare candidates even if the baseline is clean")

    p = sub.add_parser("score")
    p.add_argument("svg", nargs="+")
    p.set_defaults(func=cmd_score)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
