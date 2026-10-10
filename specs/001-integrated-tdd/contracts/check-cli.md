# Contract: the check script

**Feature**: `001-integrated-tdd` | **Data model**: [data-model.md](../data-model.md)

The deterministic checks are one script, installed at
`.specify/extensions/integrated-tdd/scripts/python/tdd_check.py`. It uses only the Python
standard library and runs on Python 3.9 or later. It is run by the coding agent on the
instruction of the wrapped lifecycle commands, by the runtime event dispatcher, and by a
person evaluating the extension. A developer never needs to run it during normal work.

```text
python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py <subcommand> [options]
```

## Common behaviour

| Aspect | Contract |
|--------|----------|
| Working directory | The repository root |
| Feature directory | `--feature-dir <path>` when given; otherwise `SPECIFY_FEATURE_DIRECTORY`; otherwise `feature_directory` in `.specify/feature.json`. `hook` uses none of these: its feature directory is the directory of the file being edited |
| Output | Human-readable text on standard output. `--json` gives one JSON object instead |
| Repeatability | The checking subcommands (`plan`, `tasks`, `gate`, `status`, `compliance`) give the same output and exit code each time they are run on the same files (FR-059, SC-011) |
| Writes | Only `tdd-evidence.md` in the feature directory, and only by the subcommands marked "writes" |
| Network | None |

Exit codes for every subcommand except `hook`:

| Code | Meaning |
|------|---------|
| 0 | The check passed, or the action was recorded and is valid |
| 1 | The check failed, or the run was recorded and is not valid evidence for its phase |
| 2 | Usage error or undeclared input. Nothing was recorded |

A failed check lists each finding as `<rule id> <subject>: <reason>`, for example
`G3 T012 VO-004: no valid failing-first record and no exception`.

## Checking subcommands

### `plan`

Checks the Verification Plan in `plan.md` against `spec.md`.

- Fails when the section or its Verification commands table is missing or empty, naming
  this as a gap to resolve in planning.
- Fails for each `FR-` requirement and each acceptance scenario (`USn-ASm`) that has
  neither an obligation nor an exemption (C1).
- Fails for an obligation with an empty scenario, expected outcome or level, or an
  exemption with an empty reason.
- Fails for an obligation or exemption that names an `FR-`, `SC-` or `USn-ASm` id not
  found in `spec.md`, or an id with any prefix other than those and `DC-` and `EC-`.
  `DC-` (design constraint) and `EC-` (edge case) ids are labels the agent assigns in the
  plan; they are accepted and not looked up.

### `tasks`

Checks `tasks.md` against the Verification Plan.

- Fails for each task with neither a `[VO-nnn]` nor a `[NT: reason]` label (G1).
- Fails for a label naming an obligation that is not in the plan.
- Fails for each obligation that is not named by a `test` task and by at least one
  `behaviour` task (C2).
- Fails for each obligation whose first `behaviour` task comes before a `test` task (C3).

### `gate`

```text
gate --task <task id>
gate --all
```

Applies rules G1 to G9 from the data model to one task, or to every task marked complete.
`--all` also reports, without failing, each incomplete task and why it would not pass.

### `status`

Prints the Review Evidence view: each obligation with its requirements, derived status,
executable tests and latest result, followed by unverified requirements with reasons,
exemptions, exceptions, expectation changes, open decisions and pre-existing failures.
Always exits 0 when the artefacts can be read.

### `compliance`

```text
compliance [--feature-dir <path>]
```

Applies rules C1 to C7 to a finished feature and prints `COMPLIANT` or `NON-COMPLIANT`
followed by the findings. Exit 0 for compliant, 1 for non-compliant. It is the evaluation
aid required by FR-064 and is not run by any lifecycle command.

## Recording subcommands (write)

Each of these appends to `tdd-evidence.md`, creating it from the extension's
`tdd-evidence-template` on first use, and regenerates its Summary section.

### `run`

Executes a declared verification command and records the outcome.

```text
run --phase <baseline|red|green|refactor|checkpoint>
    --command <command id>
    [--select <selector>]
    [--task <task id>] [--vo <obligation id> ...]
    [--tests <test file> ...]
    [--expect <text>]
    [--note <text>]
    [--timeout <seconds>]
```

| Option | Contract |
|--------|----------|
| `--command` | Must be an id in the plan's Verification commands table. Otherwise exit 2 |
| `--select` | Replaces `{select}` in the command line. Exit 2 when the command has no `{select}` |
| `--task`, `--vo` | Required for `red`, `green` and `refactor`. The obligations must be on the task |
| `--tests` | Required for `red`. The files are written to the record's Files cell and fingerprinted. For `green` and `refactor`, when omitted, the files are read from the Files cell of the latest valid `red` record of each obligation named with `--vo`, whichever task that record was made on, and hashed again as they now are. Exit 2 when the obligations named have `red` records that list different files: run them separately. When no obligation named has a valid `red` record, as for work under an exception, no files are fingerprinted |
| `--expect` | Required for `red`. Text that must appear in the run's output for the failure to count as the intended one |
| `--note` | One line stored with the record. For a failing `baseline`, the tests known to be failing before work began |
| `--timeout` | Default 600. A run that exceeds it is recorded as a failure with the note "timed out" |

