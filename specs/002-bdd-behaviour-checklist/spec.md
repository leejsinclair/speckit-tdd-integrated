# Feature Specification: BDD Behaviour Checklist

**Feature Branch**: `002-bdd-behaviour-checklist`

**Created**: 2026-10-16

**Status**: Draft

**Input**: User description: "Modify the `leejsinclair/speckit-tdd-integrated` workflow to add a higher-level, BDD-style checklist artifact that is derived from the specification and plan, so the test intent is explicit before implementation starts." The goal is stronger assurance that the coding agent cannot fudge either the tests or the code, by making functional requirements, behaviour scenarios, verification obligations, test tasks and implementation evidence line up in one reviewable chain.

## Clarifications

### Session 2026-10-16

- Q: Before implementation can start, must a named person record that they reviewed the behaviour checklist? → A: No. The deterministic checklist check is the only gate. The planning stage's report asks for review, and nothing blocks on it, so routine work still makes no approval request.
- Q: Where should the behaviour checklist live, given that the stock implement step stops on any unticked item in `checklists/`? → A: In a `tests/` folder in the feature directory, next to `checklists/`.
- Q: Should moving `tdd-evidence.md` into the new `tests/` folder be part of this feature? → A: Yes. New features keep their evidence in `tests/`, and the checks still read the old location for features planned before the change.
- Q: Must a behaviour item derived from an acceptance scenario repeat the scenario's wording exactly, so a check can catch a weakened outcome? → A: No. Items are more detailed than acceptance scenarios and there are more of them, so exact wording is not possible; each item keeps its scenario's wording as closely as it can.
- Q: At what point should a behaviour item count as fixed, so that any later change to it needs a recorded justification? → A: When the first test run is recorded for the feature (implementation's baseline run).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A behaviour checklist is produced before implementation (Priority: P1)

A developer takes a feature through the normal specification and planning stages. Without running any extra command, they find a behaviour checklist in the feature's `tests/` folder, next to `checklists/` and alongside the plan. It lists, in Given / When / Then form, every behaviour the feature must exhibit, each stated in terms someone could observe from outside the system: what a user sees, what a caller receives, what is stored and can be read back, what is refused. Each item names the functional requirements and acceptance scenarios it comes from and the verification obligations that will test it. The checklist says nothing about how the code will be structured.

**Why this priority**: The rest of the feature depends on the checklist existing and being derived from the requirements rather than from the code. If the behaviours are written after the code, or written by looking at the code, they restate what the agent built rather than what was asked for.

**Independent Test**: Take a representative story through specification and planning with the workflow installed and stop before tasks. Confirm that the checklist exists in the documented location, that every functional requirement and acceptance scenario appears in at least one item, that every item names the obligations that verify it, and that no item mentions a file, module, function, class, table or screen component.

**Acceptance Scenarios**:

1. **Given** a specification with functional requirements and acceptance scenarios, **When** the developer completes the planning stage, **Then** a behaviour checklist exists in the feature's `tests/` folder and every functional requirement and acceptance scenario is named by at least one behaviour item.
2. **Given** a completed Verification Plan, **When** the checklist is produced, **Then** every behaviour item names the verification obligations that verify it, or names the exemption that explains why it is verified another way, and every verification obligation is named by at least one behaviour item.
3. **Given** a behaviour item, **When** it is read, **Then** it is written as a context, an action and an observable outcome, and contains no reference to source files, code identifiers, data stores or interface components.
4. **Given** an edge case or failure condition in the specification, **When** the checklist is produced, **Then** the edge case or failure condition appears as its own behaviour item or within the item whose outcome it changes.
5. **Given** an acceptance scenario, **When** the checklist is produced, **Then** it is refined into one or more behaviour items that keep the scenario's terms and every outcome it states, add concrete detail such as specific values or cases, and drop or soften none of its outcomes.
6. **Given** a small, low-risk change, **When** the checklist is produced, **Then** every item traces to something the specification states, and no two items describe the same behaviour.

---

### User Story 2 - The checklist is checked, and a failed check blocks progress (Priority: P2)

A technical lead needs the checklist to be more than a document the agent writes and then forgets. When the checklist and the rest of the feature's artefacts disagree, a repeatable check reports exactly where, and the stage that produced the disagreement cannot be reported complete until it is corrected. The same check runs whenever the analysis stage runs.

**Why this priority**: A checklist that can drift from the requirements, or that the agent can quietly leave incomplete, gives no more assurance than none. A repeatable check is what stops either the tests or the checklist from wandering away from the specification.

**Independent Test**: Seed a set of feature directories, each with one inconsistency: a requirement named by no item, an item with no obligation or exemption, an obligation named by no item, an item naming an unknown requirement or obligation, an item written in terms of the code. Run the check on each and confirm that each inconsistency is reported with the item and rule concerned, the check gives the same result each time, and a consistent feature passes.

**Acceptance Scenarios**:

1. **Given** a checklist in which a functional requirement or acceptance scenario is named by no item, **When** the check runs, **Then** it fails and names the requirement or scenario.
2. **Given** a checklist item that names no obligation and no exemption, or names one the plan does not hold, **When** the check runs, **Then** it fails and names the item.
3. **Given** a verification obligation that no checklist item names, **When** the check runs, **Then** it fails and names the obligation.
4. **Given** a checklist item that names a file path or a code-level identifier, **When** the check runs, **Then** it fails and names the item.
5. **Given** a failing check, **When** the planning stage reaches its completion report, **Then** it does not report the plan complete and says which findings remain.
6. **Given** a feature at the analysis stage, **When** the analysis runs, **Then** the checklist check's findings appear in the analysis report and nothing is modified.

---

### User Story 3 - A person can review the checklist before code is written (Priority: P3)

A reviewer reads the checklist at the end of planning, before implementation starts. In a few minutes they can see whether the behaviours match what the specification asked for, without reading the plan's tables or any code. The planning stage asks for this review; it does not wait for it, and implementation is gated by the checklist check alone.

**Why this priority**: A check can prove that the checklist is consistent with the plan, but only a person can judge whether it captures what was meant. Review before implementation is cheaper than finding the gap in a finished pull request.

**Independent Test**: Give a reviewer who took no part the specification and the checklist for a representative feature. Ask them to identify any behaviour the specification requires that the checklist omits, and any item that goes beyond the specification. Confirm they can do so from these two documents alone.

**Acceptance Scenarios**:

1. **Given** a completed checklist, **When** a reviewer who took no part reads it alongside the specification, **Then** they can say for each item which requirement it comes from without consulting the plan or task list.
2. **Given** a reviewer who finds a missing or wrong behaviour, **When** they report it, **Then** the correction is made in the specification or the Verification Plan first and the checklist is brought back into line, so the checklist never holds a behaviour the specification does not state.
3. **Given** a completed plan whose checklist check passes, **When** the planning stage reports completion, **Then** the report names the checklist's location and asks for it to be reviewed, and no approval is requested or awaited.

---

### User Story 4 - Tests and evidence are anchored to the planned behaviours (Priority: P4)

During implementation, every test the agent writes traces back to a behaviour item through its obligation, and the final report and evidence summary show, for each behaviour item, which tests verify it and with what result. If a behaviour item is changed once implementation has begun, that change is visible and justified, in the same way that a changed test expectation already is.

**Why this priority**: This closes the loop from requirement to evidence. Without it, the checklist describes intended behaviour and the evidence describes tests, and a reviewer still has to work out whether the two meet.

**Independent Test**: Run implementation on a feature whose checklist passes its check. Confirm that the evidence summary lists each behaviour item with its derived status, that a test added for an untraced scenario is reported, and that an edit to an item's expected outcome after implementation began is reported until it is justified.

**Acceptance Scenarios**:

1. **Given** a feature whose checklist passes its check, **When** implementation is complete, **Then** the evidence summary shows for each behaviour item its obligations, the tests recorded against them and a status derived from those records.
2. **Given** a behaviour item with any obligation not verified, **When** results are reported, **Then** the item is not reported as verified.
3. **Given** a scenario discovered during implementation, **When** its obligation is added to the plan, **Then** it is also added to an existing or new behaviour item before its test is written, and the check passes again.
4. **Given** a behaviour item, **When** its context, action or expected outcome is changed after implementation has begun, **Then** the change is detected, a justification tied to the requirements is required, and a change that alters intended behaviour requires a person's approval.
5. **Given** a behaviour item, **When** its verification status is shown, **Then** the status comes from the recorded test runs and is never entered by hand in the checklist.

---

### User Story 5 - Adopters know when the checklist is written, where it lives and what it is for (Priority: P5)

A developer adopting the workflow, or a reviewer reading a feature produced by it, finds in the documentation when the behaviour checklist is written, by which stage, where it is stored, how it relates to `spec.md`, `plan.md` and `tasks.md`, and how to use it in review. Worked examples show a checklist for a backend feature and for a frontend feature.

**Why this priority**: The artefact only helps if people know to read it and trust what it says. It depends on the earlier stories being settled.

**Independent Test**: Give a developer new to the workflow the README and the process rules and ask when the checklist is written, where it lives, what each item must link to, and what is forbidden in it. Confirm they can answer from the documentation alone, and that the example runs include a checklist for a backend feature and one for a frontend feature that pass the check.

**Acceptance Scenarios**:

1. **Given** the repository documentation, **When** a new adopter reads it, **Then** they can state the stage that writes the checklist, its location, its relationship to the specification, plan and task list, and the rules for its content.
2. **Given** the shipped examples, **When** the check runs on them, **Then** each example that is meant to comply passes, and includes behaviour items for at least one backend feature and one frontend feature.
3. **Given** the shipped example stories, **When** a story is run that tempts the agent to write behaviour items from the code or to leave a requirement without an item, **Then** the story's expected behaviour is that the check reports it.

---

### Edge Cases

- **EC-01** A feature planned before this change has a Verification Plan but no behaviour checklist. Later stages report the missing checklist as a gap, name the planning stage as the way to produce it, and otherwise work as they do today.
- **EC-02** The workflow's extension is not installed. No checklist is produced or checked, and the stages work as core Spec Kit does.
- **EC-03** A requirement is exempted from automated verification. It still appears in a behaviour item, and that item names the exemption and how it is verified instead; it is never shown as verified by tests.
- **EC-04** One obligation verifies behaviour described by two items, or one item needs several obligations at different testing levels. Both are allowed, and the check accepts many-to-many links.
- **EC-05** A specification changes after implementation has begun. The checklist is brought back into line, the check reruns, and the change to any existing item is recorded as User Story 4 describes.
- **EC-06** The feature also has checklists in `checklists/`: the specification quality checklist and any from the custom checklist command. The stock implement step's scan of `checklists/` behaves as it does today, and neither it nor the custom checklist command reads, counts or overwrites the behaviour checklist.
- **EC-07** A requirement is ambiguous in a way that changes the observable outcome. No item is written for it until the developer answers, the check fails meanwhile, and the answer is recorded in the specification's Clarifications.
- **EC-08** A success criterion is a measured outcome rather than a behaviour, such as a time limit or a satisfaction score. It appears in an item only when the Verification Plan verifies it; otherwise it is out of the checklist's scope.
- **EC-09** A behaviour is only observable through a user interface, or only through a programmatic interface with no user interface. The item states the outcome in terms of whichever interface the specification names, without naming components or endpoints.
- **EC-10** A feature directory holds an evidence document both at its top level and in `tests/`, for example after a manual copy. The checks report the conflict and record nothing until one is removed.

## Requirements *(mandatory)*

### Functional Requirements

#### Lifecycle placement

- **FR-001**: The behaviour checklist MUST be produced within the existing planning stage, after the Verification Plan is filled, without the developer invoking an additional command.
- **FR-002**: The existing specify, plan, tasks, analyze and implement flow MUST keep its order, and no stage's current checks, gates or evidence rules MUST be removed or relaxed by this feature.
- **FR-003**: The behaviour checklist MUST be stored in a `tests/` folder in the feature directory, next to `checklists/`, under one fixed, documented file name. It MUST NOT be stored in `checklists/`, so that the stock implement step's checklist scan neither counts its items nor stops on them.
- **FR-004**: The checklist MUST exist, and its check MUST pass, before the implementation stage begins work on any task. Once implementation has begun, no task MUST be marked complete while the checklist check fails.
- **FR-005**: When the workflow's extension is not installed, no stage MUST produce, require or check the behaviour checklist.
- **FR-006**: A feature whose plan has a Verification Plan but no behaviour checklist MUST be reported as a gap by the tasks, analyze and implement stages, which MUST name the planning stage as the way to produce it.

#### Content

- **FR-007**: Each behaviour item MUST have a stable identifier, unique within the feature and never reused.
- **FR-008**: Each behaviour item MUST be written as a context, an action and an observable outcome (Given / When / Then).
- **FR-009**: Each behaviour item MUST name the functional requirements, acceptance scenarios, edge cases and success criteria from the specification that it expresses.
- **FR-010**: Each behaviour item MUST name the verification obligations that verify it, or the verification exemption that explains how it is verified instead.
- **FR-011**: Each outcome MUST be stated as something observable at the boundary the specification describes: what a user sees or can do, what a caller receives, what is persisted and can be read back, what is refused or reported. It MUST NOT describe internal steps.
- **FR-012**: A behaviour item MUST NOT name source files, directories, modules, functions, classes, data stores, schemas, endpoints, interface components or any other element of how the feature is built.
- **FR-013**: A behaviour item MUST NOT introduce behaviour the specification does not state. A behaviour found missing during review MUST be added to the specification first.
- **FR-014**: The checklist MUST hold no verification status entered by hand. Any per-item verification status shown to a reviewer MUST be derived from recorded test runs.
- **FR-015**: The number of behaviour items MUST be proportionate to the scope, risk and complexity of the change. Items are expected to outnumber acceptance scenarios, but no two items may describe the same behaviour.
- **FR-016**: A behaviour item derived from an acceptance scenario MUST keep that scenario's wording as closely as its added detail allows, using the specification's own terms for actors, actions and outcomes. Together, the items derived from one scenario MUST state every outcome the scenario states, and none of them MUST state an outcome that is weaker than the scenario's.
- **FR-017**: In the checklist itself, and in the on-demand view that presents it for review against the specification, each acceptance scenario's wording from the specification MUST be shown beside the behaviour items derived from it, so that a dropped or softened outcome can be seen without opening the specification.
- **FR-018**: The checklist's form MUST suit a feature whose behaviour is observed through a user interface, through a programmatic or command-line interface, or through stored data, without changes to its structure.

#### Consistency checks

- **FR-019**: A repeatable check MUST report every functional requirement and acceptance scenario in the specification that no behaviour item names.
- **FR-020**: The check MUST report every behaviour item that names no obligation and no exemption, and every item that names a requirement, scenario, edge case, success criterion, obligation or exemption that does not exist.
- **FR-021**: The check MUST report every verification obligation that no behaviour item names.
- **FR-022**: The check MUST report every behaviour item that is missing its context, action or outcome.
- **FR-023**: The check MUST report every behaviour item that names a file path, or a code-level identifier that also appears in the feature's task list or plan as part of the design.
- **FR-024**: The check MUST give the same result each time it is run on the same artefacts, and each finding MUST name the rule and the item, requirement or obligation concerned.
- **FR-025**: The planning stage MUST NOT report the plan complete while the checklist check fails, and MUST state the remaining findings.
- **FR-026**: The analysis stage MUST include the checklist check's findings in its report and MUST modify nothing.
- **FR-027**: The compliance check used to evaluate finished runs MUST report a run non-compliant when its checklist is missing, fails the checklist check, or holds an item whose obligations were not all verified while the run reports it as verified.

#### Review before implementation

- **FR-028**: The planning stage's completion report MUST present the behaviour checklist for review and say where it is stored.
- **FR-029**: The checklist check MUST be the only gate on the checklist before implementation. The workflow MUST NOT request, await or require a recorded human review of the checklist before implementation begins.
- **FR-030**: A correction found in review MUST be made in the specification or the Verification Plan and then carried into the checklist, so the three stay consistent.

#### Anchoring tests and evidence

- **FR-031**: Every test task MUST trace to at least one behaviour item through the obligations it names, and the tasks check MUST report a test task whose obligations trace to no item.
- **FR-032**: An obligation discovered during implementation MUST be linked to an existing or new behaviour item before its test is written.
- **FR-033**: A change to a behaviour item's context, action or outcome after implementation has begun MUST be detected and MUST require a justification tied to the requirements; a change that alters intended behaviour MUST also require a person's approval, as a changed test expectation does today. Implementation is taken to have begun when the first test run is recorded for the feature. The checklist's content at that moment is kept so that later changes can be detected; before it, the checklist may be revised freely during planning and tasks. Adding an item for an obligation discovered during implementation is not a change to an existing item; removing an item is.
- **FR-034**: The evidence summary and the on-demand status view MUST show, for each behaviour item, its obligations, the tests recorded against them and a derived status, and MUST NOT show an item as verified while any of its obligations is not verified.
- **FR-035**: The implementation stage's final report MUST list every behaviour item that is not verified, with the reason.

#### Documentation and examples

- **FR-036**: The README and process rules MUST state when the checklist is written, by which stage, where it is stored, what each item must contain and link to, what it must not contain, and how it relates to `spec.md`, `plan.md` and `tasks.md`.
- **FR-037**: The documentation MUST show the full trace from requirement to behaviour item to obligation to test task to evidence, and explain how a reviewer uses it.
- **FR-038**: The shipped example runs MUST include a behaviour checklist for every compliant example, covering at least one backend feature and one frontend feature, and every compliant example MUST pass the checklist check.
- **FR-039**: The shipped example stories MUST include at least one story whose expected behaviour is that the check reports a checklist written from the code or missing a requirement.
- **FR-040**: The changelog MUST record the new artefact, the changed stage behaviour and the effect on features planned before the change.

#### Evidence location

- **FR-041**: For a feature planned after this change, the evidence document (`tdd-evidence.md`) MUST be kept in the feature's `tests/` folder, next to the behaviour checklist.
- **FR-042**: Every protection that applies to the evidence document today MUST apply at its new location: only the check script writes it, the agent's edit tools cannot change it, and the gate, status view and compliance check read it.
- **FR-043**: For a feature whose evidence document already exists at the top of its feature directory, such as one implemented or partly implemented before this change, the checks MUST continue to read and write it there, and MUST NOT move it. A feature with no evidence document yet has it created in `tests/` (FR-041), whenever it was planned.
- **FR-044**: A feature MUST have its evidence document in one location only. When both locations hold one, the checks MUST report it and MUST NOT choose between them.
- **FR-045**: The documentation MUST state both evidence locations and which features use each.

### Key Entities

- **Behaviour checklist**: The feature's list of behaviour items, stored in the feature's `tests/` folder, derived from the specification and the Verification Plan, and checked before implementation. It holds intent, never status.
- **Behaviour item**: One observable behaviour, with a stable identifier, a context, an action and an outcome, links to the specification ids it expresses, and links to the obligations or exemption that verify it.
- **Trace link**: A reference from a behaviour item to a requirement, acceptance scenario, edge case, success criterion, obligation or exemption. The chain is requirement, behaviour item, obligation, task, test, recorded run.
- **Item change record**: A change to a behaviour item made after implementation began, with its justification tied to the requirements and, where intended behaviour changes, the approving person.
- **Feature tests folder**: The `tests/` folder in a feature directory. It holds the behaviour checklist and, for any feature that had no evidence document before this change, the evidence document.
- **Item status**: The verification state of a behaviour item, derived from the recorded runs of its obligations' tests. Never stored in the checklist.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On every compliant example, 100% of functional requirements and acceptance scenarios are named by a behaviour item, 100% of behaviour items name an obligation or an exemption, and 100% of obligations are named by a behaviour item.
- **SC-002**: Each seeded inconsistency in the check's fixture set (an unnamed requirement, an item without an obligation, an unnamed obligation, an unknown reference, a missing Given, When or Then, an implementation-specific item) is reported, and the check gives the same result on ten consecutive runs.
- **SC-003**: A reviewer who took no part can say, for any behaviour item, which requirements it expresses, which tests verify it and with what result, in under two minutes.
- **SC-004**: A reviewer who took no part can read the checklist for a representative feature of 10 to 20 requirements and judge whether it matches the specification in under ten minutes.
- **SC-005**: A story completes with the same standard lifecycle commands as today; no new command appears in the session.
- **SC-006**: All existing checks and their fixtures give the same results as before this change, a feature planned before the change is reported as a gap rather than failing, and its evidence is read and written where it already is.
- **SC-007**: A run that changes a behaviour item's outcome after implementation began, without a recorded justification, is reported non-compliant every time.
- **SC-008**: A developer new to the workflow answers the four questions in User Story 5 from the documentation alone in under five minutes.
- **SC-009**: In every compliant example, each acceptance scenario's outcomes all appear, unweakened, in the behaviour items derived from it, and no two items describe the same behaviour.
- **SC-010**: Routine planning and implementation of a feature makes no approval request on account of the behaviour checklist.
- **SC-011**: An attempt through the agent's edit tools to change the evidence document in its new location is refused every time, as it is at the old location today.

## Assumptions

- The behaviour checklist is an addition to the existing Verification Plan, not a replacement for it. The Verification Plan remains the source of obligations; the checklist groups them under observable behaviours a person can review without reading the tables.
- The checklist is produced by the planning stage because that is the first point at which both the specification and the obligations exist. The tasks stage links test tasks to items through the obligations they already name, so tasks need no new label.
- The project constitution discourages new mandatory documents. The user has explicitly asked for this one, and the plan will record in its Constitution Check why the Verification Plan section alone cannot carry it.
- The constitution's no-duplication rule is respected by having items reference obligations by identifier rather than repeating their scenario and expected outcome text. The one exception is each acceptance scenario's text, which the checklist quotes word for word so that it sits beside its items (FR-017); the plan records this as a departure, and the check keeps the quote identical to the specification.
- "Backend" and "frontend" are illustrated in examples and documentation; no feature type is detected or required.
- Closeness of an item's wording to its acceptance scenario (FR-016) is a rule for the agent and a review aid (FR-017), not a deterministic check: items are refinements, so their text cannot be compared exactly.
- Detection of implementation-specific wording by the check is limited to what can be done repeatably (file paths and identifiers that appear in the design or task list). Judgement on subtler wording rests with the process rules and the reviewer.
- Which evidence location a feature uses follows from what is on disk, not from dates: a feature that already has `tdd-evidence.md` at the top of its directory keeps it there, including when the planning stage is rerun to add a behaviour checklist; any other feature under the process uses `tests/`.
- Human review of the checklist is encouraged and supported, not enforced. Approver names for changed items are recorded as given and not verified, as with existing approvals.
- The custom checklist command and the specification quality checklist keep their current behaviour and locations. The feature's `tests/` folder holds verification artefacts about the feature; it is not where the project's executable tests live.

## System Context *(when the feature involves people or external systems)*

**System context view**: [context.md](../../docs/architecture/context.md) (not yet created)

| Actor or external system | Type | Role in this feature | In context view? |
|--------------------------|------|----------------------|------------------|
| Developer | Person | Takes a feature through the lifecycle, answers clarification requests, and corrects the specification when review finds a gap | New |
| Technical lead / reviewer | Person | Reviews the behaviour checklist before implementation and uses it with the evidence summary when reviewing finished work | New |
| Coding agent | External system | Writes the behaviour checklist from the specification and Verification Plan, and writes tests that trace to it | New |
| Spec Kit | External system | Provides the lifecycle stages and the feature directory in which the checklist lives | New |

**Changes to the system context**: None beyond those introduced by the integrated TDD feature (`001-integrated-tdd`).
