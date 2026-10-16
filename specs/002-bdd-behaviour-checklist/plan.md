# Implementation Plan: BDD Behaviour Checklist

**Branch**: `002-bdd-behaviour-checklist` | **Date**: 2026-10-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-bdd-behaviour-checklist/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Add a behaviour checklist to each feature: a reviewable list of observable behaviours, in
Given / When / Then form, refined from the specification's acceptance scenarios and linked
to the requirements they express and the verification obligations that test them. It is
written by the existing plan stage, checked by the existing `plan` and `tasks` checks, and
fixed once implementation begins, so that the chain from requirement to behaviour to
obligation to task to recorded run has no link the agent can quietly bend.

The technical approach, from [research.md](./research.md):

- **Where and what** (D1, D2, D3). `tests/behaviour-checklist.md` in the feature
  directory, outside `checklists/`, which the core implement step scans and stops on. One
  section per acceptance scenario, opening with the scenario quoted from `spec.md`, then
  items such as `- **BI-001** Expresses: FR-001, US1-AS1. Verified by: VO-001.` with
  Given, When, Then and And lines. The plan template's Verification Plan gains a
  `### Behaviour checklist` sub-heading that links to it.
- **Checks** (D4, D6). Rules B1 to B6 in `plan` and B7 in `tasks`: coverage of every
  requirement, scenario and obligation; links that exist; complete clauses; no path or
  design identifier the specification does not use; and each scenario quoted word for word,
  so a softened quote is a finding.
- **Hard stops** (D8). The baseline run is refused while the checklist fails, a Red run
  is refused for an obligation no item names, and after the baseline gate rule G11 holds
  every task while the checklist fails.
- **Freeze and drift** (D7, D9). At each run the script fingerprints any item not yet
  fixed. A later change or removal must be recorded with `expectation --item`, with an
  approval when it alters behaviour; gate rule G10 and compliance rule C8 enforce it. The
  Summary and `status` show each item with its obligations, tests and a derived status.
- **Older features and the evidence move** (D5, D10). Features without the sub-heading or
  a checklist are checked exactly as before. Evidence goes to `tests/tdd-evidence.md`
  unless a feature already has it at the top level. The runtime event guards both
  locations, and now also refuses edits that would remove the two Verification Plan
  headings from `plan.md`.

## Technical Context

**Language/Version**: Python 3.9 or later for the check script; Markdown for wrappers,
templates, rules, the checklist and documentation; YAML for the manifests

