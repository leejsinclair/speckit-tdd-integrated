# Feature Specification: Verification Only Where It Is Possible

**Feature Branch**: `003-no-tooling-manual-verification`

**Created**: 2026-10-17

**Status**: Draft

**Input**: User description: "Use TDD and BDD only where they are possible, and never block development." A project with no test tooling (for example a new project), a test that needs a service the agent cannot reach (a cache, a queue, a database), and a check that only a person can do must each be recorded openly and must not stop the developer from working.

## Clarifications

### Session 2026-10-17

- Q: For a project with no runnable test command, should the process propose and install a framework? → A: No. The process warns, records that there is no test tooling, and carries on. It never chooses or installs a framework, and the checks switch on once the developer declares a command.
- Q: How are checks that cannot be run, or that only a person can do, recorded? → A: A Manual verification list in the plan, and a `deferred` status for an obligation, with a reason. Neither blocks completion of a task, and neither is ever reported as verified.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A project with no test tooling can still be specified, planned and built (Priority: P1)

A developer starts a new project that has no test framework yet. They take a feature through specification, planning, tasks and implementation as usual. Every stage completes. Each tells the developer plainly that the project has no test tooling, that nothing is being verified by tests, and that declaring a test command later switches the checks on. The obligations and the behaviour checklist are still written and checked, because they document the intended behaviour and keep the requirements traceable.

**Why this priority**: Today the process stops dead in a new project: planning fails, no tasks are generated and implementation cannot begin. That is the largest block on development and the one that makes the process unusable for new projects.

**Independent Test**: In an empty project with no test command, run the five stages for a small feature. Confirm that each completes without refusal, that the plan and the reports say the project has no test tooling, and that no framework was chosen or installed.

**Acceptance Scenarios**:

1. **Given** a project with no runnable test command, **When** the developer completes the planning stage, **Then** the plan records that there is no test tooling, the plan check passes, and the report says so and that declaring a command switches the checks on.
2. **Given** a plan that records no test tooling, **When** the developer generates tasks, **Then** tasks are generated, each test task still names the obligation it would serve, and none is refused.
3. **Given** a plan that records no test tooling, **When** the developer runs implementation, **Then** no baseline test run is demanded, tasks can be marked complete, and the final report states that nothing was verified by tests.
4. **Given** a plan that records no test tooling, **When** the behaviour checklist is checked, **Then** the checklist rules apply as they do in any project.
5. **Given** a feature in this state, **When** the developer later declares a test command in the plan, **Then** the baseline, the task gates and the compliance rules apply from that point as they do in any project.

---

### User Story 2 - A test that cannot be run is deferred, not blocking (Priority: P2)

A developer's feature needs a service the agent cannot reach, such as a cache, a queue or a database. The agent writes the test where it can, finds it cannot be run here, and records the obligation as deferred with a reason. The developer's work is not held. The obligation is never shown as verified.

**Why this priority**: Integration tests are the commonest case in which verification is not possible in the agent's environment. Today they leave the obligation blocked and every task that serves it incomplete, indefinitely.

**Independent Test**: Plan a feature with one obligation that needs a service that is not reachable. Record it as deferred with a reason, complete its tasks, and run status and compliance. Confirm that the tasks complete, that the obligation appears as deferred with its reason and not as verified, and that compliance reports it without failing.

**Acceptance Scenarios**:

1. **Given** an obligation whose test cannot be run because a service is unreachable, **When** the agent defers it with a reason, **Then** the deferral is recorded in the evidence with the reason and cannot be altered unnoticed.
2. **Given** a deferred obligation, **When** the tasks that serve it are marked complete, **Then** the completion is accepted.
3. **Given** a deferred obligation, **When** status is shown, **Then** the obligation appears as deferred with its reason, never as verified.
4. **Given** a deferred obligation, **When** compliance is run, **Then** it lists the obligation as an open notice and the result is not a failure.
5. **Given** an obligation that has been deferred, **When** a later run of its test passes, **Then** the obligation is shown as verified and is no longer listed as deferred.
6. **Given** an obligation deferred without a reason, **When** the deferral is recorded, **Then** it is refused.

---

### User Story 3 - Manual checks are listed, can be recorded, and never block (Priority: P3)

