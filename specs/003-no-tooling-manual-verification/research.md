# Research: Verification Only Where It Is Possible

Each decision names the code read to reach it (`scripts/python/tdd_check.py`, line numbers
as of commit `822dc9f`) and what was rejected.

## D1. How "no test tooling" is represented

**Decision**: a single row whose `ID` cell is `None` in the plan's `### Verification
commands` table, the same convention the exemptions table already uses (`parse_plan`,
line 433: `row["Requirement"].lower() == "none"` is skipped). `parse_plan` sets
`plan.no_tooling = True` when that row is the only one and skips it as a command.

**Rationale**: the table already exists in every plan, so no new document or heading is
needed (Principle I), and an old reader sees an empty commands table plus a clear word.

**Alternatives**: an empty table (indistinguishable from "the agent forgot", which must
stay a finding); a new `### Test tooling` heading (a second place to keep in step); a
flag in `extension.yml` (project-level, not per feature, and a new manifest field).

## D2. The mode is derived, never stored

**Decision**: nothing is recorded in the evidence when a feature has no test tooling.
`obligation_status` reports `deferred` with reason "no test tooling" for every obligation
while `plan.no_tooling` holds (FR-012). Declaring a command removes the `None` row and the
derived state disappears, so FR-007 and SC-004 need no switch to flip.

**Rationale**: a stored mode could disagree with the plan. The plan is the one source.

**Consequences, read from the code**:

- `require_baseline` (line 1102) is called only by `run`, which needs a declared command
  (`validate_run`, line 1110). In this mode nobody calls `run`, so no baseline is demanded.
  `run` called anyway still refuses; its message gains "the plan records no test tooling".
- `gate_g11` (line 2101) applies only after a baseline is recorded. With no baseline it
  would never hold a task for a failing checklist. It gains `or plan.no_tooling` so the
  checklist rules apply in this mode (FR-005).
- Behaviour items are fixed at the baseline (`fix_new_items`, line 1233). With no baseline
  they stay editable. This is a stated limit: there is no first run to fix them at.
- EC-04: recorded runs plus `None` is a contradiction. Rule C9 reports it (D9).

## D3. Deferral: a new chained table and a `defer` subcommand

**Decision**: a deferral is a row in a new `## Deferrals` table of the evidence document
with its own chain, written by a new `defer` subcommand:

| Column | Meaning |
|--------|---------|
| ID | `DF-01`, `DF-02`, ... |
| Time | UTC |
| Obligations | one or more `VO-` ids |
| Reason | non-empty text, for example `needs queue` |
| Basis | `environment failure #N` (a record classified `environment` that names the obligation) or `other` |
| Needs approval | `no` for an environment basis, `yes` for `other` |
| Approved by | a name, or `-` (not part of the chain value) |
| Check | chained value, as for Test Execution Records |

**Rationale**: FR-008 asks for a tamper-evident record and FR-008A for approval unless the
basis is a recorded environment failure. The records table is the only chained table
(`UNCHAINED_CELLS`, line 195; `check_value`, line 893), and `check_value(previous, cells)`
is generic, so a second chain is a few lines. `cmd_classify` (line 1416) shows the pattern
of an unchained cell inside a chained row.

**Alternatives**:

- *A new exception kind `deferred`.* Reuses G7 and `approve` with no new table, but the
  Exceptions table is not chained (README, Known limits), so FR-008 would not hold, and
  `exception` means "replace the Red run", which G4 still follows with a passing run.
- *A new phase `defer` in Test Execution Records.* Rejected in Complexity Tracking.

**`defer` refuses** an obligation the plan does not hold, an empty reason, and any call in
no-tooling mode ("every obligation is already deferred"). It never writes an approval.

## D4. Gate rules

**Decision**:

- **G3 and G4** (lines 1941, 1974) skip an obligation that is deferred and whose deferral
  stands. A deferral stands when it is complete: its basis is `environment failure` or it
  has an `Approved by` name. A later passing run does not need the skip (D5).
