# Implementation Plan: Integrated Test-Driven Development for Spec Kit

**Branch**: `001-integrated-tdd` | **Date**: 2026-10-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-integrated-tdd/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Build test-driven development into the existing Spec Kit stages, so that a developer who
runs the standard commands gets verification intent derived from requirements, an
implementation stage that works through Red, Green, Refactor with real test evidence, and
a hard stop on tasks that lack that evidence.

The technical approach, from [research.md](./research.md), is two Spec Kit packages in one
repository:

- A **preset** that wraps the core plan, tasks, analyze and implement commands and appends
  a Verification Plan section to the plan template and label conventions to the tasks
  template. This is how behaviour changes inside the existing stages with no new command.
- An **extension** that supplies the agent-neutral process rules, one deterministic Python
  check script, and a `pre_tool_use` runtime event. The script runs the project's own
  declared test commands and writes the evidence itself, so a recorded result always comes
  from a real execution. The event refuses the edit that would mark a task complete when
  the task's gate fails.

Verification intent lives in `plan.md` and `tasks.md`. Evidence lives in one new document
per feature, `tdd-evidence.md`. An evaluator gets example stories and a compliance check
that reads a finished run.

## Technical Context

**Language/Version**: Python 3.9 or later for the check script; Markdown for command
wrappers, templates and rules; YAML for the two manifests

**Primary Dependencies**: Python standard library only (`argparse`, `subprocess`,
`hashlib`, `json`, `re`). Spec Kit CLI 1.0.2.dev0 as the host, examined at commit `51e52be`

**Storage**: Markdown files in the adopting project's feature directory: tables in
`plan.md`, labels in `tasks.md`, and the append-only `tdd-evidence.md`. No database

**Testing**: `unittest` from the standard library, with fixture feature directories and
recorded Claude Code hook payloads. Ruff for Python, markdownlint for Markdown. Installation
and regression tests use the `specify` CLI against throwaway projects. Agent-driven
behaviour is tested by a person using the example stories

**Target Platform**: Any platform where Spec Kit and Python 3 run. Full enforcement on
Claude Code; Linux and macOS first, Windows not tested in the first release

**Project Type**: Spec Kit customisation: one preset and one extension, containing a
single-file command-line tool

**Performance Goals**: The runtime event handler decides in under 1 second for a feature
with 200 tasks and 1,000 evidence records, so it is not noticeable on ordinary edits. Every
checking subcommand finishes in under 2 seconds at that size. Edits to files other than the
two guarded ones are allowed before any artefact is read

**Constraints**: No dependencies beyond the standard library and no network access. The
script writes only `tdd-evidence.md`. Checking subcommands give identical output on
identical input. No test framework is assumed: results come from exit status and a text
match. No new developer-facing command. Installing and removing leave other commands,
presets, extensions and the project's quality controls unchanged

**Scale/Scope**: One Python module of roughly 1,200 to 1,500 lines with twelve subcommands,
four command wrappers, two template addenda, two extension templates, one event handler
file, seven example stories and two example runs. Sixteen gate and compliance rules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Checked against constitution version 1.0.0.

| Principle | Gate | Before research | After design |
|-----------|------|-----------------|--------------|
| I. Integrate, Don't Add | No new developer-facing command; no new mandatory document without a recorded reason; no parallel workflow | Pass, with one recorded departure | Pass, with one recorded departure |
| II. Developers Stay Accountable | Ambiguity and consequential trade-offs go to a person; routine work does not; artefacts are assessable by someone who took no part | Pass | Pass |
| III. Deterministic Checks, Agent Judgement | Objective conditions are checked by a repeatable check; a failed check blocks | Pass | Pass, with five recorded limits |
| IV. Test-First with Real Evidence | Executable components are built test-first; impractical cases are recorded with an alternative | Pass | Pass, with two recorded exceptions |
| V. Verify Against Current Spec Kit | Mechanisms confirmed against the current source before the design relies on them | Open: nothing examined yet | Pass, conditional on the installation tests |
| VI. Compatible and Removable | Install and removal leave everything else working; project controls untouched; no framework required | Pass | Pass |

**I. Integrate, Don't Add.** The extension registers no command and no lifecycle hook, so
the list of commands a developer sees does not change (research D1, D6). All behaviour is
reached through the four wrapped core commands. The one departure is the new document
`tdd-evidence.md`; see Complexity Tracking.

**II. Developers Stay Accountable.** The plan wrapper puts material ambiguity to the
developer. Decisions, exception approvals and behaviour-altering expectation changes are
recorded with who decided. Routine cycles involve no request. The evidence document opens
with a generated summary written for a reviewer.

**III. Deterministic Checks, Agent Judgement.** The division is the table in research D4.
The task gate blocks through a runtime event and is not a note. Five limits are recorded and
are not presented as covered: an edit to `tasks.md` made through a shell command bypasses
the event and is caught only by the end-of-stage gate and the compliance check (D5); and
the script records an approver's name without being able to confirm a person supplied it
([check script contract](./contracts/check-cli.md)); `plan.md` is not guarded, so removing
its Verification Plan heading stops the event guarding that feature, which only the
compliance check then reports (D5); and a command added to the Verification commands table
counts as declared whatever it runs, which only a reviewer reading the table's Source
column or the diff can see (D7); and the fingerprint covers only the test files named on a
failing-first record, so a change to any other existing test is governed by the process
rules and seen by a reviewer in the diff, not by a check (D8).