Some behaviour can only be checked by a person: a visual layout, a hand-over to an external system, an operational procedure. The plan holds a Manual verification list stating each check, its steps, the expected result and why it is not automated. A person may record that they did the check and its result. None of this holds up development.

**Why this priority**: The exemption table says only that something is verified another way. It holds no steps and no record of the check, so a reviewer cannot tell what was meant or whether it happened.

**Independent Test**: Add manual checks to a plan, run the plan check, record one check as passed by a named person and leave another undone, then run status and compliance. Confirm the list is checked for format and for the requirement or obligation each covers, that the done check shows its result and person, that the undone check shows as open, and that nothing fails.

**Acceptance Scenarios**:

1. **Given** a plan with a Manual verification list, **When** the plan check runs, **Then** each row must carry an id, the requirement or obligation it covers, steps, an expected result and a reason it is not automated, and a row naming something the feature does not hold is reported.
2. **Given** a plan with no manual checks, **When** it is written, **Then** the list holds a single `None` row.
3. **Given** a manual check, **When** a person records its result and their name, **Then** the record is added to the evidence and the check is shown as done with that result and name.
4. **Given** a manual check with no record, **When** status and compliance run, **Then** the check is shown as open and the result is not a failure.
5. **Given** a manual check recorded as failed, **When** status and compliance run, **Then** the failure is shown prominently and the result is still not a failure of development, which continues.
6. **Given** a requirement covered only by a manual check, **When** the behaviour checklist is read, **Then** the item names the manual check and is never shown as verified by tests.

---

### User Story 4 - Adopters know what applies when (Priority: P4)

A developer reading the documentation can tell when test-first development and the behaviour checklist apply, what happens when they cannot, and how to switch them on.

**Why this priority**: Without it the new states look like silent skipping.

**Independent Test**: Give a reader the README and the process rules and ask what happens in a project with no test command, for an obligation needing an unreachable service, and for a check only a person can do. Confirm they can answer each from the documentation alone, and that the shipped examples include a passing feature for a project with no test tooling and one with a deferred obligation and a manual check.

**Acceptance Scenarios**:

1. **Given** the repository documentation, **When** a new adopter reads it, **Then** they can state what changes with no test tooling, with a deferred obligation and with a manual check, and that none is reported as verified.
2. **Given** the shipped examples, **When** the check runs on them, **Then** the examples meant to comply pass.
3. **Given** the shipped example stories, **When** the story for a new project with no framework is run, **Then** the expected behaviour is that every stage completes and no framework is chosen.

---

### Edge Cases

- **EC-01** The extension's check script is absent: no change from today, the stages work as core Spec Kit does.
- **EC-02** A plan records no test tooling and also declares a command. The plan check reports the contradiction.
- **EC-03** A command is declared but not yet runnable (for example not yet installed). The first run fails as an environment failure and is handled as today, and the developer may defer the affected obligations.
- **EC-04** A feature already has recorded runs and the plan is changed to no test tooling. The check reports the contradiction, because recorded runs name a command the plan no longer declares.
- **EC-05** An obligation is deferred and the agent then runs its test and it passes. The deferral no longer stands, as User Story 2 scenario 5 states.
- **EC-06** Every obligation of a feature is deferred. The feature may still complete, and the completion report states that nothing was verified by tests.
- **EC-07** A deferred obligation or an open manual check is the only evidence for a requirement the developer calls critical. The report lists it, and what to do about it is the developer's decision.
- **EC-08** A manual check covers a requirement that is also exempted. Both may stand, and the exemption names the check.
- **EC-09** Features planned before this change use the old plan layout without a Manual verification list. They are not reported as failing for lacking one.

## Requirements *(mandatory)*

### Functional Requirements

#### No test tooling

