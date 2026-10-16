# Research: BDD Behaviour Checklist

**Feature**: `002-bdd-behaviour-checklist` | **Date**: 2026-10-16 | **Spec**: [spec.md](./spec.md)

The Technical Context of the plan had no open unknowns, because the host, the language and
the tooling are those of `001-integrated-tdd` ([research D10](../001-integrated-tdd/research.md)).
This document records what was checked in the current Spec Kit, and the design decisions
the specification left to planning.

## Sources examined

| Source | What was read |
|--------|---------------|
| Spec Kit CLI 1.1.3, installed at `~/.local/share/uv/tools/specify-cli` | `core_pack/commands/implement.md`, `analyze.md`, `checklist.md`; `core_pack/scripts/bash/*.sh`; `presets/_manifest.py`; `extensions/__init__.py` (manifest validation of `provides.templates`); `integrations/claude/__init__.py` (event name mapping) |
| This project's Spec Kit workspace | `.specify/scripts/bash/setup-plan.sh`, `.claude/skills/speckit-implement/SKILL.md`, `.claude/skills/speckit-checklist/SKILL.md` |
| `001-integrated-tdd` | [research.md](../001-integrated-tdd/research.md), [data-model.md](../001-integrated-tdd/data-model.md), the three contracts, and `scripts/python/tdd_check.py` as shipped in 0.1.0 |
| The test suite | `tests/support.py`, `tests/test_trace.py`, `tests/fixtures/make_features.py` |

001 was designed against Spec Kit 1.0.2.dev0. The installed CLI is now 1.1.3, so every
mechanism this design relies on was read again in 1.1.3 (constitution Principle V).

## Findings about Spec Kit 1.1.3

| # | Finding | Where | Consequence |
|---|---------|-------|-------------|
| F1 | The core implement command scans every file in `FEATURE_DIR/checklists/`, counts `- [ ]` items and **stops to ask** when any file has one unticked | `core_pack/commands/implement.md` step 2 | The behaviour checklist must not live in `checklists/` (FR-003). Confirms the clarification of 2026-10-16 |
| F2 | The core checklist command writes only to `FEATURE_DIR/checklists/` | `core_pack/commands/checklist.md` | It neither reads nor overwrites a file in `tests/` (EC-06) |
| F3 | No core command or script reads or writes `FEATURE_DIR/tests/`. `tests/` paths in the core tasks template are paths in the project's source tree, not the feature directory | grep of `core_pack/commands`, `core_pack/scripts/bash`, `.specify/scripts/bash` | A feature-level `tests/` folder collides with nothing in Spec Kit |
| F4 | `setup-plan.sh` copies the plan template only when `plan.md` does not exist. Rerunning the plan stage keeps the existing `plan.md` | `.specify/scripts/bash/setup-plan.sh` lines 38 to 44 | A feature planned before this change does not gain the new template text on a rerun. The plan wrapper must tell the agent to add the new sub-heading itself (D5) |
| F5 | Preset strategies are still `replace`, `prepend`, `append`, `wrap` | `presets/_manifest.py` line 30 | The existing `wrap` and `append` entries need no change of strategy |
| F6 | `provides.templates` entries of an extension are validated by name pattern and file existence, and installed under `.specify/extensions/<id>/templates/` | `extensions/__init__.py` lines 389 to 418, 582 | A third extension template, the checklist template, is added the way the two existing ones were (assumption A11 below) |
| F7 | `pre_tool_use` still maps to Claude Code's `PreToolUse` | `integrations/claude/__init__.py` line 59 | The existing event, with matcher `Edit`, `Write` or `MultiEdit`, already sees edits to `plan.md` and to `tests/tdd-evidence.md`. The handler decides by path, so no manifest change is needed |

## Decisions

### D1. The plan stage writes the checklist, from an extension template

**Decision**: The plan wrapper gains a step after the Verification Plan: write
`tests/behaviour-checklist.md` from the extension's new template
`behaviour-checklist-template.md`, then run the `plan` check, which now covers the
checklist. The Verification Plan section of the plan template gains a fourth sub-heading,
`### Behaviour checklist`, holding one fixed line that links to the file.

