# Quickstart: validating Integrated TDD

**Feature**: `001-integrated-tdd` | **Plan**: [plan.md](./plan.md)

How to prove the feature works once it is built. The scenarios follow the constitution's
four test levels. Formats and commands are defined in the contracts and are not repeated
here: [check script](./contracts/check-cli.md),
[artefact formats](./contracts/artefact-formats.md),
[packaging](./contracts/packaging.md).

## Prerequisites

- Spec Kit CLI 1.0.2.dev0 or later (`specify version`)
- Python 3.9 or later
- Claude Code, for scenarios 3 to 5
- `uvx` and `npx`, for the linters only

`<repo>` is the absolute path of this repository. `<tmp>` is a throwaway directory outside
it. Never install into this repository's own `.specify/`.

## 1. Automated tests (structural and behavioural, no agent)

```bash
cd <repo>
python3 -B -m unittest discover -s tests
uvx ruff check .
npx -y markdownlint-cli2
```

**Expected**: all tests pass and both linters report nothing. The suite covers:

| Area | What is proved |
|------|----------------|
| Parsing | The Verification Plan, task labels and evidence tables are read as the artefact contract defines, including malformed input |
| `plan` and `tasks` checks | Each rule fails on a fixture that breaks it and passes on one that does not |
| `run` | A real subprocess is executed; valid and invalid Red, Green, Refactor and checkpoint outcomes are recorded as the contract's table says; an undeclared command records nothing |
| Gate | Each of G1 to G9 has a failing and a passing fixture |
| `hook` | Each row of the hook contract's situation table, using recorded Claude Code payloads |
| Compliance | `examples/runs/compliant/` is reported compliant and `examples/runs/tests-only/` non-compliant, and two runs on the same files give identical output (SC-011) |
| Manifests | `extension.yml` and `preset.yml` are well formed (read by pattern; loading by Spec Kit is proved in scenario 2), every file they name exists, and every wrapper contains `{CORE_TEMPLATE}` |

## 2. Installation and registration

```bash
specify init <tmp>/proj --integration claude
cd <tmp>/proj
cp .claude/settings.json <tmp>/settings.before.json 2>/dev/null || echo '{}' > <tmp>/settings.before.json
ls .claude/skills > <tmp>/skills.before.txt

specify extension add --dev <repo>
specify preset add --dev <repo>

specify extension list
specify preset list
specify preset resolve plan-template
specify preset resolve tasks-template
specify preset resolve speckit.plan
specify preset resolve speckit.tasks
specify preset resolve speckit.analyze
specify preset resolve speckit.implement
ls .claude/skills | diff <tmp>/skills.before.txt -
```

**Expected**:

- Both packages are listed as installed and enabled.
- `plan-template` ends with the Verification Plan section, and `tasks-template` with the
  label conventions.
- Each resolved command contains the whole core command with the wrapper's text around it.
- The skill list is unchanged: no new skill exists (SC-002).
- `.claude/settings.json` has one `PreToolUse` entry that was not in
  `<tmp>/settings.before.json`, and nothing else differs.

Research assumptions A1 to A9 are settled earlier, by the installation tests in tasks T016
to T019. This scenario repeats the checks for A4 and A9 on the finished packages.

## 3. The hard stop (research assumption A1)

In `<tmp>/proj`, with a feature that has a Verification Plan and a labelled `tasks.md` but
no evidence, ask Claude Code to mark the first behaviour task complete.

**Expected**: the edit is refused. The agent is shown the gate's findings by rule
identifier and told the two ways forward. `tasks.md` is unchanged. Asking the agent to edit
`tdd-evidence.md` directly is also refused.

Then tick a `[NT: reason]` task, and edit an unrelated file.

**Expected**: both succeed without delay.

## 4. Behavioural: the lifecycle on representative stories

Do this in three throwaway projects that differ in language and test framework, each with
its own lint and CI configuration already in place (SC-008). In the first project take
every story in `examples/stories/` (SC-010). In the other two take normal development,
justified exception and small low-risk change, the stories most sensitive to language and
test framework. That is 13 runs. For each, run the standard commands only:

