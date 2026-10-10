# Feature Specification: Integrated Test-Driven Development for Spec Kit

**Feature Branch**: `001-integrated-tdd`

**Created**: 2026-10-10

**Status**: Draft

**Input**: User description: "@stories/base.md" — Integrated Test-Driven Development for Spec Kit: a rigorous, requirements-driven TDD process built into the existing Spec Kit lifecycle so that implementation quality and consistency improve, defects are detected earlier, and code review takes less time and effort.

## Clarifications

### Session 2026-10-10

- Q: When a repeatable check finds that a process rule was not met, should the agent be stopped from marking that task complete, or should the work carry on with the problem flagged for review? → A: Hard stop. The task cannot be marked complete until the rule is met or an exception is recorded with a rationale.
- Q: Which coding agents must the extension work with in its first release? → A: Claude Code first, built to extend. Full enforcement on Claude Code; the process rules and checks are kept agent-neutral so other agents can be added later.
- Q: How much of each test run should be kept as review evidence and saved with the feature? → A: A saved summary per run (what was run, the point in the cycle, the result, and the failure type if it failed), with full output not kept. The summaries are held in a separate evidence document in the feature's directory (for example `tdd-evidence.md`).
- Q: What should be delivered so that someone can evaluate whether the extension enforces the process? → A: Example stories plus an automated compliance check that reads a finished run's artefacts and evidence and reports compliant or non-compliant. A person still runs the stories through the agent.
- Q: When the agent has to wait for a person's decision, should it stop all work until the answer arrives, or keep going on tasks the decision does not affect? → A: Hold only what depends on it. The affected task and anything depending on it wait, other tasks continue, and the open decision is reported clearly.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verification intent is derived from requirements before implementation (Priority: P1)

A developer takes a story through the normal Spec Kit specification, planning and task stages. Without doing anything extra, they find that the resulting artefacts state how each requirement will be verified: the scenarios to test, the outcomes expected, the level of testing that suits each one, and which task is responsible for it. Where a requirement cannot sensibly be verified automatically, the artefacts say so and say why. Where the requirements are too ambiguous or contradictory to design a test against, the developer is asked rather than the agent quietly choosing an interpretation.

**Why this priority**: Everything else depends on this. If test intent is invented by the coding agent while it writes the code, tests merely restate the agent's own assumptions and give reviewers no independent evidence. Establishing intent from requirements and design is what makes later verification meaningful.

**Independent Test**: Take a representative story through specification, planning and task generation with the extension installed and stop before implementation. Confirm that every applicable requirement maps to planned verification or a documented exemption, that expected outcomes are stated without reference to how the code will be written, and that no additional command had to be run.

**Acceptance Scenarios**:

1. **Given** a specification with functional requirements, acceptance scenarios and edge cases, **When** the developer completes the planning stage, **Then** each applicable requirement has identified verification scenarios with expected outcomes, or an explicit explanation of why automated verification is inappropriate.
2. **Given** a technical design that includes interfaces, data integrity rules, security requirements or integration boundaries, **When** verification is planned, **Then** those constraints are reflected in the verification approach and in the testing levels chosen.
3. **Given** a completed plan, **When** tasks are generated, **Then** each task that delivers behaviour identifies the tests needed to verify it and is ordered so that the test work precedes the behaviour it verifies.
4. **Given** a requirement that is materially ambiguous or contradicts another requirement in a way that changes what a test should assert, **When** verification is being planned, **Then** the ambiguity is raised with the developer for clarification and is not silently resolved.
5. **Given** a small, low-risk change, **When** verification is planned, **Then** the amount of test planning is proportionate to the change and does not impose the same ceremony as a large or high-risk feature.

---

### User Story 2 - Implementation proceeds through Red → Green → Refactor with real evidence (Priority: P2)

A developer starts the normal implementation stage. The coding agent works through the tasks in small increments. For each behaviour it first writes or updates a test, runs it and confirms it fails for the intended reason, then makes the smallest change that satisfies it, reruns the tests to confirm they pass, and tidies the code while keeping the tests passing. Every claim that a test failed or passed is backed by an actual test run. The developer is not interrupted during routine cycles.