**Rationale**: The plan stage is the first point at which both the specification and the
obligations exist (spec Assumptions). Writing the checklist there keeps the six standard
commands (FR-001, SC-005). A template supplied by the extension is the pattern already used
for `tdd-evidence-template.md`; Spec Kit has no template type for an arbitrary feature
document, so a preset template would not be resolved (F6). The sub-heading gives a reader
of `plan.md` the way to the checklist and marks the feature as one the checklist rules
apply to (D5).

**Alternatives considered**:

- *The tasks stage writes it.* Rejected: tasks is about work breakdown, and the checklist
  would then be written after a reviewer has stopped reading the plan. FR-001 places it in
  planning.
- *A new command, for example `/speckit-integrated-tdd-behaviours`.* Rejected by Principle
  I and SC-005.
- *Spec Kit's checklist command.* Rejected: it writes to `checklists/` (F2), where the core
  implement step would stop on the items (F1).

### D2. Format: Markdown, grouped by acceptance scenario, Given / When / Then per item

**Decision**: The checklist is Markdown with one `## USn-ASm` section per acceptance
scenario, in specification order, and one `## Other behaviours` section for items that
refine no scenario (requirements without a scenario, edge cases). Each scenario section
opens with the scenario's text from `spec.md` as a block quote, then lists its items. An
item is a list entry with a fixed first line and one indented line per clause:

```markdown
- **BI-001** Expresses: FR-001, US1-AS1. Verified by: VO-001.
  - **Given** a cart with no items
  - **When** the shopper asks for the cart total
  - **Then** the total shown is 0.00
  - **And** no error is reported
```

The full grammar is in [the checklist contract](./contracts/behaviour-checklist.md).

**Rationale**: A reviewer reads one scenario's wording and the items refined from it
together, which is what FR-017 requires and what makes a dropped or softened outcome
visible (SC-009). Given / When / Then on separate lines is readable in a diff and in a
rendered pull request, and is the form named in FR-008. It is Markdown like every other
feature artefact, and it parses with the same line-based approach the script already uses
for `tasks.md`. The same structure serves a feature observed through a screen, a
programmatic interface or stored data, because only the wording of the clauses changes
(FR-018).

**Alternatives considered**:

- *One table, one row per item.* Rejected: a Given / When / Then cell is too long to read
  in a table, and a table has nowhere to put the scenario's wording beside its items.
- *Gherkin `.feature` files.* Rejected: they suggest executable specifications and a
  Cucumber-style runner, which would imply a test framework (Principle VI). The trace
  links would have to live in tags or comments, which reviewers skim.
- *Columns added to the obligations table.* Rejected in D3.
- *YAML or JSON.* Rejected: harder for a reviewer to read than Markdown, and unlike every
  other artefact the reviewer already reads.

### D3. A separate document, not a section of `plan.md`

**Decision**: The checklist is its own file. This is a departure from Principle I (a new
mandatory document), recorded in the plan's Complexity Tracking.

**Rationale**: The obligations table states what each *test* must observe, at a chosen
testing level, and one behaviour can need several obligations (EC-04). The checklist
states what the *feature* must do, at the level a reviewer judges against the
specification. Folding it into `plan.md` would put the review document inside the design
document, which a reviewer reads for other reasons and at length. The user asked for a
separate, checklist-like artefact. A separate file can also be fixed item by item once
implementation begins (D7), without fixing the rest of the plan.

**Alternatives considered**:

- *Given / When / Then columns in the obligations table.* Rejected: it changes the fixed
  header of a table that existing plans use, which the parser would then reject
  (Principle VI), and it ties behaviours one-to-one to obligations, which EC-04 rules out.
- *A `## Behaviours` section of `plan.md`.* Rejected for the reasons above.

### D4. The scenario's wording is copied, and the copy is checked word for word

**Decision**: Each `## USn-ASm` section quotes its acceptance scenario from `spec.md`. Rule
B6 fails when the quote, after normalisation, differs from the specification's text. The
normalisation removes the block quote markers, `**` and `__` emphasis, and collapses runs
of white space; nothing else. This is a departure from the constitution's no-duplication
rule, recorded in Complexity Tracking.

**Rationale**: FR-017 requires the scenario's wording beside its items wherever the
checklist is reviewed, and the checklist is reviewed as a file: in an editor, in a diff, in
a pull request. The harm of a copy is that it drifts. A copy that fails a check the moment
it differs cannot drift, and the check turns a softened quote, an easy way to make a
weakened item look faithful, into a finding.