- **G6** (line 2027) ignores failure records whose obligations are all deferred and
  standing, so an unreachable service does not hold the task. The record is still required
  to be classified, because that classification is what makes the basis `environment`.
- **G12 (new)**: each deferral naming one of the task's obligations is complete: it has a
  reason, and a basis of `other` has an approver (FR-008A). It mirrors G7 (line 2044) and
  uses the same message form: `G12 T014 DF-02: needs approval and has no approver`.
- G5, G7, G8, G9, G10 and G11 are unchanged except G11 (D2).

**Rationale**: FR-009 says a standing deferral never holds a task, and the one exception is
an unapproved non-environment deferral. G12 is that exception.

## D5. A new obligation status, `deferred`

**Decision**: `obligation_status` (line 2187) returns `deferred` when no verifying
evidence exists and either `plan.no_tooling` holds or a standing deferral names the
obligation. Order of the tests:

1. `verified` is computed first, as today. A passing run after the Red record, or after an
   exception, wins over a deferral (FR-011, EC-05, US2 scenario 5).
2. `deferred` comes before the "latest record is a failure" return. An environment failure
   followed by a standing deferral reads `deferred`, not `blocked`. A deferral without an
   approver (basis `other`) does not stand, so the status falls through as today.
3. `blocked`, `failed`, `in progress` and `planned` follow as today.

`environment-blocked` exceptions are kept: a developer who wants the work held records one
instead of deferring (FR-013). If both exist, the deferral wins; the developer removes the
deferral by not approving it, because only a non-environment deferral needs approval.
This ordering is tested.

## D6. The Manual verification table in the plan

**Decision**: a `### Manual verification` sub-heading in the Verification Plan, after
`### Verification exemptions`, with the header `| ID | Covers | Steps | Expected result |
Why not automated |`, rows `MV-001`, ... or a single `None` row.

- **M1** (plan check): every row has an `MV-` id that is unique, a non-empty `Covers`,
  `Steps`, `Expected result` and `Why not automated`.
- **M2** (plan check): each id in `Covers` is a requirement or scenario of the spec
  (`requirement_problem`, line 1524) or an obligation of the plan.

**Back-compat** (FR-022, EC-09): the table is optional. `read_table` reports a missing
heading as a finding (line 296), so the new code calls `find_table` and treats "no heading"
as an empty list. The plan template addendum gains the sub-heading; the plan wrapper adds
it to a plan that lacks it, as it already does for `### Behaviour checklist`.

**Alternatives**: extending the exemptions table with a Steps column (changes a fixed
header that existing plans use); a separate `manual-checks.md` (a new mandatory document).

## D7. Manual results: a chained table and a `manual` subcommand

**Decision**: `## Manual results` with columns `ID, Time, Check, Result, Recorded by, Note,
Check value`, written by `manual --check MV-001 --result pass|fail --by NAME [--note ...]`.
`--by` is required and not defaulted. The latest row per check is its state. The script
refuses a check the plan does not hold. Recording is optional for everything else: no gate
or rule reads it except status and compliance.

**Rationale**: same chain as D3. The name is recorded, not verified (limit 2 under III).

## D8. The behaviour checklist and manual checks

**Decision**: an item's `Verified by:` may name `MV-` ids, as it may name exemptions.

- **B2** (line 1720) accepts an `MV-` id that the plan holds, and still requires at least
  one obligation, exemption or manual check.
- **B3** (every obligation is named by an item) is unchanged.
- **Item status** (`item_status`, line 2227) gains `manual` for an item that names only
  manual checks, shown as `manual (open)` or `manual (pass|fail)`, and is never `verified`
  (FR-018). A mixed item is judged on its obligations only, as for exemptions today.

## D9. Reporting

**Decision**:

