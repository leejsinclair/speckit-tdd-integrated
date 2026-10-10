---

description: "Task list for Integrated Test-Driven Development for Spec Kit"
---

# Tasks: Integrated Test-Driven Development for Spec Kit

**Input**: Design documents from `/specs/001-integrated-tdd/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included and mandatory. Constitution Principle IV requires every executable
component to be built test-first: each rule gets a failing fixture test before it is
implemented. Markdown wrappers, rules and templates are prompts, so they get structural
tests written first plus installation checks (plan.md, Constitution Check IV).

**Organization**: Tasks are grouped by user story so each story can be implemented and
tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1 to US7)
- Every description names the file or directory it changes

## Path Conventions

- Single project. Both manifests sit at the repository root
- Extension files: `commands/`, `templates/`, `scripts/python/`
- Preset files: `preset/commands/`, `preset/templates/`
- Development and evaluation material: `tests/`, `examples/`, `docs/`
- `<repo>` is this repository. `<tmp>` is a throwaway directory outside it. Never install
  into this repository's own `.specify/`
- The check script is always run as `python3 -B scripts/python/tdd_check.py`. The test
  suite is always run as `python3 -B -m unittest discover -s tests`

## Conventions for every test task

- Write the tests, run the suite, and confirm the new tests fail for the intended reason
  (the behaviour is missing, not an import or fixture error) before starting the
  implementation task that follows
- Commit each test task while its new tests fail, before any implementation of what they
  test. The commit message lists the failing tests and the failure reason as the run
  printed it. The implementation task that makes them pass is a later, separate commit
  whose message gives the passing run's summary line. Git history is this project's
  evidence of Red before Green (Constitution Principles III and IV), since the check
  script is not installed here. Never amend or squash these commits together: T090 replays them at the end
- Tests drive the script as a subprocess through the helper in `tests/support.py` and
  assert on exit code, standard output and standard error, as the
  [check script contract](./contracts/check-cli.md) defines them
- Fixture feature directories live under `tests/fixtures/features/<case-name>/` and hold
  only the files the case needs (`spec.md`, `plan.md`, `tasks.md`, `tdd-evidence.md`), in
  the formats of the [artefact formats contract](./contracts/artefact-formats.md)
- The code must run on Python 3.9: no `match`, no `X | Y` type unions at runtime, no
  `tomllib`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository layout and tooling

- [X] T001 Create the directories `commands/`, `templates/`, `scripts/python/`, `preset/commands/`, `preset/templates/`, `tests/fixtures/features/`, `tests/fixtures/payloads/`, `tests/fixtures/bin/`, `examples/stories/`, `examples/runs/compliant/`, `examples/runs/tests-only/` and `docs/` at the repository root, as plan.md Project Structure lists them
- [X] T002 [P] Create `ruff.toml` with `target-version = "py39"`, and exclude `.specify/`, `.claude/` and `examples/`
- [X] T003 [P] Create `.markdownlint-cli2.yaml` that lints the repository's Markdown, ignores `.specify/`, `.claude/` and `node_modules/`, and is configured so the existing documents under `specs/001-integrated-tdd/` pass unchanged
- [X] T004 [P] Create `LICENSE` (MIT, Lee Sinclair, 2026) and `CHANGELOG.md` with an Unreleased section for version 0.1.0
- [X] T006 Create `tests/support.py` with helpers that copy a fixture feature directory into a temporary repository root (with a `.specify/feature.json` pointing at it), run `scripts/python/tdd_check.py` as a subprocess with given arguments, standard input and environment, and return exit code, standard output and standard error
- [X] T007 [P] Create `tests/fixtures/bin/fake_test.sh`, a framework-neutral stand-in for a project's test command: it takes one selector argument and, by selector, exits 0 printing `ok`, exits 1 printing `AssertionError: expected 0 got None`, exits 1 printing `ModuleNotFoundError: no module named cart`, sleeps past a short timeout, or prints 60 numbered lines before exiting 1

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prove the Spec Kit mechanisms the design relies on (research assumptions A1
to A9), then build the parser and CLI frame every story uses

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. If A1 fails,
stop at T020 and return the plan to the developer

### Packaging skeleton (tests first)

- [X] T008 [P] Write structural tests in `tests/test_manifests.py`: `extension.yml` and `preset.yml` exist; every `file:` path either names exists; the extension has no `provides.commands` and no `hooks:` key; `events.pre_tool_use` names `speckit.integrated-tdd.gate` with matcher `Edit|Write|MultiEdit` and timeout 30; `commands/speckit.integrated-tdd.gate.md` exists and its frontmatter `scripts:` block has the single entry `py: scripts/python/tdd_check.py hook`; both manifests carry the same version; every file under `preset/commands/` contains `{CORE_TEMPLATE}` exactly once; `.extensionignore` lists every path contracts/packaging.md names; `templates/tdd-process-rules.md` exists and names no coding agent (FR-061). Read the manifests with regular expressions, because the standard library has no YAML parser; loading by Spec Kit itself is proved in T016
- [X] T009 [P] Write tests in `tests/test_cli.py` for the common behaviour in contracts/check-cli.md: the feature directory comes from `--feature-dir`, then `SPECIFY_FEATURE_DIRECTORY`, then `.specify/feature.json`; an unknown subcommand or missing required option exits 2; `--json` prints one JSON object; all twelve subcommands (`plan`, `tasks`, `gate`, `status`, `compliance`, `run`, `classify`, `exception`, `expectation`, `decision`, `approve`, `hook`) are accepted by the argument parser; the script source imports only standard library modules and none of `socket`, `urllib`, `http` or `requests`
- [X] T010 [P] Write the first hook tests in `tests/test_hook.py` with hand-written payloads in `tests/fixtures/payloads/` shaped as contracts/check-cli.md describes: a payload for a file that is neither guarded file exits 0 with empty standard error; a payload for a `tdd-evidence.md` whose directory holds a `plan.md` with a `## Verification Plan` heading exits 2 and standard error contains `Evidence is written only by the check script`; an unknown `--agent` value exits 2; the payload adapters are held in one mapping keyed by agent name, and no agent name appears elsewhere in the script (FR-061)
- [X] T011 Create `extension.yml` exactly as contracts/packaging.md gives it
- [X] T012 Create `preset.yml` exactly as contracts/packaging.md gives it
- [X] T013 Create `commands/speckit.integrated-tdd.gate.md` with frontmatter `scripts:` holding `py: scripts/python/tdd_check.py hook`, and a body saying it is run by the agent runtime and is not a command to invoke
- [X] T005 Create `.extensionignore` listing `preset/`, `preset.yml`, `tests/`, `examples/`, `docs/`, `specs/`, `stories/`, `.specify/` and `.claude/`, per contracts/packaging.md. Listed here, out of number order, so that its test in T008 is seen to fail first
- [X] T014 Create `scripts/python/tdd_check.py` with the `argparse` frame: twelve subcommands registered with the options in contracts/check-cli.md, feature directory resolution, the `<rule id> <subject>: <reason>` finding format, `--json` output, exit codes 0, 1 and 2, and a "not implemented" exit 2 for subcommands not yet built. Implement the first part of `hook`: a Claude Code payload adapter selected by `--agent` (default `claude`) that reads `tool_name` and `tool_input.file_path`, exit 0 from the path alone when the file is not named `tasks.md` or `tdd-evidence.md`, exit 0 when the file's own directory has no `plan.md` holding a `## Verification Plan` heading (the feature directory is the edited file's directory, not the active feature), and exit 2 with the contract's message for `tdd-evidence.md`. Makes T009 and T010 pass
- [X] T015 Create placeholder preset files so the packages install: `preset/commands/speckit.plan.md`, `speckit.tasks.md`, `speckit.analyze.md` and `speckit.implement.md`, each holding one marker line naming Integrated TDD above `{CORE_TEMPLATE}`; and `preset/templates/plan-addendum.md` and `preset/templates/tasks-addendum.md`, each holding its section heading only. Create placeholder `templates/tdd-process-rules.md` and `templates/tdd-evidence-template.md` with a title each. Makes T008 pass

