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

### T055: story 08 driven with Claude Code (User Story 5)

- **Date**: 2026-10-16. A throwaway project from `examples/runs/sample-project/` whose `shop/cart.py` holds `cart_total` with the 10% bulk discount (helper `apply_bulk_discount`) and no rejection of negative prices, one passing test, both packages installed from `git archive` of commit `882d510` (plus the docs commits that followed). `/speckit-specify` with the story text, then `/speckit-plan`, through `claude -p --model sonnet`.
- **Did the agent write items from the code?** No. The specification it wrote treated the discount as outside the cart total (a requirement, FR-006, that the total is the plain sum) and said so in its assumptions, and the checklist has seven items, one per acceptance scenario, in the specification's terms: BI-003 states that a cart of eleven items priced 1 totals 11 "with no adjustment of any kind", and BI-005 and BI-006 state the rejection of a negative price with `ValueError` (which the specification itself names). No item names `cart_total()`, `apply_bulk_discount()` or `shop/cart.py`.
- **Findings `plan` reported to the agent**: none could be read from the output of `claude -p`, which returns the final message only; the final `plan` exited 0. The Completion Report named `tests/behaviour-checklist.md`, the 7 sections and 7 items, `status --scenarios`, and said nothing waited on approval.
- **Withheld completion?** Not exercised by the agent: it had nothing to correct that is visible.
- **The seeded variant**, to show that the check reports what the story is about: in a copy of the checklist the sections of the two negative-price scenarios were deleted and BI-003's Then clause was rewritten as `cart_total() calls apply_bulk_discount() and the result is 9.9 from shop/cart.py`. `plan` exited 1 with eight findings: `B1 FR-003`, `B1 FR-004`, `B1 US3-AS1` and `B1 US3-AS2` (the requirements the "code" does not meet), `B3 VO-005` and `B3 VO-006`, and `B5 BI-003` twice (`apply_bulk_discount()` is a code-shaped token that the plan names and the specification does not; `shop/cart.py` is path-shaped). `cart_total()` was not flagged because the specification names `cart_total`. The checklist was restored and `plan` passed again.
- **Honest limit**: the story did not make this agent write from the code. Whether another agent does is for the story to show when it is driven; the check is the safeguard either way.

### T049 (the part that needs no person): `examples/runs/compliant/` regenerated

- **Date**: 2026-10-16. A copy of `examples/runs/sample-project/` with its earlier `specs/001-cart-total` removed, both packages installed from `git archive` of commit `882d510`, driven through `claude -p --model sonnet` with the six standard commands in order: `/speckit-specify` (the text of story 01), `/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-analyze` and `/speckit-implement`. All six exited 0 and no other command was used. Because the commands ran non-interactively, no clarification or approval was exercised.
- **Result**: 17 tasks all complete; `plan`, `tasks` and `gate --all` pass; `compliance` printed `COMPLIANT`; eight behaviour items (BI-001 to BI-008) over seven obligations, all verified; five obligations recorded as `no-meaningful-red` exceptions because their tests passed on first run. The evidence is `tests/tdd-evidence.md`, with the item tables.
- **Copied into the repository**: `spec.md`, `plan.md`, `tasks.md`, `tests/behaviour-checklist.md` and `tests/tdd-evidence.md` replaced the contents of `examples/runs/compliant/` (one repeated blank line in `tasks.md` removed for the Markdown linter), and `examples/runs/sample-project/specs/001-cart-total/` was updated to the planning artefacts of that run with every task unticked. `plan`, `tasks` and `compliance --feature-dir examples/runs/compliant` pass from the repository root. `examples/runs/README.md` describes the layout and the frontend example.
- **Not done, needs a person (SC-009)**: a person who took no part is to be given `spec.md` and `tests/behaviour-checklist.md` of `examples/runs/compliant/` and of `examples/runs/frontend-planned/` and say, for each, whether every outcome of each acceptance scenario appears unweakened in its items and whether any two items describe the same behaviour. The frontend example was written by the plan author and was not produced by a run.

### T058: performance at 200 tasks, 1,000 records and 200 behaviour items