**Why this priority**: This is the core behavioural change the feature exists to deliver. It depends on Story 1 for its inputs, but it is where defects are caught early instead of at review.

**Independent Test**: Run the implementation stage on a feature whose verification intent already exists. Inspect the recorded evidence and confirm that for each behaviour a failing run preceded the implementation change, a passing run followed it, and both come from real executions.

**Acceptance Scenarios**:

1. **Given** a task that delivers new behaviour, **When** the agent begins it, **Then** a relevant test is created or updated and executed before any corresponding implementation change is made.
2. **Given** a newly written test, **When** it is first executed, **Then** the agent establishes that it fails, and that it fails for the intended reason rather than because of an unrelated error.
3. **Given** a test that is failing for the intended reason, **When** the agent implements the behaviour, **Then** it makes the minimum change needed and reruns the relevant tests to establish that they now pass.
4. **Given** passing tests, **When** the agent refactors, **Then** the affected tests are rerun and remain passing.
5. **Given** work spanning several tasks, **When** implementation proceeds, **Then** tests are run throughout rather than deferred to the end, relevant existing tests are run alongside new ones, and broad or expensive suites are run at sensible checkpoints rather than after every change.
6. **Given** a test failure during implementation, **When** dependent work is next in line, **Then** the failure is investigated and resolved first, unless a documented exception applies.
7. **Given** routine cycles with no ambiguity, trade-off or exception, **When** the agent works through them, **Then** it proceeds without asking the developer for approval.

---

### User Story 3 - Passing tests cannot be achieved by weakening the verification (Priority: P3)

A technical lead needs to trust that a green test suite means something. When the coding agent finds it hard to make a test pass, it must not delete the test, loosen its assertions, skip it, or change the requirement. If a test expectation genuinely needs to change because the intended behaviour is different from what was planned, that change is justified against the requirements and, where it alters intended behaviour, approved by a person.

**Why this priority**: Without this protection, Stories 1 and 2 can be satisfied superficially. An agent optimising for a passing suite is the specific failure this feature must prevent, but the protection only has value once the cycle in Story 2 exists.

**Independent Test**: Present the agent with a situation where the simplest route to a passing suite is to weaken or remove a test. Confirm that it does not take that route, and that any change to a test expectation is recorded with a justification tied to the requirements.

**Acceptance Scenarios**:

1. **Given** an implementation that fails an existing test, **When** the agent responds, **Then** it does not remove, weaken, skip or bypass the test solely to obtain a pass.
2. **Given** a test whose expected outcome must change, **When** the change alters the intended behaviour, **Then** it is justified against the approved requirements and submitted for human approval before it is accepted.
3. **Given** a newly written test, **When** it is assessed, **Then** its assertions check a meaningful outcome of the behaviour and not merely that the code ran without error.
4. **Given** a test that uses mocks, fixtures or test doubles, **When** it covers an important integration boundary, **Then** the doubles do not hide failures that the boundary could produce.
5. **Given** incomplete verification coverage, **When** results are reported, **Then** passing tests are not presented as proof that all requirements are met.

---

### User Story 4 - Blocked, failed and impractical cases are handled openly (Priority: P4)

Sometimes test-first development does not fit: legacy code with no test seams, an external system that cannot be exercised, generated code, a data migration, infrastructure changes or exploratory work. Sometimes the test environment itself is broken. In each case the developer sees what happened, why the usual cycle was not followed, and what was done to verify the work instead. Nothing is quietly skipped and nothing incomplete is reported as done.

**Why this priority**: Real projects contain these cases, and a process that cannot accommodate them will be bypassed. It ranks below the core cycle because it governs departures from that cycle.

**Independent Test**: Run implementation on scenarios that include an environment failure, a change where an initial failing test cannot meaningfully be demonstrated, and a change of a kind unsuited to test-first development. Confirm each is classified correctly, recorded with a rationale and an alternative verification approach, and reported as what it is.

**Acceptance Scenarios**:

