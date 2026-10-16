# Quickstart: validating the BDD behaviour checklist

**Feature**: `002-bdd-behaviour-checklist` | **Plan**: [plan.md](./plan.md)

Runnable scenarios that show the feature works end to end. They follow the four test
levels of the constitution: structural validation, installation and registration,
behavioural testing, and regression. Formats and rules are in the
[checklist contract](./contracts/behaviour-checklist.md) and the
[check script changes](./contracts/check-cli-changes.md); this guide does not repeat them.

## Prerequisites

- Python 3.9 or later, `uvx` (for Ruff) and `npx` (for markdownlint).
- Spec Kit CLI 1.1.3 (`specify --version`).
- Claude Code, for scenarios 3, 4 and 6.
- A throwaway directory outside this repository for installation, for example
  `/tmp/bdd-check`.

`CHECK` below stands for
`python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py` in an installed
project, or `python3 scripts/python/tdd_check.py` in this repository.

## 1. Automated tests (structural and behavioural, no agent)

```bash
python3 -B -m unittest discover -s tests
uvx ruff check .
npx -y markdownlint-cli2
```

Expected: all pass. The suite covers, with one fixture per case under
`tests/fixtures/features/`:

| Area | Cases |
|------|-------|
| Parsing | A valid checklist; each malformed element of the contract's section 2; fenced examples ignored |
| B1 to B7 | One failing fixture per rule and per distinct reason in the contract's rules table, and one passing fixture; each finding asserted exactly |
| B5 | The examples table of the contract, including a path the specification names |
| Applicability | A feature with neither marker nor checklist gives exactly the 0.1.0 output of `plan`, `tasks`, `gate`, `status` and `compliance` |
| Evidence location | Top-level only, `tests/` only, neither (created in `tests/`), both (exit 2, nothing written) |
| Item fixing | Rows added at the baseline and for an item added later; change, removal, change awaiting approval; G10, G11 and C8 |
| Refusals | Baseline refused while the checklist fails; Red refused for an obligation no item names |
| Status | The item table; derived statuses; `--scenarios`; the Summary unchanged for an older feature |
| Hook | Recorded payloads for an edit to `tests/tdd-evidence.md`, an edit to `plan.md` removing each heading, an edit to `plan.md` keeping both, and an edit to `tests/behaviour-checklist.md` |
| Examples | `plan` passes on `examples/runs/frontend-planned`; `compliance` reports `examples/runs/compliant` compliant and `tests-only` non-compliant |
| Manifests | `extension.yml` names the new template and the file exists; the plan addendum holds the sub-heading inside the Verification Plan |
| Performance | 200 tasks, 1,000 records and 200 items within the limits |

The deterministic checks give the same output on ten consecutive runs over the seeded
fixtures (SC-002): the suite runs each B-rule fixture ten times and compares the output.

## 2. Installation and registration

```bash
cd /path/to/speckit-tdd-integrated
git archive --format=tar HEAD | (mkdir -p /tmp/bdd-release && tar -x -C /tmp/bdd-release)
mkdir -p /tmp/bdd-check && cd /tmp/bdd-check && git init -q
specify init --here --integration claude
specify extension add integrated-tdd --dev /tmp/bdd-release
specify preset add integrated-tdd --dev /tmp/bdd-release
ls .specify/extensions/integrated-tdd/templates/
specify preset resolve plan-template | grep -n '^##\|^###'
```

Expected: the templates directory lists `behaviour-checklist-template.md` (A11); the
resolved plan template has `### Behaviour checklist` after `### Verification exemptions`,
inside `## Verification Plan` (A12); the composed `speckit-plan` skill contains the
"Behaviour checklist" step (A10).

## 3. The plan stage writes a checklist that passes (User Story 1, 3)

In the throwaway project, copy the sample project from `examples/runs/sample-project/`,
then run `/speckit-specify` with the story in `examples/stories/01-normal-development.md`,
then `/speckit-plan`.

Expected:

- `specs/<feature>/tests/behaviour-checklist.md` exists and `checklists/` holds only
  `requirements.md`.
- `CHECK plan` exits 0.
- Each acceptance scenario has a section whose quote matches `spec.md`, and every item
  names its obligations.
- The Completion Report names the checklist's location and asks for review; no approval is
  requested.
- A reviewer who took no part reads `spec.md` and the checklist and judges whether they
  match in under ten minutes (SC-004), and can say for any item which requirement it comes
  from (US3 scenario 1).

## 4. A failing checklist blocks (User Story 2)

On the feature of scenario 3, make each change below in turn, run `CHECK plan`, and
restore the file:

| Change | Expected finding |
|--------|------------------|
| Delete the only item naming FR-001 | `B1 FR-001: ...` |
| Remove `VO-002` from every Verified by list | `B3 VO-002: ...` |
| Replace a Then clause with `**Then** cart_total() returns 0` (a name from the plan) | `B5 BI-nnn: ...` |
| Change one word of a scenario quote | `B6 US1-AS1: ...` |