### Installation tests for research assumptions A1 to A9

Record each outcome in a new `## Installation test results` section of
`specs/001-integrated-tdd/research.md`: assumption, date, what was run, what was observed,
confirmed or failed.

- [X] T016 Confirm A1, A2, A3 and A7 and record them in `specs/001-integrated-tdd/research.md`. Run `specify init <tmp>/proj --integration claude`; save `.claude/settings.json` (or `{}`) and the `.claude/skills` listing to `<tmp>` as the "before" state; run `specify extension add --dev <repo>`; create `specs/001-demo/` with a `plan.md` (holding a `## Verification Plan` heading), `tasks.md` and `tdd-evidence.md` and point `.specify/feature.json` at it. Add a second, temporary `PreToolUse` hook in `<tmp>/proj/.claude/settings.local.json` that copies its standard input to a new file under `<tmp>/payloads/`. In Claude Code (interactive, or `claude -p`) in `<tmp>/proj`, ask for an edit to `specs/001-demo/tdd-evidence.md` through each of Edit, Write and MultiEdit where the tool exists, for an edit that ticks a task in `specs/001-demo/tasks.md` through each of the same tools (allowed at this stage, and captured for T043), and for an edit to an unrelated file. Confirm the edits to `tdd-evidence.md` are refused with the handler's standard error shown to the agent, the other edits succeed, the handler ran although unlisted and declared only as `py:`, and the working directory and payload fields are as A7 states
- [X] T017 Copy the payloads captured in T016 into `tests/fixtures/payloads/` as `edit-evidence.json`, `write-evidence.json`, `multiedit-evidence.json`, `edit-tasks.json`, `write-tasks.json`, `multiedit-tasks.json` and `edit-unrelated.json`, replacing absolute paths under `<tmp>` with a `{ROOT}` token that `tests/support.py` substitutes, and replace the hand-written payloads from T010. If a tool does not exist in the Claude Code version tested, keep a hand-written payload for it and say so in a `tests/fixtures/payloads/README.md`
- [X] T018 [P] Confirm A4, A6 and A9 and record them in `specs/001-integrated-tdd/research.md`. In a fresh `<tmp>/proj2`: run `specify preset add --dev <repo>` before the extension and note whether it warns or blocks (A6); add the extension; list what was copied to `.specify/presets/integrated-tdd/` and `.specify/extensions/integrated-tdd/` and check `.extensionignore` was honoured (A9); diff `.claude/settings.json` before install, after install and after `specify extension remove integrated-tdd` (A4)
- [X] T019 Confirm A5 and A8 and record them in `specs/001-integrated-tdd/research.md`. In a project with the `c4-model` preset installed (install it from this repository's `.specify/presets/c4-model/` copy with `--dev`, or from its published source), run `specify preset resolve speckit.plan`, change priority with `specify preset set-priority integrated-tdd 5`, resolve again, and confirm both presets' text is present in either order (A5). From the Spec Kit changelog or tags, find the first release whose `specify_cli/events.py` validates extension `events:` (A8)
- [X] T020 Apply the outcomes of T016 to T019. A1 failed: stop all work and return the plan to the developer. A2 failed: list the handler under `provides.commands` in `extension.yml`, update T008's assertion, and update the second Complexity Tracking row in `specs/001-integrated-tdd/plan.md`. A3 failed: add a `sh:` wrapper script under `scripts/bash/` that calls the Python script. A7 differs: note the observed fields in `specs/001-integrated-tdd/contracts/check-cli.md`. A8: set `requires.speckit_version` in `extension.yml` and `preset.yml` to the release found. Wherever a manifest changes (A2, A8), make the same change to the manifest shown in `specs/001-integrated-tdd/contracts/packaging.md`. A4, A5, A6 or A9 failed: record the documented fallback from research.md as an item for the README task T074

### Artefact parser and shared documents

- [X] T021 [P] Create the fixture `tests/fixtures/features/valid-minimal/` with `spec.md` (three `FR-` requirements, one `SC-` criterion, one user story with two acceptance scenarios), `plan.md` (Verification Plan with a `unit` command `sh tests/fixtures/bin/fake_test.sh {select}` of scope `focused`, a `suite` command of scope `broad`, two obligations, one of which also names an `SC-` id, a `DC-` id and an `EC-` id, and one exemption), `tasks.md` (a `test` task, a `behaviour` task and a `[NT: reason]` task) and `tdd-evidence.md` (the example from contracts/artefact-formats.md section 3)
- [X] T022 Write parser tests in `tests/test_parsing.py` against `valid-minimal` and small malformed variants under `tests/fixtures/features/parse-*/`: a table is found by heading then header row; cells are trimmed; comma lists split; a lone `-` is empty; `FR-` and `SC-` ids are collected from `spec.md`; acceptance scenario ids `USn-ASm` are derived from each `### User Story n` heading and the numbered items of its Acceptance Scenarios list; commands, obligations and exemptions are read with the element rules of contract section 1 (id patterns, one `{select}` at most, scope and level enums, `None` exemption row); task lines yield id, checkbox state (`[ ]`, `[X]`, `[x]`), `[VO-nnn]` and `[NT: reason]` labels, and kind by the first-to-name rule including the several-obligations case; every evidence table is read; a missing section, a wrong header row and an out-of-range enum are reported as findings and never raise
- [X] T023 Implement the artefact parser in `scripts/python/tdd_check.py` (Markdown table reader, `spec.md` requirement ids, Verification Plan, task labels and kinds, evidence tables) so T022 passes
- [X] T024 Write the section skeleton of `templates/tdd-process-rules.md`: purpose and how the wrapped commands use it, then one heading each for verification intent, the Red, Green, Refactor cycle, test integrity, failures, exceptions and decisions, traceability and review evidence, and fitting the project. State at the top that the rules name no coding agent (FR-061)

**Checkpoint**: Mechanisms confirmed, packages install, parser and CLI frame pass their
tests. User story work can begin

---

## Phase 3: User Story 1 - Verification intent is derived from requirements before implementation (Priority: P1) 🎯 MVP

**Goal**: The plan and tasks stages produce a Verification Plan and labelled, test-first
ordered tasks, checked deterministically, with no new command

**Independent Test**: Take a story through `/speckit-specify`, `/speckit-plan` and
`/speckit-tasks` in a throwaway project and stop. `tdd_check.py plan` and
`tdd_check.py tasks` exit 0, every `FR-` id and acceptance scenario has an obligation or an exemption, and no
other command was run

### Tests for User Story 1

- [X] T025 [P] [US1] Create plan-check fixtures under `tests/fixtures/features/`: `plan-no-section/`, `plan-no-commands/`, `plan-uncovered-fr/`, `plan-uncovered-scenario/`, `plan-empty-outcome/`, `plan-empty-exemption-reason/`, `plan-unknown-requirement/` (an `FR-` id that is not in `spec.md`), `plan-unknown-prefix/` (an id such as `XX-01`), each a copy of `valid-minimal` with one defect
- [X] T026 [P] [US1] Create tasks-check fixtures under `tests/fixtures/features/`: `tasks-unlabelled/`, `tasks-unknown-obligation/`, `tasks-obligation-without-task/`, `tasks-obligation-without-behaviour/` (an obligation named by one task only), `tasks-behaviour-before-test/` (built with a multi-label task that is the first to name one of its obligations but not all of them, the only way C3 can fail), each a copy of `valid-minimal` with one defect
- [X] T027 [US1] Write `plan` check tests in `tests/test_trace.py`: `valid-minimal` exits 0; each T025 fixture exits 1 with the finding the contract names (missing section or commands table reported as a gap to resolve in planning; `C1 FR-nnn`; `C1 USn-ASm`; empty scenario, outcome, level or exemption reason; an `FR-`, `SC-` or `USn-ASm` id not in `spec.md`; an id whose prefix is none of those, `DC-` or `EC-`); the `DC-` and `EC-` ids in `valid-minimal` are accepted without being looked up; output is identical on two runs; `plan` creates or changes no file
- [X] T028 [US1] Write `tasks` check tests in `tests/test_trace.py`: `valid-minimal` exits 0; each T026 fixture exits 1 with `G1`, unknown-obligation, `C2` or `C3` findings naming the task or obligation; output is identical on two runs; `tasks` creates or changes no file
- [X] T029 [P] [US1] Add structural tests to `tests/test_manifests.py` for the three US1 wrappers and two addenda: each wrapper names `.specify/extensions/integrated-tdd/templates/tdd-process-rules.md` in full, begins with the check that the script exists and says the stage carries on as core Spec Kit when it does not, has text both above and below `{CORE_TEMPLATE}`, says what to do when `plan.md` has no Verification Plan (tasks and analyze), and names the subcommand it runs (`plan` for plan, `tasks` for tasks, both for analyze); `plan-addendum.md` holds the heading `## Verification Plan`, the three sub-headings and the three header rows exactly as contract section 1; `tasks-addendum.md` describes `[VO-nnn]` and `[NT: reason]`; no wrapper or addendum names a test framework, a CI system or a linter as required

### Implementation for User Story 1

- [X] T030 [US1] Implement the `plan` subcommand in `scripts/python/tdd_check.py` (trace checks: section and commands table present, C1, complete obligations and exemptions, known requirement ids) so T027 passes
- [X] T031 [US1] Implement the `tasks` subcommand in `scripts/python/tdd_check.py` (G1, known obligations, C2, C3) so T028 passes
- [X] T032 [P] [US1] Write `preset/templates/plan-addendum.md`: the Verification Plan section with its three tables and header rows from contract section 1, short guidance comments on each column, and the statement that the section holds no status
- [X] T033 [P] [US1] Write `preset/templates/tasks-addendum.md`: the label conventions and kind rules from contract section 2 with the three example task lines, and the statements that test tasks are required for behaviour and that every obligation needs a `test` task and at least one `behaviour` task, and the statement that the first task to name an obligation is its test task whatever its description says, so the test task must be written first
- [X] T034 [US1] Write the verification intent section of `templates/tdd-process-rules.md`: derive scenarios and expected outcomes from requirements, acceptance scenarios, edge cases and failure conditions (FR-006, FR-007); take interfaces, data integrity, security and integration boundaries from the design (FR-008); state outcomes without reference to the implementation (FR-010); choose a level per obligation and require no single level (FR-011); cover every `FR-` id and every acceptance scenario by an obligation or an exemption with a reason (FR-009); scale the number of obligations to scope, risk and complexity (FR-013); do not write all tests up front (FR-014); put material ambiguity or contradiction to the developer and plan nothing for it until answered (FR-015); take verification commands only from what the project already defines and raise a gap when none exists (FR-049, first edge case); for a feature already past planning, report the missing Verification Plan as a gap at the start and end of each later stage, carry on as core Spec Kit, and never describe its work as verified
- [X] T035 [US1] Write `preset/commands/speckit.plan.md` (wrap): above `{CORE_TEMPLATE}`, the missing-extension check, the instruction to read the rules file, and the statement that the plan must also fill the Verification Plan as a Phase 1 output; below it, the procedure to fill commands, obligations and exemptions, ask the developer about material ambiguity, leave the requirement without an obligation until it is answered and record the answer in `spec.md` Clarifications, run `tdd_check.py plan`, and not report the plan complete while it exits non-zero
- [X] T036 [US1] Write `preset/commands/speckit.tasks.md` (wrap): above `{CORE_TEMPLATE}`, the missing-extension check, the rules file, the statement that test tasks are not optional and override the core "Tests are OPTIONAL" wording, and the case of a `plan.md` with no Verification Plan (state the gap at the start and in the final report, name `/speckit-plan` as the remedy, then carry on as core Spec Kit without labels or checks); below it, label every task, generate a test task ahead of each behaviour task per obligation, run `tdd_check.py tasks`, and not report completion while it exits non-zero
- [X] T037 [US1] Write `preset/commands/speckit.analyze.md` (wrap): the missing-extension check and rules file above `{CORE_TEMPLATE}`; below it, run `tdd_check.py plan` and `tdd_check.py tasks`, include their findings in the analysis report, and modify nothing; where `plan.md` has no Verification Plan, report that as a gap and carry on as the core analysis. Makes T029 pass
- [X] T038 [US1] Validate the story and record the result in a new `## Validation results` section of `specs/001-integrated-tdd/quickstart.md`: in `<tmp>/proj` with both packages installed, run `specify preset resolve` for `plan-template`, `tasks-template`, `speckit.plan`, `speckit.tasks` and `speckit.analyze` and confirm the whole core content is present with the additions; take a small story through `/speckit-specify`, `/speckit-plan`, `/speckit-tasks` and `/speckit-analyze`; confirm `tdd_check.py plan` and `tdd_check.py tasks` exit 0 and the skill list is unchanged from the "before" listing

**Checkpoint**: Verification intent exists and is checked before implementation, through
the standard commands only

---

## Phase 4: User Story 2 - Implementation proceeds through Red → Green → Refactor with real evidence (Priority: P2)

**Goal**: The script runs declared commands and writes the evidence; the gate and the
runtime event refuse completion of a task without a valid failing run followed by a
passing run

**Independent Test**: With a fixture feature that has a Verification Plan and labelled
tasks, record a `red` then a `green` run through `tdd_check.py run`; `gate --task` passes
only then, and the `hook` refuses the `[ ]` to `[X]` edit before then

### Tests for User Story 2

- [X] T039 [P] [US2] Write command runner tests in `tests/test_run.py` using `tests/fixtures/bin/fake_test.sh` as the declared command: `red`, `green`, `refactor` and `checkpoint` each exit 2 and record nothing, with the record-a-baseline-first message, while the feature has no `baseline` record; each row of the contract's phase table (`baseline` always valid and exit 0; `red` valid only on non-zero exit with the `--expect` text present; `green`, `refactor` valid only on zero exit; `checkpoint` valid only for a `broad` command that exits zero); a `red` run that passes is recorded invalid with note `passed on first run: investigate`; a `red` run failing without the expected text is recorded invalid with note `failed for a different reason`; an undeclared `--command` exits 2 and records nothing; `--select` on a command without `{select}` exits 2; `--task`, `--vo`, `--tests` and `--expect` are required as the option table says and the obligations must be on the task; a run past `--timeout` is recorded as a failure with note `timed out`; only the last 40 lines of output are shown; a second declared command written in a different tool (`python3 -c` with an exit code and a message) is judged by exit status and expected text exactly as `fake_test.sh` is (FR-048)
- [X] T040 [US2] Write evidence ledger tests in `tests/test_run.py`: the first write creates `tdd-evidence.md` from the evidence template; `Seq` is contiguous from 1; the row cells match contract section 3; `Files` holds the `--tests` paths relative to the repository root, sorted and comma-separated, and `-` with no files; `Fingerprint` is the first six hex characters of the SHA-256 over sorted test file paths and contents and `-` with no files; `Check` chains from the previous row and excludes Classification and Note; a valid `red` row is classified `assertion` and its note begins `expected:`; other failures are `unclassified`; a vertical bar or line break in supplied text becomes a space; no test output beyond the matched text is stored; the feature directory and repository hold no new or changed file other than `tdd-evidence.md` after a run
- [X] T041 [P] [US2] Create gate fixtures under `tests/fixtures/features/`, one failing and one passing case each for G1, G3, G4 and G9 (`gate-g1-*`, `gate-g3-*`, `gate-g4-*`, `gate-g9-*`), each with a hand-built `tdd-evidence.md` whose check chain is valid
- [X] T042 [US2] Write gate tests in `tests/test_gate.py`: every T041 fixture gives the expected exit code and finding (for example `G3 T012 VO-004: no valid failing-first record and no exception`); a `test` task passes with a valid `red` record alone; a `no-test` task passes G3 and G4; `gate --all` applies the rules to completed tasks, reports each incomplete task and why it would not pass without failing on them; output is identical on two runs; `gate` creates or changes no file
- [X] T043 [P] [US2] Extend `tests/test_hook.py` to cover every row of the contract's situation table with the recorded payloads from T017 and fixture features, taking the `*-tasks.json` payloads as the base and varying only their edit strings and content per case: unguarded file exits 0 before any artefact is read; no Verification Plan exits 0; a guarded file in a feature other than the one `.specify/feature.json` names is guarded all the same; a `tasks.md` edit with no `[ ]` to `[X]` change exits 0; newly completed tasks that pass the gate exit 0; one that fails exits 2 with the findings and the two ways forward on standard error; `tdd-evidence.md` exits 2; an unreadable payload or artefact for a guarded file exits 2. Cover resulting-content computation for Edit (`old_string`, `new_string`, `replace_all`), MultiEdit (`edits` in order) and Write (`content`), lowercase `[x]`, and several tasks ticked in one edit
- [X] T044 [P] [US2] Add structural tests to `tests/test_manifests.py`: `templates/tdd-evidence-template.md` holds the title, the do-not-edit comment and the six section headings and header rows of contract section 3 with no data rows; `preset/commands/speckit.implement.md` meets the same wrapper rules as T029 and names the `run` and `gate` subcommands, and names no test framework, CI system or linter as required

### Implementation for User Story 2

- [X] T045 [P] [US2] Write `templates/tdd-evidence-template.md` as contract section 3 defines the empty document
- [X] T046 [US2] Implement the evidence ledger in `scripts/python/tdd_check.py`: create from the template, append a record row with sequence, UTC time, fingerprint and chained check value, sanitise cell text, write the Baseline row for `baseline` records, and rewrite the Summary section through one function that for now writes the generated-on line only (US5 fills it)
- [X] T047 [US2] Implement the command runner and the `run` subcommand in `scripts/python/tdd_check.py`: option validation, the baseline-first rule, `{select}` substitution, execution through the shell from the repository root with the timeout, validity per phase, the notes for invalid `red` runs, the last 40 lines to the caller, and exit codes. Makes T039 and T040 pass
- [X] T048 [US2] Implement gate rules G1, G3, G4 and G9 and the `gate --task` and `gate --all` subcommands in `scripts/python/tdd_check.py`, with each rule a separate function taking the parsed artefacts so later stories add rules without changing these. Makes T042 pass
- [X] T049 [US2] Complete `hook` in `scripts/python/tdd_check.py`: compute the resulting `tasks.md` content for Edit, MultiEdit and Write, find tasks changing from incomplete to complete, run the gate on each, and return the exit codes and messages of the situation table, failing closed for the two guarded files only. Makes T043 pass
- [X] T050 [US2] Write the Red, Green, Refactor section of `templates/tdd-process-rules.md`: write or update the test first (FR-017); state the expected failure text, then run `red` and proceed only on a valid record (FR-018); a first-run pass or a failure for another reason is investigated and is not a Red step; make the minimum change (FR-019); run `green` (FR-020); refactor and run `refactor` (FR-021); never state a result that did not come from `run` (FR-022); work in small increments, each verified before dependent work (FR-024, FR-025); select existing tests that cover the area alongside new ones (FR-027); run a `broad` command as a `checkpoint` at the end of each phase and not after every change (FR-028); resolve a failure before dependent work (FR-026); routine cycles involve no approval request (FR-053)
- [X] T051 [US2] Write `preset/commands/speckit.implement.md` (wrap): above `{CORE_TEMPLATE}`, the missing-extension check, the rules file, the statement that tasks are completed through the cycle and that marking a task `[X]` is refused until its gate passes, and the case of a `plan.md` with no Verification Plan (state the gap at the start and in the final report, carry on as core Spec Kit, record no evidence and never describe the work as verified); below it, the procedure: rerun `plan` and `tasks`, record a `baseline` with a `broad` command before the first task, follow the cycle per task through `run`, run `gate --task` before marking a task complete, record a `checkpoint` at the end of each phase, run `gate --all` at the end, and never edit `tdd-evidence.md` directly. Makes T044 pass
- [X] T052 [US2] Validate the hard stop (quickstart scenario 3) and record the result in `specs/001-integrated-tdd/quickstart.md` Validation results: in `<tmp>/proj`, with the feature from T038 and no evidence, ask Claude Code to mark the first behaviour task complete and to edit `tdd-evidence.md`; confirm both are refused with rule identifiers and the two ways forward and that `tasks.md` is unchanged; then confirm ticking a `[NT: reason]` task and editing an unrelated file succeed without delay; then record `red` and `green` through `run` and confirm the task can be marked complete

**Checkpoint**: The cycle is recorded from real executions and a task without evidence
cannot be marked complete

---

## Phase 5: User Story 3 - Passing tests cannot be achieved by weakening the verification (Priority: P3)

**Goal**: Any change to a test between its Red and Green runs fails the gate until it is
recorded as an Expectation Change with a requirement and, where it alters behaviour, an
approval

**Independent Test**: Record a `red` run, change the test file, record `green`: the gate
fails on G5. Record an `expectation` naming a requirement: the gate passes, unless
`--alters-behaviour` was given without an approval

**Depends on**: User Story 2 (ledger, runner, gate)

### Tests for User Story 3

- [X] T053 [P] [US3] Write tests in `tests/test_run.py` for fingerprints across the cycle and the `expectation` and `approve` subcommands: with `--tests` omitted, `green` and `refactor` read the files from the Files cell of the obligation's latest valid `red` record, which was made on a different task (the `test` task), and write the same Files cell on their own row; a changed or deleted test file gives a different fingerprint on the `green` row; naming two obligations whose `red` records list different files exits 2 and records nothing; with no valid `red` record for the obligation, Files and Fingerprint are `-`; `expectation` appends a row with id `XC-nn`, files, requirements, justification, alters-behaviour flag and the new fingerprint; it exits 2 without `--requirement`; `approve --id XC-nn --by <name>` fills Approved by, and exits 2 for an unknown id; after each subcommand the only file created or changed is the feature's `tdd-evidence.md`
- [X] T054 [P] [US3] Create fixtures `gate-g5-*` and `gate-g8-*` under `tests/fixtures/features/` and write tests in `tests/test_gate.py`: G5 fails when an obligation's latest `green` fingerprint differs from the fingerprint of its latest valid `red` record, made on the `test` task, with no Expectation Change; G5 does not apply to an obligation with no valid `red` record; G5 passes when an Expectation Change for the task carries the new fingerprint; G8 fails when an Expectation Change names no requirement, or alters behaviour with no approval; G8 passes once approved; a `test` task is not subject to G5

### Implementation for User Story 3

- [X] T055 [US3] Implement fingerprint reuse for `green` and `refactor` (files read back from the obligation's latest valid `red` record), the `expectation` subcommand and `approve` for Expectation Change ids in `scripts/python/tdd_check.py` so T053 passes
- [X] T056 [US3] Implement gate rules G5 and G8 in `scripts/python/tdd_check.py` so T054 passes
- [X] T057 [US3] Write the test integrity section of `templates/tdd-process-rules.md`: never remove, weaken, skip or bypass a test to obtain a pass (FR-029), which holds for every existing test and not only those the fingerprint covers: an existing test that starts failing is a regression to investigate (FR-027), and any change made to an existing test file is named in the stage's final report with its reason; assertions check a meaningful outcome and not that code ran (FR-030); tests agree with the approved requirements and design (FR-031); a test changed after its Red run is recorded with `expectation` against a requirement, and where it alters intended behaviour the developer approves before `approve` is recorded (FR-032); doubles must be able to produce the failures the real boundary can (FR-033); passing tests are not reported as proof while coverage is incomplete (FR-034); a requirement is never altered to pass, and a wrong requirement is raised for correction (FR-035)
- [X] T058 [US3] Add the expectation-change procedure to `preset/commands/speckit.implement.md` below `{CORE_TEMPLATE}`: on a G5 finding, decide whether the change corrects the test or alters intended behaviour, record `expectation`, ask the developer where it alters behaviour, and record `approve` only after the developer has approved in the conversation

**Checkpoint**: A green suite reached by changing a test is visible and gated

---

## Phase 6: User Story 4 - Blocked, failed and impractical cases are handled openly (Priority: P4)

**Goal**: Failures are classified, departures from the cycle are recorded as exceptions
with a rationale and an alternative, and a person's outstanding decision holds back only
the tasks that depend on it

**Independent Test**: With fixture features, an `unclassified` failure blocks its task
until `classify`; an `exception` with a rationale and alternative replaces the Red
requirement but not the passing run; an `environment-blocked` exception leaves the task
incomplete; a task on an open decision fails G2 while other tasks pass

**Depends on**: User Story 2 (ledger, runner, gate)

### Tests for User Story 4

- [X] T059 [P] [US4] Write tests in `tests/test_run.py` for the `classify`, `exception`, `decision` and `approve` subcommands: `classify` sets `assertion`, `defect`, `environment` or `unreliable` on an `unclassified` failure, may extend the note, leaves the row's check value unchanged, and exits 2 for a pass or an already classified row; `exception` appends `EX-nn` with every kind in the data model, exits 2 without `--rationale`, and without `--alternative` for every kind except `environment-blocked`; it records Needs approval as yes without `--needs-approval` for the kinds `legacy`, `exploratory` and `other` and for an alternative of `none`, and only when flagged for the other kinds; `decision open` appends `DN-nn` as `open` with its tasks; `decision resolve` requires `--answer` and `--by`; `approve` fills Approved by on an `EX-nn` id; after each subcommand the only file created or changed is the feature's `tdd-evidence.md`
- [X] T060 [P] [US4] Create fixtures `gate-g2-*`, `gate-g6-*`, `gate-g7-*` and `gate-exception-*` under `tests/fixtures/features/` and write tests in `tests/test_gate.py`: G2 fails for a task on an open Decision and passes for a task not listed and after resolution; G6 fails when the task's latest record is a failure or any failure record is `unclassified`, and passes for a `test` task whose latest record is its valid `red` record; a record classified `unreliable` never counts as valid for G3 or G4; G3 passes for both the `test` task and the `behaviour` task of an obligation when one Exception raised on either of them names the obligation; an Exception that names no obligation covers only the task it was raised on; G4 still requires a later valid passing record; a `behaviour-preserving` exception needs a passing `baseline` or `green` record before and a passing `refactor` record after on the same selector; an `environment-blocked` exception lets no task that names the obligation pass; G7 fails, for every task naming an obligation the exception covers, for an exception with no rationale, no alternative where required, or `needs_approval` with no approver; G7 also fails for a kind of `legacy`, `exploratory` or `other`, or an alternative of `none`, with no approver even when the row is not flagged

### Implementation for User Story 4

- [X] T061 [US4] Implement the `classify`, `exception` and `decision open` and `decision resolve` subcommands, and `approve` for Exception ids, in `scripts/python/tdd_check.py` so T059 passes
- [X] T062 [US4] Implement gate rules G2, G6 and G7, exception coverage in G3 and G4, the `behaviour-preserving` and `environment-blocked` rules, and the `unreliable` rule in `scripts/python/tdd_check.py` so T060 passes
- [X] T063 [US4] Write the failures, exceptions and decisions section of `templates/tdd-process-rules.md`: investigate each failure and classify it as assertion, defect, environment or unreliable, and say which (FR-036); report blocked tests and unresolved failures as such and never as verified (FR-037, FR-040); when a meaningful first failure cannot be shown, record an exception with the reason and the alternative verification (FR-023, FR-038); the exception kinds and the verification suited to legacy code, external systems, generated code, migrations, infrastructure and exploratory work (FR-039); a behaviour-preserving change runs existing tests before and after and addresses thin coverage first; tests that cannot be run at all are a blocking condition and no result is claimed; ask the developer when a trade-off is consequential or an exception exceeds the agent's authority, which it always does for the kinds `legacy`, `exploratory` and `other` and when no alternative verification is offered; set `--needs-approval` for any other kind judged consequential, and open a Decision listing the affected task and every task depending on it (FR-052); continue with tasks not listed, report the open decision and what is held, never proceed on an assumed answer, and stop when every remaining task depends on it (FR-065); explain each in terms a developer can assess (FR-051)
- [X] T064 [US4] Add the failure, exception and decision procedure to `preset/commands/speckit.implement.md` below `{CORE_TEMPLATE}`: classify after investigating, record exceptions and decisions through the script, hold only the listed tasks, and report blocked and failed items explicitly in progress and final reports

**Checkpoint**: Departures from the cycle are recorded, gated and reported as what they are

---

## Phase 7: User Story 5 - Reviewers can see what was verified, what was not, and why (Priority: P5)

**Goal**: The Summary at the top of `tdd-evidence.md` and the `status` subcommand show,
per obligation, its requirements, derived status, tests and latest result, then
everything not verified and why

**Independent Test**: Run `tdd_check.py status` on fixture features in each state; the
view matches the data model's status table, and after any recording subcommand the
Summary in `tdd-evidence.md` shows the same content

**Depends on**: User Story 2 (ledger). Shows exceptions, expectation changes and
decisions once User Stories 3 and 4 exist

### Tests for User Story 5

- [X] T065 [P] [US5] Create fixtures `status-planned/`, `status-in-progress/`, `status-verified/`, `status-verified-by-exception/`, `status-blocked-environment/`, `status-blocked-decision/`, `status-failed/` and `status-preexisting-failure/` under `tests/fixtures/features/`
- [X] T066 [US5] Write tests in `tests/test_status.py`: each T065 fixture gives the derived status of the data model's table; `status` lists each obligation with requirements, status, selectors of its records as tests and latest result as `pass (#n)` or `fail (#n)`; it lists unverified requirements with the reason, exemptions, exceptions, expectation changes, open decisions and pre-existing failures from the baseline; an obligation with origin `discovered` is shown like any other; `status` exits 0 whenever the artefacts can be read; `status --json` carries the same content; output is identical on two runs; `status` creates or changes no file; after `run`, the Summary section of `tdd-evidence.md` holds the same table and lists, and holds nothing that is not derivable from the tables beneath it and `plan.md`

### Implementation for User Story 5

- [X] T067 [US5] Implement derived obligation status and the Review Evidence view in `scripts/python/tdd_check.py`, as one function used by both the `status` subcommand and the Summary writer from T046, so T066 passes
- [X] T068 [US5] Write the traceability and review evidence section of `templates/tdd-process-rules.md`: a scenario discovered during implementation is added to the plan's obligations table with origin `discovered`, its requirements, and a task label before its test is written (FR-016); when a requirement, design decision or implementation changes, update the affected obligations, tasks and tests and rerun `plan` and `tasks` (FR-044); do not copy test output, coverage reports or CI results into the artefacts (FR-045); explain significant testing decisions, unexpected failures and exceptions so a developer can assess them (FR-051, FR-054)
- [X] T069 [US5] Add the end-of-stage report to `preset/commands/speckit.implement.md` below `{CORE_TEMPLATE}`: after `gate --all`, run `status` and report what is verified, what is not and why, list blocked and failed items, exceptions, expectation changes and open decisions, and state that passing tests do not show that unverified requirements are met (FR-034) and do not stand in for linting, static analysis, security checks or other required validation (FR-047)

**Checkpoint**: A reviewer can answer "is this requirement verified, by what, with what
result" from `tdd-evidence.md` and `plan.md` alone

---

## Phase 8: User Story 6 - The process fits the project it is installed into (Priority: P6)

**Goal**: The packages use the project's own commands, assume no framework, leave other
controls and Spec Kit components untouched, and install and remove cleanly

**Independent Test**: Quickstart scenarios 2 and 5 in throwaway projects: settings and
skill list return to their "before" state after removal, both presets compose on
`speckit.plan`, and the suite proves the script reads nothing framework-specific and
writes only `tdd-evidence.md`

**Depends on**: User Stories 1 and 2 (the wrappers and the event being installed)

### Tests for User Story 6

This story's automated tests are written with the code they guard, so that each is seen to
fail first: framework neutrality in T039; writing nothing but `tdd-evidence.md` in T027,
T028, T040, T042, T053, T059, T066 and T077; standard library imports in T009; the agent
adapter mapping in T010; `.extensionignore` and agent-neutral rules in T008; wrappers that
name no framework in T029 and T044. T070 to T072 are not used.

### Implementation for User Story 6

- [X] T073 [US6] Write the fitting-the-project section of `templates/tdd-process-rules.md`: use only the project's declared verification commands and follow its conventions for test location and naming (FR-049); never install or choose a test framework, edit test, lint or CI configuration, or add a check the project already runs (FR-046, FR-048, FR-050); passing tests do not satisfy other required validation (FR-047)
- [X] T074 [US6] Write the install, removal, changes-to-existing-behaviour and known-limits sections of `README.md`: the two install commands in order (extension, then preset) and the two removal commands; the five behaviour changes from contracts/artefact-formats.md section 4 with the reason for each (FR-004); the limits recorded in plan.md and research.md (shell edits to `tasks.md` bypass the event, the approver's name is not verified, removing the Verification Plan heading from `plan.md` stops the event guarding that feature, a command added to the Verification commands table counts as declared whatever it runs, only test files named on a failing-first record are fingerprinted so a change to another existing test is not detected by a check, the check value is not a signature, full enforcement on Claude Code only, Windows untested); and any fallback recorded in T020
- [ ] T075 [US6] Run quickstart scenario 2 (installation and registration) in a fresh `<tmp>/proj3` and scenario 5 (coexistence with `c4` and `c4-model` in both priority orders, then removal, then the preset left installed with the extension absent, where `/speckit-plan` must say the extension is missing and complete as core Spec Kit would; and, with both installed, a feature whose `plan.md` has no Verification Plan, where `/speckit-tasks` and `/speckit-implement` must state the gap at start and end and complete as core Spec Kit would) and record each expected outcome as met or not in `specs/001-integrated-tdd/quickstart.md` Validation results; fix any difference in `extension.yml`, `preset.yml` or the wrappers

**Checkpoint**: Installing and removing leave the project as it was, and nothing in the
packages assumes a language or framework

---

## Phase 9: User Story 7 - The extension's effectiveness can be evaluated (Priority: P7)

**Goal**: An evaluator has example stories with defined expected behaviour and a
compliance check that tells a run that followed the process from one that only added
tests

**Independent Test**: `tdd_check.py compliance --feature-dir examples/runs/compliant`
prints `COMPLIANT` and exits 0; the same on `examples/runs/tests-only` prints
`NON-COMPLIANT` with reasons and exits 1; each gives identical output on a second run

**Depends on**: User Stories 1 to 5 (the compliance check applies their rules, and the
compliant run is produced with their subcommands)

### Tests for User Story 7

- [X] T076 [P] [US7] Create fixtures `compliance-c1-*` to `compliance-c7-*` under `tests/fixtures/features/`, one failing and one passing case per rule, including a hand-edited record row for C4, a failing latest checkpoint with and without a failing baseline of the same command and a record table whose first row is not a `baseline` for C6, and for C7 a `failed` and a `blocked` obligation (reported and not reported in the Summary) a `planned` and an `in progress` obligation, which fail however they are reported, and a Summary left out of date by an obligation added to `plan.md` after the last record, which fails until a recording run rewrites it
- [X] T077 [US7] Write tests in `tests/test_compliance.py`: each T076 fixture gives the expected verdict and finding by rule id; `examples/runs/compliant` is `COMPLIANT` with exit 0; `examples/runs/tests-only` is `NON-COMPLIANT` with exit 1 and findings that include missing failing-first records and no C4 finding; two runs on the same directory give byte-identical output (SC-011); `compliance` writes nothing

### Implementation for User Story 7

- [X] T078 [US7] Implement the `compliance` subcommand and rules C4, C6 and C7 in `scripts/python/tdd_check.py`, reusing the C1 to C3 trace checks and the G1 to G9 gate functions for C5, so the T076 fixture tests pass
- [ ] T079 [US7] Produce `examples/runs/compliant/` and `examples/runs/tests-only/`, each with `spec.md`, `plan.md`, `tasks.md` and `tdd-evidence.md` for the same small feature. Keep the tiny sample project both runs come from in `examples/runs/sample-project/`. Build the compliant run by really working that project through `run`, `gate` and a `checkpoint` with the script, so its evidence comes from real executions, then copy the four artefacts in. Build the tests-only run by recording a `baseline` and then only `green` runs through the script, so its check chain is valid, with every task marked complete and no `red` records, exceptions or checkpoint. Add a `README.md` in `examples/runs/` saying how each was made. Makes the rest of T077 pass
- [ ] T080 [P] [US7] Write the seven example stories in `examples/stories/` as `01-normal-development.md`, `02-regression.md`, `03-material-ambiguity.md`, `04-test-failure.md`, `05-justified-exception.md`, `06-weakening-is-the-easy-route.md` and `07-small-low-risk-change.md`. Each holds the story text to give `/speckit-specify`, any setup the evaluator must do first (for example an existing failing condition or an unreachable dependency), and the expected process behaviour from quickstart scenario 4 as a checklist of observable items in the artefacts and evidence
- [ ] T081 [P] [US7] Write `docs/evaluation.md`: how to drive each story through the six standard commands by hand, how to run `compliance` and `status` and read their output, what a compliant verdict does and does not show, and how the record columns (time, task, phase, result, classification) and the exception and expectation-change tables support later comparison of review effort, escaped defects, test reliability and rework against baseline data (FR-058)
- [ ] T082 [US7] Add the observable criteria for successful operation to `README.md` (FR-055): the criteria an evaluator can check from the artefacts, each tied to a success criterion SC-001 to SC-011, with a pointer to `docs/evaluation.md` and `examples/`, and the statement that the compliance check is an evaluation aid and not a step in normal work (FR-064)

**Checkpoint**: All user stories are functional and the extension can be assessed

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Performance, portability, and the full validation the constitution's four
test levels require

- [ ] T083 [P] Write performance tests in `tests/test_performance.py` with a generated feature of 200 tasks and 1,000 evidence records: `hook` on a `tasks.md` completion decides in under 1 second; `hook` on an unguarded file returns without opening any artefact; `plan`, `tasks`, `gate --all`, `status` and `compliance` each finish in under 2 seconds. These tests measure code that already exists and are expected to pass at once (plan.md, Constitution Check IV, second exception): before accepting each one, run it once against a generated feature large enough to exceed its limit, confirm it fails on the time limit, and record that run in `specs/001-integrated-tdd/quickstart.md` Validation results. Correct `scripts/python/tdd_check.py` where a limit is missed
- [ ] T084 Run the suite on the oldest supported interpreter with `uv run --python 3.9 python -B -m unittest discover -s tests` and correct anything in `scripts/python/tdd_check.py` or `tests/` that needs a later version
- [ ] T085 Run quickstart scenario 1 in full (`python3 -B -m unittest discover -s tests`, `uvx ruff check .`, `npx -y markdownlint-cli2`), fix every finding, and record the result in `specs/001-integrated-tdd/quickstart.md` Validation results
- [ ] T086 Run quickstart scenario 4 by hand in three throwaway projects that differ in language and test framework, each with lint and CI configuration in place, taking every story in `examples/stories/` through the six standard commands in the first project, and stories 01 (normal development), 05 (justified exception) and 07 (small low-risk change) in each of the other two, 13 runs in all; record per project and story the compliance verdict, whether any other command was needed, whether the plan's commands are the project's own, whether test, lint and CI configuration are untouched, whether the project's lint and other quality commands, run before `/speckit-specify` and again after `/speckit-implement`, still run and still gate as they did before, how many approval requests were made during routine cycles, and whether any test changed after its Red run without a recorded Expectation Change, in `specs/001-integrated-tdd/quickstart.md` Validation results (SC-002, SC-004, SC-007, SC-008, SC-009, SC-010)
- [ ] T087 Have a person who took no part open one finished feature from T086 and answer, for three requirements chosen at random, whether each is verified, by which tests and with what result; record the time taken for each against the 2 minute limit in `specs/001-integrated-tdd/quickstart.md` Validation results (SC-005)
- [ ] T088 Correct `templates/tdd-process-rules.md` and the wrappers under `preset/commands/` for any story in T086 where the agent's behaviour differed from the expected behaviour, then rerun that story and update its recorded result
- [ ] T089 [P] Complete `CHANGELOG.md` for 0.1.0 and check `README.md` against the final behaviour, the outcomes in research.md Installation test results, and the plan's Complexity Tracking in `specs/001-integrated-tdd/plan.md`
- [ ] T090 Replay this project's Red-before-Green history and record the result in `specs/001-integrated-tdd/quickstart.md` Validation results (Constitution Principles III and IV). For the commit of each test task (T008 to T010, T022, T027 to T029, T039, T040, T042 to T044, T053, T054, T059, T060, T066 and T077; not T083, whose tests are not fail-first by recorded exception), check that commit out into a temporary `git worktree` under `<tmp>`, run `python3 -B -m unittest discover -s tests`, and confirm the tests its message names fail for the reason the message gives; then check out the implementation commit that its tests were written for and confirm they pass. Record for each pair the two commits, the tests, what was observed and whether it matches the messages. Report any mismatch to the developer; do not rewrite history to correct it. Run last, after every other task's commits exist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup. Blocks every user story. T020 is a stop
  point: a failed A1 returns the plan to the developer
- **User Story 1 (Phase 3)**: depends on Foundational only
- **User Story 2 (Phase 4)**: its script and test tasks (T039 to T050) depend on
  Foundational only, because their tests use fixture plans and task lists. T051 and T052
  follow User Story 1: the procedure T051 writes calls the `plan` and `tasks` subcommands
  from T030 and T031, and T052 uses the feature produced in T038
- **User Story 3 (Phase 5)** and **User Story 4 (Phase 6)**: each depends on User Story 2.
  Independent of each other
- **User Story 5 (Phase 7)**: depends on User Story 2. Its fixtures for exceptions and
  decisions are hand-built, so it can precede User Stories 3 and 4
- **User Story 6 (Phase 8)**: depends on User Stories 1 and 2
- **User Story 7 (Phase 9)**: depends on User Stories 1 to 5
- **Polish (Phase 10)**: depends on every story. T086 to T088 need a person

```text
Setup → Foundational ─┬─ US1 ────────────────┬─ US6 ─┐
                      └─ US2 ─┬─ US3 ─┐      │       ├─ Polish
                              ├─ US4 ─┼─ US7 ┘───────┘
                              └─ US5 ─┘
```

### Within Each User Story

- Fixtures, then tests, then confirm the tests fail, then implementation
- Script changes before the rules section and wrapper text that describe them
- The story's validation task last

### Shared files

Six files are changed by several stories, so tasks on them are never parallel with each
other, across stories as well as within one:

- `scripts/python/tdd_check.py`: every implementation task
- `templates/tdd-process-rules.md`: T024, T034, T050, T057, T063, T068, T073
- `preset/commands/speckit.implement.md`: T051, T058, T064, T069
- `README.md`: T074, T082, T089
- `specs/001-integrated-tdd/quickstart.md` (Validation results): T038, T052, T075, T083,
  T085, T086, T087, T090
- `specs/001-integrated-tdd/research.md` (Installation test results): T016, T018, T019

`tests/test_run.py`, `tests/test_gate.py`, `tests/test_hook.py` and
`tests/test_manifests.py` are also extended by several stories; within a story their tasks
are marked [P] only against tasks in other files.

### Parallel Opportunities

- Setup: T002, T003, T004 and T007 together
- Foundational: T008, T009 and T010 together; T018 alongside T017; T019 after T018, because
  both record in `research.md`; T021 alongside the installation tests
- User Story 1: T025, T026 and T029 together; T032 and T033 together
- User Story 2: T039, T041, T043 and T044 together; T045 alongside any script task
- User Stories 3, 4 and 5: the two test tasks of each story together. The stories
  themselves interleave only on the shared files above
- User Story 7: T080 and T081 together, alongside T078 and T079
- Polish: T083 and T089 together. T084 follows T083, because both may correct the script.
  T090 is last

---

## Parallel Example: User Story 2

```bash
# Tests and fixtures in different files, written together and seen to fail:
Task: "Write command runner tests in tests/test_run.py"
Task: "Create gate fixtures under tests/fixtures/features/ for G1, G3, G4 and G9"
Task: "Extend tests/test_hook.py to cover every row of the situation table"
Task: "Add structural tests to tests/test_manifests.py for the evidence template and implement wrapper"

# Then, alongside the first script task:
Task: "Write templates/tdd-evidence-template.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational, stopping at T020 if A1 fails
3. Phase 3: User Story 1
4. **Stop and validate** with T038: verification intent is produced and checked by the
   standard plan and tasks commands

User Story 1 alone delivers planned verification but no enforcement during
implementation. The first increment that delivers the feature's central promise is User
Stories 1 and 2 together.

### Incremental Delivery

1. Setup and Foundational: mechanisms proven, packages install
2. User Story 1: intent derived and checked (MVP)
3. User Story 2: the cycle, real evidence and the hard stop
4. User Story 3: test integrity. User Story 4: failures, exceptions, decisions
5. User Story 5: the reviewer's view
6. User Story 6: installation, removal and coexistence validated, README
7. User Story 7: example stories and the compliance check
8. Polish: performance, Python 3.9, the person-driven scenarios

### Parallel Team Strategy

Because all rule logic is one module, parallel work is limited. After User Story 2, one
developer can take the script tasks of User Stories 3, 4 and 5 in order while a second
writes fixtures, tests, rules sections, the example stories and the documentation.

---

## Notes

- This task list carries no `[VO-nnn]` or `[NT: reason]` labels: the feature that defines
  them is what is being built, and this repository does not have it installed
- Tasks T016 to T019, T038, T052, T075 and T086 to T088 drive Claude Code or the `specify`
  CLI in throwaway projects and cannot be completed by unit tests
- SC-012 needs feedback from trial use and has no task here
- Commit after each task. Test tasks and the implementation tasks that satisfy them are
  never combined in one commit (see Conventions for every test task)
- Stop at any checkpoint to validate the story on its own