1. **Given** a test run that fails, **When** the agent assesses it, **Then** it distinguishes an environmental or infrastructure failure from an implementation defect and from an assertion failure, and reports which it is.
2. **Given** a behaviour for which a meaningful initial failure cannot reasonably be demonstrated, **When** the agent proceeds, **Then** it records the reason and follows a stated alternative verification approach.
3. **Given** a change involving legacy code, external systems, generated code, migrations, infrastructure or exploratory work, **When** verification is chosen, **Then** it suits the nature of the change and is not forced into an unsuitable testing pattern.
4. **Given** a test that is blocked or a failure that remains unresolved, **When** the agent reports progress, **Then** the blocked or failed item is reported explicitly and the work is not described as successfully verified.
5. **Given** an exception that involves a consequential trade-off or exceeds what the agent may decide alone, **When** it arises, **Then** the developer is asked to decide, the affected task and any task depending on it wait for the answer, and tasks the decision does not affect continue.

---

### User Story 5 - Reviewers can see what was verified, what was not, and why (Priority: P5)

A reviewer opens a completed feature. From the feature's existing artefacts they can follow each requirement to its planned verification, to the tests that carry it out, and to the recorded outcome of running them. They can see at a glance what remains unverified and the reason. They do not have to rediscover any of this by reading the code, and they are not handed a second copy of information Spec Kit or the project's tooling already keeps.

**Why this priority**: Reducing review effort is the stated purpose of the feature, and this is where that benefit is realised. It ranks here because the evidence it presents is produced by the earlier stories.

**Independent Test**: Give a reviewer who did not take part in the work a completed feature and ask them to state, for each requirement, whether it is verified, by what, and with what result. Confirm they can do so from the artefacts alone.

**Acceptance Scenarios**:

1. **Given** a completed feature, **When** a reviewer inspects its artefacts, **Then** they can trace each requirement to its planned verification and to the relevant executable tests.
2. **Given** a completed implementation stage, **When** a reviewer looks for evidence, **Then** meaningful test execution outcomes, unresolved failures and recorded exceptions are available at the review stage.
3. **Given** a requirement, design decision or implementation that changes after verification was planned, **When** the change is made, **Then** the affected tests and verification obligations are updated to match.
4. **Given** the review evidence, **When** it is compared with what Spec Kit and existing project tooling already record, **Then** it does not duplicate that information.
5. **Given** significant testing decisions, unexpected failures or exceptions during the work, **When** a developer reads the evidence, **Then** each is explained in terms they can assess.

---

### User Story 6 - The process fits the project it is installed into (Priority: P6)

A technical lead adds the extension to a project that already has its own language, test framework, repository conventions, linting, static analysis, security scanning and CI pipeline. The TDD process uses the project's own verification commands and practices, leaves the other controls in force, and does not treat passing tests as a replacement for them. Existing Spec Kit commands and artefacts, and any other installed extensions, keep working. Developers do not have to learn or remember a new command.

**Why this priority**: Adoption across projects depends on it, but it concerns breadth of fit and not the core behaviour.

**Independent Test**: Install the extension into projects that differ in language, test framework and conventions, each with existing quality controls. Run the normal lifecycle and confirm that the project's own commands are used, existing controls still run and still gate, and no existing Spec Kit behaviour has changed unexpectedly.

**Acceptance Scenarios**:

1. **Given** a project with established verification commands and conventions, **When** the TDD process runs tests, **Then** it uses those commands and follows those conventions.
2. **Given** a project with linting, static analysis, security scanning, code-quality checks and CI, **When** the extension is installed, **Then** all of them remain effective and none is replaced, weakened or duplicated.
3. **Given** all tests passing, **When** readiness is reported, **Then** passing tests are not presented as satisfying static analysis, security checks or other required validation.
4. **Given** a project using any mainstream language and test framework, **When** the extension is installed, **Then** no particular testing framework is required of the project.
5. **Given** an existing Spec Kit project with other extensions installed, **When** this extension is added, **Then** existing commands, artefacts and extensions continue to work as before, and any change to existing behaviour is explicitly documented.
6. **Given** normal development, **When** a developer follows the standard Spec Kit lifecycle, **Then** the TDD behaviour occurs without the developer invoking a separate TDD command.

