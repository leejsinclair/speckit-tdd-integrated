#!/usr/bin/env python3
"""Writes the fixture feature directories under tests/fixtures/features/.

Each case is a copy of ``valid-minimal`` with one defect, so the directories are
generated from one description and then committed. Run from anywhere:

    python3 -B tests/fixtures/make_features.py

Evidence documents are hand-built here, not written by the check script: the
check chain and fingerprints are computed by the independent functions below,
which follow contracts/artefact-formats.md section 3.
"""

import hashlib
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURES = os.path.join(HERE, "features")

FAKE = "sh tests/fixtures/bin/fake_test.sh"

RECORD_HEADER = [
    "Seq", "Time", "Task", "Obligations", "Phase", "Command", "Selector", "Result", "Valid",
    "Classification", "Files", "Fingerprint", "Note", "Check",
]  # fmt: skip
BASELINE_HEADER = ["Seq", "Command", "Result", "Pre-existing failures"]
EXCEPTION_HEADER = [
    "ID", "Time", "Task", "Obligations", "Kind", "Rationale", "Alternative verification",
    "Needs approval", "Approved by",
]  # fmt: skip
EXPECTATION_HEADER = [
    "ID", "Time", "Task", "Files", "Requirements", "Justification", "Alters behaviour",
    "Approved by", "New fingerprint",
]  # fmt: skip
DECISION_HEADER = ["ID", "Opened", "Question", "Tasks", "Status", "Answer", "Decided by", "Resolved"]
CHAINED = [name for name in RECORD_HEADER if name not in ("Classification", "Note", "Check")]


# ---------------------------------------------------------------------------
# Independent implementations of the contract's hashes
# ---------------------------------------------------------------------------


def check_value(previous, row):
    """First six hex characters of SHA-256 over the previous check and the row's cells."""
    text = previous + "\n" + "|".join(row[name] for name in CHAINED)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:6]


def fingerprint(contents):
    """Fingerprint of ``{path: bytes or None}``; None stands for a missing file."""
    if not contents:
        return "-"
    digest = hashlib.sha256()
    for path in sorted(contents):
        digest.update(path.encode("utf-8") + b"\0")
        data = contents[path]
        digest.update(b"\0" if data is None else b"\1" + data)
        digest.update(b"\0")
    return digest.hexdigest()[:6]


FP_A = fingerprint({"tests/test_cart.py": b"assert total([]) == 0\n"})
FP_B = fingerprint({"tests/test_cart.py": b"assert True\n"})


# ---------------------------------------------------------------------------
# Markdown builders
# ---------------------------------------------------------------------------


def table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("-" * (len(name) + 2) for name in header) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(row[name] for name in header) + " |")
    return "\n".join(lines) + "\n"


def stamp(seq):
    return f"2026-10-10T13:{seq:02d}:00Z"


def rec(task, vos, phase, command, selector, result, valid, classification="-", files="-", fp="-", note="-"):
    return {
        "Task": task, "Obligations": vos, "Phase": phase, "Command": command, "Selector": selector,
        "Result": result, "Valid": valid, "Classification": classification, "Files": files,
        "Fingerprint": fp, "Note": note,
    }  # fmt: skip


def baseline(result="pass", note="-", command="suite"):
    return rec("-", "-", "baseline", command, "-", result, "yes", "-" if result == "pass" else "unclassified", note=note)


def red(task, vo, selector="assert", fp=FP_A, files="tests/test_cart.py", command="unit"):
    return rec(task, vo, "red", command, selector, "fail", "yes", "assertion", files, fp, "expected: AssertionError")


def green(task, vo, selector="pass", fp=FP_A, files="tests/test_cart.py", command="unit"):
    return rec(task, vo, "green", command, selector, "pass", "yes", "-", files, fp)


def checkpoint(result="pass", command="suite"):
    valid = "yes" if result == "pass" else "no"
    return rec("-", "-", "checkpoint", command, "-", result, valid, "-" if result == "pass" else "unclassified")


def chain(records):
    """Number the records and give each its check value."""
    previous = ""
    rows = []
    for index, record in enumerate(records, 1):
        row = dict(record)
        row.setdefault("Seq", str(index))
        row.setdefault("Time", stamp(index))
        if "Check" not in row:
            row["Check"] = check_value(previous, row)
        previous = row["Check"]
        rows.append(row)
    return rows


def exc(ident, task, vos, kind, rationale="No seam to test through", alternative="Existing suite run before and after",
        needs="no", approved="-", after=1):  # fmt: skip
    """An exception raised just after record ``after``: record n is stamped minute n."""
    return {
        "ID": ident, "Time": stamp(after), "Task": task, "Obligations": vos, "Kind": kind, "Rationale": rationale,
        "Alternative verification": alternative, "Needs approval": needs, "Approved by": approved,
    }  # fmt: skip


def xc(ident, task, fp, requirements="FR-001", alters="no", approved="-", files="tests/test_cart.py"):
    return {
        "ID": ident, "Time": stamp(31), "Task": task, "Files": files, "Requirements": requirements,
        "Justification": "The expected total was mistyped", "Alters behaviour": alters,
        "Approved by": approved, "New fingerprint": fp,
    }  # fmt: skip


