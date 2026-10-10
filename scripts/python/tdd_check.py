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
import json
import os
import re
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
    for number, line in enumerate(text.splitlines(), 1):
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
            )
        )

    for row in read_table(text, RECORDS_HEADING, RECORDS_HEADER, "EVIDENCE", EVIDENCE_FILE, findings):
        if not row["Seq"].isdigit():
            findings.append(Finding("EVIDENCE", EVIDENCE_FILE, f"Seq '{row['Seq']}' is not a number"))
            continue
        subject = "#" + row["Seq"]
        check_enum(row["Phase"], PHASES, "phase", "EVIDENCE", subject, findings)
        check_enum(row["Result"], RESULTS, "result", "EVIDENCE", subject, findings)
        classification = undash(row["Classification"])
        check_enum(classification, CLASSIFICATIONS + ("unclassified",), "classification", "EVIDENCE", subject, findings)
        evidence.records.append(
            Item(
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
        )

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
            )
        )
    return evidence


# ---------------------------------------------------------------------------
# hook: the runtime event handler
# ---------------------------------------------------------------------------


class ToolCall:
    """What an agent is about to do to one file, in agent-neutral terms."""

    def __init__(self, tool, file_path, tool_input):
        self.tool = tool
        self.file_path = file_path
        self.tool_input = tool_input


def _adapt_edit_tool_payload(payload):
    """Read a pre-tool-use payload carrying ``tool_name`` and ``tool_input``."""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        raise ValueError("payload has no tool_input")
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        raise ValueError("payload has no tool_input.file_path")
    return ToolCall(payload.get("tool_name"), file_path, tool_input)


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


def refuse(message):
    sys.stderr.write(message if message.endswith("\n") else message + "\n")
    return EXIT_USAGE


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
            return refuse(f"Integrated TDD: cannot read the tool call payload: {error}")
        return EXIT_OK

    name = os.path.basename(call.file_path)
    if name not in GUARDED_FILES:
        return EXIT_OK

    path = call.file_path if os.path.isabs(call.file_path) else os.path.join(root, call.file_path)
    feature_dir = os.path.dirname(path)
    try:
        if not has_verification_plan(feature_dir):
            return EXIT_OK
    except (OSError, UnicodeDecodeError) as error:
        return refuse(f"Integrated TDD: cannot read {PLAN_FILE}: {error}")

    if name == EVIDENCE_FILE:
        return refuse(EVIDENCE_REFUSAL)
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
HANDLERS = {}


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
        for line in lines:
            sys.stdout.write(line + "\n")
        for finding in findings:
            sys.stdout.write(str(finding) + "\n")
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