---

### User Story 7 - The extension's effectiveness can be evaluated (Priority: P7)

A technical lead deciding whether to roll the extension out across teams can test it against a set of representative stories and see whether it enforces the process correctly. The evaluation tells the difference between an agent that genuinely followed the process and one that only produced more test files. Where the team has baseline data, the evidence the extension produces can later be compared against review effort, escaped defects, test reliability and rework.

**Why this priority**: It establishes confidence in the feature and supports rollout decisions, but delivers no value until the behaviour it measures exists.

**Independent Test**: Run the extension against representative stories covering normal development, a regression, a material ambiguity, test failures, a justified exception and a small low-risk change. Confirm each produces the expected process behaviour and that a run which only adds test files without following the process is identified as non-compliant.

**Acceptance Scenarios**:

1. **Given** the delivered extension, **When** its documentation is consulted, **Then** observable criteria for its successful operation are stated.
2. **Given** representative stories covering normal development, regressions, ambiguity, failures, justified exceptions and a small low-risk change, **When** the extension is exercised against them, **Then** the expected behaviour for each is defined and can be checked.
3. **Given** two runs, one that followed the process and one that only generated additional test files, **When** the automated compliance check is run on each, **Then** it reports the first as compliant and the second as non-compliant, with the reasons.
4. **Given** a team with suitable baseline data, **When** they want to measure impact, **Then** the evidence produced supports comparison of review effort, escaped defects, test reliability and implementation rework.

---

### Edge Cases

- A project has no test tooling or no runnable verification command at all: this is surfaced during planning as a gap to resolve, and the agent does not proceed as though verification had happened.
- A new test passes the first time it is run: this is treated as a signal to investigate (behaviour already exists, or the test does not exercise it) and not as a successful Red step.
- A test fails, but for a reason other than the intended one, such as a missing dependency or a mistake in the test itself: this does not count as a valid Red step.
- A test passes and fails intermittently with no code change: it is reported as unreliable and not counted as evidence in either direction.
- Tests were already failing before the feature began: pre-existing failures are identified and kept distinct from failures the work introduces.
- Implementation reveals a scenario that planning did not anticipate: the scenario is added and reconciled with the requirements and design, and is not left as an untraceable test.
- Implementation reveals that a requirement is wrong: the requirement is raised for correction through the normal process, and the test is not altered to match the code.
- A requirement or design decision changes partway through implementation: affected verification obligations and tests are identified and updated.
- A change is intended to leave functional behaviour unchanged, such as a refactor or a performance optimisation: no new failing test is expected, because there is no new behaviour to fail. The reason is recorded, the existing tests covering that behaviour are run before and after the change and must pass both times, and where existing coverage is too thin to show that behaviour was preserved, that gap is addressed before the change is made.
- A task has no behaviour to test, such as documentation or configuration with no observable effect: it is recorded as not requiring automated verification, with the reason.
- The full test suite is too slow to run in every cycle: a relevant subset is run per increment and the broad suite at defined checkpoints.
- The extension is installed into a feature that is already partway through the lifecycle: stages already completed without verification intent are identified as a gap and not silently assumed to be covered.
- The extension is removed from a project: existing Spec Kit commands and artefacts continue to work.
- The agent cannot run tests in its environment at all: this is reported as a blocking condition and no pass or fail results are claimed.
- A person's decision is outstanding and every remaining task depends on it: the agent stops, reports the outstanding decision and what it is holding back, and does not proceed on an assumed answer.
- A task reaches completion without the evidence its process rules require, such as a recorded failing run before the implementation change: the task is not marked complete until the evidence exists or an exception with a rationale is recorded.

## Requirements *(mandatory)*

### Functional Requirements

#### Lifecycle integration