Then, with one finding left in place, run `/speckit-implement`. Expected: the stage stops
before the first task and reports the finding; `CHECK run --phase baseline --command
<broad id>` exits 2 and writes no evidence.

## 5. Items are fixed at the baseline (User Story 4)

Restore the checklist, run `/speckit-tasks` and start `/speckit-implement`. After the
baseline is recorded:

1. `tests/tdd-evidence.md` exists, holds a `## Behaviour items at baseline` row for every
   item, and no `tdd-evidence.md` exists at the top of the feature directory.
2. Weaken one item's Then clause, then try to mark a task naming its obligation complete.
   Expected: the edit is refused with `G10 T... BI-...: changed since the baseline ...`.
3. Record the change with `expectation --item BI-... --requirement FR-... --justification
   "..." --alters-behaviour`. Expected: still refused (`awaits approval`) until
   `approve --id BX-01 --by "<name>"` is recorded after the developer agrees.
4. Add a requirement to `spec.md` that no item names, then try to mark any task complete.
   Expected: refused with `G11 T... FR-...: B1: ...`. Add the item, rerun `CHECK plan`,
   and the task can be marked complete.
5. At the end, `CHECK status` shows each item with its obligations, tests and derived
   status, and no item is `verified` while an obligation it names is not.
6. `CHECK compliance` exits 0. Deleting step 3's change record from the evidence by hand
   makes it exit 1 with a C8 finding for the item.
7. A reviewer who took no part picks any item and, from the checklist and `CHECK status`,
   names the requirements it expresses and the tests that verify it with their result, in
   under two minutes (SC-003).

## 6. The guard covers the new locations (FR-042, SC-011)

In Claude Code, on the feature of scenario 5, ask the agent to:

| Edit | Expected |
|------|----------|
| Change a cell of `tests/tdd-evidence.md` | Refused every time, with the evidence refusal |
| Delete the `### Behaviour checklist` heading from `plan.md` | Refused, naming the heading |
| Delete the `## Verification Plan` heading from `plan.md` | Refused, naming the heading |
| Reword a sentence of the plan's Summary | Allowed |

## 7. Regression: features planned before the change (SC-006)

```bash
cd /path/to/speckit-tdd-integrated
for f in tests/fixtures/features/*/; do
  for s in plan tasks status compliance; do
    python3 scripts/python/tdd_check.py $s --feature-dir "$f" --json
  done
done > /tmp/after.json
```

Run the same loop at the 0.1.0 tag into `/tmp/before.json` (from a worktree of `v0.1.0`)
and compare. Expected: identical, because no existing fixture has the sub-heading or a
checklist. Then, in the throwaway project, install 0.1.0, plan and partly implement a
feature, upgrade to this version and run `/speckit-implement` again. Expected: the stage
reports the missing checklist as a gap naming `/speckit-plan`, continues as before, and the
evidence stays at the top level. Rerun `/speckit-plan`: the sub-heading and the checklist
are added and the evidence still stays where it is.

Finally, complete `checklists/requirements.md` and run `/speckit-implement`. Expected: the
core step's checklist table lists only `requirements.md` and it does not stop to ask
(A14).

Then remove both packages (constitution, quality gate level 4):

```bash
specify preset remove integrated-tdd
specify extension remove integrated-tdd
```

Take a new small feature through `/speckit-specify`, `/speckit-plan`, `/speckit-tasks` and
`/speckit-implement`. Expected: each stage completes as core Spec Kit does; the new feature
has no `tests/` folder and no checklist (FR-005, EC-02); the earlier feature's
`tests/behaviour-checklist.md` and evidence document are unchanged and readable.

## 8. Documentation (User Story 5)

Give a developer new to the workflow `README.md` and `templates/tdd-process-rules.md` and
ask the four questions of User Story 5: when the checklist is written, where it lives,
what each item must link to, and what is forbidden in it. Expected: correct answers from
the documents alone in under five minutes (SC-008). Then drive story 08. Expected: the
plan check reports the item written from the code (B5) and the requirement left without an
item (B1), and the plan stage does not report completion until both are corrected.

Finally, a reviewer who took no part reads the specification and checklist of
`examples/runs/compliant` and `examples/runs/frontend-planned`. Expected: every outcome of
each acceptance scenario appears unweakened in its items, and no two items describe the
same behaviour (SC-009).

## 9. A story end to end with Claude Haiku

In a fresh copy of `examples/runs/sample-project/` for each of stories 01, 07 and 08, with
Spec Kit 1.1.3 and both packages installed from a release tree as in scenario 2, drive the
story non-interactively, one command per invocation:

