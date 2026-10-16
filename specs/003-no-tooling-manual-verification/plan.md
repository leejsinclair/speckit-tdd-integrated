# Implementation Plan: Verification Only Where It Is Possible

**Branch**: `003-no-tooling-manual-verification` | **Date**: 2026-10-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-no-tooling-manual-verification/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Make the process apply test-first development and the behaviour checklist where they are
possible, and say so plainly where they are not, without ever stopping the developer. Two
situations get a first-class, reported state instead of a dead end:

- **No test tooling.** A project with no runnable test command records a single `None` row
  in the plan's Verification commands table. The plan check passes, tasks are generated,
  implementation needs no baseline, and every obligation is reported as deferred for that
  reason. The process still never chooses or installs a framework. Declaring a command
  switches every check on.
- **Tests that cannot be run, and checks only a person can do.** An obligation can be
  deferred with a reason, in a new chained evidence table. A new `### Manual verification`
  table in the plan lists checks with steps and expected results, and a person can record
  their result. Deferred obligations and open manual checks are shown by `status` and
  listed by `compliance` as notices that never fail. Nothing deferred is ever reported as
  verified.

The technical approach, from [research.md](./research.md):

- **Mode derived, not recorded** (D1, D2). `None` in the commands table sets
  `plan.no_tooling`. Gate rules G3, G4 and G6 skip an obligation that is deferred, and the
  baseline is demanded only by `run`, which is not called in this mode.
- **Deferral** (D3, D4, D5). A new `## Deferrals` table in the evidence document, chained
  like the Test Execution Records, written by a new `defer` subcommand. The agent defers
  alone only on a recorded environment failure; any other basis needs a named person
  (`approve` gains `DF-` ids), enforced by a new gate rule G12. `obligation_status` gains
  `deferred`; a later passing run still makes an obligation `verified`.
- **Manual verification** (D6, D7, D8). A `### Manual verification` table in the Verification
  Plan, checked by rules M1 and M2; a `## Manual results` evidence table written by a new
  `manual` subcommand; behaviour items may name `MV-` ids and show status `manual`.
- **Reporting** (D9). `status` and `compliance` print deferred obligations, open manual
  checks and the no-tooling state as notices; a new compliance rule C9 reports the one
  contradiction (no tooling recorded but runs exist, or a command declared as well).
- **Older features** (D10). Plans without the new table, and evidence without the new
  tables, are read as empty and are not reported as failing.

## Technical Context

**Language/Version**: Python 3.9 or later for the check script; Markdown for wrappers,
templates, rules and documentation; YAML for the manifests

**Primary Dependencies**: Python standard library only, as in 001 and 002. Spec Kit CLI
1.1.3 as the host. No new Spec Kit mechanism is used (research D12)

**Storage**: Markdown files in the adopting project's feature directory: one new
sub-heading and table in `plan.md`, and two new tables in the evidence document. No
database

**Testing**: `unittest` with generated fixture feature directories and recorded Claude Code
payloads; Ruff; markdownlint; installation tests with the `specify` CLI in a throwaway
project; agent-driven behaviour by a person using the example stories

**Target Platform**: As 001 and 002: any platform with Spec Kit and Python 3; full
enforcement on Claude Code; Linux and macOS

**Project Type**: Spec Kit customisation: changes to one preset and one extension, and to
their single-file check script

**Performance Goals**: As 002: the event handler decides in under 1 second, and every
checking subcommand finishes in under 2 seconds, for a feature with 200 tasks, 1,000
records, 200 behaviour items and now also 50 deferrals and 50 manual checks

**Constraints**: Standard library only; no network. Checking subcommands stay
deterministic. For a feature with a declared command and no deferral or manual check, every
subcommand's output and exit code are those of 0.2.0 (SC-006). The process never chooses,
installs or configures a test framework. The agent's edit tools stay refused for the
evidence document

**Scale/Scope**: About 350 to 500 added lines in `tdd_check.py`; edits to four wrappers,
two template addenda, the evidence template and the process rules; about 25 new fixture
directories; two new examples and one new story; README, CHANGELOG and evaluation guide.
Two parsing additions, one gate rule, two plan rules, one compliance rule, two subcommands

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Checked against constitution version 1.0.0.