def dn(ident, tasks, status="open", answer="-", by="-"):
    return {
        "ID": ident, "Opened": stamp(32), "Question": "Should an empty cart raise or return zero?",
        "Tasks": tasks, "Status": status, "Answer": answer, "Decided by": by,
        "Resolved": "-" if status == "open" else stamp(33),
    }  # fmt: skip


DEFAULT_SUMMARY = "_Generated from the tables below on 2026-10-10T14:00:00Z._\n"


def evidence(records, exceptions=(), expectations=(), decisions=(), summary=DEFAULT_SUMMARY, name="001-demo"):
    rows = chain(records)
    base_rows = []
    for row in rows:
        if row["Phase"] == "baseline":
            failures = "-"
            if row["Result"] == "fail":
                failures = row["Note"] if row["Note"] != "-" else "failing before work began"
            base_rows.append(
                {"Seq": row["Seq"], "Command": row["Command"], "Result": row["Result"],
                 "Pre-existing failures": failures}
            )  # fmt: skip
    return (
        "# TDD Evidence: " + name + "\n\n"
        "<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->\n\n"
        "## Summary\n\n" + summary + "\n"
        "## Baseline\n\n" + table(BASELINE_HEADER, base_rows) + "\n"
        "## Test execution records\n\n" + table(RECORD_HEADER, rows) + "\n"
        "## Exceptions\n\n" + table(EXCEPTION_HEADER, list(exceptions)) + "\n"
        "## Expectation changes\n\n" + table(EXPECTATION_HEADER, list(expectations)) + "\n"
        "## Decisions\n\n" + table(DECISION_HEADER, list(decisions))
    )


# ---------------------------------------------------------------------------
# valid-minimal
# ---------------------------------------------------------------------------

SPEC = """# Feature Specification: Cart totals

## User Scenarios & Testing

### User Story 1 - A shopper sees the cart total (Priority: P1)

A shopper opens the cart and sees what the order will cost.

**Acceptance Scenarios**:

1. **Given** an empty cart, **When** it is totalled, **Then** the total is zero.
2. **Given** a cart with two items, **When** it is totalled, **Then** the total is their sum.

---

### Edge Cases

- A price of zero is allowed.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST total an empty cart as zero.
- **FR-002**: The system MUST total a cart as the sum of its item prices.
- **FR-003**: The cart page MUST follow the shop's visual layout.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A shopper sees the total within one second.
"""

PLAN = """# Implementation Plan: Cart totals

## Summary

Add a cart total.

## Verification Plan

### Verification commands

| ID | Command | Scope | Source |
|----|---------|-------|--------|
| unit | `sh tests/fixtures/bin/fake_test.sh {select}` | focused | tests/fixtures/bin |
| suite | `sh tests/fixtures/bin/fake_test.sh pass` | broad | tests/fixtures/bin |

### Verification obligations

| ID | Requirements | Scenario | Expected outcome | Level | Origin |
|----|--------------|----------|------------------|-------|--------|
| VO-001 | FR-001, US1-AS1 | An empty cart is totalled | The total is zero and no error is raised | unit | planned |
| VO-002 | FR-002, US1-AS2, SC-001, DC-01, EC-01 | A cart with a zero-priced item is totalled through the public interface | The total is the sum of the prices | integration | planned |

### Verification exemptions

| Requirement | Reason | Alternative verification |
|-------------|--------|--------------------------|
| FR-003 | Visual layout has no stable automated check in this project | Reviewed against the design at code review |

## Project Structure

Single project.
"""

TASKS = """# Tasks: Cart totals

## Phase 1: User Story 1

- [ ] T011 [P] [US1] [VO-001] Write the failing test for an empty cart total in tests/test_cart.py
- [ ] T012 [US1] [VO-001] Implement the empty cart total in src/cart.py
- [ ] T013 [US1] [VO-002] Write the failing test for a cart of items in tests/test_cart.py
- [ ] T014 [US1] [VO-002] Implement the sum of item prices in src/cart.py
- [ ] T015 [US1] [NT: README wording only] Document the cart total in README.md
"""

NOT_VERIFIED_VO2 = (
    "FR-002 (VO-002 planned), US1-AS2 (VO-002 planned), SC-001 (VO-002 planned), DC-01 (VO-002 planned), "
    "EC-01 (VO-002 planned), FR-003 (exempt: see plan)"
)
EXAMPLE_SUMMARY = (
    "_Generated from the tables below on 2026-10-10T14:02:11Z._\n\n"
    "| Obligation | Requirements | Status | Tests | Latest result |\n"
    "|------------|--------------|--------|-------|---------------|\n"
    "| VO-001 | FR-001, US1-AS1 | verified | assert, pass | pass (#3) |\n"
    "| VO-002 | FR-002, US1-AS2, SC-001, DC-01, EC-01 | planned | - | - |\n\n"
    "**Not verified**: " + NOT_VERIFIED_VO2 + ".\n\n"
    "**Open decisions**: none. **Exceptions**: none. **Expectation changes**: none.\n\n"
    "**Pre-existing failures**: none.\n"
)

VALID_RECORDS = [baseline(), red("T011", "VO-001"), green("T012", "VO-001")]


def valid_minimal():
    return {
        "spec.md": SPEC,
        "plan.md": PLAN,
        "tasks.md": TASKS,
        "tdd-evidence.md": evidence(VALID_RECORDS, summary=EXAMPLE_SUMMARY),
    }