```bash
claude -p --model haiku --permission-mode acceptEdits --allowedTools Bash "/speckit-specify <story text>"
```

then `/speckit-plan`, `/speckit-tasks`, `/speckit-analyze` and `/speckit-implement` the same
way (story 08 stops after `/speckit-plan`). Expected: only the standard commands are used;
the checklist and evidence are in `tests/`; `CHECK plan` passes and, after implementation,
`CHECK compliance` is COMPLIANT; story 07 has one item per scenario and per requirement and
no more; story 08's plan stage reports B5 and B1 and withholds completion until they are
corrected. A person who took no part reads each `spec.md`, checklist and final
`CHECK status` and notes any item that is missing, weaker than its scenario, beyond the
specification or written in terms of the code.

These runs are non-interactive, so they exercise no clarification and no approval. They add
to scenarios 3 to 6 and 8 and do not replace them.

## What these scenarios do not prove

- That an item keeps its scenario's wording as closely as it could, or states no weaker
  outcome than its scenario (FR-016). Scenario 3's reviewer judges that; no check does.
- That no two items describe the same behaviour (FR-015).
- That implementation wording outside B5's token shapes is absent.
- That a name given to `approve` is the developer's.

## Validation results

### T005: the 0.1.0 compatibility guard fails when a stored output differs

- **Date**: 2026-10-16.
- **Run**: `TDD_GOLDEN_FILE=<scratch copy> python3 -B -m unittest discover -s tests -p test_compatibility.py`, where the scratch copy of `golden_0_1_0.json` had `x` appended to the stored `plan` output of `valid-minimal`.
- **Observed**: `FAILED (failures=1)`, with `valid-minimal plan: expected 0 '{"exit_code": 0, "findings": [], "subcommand": "plan"}\nx', got 0 '{"exit_code": 0, "findings": [], "subcommand": "plan"}\n'`. With the real golden file the test passes (465 outputs, 93 fixtures).

### T017: scenario 3 up to the end of `/speckit-plan`, with Claude Code (User Story 1)

- **Date**: 2026-10-16. Project: a copy of `examples/runs/sample-project/` without its earlier `specs/001-cart-total`, Spec Kit 1.1.3, both packages installed from `git archive` of commit `0bb2d3a`. Driven with `claude -p --model sonnet --permission-mode acceptEdits --allowedTools=Bash`, one invocation per command: `/speckit-specify` with the text of story 01, then `/speckit-plan`. No other command was used (SC-005).
- **Where the checklist was written**: `specs/001-cart-total/tests/behaviour-checklist.md`. `checklists/` holds only `requirements.md`.
- **Coverage**: 6 sections (five acceptance scenarios and Other behaviours) and 7 items. Every `FR-` requirement and scenario is named by an item (FR-001 to FR-005; US1-AS1, US1-AS2, US2-AS1, US3-AS1, US3-AS2), and each item names its obligation (VO-001 to VO-007), with no exemptions. The plan holds the `### Behaviour checklist` sub-heading and the fixed link line.
- **Quotes**: all five quotes match the scenario text of `spec.md` word for word.
- **Design elements**: no item names a file, module, function, class, table or screen component. `ValueError` appears in two items; the specification names it, so it is part of the boundary it describes.
- **Check**: the installed script at this commit has the parser and no checklist rules yet, so `plan` could not check the checklist; the reading above is by eye. The 0.1.0 `plan` check exits 0.
- **Completion Report**: named the location, the 6 sections and 7 items and the result of the check, and ended "Please review the checklist against the spec." It asked for no approval.
- **Approval requested on account of the checklist (SC-010)**: none.
- The project is kept at the path recorded in the session for T029.

### T029: quickstart scenario 4, a failing checklist blocks (User Story 2)

- **Date**: 2026-10-16. The project kept from T017, with both packages reinstalled from `git archive` of commit `e80b85e`, then `/speckit-tasks` run through `claude -p` (16 tasks; the check reported no finding against the checklist).
- **Before the changes**: the checklist as the plan stage wrote it failed `plan`. Three items (BI-005, BI-006, BI-007) expressed `EC-01`, `EC-02` and `EC-03`, which the specification does not hold because it lists its edge cases without ids, and the plan check reported `B6 BI-005: Expresses EC-01, which spec.md does not hold` and the same for the other two. The first run of the plan stage could not have caught it: the script installed then had no checklist rule. The three ids were removed (`EC-03` replaced by `FR-004`) so that the next changes start from a passing checklist.
- **Changes and findings** (each restored afterwards; `plan` passed again after the last):