**Alternatives considered**:

- *A view generated by the script, for example `status` printing scenarios beside items.*
  Rejected as the only presentation: a reviewer reading the file in a pull request would
  not see it, so FR-017 would hold only in one place. `status` still shows it (D9).
- *The script writing the quotes into the checklist.* Rejected: the checking subcommands
  are read-only by contract, and the checklist would then have two writers.

### D5. Which features the checklist rules apply to

**Decision**: The checklist rules apply to a feature when its Verification Plan holds the
`### Behaviour checklist` sub-heading, or when `tests/behaviour-checklist.md` exists.
Otherwise the feature was planned before this change: the script applies no checklist
rule, its output for that feature is unchanged, and the tasks, analyze and implement
wrappers report the gap and name the plan stage, as they already do for a missing
Verification Plan. The runtime event refuses an edit through the agent's tools that would
remove the `## Verification Plan` or the `### Behaviour checklist` heading from a `plan.md`
that has it.

**Rationale**: Whether a feature was planned before the change has to be decided from what
is on disk, and the only thing the plan stage of a new feature always writes is the plan
template, which now holds the sub-heading. Leaving the output unchanged for older features
is what lets every existing check and fixture give the same result (SC-006, EC-01).

A marker the agent can delete would be an easy way out of the checklist, so the event now
guards it. Guarding the `## Verification Plan` heading too closes a limit that 0.1.0
recorded ("`plan.md` is not guarded"), because removing it removes the sub-heading with it.
The guard covers only the removal of the two headings; every other edit to `plan.md` is
allowed.

**Alternatives considered**:

- *Apply the rules whenever the evidence is in `tests/`.* Rejected: a feature planned
  before the change with no evidence yet would receive its evidence in `tests/` (D10) and
  then be blocked by a checklist it was never asked for, contrary to EC-01.
- *Always apply the rules.* Rejected: every feature planned before the change, and every
  existing fixture, would fail the `plan` check (SC-006).
- *The script prints a gap line for older features.* Rejected: it changes the output of
  every existing check on every existing fixture. The wrappers already detect the missing
  Verification Plan from its heading, and the same reading detects the missing
  sub-heading.

### D6. The checks are rules B1 to B7 in the existing `plan` and `tasks` subcommands

**Decision**: No subcommand is added. When the rules apply, `plan` also applies B1 to B6 to
the checklist and `tasks` also applies B7. Every lifecycle point that already runs those
two checks (the plan, tasks and analyze stages, and the start of implement) therefore
checks the checklist with no further instruction.

| Rule | Fails when | Requirement |
|------|-----------|-------------|
| `CHECKLIST` | The rules apply and the file is missing or unreadable | FR-003, FR-004 |
| B1 | A functional requirement or acceptance scenario in `spec.md` is named by no item | FR-019 |
| B2 | An item names no obligation and no exemption, or names one the plan does not hold | FR-010, FR-020 |
| B3 | An obligation in the plan is named by no item | FR-021 |
| B4 | An item's id is malformed or repeated, a clause is missing or out of order, an item sits outside a section, or the file holds a task-list checkbox or a status label | FR-007, FR-008, FR-014, FR-022 |
| B5 | An item names a file path, or a code-level identifier from the plan or task list, that the specification does not use | FR-012, FR-023 |
| B6 | An item names an unknown `FR-`, `SC-` or scenario id; a scenario section's quote is missing or differs from `spec.md`; an item in a scenario section does not name that scenario, or names another | FR-016, FR-017, FR-020 |
| B7 | A test task's obligations are named by no item | FR-031 |

**B5 is limited to what can be decided repeatably.** A token is *path-shaped* when it
contains `/` between two non-space characters or ends in a listed source or configuration
extension. A token is *code-shaped* when it contains `_`, `::` or `->`, ends in `()`, is
lower camel case, or is written in backticks. A path-shaped token is a finding unless it
appears in `spec.md`; a code-shaped token is a finding when it appears in `plan.md` or
`tasks.md` and not in `spec.md`. The exception for `spec.md` matters: for a feature whose
users work with files, such as this one, a file the specification names is part of the
observable boundary (FR-011), not of the design. Subtler implementation wording is left to
the process rules and the reviewer (spec Assumptions).

