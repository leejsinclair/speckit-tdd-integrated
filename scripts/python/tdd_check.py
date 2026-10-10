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
