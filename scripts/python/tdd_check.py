#!/usr/bin/env python3
"""Deterministic checks for Integrated TDD.

One script, standard library only, Python 3.9 or later. It is run by the coding
agent on the instruction of the wrapped lifecycle commands, by the runtime event
dispatcher, and by a person evaluating the extension.

    python3 tdd_check.py <subcommand> [options]

Exit codes for every subcommand except ``hook``:

    0  the check passed, or the action was recorded and is valid
    1  the check failed, or the run was recorded and is not valid evidence
    2  usage error or undeclared input; nothing was recorded

``hook`` exits 0 to allow a tool call and 2 to refuse it.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

PLAN_FILE = "plan.md"
TASKS_FILE = "tasks.md"
EVIDENCE_FILE = "tdd-evidence.md"
GUARDED_FILES = (TASKS_FILE, EVIDENCE_FILE)

VERIFICATION_PLAN_HEADING = "## Verification Plan"

PHASES = ("baseline", "red", "green", "refactor", "checkpoint")
CLASSIFICATIONS = ("assertion", "defect", "environment", "unreliable")
EXCEPTION_KINDS = (
    "no-meaningful-red",
    "behaviour-preserving",
    "legacy",
    "external-system",
    "generated-code",
    "migration",
    "infrastructure",
    "exploratory",
    "environment-blocked",
    "other",
)

SCRIPT_INSTALL_PATH = ".specify/extensions/integrated-tdd/scripts/python/tdd_check.py"


class UsageError(Exception):
    """Wrong or undeclared input. Exit 2, nothing recorded."""


class Finding:
    """One failed rule: ``<rule id> <subject>: <reason>``."""

    def __init__(self, rule, subject, reason):
        self.rule = rule
        self.subject = subject
        self.reason = reason

    def __str__(self):
        return f"{self.rule} {self.subject}: {self.reason}"

    def as_dict(self):
        return {"rule": self.rule, "subject": self.subject, "reason": self.reason}


# ---------------------------------------------------------------------------
# Feature directory
# ---------------------------------------------------------------------------


def resolve_feature_dir(option, root):
    """Return the feature directory: option, then environment, then feature.json."""
    chosen = option or os.environ.get("SPECIFY_FEATURE_DIRECTORY")
    if not chosen:
        pointer = os.path.join(root, ".specify", "feature.json")
        if os.path.isfile(pointer):
            try:
                with open(pointer, encoding="utf-8") as handle:
                    chosen = json.load(handle).get("feature_directory")
            except (OSError, ValueError, AttributeError) as error:
                raise UsageError(f"cannot read .specify/feature.json: {error}") from error
    if not chosen:
        raise UsageError(
            "no feature directory: give --feature-dir, set SPECIFY_FEATURE_DIRECTORY, "
            "or set feature_directory in .specify/feature.json"
        )
    path = chosen if os.path.isabs(chosen) else os.path.join(root, chosen)
    if not os.path.isdir(path):
        raise UsageError(f"feature directory not found: {chosen}")
    return path


def has_verification_plan(feature_dir):
    """Whether the directory's plan.md holds the Verification Plan heading."""
    path = os.path.join(feature_dir, PLAN_FILE)
    if not os.path.isfile(path):
        return False
    with open(path, encoding="utf-8") as handle:
        return any(line.rstrip() == VERIFICATION_PLAN_HEADING for line in handle)


# ---------------------------------------------------------------------------
# Artefact parser (contracts/artefact-formats.md)
#
# Malformed input is reported as findings and never raises.
# ---------------------------------------------------------------------------

SCOPES = ("focused", "broad")
LEVELS = ("unit", "integration", "contract", "end-to-end", "other")
ORIGINS = ("planned", "discovered")
RESULTS = ("pass", "fail")

COMMANDS_HEADING = "### Verification commands"
OBLIGATIONS_HEADING = "### Verification obligations"
EXEMPTIONS_HEADING = "### Verification exemptions"
COMMANDS_HEADER = ["ID", "Command", "Scope", "Source"]
OBLIGATIONS_HEADER = ["ID", "Requirements", "Scenario", "Expected outcome", "Level", "Origin"]
EXEMPTIONS_HEADER = ["Requirement", "Reason", "Alternative verification"]

BASELINE_HEADING = "## Baseline"
RECORDS_HEADING = "## Test execution records"
EXCEPTIONS_HEADING = "## Exceptions"
EXPECTATIONS_HEADING = "## Expectation changes"
DECISIONS_HEADING = "## Decisions"
SUMMARY_HEADING = "## Summary"
BASELINE_HEADER = ["Seq", "Command", "Result", "Pre-existing failures"]
RECORDS_HEADER = [
    "Seq",
    "Time",
    "Task",
    "Obligations",
    "Phase",
    "Command",
    "Selector",
    "Result",
    "Valid",
    "Classification",
    "Files",
    "Fingerprint",
    "Note",
    "Check",
]
EXCEPTIONS_HEADER = [
    "ID",
    "Time",
    "Task",
    "Obligations",
    "Kind",
    "Rationale",
    "Alternative verification",
    "Needs approval",
    "Approved by",
]
EXPECTATIONS_HEADER = [
    "ID",
    "Time",
    "Task",
    "Files",
    "Requirements",
    "Justification",
    "Alters behaviour",
    "Approved by",
    "New fingerprint",
]
DECISIONS_HEADER = ["ID", "Opened", "Question", "Tasks", "Status", "Answer", "Decided by", "Resolved"]
# The record cells the check value is not computed over.
UNCHAINED_CELLS = ("Classification", "Note", "Check")

COMMAND_ID = re.compile(r"^[a-z0-9-]+$")
OBLIGATION_ID = re.compile(r"^VO-\d{3,}$")
TASK_LINE = re.compile(r"^\s*- \[([ xX])\] (T\d{3,})(?=\s|$)(.*)$")
LABEL = re.compile(r"\s*\[([^\]]*)\]")
FENCE = re.compile(r"^\s*(```+|~~~+)(.*)$")
STORY_HEADING = re.compile(r"^###\s+User Story\s+(\d+)\b")
SCENARIOS_MARKER = re.compile(r"^\*\*Acceptance Scenarios\*\*")
NUMBERED_ITEM = re.compile(r"^\d+\.\s")
DEFINED_ID = re.compile(r"\*\*((?:FR|SC)-\d+)\*\*")


class Item:
    """A parsed row: plain attributes, no behaviour."""

    def __init__(self, **fields):
        self.__dict__.update(fields)