def swap(text, old, new, count=1):
    """Replace ``old`` with ``new``, failing loudly when ``old`` is absent."""
    if text.count(old) < 1:
        raise AssertionError("fixture text not found: " + old)
    return text.replace(old, new, count)


def variant(**changes):
    """A copy of valid-minimal with whole files replaced or removed (None)."""
    files = valid_minimal()
    for key, value in changes.items():
        name = {"spec": "spec.md", "plan": "plan.md", "tasks": "tasks.md", "evidence": "tdd-evidence.md"}[key]
        if value is None:
            del files[name]
        else:
            files[name] = value
    return files


MARKER = (
    "### Behaviour checklist\n\n"
    "Behaviour items are in [tests/behaviour-checklist.md](tests/behaviour-checklist.md).\n"
)


def checklist_text(sections, other=None, name="001-demo"):
    """Write the checklist format of contracts/behaviour-checklist.md section 1.

    ``sections`` is a list of ``(heading, quote, items)`` with ``heading`` such as
    ``US1-AS1``; ``other`` is a list of items or None. An item is a dict with ``id``,
    ``expresses`` and ``verified`` (lists or strings) and ``clauses``, a list of
    ``(keyword, text)`` pairs.
    """

    def join(value):
        return value if isinstance(value, str) else ", ".join(value)

    def item_lines(item):
        lines = [f"- **{item['id']}** Expresses: {join(item['expresses'])}. Verified by: {join(item['verified'])}."]
        lines += [f"  - **{keyword}** {text}" for keyword, text in item["clauses"]]
        return lines

    out = ["# Behaviour Checklist: " + name, ""]
    for heading, quote, items in sections:
        out += ["## " + heading, ""]
        if quote is not None:
            out += ["> " + line for line in quote.splitlines()] + [""]
        for item in items:
            out += item_lines(item)
        out.append("")
    if other is not None:
        out += ["## Other behaviours", ""]
        for item in other:
            out += item_lines(item)
        out.append("")
    return "\n".join(out)


def with_checklist(checklist=None, **changes):
    """A ``variant()`` whose plan holds ``MARKER`` and that carries ``tests/behaviour-checklist.md``."""
    files = variant(**changes)
    plan = files["plan.md"]
    if MARKER not in plan:
        files["plan.md"] = swap(plan, "\n## Project Structure", "\n" + MARKER + "\n## Project Structure")
    if checklist is not None:
        files["tests/behaviour-checklist.md"] = checklist
    return files


CASES = {}


def case(name):
    def register(function):
        CASES[name] = function
        return function

    return register


CASES["valid-minimal"] = valid_minimal


# ---------------------------------------------------------------------------
# Parser cases (T022)
# ---------------------------------------------------------------------------


@case("parse-no-section")
def _parse_no_section():
    return variant(plan=swap(PLAN, "## Verification Plan", "## Testing notes"))


@case("parse-wrong-header")
def _parse_wrong_header():
    return variant(plan=swap(PLAN, "| ID | Command | Scope | Source |", "| ID | Command line | Scope | Source |"))


@case("parse-bad-enum")
def _parse_bad_enum():
    plan = swap(PLAN, "| focused |", "| wide |")
    plan = swap(plan, "| unit | planned |", "| smoke | planned |")
    plan = swap(plan, "| integration | planned |", "| integration | guessed |")
    return variant(plan=plan)


@case("parse-bad-ids")
def _parse_bad_ids():
    plan = swap(PLAN, "| unit | `sh", "| Unit_1 | `sh")
    plan = swap(plan, "fake_test.sh pass` |", "fake_test.sh {select} {select}` |")
    plan = swap(plan, "| VO-002 |", "| VO-001 |")
    plan += ""
    plan = swap(
        plan,
        "\n### Verification exemptions",
        "| VO-3 | FR-002 | A short id | Rejected | unit | planned |\n\n### Verification exemptions",
    )
    return variant(plan=plan)


@case("parse-unquoted-command")
def _parse_unquoted_command():
    return variant(plan=swap(PLAN, "| `sh tests/fixtures/bin/fake_test.sh pass` |", "| make test |"))


@case("parse-no-exemptions")
def _parse_no_exemptions():
    plan = swap(PLAN, "| FR-003 | Visual layout has no stable automated check in this project | "
                      "Reviewed against the design at code review |", "| None | - | - |")  # fmt: skip
    return variant(plan=plan)


@case("parse-task-labels")
def _parse_task_labels():
    tasks = """# Tasks

- [ ] T001 Set up the project (no label at all)
- [x] T002 [P] [US1] [VO-001] [VO-002] Write both failing tests
- [X] T003 [US1] [VO-001] Implement the first behaviour
- [ ] T004 [US1] [VO-002] [VO-003] Implement the second behaviour and a third
- [ ] T005 [US1] [VO-003] Finish the third
- [ ] T006 [NT: ] Tidy with an empty reason
- [ ] T007 [NT: configuration with no observable effect] Add the editor settings
- [ ] T008 [US2] [VO-001] [NT: ignored when an obligation is named] Mixed labels, see [VO-009] in text
- [ ] T12 A task id that is too short to be a task
* [ ] T009 [VO-001] A bullet that is not a task line
"""
    return variant(tasks=tasks)


@case("parse-evidence-wrong-header")
def _parse_evidence_wrong_header():
    text = evidence(VALID_RECORDS)
    return variant(evidence=swap(text, "| Seq | Time | Task | Obligations |", "| Seq | When | Task | Obligations |"))