| Principle | Gate | Before research | After design |
|-----------|------|-----------------|--------------|
| I. Integrate, Don't Add | No new developer-facing command; no new mandatory document without a recorded reason; no parallel workflow | Pass, with one departure to record | Pass, with one recorded departure |
| II. Developers Stay Accountable | Ambiguity and consequential trade-offs go to a person; routine work does not; artefacts assessable by someone who took no part | Pass | Pass |
| III. Deterministic Checks, Agent Judgement | Objective conditions checked repeatably; a failed check blocks | Pass | Pass, with three recorded limits |
| IV. Test-First with Real Evidence | Executable components built test-first; exceptions recorded with an alternative | Pass | Pass, with the exceptions approved for 001 |
| V. Verify Against Current Spec Kit | Mechanisms confirmed against the current source | Pass: no new mechanism | Pass: no new mechanism (D12) |
| VI. Compatible and Removable | Install and removal leave everything working; changes to behaviour justified and documented; no framework required | Pass | Pass, with two documented behaviour changes |
| No duplication (Additional Constraints) | Information held elsewhere is not copied into new artefacts | Pass | Pass |

**I. Integrate, Don't Add.** Nothing is added to the lifecycle. The no-tooling state is a
value in an existing plan table, and the manual list is a sub-section of the existing
Verification Plan. Two subcommands of the check script, `defer` and `manual`, are new. They
are called by the agent, and by a person for a manual result, and are not Spec Kit
commands; 001 and 002 gave the same treatment to `run`, `exception` and `expectation`.
Recorded as departure 1 because 002 chose to add none (research D3).

**II. Developers Stay Accountable.** Deferring for any reason other than a recorded
environment failure needs a named person (FR-008A), checked by G12. A manual result is
recorded under a person's name. The no-tooling and deferred states are in every report so a
developer who did not take part can see that nothing was verified by tests (FR-006, FR-010,
FR-021). Routine work asks for nothing.

**III. Deterministic Checks, Agent Judgement.** M1, M2, G12, C9 and the extended G3, G4, G6
and B2 are rules of the script. Three limits are recorded and not presented as covered:

1. Whether a reason given for a deferral is a true one (the queue really was unreachable)
   is judgement. The script requires a recorded environment failure for an unapproved
   deferral, which the agent cannot invent without a failing run in the evidence.
2. Whether a manual check was actually done is the word of the person named. The record
   shows who said so and when.
3. A feature with no test tooling can complete with nothing verified. This is deliberate
   (clarification of 2026-10-17); the reports make it visible and there is no setting.

**IV. Test-First with Real Evidence.** Every script change is built test-first. The wrapper,
rule and template text is not executable and is checked by the manifest and wording tests,
as for 001 and 002. The one exception recorded in 002 for the performance test is repeated
(research D13).

**V. Verify Against Current Spec Kit.** The change uses the preset `wrap` and `append`
strategies and the extension template mechanism that 001 and 002 already confirmed against
1.1.3. No manifest field is added (research D12).

**VI. Compatible and Removable.** Two behaviour changes are documented: a plan whose
Verification commands table holds only `None` now passes (it was a finding), and `defer`
and `manual` add tables to the evidence document only when first used. Features planned
before this change are read as before (D10). No framework is required, chosen or installed.

## Project Structure

### Documentation (this feature)

```text
specs/003-no-tooling-manual-verification/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── architecture.md      # Phase 1 output (C4 preset)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── check-cli-changes.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
scripts/python/tdd_check.py          # parsing, rules M1 M2 G12 C9, defer, manual, status
templates/
├── tdd-process-rules.md             # new section "When verification is not possible"
└── tdd-evidence-template.md         # unchanged; the script writes the two new tables on first use
preset/
├── commands/                        # plan, tasks, implement, analyze wrappers
└── templates/plan-addendum.md       # the "### Manual verification" sub-heading
examples/runs/                       # no-tooling and deferred examples (new)
examples/stories/                    # story 09, new project with no framework (new)
tests/
├── fixtures/features/               # generated feature directories (new cases)
└── test_*.py                        # new and extended unit tests
README.md  CHANGELOG.md  docs/evaluation.md  extension.yml  preset.yml
```

