# Integrated TDD process rules

These rules name no coding agent. They apply to whichever agent carries out the Spec Kit
lifecycle, and to the developer who remains accountable for the result.

## Purpose and how the wrapped commands use these rules

The plan, tasks, analyze and implement stages of Spec Kit are extended so that
verification is derived from requirements before implementation, implementation proceeds
through Red, Green, Refactor with evidence from real test runs, and a task cannot be marked
complete without that evidence. No command is added: each extended stage tells the agent to
read this file first and then follow its own procedure.

Two things do the work:

- **These rules**, which the agent follows and a reviewer can hold it to.
- **The check script**, `.specify/extensions/integrated-tdd/scripts/python/tdd_check.py`,
  which checks what can be checked objectively, runs the project's declared test commands
  and writes the evidence. Run it from the repository root. A check that fails blocks the
  work it guards; it is never downgraded to a note.

Verification intent is kept in the feature's `plan.md` (the Verification Plan section) and
`tasks.md` (task labels). Evidence is kept in `tdd-evidence.md` in the feature directory,
which only the check script writes.

## Verification intent

Verification is decided from the requirements and the design, before implementation, and
recorded in the plan's Verification Plan. It is not invented while the code is written.

**Where it comes from.**

- Derive verification scenarios and their expected outcomes from the specification: its
  functional requirements, acceptance scenarios, edge cases and failure conditions
  (FR-006, FR-007).
- Take interfaces, data integrity rules, security requirements and integration boundaries
  from the design, and reflect them in the scenarios and in the levels chosen (FR-008).
  Give a design constraint a `DC-nn` label and an edge case an `EC-nn` label, and state it
  in the obligation's Scenario cell.
- State each expected outcome as what must be observed, without reference to how the code
  will be written (FR-010). "The total is zero and no error is raised" is an outcome;
  "the loop returns early" is not.

**Coverage.**

- Every `FR-` requirement and every acceptance scenario is covered by a verification
  obligation, or by an exemption that says why automated verification is inappropriate and
  how the requirement is verified instead (FR-009). An acceptance scenario's id is
  `USn-ASm`: scenario `m` of user story `n`.
- Choose a testing level for each obligation: unit, integration, contract, end-to-end or
  other. No single level is required for all verification (FR-011).
- Scale the number of obligations to the scope, risk and complexity of the change
  (FR-013). A small, low-risk change gets one obligation per requirement and per
  acceptance scenario and no more. A large or risky one gets obligations for its failure
  conditions, boundaries and constraints as well.
- Planning names scenarios and outcomes. It does not write the executable tests: those are
  written one at a time during implementation, each just before the behaviour it verifies
  (FR-014).

**Ambiguity.** When a requirement is ambiguous, or contradicts another, in a way that
changes what a test should assert, put the question to the developer. Do not choose an
interpretation. Plan nothing for that requirement until it is answered: leave it without
an obligation, so that the plan check fails and the plan is not reported complete. Record
the answer in the specification's Clarifications, then write the obligation (FR-015).

**Verification commands.** Take the commands only from what the project already defines:
its package scripts, Makefile, CI configuration or contributor documentation (FR-049).
Record where each one is defined. When the project has no runnable test command, say so
as a gap to resolve and do not proceed as though verification had happened. Do not choose
or install a test framework on the project's behalf.

**A feature already past planning.** A feature whose `plan.md` has no Verification Plan
was planned before these rules applied and is not under the process. Each later stage
reports that as a gap at its start and again in its final report, names the plan stage as
the way to bring the feature under the process, and then carries on as core Spec Kit does.
No check is run and no evidence is recorded for it, and its work is never described as
verified.

## The Red, Green, Refactor cycle

Implementation proceeds one behaviour at a time. Every result comes from the check
script's `run` subcommand, which executes one of the plan's declared verification commands,
judges the outcome by exit status and expected text, and writes the record itself.

```text
python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py run \
    --phase <baseline|red|green|refactor|checkpoint> --command <command id> \
    [--select <selector>] [--task <task id>] [--vo <obligation id> ...] \
    [--tests <test file> ...] [--expect <text>] [--note <text>]
```

**Before the first task.** Record a `baseline` with a `broad` command, so that tests
already failing before this feature are known and kept apart from failures the work
introduces. Name the failing tests with `--note`. No other run is accepted until a
baseline exists.

**For each behaviour, in this order.**

1. **Write the test first.** Create or update the test for the behaviour before any of
   its implementation (FR-017). This is the obligation's test task.
2. **Red.** State in advance the text the failure should show, then run the test with
   `--phase red`, the test task, the obligation, the test files (`--tests`) and that text
   (`--expect`). Proceed only when the record is valid: the run failed and its output
   held the expected text (FR-018).
   - A test that passes on its first run is not a Red step. Investigate: the behaviour may
     already exist, or the test may not exercise it.
   - A test that fails for another reason, such as a missing import or a mistake in the
     test, is not a Red step either. Correct the test and run `red` again.
3. **Green.** Make the minimum change that satisfies the failing test (FR-019), then run
   it with `--phase green` on the behaviour task (FR-020).
4. **Refactor.** Tidy the code while the tests stay passing, and run the affected tests
   with `--phase refactor` afterwards (FR-021). Where there is nothing to tidy, there is
   nothing to run.

**Rules that hold throughout.**

- Never state that a test failed or passed unless `run` recorded it. "It should pass" is
  not a result (FR-022).
- Work in small increments, and verify each one before starting work that depends on it
  (FR-024). Tests are run throughout and never left to the end (FR-025).
- Select the existing tests that cover the area being changed and run them alongside the
  new one, so that a regression shows at once (FR-027).
- Run a `broad` command as a `checkpoint` at the end of each phase of the task list, and
  not after every change (FR-028).
- When a run fails, resolve the failure before starting dependent work (FR-026). The
  section on failures says how.
- Before marking a task complete, run `gate --task <task id>`. The edit that marks a task
  `[X]` is refused while its gate fails. Never edit `tdd-evidence.md`: only the script
  writes it.
- A routine cycle involves no approval request (FR-053). Ask the developer only for what
  the sections on test integrity and on failures, exceptions and decisions name.

## Test integrity

## Failures, exceptions and decisions

## Traceability and review evidence

## Fitting the project