@case("parse-evidence-bad-row")
def _parse_evidence_bad_row():
    text = evidence(VALID_RECORDS)
    text = swap(text, "| red | unit |", "| purple | unit |")
    text = swap(text, "| 3 | 2026", "| three | 2026")
    return variant(evidence=text)


@case("parse-evidence-full")
def _parse_evidence_full():
    records = VALID_RECORDS + [rec("T014", "VO-002", "green", "unit", "import", "fail", "no", "unclassified")]
    return variant(
        evidence=evidence(
            records,
            exceptions=[exc("EX-01", "T013", "VO-002", "legacy", needs="yes", approved="Lee Sinclair")],
            expectations=[xc("XC-01", "T012", FP_B, requirements="FR-001, US1-AS1", alters="yes", approved="Lee")],
            decisions=[dn("DN-01", "T013, T014"), dn("DN-02", "T015", "resolved", "Return zero", "Lee")],
        )
    )


# ---------------------------------------------------------------------------
# plan check cases (T025)
# ---------------------------------------------------------------------------

VO1_ROW = "| VO-001 | FR-001, US1-AS1 | An empty cart is totalled | The total is zero and no error is raised | unit | planned |"
EXEMPTION_ROW = (
    "| FR-003 | Visual layout has no stable automated check in this project | "
    "Reviewed against the design at code review |"
)


@case("plan-no-section")
def _plan_no_section():
    return variant(plan=swap(PLAN, "## Verification Plan", "## Testing notes"))


@case("plan-no-commands")
def _plan_no_commands():
    plan = swap(PLAN, "| unit | `sh tests/fixtures/bin/fake_test.sh {select}` | focused | tests/fixtures/bin |\n", "")
    plan = swap(plan, "| suite | `sh tests/fixtures/bin/fake_test.sh pass` | broad | tests/fixtures/bin |\n", "")
    return variant(plan=plan)


@case("plan-uncovered-fr")
def _plan_uncovered_fr():
    return variant(plan=swap(PLAN, "| VO-001 | FR-001, US1-AS1 |", "| VO-001 | US1-AS1 |"))


@case("plan-uncovered-scenario")
def _plan_uncovered_scenario():
    return variant(plan=swap(PLAN, "| VO-002 | FR-002, US1-AS2, SC-001,", "| VO-002 | FR-002, SC-001,"))


@case("plan-empty-outcome")
def _plan_empty_outcome():
    return variant(plan=swap(PLAN, "| The total is zero and no error is raised |", "| - |"))


@case("plan-empty-exemption-reason")
def _plan_empty_exemption_reason():
    return variant(plan=swap(PLAN, "| Visual layout has no stable automated check in this project |", "| - |"))


@case("plan-unknown-requirement")
def _plan_unknown_requirement():
    return variant(plan=swap(PLAN, "| VO-001 | FR-001, US1-AS1 |", "| VO-001 | FR-001, US1-AS1, FR-099 |"))


@case("plan-unknown-prefix")
def _plan_unknown_prefix():
    return variant(plan=swap(PLAN, "| VO-001 | FR-001, US1-AS1 |", "| VO-001 | FR-001, US1-AS1, XX-01 |"))


# ---------------------------------------------------------------------------
# tasks check cases (T026)
# ---------------------------------------------------------------------------

T013_LINE = "- [ ] T013 [US1] [VO-002] Write the failing test for a cart of items in tests/test_cart.py\n"
T014_LINE = "- [ ] T014 [US1] [VO-002] Implement the sum of item prices in src/cart.py\n"


@case("tasks-unlabelled")
def _tasks_unlabelled():
    return variant(tasks=swap(TASKS, "T015 [US1] [NT: README wording only] Document", "T015 [US1] Document"))


@case("tasks-unknown-obligation")
def _tasks_unknown_obligation():
    return variant(tasks=swap(TASKS, "T015 [US1] [NT: README wording only]", "T015 [US1] [VO-009]"))


@case("tasks-obligation-without-task")
def _tasks_obligation_without_task():
    return variant(tasks=swap(swap(TASKS, T013_LINE, ""), T014_LINE, ""))


@case("tasks-obligation-without-behaviour")
def _tasks_obligation_without_behaviour():
    return variant(tasks=swap(TASKS, T014_LINE, ""))


@case("tasks-behaviour-before-test")
def _tasks_behaviour_before_test():
    # T012 is the first task to name VO-002 but not the first to name VO-001,
    # so it is a behaviour task and VO-002 has no test task before it.
    return variant(tasks=swap(TASKS, "T012 [US1] [VO-001] Implement", "T012 [US1] [VO-001] [VO-002] Implement"))


# ---------------------------------------------------------------------------
# Gate cases for G1, G3, G4 and G9 (T041). Every check chain is valid.
# ---------------------------------------------------------------------------


def done(tasks, *idents):
    """Mark the named tasks complete."""
    for ident in idents:
        tasks = swap(tasks, f"- [ ] {ident} ", f"- [X] {ident} ")
    return tasks


RED_1 = red("T011", "VO-001")
GREEN_1 = green("T012", "VO-001")
RED_2 = red("T013", "VO-002")
GREEN_2 = green("T014", "VO-002")
FIRST_CYCLE = [baseline(), RED_1, GREEN_1]
BOTH_CYCLES = [baseline(), RED_1, GREEN_1, RED_2, GREEN_2, checkpoint()]


