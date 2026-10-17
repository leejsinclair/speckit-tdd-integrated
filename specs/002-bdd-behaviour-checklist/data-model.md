# Data Model: BDD Behaviour Checklist

**Feature**: `002-bdd-behaviour-checklist` | **Date**: 2026-10-16 | **Spec**: [spec.md](./spec.md)

This feature adds entities to the model of
[001-integrated-tdd](../001-integrated-tdd/data-model.md) and changes three. Entities of
001 that are not listed here are unchanged. All data is Markdown in the feature directory;
nothing is stored anywhere else.

```text
specs/<feature>/
├── spec.md                    # Requirement, Acceptance Scenario (read)
├── plan.md                    # Verification Plan, now with a Behaviour checklist sub-heading
├── tasks.md                   # Task (read)
├── checklists/                # Spec Kit's own checklists: unchanged and not read
└── tests/                     # Feature tests folder (new)
    ├── behaviour-checklist.md # Behaviour Checklist: written by the agent at the plan stage
    └── tdd-evidence.md        # Evidence Document: written only by the check script
```

## Entities

### Acceptance Scenario (changed)

One numbered scenario under a user story's **Acceptance Scenarios** in `spec.md`.

| Field | Source | Rule |
|-------|--------|------|
| id | Derived: `USn-ASm`, scenario `m` of user story `n` | As in 001 |
| text | The numbered line and any indented lines that continue it, without the number | **New.** Read so that rule B6 can compare a checklist quote with it |

### Verification Plan (changed)

The `## Verification Plan` section of `plan.md`.

| Field | Rule |
|-------|------|
| Behaviour checklist marker | **New.** A `### Behaviour checklist` sub-heading, after the three tables, holding one fixed line that links to `tests/behaviour-checklist.md`. Its presence makes the checklist rules apply (research D5) |

The three tables and their headers are unchanged. The runtime event refuses an edit
through the agent's tools that would remove `## Verification Plan` or
`### Behaviour checklist` from a `plan.md` that holds it.

### Feature Tests Folder (new)

The `tests/` folder of a feature directory. It holds verification artefacts *about* the
feature: the Behaviour Checklist and, for a feature with no evidence before this change,
the Evidence Document. It is not where the project's executable tests live, and Spec Kit
neither reads nor writes it.

### Behaviour Checklist (new)

`tests/behaviour-checklist.md`. Written by the coding agent during the plan stage, from
`spec.md` and the Verification Plan, starting from the extension's
`behaviour-checklist-template.md`. Read by the check script. Format:
[behaviour-checklist contract](./contracts/behaviour-checklist.md).

| Field | Rule |
|-------|------|
| sections | One Scenario Section per acceptance scenario in `spec.md`, then at most one Other Behaviours Section |
| items | Every Behaviour Item, each in exactly one section |
| status | **None.** The file holds no checkbox and no status label (FR-014, rule B4) |

**Applies to a feature** when the Verification Plan holds the Behaviour checklist marker,
or when the file exists. Otherwise the feature was planned before this change and no
checklist rule is applied to it (EC-01).

### Scenario Section (new)

A `## USn-ASm` heading in the checklist.

| Field | Rule |
|-------|------|
| scenario | The heading's id. Must be an acceptance scenario of `spec.md` (B6), and appear once |
| quote | The block quote directly under the heading. After normalisation it must equal the scenario's text in `spec.md` (B6, FR-017) |
| items | One or more Behaviour Items, each naming this scenario and no other (B6) |

### Other Behaviours Section (new)

The `## Other behaviours` heading. Holds items that refine no acceptance scenario: a
requirement with no scenario of its own, an edge case with its own outcome, a success
criterion the Verification Plan verifies (EC-08). Its items name no scenario.

### Behaviour Item (new)

One observable behaviour.

| Field | Format | Rule |
|-------|--------|------|
| id | `BI-` and three or more digits | Unique in the file (FR-007, B4), and never reused once its item has been removed: an id with an accepted removal that appears in the checklist again is reported by G10 and C8, and no change record accepts it (FR-007) |
| expresses | `Expresses:` and a comma-separated list of `FR-`, `SC-`, `USn-ASm` and `EC-` ids | At least one. `FR-`, `SC-` and scenario ids must be in `spec.md`; an `EC-` id must occur in `spec.md` as a whole word, so it is checked whether or not the specification numbers its edge cases (FR-009, FR-020, B6) |
| verified by | `Verified by:` and a comma-separated list of `VO-nnn` ids and `exemption <requirement id>` entries | At least one. Each obligation must be in the Verification obligations table; each exemption must be a row of the Verification exemptions table (FR-010, B2) |
| given | One `**Given**` clause, then any `**And**` clauses | Required (FR-008, B4) |
| when | One `**When**` clause, then any `**And**` clauses | Required, after Given |
| then | One `**Then**` clause, then any `**And**` clauses | Required, after When |
| fingerprint | Derived: the first six hexadecimal characters of SHA-256 over the clauses, each as `<keyword> <text>`, normalised, joined by line breaks | Not written in the checklist. Excludes the id and the trace links, so linking a discovered obligation to an existing item is not a change |

Clause text states what is observable at the boundary the specification describes, and
names no element of how the feature is built (FR-011, FR-012). The repeatable part of that
rule is B5; the rest is for the process rules and the reviewer.

Relationships: many-to-many with Requirement and Acceptance Scenario through *expresses*;
many-to-many with Verification Obligation and Verification Exemption through *verified by*
(EC-04).

### Item Baseline (new)

The content of the items as they were when implementation began, kept in a new table of
the Evidence Document, `## Behaviour items at baseline`. Written only by the check script.