**Rationale**: Reusing `plan` and `tasks` adds nothing a developer or agent must remember.
Each rule maps to a requirement and names the item, requirement or obligation it concerns
(FR-024). The checks read files only and are deterministic (SC-002).

**Alternatives considered**:

- *A new `behaviours` subcommand.* Rejected: every wrapper would need another instruction,
  and a forgotten instruction is a check that does not run.
- *A word list of forbidden implementation terms for B5.* Rejected: any list is either
  too short to catch much or long enough to reject domain words, and it differs by
  language.

### D7. Items are fixed at the first recorded run, and changes are recorded like test changes

**Decision**: The script keeps, in the evidence document, a fingerprint of each item's
clauses as they stood at the first recorded run at which the item existed. For a feature
whose checklist was written before implementation, that run is the baseline (FR-033). An
item added later is fixed from the first run after it appears. A change to the clauses of a
fixed item, or its removal, is recorded with
`expectation --item <BI-nnn> --requirement <id> --justification <text> [--alters-behaviour]`,
and needs `approve` when it alters intended behaviour. A new gate rule, G10, keeps a task
from completion while an item naming one of its obligations has an unrecorded or
unapproved change. A new compliance rule, C8, reports a feature whose checklist is
missing, fails B1 to B7, or has an unrecorded change.

The fingerprint covers the item's Given, When, Then and And clauses after normalisation,
and not its trace links, so that linking a discovered obligation to an existing item
(US4 scenario 3) is not a change.

**Rationale**: This is the mechanism the developer already knows for tests: a fingerprint
at the failing-first run, a recorded justification for a change, an approval when
behaviour changes, and a gate that holds the task meanwhile (FR-033). Keeping
fingerprints and not text keeps the evidence document free of a second copy of the
checklist; git history shows what changed.

**Alternatives considered**:

- *The event refuses edits to the checklist after the baseline.* Rejected: a
  specification can change mid-implementation (EC-05), and the checklist must follow it.
  Detection with a recorded justification lets it follow without letting it drift
  silently.
- *A copy of the checklist kept at the baseline.* Rejected: a second file to guard and a
  second copy of the same text.
- *Fix items when tasks are generated.* Rejected by the clarification of 2026-10-16: the
  first recorded run.

### D8. Implementation cannot start, and a test cannot be written, ahead of the checklist

**Decision**: When the checklist rules apply, `run --phase baseline` exits 2 and records
nothing while `plan` would fail on any of B1 to B6, and `run --phase red` exits 2 and
records nothing when an obligation it names is named by no item. Once the baseline exists,
a new gate rule, G11, keeps every task from completion while the checklist fails
`CHECKLIST` or any of B1 to B7, so a checklist that stops matching the specification or the
plan mid-implementation (EC-05) holds the work until it is brought back into line.

**Rationale**: The implement wrapper already stops when `plan` fails, but that is an
instruction to the agent. Refusing the baseline makes FR-004 a hard stop, because no other
run is accepted before a baseline. Refusing a Red run for an unlinked obligation makes
FR-032 one: the test of a discovered obligation cannot be recorded as failing first until
the obligation has an item. Without G11, a requirement added to the specification after the
baseline, or an item broken by an edit, would be noticed only by `compliance` at the end
of the run, and Principle III asks that a failed check block the work it guards. The event
already runs the gate when a task is marked complete, so G11 needs no new trigger.

**Alternatives considered**:

- *A gate rule only.* Rejected: by the time a task is marked complete, the test has been
  written; FR-032 asks for the link before. G11 adds to the refusals and does not replace
  them.
- *A recorded limit, with the implement wrapper told to rerun `plan` after a specification
  change.* Rejected by the developer on 2026-10-16: it relies on the agent following an
  instruction, which is what this feature exists to avoid.
- *G11 for coverage only (`CHECKLIST`, B1, B3).* Rejected: an item edited after the
  baseline into code terms (B5) or a malformed one (B4) would go unnoticed until the end.

### D9. Item status is derived, and shown in `status` and the Summary

**Decision**: When the rules apply, the Review Evidence view gains a table of behaviour
items: each item, the scenario it refines, its obligations, the tests recorded against
them and a derived status. An item is `verified` only when every obligation it names is
verified; `exempt` when it names only exemptions; otherwise `failed`, `blocked`,
`in progress` or `planned`, from its obligations, in that order of precedence. Items not
verified are added to the view's Not verified list, and unrecorded item changes get their
own line. The table is absent for a feature the rules do not apply to, so its Summary
stays byte for byte as it is (SC-006). `status` also prints each scenario's wording above
its items (FR-017).

