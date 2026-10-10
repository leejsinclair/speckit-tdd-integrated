# Contract: artefact formats

**Feature**: `001-integrated-tdd` | **Data model**: [data-model.md](../data-model.md)

The formats the check script parses. They are what the coding agent writes into the
existing Spec Kit artefacts, and what the script writes into the evidence document. A
reviewer reads the same text.

Parsing rules common to every table: the table is found by its heading and then its header
row; column order is fixed; cells are trimmed; lists inside a cell are separated by commas;
a cell containing only `-` is empty. Rows may wrap in the source only as Markdown allows,
which is not at all.

## 1. Verification Plan section of `plan.md`

Appended to the core plan template by the preset. The heading text is fixed.

```markdown
## Verification Plan

### Verification commands

| ID | Command | Scope | Source |
|----|---------|-------|--------|
| unit | `pytest {select} -q` | focused | pyproject.toml, tool.pytest |
| suite | `make test` | broad | Makefile, test target |

### Verification obligations

| ID | Requirements | Scenario | Expected outcome | Level | Origin |
|----|--------------|----------|------------------|-------|--------|
| VO-001 | FR-003, US1-AS2 | An empty cart is totalled | The total is zero and no error is raised | unit | planned |
| VO-002 | FR-007, DC-01 | An order is submitted while the payment provider is unreachable | The order is not created and the customer is told payment failed | integration | planned |

### Verification exemptions

| Requirement | Reason | Alternative verification |
|-------------|--------|--------------------------|
| FR-019 | Visual layout has no stable automated check in this project | Reviewed against the design at code review |
```

| Element | Rule |
|---------|------|
| Command ID | Lowercase letters, digits and hyphens. Unique |
| Command | In backticks. At most one `{select}` |
| Scope | `focused` or `broad`. At least one command of each scope is recommended; one `broad` command is required before a checkpoint can be recorded |
| Obligation ID | `VO-` and three or more digits. Unique. Never renumbered or reused |
| Requirements | Ids as defined in the data model. `FR-`, `SC-` and `USn-ASm` ids must exist in `spec.md`. `DC-` and `EC-` ids are labels the agent assigns in the plan, with the constraint or edge case stated in the Scenario cell; they are not looked up. Any other prefix is an error |
| Level | `unit`, `integration`, `contract`, `end-to-end` or `other` |
| Origin | `planned` or `discovered` |
| Exemptions | A single row reading `None` in the Requirement column when there are none |

The section holds no status column. Status is derived from the evidence.

## 2. Task labels in `tasks.md`

Labels are added to Spec Kit's task line, after the story label and before the description.
The rest of the line is unchanged.

```markdown
- [ ] T011 [P] [US1] [VO-001] Write the failing test for an empty cart total in tests/test_cart.py
- [ ] T012 [US1] [VO-001] Implement the cart total in src/cart.py
- [ ] T013 [US1] [NT: README wording only] Document the cart total in README.md
```

| Label | Meaning |
|-------|---------|
| `[VO-nnn]` | The task satisfies this obligation. Repeat the label for several obligations |
| `[NT: reason]` | The task has no behaviour to verify. The reason is required |

A task's kind follows from its labels and its position:

| Kind | Rule |
|------|------|
| `no-test` | Carries `[NT: reason]` and no `[VO-nnn]` |
| `test` | The first task in the file to name a given obligation |
| `behaviour` | Any later task naming that obligation |

A task naming several obligations is a `test` task only when it is the first to name all
of them, and is otherwise a `behaviour` task. The task identifier pattern is `T` followed
by three or more digits, as Spec Kit writes it. The checkbox is `[ ]`, `[X]` or `[x]`.

Every obligation is named by at least two tasks, so that it has a `test` task and a
`behaviour` task. The passing run is required of the `behaviour` task.

Order alone decides kind; the description is not read. For an obligation named only by
single-label tasks, the first is always the `test` task, so rule C3 cannot fail for it. C3
fails only when a task carrying several labels is the first to name one of its obligations
without being the first to name all of them. That the failing run comes before the passing
run is enforced by the task gate on the evidence (G3, G4), not by C3. A task list whose
descriptions put implementation first is therefore not caught at the tasks stage; the
tasks wrapper tells the agent to write the test task first, and a reviewer reads the list.

## 3. Evidence document `tdd-evidence.md`

One per feature, in the feature directory, written only by the check script.