```text
/speckit-specify <story>
/speckit-clarify
/speckit-plan
/speckit-tasks
/speckit-analyze
/speckit-implement
```

Then check the run:

```bash
python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py compliance
python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py status
```

**Expected for every run**: no command other than those six was needed; the compliance
check reports `COMPLIANT`; the verification commands in the plan are the project's own; the
project's test, lint and CI configuration are untouched; and the project's lint and other
quality commands, run before the first command and again after the last, still run and
still gate as they did before (SC-009).

**Expected per story**, as each story's own file defines in full:

| Story | Expected behaviour |
|-------|--------------------|
| Normal development | Every obligation shows a valid failing-first record before a passing one. No approval was requested (SC-007) |
| Regression | An existing test fails after a change. The failure is classified, fixed and rerun; the test itself is unchanged |
| Material ambiguity | Planning stops to ask the developer about the ambiguity. Nothing is planned for it until answered, so the `plan` check fails and the plan is not reported complete. The answer is recorded in the specification's Clarifications before the obligation is written. No Decision is recorded: those belong to the implementation stage |
| Test failure | An environment failure is classified as environmental and reported as blocked. The task is not marked complete and the final report does not call it verified |
| Justified exception | A change unsuited to test-first has an Exception with a rationale and an alternative verification. Where the trade-off is consequential the developer is asked |
| Weakening is the easy route | The agent does not alter the test to pass. Any change to a test after its Red run appears as an Expectation Change with a requirement and, where behaviour changes, an approval (SC-004) |
| Small, low-risk change | A change to one existing behaviour, such as a default value. The plan holds one obligation per requirement and acceptance scenario and no more, at one testing level, with no exemption or exception that a larger change would not also need. No approval was requested, and the same commands were used (FR-013, US1-AS5) |

A reviewer who took no part then opens `tdd-evidence.md` and answers, for three
requirements chosen at random, whether each is verified, by which tests and with what
result.

**Expected**: each answer in under 2 minutes from the artefacts alone (SC-005).

## 5. Regression and removal

In a project that also has the `c4` extension and `c4-model` preset installed:

```bash
specify preset resolve speckit.plan
specify preset set-priority integrated-tdd 5
specify preset resolve speckit.plan
```

**Expected**: both presets' additions are present in the composed plan command in either
order, and `/speckit-plan` produces both `architecture.md` and the Verification Plan.

Then remove:

```bash
specify preset remove integrated-tdd
specify extension remove integrated-tdd
diff <tmp>/settings.before.json .claude/settings.json
ls .claude/skills | diff <tmp>/skills.before.txt -
specify preset resolve speckit.implement
```

**Expected**: the settings file and skill list match their state before installation, the
implement command is the core command again, existing feature directories are untouched,
and `/speckit-plan` on a new feature works as core Spec Kit does (FR-003).

In a further throwaway project, leave the preset installed with the extension absent:
remove the extension first, or add the preset alone where Spec Kit allows it. Run
`/speckit-plan` on a small story.

**Expected**: the wrapper says the extension is missing, and the stage completes as core
Spec Kit would.

With both packages installed, take a feature whose `plan.md` was written without a
Verification Plan and run `/speckit-tasks` and `/speckit-implement`.

**Expected**: each stage states the gap at its start and in its final report, names
`/speckit-plan` as the remedy, completes as core Spec Kit would, and does not describe the
work as verified.

## What these scenarios do not prove

- Scenario 4 is run by a person. A passing compliance check shows the recorded process was
  followed; it does not show that the tests' assertions are meaningful, which a reviewer
  judges.
- SC-012 needs feedback gathered from trial use and is not covered here.
- Reductions in review effort, escaped defects and rework need baseline data the adopting
  team holds, and are outside this feature.

## Validation results

Results of running the scenarios above while the feature was built. Each entry names the
task that produced it. `<tmp>/proj` is a throwaway project created with
`specify init --integration claude` (Spec Kit CLI 1.0.2.dev0, Claude Code 2.1.296, Linux),
holding a small Python library with its own `make test` and `make lint`.

### User Story 1: verification intent before implementation (T038, 2026-10-10)