- `status` (`review_view`, line 2346) gains a `Not verified` list with each deferred
  obligation and its reason, each open manual check, and the line `no test tooling:
  nothing is verified by tests` when D2 holds. Counts: `verified N, deferred N, manual N`
  (FR-021). The stored Summary is the regenerated view, so C7 keeps working.
- `compliance` (`cmd_compliance`, line 2644) prints the same items as lines beginning
  `notice:` and returns them in the result's data. They are not findings, so the exit code
  and `COMPLIANT` are unchanged (FR-020, SC-003).
- **C9 (new)**: a finding when the plan records no tooling and the evidence holds runs or a
  baseline (EC-04), or when it records no tooling and also declares a command (EC-02,
  FR-007; the second case is also an M-level finding in `plan`, because it is a plan
  defect).
- `rule_c7` (line 2606) flags only `planned` and `in progress`. `deferred` is not flagged.
  A pre-existing observation: `blocked` and `failed` also appear not to be flagged; that is
  outside this feature and is recorded for a later change.

## D10. Older features and unused tables

**Decision**: absent `### Manual verification`, `## Deferrals` and `## Manual results` read
as empty. The evidence template and `render_evidence` (line 989) write the two evidence
tables only when they hold rows or when `defer` or `manual` first runs, as 002 did for the
item tables (line 628). A feature with a declared command and neither table renders and
checks byte-for-byte as under 0.2.0 (SC-006).

## D11. Wrappers, rules and addenda

**Decision**: Markdown only.

- **Plan wrapper**, step 1 (commands): if there is no way to run tests, write the `None` row,
  say the project has no test tooling, say the process never chooses a framework and that
  declaring a command later switches the checks on, and carry on. Step 5 gains Manual
  verification. The completion report counts obligations and manual checks.
- **Tasks wrapper**: the "plan first, generate nothing if it fails" rule is kept; the plan
  no longer fails for a missing command. In this mode test tasks are generated as usual.
- **Implement wrapper**: in no-tooling mode, do not run `run`, do not choose a framework,
  write a test only where the project already has a place for it, mark tasks complete, and
  report "nothing verified by tests". For an unreachable service: classify the failure as
  `environment`, then `defer`. Report the counts of FR-021.
- **Analyze wrapper**: copies the notices into its report.
- **Process rules**: a new section "When verification is not possible", placed after
  "Exceptions", stating the three cases, who may defer, that nothing deferred is reported
  as verified, and that a person's record is theirs.
- **Wording tests** (`test_manifests.py`, line 140, `TOOL_NAMES`): the wrappers still name
  no framework.

## D12. Spec Kit mechanisms (Principle V)

**Decision**: no new mechanism. The plan-template append, the four `wrap` commands and the
extension template are those confirmed against 1.1.3 for 001 and 002. No manifest field
is added, so no re-examination of the schema is needed. The installation tests of 002 are
re-run for 0.3.0 as a regression check.

## D13. Performance

**Decision**: `test_performance.py` gains a feature with 50 deferrals and 50 manual
checks on top of the 200-item case. Limits stay 1 second for the event handler and 2 for
checks. Parsing two more small tables does not change the order of the work (one pass
per table). Recorded as the same exception as 002: measured on existing-shaped code, so
the first run is expected to pass; the scale knob `TDD_PERF_SCALE` shows the limit is
reachable.

## D14. One file

**Decision**: the script stays a single file. A split would change the install tree and the
README's description of the extension, for no behaviour.

## D15. What is deliberately not done

- The process does not propose, choose or install a framework, and does not write example
  tests for a project that has none. The original request mentioned choosing a modern
  framework with example tests; the answer on 2026-10-17 was to warn and continue. A
  later feature could add an optional, developer-approved setup task.
- No setting to make all-deferred fail (clarification of 2026-10-17).
- A level of `integration` or `end-to-end` still does nothing by itself; the developer or
  the agent chooses to defer.