@case("gate-g1-fail")
def _gate_g1_fail():
    tasks = swap(TASKS, "T015 [US1] [NT: README wording only] Document", "T015 [US1] Document")
    return variant(tasks=done(tasks, "T015"), evidence=evidence([baseline()]))


@case("gate-g1-pass")
def _gate_g1_pass():
    return variant(tasks=done(TASKS, "T015"), evidence=evidence([baseline()]))


@case("gate-g3-fail")
def _gate_g3_fail():
    # The only red run passed on first run, so it is not a valid failing-first record.
    invalid = rec("T011", "VO-001", "red", "unit", "pass", "pass", "no", "-", "tests/test_cart.py", FP_A,
                  "passed on first run: investigate")  # fmt: skip
    return variant(tasks=done(TASKS, "T011"), evidence=evidence([baseline(), invalid]))


@case("gate-g3-pass")
def _gate_g3_pass():
    return variant(tasks=done(TASKS, "T011"), evidence=evidence([baseline(), RED_1]))


@case("gate-g4-fail")
def _gate_g4_fail():
    # The passing run came before the failing-first run, and none follows it.
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence([baseline(), GREEN_1, RED_1]))


@case("gate-g4-pass")
def _gate_g4_pass():
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence(FIRST_CYCLE))


@case("gate-g9-fail")
def _gate_g9_fail():
    undeclared = green("T012", "VO-001", command="adhoc")
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence([baseline(), RED_1, undeclared]))


@case("gate-g9-pass")
def _gate_g9_pass():
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence(FIRST_CYCLE))


@case("gate-all-pass")
def _gate_all_pass():
    return variant(tasks=done(TASKS, "T011", "T012", "T015"), evidence=evidence(FIRST_CYCLE))


@case("gate-all-fail")
def _gate_all_fail():
    return variant(tasks=done(TASKS, "T011", "T012", "T014", "T015"), evidence=evidence(FIRST_CYCLE))


# ---------------------------------------------------------------------------
# Gate cases for G5 and G8 (T054)
# ---------------------------------------------------------------------------

GREEN_CHANGED = green("T012", "VO-001", fp=FP_B)
CHANGED_CYCLE = [baseline(), RED_1, GREEN_CHANGED]


@case("gate-g5-fail")
def _gate_g5_fail():
    # The test file's fingerprint differs between red and green and nothing records why.
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence(CHANGED_CYCLE))


@case("gate-g5-pass")
def _gate_g5_pass():
    change = xc("XC-01", "T012", FP_B)
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence(CHANGED_CYCLE, expectations=[change]))


@case("gate-g5-other-task")
def _gate_g5_other_task():
    # The expectation change carries the fingerprint but was recorded for another task.
    change = xc("XC-01", "T014", FP_B)
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence(CHANGED_CYCLE, expectations=[change]))


@case("gate-g5-no-red")
def _gate_g5_no_red():
    # No valid failing-first record: G3 fails and G5 has nothing to compare.
    only_green = green("T012", "VO-001", files="-", fp="-")
    return variant(tasks=done(TASKS, "T012"), evidence=evidence([baseline(), only_green]))


@case("gate-g8-fail-no-requirement")
def _gate_g8_fail_no_requirement():
    change = xc("XC-01", "T012", FP_B, requirements="-")
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence(CHANGED_CYCLE, expectations=[change]))


@case("gate-g8-fail-no-approval")
def _gate_g8_fail_no_approval():
    change = xc("XC-01", "T012", FP_B, alters="yes")
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence(CHANGED_CYCLE, expectations=[change]))


@case("gate-g8-pass")
def _gate_g8_pass():
    change = xc("XC-01", "T012", FP_B, alters="yes", approved="Lee Sinclair")
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence(CHANGED_CYCLE, expectations=[change]))


# ---------------------------------------------------------------------------
# Gate cases for G2, G6, G7 and exceptions (T060)
# ---------------------------------------------------------------------------

ALL_DONE = done(TASKS, "T011", "T012", "T013", "T014")
FAILED_GREEN = rec("T012", "VO-001", "green", "unit", "assert", "fail", "no", "defect", "tests/test_cart.py", FP_A)
UNCLASSIFIED_GREEN = dict(FAILED_GREEN, Classification="unclassified")


@case("gate-g2-fail")
def _gate_g2_fail():
    return variant(tasks=ALL_DONE, evidence=evidence(BOTH_CYCLES, decisions=[dn("DN-01", "T013, T014")]))


@case("gate-g2-pass")
def _gate_g2_pass():
    resolved = dn("DN-01", "T013, T014", "resolved", "Return zero", "Lee Sinclair")
    return variant(tasks=ALL_DONE, evidence=evidence(BOTH_CYCLES, decisions=[resolved]))


@case("gate-g6-fail-latest")
def _gate_g6_fail_latest():
    # The task passed and then failed: its latest record is a failure, classified as a defect.
    return variant(tasks=ALL_DONE, evidence=evidence([baseline(), RED_1, GREEN_1, FAILED_GREEN]))


@case("gate-g6-fail-unclassified")
def _gate_g6_fail_unclassified():
    return variant(tasks=ALL_DONE, evidence=evidence([baseline(), RED_1, UNCLASSIFIED_GREEN, GREEN_1]))