Both packages were installed with `--dev` from this repository.

| Check | Expected | Observed | Met |
|-------|----------|----------|-----|
| `specify preset resolve plan-template` and `tasks-template` | Core template with the addendum appended | Chain: core, then `integrated-tdd` append. The composed plan template holds every core section and ends with `## Verification Plan` and its three tables; the composed tasks template ends with `## Verification labels` | Yes |
| `specify preset resolve speckit.plan`, `speckit.tasks`, `speckit.analyze` | Whole core command with the wrapper's text around it | Chain: core, then `integrated-tdd` wrap. Each composed skill holds the core command once (plan 170 core lines in 241, tasks 219 in 284, analyze 255 in 313), the note above it and the added section below it, and no `{CORE_TEMPLATE}` token | Yes |
| `/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-analyze` on a small story (a cart total with an empty-cart and a negative-price rule), run through `claude -p`, no other command | Verification Plan and labelled tasks produced by the standard commands | The plan held two commands taken from the project's README and Makefile (`python3 -m unittest {select}`, `make test`), 12 obligations and no exemptions. The task list held 25 tasks: a test task ahead of each behaviour task for every obligation, and one `[NT: reason]` task. The analysis report had a "Verification coverage" section quoting both checks, and `git status` showed analyze changed no file | Yes |
| `tdd_check.py plan` | Exit 0 | `plan: passed`, exit 0 | Yes |
| `tdd_check.py tasks` | Exit 0 | `tasks: passed`, exit 0, after the correction below | Yes |
| Skill list against the "before" listing | Unchanged | Identical | Yes |

Two defects were found and corrected:

- The generated `tasks.md` keeps the "Verification labels" section, whose three example
  task lines sit in a fenced code block. The parser read them as tasks `T011` to `T013`, a
  second use of those ids. Tests were added and seen to fail (commit `3fded87`), then the
  parser was changed to skip fenced code blocks and the `tasks` check to report a task id
  used twice (commit `268f62b`).
- The wrappers wrote `/__SPECKIT_COMMAND_PLAN__`, which Spec Kit expanded to
  `//speckit-plan`, because the token already carries the slash. The wrappers now use the
  bare token.

### User Story 2: the hard stop, scenario 3 (T052, 2026-10-10)

In `<tmp>/proj`, with the feature from T038 (a Verification Plan, labelled tasks, no
evidence) and the finished packages reinstalled. Claude Code was run with `claude -p`,
edits accepted and the shell tool disallowed, and told not to retry or work round a
refusal.

| Step | Expected | Observed | Met |
|------|----------|----------|-----|
| Mark the first behaviour task (`T003`, `[VO-001]`) complete with Edit | Refused, with rule identifiers and the two ways forward; `tasks.md` unchanged | Refused. The agent was shown `G3 T003 VO-001: no valid failing-first record and no exception`, `G4 T003 VO-001: no valid passing record after its failing-first record` and the two ways forward. `tasks.md` was unchanged | Yes |
| Write `tdd-evidence.md` with Write | Refused | Refused with "Evidence is written only by the check script" and the subcommand to use. No file was created | Yes |
| Tick the `[NT: reason]` task (`T025`) | Succeeds without delay | Succeeded | Yes |
| Edit an unrelated file (`README.md`) | Succeeds without delay | Succeeded | Yes |
| `run --phase red` before any baseline | Exit 2, nothing recorded | Exit 2 with the record-a-baseline-first message; no evidence document was created | Yes |
| `run --phase baseline --command suite` (`make test`) | Recorded, valid | `recorded #1: baseline suite: pass, valid` | Yes |
| Write the test, then `run --phase red` on the test task `T002` with the expected failure text | Recorded as a valid failing-first record | `recorded #2: red unit-one: fail, valid`. `gate --task T002` passed; `gate --task T003` failed on G4 only | Yes |
| Implement, then `run --phase green` on `T003` | Recorded, valid; the gate passes | `recorded #3: green unit-one: pass, valid`; `gate T003: passed` | Yes |
| Mark `T002` and `T003` complete with Edit | Both succeed | Both succeeded | Yes |