def split_row(line):
    """Split one Markdown table row into trimmed cells.

    A vertical bar inside backticks, or escaped with a backslash, stays in its cell.
    """
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    cells = []
    current = []
    in_code = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and text[index + 1 : index + 2] == "|":
            current.append("|")
            index += 2
            continue
        if char == "`":
            in_code = not in_code
        if char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    if "".join(current).strip():
        cells.append("".join(current).strip())
    return cells


def split_list(cell):
    """Split a comma-separated cell. A lone ``-`` or an empty cell is no items."""
    text = cell.strip()
    if text in ("", "-"):
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def undash(cell):
    """A cell containing only ``-`` is empty."""
    text = cell.strip()
    return "" if text == "-" else text


def find_table(text, heading, header):
    """Find a table by its heading and then its header row.

    Returns ``(rows, None)`` with each row a list of cells, or ``(None, problem)``.
    """
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.rstrip() == heading:
            start = index + 1
            break
    if start is None:
        return None, f"no heading '{heading}'"
    while start < len(lines) and not lines[start].lstrip().startswith("|"):
        if lines[start].startswith("#"):
            return None, f"no table under '{heading}'"
        start += 1
    if start >= len(lines):
        return None, f"no table under '{heading}'"
    if split_row(lines[start]) != list(header):
        return None, f"header row under '{heading}' is not | " + " | ".join(header) + " |"
    rows = []
    for line in lines[start + 1 :]:
        if not line.lstrip().startswith("|"):
            break
        if re.match(r"^\s*\|[\s:|-]*$", line):
            continue
        rows.append(split_row(line))
    return rows, None


def read_table(text, heading, header, rule, subject, findings):
    """Read a table as a list of ``{column: cell}``, adding findings for what is malformed."""
    rows, problem = find_table(text, heading, header)
    if problem is not None:
        findings.append(Finding(rule, subject, problem))
        return []
    found = []
    for number, cells in enumerate(rows, 1):
        if len(cells) != len(header):
            findings.append(
                Finding(rule, subject, f"row {number} under '{heading}' has {len(cells)} cells, expected {len(header)}")
            )
            continue
        found.append(dict(zip(header, cells)))
    return found


def check_enum(value, allowed, name, rule, subject, findings):
    if value and value not in allowed:
        findings.append(Finding(rule, subject, f"{name} '{value}' is not one of " + ", ".join(allowed)))


def unique(values):
    seen = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


def parse_spec(text):
    """Collect requirement ids and derive acceptance scenario ids from spec.md."""
    fr_ids = []
    sc_ids = []
    scenario_ids = []
    story = None
    in_scenarios = False
    count = 0
    for line in text.splitlines():
        for ident in DEFINED_ID.findall(line):
            (fr_ids if ident.startswith("FR-") else sc_ids).append(ident)
        heading = STORY_HEADING.match(line)
        if heading:
            story = heading.group(1)
            in_scenarios = False
            count = 0
            continue
        if line.startswith("#"):
            story = None
            in_scenarios = False
            continue
        if story is None:
            continue
        stripped = line.strip()
        if SCENARIOS_MARKER.match(stripped):
            in_scenarios = True
            count = 0
        elif in_scenarios and NUMBERED_ITEM.match(stripped):
            count += 1
            scenario_ids.append(f"US{story}-AS{count}")
        elif in_scenarios and stripped and not line.startswith((" ", "\t")):
            in_scenarios = False
    return Item(fr_ids=unique(fr_ids), sc_ids=unique(sc_ids), scenario_ids=scenario_ids)


