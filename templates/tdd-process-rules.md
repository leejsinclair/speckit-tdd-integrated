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

## The Red, Green, Refactor cycle

## Test integrity

## Failures, exceptions and decisions

## Traceability and review evidence

## Fitting the project