| Change | Finding reported |
|--------|------------------|
| Delete BI-001, the only item naming FR-001 | `B1 FR-001: no behaviour item expresses it`, `B1 US1-AS1: ...`, `B3 VO-001: no behaviour item names it in Verified by`, `B4 US1-AS1: the scenario section has no items` |
| Replace `VO-002` with `VO-001` in the Verified by list | `B3 VO-002: no behaviour item names it in Verified by` |
| Replace a Then clause with `**Then** test_cart reports 17` (a name from the task list) | `B5 BI-001: \`test_cart\` is a code-shaped token that plan.md or tasks.md names and spec.md does not` |
| Change `17` to `18` in the US1-AS1 quote | `B6 US1-AS1: the quote differs from the scenario text in spec.md` |

- **Two differences from the quickstart's table.** The table suggests `cart_total()` as the name from the plan. The specification of this feature already names `cart_total` and `item_count`, so B5 correctly did not report them; `test_cart`, which only the task list holds, was used instead. Running this row first with `item_count()` showed that B5 compared a token literally and did not match the bare name in the task list; `name()` now also matches `name` (commit `e80b85e`), with a fixture and test written first.
- **Implement stopped**: with the quote finding left in place and no evidence document, `/speckit-implement` (through `claude -p`) stopped before the first task. It reported `B6 US1-AS1`, the quote saying 18 against 17 in the specification, changed no file, marked no task, and said the checklist is corrected by the plan stage. `CHECK run --phase baseline --command make-test` exited 2 with the message and the finding, and `tests/` held only `behaviour-checklist.md`.
- The checklist was restored and `plan` passes; the project is kept for T033 and T046.

### T046 (the part that needs no person): quickstart scenarios 5 and 6 with Claude Code (User Story 4)

- **Date**: 2026-10-16. The project kept from T029, both packages reinstalled from `git archive` of commit `bc9c9b2`, `/speckit-implement` run through `claude -p --model sonnet` (the checklist passing, 16 tasks, an unchanged `plan.md`).
- **Evidence location**: `specs/001-cart-total/tests/tdd-evidence.md`; no `tdd-evidence.md` at the top of the feature directory.
- **Baseline rows**: `## Behaviour items at baseline` held one row per item, BI-001 to BI-007, each with its Verified by list, a six-character fingerprint and `Seq` 1, the sequence number of the baseline record.
- **The run**: all 16 tasks completed; `gate --all` passed; `status` showed VO-001 to VO-007 and BI-001 to BI-007 verified, `Not verified: none`; `compliance` printed `COMPLIANT`. Five obligations were recorded as `no-meaningful-red` exceptions (the earlier implementation already satisfied their tests), none needing approval.
- **A fixed item weakened, then a task ticked** (T008 unticked, BI-004's Then clause changed from `a ValueError is raised` to `an error is raised`; a haiku agent was asked to tick T008 with the Edit tool):
  - refused: `G10 T008 BI-004: changed since the baseline and no change is recorded`;
  - `expectation --item BI-004 --requirement FR-003 FR-004 --justification ... --alters-behaviour` recorded `BX-01`; the next tick was refused: `G10 T008 BI-004: change BX-01 alters behaviour and awaits approval`;
  - `approve --id BX-01 --by "validation reviewer"` (a stand-in name: this was a validation run, with no developer to ask); `gate --task T008` passed and the tick was accepted.
- **A requirement added that no item names** (T016 unticked, `FR-006` added to `spec.md`): the tick of T016, a no-test task, was refused with `G11 T016 FR-006: B1: no behaviour item expresses it`. After an item `BI-008` expressing FR-006 was added, `gate --task T016` passed and the tick was accepted. `plan` still reported `C1 FR-006` (no obligation), which G11 does not carry: it applies the checklist rules only.
- **A mistake of the validation, caught by the script**: the sed that weakened BI-004 matched the same text in BI-005 and BI-007. `compliance` reported `C8 BI-005` and `C8 BI-007: changed since the baseline and no change is recorded`, with the `G10` findings of the tasks that verify them, until those two items were restored.
- **Compliance before and after deleting the change record**: after restoring the other items and recording a checkpoint, `compliance` printed `COMPLIANT` (exit 0). With the `BX-01` row deleted from the evidence by hand, it printed `NON-COMPLIANT` with `C8 BI-004: changed since the baseline and no change is recorded`, the `C5` findings for T008 and T009, and `C7 tests/tdd-evidence.md: the Summary is out of date`. Restoring the row made it `COMPLIANT` again.
- **Findings from the run**: (1) the refusal text the hook gives for a completion refused on G10 or G11 offers only the two routes for test evidence (run, exception); an agent that read it did not know to record an item change or return to the plan stage. The hook now adds the route for these rules (commit following this entry). (2) No approval was requested beyond the one for the behaviour-altering change (SC-010).
- **Not done, needs a person (SC-003)**: a person who took no part is to be given the checklist and the final `status` and asked to name, for three items picked at random, the requirements each expresses and the tests that verify it with their result, with the time for each against the 2 minute limit.
