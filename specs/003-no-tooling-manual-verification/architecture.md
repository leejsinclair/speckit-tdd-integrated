# Architecture: Verification Only Where It Is Possible

**Feature**: `003-no-tooling-manual-verification` | **Date**: 2026-10-17
**Feature docs**: [Spec](./spec.md) | [Plan](./plan.md) |
[Data model](./data-model.md) | [Contracts](./contracts/)
**System views**: not yet created. `docs/architecture/context.md`, `containers.md` and
`erd.md` do not exist; `/speckit-c4-system` has not yet been run for
[001](../001-integrated-tdd/architecture.md) or
[002](../002-bdd-behaviour-checklist/architecture.md), whose element aliases and labels are
reused here unchanged. The [Architecture Impact](#architecture-impact) table lists what this
feature changes relative to them.

## Components

The containers are those of 001: the Integrated TDD Preset, the Integrated TDD Extension and
Feature Artefacts. No container is added. Both packages change.

### Integrated TDD Preset

```mermaid
C4Component
    title Component View for Integrated TDD Preset - Verification Only Where It Is Possible

    Container_Boundary(tddPreset, "Integrated TDD Preset") {
        Component(planAddendum, "Plan Template Addendum", "Markdown template", "Adds the Manual verification sub-heading to the Verification Plan")
        Component(planWrapper, "Plan Wrapper", "Markdown command wrap", "Records no test tooling and writes the manual checks instead of stopping")
        Component(tasksWrapper, "Tasks Wrapper", "Markdown command wrap", "Generates tasks for a plan that records no test tooling")
        Component(analyzeWrapper, "Analyze Wrapper", "Markdown command wrap", "Copies the notices into its report")
        Component(implementWrapper, "Implement Wrapper", "Markdown command wrap", "Defers an unreachable test and reports verified and deferred counts")
    }

    System_Ext(specKit, "Spec Kit", "Provides the lifecycle and composes presets into its commands")
    System_Ext(codingAgent, "Coding Agent", "Carries out the lifecycle stages")
    Container(tddExtension, "Integrated TDD Extension", "Python 3 standard library, Markdown", "Holds the process rules and runs the deterministic checks")

    Rel(specKit, planAddendum, "Appends to the plan template", "Preset append")
    Rel(specKit, planWrapper, "Composes around the core plan command", "Preset wrap")
    Rel(specKit, tasksWrapper, "Composes around the core tasks command", "Preset wrap")
    Rel(specKit, analyzeWrapper, "Composes around the core analyze command", "Preset wrap")
    Rel(specKit, implementWrapper, "Composes around the core implement command", "Preset wrap")
    Rel(codingAgent, specKit, "Runs the composed lifecycle commands of", "Skill prompt")
    Rel(planWrapper, tddExtension, "Directs the agent to the plan check in", "File path")
    Rel(tasksWrapper, tddExtension, "Directs the agent to the tasks check in", "File path")
    Rel(analyzeWrapper, tddExtension, "Directs the agent to the read-only checks in", "File path")
    Rel(implementWrapper, tddExtension, "Directs the agent to defer and manual and status in", "File path")
```

| Component | Responsibility | Technology | Status | Source location |
|-----------|----------------|------------|--------|-----------------|
| Plan Template Addendum | Gains the `### Manual verification` sub-heading and an empty table | Markdown, preset `append` | Changed | `preset/templates/plan-addendum.md` |
| Plan Wrapper | Writes the `None` commands row when there is no way to run tests, writes the Manual verification table, and counts both in the report | Markdown, preset `wrap` | Changed | `preset/commands/speckit.plan.md` |
| Tasks Wrapper | States that a plan recording no test tooling passes, so tasks are generated | Markdown, preset `wrap` | Changed | `preset/commands/speckit.tasks.md` |
| Analyze Wrapper | Describes M1, M2, G12 and C9 and the notices among what it copies | Markdown, preset `wrap` | Changed | `preset/commands/speckit.analyze.md` |
| Implement Wrapper | Describes the no-tooling mode, `defer`, `manual` and the FR-021 counts | Markdown, preset `wrap` | Changed | `preset/commands/speckit.implement.md` |

The Tasks Template Addendum is unchanged. **Layout**: not checked. The configured Mermaid
CLI, `mmdc`, is not installed, so nothing was rendered; the declaration order follows the
ordering rules of the conventions.

### Integrated TDD Extension

```mermaid
C4Component
    title Component View for Integrated TDD Extension - Verification Only Where It Is Possible

    Container_Boundary(tddExtension, "Integrated TDD Extension") {
        Component(processRules, "Process Rules", "Markdown template", "States the agent-neutral rules for the cycle and its exceptions")
        Component(checkCli, "Check CLI", "Python 3 argparse", "Parses subcommands and reports findings and exit codes")
        Component(traceChecks, "Trace Checks", "Python 3", "Checks the plan, including the commands and manual checks")
        Component(checklistChecks, "Checklist Checks", "Python 3", "Applies rules B1 to B7 and accepts manual checks as verification")
        Component(gateRules, "Gate Rules", "Python 3", "Decides whether a task or a feature meets the process rules")
        Component(deferralChecks, "Deferral and Manual Checks", "Python 3", "Records deferrals and manual results and derives the deferred status")
        Component(commandRunner, "Command Runner", "Python 3 subprocess", "Runs a declared verification command and observes its result")
        Component(evidenceLedger, "Evidence Ledger", "Python 3", "Appends evidence entries and regenerates the review summary")
        Component(artefactParser, "Artefact Parser", "Python 3", "Reads the specification and plan and tasks and checklist and evidence")
    }

    ContainerDb(featureArtefacts, "Feature Artefacts", "Markdown files in git", "Stores the plan and tasks and checklist and evidence of one feature")
    System_Ext(codingAgent, "Coding Agent", "Carries out the lifecycle stages")

    Rel(codingAgent, processRules, "Reads the rules in", "File read")
    Rel(codingAgent, checkCli, "Runs checks and recordings through", "Shell command")
    Rel(codingAgent, featureArtefacts, "Writes the Manual verification table to", "File edit")
    Rel(checkCli, traceChecks, "Delegates plan and tasks checks to")
    Rel(checkCli, gateRules, "Delegates gate and status and compliance to")
    Rel(checkCli, deferralChecks, "Delegates defer and manual to")
    Rel(checkCli, commandRunner, "Delegates test runs to")
    Rel(traceChecks, checklistChecks, "Adds the checklist rules from")
    Rel(gateRules, deferralChecks, "Skips deferred obligations through")
    Rel(gateRules, checklistChecks, "Applies G10, G11, C8 and item status through")
    Rel(deferralChecks, evidenceLedger, "Appends chained rows through")
    Rel(commandRunner, evidenceLedger, "Records the outcome through")
    Rel(traceChecks, artefactParser, "Reads artefacts through")
    Rel(gateRules, artefactParser, "Reads artefacts through")
    Rel(deferralChecks, artefactParser, "Reads artefacts through")
    Rel(evidenceLedger, featureArtefacts, "Writes the deferral and manual result tables of", "File write")
    Rel(artefactParser, featureArtefacts, "Reads the five feature documents from", "File read")
```

| Component | Responsibility | Technology | Status | Source location |
|-----------|----------------|------------|--------|-----------------|
| Process Rules | Gains the section "When verification is not possible" | Markdown, extension template | Changed | `templates/tdd-process-rules.md` |
| Check CLI | Gains `defer`, `manual` and `approve` for `DF-` ids; `plan` passes with no test tooling | Python 3, `argparse` | Changed | `scripts/python/tdd_check.py` (`main`, handlers) |
| Trace Checks | Accepts a `None` commands row; adds M1 and M2; reports a `None` row beside commands | Python 3 | Changed | `scripts/python/tdd_check.py` (trace section) |
| Checklist Checks | B2 accepts `MV-` ids; item status `manual` | Python 3 | Changed | `scripts/python/tdd_check.py` (checklist section) |
| Gate Rules | G3, G4, G6 skip deferred obligations; adds G12 and C9; prints notices and counts | Python 3 | Changed | `scripts/python/tdd_check.py` (rules section) |
| Deferral and Manual Checks | Derives `deferred` status, decides whether a deferral stands, writes `defer` and `manual` rows | Python 3 | New | `scripts/python/tdd_check.py` (deferral section) |
| Command Runner | Refusal message names the recorded no-tooling state | Python 3, `subprocess` | Changed | `scripts/python/tdd_check.py` (run section) |
| Evidence Ledger | Renders and chains the two new tables only when they hold rows | Python 3 | Changed | `scripts/python/tdd_check.py` (ledger section) |
| Artefact Parser | Reads the Manual verification table and the two new evidence tables; optional | Python 3, `re` | Changed | `scripts/python/tdd_check.py` (parsing section) |

The Hook Adapter, Gate Event Handler and Evidence Template of 001 are unchanged and not
drawn. **Layout**: not checked, for the same reason as above.

## Flows

### Flow 1: A project with no test tooling reaches the end of implementation (User Story 1)

```mermaid
sequenceDiagram
    autonumber
    actor developer as Developer
    participant codingAgent as Coding Agent
    participant tddExtension as Integrated TDD Extension
    participant featureArtefacts as Feature Artefacts

    developer->>codingAgent: Run the plan command
    codingAgent->>featureArtefacts: Write the None row in Verification commands
    codingAgent->>tddExtension: plan
    tddExtension->>featureArtefacts: Read spec.md and plan.md
    tddExtension-->>codingAgent: passed with no test tooling recorded
    codingAgent-->>developer: Report that nothing will be verified by tests and how to switch the checks on
    developer->>codingAgent: Run the tasks and implement commands
    codingAgent->>featureArtefacts: Mark tasks complete
    featureArtefacts->>tddExtension: hook with the tool call
    tddExtension-->>codingAgent: Exit 0, every obligation deferred for no test tooling
    codingAgent-->>developer: Completion report with verified 0 and deferred N
```

**Covers**: FR-001 to FR-007, FR-012, FR-021; US1 scenarios 1 to 5; EC-06.

### Flow 2: An unreachable test is deferred and later verified (User Story 2)

```mermaid
sequenceDiagram
    autonumber
    actor developer as Developer
    participant codingAgent as Coding Agent
    participant tddExtension as Integrated TDD Extension
    participant featureArtefacts as Feature Artefacts

    codingAgent->>tddExtension: run --phase red for VO-002
    tddExtension-->>codingAgent: Record 7 fails, connection refused
    codingAgent->>tddExtension: classify 7 environment
    codingAgent->>tddExtension: defer --vo VO-002 --reason needs queue
    tddExtension->>featureArtefacts: Append DF-01 with basis environment failure 7
    tddExtension-->>codingAgent: deferred VO-002 as DF-01
    codingAgent->>featureArtefacts: Mark the task complete
    featureArtefacts->>tddExtension: hook with the tool call
    tddExtension-->>codingAgent: Exit 0, G3 G4 G6 skip VO-002
    developer->>codingAgent: Start the queue and run the test
    codingAgent->>tddExtension: run --phase green for VO-002
    tddExtension-->>codingAgent: Record 9 passes
    codingAgent->>tddExtension: status
    tddExtension-->>codingAgent: VO-002 verified, no longer deferred
```

**Covers**: FR-008 to FR-013; US2 scenarios 1 to 6; EC-05. A deferral on any other basis
waits for `approve DF-01 --by NAME` (FR-008A, G12).

### Flow 3: A manual check is listed, recorded and reported (User Story 3)

```mermaid
sequenceDiagram
    autonumber
    actor developer as Developer
    participant codingAgent as Coding Agent
    participant tddExtension as Integrated TDD Extension
    participant featureArtefacts as Feature Artefacts

    codingAgent->>featureArtefacts: Write MV-001 in Manual verification
    codingAgent->>tddExtension: plan
    tddExtension-->>codingAgent: M1 and M2 pass
    codingAgent->>tddExtension: compliance
    tddExtension-->>codingAgent: COMPLIANT with notice MV-001 open
    developer->>tddExtension: manual --check MV-001 --result pass --by NAME
    tddExtension->>featureArtefacts: Append MR-01 to Manual results
    codingAgent->>tddExtension: status
    tddExtension-->>codingAgent: MV-001 manual, pass by NAME
```

**Covers**: FR-014 to FR-018, FR-020; US3 scenarios 1 to 6; EC-08.

## Data

```mermaid
erDiagram
    VERIFICATION_COMMAND {
        string id PK "or None"
        string command
        string scope
    }
    VERIFICATION_OBLIGATION {
        string id PK "VO and a number"
    }
    MANUAL_CHECK {
        string id PK "MV and a number"
        string covers FK "one or more"
        string steps "not null"
        string expected_result "not null"
        string why_not_automated "not null"
    }
    DEFERRAL {
        string id PK "DF and a number"
        datetime time
        string obligation_ids FK "one or more"
        string reason "not null"
        string basis "environment failure or other"
        boolean needs_approval
        string approved_by
        string check_value "chained"
    }
    MANUAL_RESULT {
        string id PK "MR and a number"
        datetime time
        string check_id FK
        string result "pass or fail"
        string recorded_by "not null"
        string note
        string check_value "chained"
    }
    TEST_EXECUTION_RECORD {
        int seq PK
        string classification
    }
    BEHAVIOUR_ITEM {
        string id PK "BI and a number"
        string verified_by FK "obligation, exemption or manual check"
    }

    VERIFICATION_OBLIGATION ||--o{ DEFERRAL : "is deferred by"
    TEST_EXECUTION_RECORD ||--o{ DEFERRAL : "is the basis of"
    MANUAL_CHECK ||--o{ MANUAL_RESULT : "is recorded by"
    MANUAL_CHECK }o--o{ BEHAVIOUR_ITEM : "verifies"
    MANUAL_CHECK }o--o{ VERIFICATION_OBLIGATION : "covers"
```

| Entity | Status | Stored in | Notes |
|--------|--------|-----------|-------|
| VERIFICATION_COMMAND | Changed | Feature Artefacts: `plan.md` | A single `None` row means no test tooling |
| VERIFICATION_OBLIGATION | Changed | Feature Artefacts: `plan.md` | Status gains `deferred`, derived |
| MANUAL_CHECK | New | Feature Artefacts: `plan.md`, `### Manual verification` | Optional table |
| DEFERRAL | New | Feature Artefacts: evidence document, `## Deferrals` | Chained; approval where the basis is not an environment failure |
| MANUAL_RESULT | New | Feature Artefacts: evidence document, `## Manual results` | Chained; the latest row per check is its state |
| TEST_EXECUTION_RECORD | Existing | Feature Artefacts: the evidence document | Shown with the fields the basis needs |
| BEHAVIOUR_ITEM | Existing | Feature Artefacts: the checklist | May name a manual check |

## Architecture Impact

Relative to the views 001 and 002 will create, since the project-level views do not yet exist.

| View | Change | Element | Detail |
|------|--------|---------|--------|
| Context | None | - | No person or external system is added |
| Containers | Change | Feature Artefacts | Also stores a Manual verification table and the deferrals and manual results of the evidence |
| Containers | Change | Integrated TDD Extension to Feature Artefacts | The extension also writes deferrals and manual results |
| ERD | Add | MANUAL_CHECK, DEFERRAL, MANUAL_RESULT | And their relationships as drawn above |
| ERD | Change | VERIFICATION_COMMAND, VERIFICATION_OBLIGATION | A `None` row; a derived `deferred` status |