def verification_plan_section(text):
    """The text from the Verification Plan heading to the next heading of its level, or None."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.rstrip() == VERIFICATION_PLAN_HEADING:
            end = len(lines)
            for later in range(index + 1, len(lines)):
                if re.match(r"^#{1,2}\s", lines[later]):
                    end = later
                    break
            return "\n".join(lines[index:end])
    return None


def parse_plan(text):
    """Read the Verification Plan section of plan.md with the element rules of the contract."""
    findings = []
    plan = Item(has_section=False, commands=[], obligations=[], exemptions=[], findings=findings)
    section = verification_plan_section(text)
    if section is None:
        findings.append(
            Finding("PLAN", PLAN_FILE, "no Verification Plan section: a gap to resolve in planning, by the plan stage")
        )
        return plan
    plan.has_section = True

    seen = set()
    for row in read_table(section, COMMANDS_HEADING, COMMANDS_HEADER, "PLAN", PLAN_FILE, findings):
        ident = row["ID"]
        if not COMMAND_ID.match(ident):
            findings.append(Finding("PLAN", ident, "command id must be lowercase letters, digits and hyphens"))
        if ident in seen:
            findings.append(Finding("PLAN", ident, "command id is used more than once"))
        seen.add(ident)
        command = row["Command"]
        if len(command) >= 2 and command.startswith("`") and command.endswith("`"):
            command = command.strip("`").strip()
        else:
            findings.append(Finding("PLAN", ident, "command must be written in backticks"))
        if command.count("{select}") > 1:
            findings.append(Finding("PLAN", ident, "command holds more than one {select}"))
        check_enum(row["Scope"], SCOPES, "scope", "PLAN", ident, findings)
        plan.commands.append(Item(id=ident, command=command, scope=row["Scope"], source=undash(row["Source"])))

    seen = set()
    for row in read_table(section, OBLIGATIONS_HEADING, OBLIGATIONS_HEADER, "PLAN", PLAN_FILE, findings):
        ident = row["ID"]
        if not OBLIGATION_ID.match(ident):
            findings.append(Finding("PLAN", ident, "obligation id must be VO- and three or more digits"))
        if ident in seen:
            findings.append(Finding("PLAN", ident, "obligation id is used more than once"))
        seen.add(ident)
        check_enum(row["Level"], LEVELS, "level", "PLAN", ident, findings)
        check_enum(row["Origin"], ORIGINS, "origin", "PLAN", ident, findings)
        plan.obligations.append(
            Item(
                id=ident,
                requirements=split_list(row["Requirements"]),
                scenario=undash(row["Scenario"]),
                outcome=undash(row["Expected outcome"]),
                level=undash(row["Level"]),
                origin=undash(row["Origin"]),
            )
        )

    for row in read_table(section, EXEMPTIONS_HEADING, EXEMPTIONS_HEADER, "PLAN", PLAN_FILE, findings):
        if row["Requirement"].lower() == "none":
            continue
        plan.exemptions.append(
            Item(
                requirement=row["Requirement"],
                reason=undash(row["Reason"]),
                alternative=undash(row["Alternative verification"]),
            )
        )
    return plan


def parse_tasks(text):
    """Read task lines: id, checkbox, labels, and kind by the first-to-name rule."""
    tasks = []
    named = set()
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        # Task lines inside a fenced code block are examples, not tasks.
        marker = FENCE.match(line)
        if marker and fence is None:
            fence = marker.group(1)[0]
            continue
        if fence is not None:
            if marker and marker.group(1)[0] == fence and not marker.group(2).strip():
                fence = None
            continue
        found = TASK_LINE.match(line)
        if not found:
            continue
        rest = found.group(3)
        obligations = []
        reason = ""
        while True:
            label = LABEL.match(rest)
            if not label:
                break
            content = label.group(1).strip()
            if OBLIGATION_ID.match(content):
                obligations.append(content)
            elif content.startswith("NT:"):
                reason = content[3:].strip()
            elif not re.match(r"^(P|US\d+)$", content):
                break
            rest = rest[label.end() :]
        obligations = unique(obligations)
        if obligations:
            kind = "test" if not any(ident in named for ident in obligations) else "behaviour"
            named.update(obligations)
        elif reason:
            kind = "no-test"
        else:
            kind = None
        tasks.append(
            Item(
                id=found.group(2),
                complete=found.group(1) != " ",
                obligations=obligations,
                no_test_reason=reason,
                kind=kind,
                line=number,
                description=rest.strip(),
            )
        )
    return tasks


def yes_no(value, name, subject, findings):
    if value not in ("yes", "no"):
        findings.append(Finding("EVIDENCE", subject, f"{name} '{value}' is not one of yes, no"))
    return value == "yes"


def make_record(row, findings):
    """A Test Execution Record from its row of cells, or None when it has no sequence number."""
    if not row["Seq"].isdigit():
        findings.append(Finding("EVIDENCE", EVIDENCE_FILE, f"Seq '{row['Seq']}' is not a number"))
        return None
    subject = "#" + row["Seq"]
    check_enum(row["Phase"], PHASES, "phase", "EVIDENCE", subject, findings)
    check_enum(row["Result"], RESULTS, "result", "EVIDENCE", subject, findings)
    classification = undash(row["Classification"])
    check_enum(classification, CLASSIFICATIONS + ("unclassified",), "classification", "EVIDENCE", subject, findings)
    return Item(
        seq=int(row["Seq"]),
        time=row["Time"],
        task=undash(row["Task"]),
        obligations=split_list(row["Obligations"]),
        phase=row["Phase"],
        command=row["Command"],
        selector=undash(row["Selector"]),
        result=row["Result"],
        valid=yes_no(row["Valid"], "Valid", subject, findings),
        classification=classification,
        files=split_list(row["Files"]),
        fingerprint=undash(row["Fingerprint"]),
        note=undash(row["Note"]),
        check=row["Check"],
        cells=row,
    )


def parse_evidence(text):
    """Read every table of tdd-evidence.md."""
    findings = []
    evidence = Item(baseline=[], records=[], exceptions=[], expectations=[], decisions=[], findings=findings)

    for row in read_table(text, BASELINE_HEADING, BASELINE_HEADER, "EVIDENCE", EVIDENCE_FILE, findings):
        evidence.baseline.append(
            Item(
                seq=row["Seq"],
                command=row["Command"],
                result=row["Result"],
                failures=undash(row["Pre-existing failures"]),
                cells=row,
            )
        )

    for row in read_table(text, RECORDS_HEADING, RECORDS_HEADER, "EVIDENCE", EVIDENCE_FILE, findings):
        record = make_record(row, findings)
        if record is not None:
            evidence.records.append(record)

    for row in read_table(text, EXCEPTIONS_HEADING, EXCEPTIONS_HEADER, "EVIDENCE", EVIDENCE_FILE, findings):
        check_enum(row["Kind"], EXCEPTION_KINDS, "kind", "EVIDENCE", row["ID"], findings)
        evidence.exceptions.append(
            Item(
                id=row["ID"],
                time=row["Time"],
                task=undash(row["Task"]),
                obligations=split_list(row["Obligations"]),
                kind=row["Kind"],
                rationale=undash(row["Rationale"]),
                alternative=undash(row["Alternative verification"]),
                needs_approval=yes_no(row["Needs approval"], "Needs approval", row["ID"], findings),
                approved_by=undash(row["Approved by"]),
                cells=row,
            )
        )

    for row in read_table(text, EXPECTATIONS_HEADING, EXPECTATIONS_HEADER, "EVIDENCE", EVIDENCE_FILE, findings):
        evidence.expectations.append(
            Item(
                id=row["ID"],
                time=row["Time"],
                task=undash(row["Task"]),
                files=split_list(row["Files"]),
                requirements=split_list(row["Requirements"]),
                justification=undash(row["Justification"]),
                alters_behaviour=yes_no(row["Alters behaviour"], "Alters behaviour", row["ID"], findings),
                approved_by=undash(row["Approved by"]),
                new_fingerprint=undash(row["New fingerprint"]),
                cells=row,
            )
        )

    for row in read_table(text, DECISIONS_HEADING, DECISIONS_HEADER, "EVIDENCE", EVIDENCE_FILE, findings):
        check_enum(row["Status"], ("open", "resolved"), "status", "EVIDENCE", row["ID"], findings)
        evidence.decisions.append(
            Item(
                id=row["ID"],
                opened=row["Opened"],
                question=undash(row["Question"]),
                tasks=split_list(row["Tasks"]),
                status=row["Status"],
                answer=undash(row["Answer"]),
                decided_by=undash(row["Decided by"]),
                resolved=undash(row["Resolved"]),
                cells=row,
            )
        )
    return evidence


# ---------------------------------------------------------------------------
# Loading a feature's artefacts
# ---------------------------------------------------------------------------

SPEC_FILE = "spec.md"


def read_text(path):
    """The file's text, or None when it does not exist."""
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def require_text(feature_dir, name):
    try:
        text = read_text(os.path.join(feature_dir, name))
    except (OSError, UnicodeDecodeError) as error:
        raise UsageError(f"cannot read {name}: {error}") from error
    if text is None:
        raise UsageError(f"cannot read {name}: no such file in the feature directory")
    return text


def load_plan(feature_dir):
    """The parsed Verification Plan. A missing plan.md is a plan with no section."""
    try:
        text = read_text(os.path.join(feature_dir, PLAN_FILE))
    except (OSError, UnicodeDecodeError) as error:
        raise UsageError(f"cannot read {PLAN_FILE}: {error}") from error
    return parse_plan(text or "")


# ---------------------------------------------------------------------------
# Evidence ledger: the only code that writes, and it writes only tdd-evidence.md
# ---------------------------------------------------------------------------