- **FR-001**: The extension MUST operate within the existing Spec Kit lifecycle stages and MUST NOT introduce a parallel development lifecycle.
- **FR-002**: TDD behaviour MUST take effect during the normal lifecycle without the developer invoking a separate TDD command.
- **FR-003**: Existing Spec Kit commands, artefacts and other installed extensions MUST continue to work as before once the extension is installed, and after it is removed.
- **FR-004**: Any change the extension makes to existing workflow behaviour MUST be justified and explicitly documented.
- **FR-005**: The extension MUST prefer adding to existing stages and artefacts over introducing new mandatory commands or documents.

#### Requirements-driven verification intent

- **FR-006**: Verification scenarios and their expected outcomes MUST be identified before implementation begins.
- **FR-007**: Verification scenarios MUST be derived from the functional requirements, acceptance scenarios, edge cases and failure conditions in the specification.
- **FR-008**: Verification planning MUST take account of relevant technical constraints from the design, including interfaces, data integrity rules, security requirements and integration boundaries.
- **FR-009**: Each applicable requirement MUST have identifiable verification coverage or an explicit explanation of why automated verification is inappropriate.
- **FR-010**: Expected outcomes MUST be defined from the requirements and design, independently of the implementation.
- **FR-011**: The planning stage MUST identify the testing levels appropriate to the change (for example unit, integration, contract and end-to-end) and MUST NOT require any single level for all verification.
- **FR-012**: Tasks that deliver behaviour MUST identify the tests needed to verify that behaviour, with dependencies that place test work before the behaviour it verifies.
- **FR-013**: The extent of test planning MUST be proportionate to the scope, risk and complexity of the change.
- **FR-014**: The process MUST NOT require all executable tests to be written before implementation begins.
- **FR-015**: Ambiguities or contradictions that materially affect test design MUST be raised for human clarification and MUST NOT be silently resolved by the agent. This is the test-design case of FR-052.
- **FR-016**: Additional scenarios discovered during implementation MUST be reconciled with the requirements and design and recorded with the same traceability as planned scenarios.

#### Red → Green → Refactor

- **FR-017**: For each behaviour, the agent MUST create or update a relevant test before implementing that behaviour, wherever test-first development is practical.
- **FR-018**: The agent MUST execute the test and establish that it fails for the intended reason before making the implementation change.
- **FR-019**: The agent MUST implement the minimum change needed to satisfy the failing test.
- **FR-020**: The agent MUST rerun the relevant tests after the implementation change to establish that the expected behaviour now passes.
- **FR-021**: After refactoring, the agent MUST rerun the affected tests and confirm they still pass.
- **FR-022**: Reported test results MUST be based on actual execution and MUST NOT rest on the agent's assertion that tests should pass.
- **FR-023**: Where a meaningful initial failure cannot reasonably be demonstrated, the agent MUST record the reason and follow a stated alternative verification approach.

#### Incremental verification

- **FR-024**: Implementation MUST proceed in small increments, each verified before the next dependent increment begins.
- **FR-025**: Tests MUST be executed throughout implementation and MUST NOT be deferred until the end.
- **FR-026**: A failure MUST be investigated and resolved before dependent work proceeds, unless an explicitly documented exception applies.
- **FR-027**: Relevant existing tests MUST be run alongside new tests so that regressions are detected, and regressions MUST be investigated and not concealed.
- **FR-028**: Broad or expensive test suites MUST be run at appropriate checkpoints and not indiscriminately after every change.

#### Test integrity

- **FR-029**: The agent MUST NOT remove, weaken, skip or bypass a test solely to make the implementation pass.
- **FR-030**: Assertions MUST verify meaningful outcomes of the behaviour under test and not merely that code executes.
- **FR-031**: Tests MUST be consistent with the approved requirements and design.
- **FR-032**: A change to a test expectation that alters intended behaviour MUST be justified against the requirements and MUST receive human approval before it is accepted.
- **FR-033**: Mocks, fixtures and test doubles MUST NOT conceal failures at important integration boundaries.
- **FR-034**: Passing tests MUST NOT be presented as proof that all requirements are met when verification coverage is incomplete. This is a specific case of FR-040.
- **FR-035**: The agent MUST NOT alter requirements in order to achieve a passing test suite.

#### Failure handling and exceptions