**Rationale**: FR-014 and FR-034: status comes only from the records. An item is not
verified while any obligation is open, so a reviewer cannot be shown a behaviour as
verified on the strength of some of its tests.

### D10. Evidence location follows from what is on disk

**Decision**: One function decides the evidence document's path for a feature:

| On disk | Path | Applies to |
|---------|------|------------|
| `tdd-evidence.md` at the top of the feature directory, and none in `tests/` | the top-level file | Features with evidence before this change, including when the plan stage is rerun (FR-043) |
| `tests/tdd-evidence.md` only | `tests/tdd-evidence.md` | Features begun after this change |
| Neither | `tests/tdd-evidence.md`, with `tests/` created on the first write | Every feature that has no evidence yet (FR-041) |
| Both | none: every subcommand exits 2 and records nothing, and the event refuses to mark a task complete | EC-10, FR-044 |

The runtime event recognises an evidence document in `tests/` and takes the feature
directory to be the parent of `tests/`; `tasks.md` and `plan.md` stay at the top of the
feature directory. The refusal of a direct edit, the gate, `status` and `compliance` all
use the same function (FR-042).

**Rationale**: The clarification of 2026-10-16 fixed the location rule. Deciding from disk
keeps features already under way where they are (SC-006). Exiting 2 when both exist is the
existing contract for input the script cannot trust: it records nothing and chooses
nothing.

**Consequence for the test suite**: tests that run `run` on a fixture with no evidence, and
read the evidence document afterwards, now find it in `tests/`. The path is defined once,
in `tests/support.py`; changing it there is a consequence of FR-041 and weakens no
assertion. Every fixture that holds an evidence document keeps it at the top level and
gives the same results.

### D11. Examples: a backend run regenerated, and a frontend example at the planning stage

**Decision**:

- `examples/runs/compliant/` (a cart total: behaviour observed through a programmatic
  interface) is produced again by driving the sample project through the six standard
  commands with this change installed. It then holds `tests/behaviour-checklist.md` and
  `tests/tdd-evidence.md`, and `compliance` reports it compliant.
- A new `examples/runs/frontend-planned/` holds the specification, plan and behaviour
  checklist of a small screen feature, observed through what a user sees and can do. It
  stops at the end of planning and passes `plan`. It shows the same checklist structure
  with user-interface wording (FR-018, FR-038).
- `examples/runs/tests-only/` is unchanged: it was planned before this change and stays
  non-compliant for its own reasons.
- A new story, `examples/stories/08-behaviours-from-the-code.md`, starts from a project
  whose code already does more than its specification asks. It tempts the agent to
  describe the code, naming its functions, and to leave out a requirement the code does
  not yet meet. The expected behaviour is that B5 and B1 report both (FR-039).

**Rationale**: The evidence of a compliant run must come from real executions
(Principle IV), so the backend example is regenerated, not edited. A complete frontend
run would add a JavaScript toolchain to the repository and would show nothing about the
checklist that the planning artefacts do not; FR-038 asks for the checklist and its check,
both of which the planning example has.

**Alternatives considered**: *A second full run for a frontend project.* Rejected as
above. *Hand-editing the existing compliant evidence.* Rejected: the evidence would no
longer come from the runs it records.

### D12. How this project is built and tested

**Decision**: As for 001 (Principle IV). Each new rule and each changed behaviour of the
script gets a fixture and a failing `unittest` test, committed with the failure in the
commit message, before the commit that makes it pass; the history is replayed at the end.
Fixtures are generated by `tests/fixtures/make_features.py`. The wrappers, rules,
templates and documentation are prompts and prose: they are verified structurally (the
wrappers name the template and the checks; the template parses and passes `plan` on the
examples) and behaviourally by driving the stories, as recorded in 001.

### D13. Performance

**Decision**: The limits of 001 stand, extended to a checklist of 200 items: the event
handler decides in under one second, and every checking subcommand finishes in under two
seconds, for a feature with 200 tasks, 1,000 records and 200 behaviour items. B5 tokenises
each item once and looks tokens up in sets built once from `spec.md`, `plan.md` and
`tasks.md`.