@case("gate-g6-pass")
def _gate_g6_pass():
    return variant(tasks=ALL_DONE, evidence=evidence([baseline(), RED_1, FAILED_GREEN, GREEN_1]))


@case("gate-unreliable")
def _gate_unreliable():
    # Both runs for VO-001 were later classified unreliable, so neither counts as evidence.
    flaky_red = dict(RED_1, Classification="unreliable")
    flaky_fail = dict(FAILED_GREEN, Classification="unreliable")
    return variant(tasks=ALL_DONE, evidence=evidence([baseline(), flaky_red, flaky_fail]))


def _with_exception(records, exception, tasks=ALL_DONE):
    return variant(tasks=tasks, evidence=evidence(records, exceptions=[exception]))


NO_RED = exc("EX-01", "T013", "VO-002", "no-meaningful-red")


@case("gate-exception-pass")
def _gate_exception_pass():
    # One exception raised on the test task covers the obligation's behaviour task too.
    return _with_exception([baseline(), GREEN_2], NO_RED)


@case("gate-exception-no-green")
def _gate_exception_no_green():
    return _with_exception([baseline()], NO_RED)


@case("gate-exception-green-before")
def _gate_exception_green_before():
    # The only passing record was made before the exception was raised.
    return _with_exception([baseline(), GREEN_2, checkpoint()], dict(NO_RED, Time=stamp(3)))


@case("gate-exception-task-only")
def _gate_exception_task_only():
    # An exception naming no obligation covers only the task it was raised on.
    return _with_exception([baseline(), GREEN_2], exc("EX-01", "T013", "-", "no-meaningful-red"))


PRESERVING = exc("EX-01", "T013", "VO-002", "behaviour-preserving")
REFACTOR_SUITE = rec("T014", "VO-002", "refactor", "suite", "-", "pass", "yes")


@case("gate-exception-preserving-pass")
def _gate_exception_preserving_pass():
    return _with_exception([baseline(), REFACTOR_SUITE], PRESERVING)


@case("gate-exception-preserving-fail")
def _gate_exception_preserving_fail():
    # A passing run after the change, but none before it on the same selector.
    other = rec("T014", "VO-002", "refactor", "unit", "pass", "pass", "yes")
    return _with_exception([baseline(), other], PRESERVING)


@case("gate-exception-preserving-no-refactor")
def _gate_exception_preserving_no_refactor():
    return _with_exception([baseline(), GREEN_2], PRESERVING)


@case("gate-exception-blocked")
def _gate_exception_blocked():
    blocked = exc("EX-01", "T013", "VO-002", "environment-blocked", "The test database cannot be reached", "-")
    return _with_exception([baseline(), GREEN_2], blocked)


@case("gate-g7-fail-no-rationale")
def _gate_g7_fail_no_rationale():
    return _with_exception([baseline(), GREEN_2], exc("EX-01", "T013", "VO-002", "generated-code", rationale="-"))


@case("gate-g7-fail-no-alternative")
def _gate_g7_fail_no_alternative():
    return _with_exception([baseline(), GREEN_2], exc("EX-01", "T013", "VO-002", "generated-code", alternative="-"))


@case("gate-g7-fail-flagged")
def _gate_g7_fail_flagged():
    return _with_exception([baseline(), GREEN_2], exc("EX-01", "T013", "VO-002", "migration", needs="yes"))


@case("gate-g7-fail-kind")
def _gate_g7_fail_kind():
    # Not flagged, but the kind is beyond the agent's authority.
    return _with_exception([baseline(), GREEN_2], exc("EX-01", "T013", "VO-002", "legacy", needs="no"))


@case("gate-g7-fail-none")
def _gate_g7_fail_none():
    # Not flagged, but no alternative verification is offered.
    return _with_exception([baseline(), GREEN_2], exc("EX-01", "T013", "VO-002", "migration", alternative="none"))


@case("gate-g7-pass")
def _gate_g7_pass():
    approved = exc("EX-01", "T013", "VO-002", "legacy", needs="yes", approved="Lee Sinclair")
    return _with_exception([baseline(), GREEN_2], approved)


# ---------------------------------------------------------------------------
# Status cases (T065): one per derived status of the data model's table
# ---------------------------------------------------------------------------

ENV_FAIL_2 = rec("T014", "VO-002", "green", "unit", "import", "fail", "no", "environment", "tests/test_cart.py", FP_A,
                 "the test database was unreachable")  # fmt: skip


@case("status-planned")
def _status_planned():
    return variant(evidence=evidence([baseline()]))


@case("status-in-progress")
def _status_in_progress():
    return variant(tasks=done(TASKS, "T011"), evidence=evidence([baseline(), RED_1]))


@case("status-verified")
def _status_verified():
    return variant(tasks=done(TASKS, "T011", "T012"), evidence=evidence(FIRST_CYCLE))


@case("status-verified-by-exception")
def _status_verified_by_exception():
    approved = exc("EX-01", "T013", "VO-002", "legacy", needs="yes", approved="Lee Sinclair")
    return variant(tasks=ALL_DONE, evidence=evidence([baseline(), RED_1, GREEN_1, GREEN_2], exceptions=[approved]))