| Field | Rule |
|-------|------|
| item | A Behaviour Item id |
| verified by | The item's *verified by* list at the time, so that a removed item can still be traced to its obligations' tasks |
| fingerprint | The item's fingerprint at the time |
| seq | The sequence number of the record at which the row was taken |

**When rows are written**: on every `run` that records a record, the script adds a row for
each item in the checklist that has no row yet. The first such run is the baseline, so
every item written during planning is fixed at the baseline (FR-033); an item added during
implementation is fixed at the first run after it appears. A row is never changed or
removed.

### Item Change Record (new)

A change to a fixed item, recorded in a new table of the Evidence Document,
`## Behaviour item changes`, with `expectation --item`.

| Field | Format | Rule |
|-------|--------|------|
| id | `BX-` and two or more digits | Next unused |
| time | UTC timestamp | Set by the script |
| item | `BI-nnn` | Must have an Item Baseline row |
| requirements | Requirement ids | At least one. The requirement the change is justified against |
| justification | Text | Required |
| alters behaviour | `yes` or `no` | `yes` when the change alters intended behaviour; it then needs an approval |
| approved by | A name, or `-` | Set with `approve --id BX-nn --by <name>` |
| new fingerprint | Six hexadecimal characters, or `removed` | The item's fingerprint when the change was recorded, or `removed` when the item was no longer in the checklist |

An item is **unchanged** when its current fingerprint equals its baseline fingerprint, or
equals the new fingerprint of an accepted change record for it. A change record is
**accepted** when it alters no behaviour, or when it has an approval. A removed item is
unchanged only when an accepted change record with `removed` exists for it. An item whose
id has such a record and that is in the checklist again is **reused**: it is never
unchanged, and `expectation --item` refuses to record a change for it. The new behaviour
takes a new id.

### Item Status (new, derived)

The verification state of a Behaviour Item. Never stored. Derived from the statuses of the
obligations it names, which are derived from the records as in 001.

| Status | When |
|--------|------|
| `exempt` | The item names exemptions only |
| `verified` | Every obligation it names is verified |
| `failed` | Not verified, and an obligation it names is failed |
| `blocked` | Not verified or failed, and an obligation it names is blocked |
| `in progress` | None of the above, and an obligation it names is in progress or verified |
| `planned` | Every obligation it names is planned |

An item that names obligations and exemptions is judged on its obligations alone, and the
exemption is shown beside its status. An item is never `verified` while any obligation it
names is not (FR-034).

### Evidence Document (changed)

`tdd-evidence.md`, written only by the check script.

| Aspect | Rule |
|--------|------|
| Location | **Changed.** At the top of the feature directory when a document is already there and none is in `tests/`; otherwise `tests/tdd-evidence.md`. When both exist, nothing is read, recorded or chosen (FR-041 to FR-044, research D10) |
| Tables | **New**, present only when the checklist rules apply: `## Behaviour items at baseline` and `## Behaviour item changes`, after `## Decisions`. A document without them reads as having both empty, so documents written before this change parse unchanged |
| Summary | **Changed** only when the checklist rules apply: it gains the behaviour item table, items not verified, and unrecorded item changes (research D9). Otherwise it is generated exactly as before |

Neither new table is chained into the check values of the record table. The baseline
table can only grow, and the compliance check reports an Item Baseline row whose item is
missing without an accepted removal.

### Trace Link (new, derived)

A reference that joins two entities. The chain a reviewer follows is:

```text
Requirement / Acceptance Scenario
  └─ named by ─ Behaviour Item (expresses)
                  └─ verified by ─ Verification Obligation | Verification Exemption
                                     └─ named by ─ Task (label)
                                                     └─ Test Execution Record (task, obligations, selector)
```

Every link is held at its lower end, by id, and no text is copied along the chain except
the scenario quote of D4, which B6 keeps identical.

## Rules on the chain

| Rule | Where checked | Statement |
|------|---------------|-----------|
| B1 | `plan` | Every `FR-` requirement and acceptance scenario is named by at least one item |
| B2 | `plan` | Every item names an obligation or exemption, and only ones the plan holds |
| B3 | `plan` | Every obligation is named by at least one item |
| B4 | `plan` | Every item has a valid unique id and Given, When and Then in order; no checkbox or status |
| B5 | `plan` | No item names a path, or a design identifier, that the specification does not |
| B6 | `plan` | Every reference to the specification exists; every scenario section quotes its scenario exactly; every item sits in the section of the scenario it names |
| B7 | `tasks` | Every test task's obligations are named by at least one item |
| G10 | `gate`, and the event | A task cannot be completed while an item naming one of its obligations is changed or removed without an accepted change record, or reuses a removed item's id |
| G11 | `gate`, and the event | Once the baseline exists, no task can be completed while the checklist fails `CHECKLIST` or any of B1 to B7 |
| C8 | `compliance` | The checklist exists and passes B1 to B7, no item is changed or removed without an accepted change record, and no id is reused |
| Baseline refusal | `run --phase baseline` | Refused, exit 2, while any of B1 to B6 fails |
| Red refusal | `run --phase red` | Refused, exit 2, when an obligation named is named by no item |

Every rule above applies only when the checklist rules apply to the feature. For a
feature planned before this change, the checks behave exactly as in 001.

## The task gate, extended

001's gate applies G1 to G9 to a task. G10 and G11 are added after G9:

**G10.** For each obligation on the task, every item that names it, or that named it at the
baseline, is unchanged. Each finding names the item and says whether it was changed,
removed, changed with a record that awaits approval, or reused.

**G11.** When the evidence holds a baseline record, the checklist passes `CHECKLIST` and B1
to B7, whether or not the task names an obligation. Each finding names the task and
carries the checklist finding with its rule. Before the baseline, G11 does not apply: the
baseline refusal already covers that period.