**Structure Decision**: unchanged from 001 and 002: one preset, one extension, one
single-file check script. The new behaviour is added to the script's existing sections
(parsing, rules, run and ledger, status and compliance), not to a new module (research D14).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Two new subcommands of the check script, `defer` and `manual` (Principle I, as 002 read it) | A deferral and a manual result must be recorded in a chained table, which only the script can write without breaking the chain. A person records a manual result by running `manual` or by asking the agent to | Reusing `exception` for deferral would put it in a table that is not chained, which FR-008 forbids. Reusing `decision` has the wrong meaning. Asking people to edit the evidence document breaks its protection |
| Two new evidence tables, `## Deferrals` and `## Manual results` (Principle I) | The records table cannot carry them: a deferral is not a run and a manual result has a person but no command. Each needs its own chain | Adding phases `defer` and `manual` to Test Execution Records would give them a Result column of `pass` or `fail` and put them in the path of G4 and G6, which would then need special cases in every rule that reads the records |

**Approved by Lee Sinclair on 2026-10-17** (constitution, Governance: a departure is
acceptable only when recorded with a justification and approved by a person). All five
items approved in the conversation:

1. The two new subcommands `defer` and `manual` (Principle I).
2. The two new evidence tables (Principle I).
3. The Markdown wrappers, rules and template text are not built test-first (Principle IV,
   as approved for 001 and 002).
4. The extended performance test is not fail-first in the ordinary way (Principle IV, as
   approved for 001 and 002).
5. The three limits recorded under Principle III above.

## As built (T039)

The Constitution Check and Complexity Tracking above were re-read against what was built on
2026-10-17. No new departure was found, so nothing waits for the maintainer. The differences
and limits as built:

- **Principle I.** Two subcommands (`defer`, `manual`) and two evidence tables (`## Deferrals`,
  `## Manual results`) were added, the approved departures. No Spec Kit command, document or
  workflow was added.
- **Principle III, limits.** The three recorded limits stand as built. Two more are in the
  README's Known limits: items stay editable with no baseline, and a feature whose
  obligations are all deferred completes, with notices. Neither is a new departure.
- **Principle IV.** Every script change has a failing-test commit before its implementation
  commit (replayed in T040). The wrapper, rule and template text was tested by wording tests,
  as approved. The extended performance test passed on its first run, the approved exception;
  each limit was shown reachable (quickstart, T032). The example tests (T028) failed first and
  the examples were then made by the check script.
- **Principle VI.** The two documented behaviour changes are in the CHANGELOG under 0.3.0. The
  0.2.0 outputs on every fixture that existed then are unchanged (compatibility tests).
- **Layout of the status view.** The "Not verified by tests" section is a bullet list with a
  `Counts:` line, not the table drawn in the design; the content is the same.
- **Command syntax.** `approve` takes `--id` (`approve --id DF-02 --by NAME`), and the
  quickstart's shorthand was corrected to match.
- **A verified record after a deferral.** A passing run for a deferred obligation leaves it
  `deferred` unless a valid failing-first record precedes it; the obligation reads `verified`
  only then. This follows from rule G3 and G4 and is a limit, not a departure.
- **Performance as built.** At ten times the stated scale `gate --all` and `compliance` take
  about 35 s against the 2 s limit, with or without deferrals and manual checks. The README
  records it as a known limit.
- **Observed in an agent run (T037).** One model's task list named the standard library
  `unittest` as a placeholder. Nothing was installed or configured. The wrapper says the
  process never chooses a framework, and it was not changed; a maintainer may wish to tighten
  the tasks wrapper.
- **Format check.** `ruff format --check` flags two older test files; this feature's code is
  clean.

<!-- markdownlint-disable-file MD041 -->

## Architecture

**Feature architecture**: [architecture.md](./architecture.md) (C4 component views,
sequence diagrams, ER diagram)

**System views**: not yet created. `docs/architecture/context.md`, `containers.md` and
`erd.md` do not exist; `/speckit-c4-system` creates them from the Architecture Impact
tables of 001, 002 and this feature.

| View | Impact of this feature |
|------|------------------------|
| Context | None: the same people and external systems as 001 |
| Containers | No container added. Feature Artefacts gains two evidence tables and one plan table |
| Components | Preset: four wrappers and one addendum changed. Extension: Artefact Parser, Gate Rules, Evidence Ledger, Command Runner, Trace Checks, Checklist Checks and Process Rules changed; one new component, Deferral and Manual Checks |
| Flows | Three: a project with no test tooling reaches the end of implementation; an obligation is deferred and later verified; a manual check is listed, recorded and reported |
| ERD | New: Deferral, Manual Check, Manual Result. Changed: Verification Command (a `None` row), Obligation (status `deferred`) |
