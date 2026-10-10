"""Regression tests for scripts/python/c4_layout.py. Standard library only.

    python3 -m unittest discover -s tests -v

The fixtures are diagrams with pre-rendered SVGs, so no Mermaid CLI is needed.
Set C4_LAYOUT_MMDC (for example "npx -y @mermaid-js/mermaid-cli") to also render
the fixtures again and compare, which shows whether a new Mermaid version changed
the layout. Regenerate fixtures with tests/make_fixtures.py.
"""
import json
import os
import shlex

# Tests invoke the repository script directly without a shell.
import subprocess  # nosec B404
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "python" / "c4_layout.py"
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(SCRIPT.parent))
import c4_layout  # noqa: E402

DIAGRAMS = sorted(p.name for p in FIXTURES.iterdir() if p.is_dir())
METRICS = ("N", "O", "X", "T", "L", "long", "canvas_ratio", "score", "same_geometry_as_baseline")


def lines_of(diagram, name="baseline"):
    return (FIXTURES / diagram / f"{name}.mmd").read_text(encoding="utf-8").splitlines()


def expected(diagram):
    return json.loads((FIXTURES / diagram / "expected.json").read_text(encoding="utf-8"))


def run(*args):
    # The executable and script are fixed test paths.
    return subprocess.run(  # nosec B603
        [sys.executable, "-B", str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def fake_renderer(diagram):
    return " ".join(shlex.quote(str(p)) for p in
                    (sys.executable, FIXTURES.parent / "fake_mmdc.py", FIXTURES / diagram))


class ParsingTest(unittest.TestCase):
    def test_split_args(self):
        self.assertEqual(c4_layout.split_args('api, "Order API", "TypeScript, Fastify", "Does it"'),
                         ["api", "Order API", "TypeScript, Fastify", "Does it"])
        self.assertEqual(c4_layout.split_args('a, b, "Uses"'), ["a", "b", "Uses"])

    def test_inventory_of_container_view(self):
        inv = c4_layout.inventory(lines_of("container"))
        self.assertEqual(inv["type"], "C4Container")
        parents = {e["alias"]: e["boundary"] for e in inv["elements"]}
        self.assertEqual(parents, {
            "customer": None, "system": None, "paymentProvider": None, "emailService": None,
            "orderApi": "system", "webApp": "system", "ordersDb": "system",
            "eventBus": "system", "notifier": "system"})
        self.assertEqual(len(inv["relationships"]), 7)
        self.assertIn(["Rel", "webApp", "orderApi", "Calls", "JSON/HTTPS"], inv["relationships"])

    def test_emit_round_trips_every_fixture(self):
        for diagram in DIAGRAMS:
            lines = lines_of(diagram)
            self.assertEqual(c4_layout.emit(c4_layout.parse(lines)), lines, diagram)

    def test_only_c4_blocks_are_read_from_markdown(self):
        text = "\n".join(["# Doc", "```mermaid", "sequenceDiagram", "    a->>b: hi", "```",
                          "```mermaid", *lines_of("tiny"), "```",
                          "```mermaid", *lines_of("context"), "```", ""])
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text(text, encoding="utf-8")
            blocks = c4_layout.c4_blocks(doc)
            self.assertEqual(blocks, [lines_of("tiny"), lines_of("context")])
            self.assertEqual(c4_layout.load_block(doc, 2), lines_of("context"))
            with self.assertRaises(SystemExit):
                c4_layout.load_block(doc, 3)


class FidelityTest(unittest.TestCase):
    def setUp(self):
        self.lines = lines_of("container")
        self.base = c4_layout.inventory(self.lines)

    def diff(self, lines):
        return c4_layout.differences(self.base, c4_layout.inventory(lines))

    def edit(self, old, new):
        self.assertTrue(any(old in line for line in self.lines), old)
        return [line.replace(old, new) for line in self.lines]

    def test_reordering_is_not_a_difference(self):
        self.assertEqual(self.diff(lines_of("container", "connected")), [])

    def test_reversed_relationship(self):
        found = self.diff(self.edit("Rel(webApp, orderApi", "Rel(orderApi, webApp"))
        self.assertEqual(len(found), 2)
        self.assertTrue(found[0].startswith("relationship added"))
        self.assertTrue(found[1].startswith("relationship removed"))

    def test_changed_relationship_label(self):
        self.assertEqual(len(self.diff(self.edit('"Calls"', '"Invokes"'))), 2)

    def test_removed_relationship_and_element(self):
        without_rel = [line for line in self.lines if "Rel(notifier, emailService" not in line]
        self.assertEqual(len(self.diff(without_rel)), 1)
        without_element = [line for line in self.lines if "System_Ext(emailService" not in line]
        self.assertEqual(self.diff(without_element), ["element removed: emailService"])

    def test_element_moved_out_of_its_boundary(self):
        moved = [line for line in self.lines if "Container(notifier" not in line]
        moved.insert(3, next(line for line in self.lines if "Container(notifier" in line))
        self.assertEqual(self.diff(moved), ["element changed: notifier"])

    def test_changed_element_type(self):
        self.assertEqual(self.diff(self.edit("ContainerDb(ordersDb", "Container(ordersDb")),
                         ["element changed: ordersDb"])

    def test_layout_config_is_ignored(self):
        self.assertEqual(self.diff(lines_of("container", "rows")), [])

    def test_check_command_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.mmd"
            bad.write_text("\n".join(self.edit("Rel(webApp, orderApi", "Rel(orderApi, webApp")),
                           encoding="utf-8")
            base = FIXTURES / "container" / "baseline.mmd"
            self.assertEqual(run("check", base, FIXTURES / "container" / "connected.mmd").returncode, 0)
            result = run("check", base, bad)
            self.assertEqual(result.returncode, 1)
            self.assertIn("relationship removed", result.stdout)


class CandidateTest(unittest.TestCase):
    def test_candidates_match_golden_files(self):
        for diagram in DIAGRAMS:
            made = c4_layout.make_candidates(lines_of(diagram))
            self.assertEqual([name for name, _ in made], [row["name"] for row in expected(diagram)])
            for name, lines in made:
                self.assertEqual(lines, lines_of(diagram, name), f"{diagram}/{name}")

    def test_candidates_preserve_the_architecture(self):
        for diagram in DIAGRAMS:
            base = lines_of(diagram)
            made = c4_layout.make_candidates(base)
            self.assertEqual(made[0], ("baseline", base))
            self.assertEqual(len({tuple(lines) for _, lines in made}), len(made), "duplicates")
            for name, lines in made:
                self.assertEqual(c4_layout.differences(c4_layout.inventory(base),
                                                       c4_layout.inventory(lines)), [], name)
                if name != "rows":
                    self.assertEqual(sorted(lines), sorted(base), f"{diagram}/{name} edits a line")

                    def is_rel(line):
                        return line.strip().startswith("Rel")

                    self.assertEqual(list(filter(is_rel, lines)), list(filter(is_rel, base)))

    def test_peer_groups_keep_their_position(self):
        def kinds(lines):
            return [line.strip().split("(")[0] for line in lines if "(" in line]

        base = kinds(lines_of("context"))
        for name in ("connected", "primary-path", "reversed-peers"):
            self.assertEqual(kinds(lines_of("context", name)), base, name)

    def test_rows_toggles_an_existing_setting(self):
        once = c4_layout.with_rows(lines_of("tiny"))
        twice = c4_layout.with_rows(once)
        self.assertEqual(len(twice), len(once))
        self.assertIn('$c4ShapeInRow="3"', once[-1])
        self.assertIn('$c4ShapeInRow="2"', twice[-1])


class MeasurementTest(unittest.TestCase):
    def test_metrics_match_expected(self):
        for diagram in DIAGRAMS:
            want = expected(diagram)
            rows = c4_layout.score_files([(r["name"], FIXTURES / diagram / f"{r['name']}.svg") for r in want])
            for got, exp in zip(rows, want):
                self.assertEqual({k: got[k] for k in METRICS}, {k: exp[k] for k in METRICS},
                                 f"{diagram}/{exp['name']}")

    def test_elements_and_relationships_are_all_found(self):
        for diagram in DIAGRAMS:
            inv = c4_layout.inventory(lines_of(diagram))
            svg = c4_layout.read_svg(FIXTURES / diagram / "baseline.svg")
            leaves = {e["alias"] for e in inv["elements"]} - {e["boundary"] for e in inv["elements"]}
            self.assertEqual(set(svg["nodes"]), leaves, diagram)
            self.assertEqual([sorted(e["ends"]) for e in svg["edges"]],
                             [sorted(r[1:3]) for r in inv["relationships"]], diagram)
            self.assertTrue(all(e["label"] for e in svg["edges"]), diagram)

    def test_known_defects_in_component_view(self):
        # Seen in the rendered image: three lines pass through unrelated boxes.
        rows = {r["name"]: r for r in expected("component")}
        self.assertEqual((rows["baseline"]["N"], rows["baseline"]["X"]), (3, 0))
        self.assertEqual(rows["connected"]["N"], 2)
        self.assertTrue(rows["rows"]["same_geometry_as_baseline"])

    def test_geometry_helpers(self):
        self.assertEqual(c4_layout.segments_cross((0, 0), (10, 10), (0, 10), (10, 0)), (5.0, 5.0))
        self.assertIsNone(c4_layout.segments_cross((0, 0), (10, 0), (0, 5), (10, 5)))
        self.assertIsNone(c4_layout.segments_cross((0, 0), (10, 0), (10, 0), (10, 10)))  # shared end
        box = (10, 10, 30, 30)
        self.assertTrue(c4_layout.route_hits([(0, 20), (40, 20)], box))
        self.assertFalse(c4_layout.route_hits([(0, 0), (40, 0)], box))
        self.assertFalse(c4_layout.route_hits([(0, 10), (40, 10)], box))  # along the border

    def test_penalty_weights(self):
        m = {"N": 1, "O": 1, "X": 1, "T": 1, "long": 1}
        self.assertEqual(c4_layout.penalty(m, 1.0), 6 + 6 + 5 + 2 + 2)
        self.assertEqual(c4_layout.penalty(m, 1.6), 21 + 3)


class OptimiseTest(unittest.TestCase):
    def optimise(self, diagram, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("optimise", FIXTURES / diagram / "baseline.mmd", "--out", tmp, *extra)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout), sorted(p.name for p in Path(tmp).iterdir())

    def test_readable_baseline_stops_early(self):
        out, files = self.optimise("tiny", "--mmdc", fake_renderer("tiny"))
        self.assertTrue(out["measured"])
        self.assertTrue(out["baseline_sufficient"])
        self.assertEqual(out["selected"], "baseline")
        self.assertEqual([c["name"] for c in out["candidates"]], ["baseline"])
        self.assertEqual(files, ["baseline.mmd", "baseline.png", "baseline.svg"])

    def test_force_compares_candidates_and_a_tie_keeps_the_baseline(self):
        out, files = self.optimise("tiny", "--force", "--mmdc", fake_renderer("tiny"))
        self.assertFalse(out["baseline_sufficient"])
        self.assertEqual(out["selected"], "baseline")
        self.assertEqual({c["name"] for c in out["candidates"]}, {"baseline", "rows"})
        self.assertIn("rows.svg", files)

    def test_defective_baseline_is_ranked_against_candidates(self):
        out, files = self.optimise("component", "--mmdc", fake_renderer("component"))
        self.assertFalse(out["baseline_sufficient"])
        self.assertEqual(out["selected"], "connected")
        self.assertTrue(out["selected_source"].endswith("connected.mmd"))
        self.assertEqual([Path(p).name for p in out["images"]], ["baseline.png", "connected.png"])
        scores = [c["score"] for c in out["candidates"]]
        self.assertEqual(scores, sorted(scores))
        self.assertEqual({c["name"]: c["score"] for c in out["candidates"]},
                         {r["name"]: r["score"] for r in expected("component")})
        self.assertEqual(out["failed"], [])

    def test_candidate_that_fails_to_render_is_reported(self):
        # A renderer that can only produce two of the five context candidates.
        with tempfile.TemporaryDirectory() as tmp:
            partial = Path(tmp) / "fixtures"
            partial.mkdir()
            for name in ("baseline", "rows"):
                (partial / f"{name}.svg").write_bytes((FIXTURES / "context" / f"{name}.svg").read_bytes())
            cmd = " ".join(shlex.quote(str(p)) for p in (sys.executable, FIXTURES.parent / "fake_mmdc.py", partial))
            result = run("optimise", FIXTURES / "context" / "baseline.mmd", "--out", Path(tmp) / "out", "--mmdc", cmd)
            out = json.loads(result.stdout)
        self.assertEqual({f["name"] for f in out["failed"]}, {"connected", "primary-path", "reversed-peers"})
        self.assertEqual(out["selected"], "baseline")

    def test_baseline_that_fails_to_render_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            cmd = " ".join(shlex.quote(str(p)) for p in (sys.executable, FIXTURES.parent / "fake_mmdc.py", tmp))
            result = run("optimise", FIXTURES / "tiny" / "baseline.mmd", "--out", Path(tmp) / "out", "--mmdc", cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("baseline does not render", result.stderr)

    def test_without_a_renderer_nothing_is_measured(self):
        out, files = self.optimise("container", "--mmdc", "no-such-mermaid-cli")
        self.assertFalse(out["measured"])
        self.assertEqual(out["selected"], "baseline")
        self.assertTrue(all("declaration_distance" in c for c in out["candidates"]))
        self.assertFalse(any(f.endswith(".svg") for f in files))

    def test_score_command(self):
        result = run("score", FIXTURES / "container" / "baseline.svg", FIXTURES / "container" / "primary-path.svg")
        rows = json.loads(result.stdout)["diagrams"]
        want = {r["name"]: r["score"] for r in expected("container")}
        self.assertEqual([r["score"] for r in rows], [want["baseline"], want["primary-path"]])


@unittest.skipUnless(os.environ.get("C4_LAYOUT_MMDC"), "set C4_LAYOUT_MMDC to render with a real Mermaid CLI")
class LiveRenderTest(unittest.TestCase):
    def test_current_renderer_reproduces_the_fixtures(self):
        cmd = shlex.split(os.environ["C4_LAYOUT_MMDC"])
        for diagram in DIAGRAMS:
            with tempfile.TemporaryDirectory() as tmp:
                rendered = []
                for row in expected(diagram):
                    svg = Path(tmp) / f"{row['name']}.svg"
                    self.assertIsNone(c4_layout.render(cmd, FIXTURES / diagram / f"{row['name']}.mmd", svg))
                    rendered.append((row["name"], svg))
                got = c4_layout.score_files(rendered)
            for row, exp in zip(got, expected(diagram)):
                self.assertEqual({k: row[k] for k in METRICS}, {k: exp[k] for k in METRICS},
                                 f"{diagram}/{exp['name']}: the renderer's layout has changed")


if __name__ == "__main__":
    unittest.main()