@case("status-blocked-environment")
def _status_blocked_environment():
    return variant(tasks=done(TASKS, "T011", "T012", "T013"), evidence=evidence(FIRST_CYCLE + [RED_2, ENV_FAIL_2]))


@case("status-blocked-decision")
def _status_blocked_decision():
    return variant(
        tasks=done(TASKS, "T011", "T012", "T013"),
        evidence=evidence(FIRST_CYCLE + [RED_2], decisions=[dn("DN-01", "T014")]),
    )


@case("status-failed")
def _status_failed():
    return variant(tasks=done(TASKS, "T011"), evidence=evidence([baseline(), RED_1, FAILED_GREEN]))


@case("status-preexisting-failure")
def _status_preexisting_failure():
    failing = baseline("fail", "test_old_total fails", command="suite")
    change = xc("XC-01", "T012", FP_B, alters="yes", approved="Lee Sinclair")
    records = [failing, RED_1, GREEN_CHANGED, RED_2, GREEN_2]
    return variant(tasks=ALL_DONE, evidence=evidence(records, expectations=[change]))


# ---------------------------------------------------------------------------
# Compliance cases (T076): one failing and one passing case per rule C1 to C7.
# The stored Summary of each is written out here as the view it should equal.
# ---------------------------------------------------------------------------

EVERY_TASK = done(TASKS, "T011", "T012", "T013", "T014", "T015")
REQS_1 = "FR-001, US1-AS1"
REQS_2 = "FR-002, US1-AS2, SC-001, DC-01, EC-01"
NONE_LINE = "**Open decisions**: none. **Exceptions**: none. **Expectation changes**: none."
VERIFIED_1 = "verified | assert, pass | pass (#3)"
VERIFIED_2 = "verified | assert, pass | pass (#5)"


def unverified(*pairs, exempt=True):
    parts = []
    for requirements, reason in pairs:
        parts.extend(f"{ident} ({reason})" for ident in requirements.split(", "))
    if exempt:
        parts.append("FR-003 (exempt: see plan)")
    return ", ".join(parts) or "none"


def summary(row_1, row_2, not_verified=None, failures="none", reqs_1=REQS_1, extra_rows=()):
    rows = [f"| VO-001 | {reqs_1} | {row_1} |", f"| VO-002 | {REQS_2} | {row_2} |"] + list(extra_rows)
    return (
        "_Generated from the tables below on 2026-10-10T14:00:00Z._\n\n"
        "| Obligation | Requirements | Status | Tests | Latest result |\n"
        "|------------|--------------|--------|-------|---------------|\n"
        + "\n".join(rows) + "\n\n"
        "**Not verified**: " + (not_verified if not_verified is not None else unverified()) + ".\n\n"
        + NONE_LINE + "\n\n"
        "**Pre-existing failures**: " + failures + ".\n"
    )  # fmt: skip


COMPLIANT_SUMMARY = summary(VERIFIED_1, VERIFIED_2)


def compliant(**changes):
    files = variant(tasks=EVERY_TASK, evidence=evidence(BOTH_CYCLES, summary=COMPLIANT_SUMMARY))
    files.update(variant(**changes) if changes else {})
    if "tasks" not in changes:
        files["tasks.md"] = EVERY_TASK
    if "evidence" not in changes:
        files["tdd-evidence.md"] = evidence(BOTH_CYCLES, summary=COMPLIANT_SUMMARY)
    return files


for _rule in ("c1", "c2", "c3", "c4", "c5", "c6", "c7"):
    CASES[f"compliance-{_rule}-pass"] = compliant


@case("compliance-c1-fail")
def _compliance_c1_fail():
    plan = swap(PLAN, "| VO-001 | FR-001, US1-AS1 |", "| VO-001 | US1-AS1 |")
    text = evidence(BOTH_CYCLES, summary=summary(VERIFIED_1, VERIFIED_2, reqs_1="US1-AS1"))
    return compliant(plan=plan, evidence=text)


@case("compliance-c2-fail")
def _compliance_c2_fail():
    return compliant(tasks=swap(EVERY_TASK, done(T014_LINE, "T014"), ""))


@case("compliance-c3-fail")
def _compliance_c3_fail():
    return compliant(tasks=swap(EVERY_TASK, "T012 [US1] [VO-001] Implement", "T012 [US1] [VO-001] [VO-002] Implement"))


@case("compliance-c4-fail")
def _compliance_c4_fail():
    # Row 3 was edited by hand after it was written: its selector no longer matches its check value.
    text = evidence(BOTH_CYCLES, summary=summary("verified | assert, edited | pass (#3)", VERIFIED_2))
    return compliant(evidence=swap(text, "| green | unit | pass | pass |", "| green | unit | edited | pass |"))


@case("compliance-c5-fail")
def _compliance_c5_fail():
    records = [baseline(), RED_1, green("T012", "VO-001", command="adhoc"), RED_2, GREEN_2, checkpoint()]
    return compliant(evidence=evidence(records, summary=COMPLIANT_SUMMARY))


@case("compliance-c6-fail-no-checkpoint")
def _compliance_c6_fail_no_checkpoint():
    return compliant(evidence=evidence(BOTH_CYCLES[:-1], summary=COMPLIANT_SUMMARY))


@case("compliance-c6-fail-checkpoint")
def _compliance_c6_fail_checkpoint():
    # The broad suite passed before the work and fails after it.
    return compliant(evidence=evidence(BOTH_CYCLES + [checkpoint("fail")], summary=COMPLIANT_SUMMARY))