```markdown
# TDD Evidence: <feature directory name>

<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->

## Summary

_Generated from the tables below on 2026-10-10T14:02:11Z._

| Obligation | Requirements | Status | Tests | Latest result |
|------------|--------------|--------|-------|---------------|
| VO-001 | FR-003, US1-AS2 | verified | tests/test_cart.py::test_empty_cart_total | pass (#4) |
| VO-002 | FR-007, DC-01 | planned | - | - |

**Not verified**: FR-007 (VO-002 planned), FR-019 (exempt: see plan).

**Open decisions**: none. **Exceptions**: none. **Expectation changes**: none.

**Pre-existing failures**: none.

## Baseline

| Seq | Command | Result | Pre-existing failures |
|-----|---------|--------|-----------------------|
| 1 | suite | pass | - |

## Test execution records

| Seq | Time | Task | Obligations | Phase | Command | Selector | Result | Valid | Classification | Files | Fingerprint | Note | Check |
|-----|------|------|-------------|-------|---------|----------|--------|-------|----------------|-------|-------------|------|-------|
| 1 | 2026-10-10T13:40:02Z | - | - | baseline | suite | - | pass | yes | - | - | - | - | 9c1f2a |
| 2 | 2026-10-10T13:51:47Z | T011 | VO-001 | red | unit | tests/test_cart.py::test_empty_cart_total | fail | yes | assertion | tests/test_cart.py | 5be0d1 | expected: assert 0 == None | 41d7c0 |
| 3 | 2026-10-10T13:58:20Z | T012 | VO-001 | green | unit | tests/test_cart.py::test_empty_cart_total | pass | yes | - | tests/test_cart.py | 5be0d1 | - | a02e9b |

## Exceptions

| ID | Time | Task | Obligations | Kind | Rationale | Alternative verification | Needs approval | Approved by |
|----|------|------|-------------|------|-----------|--------------------------|----------------|-------------|

## Expectation changes

| ID | Time | Task | Files | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|-------|--------------|---------------|------------------|-------------|-----------------|

## Decisions

| ID | Opened | Question | Tasks | Status | Answer | Decided by | Resolved |
|----|--------|----------|-------|--------|--------|------------|----------|
```

| Element | Rule |
|---------|------|
| Summary | Rewritten whole on every write. Holds nothing that is not derivable from the tables beneath it and from `plan.md`. No check reads it as input. When it differs from a freshly generated view, apart from the generated-on line, the compliance check reports it as out of date (C7); any recording run rewrites it |
| Baseline | One row per `baseline` record. Pre-existing failures are taken from the record's note, or read `failing before work began` when the note is empty |
| Records | Append-only. `Seq` is contiguous from 1. `Note` for a valid `red` record begins `expected:` followed by the text that was matched |
| Files | The test files the run was fingerprinted over, as paths relative to the repository root, in sorted order, separated by commas. For a `red` record, the files named with `--tests`. For a `green` or `refactor` record made without `--tests`, the files of the latest valid `red` record of the obligations named. `-` when there are none |
| Fingerprint | First six hexadecimal characters of the SHA-256 over the paths and current contents of the files in the Files cell, in sorted path order. A file that no longer exists is hashed as missing, so deleting it changes the fingerprint. `-` when Files is `-` |
| Check | First six hexadecimal characters of the SHA-256 over the previous row's check and this row's cells, excluding Classification and Note |
| Cell text | The script replaces a vertical bar or a line break in supplied text with a space |
| Size | What was run, the point in the cycle, the result and the failure classification. No test output beyond the matched expected text (FR-062) |

## 4. What each lifecycle stage adds

The observable contract of the wrapped commands. Each row is an addition to what the core
command already does; nothing the core command does is removed.

| Stage | Added to the stage | Check run by the stage | Blocks the stage when |
|-------|--------------------|------------------------|-----------------------|
| Plan | The Verification Plan is filled as a Phase 1 output: commands from the project's own tooling, obligations derived from the specification's requirements, scenarios and edge cases and from the design's constraints, levels chosen per obligation, exemptions with reasons. Material ambiguity is put to the developer and not resolved by the agent. The amount of planning is scaled to the change | `plan` | A requirement has no obligation or exemption, or no verification command exists |
| Tasks | Every task is labelled. For each obligation a test task is generated ahead of the task that delivers the behaviour. Test tasks are not optional | `tasks` | A task is unlabelled, an obligation lacks a test task or a behaviour task, or behaviour is ordered before its test |
| Analyze | The `plan` and `tasks` findings are included in the analysis report. Nothing is modified | `plan`, `tasks` | Never. Analyze stays read-only and reports |
| Implement | Before the first task: the checks are rerun and a baseline is recorded. Per task: the Red, Green, Refactor cycle through `run`, with failures classified, exceptions and decisions recorded, and a broad checkpoint at the end of each phase. Before a task is marked complete: `gate`. At the end: `gate --all` and the review summary, stating what passing tests do and do not show | `plan`, `tasks`, `run`, `gate` | A task fails its gate. The runtime event enforces this at the edit that would mark the task complete |

A feature whose `plan.md` has no Verification Plan, because it was planned before the
packages were installed, is not under the process. The tasks, analyze and implement
wrappers say so at the start of the stage and again in its final report, naming
`/speckit-plan` as the way to bring the feature under the process, and then carry on as
core Spec Kit does: no checks are run, no evidence is recorded and the runtime event
allows every edit. The stage never describes such a feature's work as verified.

Changes to existing Spec Kit behaviour, to be listed in the README under FR-004:

1. `plan.md` gains a Verification Plan section.
2. Test tasks in `tasks.md` are mandatory for behaviour, where core Spec Kit generates them
   only on request, and tasks gain labels.
3. A task cannot be marked complete in `tasks.md` through the agent's edit tools until its
   gate passes.
4. `.claude/settings.json` gains one `PreToolUse` entry, managed by Spec Kit.
5. The feature directory gains `tdd-evidence.md`, which the agent's edit tools cannot
   change directly.