The script runs the command through the shell from the repository root, shows the last 40
lines of its output to the caller, and stores none of the output.

| Phase | Recorded as valid when | Exit |
|-------|------------------------|------|
| `baseline` | Always. Failures are listed as pre-existing | 0 |
| `red` | The run exited non-zero and the output contains the `--expect` text | 0 valid, 1 not |
| `green` | The run exited zero | 0 valid, 1 not |
| `refactor` | The run exited zero | 0 valid, 1 not |
| `checkpoint` | The command's scope is `broad` and the run exited zero | 0 valid, 1 not |

A `baseline` record comes first. Until the evidence document holds one, every other phase
exits 2 and records nothing, with a message saying to record a baseline with a `broad`
command first, so that pre-existing failures are known before the feature's work begins.

A `red` run that exits zero is recorded with the note "passed on first run: investigate".
A `red` run that fails without the expected text is recorded with the note "failed for a
different reason". Neither satisfies G3.

### `classify`

```text
classify --seq <n> --as <assertion|defect|environment|unreliable> [--note <text>]
```

Sets the classification of a failure record that is `unclassified`. Exit 2 when the record
is a pass or is already classified.

### `exception`

```text
exception --task <task id> [--vo <obligation id> ...] --kind <kind>
          --rationale <text> [--alternative <text>]
          [--needs-approval] [--approved-by <name>]
```

Records a TDD Exception. It covers the obligations named with `--vo` for every task that
names them, so one exception serves an obligation's `test` task and its `behaviour` tasks;
`--task` records the task it was raised on. With no `--vo` it applies to that task only.
`--alternative` is required for every kind except
`environment-blocked`. Needs approval is recorded as yes, with or without
`--needs-approval`, for the kinds `legacy`, `exploratory` and `other` and when the
alternative is `none` (FR-052).

### `expectation`

```text
expectation --task <task id> --tests <test file> ... --requirement <id> ...
            --justification <text> [--alters-behaviour] [--approved-by <name>]
```

Records an Expectation Change and the new fingerprint of the named files.

### `decision`

```text
decision open --question <text> --tasks <task id> ...
decision resolve --id <decision id> --answer <text> --by <name>
```

### `approve`

```text
approve --id <exception or expectation change id> --by <name>
```

Records a person's approval on an entry that was waiting for one.

**Limit**: the script records the name it is given and cannot confirm a person supplied
it. The wrapped implement command tells the agent to record an approval only after the
developer has given it in the conversation. The name is visible to the reviewer.

## `hook`

The runtime event handler. It reads the coding agent's tool-call payload as JSON on
standard input and decides whether the call may proceed.

Payload fields read, as Claude Code sends them for `PreToolUse`:

| Field | Used for |
|-------|----------|
| `tool_name` | `Edit`, `Write` or `MultiEdit` |
| `tool_input.file_path` | The file about to change |
| `tool_input.old_string`, `tool_input.new_string`, `tool_input.replace_all` | The resulting content for `Edit` |
| `tool_input.edits` | The resulting content for `MultiEdit` |
| `tool_input.content` | The resulting content for `Write` |

Reading the payload is the only agent-specific code in the script. It is isolated in one
adapter function per agent, selected by `--agent`, default `claude`.

| Situation | Exit | Standard error |
|-----------|------|----------------|
| The file is not named `tasks.md` or `tdd-evidence.md` | 0 | Nothing. Decided from the path alone, before any file is read |
| The file's own directory has no `plan.md`, or its `plan.md` has no Verification Plan | 0 | Nothing. The feature is not under the process; the wrapped commands report this as a gap |
| The file is `tasks.md` and no task changes from `[ ]` to `[X]` | 0 | Nothing |
| The file is `tasks.md` and every newly completed task passes `gate` | 0 | Nothing |
| The file is `tasks.md` and a newly completed task fails `gate` | 2 | The findings, and the two ways forward: meet the rule, or record an exception with a rationale |
| The file is `tdd-evidence.md` | 2 | "Evidence is written only by the check script" and the subcommand to use |
| The payload or the artefacts cannot be read, for one of the two guarded files | 2 | The error. The stop fails closed for the guarded files only |

Exit code 2 is what makes Claude Code refuse the tool call and return the message to the
agent. The handler must return within the event timeout of 30 seconds; it reads three
files and runs no tests.

The guard follows the file and not the active feature: every feature directory whose
`plan.md` holds a Verification Plan is guarded, whichever feature `.specify/feature.json`
names.

**Limit**: `plan.md` itself is not guarded. An edit that removes its Verification Plan
heading takes the feature out of the guard, and a command added to its Verification
commands table counts as declared. The first is reported by `compliance`; the second is
visible only to a reviewer.
