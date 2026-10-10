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
        needs="no", approved="-"):  # fmt: skip
    return {
        "ID": ident, "Time": stamp(30), "Task": task, "Obligations": vos, "Kind": kind, "Rationale": rationale,
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

EXAMPLE_SUMMARY = """_Generated from the tables below on 2026-10-10T14:02:11Z._

| Obligation | Requirements | Status | Tests | Latest result |
|------------|--------------|--------|-------|---------------|
| VO-001 | FR-001, US1-AS1 | verified | assert, pass | pass (#3) |
| VO-002 | FR-002, US1-AS2, SC-001, DC-01, EC-01 | planned | - | - |

**Not verified**: FR-002 (VO-002 planned), US1-AS2 (VO-002 planned), FR-003 (exempt: see plan).

**Open decisions**: none. **Exceptions**: none. **Expectation changes**: none.

**Pre-existing failures**: none.
"""

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


def write_case(name, files):
    folder = os.path.join(FEATURES, name)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    for filename, text in sorted(files.items()):
        with open(os.path.join(folder, filename), "w", encoding="utf-8") as handle:
            handle.write(text)


def main():
    for name in sorted(CASES):
        write_case(name, CASES[name]())
    print(f"wrote {len(CASES)} fixture features")


if __name__ == "__main__":
    main()
