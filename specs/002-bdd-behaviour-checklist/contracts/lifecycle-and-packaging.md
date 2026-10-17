# Contract: lifecycle stages, packaging and deliverables

**Feature**: `002-bdd-behaviour-checklist` | **Data model**: [data-model.md](../data-model.md)
| **Base contracts**: [001 artefact formats](../../001-integrated-tdd/contracts/artefact-formats.md),
[001 packaging](../../001-integrated-tdd/contracts/packaging.md)

What changes in the preset, the extension's non-script files, and the repository's
documentation and examples. No command is added, and the order of the stages is unchanged
(FR-002, SC-005).

## 1. What each lifecycle stage adds

The table extends section 4 of the 001 artefact formats contract. "Older feature" means a
feature whose Verification Plan has no `### Behaviour checklist` sub-heading and that has
no `tests/behaviour-checklist.md`.

| Stage | Added by this feature | For an older feature |
|-------|-----------------------|----------------------|
| `/speckit-plan` | After the Verification Plan, write `tests/behaviour-checklist.md` from the template, following "Behaviour checklist" in the process rules. The `plan` check now covers it. When the plan already exists without the sub-heading (Spec Kit does not recopy the template), add the sub-heading first. The Completion Report names the checklist's location, the number of items and sections, the result of the check, and asks for the checklist to be reviewed against the specification; it requests and awaits no approval (FR-028, FR-029) | Rerunning the stage brings it under the checklist rules: the sub-heading is added and the checklist written. Evidence already at the top level stays there (FR-043) |
| `/speckit-tasks` | No new label. The `tasks` check reports B7 | Report the missing checklist as a gap, name the plan stage, carry on as in 0.1.0 (FR-006) |
| `/speckit-analyze` | The findings of B1 to B7 appear under the "Verification coverage" heading with the other findings; nothing is modified (FR-026) | As for tasks |
| `/speckit-implement` | Before the first task, `plan` and `tasks` already run and must pass, now including the checklist; the baseline is refused while the checklist fails. A Red run is refused for an obligation no item names. A change to a fixed item is recorded with `expectation --item`. The final report lists every behaviour item that is not verified, with the reason, from `status` (FR-035) and points the reviewer to `tests/tdd-evidence.md` or, for an older feature, `tdd-evidence.md` | As for tasks; implementation otherwise proceeds as in 0.1.0 |

## 2. Preset files

| File | Change |
|------|--------|
| `preset/templates/plan-addendum.md` | After the Verification exemptions table, a fourth sub-heading `### Behaviour checklist` with the fixed line `Behaviour items are in [tests/behaviour-checklist.md](tests/behaviour-checklist.md).` and a comment saying the heading is read by the checks and must be kept |
| `preset/commands/speckit.plan.md` | A step "Behaviour checklist" after step 3 of "Verification Plan" and before the check; the Completion Report text above |
| `preset/commands/speckit.tasks.md` | The older-feature gap; B7 named among the findings of the check |
| `preset/commands/speckit.analyze.md` | The older-feature gap; B1 to B7 described among the findings |
| `preset/commands/speckit.implement.md` | The older-feature gap; the refusals of baseline and Red; recording an item change; the final report; the evidence location |
| `preset/templates/tasks-addendum.md` | One sentence: a test task's obligations must each be named by a behaviour item |
| `preset.yml` | Version only |

Strategies stay `append` and `wrap`, so the preset still composes with others (F5 in
[research](../research.md)).

## 3. Extension files

| File | Change |
|------|--------|
| `templates/behaviour-checklist-template.md` | **New**: the template of the [checklist contract](./behaviour-checklist.md#1-the-template) |
| `templates/tdd-process-rules.md` | A new section "Behaviour checklist" between "Verification intent" and "The Red, Green, Refactor cycle", covering: when it is written and by which stage; where it lives and why not in `checklists/`; one section per scenario with the scenario quoted word for word; items as refinements that keep the scenario's terms and every outcome, none weaker; what an item must not name; proportion and no duplicate items; no status; corrections go to the specification or Verification Plan first; and how items are fixed at the baseline and changed afterwards. "Traceability and review evidence" gains the behaviour item in the chain. Every mention of the evidence location names both locations |
| `extension.yml` | A third entry under `provides.templates`: `behaviour-checklist-template`, `templates/behaviour-checklist-template.md`. Version |
| `commands/speckit.integrated-tdd.gate.md` | No change: the event and its matcher are unchanged |

## 4. Repository deliverables

| Deliverable | Change |
|-------------|--------|
| `README.md` | "What changes in an existing Spec Kit project" gains rows for the checklist, the `tests/` folder, the evidence location and the `plan.md` heading guard. "How it works" gains the checklist in the plan, tasks, analyze and implement rows. A new section "The behaviour checklist" states when it is written, by which stage, where it lives, what each item contains and links to, what it must not contain, and its relationship to `spec.md`, `plan.md` and `tasks.md`, with the full trace and how a reviewer uses it (FR-036, FR-037). "Observable criteria" gains this feature's success criteria. "Known limits" revises the `plan.md` limit and adds the limits of B5 and of wording closeness. "Requirements" names Spec Kit 1.1.3 as tested |
| `CHANGELOG.md` | A release entry: the new artefact, the changed stage behaviour, the new rules and gate rule, the evidence location, the `plan.md` guard, and the effect on features planned before the change (FR-040) |
| `docs/evaluation.md` | How to judge a checklist against its specification, how to read the item table of the Summary, and story 08 |
| `examples/runs/compliant/` | Regenerated by a real run (research D11); holds `tests/behaviour-checklist.md` and `tests/tdd-evidence.md` |
| `examples/runs/frontend-planned/` | **New**: `spec.md`, `plan.md` and `tests/behaviour-checklist.md` of a small screen feature; passes `plan` |
| `examples/runs/README.md` | Describes the frontend example and the new layout |
| `examples/stories/08-behaviours-from-the-code.md` | **New** story with its expected behaviour (FR-039) |
| `examples/stories/01` to `07` | Each story's expected-behaviour checklist gains the behaviour checklist where the story reaches planning |
| `tests/` | New and changed tests and fixtures (quickstart scenario 1) |

## 5. Effect on an adopting project

| Situation | Effect |
|-----------|--------|
| A new feature | Gains `tests/behaviour-checklist.md` and keeps its evidence in `tests/tdd-evidence.md`. The checklist must pass before implementation, and items are fixed from the baseline |
| A feature planned before the change, not yet implemented | No checklist rule applies; the stages report the gap. Its first evidence document is written to `tests/` |
| A feature with evidence at the top level | The evidence stays where it is. No checklist rule applies unless the plan stage is rerun, which adds the sub-heading and the checklist |
| `checklists/` | Unchanged. The core implement step's scan of it behaves as before and does not see the behaviour checklist |
| Removal | As in 0.1.0. Both files in `tests/` stay as readable Markdown |