## Assumptions to confirm by installation test

| # | Assumption | How it is confirmed |
|---|------------|---------------------|
| A10 | Spec Kit 1.1.3 installs the extension and the preset from a release tree as 1.0.2.dev0 did, with the composed commands carrying the wrapper text | Install into a throwaway project; read the composed `speckit-plan`, `speckit-tasks`, `speckit-analyze` and `speckit-implement` skills |
| A11 | The new template installs at `.specify/extensions/integrated-tdd/templates/behaviour-checklist-template.md` | The same installation; list the directory |
| A12 | The appended plan template carries the `### Behaviour checklist` sub-heading inside the Verification Plan | `specify preset resolve plan-template` in the throwaway project |
| A13 | The `PreToolUse` event runs the handler for an edit to `plan.md` and to `tests/tdd-evidence.md`, and a refusal with exit 2 stops the edit | Recorded payloads in `tests/fixtures/payloads/`, then one live edit of each in Claude Code |
| A14 | The core implement step's checklist scan does not see `tests/behaviour-checklist.md` | Run the implement stage on a feature with a complete `checklists/requirements.md` and a checklist in `tests/`; it does not stop to ask |

If A10 fails, the plan returns to the developer before further work, as A1 did in 001; the numbering continues from 001's A1 to A9.

## Unknowns resolved

| Unknown | Resolution |
|---------|------------|
| File name and format of the checklist | D1, D2: `tests/behaviour-checklist.md`, Markdown, grammar in the checklist contract |
| How the item content at the first run is kept | D7: per-item fingerprints in the evidence document |
| Whether the checklist check is part of the `plan` check | D6: yes, rules B1 to B6; B7 in `tasks` |
| Justification against the constitution's rules on new documents and duplication | D3, D4, and the plan's Complexity Tracking |
| How older features are told apart from new ones | D5 |
| How the evidence move reaches the event, the gate, the fixtures and the examples | D10, D11 |

## Installation test results

### A10: both packages compose with Spec Kit 1.1.3 and the hook is installed

- **Date**: 2026-10-16.
- **Run**: `git archive HEAD` into a throwaway `release` directory; in a fresh git project, `specify init --here --integration claude --force`, `specify preset add --dev <release>` and `specify extension add --dev <release>` with Spec Kit CLI 1.1.3. In 1.1.3 `--dev` is a flag and the path is the positional argument, so the task's `add integrated-tdd --dev <path>` form is rejected with "unexpected extra argument".
- **Observed**: `speckit-plan`, `speckit-tasks`, `speckit-analyze` and `speckit-implement` under `.claude/skills/` carry the wrapper text (`source: preset:integrated-tdd`, the check-script preamble) around the core text. `.specify/extensions/integrated-tdd/scripts/python/tdd_check.py` is installed. `.claude/settings.json` holds the `PreToolUse` entry for `Edit|Write|MultiEdit`. In Claude Code (`claude -p --model haiku --permission-mode acceptEdits`), an Edit of `specs/001-x/tdd-evidence.md` was refused with the hook's message that the file is written only by the check script, and the file was unchanged.
- **Result**: confirmed.

### A11 and A12: the template installs, and the appended plan template carries the sub-heading

- **Date**: 2026-10-16.
- **Run**: `git archive HEAD` of commit `0bb2d3a` into a fresh release tree; in a fresh git project, `specify init --here --integration claude --force`, `specify extension add --dev <release>`, `specify preset add --dev <release>` with Spec Kit CLI 1.1.3; `ls .specify/extensions/integrated-tdd/templates/`; `specify preset resolve plan-template`.
- **A11 observed**: the directory lists `behaviour-checklist-template.md`, `tdd-evidence-template.md` and `tdd-process-rules.md`. Confirmed.
- **A12 observed**: `preset resolve` reports the composition chain `[base] core plan-template` then `[append] integrated-tdd`, whose file is `plan-addendum.md`. The addendum is the last layer, and its headings are `## Verification Plan` (line 1), the three sub-headings and `### Behaviour checklist` (line 54), with no second-level heading after it. The sub-heading is therefore inside the Verification Plan of the composed template. `resolve` prints the chain and not the composed text, so the position is read from the appended file. Confirmed.