PREEXISTING = [baseline("fail", "test_old_total fails")] + BOTH_CYCLES[1:-1] + [checkpoint("fail")]
PREEXISTING_LINE = "#1 suite: test_old_total fails"


@case("compliance-c6-pass-preexisting")
def _compliance_c6_pass_preexisting():
    # The latest checkpoint fails, as the baseline of the same command did, and the Summary says so.
    text = evidence(PREEXISTING, summary=summary(VERIFIED_1, VERIFIED_2, failures=PREEXISTING_LINE))
    return compliant(evidence=text)


@case("compliance-c6-fail-not-reported")
def _compliance_c6_fail_not_reported():
    return compliant(evidence=evidence(PREEXISTING, summary=COMPLIANT_SUMMARY))


@case("compliance-c6-fail-first-record")
def _compliance_c6_fail_first_record():
    records = [RED_1, baseline(), GREEN_1, RED_2, GREEN_2, checkpoint()]
    text = evidence(records, summary=summary("verified | assert, pass | pass (#3)", VERIFIED_2))
    return compliant(evidence=text)


PLANNED_2 = unverified((REQS_2, "VO-002 planned"))


@case("compliance-c7-fail-planned")
def _compliance_c7_fail_planned():
    text = evidence(FIRST_CYCLE + [checkpoint()], summary=summary(VERIFIED_1, "planned | - | -", PLANNED_2))
    return compliant(tasks=done(TASKS, "T011", "T012", "T015"), evidence=text)


@case("compliance-c7-fail-in-progress")
def _compliance_c7_fail_in_progress():
    text = evidence(
        FIRST_CYCLE + [RED_2, checkpoint()],
        summary=summary(VERIFIED_1, "in progress | assert | fail (#4)", unverified((REQS_2, "VO-002 in progress"))),
    )
    return compliant(tasks=done(TASKS, "T011", "T012", "T013", "T015"), evidence=text)


DEFECT_2 = rec("T014", "VO-002", "green", "unit", "assert", "fail", "no", "defect", "tests/test_cart.py", FP_A)
FAILED_RUN = FIRST_CYCLE + [RED_2, DEFECT_2, checkpoint()]
BLOCKED_RUN = FIRST_CYCLE + [RED_2, ENV_FAIL_2, checkpoint()]
HELD_TASKS = done(TASKS, "T011", "T012", "T013", "T015")
CLAIMS_VERIFIED = summary(VERIFIED_1, VERIFIED_2)


@case("compliance-c7-pass-failed")
def _compliance_c7_pass_failed():
    # An obligation failed and the Summary reports it as failed: the process was followed.
    text = evidence(
        FAILED_RUN,
        summary=summary(VERIFIED_1, "failed | assert | fail (#5)", unverified((REQS_2, "VO-002 failed"))),
    )
    return compliant(tasks=HELD_TASKS, evidence=text)


@case("compliance-c7-fail-failed-not-reported")
def _compliance_c7_fail_failed_not_reported():
    return compliant(tasks=HELD_TASKS, evidence=evidence(FAILED_RUN, summary=CLAIMS_VERIFIED))


@case("compliance-c7-pass-blocked")
def _compliance_c7_pass_blocked():
    text = evidence(
        BLOCKED_RUN,
        summary=summary(VERIFIED_1, "blocked | assert, import | fail (#5)", unverified((REQS_2, "VO-002 blocked"))),
    )
    return compliant(tasks=HELD_TASKS, evidence=text)


@case("compliance-c7-fail-blocked-not-reported")
def _compliance_c7_fail_blocked_not_reported():
    return compliant(tasks=HELD_TASKS, evidence=evidence(BLOCKED_RUN, summary=CLAIMS_VERIFIED))


@case("compliance-c7-fail-stale-plan")
def _compliance_c7_fail_stale_plan():
    # An obligation was added to plan.md after the last record, so the stored Summary lacks it.
    plan = swap(
        PLAN,
        "\n### Verification exemptions",
        "| VO-003 | EC-02 | A very large cart is totalled | The total is returned | unit | discovered |\n"
        "\n### Verification exemptions",
    )
    tasks = EVERY_TASK + (
        "- [ ] T016 [US1] [VO-003] Write the failing test for a very large cart in tests/test_cart.py\n"
        "- [ ] T017 [US1] [VO-003] Make the very large cart total pass in src/cart.py\n"
    )
    return compliant(plan=plan, tasks=tasks)


# ---------------------------------------------------------------------------
# Evidence location cases (T006)
# ---------------------------------------------------------------------------


@case("evidence-top")
def _evidence_top():
    return variant()


@case("evidence-tests")
def _evidence_tests():
    files = variant()
    files["tests/tdd-evidence.md"] = files.pop("tdd-evidence.md")
    return files


@case("evidence-both")
def _evidence_both():
    files = variant()
    files["tests/tdd-evidence.md"] = files["tdd-evidence.md"]
    return files


# ---------------------------------------------------------------------------


def write_case(name, files):
    folder = os.path.join(FEATURES, name)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    for filename, text in sorted(files.items()):
        path = os.path.join(folder, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)


def main():
    for name in sorted(CASES):
        write_case(name, CASES[name]())
    print(f"wrote {len(CASES)} fixture features")


if __name__ == "__main__":
    main()
