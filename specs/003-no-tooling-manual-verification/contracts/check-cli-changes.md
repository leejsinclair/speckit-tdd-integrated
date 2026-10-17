# Contract: Check CLI changes

All other subcommands, options, output and exit codes are those of 0.2.0 for a feature that
has a declared command and no deferral or manual check (SC-006). Exit codes: 0 success, 1
findings, 2 usage or refusal. `--json` output carries the same data as the text.

## `defer`

```text
tdd_check.py defer --vo VO-002 [--vo VO-003 ...] --reason "needs queue" [--feature-dir DIR]
```

- Requires the plan to hold each obligation; a non-empty `--reason`.
- Refuses with exit 2, recording nothing, in no-tooling mode: `every obligation is already
  deferred: the plan records no test tooling`.
- Basis: `environment failure #N` when record N names the obligation and is classified
  `environment` (the latest such record); otherwise `other` and Needs approval `yes`. With
  several obligations, each must have its own environment failure for Basis to be an
  environment failure; otherwise it is `other`.
- Appends one Deferral row to `## Deferrals`, creating the table. Prints
  `deferred VO-002 as DF-01 (environment failure #7)` or `... (needs approval: other)`.
- Never approves. A later `approve DF-01 --by NAME` records an approver.

## `manual`

```text
tdd_check.py manual --check MV-001 --result pass|fail --by NAME [--note TEXT]
```

- Requires the plan to hold the check, a result, and a non-empty `--by`.
- Appends one Manual Result row, creating the table. Prints `recorded MR-01: MV-001 pass by NAME`.
- No gate or rule requires it.

## `approve` (extended)

`approve DF-01 --by NAME` sets Approved by on a Deferral. Refused if the id does not exist
or the row does not need approval. Other ids behave as before.

## `plan` (extended)

- Passes with a commands table holding only `None`; the line becomes `plan: passed (no test
  tooling recorded)`.
- Adds M1 and M2 findings for the Manual verification table. A `None` row with other rows is
  a finding on the commands table.

## `tasks` (unchanged)

## `gate` and `hook` (extended)

G3, G4, G6 skip a deferred obligation (D4). G12 added: `G12 T014 DF-02: needs approval and
has no approver`. In no-tooling mode no gate rule needs a run. The hook's refusal text for
G12 names `approve DF-nn --by NAME` as the way forward.

## `run` (message only)

In no-tooling mode a run is refused as before, with the added words `the plan records no
test tooling`.

## `status` (extended)

Adds, after the obligation table, when any apply:

```text
Not verified
  VO-002 deferred: needs queue (DF-01)
  MV-001 manual: open
Counts: verified 1, deferred 1, manual checks 1 open
```

and, in no-tooling mode, `No test tooling: nothing is verified by tests`.

## `compliance` (extended)

Adds C9 as a finding. Lines beginning `notice:` list deferred obligations, open or failed
manual checks and the no-tooling state. Notices never change the exit code or the verdict.

## Evidence document

Two optional tables after `## Behaviour item changes`, in this order: `## Deferrals` with
header `| ID | Time | Obligations | Reason | Basis | Needs approval | Approved by | Check |`
and `## Manual results` with header `| ID | Time | Check | Result | Recorded by | Note |
Check value |`. Absent tables read as empty.