- **Date**: 2026-10-16. `tests/test_performance.py` gained `ChecklistPerformanceCase`, which builds the feature of 001's performance test with a behaviour checklist of 200 items fixed at the baseline and runs the same eight timing tests on it, plus a `hook` on a `plan.md` edit and on a heading removal. At normal size all 19 tests pass in about 4 seconds in total. Measured on this machine: `compliance` 0.74s, `gate --all` 0.45s, a `hook` on a task completion 0.39s, `plan` 0.36s, `status` 0.12s, `tasks` 0.08s, a `hook` on a `plan.md` edit 0.07s. These tests measure code that already exists and passed at once, as the approved exception allows.
- **Shown reachable, by size**: `TDD_PERF_SCALE=10` (2,000 items, 2,000 tasks, 10,000 records) made five tests fail on their limits: `compliance` 59.7s, `gate --all` 31.6s, a `hook` on a task completion 26.6s, `plan` 26.3s and `status` 2.17s against the 2 second limit. The same limit failures are the known cost of scale that the README lists: the checks scan every record per task.
- **Shown reachable, by limit**: `tasks` and the two `plan.md` hooks stayed within their limits even at `TDD_PERF_SCALE=40`, so the size route could not show them failing. `TDD_PERF_LIMIT_SCALE` (new) multiplies the limits; at `0.001` every timing test of `ChecklistPerformanceCase` failed with a message such as `tasks took 0.08s, limit 0.002s` and `hook took 0.07s, limit 0.001s`.
- No correction to `tdd_check.py` was needed to meet a limit at the stated size.

### T059: the suite on Python 3.9

- **Date**: 2026-10-16. `uv run --python 3.9 python -B -m unittest discover -s tests`: `Ran 574 tests in 217.429s`, `OK`. No code in `scripts/python/tdd_check.py` or `tests/` needed a later version.

### T056 (the part that needs no person): stories 01, 07 and 08 with Claude Haiku

- **Date**: 2026-10-16. Spec Kit 1.1.3 and both packages (0.2.0, from `git archive` of commit `e54094a`) installed in a fresh copy of `examples/runs/sample-project/` per story. Each command was one invocation of `claude -p --model haiku --permission-mode acceptEdits --allowedTools=Bash` (the option is written with `=` here: `--allowedTools Bash "<prompt>"` takes the prompt as a second tool name and exits with "Input must be provided"), each with the instruction not to retry or work round a refusal. Story 01 and story 07 ran `/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-analyze` and `/speckit-implement`; story 08 stopped after `/speckit-plan`. The runs are non-interactive: no clarification and no approval was exercised, and they add to T017, T029, T046 and T055 and do not replace them.
- **Story 01**: only the commands above were used. The checklist and the evidence were written to `specs/001-cart-total/tests/`; no evidence at the top of the feature directory. `plan` and `tasks` pass; `gate --all` passes for 21 completed tasks; `compliance` printed `COMPLIANT`. The checklist has 9 items (BI-001 to BI-009) over 5 acceptance scenarios and 6 functional requirements: one item per scenario, then four Other behaviours items for edge cases and a success criterion. All 9 items and all 9 obligations are verified in `status`; seven obligations carry a `no-meaningful-red` exception. The agent's report noted a checkpoint missing at the end of two phases.
- **Story 07**: the specification the agent wrote has 3 acceptance scenarios, 4 functional requirements, 2 edge cases and 3 success criteria for a one-line change, and the plan has 4 obligations and the checklist 4 items (3 scenario items and one Other behaviour for EC-02 verified by an exemption). `plan` exits 1: FR-004 (an explicitly set symbol keeps working) has no obligation and no item (`C1 FR-004`, `B1 FR-004`), because the agent left it behind an open question to the developer. `/speckit-analyze` named that as the one blocker. `/speckit-implement` stopped before recording a baseline and told the developer to answer the question and rerun `/speckit-plan`, so no evidence document was written and `compliance` printed `NON-COMPLIANT` (C1, C6, C7, C8). **US1 scenario 6 is not met here**: the checklist is not one item per scenario and per requirement and no more, because the model produced more requirements than the story needs and then could not cover them. That is a finding about proportion in the plan stage for a small model, which the process rules ask for and the check cannot enforce.
- **Story 08**: `/speckit-specify` marked FR-006 `[NEEDS CLARIFICATION]` (the code takes 10% off carts of more than ten items; the story does not ask for it) and the plan stage did not report completion: its message begins "The plan is not complete" and puts the question to the developer. `plan` exits 1 with `C1 FR-006` and `B1 FR-006`; no item names a file or function, so **B5 was not reported** for this run, and the checklist has six scenario items, one per scenario, in the specification's terms. The story's expected B5 therefore did not occur; B1 did, and completion was withheld. The negative-price scenarios have items (BI-005 and BI-006), because the specification states them.
- **Not done, needs a person**: a person who took no part is to read each feature's `spec.md`, `tests/behaviour-checklist.md` and final `status` (`status --scenarios` for story 08) and note any item that is missing, weaker than its scenario, beyond the specification or written in terms of the code. The material is kept in the session's scratch directories.