TEMPLATE_NAME = "tdd-evidence-template.md"
TITLE_PLACEHOLDER = "<feature directory name>"
FALLBACK_PREAMBLE = (
    "# TDD Evidence: " + TITLE_PLACEHOLDER + "\n\n"
    "<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->\n\n"
)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean(text):
    """Supplied text as one table cell: a bar or a line break becomes a space."""
    if text is None:
        return "-"
    cell = " ".join(re.sub(r"[|\r\n]", " ", str(text)).split())
    return cell or "-"


def join_cell(values):
    return ", ".join(values) if values else "-"


def repo_relative(path, root):
    """A path as written in the Files cell: relative to the repository root, forward slashes."""
    absolute = path if os.path.isabs(path) else os.path.join(root, path)
    return os.path.relpath(absolute, root).replace(os.sep, "/")


def fingerprint(files, root):
    """Short hash over the paths and current contents of the files, in sorted path order.

    A file that no longer exists is hashed as missing, so deleting it changes the value.
    """
    if not files:
        return "-"
    digest = hashlib.sha256()
    for name in sorted(files):
        digest.update(name.encode("utf-8") + b"\0")
        path = os.path.join(root, name)
        if os.path.isfile(path):
            with open(path, "rb") as handle:
                digest.update(b"\1" + handle.read())
        else:
            digest.update(b"\0")
        digest.update(b"\0")
    return digest.hexdigest()[:6]


def check_value(previous, cells):
    """Short hash of a record row's cells, chained from the previous row's check value."""
    chained = [cells[name] for name in RECORDS_HEADER if name not in UNCHAINED_CELLS]
    return hashlib.sha256((previous + "\n" + "|".join(chained)).encode("utf-8")).hexdigest()[:6]


def empty_evidence():
    return Item(baseline=[], records=[], exceptions=[], expectations=[], decisions=[], findings=[], text=None)


def load_evidence(feature_dir):
    """The parsed evidence document. A feature with no document yet has empty evidence."""
    text = read_text(os.path.join(feature_dir, EVIDENCE_FILE))
    if text is None:
        return empty_evidence()
    evidence = parse_evidence(text)
    evidence.text = text
    return evidence


def open_ledger(feature_dir):
    """The evidence to append to. A malformed document is never written to."""
    try:
        evidence = load_evidence(feature_dir)
    except (OSError, UnicodeDecodeError) as error:
        raise UsageError(f"cannot read {EVIDENCE_FILE}: {error}") from error
    if evidence.findings:
        raise UsageError(f"{EVIDENCE_FILE} is malformed, nothing was recorded: {evidence.findings[0].reason}")
    return evidence


def preamble(feature_dir, evidence):
    """The title and comment above the Summary: kept from the document, or taken from the template."""
    if evidence.text is not None and SUMMARY_HEADING in evidence.text:
        return evidence.text.split(SUMMARY_HEADING, 1)[0]
    here = os.path.dirname(os.path.abspath(__file__))
    template = read_text(os.path.join(os.path.dirname(os.path.dirname(here)), "templates", TEMPLATE_NAME))
    text = template.split(SUMMARY_HEADING, 1)[0] if template and SUMMARY_HEADING in template else FALLBACK_PREAMBLE
    return text.replace(TITLE_PLACEHOLDER, os.path.basename(os.path.normpath(feature_dir)))


def render_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("-" * (len(name) + 2) for name in header) + "|"]
    lines.extend("| " + " | ".join(row[name] for name in header) + " |" for row in rows)
    return "\n".join(lines) + "\n"


def baseline_rows(evidence):
    """One Baseline row per baseline record, derived from the record table."""
    rows = []
    for record in evidence.records:
        if record.phase != "baseline":
            continue
        failures = "-"
        if record.result == "fail":
            failures = record.cells["Note"] if record.note else "failing before work began"
        rows.append(
            {
                "Seq": record.cells["Seq"],
                "Command": record.cells["Command"],
                "Result": record.cells["Result"],
                "Pre-existing failures": failures,
            }
        )
    return rows


def summary_body(feature_dir, evidence):
    """The Summary below its generated-on line. Derived only from plan.md and the tables."""
    return ""


def render_evidence(feature_dir, evidence, now):
    body = summary_body(feature_dir, evidence)
    summary = f"_Generated from the tables below on {now}._\n" + ("\n" + body if body else "")
    return (
        preamble(feature_dir, evidence)
        + SUMMARY_HEADING + "\n\n" + summary + "\n"
        + BASELINE_HEADING + "\n\n" + render_table(BASELINE_HEADER, baseline_rows(evidence)) + "\n"
        + RECORDS_HEADING + "\n\n" + render_table(RECORDS_HEADER, [item.cells for item in evidence.records]) + "\n"
        + EXCEPTIONS_HEADING + "\n\n"
        + render_table(EXCEPTIONS_HEADER, [item.cells for item in evidence.exceptions]) + "\n"
        + EXPECTATIONS_HEADING + "\n\n"
        + render_table(EXPECTATIONS_HEADER, [item.cells for item in evidence.expectations]) + "\n"
        + DECISIONS_HEADING + "\n\n" + render_table(DECISIONS_HEADER, [item.cells for item in evidence.decisions])
    )  # fmt: skip


