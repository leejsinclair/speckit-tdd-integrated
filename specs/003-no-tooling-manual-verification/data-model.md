# Data Model: Verification Only Where It Is Possible

Entities are documents or tables of the feature directory. Existing ones are described in
[001](../001-integrated-tdd/data-model.md) and [002](../002-bdd-behaviour-checklist/data-model.md);
only what changes is here.

## Verification Command (changed)

| Field | Rule |
|-------|------|
| ID | Lowercase letters, digits and hyphens, or the single word `None` |
| Command, Scope, Source | As before. A `None` row has `-` in all three |

`None` is valid only as the only row. `plan.no_tooling` is true when it is. A `None` row
with other rows is an M-level finding in `plan` (EC-02, FR-007).

## Manual Check (new, a row of `### Manual verification` in plan.md)

| Field | Rule |
|-------|------|
| ID | `MV-` and three or more digits; unique in the plan |
| Covers | One or more ids, each a requirement or scenario of the spec or an obligation of the plan (M2) |
| Steps | Non-empty text |
| Expected result | Non-empty text |
| Why not automated | Non-empty text |

A single row whose ID is `None` means no manual checks. A plan without the sub-heading has none.

## Deferral (new, a row of `## Deferrals` in the evidence document)

| Field | Rule |
|-------|------|
| ID | `DF-01`, `DF-02`, ... |
| Time | UTC, set by the script |
| Obligations | One or more `VO-` ids the plan holds |
| Reason | Non-empty, one line |
| Basis | `environment failure #N` where record N names an obligation and is classified `environment`; otherwise `other` |
| Needs approval | `no` when the basis is an environment failure, otherwise `yes` |
| Approved by | A name, or `-`. Set by `approve`; not part of the chain value |
| Check | Chained value over the row and the previous row's value |

A deferral **stands** when Needs approval is `no`, or Approved by holds a name.

## Manual Result (new, a row of `## Manual results`)

| Field | Rule |
|-------|------|
| ID | `MR-01`, ... |
| Time | UTC |
| Check | An `MV-` id the plan holds |
| Result | `pass` or `fail` |
| Recorded by | A name; required |
| Note | Free text, may be `-`; not part of the chain value |
| Check value | Chained as for Deferral, in a chain of its own |

The latest row for a check is its state: `open` when it has none.

## Obligation status (changed)

`planned`, `in progress`, `verified`, `blocked`, `failed`, and now `deferred`.

| State | When |
|-------|------|
| verified | As before. Takes precedence over deferred |
| deferred | Not verified, and `plan.no_tooling`, or a standing Deferral names the obligation |
| blocked, failed, in progress, planned | As before |

Reason shown with `deferred`: `no test tooling`, or the Deferral's Reason.

## Behaviour item status (changed)

Adds `manual`: an item that names only manual checks. It is shown with the latest result
(`open`, `pass` or `fail`) and is never `verified`.

## Relationships

```text
Plan ── has 0..n ── Manual Check ── covers ──> Requirement | Scenario | Obligation
Evidence ── has 0..n ── Deferral ── names 1..n ──> Obligation
Evidence ── has 0..n ── Manual Result ── records ──> Manual Check
Behaviour Item ── Verified by 0..n ──> Obligation | Exemption | Manual Check
```

## Rules on the chain

| Rule | Statement |
|------|-----------|
| M1 | Each Manual Check has a unique `MV-` id and non-empty Covers, Steps, Expected result and Why not automated |
| M2 | Each id a Manual Check covers exists |
| G12 | Each Deferral naming a task's obligation has a reason, and one needing approval has an approver |
| C9 | No test tooling is recorded and runs or a baseline exist, or a command is declared as well |
| C4 (extended) | The two new tables' chains verify |
| B2 (extended) | An item may name an `MV-` id the plan holds |

## State transitions

```text
Obligation:  planned -> in progress -> verified
                  \-> deferred -> verified   (a later passing run)
                  \-> blocked  -> deferred   (a standing deferral)
Deferral:    recorded (basis environment) -> stands
             recorded (basis other) -> waits -> stands   (approve DF-nn --by NAME)
Manual check: open -> done (pass | fail) -> done (latest result wins)
```
