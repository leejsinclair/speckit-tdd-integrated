## Verification Plan

<!--
  Added by the Integrated TDD preset and filled by the plan stage as a Phase 1 output.
  The heading text, the three sub-headings and the three header rows are fixed: a check
  script reads them. Replace the example rows. This section holds no status: what is
  verified is derived from the evidence in tdd-evidence.md, never written here.
-->

### Verification commands

<!--
  The ways this project already runs its tests, taken from what the project defines
  (package scripts, a Makefile, CI configuration, contributor documentation).
  ID: short, lowercase letters, digits and hyphens. Command: in backticks, with at most
  one {select} where a test selector goes. Scope: focused (run per increment) or broad
  (run at checkpoints). Source: where the project defines the command.
  If the project has no runnable test command, leave the table empty and raise the gap.
-->

| ID | Command | Scope | Source |
|----|---------|-------|--------|
| [id] | `[the project's own command, with {select} where a selector goes]` | focused | [where it is defined] |
| [id] | `[the project's own command for the whole suite]` | broad | [where it is defined] |

### Verification obligations

<!--
  One row per scenario that must be verified. ID: VO- and three digits, numbered in
  order of creation and never reused. Requirements: the FR-, SC- and acceptance scenario
  ids (USn-ASm, scenario m of user story n) from spec.md that the row verifies, with
  DC-nn for a design constraint and EC-nn for an edge case, each stated in the Scenario
  cell. Expected outcome: what must be observed, stated without reference to how the code
  will be written. Level: unit, integration, contract, end-to-end or other. Origin:
  planned, or discovered when added during implementation.
-->

| ID | Requirements | Scenario | Expected outcome | Level | Origin |
|----|--------------|----------|------------------|-------|--------|
| VO-001 | [FR-001, US1-AS1] | [The situation to test, in terms of behaviour] | [What must be observed] | [level] | planned |

### Verification exemptions

<!--
  One row per requirement that will not be verified automatically, with the reason and
  how it is verified instead (or none, with why). A single row reading None in the
  Requirement column when there are no exemptions.
-->

| Requirement | Reason | Alternative verification |
|-------------|--------|--------------------------|
| None | - | - |
