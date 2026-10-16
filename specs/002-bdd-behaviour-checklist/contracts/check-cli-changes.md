# Contract: changes to the check script

**Feature**: `002-bdd-behaviour-checklist` | **Data model**: [data-model.md](../data-model.md)
| **Base contract**: [001 check script](../../001-integrated-tdd/contracts/check-cli.md)

This contract lists only what changes in `scripts/python/tdd_check.py`. Everything in the
base contract that is not mentioned here stays as it is: the options, the exit codes, the
output forms, the standard-library-only rule and the absence of network access.

**Compatibility rule.** For a feature the checklist rules do not apply to (no
`### Behaviour checklist` sub-heading and no `tests/behaviour-checklist.md`), every
subcommand gives exactly the output and exit code it gives in 0.1.0, except that a new
evidence document is written to `tests/` (section 2). No subcommand is added.

## 1. Common behaviour

| Aspect | Change |
|--------|--------|
| Reads | Also `tests/behaviour-checklist.md`, when the checklist rules apply |
| Writes | Only the evidence document, now at the path of section 2, and only by the recording subcommands. `run` creates `tests/` when it writes the first document there. The checklist is never written |
| Repeatability | Unchanged: the checking subcommands give the same output each time on the same files, including the new rules |

## 2. Evidence location

Every subcommand that reads or writes the evidence document finds it the same way:

| On disk | The evidence document is |
|---------|--------------------------|
| `tdd-evidence.md` only | `tdd-evidence.md` |
| `tests/tdd-evidence.md` only | `tests/tdd-evidence.md` |
| Neither | `tests/tdd-evidence.md`, created on the first write |
| Both | Not chosen. Every subcommand except `hook` exits 2, records nothing, and prints `evidence is in two places: tdd-evidence.md and tests/tdd-evidence.md; keep one and remove the other` |

Paths printed in findings and messages are relative to the feature directory, for example
`C6 tests/tdd-evidence.md: no baseline record`. For a document at the top level they read
`tdd-evidence.md`, as in 0.1.0.

## 3. Checking subcommands

### `plan`

After the 0.1.0 findings, and only when the checklist rules apply, also applies the
`CHECKLIST` rule and B1 to B6 of the
[checklist contract](./behaviour-checklist.md#4-rules). When the checklist is missing,
B1 to B6 are not applied and the one `CHECKLIST` finding is reported.

### `tasks`

After the 0.1.0 findings, and only when the checklist rules apply, also applies B7. A
missing or unreadable checklist gives the `CHECKLIST` finding.

### `gate`

Applies G10 and then G11 after G9, when the checklist rules apply (data model, "The task
gate, extended"). G11 applies only once the evidence holds a baseline record. `gate --all`
reports G10 and G11 for completed tasks as for the other rules.

Findings, for example:

```text
G10 T014 BI-003: changed since the baseline and no change is recorded
G10 T014 BI-005: removed since the baseline and no removal is recorded
G10 T014 BI-003: change BX-01 alters behaviour and awaits approval
G10 T014 BI-005: removed since the baseline and its id is reused
G11 T014 FR-046: B1: ...
G11 T014 BI-007: B5: ...
```

A G11 finding is `G11 <task id> <subject>: <rule>: <reason>`, where `<subject>`, `<rule>`
and `<reason>` are those of the checklist finding as `plan` or `tasks` prints it.

### `status`

When the checklist rules apply, the view gains, after the obligation table:

```text
| Behaviour item | Scenario | Obligations | Status | Tests |
|----------------|----------|-------------|--------|-------|
| BI-001 | US1-AS1 | VO-001 | verified | assert, pass |
| BI-002 | - | VO-002 | in progress | edge |
| BI-003 | US1-AS2 | exemption FR-003 | exempt | - |
```

and, on the Not verified line, each item that is not verified with its status. A line
**Item changes** lists each item change record, with its approval state, and each
unrecorded change. With `--scenarios`, `status` prints each scenario section's quote above
its items, so that a reviewer sees the specification's wording beside them (FR-017).
The JSON form gains the keys `items` and `item_changes`.

For a feature the rules do not apply to, the view, and so the stored Summary, is unchanged.

### `compliance`

Applies C8 after C7, when the checklist rules apply:

| Rule | Reports |
|------|---------|
| C8 | `CHECKLIST`, or any of B1 to B7, as `C8 <subject>: <rule>: <reason>`; and every item changed or removed since the baseline without an accepted change record, and every reused id |

C7 continues to compare the stored Summary with the regenerated view, which now includes
the item table, so a Summary that shows an item as verified when its obligations are not
is out of date and reported (FR-027).

## 4. Recording subcommands

### `run`

| Situation | Behaviour |
|-----------|-----------|
| `--phase baseline`, the checklist rules apply, and `plan` would report a `CHECKLIST` or B1 to B6 finding | Exit 2, nothing recorded. The message lists the findings and says that the checklist must pass before implementation begins |
| `--phase red`, the checklist rules apply, and an obligation named with `--vo` is in no item's Verified by list | Exit 2, nothing recorded. The message names the obligation and says to add it to an existing or new item first |
| Any phase, the checklist rules apply, and a record is written | Before the document is written, a row is added to `## Behaviour items at baseline` for each item that has none, with the sequence number of the record being written |

### `expectation`

A second form records an Item Change Record:

```text
expectation --item <BI-nnn> --requirement <id> ... --justification <text>
            [--alters-behaviour] [--approved-by <name>]
```

| Option | Contract |
|--------|----------|
| `--item` | Required for this form, and not allowed with `--task` or `--tests`. Exit 2 when the item has no baseline row |
| `--requirement`, `--justification` | Required, as for a test expectation change |
| `--alters-behaviour` | As for a test expectation change: the record then needs `approve` |

The record's New fingerprint is the item's current fingerprint, or `removed` when the item
is no longer in the checklist. Exit 2 when the item is unchanged, and when its id is reused
(data model, "Item Change Record"): no record accepts a reused id.

### `approve`

Also accepts a `BX-nn` id.

## 5. `hook`

| Situation | Exit | Standard error |
|-----------|------|----------------|
| The file is named `plan.md`, its directory's `plan.md` currently holds `## Verification Plan` or `### Behaviour checklist`, and the resulting content would lack a heading the current content has | 2 | "The Verification Plan and its Behaviour checklist sub-heading are read by the checks and cannot be removed through the agent's edit tools", naming the heading |
| The file is named `plan.md` and keeps both headings, or holds neither | 0 | Nothing |
| The file is `tdd-evidence.md` in a directory named `tests` whose parent's `plan.md` holds a Verification Plan | 2 | The 0.1.0 evidence refusal |
| The file is `tasks.md` and the feature's evidence is in two places | 2 | The artefacts cannot be read, with the message of section 2 |

The guard still follows the file: for `tasks.md` and `plan.md` the feature directory is
the file's own directory; for `tdd-evidence.md` it is the file's own directory, or the
parent when that directory is named `tests`. Files with any other name are allowed from the
path alone, before any file is read. The checklist itself is not guarded: changes to it
are detected by G10, G11 and C8.

**Limit, revised**: 0.1.0 recorded that `plan.md` is not guarded. Removing its two headings
through the agent's edit tools is now refused. A command added to the Verification
commands table still counts as declared whatever it runs, and an edit made through a shell
command is still not seen at the time.

## 6. Performance

Each limit of the base contract holds for a feature with 200 tasks, 1,000 records and 200
behaviour items: the `hook` decision in under one second, and each checking subcommand in
under two seconds.