**IV. Test-First with Real Evidence.** `tdd_check.py` is built test-first with `unittest`:
each rule gets a failing fixture test before it is implemented. The evidence is the git
history: failing tests are committed, with the failure in the commit message, before the
commit that makes them pass. Because a commit message is the agent's account, the history
is replayed at the end: each test commit is checked out and run, and must fail as its
message says (task T090). Recorded exception: the
Markdown command wrappers, rules and templates are prompts, and a failing automated test of
how an agent behaves on reading them is not practical. Alternative verification: structural
tests written first where a condition is objective (the manifests are well formed, every named file
exists, every wrapper contains `{CORE_TEMPLATE}` and names the rules file), installation
tests that read the composed commands, and the example stories driven by a person and
checked with the compliance check ([quickstart.md](./quickstart.md) scenarios 2 to 4).

Second recorded exception: the performance tests measure code that already exists when they
are written, so they are expected to pass on their first run. Alternative verification:
each is run once against a generated feature large enough to exceed its limit and is seen
to fail on the time limit, and that run is recorded, before the test is accepted at the
stated size. Every other guard on the script (standard library imports, the agent adapter
mapping, writing only `tdd-evidence.md`, framework neutrality) is written with the first
tests of the code it guards, and so fails first in the ordinary way.

**V. Verify Against Current Spec Kit.** Every mechanism the design uses was read in the
installed CLI source, and research.md cites where. None of it was run. Nine assumptions
(A1 to A9) must be confirmed by installation tests, and these are the first implementation
tasks. A1, that an exit code of 2 from the handler makes Claude Code refuse the tool call,
decides whether FR-060, and with it the full enforcement FR-061 requires on Claude Code,
can be met as designed; if it fails, the plan returns to the
developer before further work. Bundles were not examined and are not designed (D13).

**VI. Compatible and Removable.** Wrappers use the `wrap` strategy and addenda use
`append`, so they compose with other presets and track upstream changes to the core
commands. The extension is installed and removed entirely by Spec Kit's own commands,
including its entry in `.claude/settings.json`. Nothing reads or writes the project's test,
lint or CI configuration. Changes to existing behaviour are listed in the
[artefact formats contract](./contracts/artefact-formats.md) section 4, for the README.

**Additional constraints.** Delivery is through a preset and an extension, chosen in D1.
Process rules and checks are agent-neutral, with one payload adapter for Claude Code (D11).
Proportion is the agent's judgement on how many obligations a requirement needs; the checks
set only the floor of one obligation or exemption per functional requirement and per
acceptance scenario. Obligation status is
derived and never stored. The review summary is a view the script regenerates into
`tdd-evidence.md` on every write; no check reads it as a source, and the compliance check
reports it when it has fallen behind `plan.md` or the records (D2, D9).

**Quality gates.** The four required test levels map to quickstart scenarios: structural
validation in scenario 1; installation and registration in scenario 2; behavioural testing
in scenarios 1, 3 and 4; regression testing in scenario 5.

**Result**: the gates pass. Phase 2 may proceed, with the installation tests for A1 to A9
ordered first.

## Project Structure

### Documentation (this feature)

```text
specs/001-integrated-tdd/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── architecture.md      # Phase 1 output (/speckit-plan command, C4 preset)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── check-cli.md         # The check script: subcommands, options, exit codes, hook
│   ├── artefact-formats.md  # Verification Plan, task labels, evidence document, stage additions
│   └── packaging.md         # Manifests, install and removal effects, repository deliverables
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
extension.yml                             # Extension manifest: templates, script, pre_tool_use event
preset.yml                                # Preset manifest: four command wraps, two template appends
.extensionignore                          # Keeps preset, tests, examples and project files out of the extension install

commands/
└── speckit.integrated-tdd.gate.md        # Event handler carrier, not a registered command

templates/
├── tdd-process-rules.md                  # Agent-neutral process rules
└── tdd-evidence-template.md              # Starting content of tdd-evidence.md

scripts/
└── python/
    └── tdd_check.py                      # Checks, run recording, gate, hook, compliance

preset/
├── commands/
│   ├── speckit.plan.md                   # wrap
│   ├── speckit.tasks.md                  # wrap
│   ├── speckit.analyze.md                # wrap
│   └── speckit.implement.md              # wrap
└── templates/
    ├── plan-addendum.md                  # append: Verification Plan section
    └── tasks-addendum.md                 # append: task label conventions

tests/
├── support.py                            # Fixture copying and subprocess helper
├── test_cli.py                           # Common CLI behaviour
├── test_parsing.py                       # Artefact parser
├── test_trace.py                         # plan and tasks checks
├── test_run.py                           # Command runner and evidence ledger
├── test_gate.py                          # Rules G1 to G9
├── test_hook.py                          # Hook adapter and decisions
├── test_status.py                        # Derived status and the Summary
├── test_compliance.py                    # Rules C1 to C7 against examples/runs
├── test_manifests.py                     # Structural validation of both packages
├── test_performance.py                   # Time limits at 200 tasks and 1,000 records
└── fixtures/
    ├── bin/                              # Stand-in test commands
    ├── features/                         # Small feature directories, one per rule case
    └── payloads/                         # Recorded Claude Code PreToolUse payloads

examples/
├── stories/                              # Seven example stories with expected behaviour
└── runs/
    ├── sample-project/                   # The tiny project both runs were produced from
    ├── compliant/                        # Artefacts of a run that followed the process
    └── tests-only/                       # Artefacts of a run that only added test files

docs/
└── evaluation.md                         # Driving the stories, the compliance check, later comparison

README.md                                 # Install, removal, behaviour changes, success criteria, limits
CHANGELOG.md
LICENSE
ruff.toml
.markdownlint-cli2.yaml
```