**Primary Dependencies**: Python standard library only, as in 001. Spec Kit CLI 1.1.3 as
the host, examined for this plan ([research](./research.md#findings-about-spec-kit-113))

**Storage**: Markdown files in the adopting project's feature directory: the new
`tests/behaviour-checklist.md`, the evidence document at its resolved location with two
new tables, and one new sub-heading in `plan.md`. No database

**Testing**: `unittest` with generated fixture feature directories and recorded Claude Code
payloads; Ruff; markdownlint; installation tests with the `specify` CLI in a throwaway
project; agent-driven behaviour by a person using the example stories, as in 001

**Target Platform**: As 001: any platform with Spec Kit and Python 3; full enforcement on
Claude Code; Linux and macOS

**Project Type**: Spec Kit customisation: changes to one preset and one extension, and to
their single-file check script

**Performance Goals**: The event handler decides in under 1 second, and every checking
subcommand finishes in under 2 seconds, for a feature with 200 tasks, 1,000 records and 200
behaviour items (research D13)

**Constraints**: Standard library only; no network. The script still writes only the
evidence document and never the checklist. Checking subcommands are deterministic. For a
feature the checklist rules do not apply to, every subcommand's output and exit code are
those of 0.1.0, except that an evidence document that does not exist yet is created in
`tests/` (Principle VI, change 1). No new command and no new subcommand. No test framework assumed

**Scale/Scope**: About 600 to 800 added lines in `tdd_check.py`; one new extension template;
edits to four wrappers, two template addenda and the process rules; about 40 new fixture
directories; one regenerated example run, one new planning example and one new story;
README, CHANGELOG and evaluation guide. Seven checklist rules, two gate rules, one
compliance rule

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Checked against constitution version 1.0.0.

| Principle | Gate | Before research | After design |
|-----------|------|-----------------|--------------|
| I. Integrate, Don't Add | No new command; no new mandatory document without a recorded reason; no parallel workflow | Pass, with one departure to record | Pass, with one recorded departure |
| II. Developers Stay Accountable | Ambiguity and consequential trade-offs go to a person; routine work does not; artefacts assessable by someone who took no part | Pass | Pass |
| III. Deterministic Checks, Agent Judgement | Objective conditions checked repeatably; a failed check blocks | Pass | Pass, with five recorded limits |
| IV. Test-First with Real Evidence | Executable components built test-first; exceptions recorded with an alternative | Pass | Pass, with the two exceptions approved for 001 |
| V. Verify Against Current Spec Kit | Mechanisms confirmed against the current source | Open: 1.1.3 not yet examined | Pass, conditional on installation tests A10 to A14 |
| VI. Compatible and Removable | Install and removal leave everything working; changes to behaviour justified and documented; no framework required | Pass | Pass, with three documented behaviour changes |
| No duplication (Additional Constraints) | Information held elsewhere is not copied into new artefacts | Departure to record | Pass, with one recorded departure |

**I. Integrate, Don't Add.** The checklist is written by the existing plan stage, checked
by the existing `plan` and `tasks` subcommands, and enforced at the existing baseline run,
gate and event (research D1, D6, D8). No command or subcommand is added: `expectation`
gains an `--item` form and `status` a `--scenarios` option. The one departure is the new
document, `tests/behaviour-checklist.md`, mandatory for features planned after this change;
see Complexity Tracking and research D3. The evidence document moves; it is not new.

**II. Developers Stay Accountable.** The plan stage asks for the checklist to be reviewed
and waits for no approval (FR-029, clarification of 2026-10-16), so routine work makes no
approval request (SC-010). A material ambiguity is still put to the developer and leaves
the requirement without an item until answered (EC-07). A change to a fixed item that
alters intended behaviour needs the developer's approval, recorded as for a changed test.
The checklist is written for a reviewer who took no part: one file, the specification's
wording beside the items (FR-017).

**III. Deterministic Checks, Agent Judgement.** Every objective condition in the
specification is a rule: B1 to B7, G10, G11, C8, and the two `run` refusals (data model, "Rules
on the chain"). A failed rule blocks: the plan is not reported complete, the baseline is
refused, a task cannot be marked complete. Five limits are recorded and not presented as
covered:

1. Whether an item keeps its scenario's wording as closely as it could, and states no
   weaker outcome, is judgement (FR-016). The word-for-word quote (B6) puts the
   specification's text beside the items for the reviewer; nothing compares their
   meaning.
2. B5 detects only paths and code-shaped identifiers by fixed token shapes (research D6).
   Other implementation wording is left to the rules and the reviewer.
3. That no two items describe the same behaviour (FR-015) is not checked.
4. The `plan.md` heading guard, like the rest of the event, sees only the agent's edit
   tools. A shell edit that removes the `### Behaviour checklist` heading before the
   checklist exists takes the feature out of the checklist rules until a reviewer sees the
   diff. A shell edit to the checklist itself is still caught by G10, G11 and C8 once items
   are fixed.
5. The item baseline rows are not chained into the record check values. Editing them is
   refused through the agent's tools, as for every part of the evidence; a shell edit is
   not detected, as for the existing exception and expectation tables.

**IV. Test-First with Real Evidence.** As in 001 (research D12): every new rule and changed
behaviour of `tdd_check.py` gets a fixture and a failing test first, committed with the
failure in the commit message, and the history is replayed at the end. The compliant
example is regenerated by real runs, not edited (D11). The two exceptions approved for 001
apply unchanged and are listed again for approval in Complexity Tracking: the Markdown
wrappers, rules and template are prompts, verified structurally and by driving the
stories; and the performance test for the new size measures code that exists when it is
written, so it is first run against a generated feature large enough to exceed its limit
and seen to fail on time.

**V. Verify Against Current Spec Kit.** 001 was designed against 1.0.2.dev0; this design
was checked against the installed 1.1.3 (findings F1 to F7). F1 confirms that the core
implement step stops on unticked items in `checklists/`, which is why the checklist is in
`tests/`. F4, that the plan template is not recopied when `plan.md` exists, shaped the
wrapper step for older features. Five assumptions, A10 to A14, are confirmed by
installation tests ordered first; if A10 fails the plan returns to the developer.

**VI. Compatible and Removable.** For a feature the checklist rules do not apply to, every
check and fixture gives the 0.1.0 result (D5, SC-006); every existing fixture already has
its evidence document at the top level. Three changes to existing behaviour
are justified in research and documented in the README and CHANGELOG
([lifecycle contract](./contracts/lifecycle-and-packaging.md)):

1. A feature with no evidence yet keeps its evidence in `tests/` (D10, FR-041).
2. The event refuses an edit that removes `## Verification Plan` or
   `### Behaviour checklist` from `plan.md` (D5). This narrows a 0.1.0 limit.
3. For a feature under the checklist rules, `plan`, `tasks`, `gate` and `compliance` apply
   the new rules, and `run` refuses a baseline or Red run as D8 describes.

The preset keeps `append` and `wrap`. Nothing reads or writes the project's own test, lint
or CI configuration. The checklist is Markdown and names no framework. Removal leaves both
files in `tests/` as readable Markdown.

**Additional constraints.** *No duplication*: items name obligations by id and do not
repeat their scenarios or outcomes, and the evidence keeps fingerprints, not a copy of the
checklist. The one departure is the scenario quote, recorded in Complexity Tracking and
research D4; B6 keeps the copy identical to its source. *Proportion*: for a small, low-risk
change the rules ask for an item per acceptance scenario and per requirement, and no more
(FR-015, US1 scenario 6). *Agent neutrality*: the rules and checks name no agent; the only
agent-specific code is still the payload adapter.

**Quality gates.** The four test levels map to [quickstart](./quickstart.md) scenarios:
structural in 1; installation and registration in 2; behavioural in 1, 3, 4, 5, 6, 8 and 9;
regression in 7.

**Result**: the gates pass, subject to approval of the departures below. Phase 2 may
proceed, with the installation tests for A10 to A14 ordered first.

## Project Structure

### Documentation (this feature)

```text
specs/002-bdd-behaviour-checklist/
├── spec.md
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── architecture.md      # Phase 1 output (/speckit-plan command, C4 preset)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── behaviour-checklist.md       # The checklist file: template, grammar, rules B1 to B7
│   ├── check-cli-changes.md         # Changes to the check script, evidence location, hook
│   └── lifecycle-and-packaging.md   # Stage additions, preset and extension files, deliverables
├── checklists/
│   └── requirements.md  # Spec quality checklist (/speckit-specify)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

Only files this feature adds (`+`) or changes (`~`) are listed.

```text
extension.yml                                 ~ third template; version
preset.yml                                    ~ version

templates/
├── behaviour-checklist-template.md           + starting content of tests/behaviour-checklist.md
└── tdd-process-rules.md                      ~ "Behaviour checklist" section; evidence locations

scripts/python/
└── tdd_check.py                              ~ evidence location; checklist parser and rules B1 to B7;
                                                item fingerprints and baseline; G10; G11; C8; item status;
                                                run refusals; expectation --item; status --scenarios;
                                                hook: plan.md headings, tests/tdd-evidence.md

preset/
├── commands/
│   ├── speckit.plan.md                       ~ Behaviour checklist step and report
│   ├── speckit.tasks.md                      ~ older-feature gap; B7
│   ├── speckit.analyze.md                    ~ older-feature gap; B1 to B7
│   └── speckit.implement.md                  ~ refusals, item changes, item report, evidence location
└── templates/
    ├── plan-addendum.md                      ~ ### Behaviour checklist sub-heading
    └── tasks-addendum.md                     ~ one sentence on behaviour items

tests/
├── support.py                                ~ evidence path; checklist helpers
├── test_checklist.py                         + parser and rules B1 to B7
├── test_item_changes.py                      + item baseline, expectation --item, G10, G11, C8
├── test_evidence_location.py                 + the four location cases
├── test_trace.py, test_run.py, test_gate.py,
│   test_status.py, test_compliance.py,
│   test_hook.py, test_manifests.py,
│   test_performance.py                       ~ new cases; existing assertions unchanged
└── fixtures/
    ├── make_features.py                      ~ checklist fixtures
    ├── features/                             + about 40 generated directories
    └── payloads/                             + plan.md and tests/tdd-evidence.md edits

examples/
├── runs/
│   ├── README.md                             ~ layout and the frontend example
│   ├── compliant/                            ~ regenerated: tests/behaviour-checklist.md, tests/tdd-evidence.md
│   └── frontend-planned/                     + spec.md, plan.md, tests/behaviour-checklist.md
└── stories/
    ├── 01 to 07                              ~ expected behaviour includes the checklist
    └── 08-behaviours-from-the-code.md        + tempting story

docs/evaluation.md                            ~ judging a checklist; the item table; story 08
README.md                                     ~ the behaviour checklist; changes; criteria; limits
CHANGELOG.md                                  ~ release entry
```

**Structure Decision**: The layout of 001 is kept: both manifests at the repository root,
extension files in `templates/`, `scripts/python/` and `commands/`, preset files under
`preset/`. The checklist logic goes into `tdd_check.py` as a new section, because the
script is installed by copying and must run with no installation step, and because the
gate, the event and the compliance check need the same parser. The new tests are split by
concern, as the existing ones are. `tests/`, `examples/` and `docs/` remain outside the
extension install (`.extensionignore` is unchanged).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| A new mandatory document, `tests/behaviour-checklist.md`, for features planned after this change (Principle I) | The user asked for a separate, checklist-like artefact that a reviewer reads before code is written. Behaviours are stated at the level a reviewer judges against the specification, while obligations are stated per test and level, and one behaviour may need several (EC-04). A separate file can be fixed item by item at the baseline without fixing the rest of the plan (research D3, D7) | Given / When / Then columns in the obligations table would change a fixed table header that existing plans use, and tie behaviours one-to-one to obligations. A `## Behaviours` section of `plan.md` would put the review document inside the design document, which a reviewer reads for other reasons |
| The text of each acceptance scenario is copied from `spec.md` into the checklist (No duplication) | FR-017 requires the specification's wording beside the items wherever the checklist is reviewed, and it is reviewed as a file in editors, diffs and pull requests (research D4) | A view generated only by `status` would leave the file, as read in a pull request, without the wording. The script writing the quotes into the checklist would give the checklist two writers and make a checking subcommand write. Rule B6 fails on any difference, so the copy cannot drift from its source |

**Approval** (constitution, Governance: a departure is acceptable only when recorded with a
justification and approved by a person). Approved by Lee Sinclair on 2026-10-16:

1. The new mandatory document `tests/behaviour-checklist.md` (Principle I).
2. The copied scenario text, kept identical by B6 (No duplication).
3. The Markdown wrappers, rules and the new template are not built test-first
   (Principle IV, as approved for 001).
4. The new performance test is not fail-first in the ordinary way (Principle IV, as
   approved for 001).
5. The five limits recorded under Principle III above.

<!-- markdownlint-disable-file MD041 -->

## Architecture

**Feature architecture**: [architecture.md](./architecture.md) (C4 component views,
sequence diagrams, ER diagram)

**System views**: not yet created. `docs/architecture/context.md`, `containers.md` and
`erd.md` do not exist; `/speckit-c4-system` creates them from the Architecture Impact
tables of 001 and of this feature.

| View | Impact of this feature |
|------|------------------------|
| Context | None: the same people and external systems as 001 |
| Containers | No container added. Feature Artefacts gains a `tests/` folder; the extension's and the agent's relationships to it gain the behaviour checklist |
| Components | Preset: six changed components, five drawn. Extension: one new template and one new Checklist Checks component; eight changed |
| Flows | Five: the plan stage writes and checks the checklist; implementation refused while it fails; a changed item holds its tasks; a reviewer reads items with evidence; the evidence and plan headings guarded |
| ERD | New: Behaviour Checklist, Scenario Section, Behaviour Item, Item Baseline, Item Change Record. Changed: Acceptance Scenario, separated from Requirement with its text |