### T061: regression, upgrade and removal (quickstart scenario 7)

- **Date**: 2026-10-16.
- **Golden comparison**: `tests/test_compatibility.py` runs the current script on the 93 fixtures that existed at `v0.1.0` for `plan`, `tasks`, `gate --all`, `status` and `compliance` with `--json` and compares each exit code and output with the stored 0.1.0 output; it passed in the full suite at every commit since T005 (465 comparisons, identical).
- **Upgrade path**: a copy of `examples/runs/sample-project/` with Spec Kit 1.1.3 and 0.1.0 of both packages (`git archive v0.1.0`). Through `claude -p --model sonnet`, `/speckit-specify` (story 01), `/speckit-plan`, `/speckit-tasks` and `/speckit-implement` for the first two tasks: the feature had a Verification Plan, no checklist, and its evidence at `tdd-evidence.md` (baseline, one Red run). Both packages were then removed and 0.2.0 installed.
  - `/speckit-implement` again (one task): it did T003, recorded the Green run in `specs/001-cart-total/tdd-evidence.md`, and reported the gap: "This feature has no Behaviour checklist section in `plan.md` and no `tests/behaviour-checklist.md`, because it was planned before that existed. No checklist rule applies to it. Its evidence stays in `specs/001-cart-total/tdd-evidence.md`. Running `/speckit-plan` would add the checklist." The gap was in the final report; the start-of-stage statement is not visible in `claude -p` output.
  - `/speckit-plan` again: the plan check passed, `### Behaviour checklist` and its line were added to `plan.md`, `tests/behaviour-checklist.md` was written (6 sections, 7 items), and `tdd-evidence.md` stayed at the top of the feature directory (no `tests/tdd-evidence.md`). The check rejected `EC-01` and `EC-02` as not in `spec.md`, and the agent added those two labels to the specification's edge cases without changing any requirement text.
- **A14**: with `checklists/requirements.md` complete (16 of 16 checked), `/speckit-implement` printed the core step's table with the single row `requirements.md | 16 | 16 | 0 | PASS`, did not stop to ask, and went on to T004. The behaviour checklist is not listed because it is not in `checklists/`. Confirmed (research.md).
- **Removal**: `specify preset remove integrated-tdd` and `specify extension remove integrated-tdd --force`. What was left: `.specify/extensions/.backup` and `.registry`; `.claude/skills` with the four commands in their core content (no mention of `tdd_check` or the checklist); `.claude/settings.json` no longer exists, because the event was the only thing in it. A new small feature (`item_names`) taken through `/speckit-specify`, `/speckit-plan`, `/speckit-tasks` and `/speckit-implement` completed as core Spec Kit does: 8 tasks, 12 tests passing, no `tests/` folder and no checklist in `specs/002-item-names/`. The earlier feature's `tests/behaviour-checklist.md` and `tdd-evidence.md` are byte-for-byte unchanged and readable.

### T062: quickstart scenario 1 in full

- **Date**: 2026-10-16, at the commit that follows T061.
- `python3 -B -m unittest discover -s tests`: `Ran 574 tests in 127.120s`, `OK`.
- `uvx ruff check .`: `All checks passed!`.
- `npx -y markdownlint-cli2`: `Linting: 63 files`, `Summary: 0 issues in 0 files`.
- Findings fixed along the way: line length and unused imports in the new tests; files opened and not closed in four of them (the `ResourceWarning`s of earlier full runs); none remain.

### T063: Red before Green replayed from git history

- **Date**: 2026-10-16. For the commit of each test task, a temporary `git worktree` was checked out, the test modules that commit names were run there with `python3 -B -m unittest discover -s tests -p <module>`, and the same modules were run at the implementation commit that follows. The whole suite was not run at each of the 34 checkouts (it takes about two minutes); the modules are those the commit message lists as failing. Not replayed, as the task says: T005 (a guard that passes when written, shown to fail against an altered golden file in its own entry) and T058 (measures existing code, shown reachable in its own entry).
- **Result**: every test commit fails for the reason its message gives and every implementation commit passes the same modules. The counts equal those in the messages: for example T006 fails 18 + 77 + 3 = 98 tests, as its message states, and T010 fails with `failures=14, errors=4`. Four test commits beyond the list in the task were replayed because they were made fail-first too: the B5 follow-up, the reviewing-the-checklist guidance (T032), the hook's way-forward text for G10 and G11, and T025/T027.
- **Mismatches**: none in the failures. One commit message misstates a count: the message of the commit for T024 says "Ran 475 tests" for a full-suite run that printed 477. No history was rewritten.
- T036, T038, T040 and T042 share one implementation commit, so T037, T039 and T041 are matched with it as T035 is.