- **FR-036**: The agent MUST distinguish environmental or infrastructure failures from implementation defects and from assertion failures, and report which applies.
- **FR-037**: Blocked tests and unresolved failures MUST be reported explicitly. FR-040 gives the general rule.
- **FR-038**: Every exception to test-first development MUST include a documented rationale and, where appropriate, an alternative verification strategy.
- **FR-039**: Changes involving legacy code, external systems, generated code, migrations, infrastructure or exploratory work MUST receive verification suited to their nature.
- **FR-040**: The agent MUST NOT silently skip a verification obligation or report incomplete verification as successful.

#### Traceability and review evidence

- **FR-041**: The feature's artefacts MUST allow a reviewer to trace each requirement to its planned verification and to the relevant executable tests.
- **FR-042**: Meaningful test execution outcomes, unresolved failures and recorded exceptions MUST be available at the review stage.
- **FR-043**: Reviewers MUST be able to identify what has been verified, what remains unverified, and why.
- **FR-044**: When requirements, design or implementation change, the affected tests and verification obligations MUST be updated to reflect the change.
- **FR-045**: Review evidence MUST NOT duplicate information already maintained by Spec Kit or by the project's existing tooling.
- **FR-062**: Each test run that counts as evidence MUST be saved as a summary stating what was run, the point in the cycle (baseline before work begins, failing-first, passing, post-refactor or checkpoint), the result and, for a failure, its classification. Full test output MUST NOT be stored as review evidence.
- **FR-063**: Test execution summaries MUST be kept in a single dedicated evidence document in the feature's directory, separate from the specification, plan and task documents, and saved with the feature.

#### Compatibility with existing engineering controls

- **FR-046**: The extension MUST leave existing linting, static analysis, security scanning, code-quality checks and CI pipelines in effect.
- **FR-047**: The process MUST NOT treat passing tests as a substitute for static analysis, security checks or other required validation.
- **FR-048**: The extension MUST work across different project languages, testing frameworks and repository conventions, and MUST NOT require a particular testing framework without justification.
- **FR-049**: The process MUST use the project's own verification commands and respect its established engineering practices.
- **FR-050**: The extension MUST NOT introduce checks that duplicate those the project already performs.
- **FR-061**: The first release MUST provide full enforcement, including the hard stop in FR-060, when the coding agent is Claude Code. The process rules and the repeatable checks MUST be defined independently of any one coding agent, so that support for another agent can be added without changing them.

#### Developer experience and accountability

- **FR-051**: The agent MUST explain significant testing decisions, unexpected failures and exceptions in terms a developer can assess.
- **FR-052**: Human clarification or approval MUST be requested when requirements are materially ambiguous, when verification requires a consequential trade-off, or when an exception exceeds the agent's authority. An exception exceeds the agent's authority when it is made because the work is legacy code or exploratory, when it is of a kind the process does not name, or when it offers no alternative verification. Any other exception needs approval only when the agent judges that it involves a consequential trade-off, and that judgement is visible to the reviewer.
- **FR-053**: Routine TDD cycles MUST proceed without approval requests.
- **FR-065**: While a requested clarification or approval is outstanding, the agent MUST NOT proceed with the affected task or any task that depends on it, MUST continue with tasks the decision does not affect, and MUST report the outstanding decision and the work it is holding back. The agent MUST NOT proceed on an assumed answer.
- **FR-054**: The artefacts MUST allow a developer to understand the purpose of each test, the behaviour it expects and the evidence supporting the implementation.

#### Evaluation