**Structure Decision**: A single project with both manifests at the repository root, the
layout the author's `c4` extension and `c4-model` preset already use, so that one tag
archive installs either package. Extension files sit in Spec Kit's conventional top-level
folders (`commands/`, `templates/`, `scripts/python/`); preset files sit under `preset/`
and are excluded from the extension install. All rule logic is in one Python module
because Spec Kit installs an extension by copying files and the module must run with no
installation step. `tests/` and `examples/` are development and evaluation material and do
not ship to adopting projects. The existing `specs/`, `stories/`, `.specify/` and `.claude/`
directories are this project's own Spec Kit workspace and are also excluded.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| A new mandatory document, `tdd-evidence.md` (Principle I) | Test execution evidence is append-only, written by a script, and grows through implementation. The specification requires one dedicated evidence document, separate from the specification, plan and tasks (FR-063, clarification of 2026-10-10) | Appending evidence to `tasks.md` or `plan.md` would have a script rewriting documents the agent and developer edit, would mix intent with outcome, and would make the "only the script writes evidence" guard impossible |
| A command file in the extension, `speckit.integrated-tdd.gate.md` (Principle I) | Spec Kit's runtime events resolve a handler through a command file's `scripts:` frontmatter; there is no other way to attach a script to an event | Not a developer-facing command: it is unlisted, so no skill or slash command is created. If installation test A2 fails it must be listed, and this row then records a visible command the developer never needs to run |

**Approval** (constitution, Governance: a departure is acceptable only when recorded with a
justification and approved by a person). Approved by Lee Sinclair on 2026-10-10:

1. The new mandatory document `tdd-evidence.md` (Principle I, first row above).
2. The unlisted command file that carries the event handler (Principle I, second row).
3. Markdown wrappers, rules and templates are not built test-first (Principle IV, first
   recorded exception).
4. Performance tests are not fail-first (Principle IV, second recorded exception).
5. The limit that a shell edit to `tasks.md` bypasses the hard stop until the end-of-stage
   gate (Principle III).
6. The limit that an approver's name is recorded but cannot be verified (Principle III).
7. The limit that removing the Verification Plan heading from `plan.md` stops the event
   guarding that feature until the compliance check reports it (Principle III).
8. The limit that a command added to the Verification commands table counts as declared
   whatever it runs, and is visible only to a reviewer (Principle III).
9. The limit that only test files named on a failing-first record are fingerprinted, so
   weakening, skipping or removing another existing test is not detected by a check
   (Principle III, FR-029).

<!-- markdownlint-disable-file MD041 -->

## Architecture

**Feature architecture**: [architecture.md](./architecture.md) (C4 component views,
sequence diagrams, ER diagram)

**System views**: not yet created. `docs/architecture/context.md`, `containers.md` and
`erd.md` do not exist; `/speckit-c4-system` creates them from the Architecture Impact table
once the feature is implemented.

| View | Impact of this feature |
|------|------------------------|
| Context | New: the Integrated TDD system; Developer and Technical Lead or Reviewer; Coding Agent, Spec Kit, Project Test Tooling and Project Quality Controls as external systems |
| Containers | New: Integrated TDD Preset, Integrated TDD Extension, Feature Artefacts, and eight relationships among them and the external systems |
| Components | Integrated TDD Preset: four command wrappers and two template addenda. Integrated TDD Extension: process rules, gate event handler, check CLI, hook adapter, trace checks, gate rules, command runner, evidence ledger, artefact parser, evidence template. All new |
| Flows | Eight: verification intent in plan and tasks; one task through Red, Green, Refactor; completion refused without evidence; a test changed between Red and Green; blocked run, exception and decision; reviewer reading the evidence; installation; evaluating a finished run |
| ERD | New: Verification Command, Verification Obligation, Verification Exemption, Test Execution Record, TDD Exception, Expectation Change, Decision. Changed: Task gains obligation and no-test labels. Referenced: Requirement, Executable Test |