| Task | Test commit | Named modules at the test commit | Implementation commit | Same modules at the implementation commit |
|------|-------------|----------------------------------|-----------------------|-------------------------------------------|
| T006 | bf23939 | test_evidence_location.py: 13 tests, FAILED (failures=18); test_run.py: 86 tests, FAILED (failures=77); test_status.py: 29 tests, FAILED (failures=3) | cae6e5a | test_evidence_location.py: 13 tests, OK; test_run.py: 86 tests, OK; test_status.py: 29 tests, OK |
| T008 | 1d3fbfd | test_parsing.py: 63 tests, FAILED (failures=21, errors=5) | ca06a96 | test_parsing.py: 63 tests, OK |
| T010 | 6b3ac8b | test_manifests.py: 62 tests, FAILED (failures=14, errors=4) | 0bb2d3a | test_manifests.py: 62 tests, OK |
| T019 | c4c6c32 | test_checklist.py: 15 tests, FAILED (failures=39, errors=1) | 88dce80 | test_checklist.py: 15 tests, OK |
| T021 | 0425310 | test_run.py: 91 tests, FAILED (failures=3) | 6f17612 | test_run.py: 91 tests, OK |
| T023 | 3bfc647 | test_hook.py: 55 tests, FAILED (failures=6) | 8bee329 | test_hook.py: 55 tests, OK |
| T025 | a095ae2 | test_manifests.py: 69 tests, FAILED (failures=13) | f56d64b | test_manifests.py: 69 tests, OK |
| T030 | ff06da3 | test_status.py: 35 tests, FAILED (failures=5); test_cli.py: 14 tests, FAILED (failures=1) | 25c983e | test_status.py: 35 tests, OK; test_cli.py: 14 tests, OK |
| T035 | 22b8d3d | test_item_changes.py: 27 tests, FAILED (failures=18); test_gate.py: 60 tests, FAILED (failures=6) | 3b000cb | test_item_changes.py: 27 tests, OK; test_gate.py: 60 tests, OK |
| T037 | f5aa6cf | test_run.py: 95 tests, FAILED (failures=1) | 3b000cb | test_run.py: 95 tests, OK |
| T039 | 7cceaff | test_status.py: 47 tests, FAILED (failures=20, errors=1) | 3b000cb | test_status.py: 47 tests, OK |
| T041 | 9c95008 | test_compliance.py: 40 tests, FAILED (failures=6) | 3b000cb | test_compliance.py: 40 tests, OK |
| T043 | 5ef534b | test_manifests.py: 82 tests, FAILED (failures=7, errors=1) | bc9c9b2 | test_manifests.py: 82 tests, OK |
| T047 | 1889128 | test_compliance.py: 43 tests, FAILED (failures=3) | e54094a | test_compliance.py: 43 tests, OK |
| T020+ | 6b71c94 | test_checklist.py: 15 tests, FAILED (failures=1) | e80b85e | test_checklist.py: 15 tests, OK |
| T032 | ff9b4c3 | test_manifests.py: 74 tests, FAILED (failures=1, errors=4) | 462cf7c | test_manifests.py: 74 tests, OK |
| T045+ | ceb68c9 | test_item_changes.py: 28 tests, FAILED (failures=1); test_gate.py: 61 tests, FAILED (failures=1) | 882d510 | test_item_changes.py: 28 tests, OK; test_gate.py: 61 tests, OK |

### Review by the project owner (T049, T056; T033 and T046 in part)

- **Date**: 2026-10-16. The project owner read the spec and behaviour checklist of every set: `examples/runs/compliant`, `examples/runs/frontend-planned`, the cart-total project of T017 to T046, and the Haiku runs of stories 01, 07 and 08. Reported verbatim in substance: the documents "look good". No omission, weakened outcome, duplicate or code-level wording was reported.
- **T049 (SC-009)** and the reviewer's notes of **T056** are taken as met by this review.
- **Still open, because they need a time**: T033 (judge a checklist against its spec in under ten minutes, SC-004), T046 (name the requirements and tests of three random items in under two minutes each, SC-003) and T057 (a new developer answers four questions in under five minutes, SC-008). Three items of the T046 project were picked at random for the owner to answer: BI-006, BI-001 and BI-002.