- **FR-055**: The extension MUST define observable criteria for its own successful operation.
- **FR-056**: The extension MUST be testable against representative stories covering normal development, regressions, ambiguity, failures, justified exceptions and a small low-risk change (for FR-013).
- **FR-057**: Evaluation of the extension MUST distinguish correct enforcement of the process from the mere generation of additional test files.
- **FR-064**: The extension MUST be delivered with a set of representative example stories, each with its defined expected behaviour, and an automated compliance check that reads the artefacts and evidence of a finished run and reports it as compliant or non-compliant with the reasons. Driving the agent through the example stories is done by a person and is not automated. The compliance check is an aid for whoever is assessing the extension and MUST NOT be a step that developers have to run during normal work.
- **FR-058**: The evidence the extension produces MUST support later comparison of review effort, escaped defects, test reliability and implementation rework where baseline data exists.
- **FR-059**: Conditions that can be checked objectively MUST be checked in a repeatable way that gives the same result each time, with agent judgement reserved for interpreting requirements, choosing appropriate tests and handling exceptions.
- **FR-060**: When such a check finds that a process rule has not been met for a task, the task MUST NOT be marked complete until the rule is met or a TDD Exception with a rationale is recorded for it. A violation MUST NOT be downgraded to a note for review. The check MUST run as part of the existing implementation stage, without the developer invoking it.

### Key Entities

- **Requirement**: A functional requirement, acceptance scenario, edge case, failure condition or success criterion from the specification, or a constraint from the technical design. The origin of all verification.
- **Verification Command**: A way the adopting project already runs its tests, declared once during planning. Test runs that count as evidence use only these commands.
- **Verification Obligation**: A statement that a particular requirement must be verified, covering the scenario, the expected outcome, the testing level and its current status (planned, in progress, verified, blocked, failed). Links one or more requirements to one or more tests.
- **Verification Exemption**: A recorded decision that a requirement will not be verified automatically, with the reason and any alternative means of verification.
- **Task**: A unit of implementation work from the task stage. Identifies the verification obligations it must satisfy and the order of test work relative to behaviour.
- **Executable Test**: A runnable check in the project's own test tooling that carries out one or more verification obligations.
- **Test Execution Record**: A summary of the outcome of an actual test run: what was run, when in the cycle (baseline, failing-first, passing, post-refactor, checkpoint), the result, and for a failure its classification (assertion, implementation defect, environment or unreliable; unclassified until it has been investigated). It does not include the full test output. Records are held in the feature's evidence document.
- **TDD Exception**: A recorded departure from the test-first cycle for a specific piece of work, with rationale, alternative verification approach and, where required, who approved it.
- **Expectation Change**: A recorded change to what a test expects, with its justification against the requirements and its approval status.
- **Decision**: A clarification or approval requested from a person, with the question, the tasks it holds back, and once resolved the answer and who gave it.
- **Review Evidence**: The view a reviewer uses, drawn from the above, showing what is verified, what is not, and why.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Before implementation begins, 100% of applicable requirements in a feature have either planned verification with a stated expected outcome or a documented exemption.
- **SC-002**: A developer completes a story from specification through implementation using only the standard lifecycle commands, with zero additional TDD-specific commands required.
- **SC-003**: For every implemented behaviour, the evidence shows either a failing run followed by a passing run, both from real executions, or a recorded exception with a rationale. No behaviour falls into neither category.
- **SC-004**: In evaluation scenarios where weakening or removing a test is the easiest route to a passing suite, the agent takes that route in 0% of cases without a recorded justification and, where intended behaviour changes, human approval.
- **SC-005**: A reviewer who did not take part in the work can state, for any requirement in a completed feature, whether it is verified, by which tests and with what result, in under 2 minutes using the feature's artefacts alone.
- **SC-006**: 100% of blocked tests, unresolved failures and exceptions that occurred during implementation appear in the evidence available at review; none is reported as successful verification.
- **SC-007**: Routine Red → Green → Refactor cycles generate zero approval requests to the developer; approval requests occur only for material ambiguity, consequential trade-offs or exceptions beyond the agent's authority.
- **SC-008**: The extension operates correctly on at least three projects that differ in language and test framework, using each project's own verification commands, without requiring any of them to adopt a new test framework.
- **SC-009**: After installation, 100% of the project's existing quality controls still run and still gate as before, and 100% of pre-existing Spec Kit commands and artefacts behave as before apart from documented changes.
- **SC-010**: When exercised against a representative set of stories covering normal development, a regression, a material ambiguity, a test failure, a justified exception and a small low-risk change, the extension produces the defined expected behaviour for every one.
- **SC-011**: The automated compliance check classifies a run that only added test files without following the process as non-compliant in every case tested, and gives the same result each time it is run on the same artefacts.
- **SC-012**: Developers and reviewers using the extension report that the tests' purpose and the supporting evidence are understandable, and that the process does not add disproportionate overhead, in at least 80% of responses gathered during trial use.