- **FR-001**: When the project has no runnable test command, the plan MUST record that fact in the Verification commands table in a way the checks recognise, and the plan check MUST pass for that reason alone.
- **FR-002**: The process MUST NOT choose, install or configure a test framework, and MUST NOT write a test command that the project does not define.
- **FR-003**: While the plan records no test tooling, the tasks stage MUST generate tasks, with each test task still naming the obligation it would serve.
- **FR-004**: While the plan records no test tooling, implementation MUST NOT require a baseline test run, a failing-first run or a passing run, and tasks MUST be accepted as complete.
- **FR-005**: While the plan records no test tooling, the obligation checks and the behaviour checklist rules MUST apply unchanged.
- **FR-006**: Every stage report, and status, MUST state that the project has no test tooling and that nothing was verified by tests.
- **FR-007**: When a test command is declared, the process MUST apply the baseline, gates and compliance rules from that point, and the plan check MUST report a plan that records no test tooling and also declares a command.

#### Deferred obligations

- **FR-008**: An obligation MUST be capable of being recorded as deferred, with a reason that is not empty, as a tamper-evident record in the evidence.
- **FR-009**: A deferred obligation MUST NOT hold the completion of the tasks that serve it.
- **FR-010**: A deferred obligation MUST NOT be reported as verified in any report, and MUST be reported with its reason.
- **FR-011**: A later passing run of a deferred obligation's test MUST make the obligation verified and remove it from the deferred list.
- **FR-012**: When no test tooling is recorded, every obligation MUST be reported as deferred for that reason without a separate record for each.
- **FR-013**: A test that cannot be run because a service is unreachable MAY be deferred in place of being left blocked. A developer MAY still choose to hold the work instead, as today.

#### Manual verification

- **FR-014**: The plan MUST hold a Manual verification list with, for each check, an id, the requirement or obligation it covers, the steps, the expected result and the reason it is not automated, or a single `None` row.
- **FR-015**: The plan check MUST report a manual check with a missing field, a duplicate id, or a requirement or obligation the feature does not hold.
- **FR-016**: A person MUST be able to record the result of a manual check, `pass` or `fail`, with their name, as a tamper-evident record in the evidence. The record MUST NOT be required for any task to complete.
- **FR-017**: Status MUST show each manual check as open, or done with its result and name.
- **FR-018**: A requirement covered by a manual check MUST appear in the behaviour checklist in an item that names the check and MUST NOT be reported as verified by tests.

#### Reporting

- **FR-019**: Status MUST list deferred obligations with reasons and open manual checks as not verified.
- **FR-020**: Compliance MUST list deferred obligations and open or failed manual checks as notices, and MUST NOT fail for them.
- **FR-021**: The completion report of the implementation stage MUST count the obligations verified by tests, deferred, and covered by manual checks.

#### Compatibility and documentation

- **FR-022**: Features planned before this change MUST NOT be reported as failing for lacking a Manual verification list.
- **FR-023**: The README, the process rules, the stage wrappers, the CHANGELOG and the versions MUST describe the change, for release 0.3.0.
- **FR-024**: The repository MUST ship an example feature for a project with no test tooling, an example with a deferred obligation and a manual check, and a story for a new project with no framework.

### Key Entities

- **No test tooling record**: the plan's statement that the project has no runnable test command.
- **Deferral**: a tamper-evident evidence record that an obligation's test is not being run, with a reason.
- **Manual check**: a plan row with an id, what it covers, steps, expected result and why it is not automated.
- **Manual result**: a tamper-evident evidence record of a person's `pass` or `fail`, with their name.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In an empty project with no test command, 100% of the five stages complete without a refusal for a small feature.
- **SC-002**: In no scenario is a deferred obligation, or an obligation reported while no test tooling is recorded, shown as verified.
- **SC-003**: A feature with deferred obligations and open manual checks completes every task, and compliance exits with no failure caused by them.
- **SC-004**: Declaring a test command in a feature that recorded no test tooling brings the baseline and gates into effect, in 100% of seeded cases.
- **SC-005**: A reader of the documentation can answer the three questions of User Story 4 correctly without help.
- **SC-006**: The existing test suite passes unchanged except where a test asserted the behaviour this feature replaces.

## Assumptions

- The Verification commands table is where a plan records its test commands, and `None` is already the convention for an empty table of exemptions.
- The agent's choice of framework for a new project remains the developer's, taken outside the process.
- A developer who wants the work held for a missing service keeps the `environment-blocked` exception.
- Builds on `specs/002-bdd-behaviour-checklist`; its behaviour checklist rules are unchanged.
- The design was approved in outline in `/home/lee/.claude/plans/cozy-sauteeing-hamster.md`.
