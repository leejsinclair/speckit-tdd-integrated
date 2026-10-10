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

## Test integrity

## Failures, exceptions and decisions

## Traceability and review evidence

## Fitting the project