## Assumptions

- The extension is a separate extension in its own right, published for the author's team and available to the community. It takes the existing community Spec Kit TDD extension (https://github.com/d0whc3r/spec-kit-tdd) as a reference for its approach, but is not a contribution to it and does not require it to be installed. It differs from an approach built on additional commands: its requirements are met inside the existing Spec Kit stages. It is delivered through Spec Kit's standard extension mechanisms. How it is built is deliberately left to the planning stage, after the current Spec Kit repository and extension infrastructure have been examined.
- The extension is built first for the author's own team, as the way that team is expected to work, and is published so that others in the community can use it. Where the two pull in different directions, the team's way of working takes precedence over general configurability.
- Developers follow the same Spec Kit process they already use. The requirements in this specification are met inside the existing stages, and the set of commands a developer uses does not grow (FR-002, FR-005, SC-002).
- Once installed, TDD is the default for every feature in the project. Departures are handled per piece of work through recorded exceptions, not by switching the process off.
- "Wherever practical" is judged by the agent for routine cases and recorded when it decides test-first does not apply. A person decides when the departure involves a consequential trade-off, and always for the exceptions FR-052 lists as beyond the agent's authority.
- Human approval is required for a test expectation change only when it alters intended behaviour. Corrections that bring a test into line with the approved requirements need a recorded justification but not approval.
- Verification intent lives in the feature's existing Spec Kit artefacts. Test execution evidence lives alongside them in one dedicated evidence document in the feature's directory (for example `tdd-evidence.md`; the exact name is settled in planning), so that reviewers find both where they already look. This is the one new document the feature introduces, as an addition under FR-005.
- The project supplies a way to run its tests. Where it has none, that is treated as a gap to raise during planning, and the extension does not choose or install a test framework on the project's behalf.
- The first release targets Claude Code as the coding agent. Support for other coding agents that Spec Kit works with is outside this feature, though the design must not prevent it (FR-061).
- The coding agent is able to execute the project's verification commands in its working environment. Where it cannot, that is a blocking condition to report.
- Measuring actual reductions in review effort, escaped defects or rework depends on baseline data the adopting team may or may not hold. The extension makes such comparison possible; gathering baselines and running the comparison are outside this feature.
- The following are out of scope: replacing the project's test frameworks, CI pipelines, code review process or security tooling; mandating unit tests for everything; requiring all executable tests up front; treating full code coverage as correctness; removing human code review or developer accountability; and introducing a separate mandatory workflow that duplicates the Spec Kit lifecycle.
- No git branch was created for this feature, because no branch-creation hook is configured in this project. The feature branch name above is the intended name.

<!-- markdownlint-disable-file MD041 -->

## System Context *(when the feature involves people or external systems)*

**System context view**: [context.md](../../docs/architecture/context.md) (not yet created)

| Actor or external system | Type | Role in this feature | In context view? |
|--------------------------|------|----------------------|------------------|
| Developer | Person | Takes a story through the lifecycle, answers clarification requests, approves consequential exceptions and expectation changes, and remains accountable for the result | New |
| Technical lead / reviewer | Person | Adopts the extension for a project, reviews completed work using the evidence produced, and evaluates the extension's effectiveness | New |
| Coding agent | External system | Carries out the lifecycle stages: derives verification intent, writes tests and code, executes tests and records evidence | New |
| Spec Kit | External system | Provides the lifecycle, commands, artefacts and extension mechanisms that this feature integrates with | New |
| Project test tooling | External system | The adopting project's own test frameworks and verification commands, which run the tests and return the results | New |
| Project quality controls | External system | The adopting project's linting, static analysis, security scanning, code-quality checks and CI pipeline, which stay in force alongside the TDD process | New |

**Changes to the system context**: No project-level context view exists yet, so every actor and external system above is new to it.