def write_evidence(feature_dir, evidence):
    """Rewrite tdd-evidence.md whole, with a fresh Summary."""
    text = render_evidence(feature_dir, evidence, utc_now())
    path = os.path.join(feature_dir, EVIDENCE_FILE)
    partial = path + ".partial"
    with open(partial, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(partial, path)


def append_record(evidence, cells):
    """Add a record row with the next sequence number and its chained check value."""
    row = dict(cells)
    row["Seq"] = str(len(evidence.records) + 1)
    row["Time"] = utc_now()
    row["Check"] = check_value(evidence.records[-1].check if evidence.records else "", row)
    record = make_record(row, [])
    evidence.records.append(record)
    return record


# ---------------------------------------------------------------------------
# Command runner and the run subcommand
# ---------------------------------------------------------------------------

CYCLE_PHASES = ("red", "green", "refactor")
OUTPUT_TAIL = 40
SAFE_SELECTOR = re.compile(r"^[A-Za-z0-9_@%+=:,./-]+$")
KILL = 9


def shell_quote(text):
    """Quote a selector for the shell when it holds anything the shell would interpret."""
    if SAFE_SELECTOR.match(text):
        return text
    return "'" + text.replace("'", "'\"'\"'") + "'"


def execute(command_line, root, timeout):
    """Run a command line through the shell from the repository root.

    Returns ``(exit status, output, timed out)``. Standard error is folded into the output.
    """
    try:
        process = subprocess.Popen(
            command_line,
            shell=True,
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=os.name == "posix",
        )
    except OSError as error:
        return 1, f"could not start the command: {error}\n", False
    timed_out = False
    try:
        raw, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            # The whole process group, so that a test runner's children do not keep the pipe open.
            os.killpg(process.pid, KILL)
        except (AttributeError, OSError):
            process.kill()
        raw, _ = process.communicate()
    return process.returncode, raw.decode("utf-8", errors="replace"), timed_out


def find_task(tasks, ident):
    for task in tasks:
        if task.id == ident:
            return task
    raise UsageError(f"task {ident} is not in {TASKS_FILE}")


def require_plan(feature_dir):
    plan = load_plan(feature_dir)
    if not plan.has_section:
        raise UsageError(
            f"{PLAN_FILE} has no Verification Plan: the feature is not under the process, nothing was recorded"
        )
    return plan


def has_baseline(evidence):
    return any(record.phase == "baseline" for record in evidence.records)


def require_baseline(evidence):
    if not has_baseline(evidence):
        raise UsageError(
            "record a baseline with a broad command first (run --phase baseline --command <id>), "
            "so that failures from before this feature's work are known; nothing was recorded"
        )


def validate_run(args, plan, feature_dir):
    """Check the run options against the plan and the task list. Returns the declared command."""
    command = next((item for item in plan.commands if item.id == args.command), None)
    if command is None:
        raise UsageError(f"command '{args.command}' is not declared in the plan; nothing was recorded")
    takes_selector = "{select}" in command.command
    if args.select is not None and not takes_selector:
        raise UsageError(f"command '{command.id}' has no {{select}}; nothing was recorded")
    if args.select is None and takes_selector:
        raise UsageError(f"command '{command.id}' needs --select; nothing was recorded")
    phase = args.phase
    if phase in CYCLE_PHASES:
        if not args.task:
            raise UsageError(f"--task is required for {phase}")
        if not args.vo:
            raise UsageError(f"--vo is required for {phase}")
        if phase == "red" and not args.tests:
            raise UsageError("--tests is required for red")
        if phase == "red" and not args.expect:
            raise UsageError("--expect is required for red")
        task = find_task(parse_tasks(require_text(feature_dir, TASKS_FILE)), args.task)
        for ident in args.vo:
            if ident not in task.obligations:
                raise UsageError(f"obligation {ident} is not on task {task.id}")
    elif args.task or args.vo:
        raise UsageError(f"--task and --vo do not apply to {phase}")
    return command


def judge(phase, command, status, output, timed_out, expect):
    """Result, validity, classification and the script's note for a run, by the phase table."""
    passed = status == 0 and not timed_out
    result = "pass" if passed else "fail"
    classification = "-" if passed else "unclassified"
    note = "timed out" if timed_out else ""
    if phase == "baseline":
        valid = True
    elif phase == "red":
        valid = not passed and not timed_out and expect in output
        if valid:
            classification = "assertion"
            note = "expected: " + expect
        elif passed:
            note = "passed on first run: investigate"
        elif not timed_out:
            note = "failed for a different reason"
    elif phase == "checkpoint":
        valid = passed and command.scope == "broad"
        if command.scope != "broad":
            note = "command scope is not broad"
    else:
        valid = passed
    return result, valid, classification, note


def run_files(args, root, evidence):
    """The test files a run is fingerprinted over."""
    return sorted(unique(repo_relative(path, root) for path in args.tests or []))


def cmd_run(args, root, feature_dir):
    plan = require_plan(feature_dir)
    command = validate_run(args, plan, feature_dir)
    evidence = open_ledger(feature_dir)
    if args.phase != "baseline":
        require_baseline(evidence)
    files = run_files(args, root, evidence)

    line = command.command
    if args.select is not None:
        line = line.replace("{select}", shell_quote(args.select))
    status, output, timed_out = execute(line, root, args.timeout)
    result, valid, classification, note = judge(args.phase, command, status, output, timed_out, args.expect or "")
    # Hashed after the run, so the fingerprint is of the files as the run saw them.
    supplied = clean(args.note)
    if supplied != "-":
        note = f"{note}; {supplied}" if note else supplied
    record = append_record(
        evidence,
        {
            "Task": clean(args.task),
            "Obligations": join_cell(args.vo),
            "Phase": args.phase,
            "Command": command.id,
            "Selector": clean(args.select),
            "Result": result,
            "Valid": "yes" if valid else "no",
            "Classification": classification,
            "Files": join_cell(files),
            "Fingerprint": fingerprint(files, root),
            "Note": clean(note),
        },
    )
    write_evidence(feature_dir, evidence)

    tail = output.splitlines()[-OUTPUT_TAIL:]
    state = "valid" if valid else f"not valid for {args.phase}"
    lines = list(tail)
    if not valid and note:
        lines.append(f"not valid: {note}")
    lines.append(f"recorded #{record.seq}: {args.phase} {command.id}: {result}, {state}")
    extra = {
        "seq": record.seq,
        "phase": args.phase,
        "result": result,
        "valid": valid,
        "classification": record.classification,
        "note": record.note,
        "output_tail": tail,
    }
    return (EXIT_OK if valid else EXIT_FAIL), [], lines, extra


# ---------------------------------------------------------------------------
# Trace checks: plan (C1) and tasks (G1, C2, C3)
# ---------------------------------------------------------------------------

SCENARIO_ID = re.compile(r"^US\d+-AS\d+$")
LOOKED_UP_ID = re.compile(r"^(FR|SC)-\d+$")
ASSIGNED_ID = re.compile(r"^(DC|EC)-\w+$")


def requirement_problem(ident, spec):
    """Why a requirement id is not acceptable, or None."""
    if LOOKED_UP_ID.match(ident):
        known = spec.fr_ids if ident.startswith("FR-") else spec.sc_ids
        return None if ident in known else "is not in spec.md"
    if SCENARIO_ID.match(ident):
        return None if ident in spec.scenario_ids else "is not in spec.md"
    if ASSIGNED_ID.match(ident):
        return None
    return "has an unknown prefix (expected FR-, SC-, USn-ASm, DC- or EC-)"


def check_plan(spec, plan):
    """Findings for the Verification Plan against spec.md."""
    if not plan.has_section:
        return list(plan.findings)
    findings = list(plan.findings)
    if not plan.commands and not any(COMMANDS_HEADING in finding.reason for finding in findings):
        findings.append(
            Finding("PLAN", PLAN_FILE, "no verification command is declared: a gap to resolve in planning")
        )
    for obligation in plan.obligations:
        if not obligation.requirements:
            findings.append(Finding("PLAN", obligation.id, "names no requirement"))
        for name, value in (
            ("scenario", obligation.scenario),
            ("expected outcome", obligation.outcome),
            ("level", obligation.level),
        ):
            if not value:
                findings.append(Finding("PLAN", obligation.id, f"{name} is empty"))
        for ident in obligation.requirements:
            problem = requirement_problem(ident, spec)
            if problem:
                findings.append(Finding("PLAN", obligation.id, f"requirement {ident} {problem}"))
    for exemption in plan.exemptions:
        if not exemption.reason:
            findings.append(Finding("PLAN", exemption.requirement, "exemption reason is empty"))
        problem = requirement_problem(exemption.requirement, spec)
        if problem:
            findings.append(Finding("PLAN", exemption.requirement, f"exempted requirement {problem}"))
    findings.extend(rule_c1(spec, plan))
    return findings


def rule_c1(spec, plan):
    """Every FR- requirement and every acceptance scenario has an obligation or an exemption."""
    covered = {exemption.requirement for exemption in plan.exemptions}
    for obligation in plan.obligations:
        covered.update(obligation.requirements)
    return [
        Finding("C1", ident, "no obligation and no exemption")
        for ident in spec.fr_ids + spec.scenario_ids
        if ident not in covered
    ]


def rule_g1(task):
    """The task carries a [VO-nnn] or [NT: reason] label."""
    if task.kind is None:
        return [Finding("G1", task.id, "no [VO-nnn] or [NT: reason] label")]
    return []


def duplicate_task_ids(tasks):
    seen = set()
    repeated = []
    for task in tasks:
        if task.id in seen and task.id not in repeated:
            repeated.append(task.id)
        seen.add(task.id)
    return [Finding("TASKS", ident, "task id is used more than once") for ident in repeated]


def unknown_obligations(plan, tasks):
    known = {obligation.id for obligation in plan.obligations}
    return [
        Finding("TASKS", task.id, f"obligation {ident} is not in the plan")
        for task in tasks
        for ident in task.obligations
        if ident not in known
    ]


def rule_c2_c3(plan, tasks):
    """Each obligation has a test task and a behaviour task (C2), the test task first (C3)."""
    findings = []
    for obligation in plan.obligations:
        namers = [task for task in tasks if obligation.id in task.obligations]
        if not namers:
            findings.append(Finding("C2", obligation.id, "no task names it"))
        elif namers[0].kind != "test":
            findings.append(
                Finding(
                    "C3",
                    obligation.id,
                    f"its first task {namers[0].id} is a behaviour task, so no test task comes before it",
                )
            )
        elif len(namers) == 1:
            findings.append(
                Finding("C2", obligation.id, f"named by a test task ({namers[0].id}) but by no behaviour task")
            )
    return findings


def check_tasks(plan, tasks):
    """Findings for tasks.md against the Verification Plan."""
    if not plan.has_section:
        return list(plan.findings)
    findings = []
    for task in tasks:
        findings.extend(rule_g1(task))
    findings.extend(duplicate_task_ids(tasks))
    findings.extend(unknown_obligations(plan, tasks))
    findings.extend(rule_c2_c3(plan, tasks))
    return findings


def verdict(name, findings):
    """Exit code and heading line for a check."""
    if not findings:
        return EXIT_OK, [f"{name}: passed"]
    noun = "finding" if len(findings) == 1 else "findings"
    return EXIT_FAIL, [f"{name}: failed, {len(findings)} {noun}"]


def cmd_plan(args, root, feature_dir):
    spec = parse_spec(require_text(feature_dir, SPEC_FILE))
    findings = check_plan(spec, load_plan(feature_dir))
    code, lines = verdict("plan", findings)
    return code, findings, lines, None


def cmd_tasks(args, root, feature_dir):
    tasks = parse_tasks(require_text(feature_dir, TASKS_FILE))
    findings = check_tasks(load_plan(feature_dir), tasks)
    code, lines = verdict("tasks", findings)
    return code, findings, lines, None


# ---------------------------------------------------------------------------
# The task gate (data-model.md). One function per rule, each taking the task
# and the parsed artefacts, so that a rule can be added without changing others.
# ---------------------------------------------------------------------------


def load_feature(feature_dir, tasks=None):
    """The plan, the task list and the evidence of a feature, parsed."""
    try:
        plan = load_plan(feature_dir)
        if tasks is None:
            tasks = parse_tasks(require_text(feature_dir, TASKS_FILE))
        evidence = load_evidence(feature_dir)
    except (OSError, UnicodeDecodeError) as error:
        raise UsageError(f"cannot read the feature's artefacts: {error}") from error
    return Item(dir=feature_dir, plan=plan, tasks=tasks, evidence=evidence)


def unreadable(feature):
    """Findings that stop the gate before any rule is applied: no plan section, malformed evidence."""
    if not feature.plan.has_section:
        return list(feature.plan.findings)
    return list(feature.evidence.findings)


def counts(record):
    """Whether a record counts as evidence for its phase. An unreliable record never does."""
    return record.valid and record.classification != "unreliable"


def records_of(feature, obligation, phase=None):
    return [
        record
        for record in feature.evidence.records
        if obligation in record.obligations and (phase is None or record.phase == phase)
    ]


def latest_red(feature, obligation):
    """The latest valid failing-first record of an obligation, whichever task it was made on."""
    found = [record for record in records_of(feature, obligation, "red") if counts(record)]
    return found[-1] if found else None


def gate_g1(task, feature):
    return rule_g1(task)


def gate_g3(task, feature):
    """Each obligation on a test or behaviour task has a valid failing-first record."""
    return [
        Finding("G3", f"{task.id} {obligation}", "no valid failing-first record and no exception")
        for obligation in task.obligations
        if latest_red(feature, obligation) is None
    ]


def gate_g4(task, feature):
    """Each obligation on a behaviour task has a valid passing record after its failing-first record."""
    if task.kind != "behaviour":
        return []
    findings = []
    for obligation in task.obligations:
        red = latest_red(feature, obligation)
        after = red.seq if red else 0
        greens = [
            record for record in records_of(feature, obligation, "green") if counts(record) and record.seq > after
        ]
        if not greens:
            findings.append(
                Finding("G4", f"{task.id} {obligation}", "no valid passing record after its failing-first record")
            )
    return findings


def gate_g9(task, feature):
    """Every record for the task used a declared Verification Command."""
    declared = {command.id for command in feature.plan.commands}
    return [
        Finding("G9", f"{task.id} #{record.seq}", f"command '{record.command}' is not declared in the plan")
        for record in feature.evidence.records
        if record.task == task.id and record.command not in declared
    ]


# In rule order. Later rules are added here.
GATE_RULES = [gate_g1, gate_g3, gate_g4, gate_g9]


def gate_task(task, feature):
    """Findings of every gate rule for one task."""
    findings = []
    for rule in GATE_RULES:
        findings.extend(rule(task, feature))
    return findings


def plural(count, noun):
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def cmd_gate(args, root, feature_dir):
    feature = load_feature(feature_dir)
    blocked = unreadable(feature)
    if args.task:
        task = find_task(feature.tasks, args.task)
        findings = blocked or gate_task(task, feature)
        code, lines = verdict(f"gate {task.id}", findings)
        return code, findings, lines, None
    if blocked:
        code, lines = verdict("gate", blocked)
        return code, blocked, lines, None

    completed = [task for task in feature.tasks if task.complete]
    findings = []
    for task in completed:
        findings.extend(gate_task(task, feature))
    code, lines = verdict("gate", findings)
    if code == EXIT_OK:
        lines = ["gate: passed, " + plural(len(completed), "completed task")]
    # Incomplete tasks are reported, and never fail the gate.
    incomplete = []
    for task in feature.tasks:
        if task.complete:
            continue
        would = gate_task(task, feature)
        incomplete.append(
            {"task": task.id, "would_pass": not would, "findings": [finding.as_dict() for finding in would]}
        )
        if not would:
            lines.append(f"{task.id} would pass")
        else:
            lines.append(f"{task.id} would not pass: " + "; ".join(str(finding) for finding in would))
    if incomplete:
        lines.insert(1, "Incomplete tasks:")
    return code, findings, lines, {"incomplete": incomplete}


# ---------------------------------------------------------------------------
# hook: the runtime event handler
# ---------------------------------------------------------------------------


class ToolCall:
    """What an agent is about to do to one file, in agent-neutral terms.

    ``result`` takes the file's current content (None when it does not exist) and
    returns the content the tool call would leave. It raises ValueError when the
    payload does not say.
    """

    def __init__(self, file_path, result):
        self.file_path = file_path
        self.result = result


def _apply_edit(text, edit):
    old = edit.get("old_string")
    new = edit.get("new_string")
    if not isinstance(old, str) or not isinstance(new, str):
        raise ValueError("an edit has no old_string or new_string")
    if old == "":
        return text or new
    if old not in text:
        # The tool will report this itself; nothing changes.
        return text
    return text.replace(old, new) if edit.get("replace_all") else text.replace(old, new, 1)


def _adapt_edit_tool_payload(payload):
    """Read a pre-tool-use payload carrying ``tool_name`` and ``tool_input``."""
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        raise ValueError("payload has no tool_input")
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        raise ValueError("payload has no tool_input.file_path")

    def result(current):
        text = current or ""
        if tool == "Write":
            content = tool_input.get("content")
            if not isinstance(content, str):
                raise ValueError("payload has no tool_input.content")
            return content
        if tool == "Edit":
            return _apply_edit(text, tool_input)
        if tool == "MultiEdit":
            edits = tool_input.get("edits")
            if not isinstance(edits, list) or not all(isinstance(edit, dict) for edit in edits):
                raise ValueError("payload has no tool_input.edits")
            for edit in edits:
                text = _apply_edit(text, edit)
            return text
        raise ValueError(f"unknown tool '{tool}'")

    return ToolCall(file_path, result)


# The only agent-specific code in the script: one payload adapter per agent,
# selected by --agent. The first entry is the default.
PAYLOAD_ADAPTERS = {
    "claude": _adapt_edit_tool_payload,
}

DEFAULT_AGENT = next(iter(PAYLOAD_ADAPTERS))

EVIDENCE_REFUSAL = (
    "Evidence is written only by the check script. Do not edit tdd-evidence.md.\n"
    "Record a test run, a classification, an exception, an expectation change or a\n"
    "decision with its subcommands, for example:\n"
    f"  python3 {SCRIPT_INSTALL_PATH} run --phase <phase> --command <id> ...\n"
)
PAYLOAD_REFUSAL = "Integrated TDD: cannot read the tool call payload"


def refuse(message):
    sys.stderr.write(message if message.endswith("\n") else message + "\n")
    return EXIT_USAGE


def completion_refusal(failing, findings):
    """What the agent is told when a task it is marking complete fails its gate."""
    first = failing[0]
    return (
        f"Integrated TDD: {', '.join(failing)} cannot be marked complete. tasks.md was not changed.\n"
        + "".join(str(finding) + "\n" for finding in findings)
        + "Two ways forward:\n"
        "  1. Meet the rule. Record the missing evidence from a real test run, then mark the task complete:\n"
        f"       python3 {SCRIPT_INSTALL_PATH} run --phase <red|green|refactor> --command <id> "
        f"--task {first} --vo <obligation> ...\n"
        "  2. Record an exception with a rationale, where the cycle does not fit this work:\n"
        f"       python3 {SCRIPT_INSTALL_PATH} exception --task {first} --kind <kind> "
        '--rationale "<why>" --alternative "<how it is verified instead>"\n'
        f"Check a task before marking it: python3 {SCRIPT_INSTALL_PATH} gate --task {first}\n"
    )


def newly_completed(before, after):
    """Tasks complete in the resulting content that were not complete before, absent ones included."""
    already = {task.id for task in before if task.complete}
    found = []
    for task in after:
        if task.complete and task.id not in already and task.id not in [item.id for item in found]:
            found.append(task)
    return found


def cmd_hook(args, root):
    """Decide whether a tool call may proceed. Exit 0 allows, exit 2 refuses."""
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("payload is not a JSON object")
        call = PAYLOAD_ADAPTERS[args.agent](payload)
    except ValueError as error:
        # The stop fails closed for the guarded files only: an unreadable
        # payload is refused when it mentions one of them.
        if any(name in raw for name in GUARDED_FILES):
            return refuse(f"{PAYLOAD_REFUSAL}: {error}")
        return EXIT_OK

    # Decided from the path alone, before any file is read.
    name = os.path.basename(call.file_path)
    if name not in GUARDED_FILES:
        return EXIT_OK

    path = call.file_path if os.path.isabs(call.file_path) else os.path.join(root, call.file_path)
    # The guard follows the file: its own directory is the feature directory.
    feature_dir = os.path.dirname(path)
    try:
        if not has_verification_plan(feature_dir):
            return EXIT_OK
    except (OSError, UnicodeDecodeError) as error:
        return refuse(f"Integrated TDD: cannot read {PLAN_FILE}: {error}")

    if name == EVIDENCE_FILE:
        return refuse(EVIDENCE_REFUSAL)

    try:
        current = read_text(path)
        resulting = call.result(current)
    except ValueError as error:
        return refuse(f"{PAYLOAD_REFUSAL}: {error}")
    except (OSError, UnicodeDecodeError) as error:
        return refuse(f"Integrated TDD: cannot read {TASKS_FILE}: {error}")

    after = parse_tasks(resulting)
    completing = newly_completed(parse_tasks(current or ""), after)
    if not completing:
        return EXIT_OK

    try:
        feature = load_feature(feature_dir, tasks=after)
    except UsageError as error:
        return refuse(f"Integrated TDD: {error}")
    blocked = unreadable(feature)
    if blocked:
        return refuse(
            "Integrated TDD: the feature's artefacts cannot be read, so no task can be marked complete.\n"
            + "".join(str(finding) + "\n" for finding in blocked)
        )
    failing = []
    findings = []
    for task in completing:
        found = gate_task(task, feature)
        if found:
            failing.append(task.id)
            findings.extend(found)
    if failing:
        return refuse(completion_refusal(failing, findings))
    return EXIT_OK


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def build_parser():
    parser = argparse.ArgumentParser(
        prog="tdd_check.py",
        description="Deterministic checks, test run recording, task gate and compliance check.",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--feature-dir", help="feature directory (default: the active feature)")
    common.add_argument("--json", action="store_true", help="print one JSON object")

    subs = parser.add_subparsers(dest="subcommand", metavar="<subcommand>")
    subs.required = True

    subs.add_parser("plan", parents=[common], help="check the Verification Plan against spec.md")
    subs.add_parser("tasks", parents=[common], help="check tasks.md against the Verification Plan")

    gate = subs.add_parser("gate", parents=[common], help="apply rules G1 to G9")
    which = gate.add_mutually_exclusive_group(required=True)
    which.add_argument("--task", help="the task about to be marked complete")
    which.add_argument("--all", action="store_true", help="every task marked complete")

    subs.add_parser("status", parents=[common], help="print the Review Evidence view")
    subs.add_parser("compliance", parents=[common], help="apply rules C1 to C7 to a finished feature")

    run = subs.add_parser("run", parents=[common], help="run a declared command and record the outcome")
    run.add_argument("--phase", required=True, choices=PHASES)
    run.add_argument("--command", required=True, help="an id in the Verification commands table")
    run.add_argument("--select", help="replaces {select} in the command line")
    run.add_argument("--task", help="the task being worked on")
    run.add_argument("--vo", nargs="+", default=[], metavar="VO", help="obligations the run concerns")
    run.add_argument("--tests", nargs="+", default=None, metavar="FILE", help="test files to fingerprint")
    run.add_argument("--expect", help="text the failing output must contain")
    run.add_argument("--note", help="one line stored with the record")
    run.add_argument("--timeout", type=float, default=600.0, help="seconds (default 600)")

    classify = subs.add_parser("classify", parents=[common], help="classify a failure record")
    classify.add_argument("--seq", required=True, type=int)
    classify.add_argument("--as", required=True, choices=CLASSIFICATIONS, dest="classification")
    classify.add_argument("--note")

    exception = subs.add_parser("exception", parents=[common], help="record a TDD Exception")
    exception.add_argument("--task", required=True)
    exception.add_argument("--vo", nargs="+", default=[], metavar="VO")
    exception.add_argument("--kind", required=True, choices=EXCEPTION_KINDS)
    exception.add_argument("--rationale", required=True)
    exception.add_argument("--alternative")
    exception.add_argument("--needs-approval", action="store_true")
    exception.add_argument("--approved-by")

    expectation = subs.add_parser("expectation", parents=[common], help="record an Expectation Change")
    expectation.add_argument("--task", required=True)
    expectation.add_argument("--tests", required=True, nargs="+", metavar="FILE")
    expectation.add_argument("--requirement", required=True, nargs="+", metavar="ID")
    expectation.add_argument("--justification", required=True)
    expectation.add_argument("--alters-behaviour", action="store_true")
    expectation.add_argument("--approved-by")

    decision = subs.add_parser("decision", help="open or resolve a Decision")
    actions = decision.add_subparsers(dest="action", metavar="<open|resolve>")
    actions.required = True
    opened = actions.add_parser("open", parents=[common])
    opened.add_argument("--question", required=True)
    opened.add_argument("--tasks", required=True, nargs="+", metavar="TASK")
    resolved = actions.add_parser("resolve", parents=[common])
    resolved.add_argument("--id", required=True)
    resolved.add_argument("--answer", required=True)
    resolved.add_argument("--by", required=True)

    approve = subs.add_parser("approve", parents=[common], help="record a person's approval")
    approve.add_argument("--id", required=True)
    approve.add_argument("--by", required=True)

    hook = subs.add_parser("hook", help="runtime event handler: reads a tool call on standard input")
    hook.add_argument("--agent", choices=sorted(PAYLOAD_ADAPTERS), default=DEFAULT_AGENT)
    return parser


# Subcommand handlers take (args, root, feature_dir) and return
# (exit code, findings, lines of text, extra fields for --json).
HANDLERS = {
    "plan": cmd_plan,
    "tasks": cmd_tasks,
    "run": cmd_run,
    "gate": cmd_gate,
}


def emit(args, code, findings=(), lines=(), extra=None, error=None):
    """Print the outcome as text, or as one JSON object with --json."""
    if getattr(args, "json", False):
        data = {
            "subcommand": args.subcommand,
            "exit_code": code,
            "findings": [finding.as_dict() for finding in findings],
        }
        if error is not None:
            data["error"] = error
        if extra:
            data.update(extra)
        sys.stdout.write(json.dumps(data, sort_keys=True) + "\n")
    else:
        lines = list(lines)
        if findings:
            # The heading line, then the findings, then anything the subcommand adds.
            lines = lines[:1] + [str(finding) for finding in findings] + lines[1:]
        for line in lines:
            sys.stdout.write(line + "\n")
    if error is not None:
        sys.stderr.write(f"tdd_check.py {args.subcommand}: {error}\n")
    return code


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = os.getcwd()
    if args.subcommand == "hook":
        return cmd_hook(args, root)
    try:
        feature_dir = resolve_feature_dir(args.feature_dir, root)
        handler = HANDLERS.get(args.subcommand)
        if handler is None:
            raise UsageError(f"subcommand not implemented: {args.subcommand}")
        code, findings, lines, extra = handler(args, root, feature_dir)
    except UsageError as error:
        return emit(args, EXIT_USAGE, error=str(error))
    return emit(args, code, findings, lines, extra)


if __name__ == "__main__":
    sys.exit(main())
