# Architecture: Integrated Test-Driven Development for Spec Kit

**Feature**: `001-integrated-tdd` | **Date**: 2026-10-10
**Feature docs**: [Spec](./spec.md) | [Plan](./plan.md) |
[Data model](./data-model.md) | [Contracts](./contracts/)
**System views**: not yet created. `docs/architecture/context.md`, `containers.md` and
`erd.md` do not exist, so every person, external system, container and entity below is new.
The [Architecture Impact](#architecture-impact) table is the input for creating them.

## Components

The system is delivered as two Spec Kit packages and keeps its data in the adopting
project's feature directory. That gives three containers. The two packages each get a
component view. The third, Feature Artefacts, is a file store and has no components; its
contents are in [Data](#data).

### Integrated TDD Preset

```mermaid
C4Component
    title Component View for Integrated TDD Preset - Integrated TDD

    Container_Boundary(tddPreset, "Integrated TDD Preset") {
        Component(planAddendum, "Plan Template Addendum", "Markdown template", "Adds the Verification Plan section to each new plan")
        Component(planWrapper, "Plan Wrapper", "Markdown command wrap", "Has the plan stage derive and check verification intent")
        Component(tasksAddendum, "Tasks Template Addendum", "Markdown template", "Adds the task label conventions to each new task list")
        Component(tasksWrapper, "Tasks Wrapper", "Markdown command wrap", "Has the tasks stage label tasks and order test work first")
        Component(analyzeWrapper, "Analyze Wrapper", "Markdown command wrap", "Has the analyze stage report verification coverage findings")
        Component(implementWrapper, "Implement Wrapper", "Markdown command wrap", "Has the implement stage follow the cycle and gate each task")
    }

    Container(tddExtension, "Integrated TDD Extension", "Python 3 standard library, Markdown", "Holds the process rules and runs the deterministic checks")
    ContainerDb(featureArtefacts, "Feature Artefacts", "Markdown files in git", "Stores the plan and tasks and evidence of one feature")
    System_Ext(specKit, "Spec Kit", "Provides the lifecycle and composes presets into its commands")
    System_Ext(codingAgent, "Coding Agent", "Carries out the lifecycle stages")

    Rel(specKit, planAddendum, "Appends to the plan template", "Preset append")
    Rel(specKit, tasksAddendum, "Appends to the tasks template", "Preset append")
    Rel(specKit, planWrapper, "Composes around the core plan command", "Preset wrap")
    Rel(specKit, tasksWrapper, "Composes around the core tasks command", "Preset wrap")
    Rel(specKit, analyzeWrapper, "Composes around the core analyze command", "Preset wrap")
    Rel(specKit, implementWrapper, "Composes around the core implement command", "Preset wrap")
    Rel(codingAgent, specKit, "Runs the composed lifecycle commands of", "Skill prompt")
    Rel(planWrapper, tddExtension, "Directs the agent to the rules and the plan check in", "File path")
    Rel(tasksWrapper, tddExtension, "Directs the agent to the rules and the tasks check in", "File path")
    Rel(analyzeWrapper, tddExtension, "Directs the agent to the read-only checks in", "File path")
    Rel(implementWrapper, tddExtension, "Directs the agent to the rules and the run and gate checks in", "File path")
    Rel(codingAgent, featureArtefacts, "Writes verification intent and task labels to", "File edit")
```

| Component | Responsibility | Technology | Status | Source location |
|-----------|----------------|------------|--------|-----------------|
| Plan Template Addendum | Adds the empty Verification Plan section, with its three tables, to the end of the plan template | Markdown, preset `append` | New | `preset/templates/plan-addendum.md` |
| Plan Wrapper | Declares the Verification Plan as a Phase 1 output; has the agent derive obligations from requirements and design, record exemptions, raise material ambiguity with the developer, and run the `plan` check | Markdown, preset `wrap` | New | `preset/commands/speckit.plan.md` |
| Tasks Template Addendum | Adds the `[VO-nnn]` and `[NT: reason]` label conventions to the end of the tasks template | Markdown, preset `append` | New | `preset/templates/tasks-addendum.md` |
| Tasks Wrapper | Makes test tasks mandatory for behaviour, has every task labelled and ordered test-first, and runs the `tasks` check | Markdown, preset `wrap` | New | `preset/commands/speckit.tasks.md` |
| Analyze Wrapper | Adds the `plan` and `tasks` findings to the analysis report without modifying anything | Markdown, preset `wrap` | New | `preset/commands/speckit.analyze.md` |
| Implement Wrapper | Has the agent record a baseline, work each task through Red, Green, Refactor using `run`, classify failures, record exceptions and decisions, run the gate before marking a task complete, and report what was and was not verified | Markdown, preset `wrap` | New | `preset/commands/speckit.implement.md` |

### Integrated TDD Extension

```mermaid
C4Component
    title Component View for Integrated TDD Extension - Integrated TDD

    Container_Boundary(tddExtension, "Integrated TDD Extension") {
        Component(processRules, "Process Rules", "Markdown template", "States the agent-neutral rules for the cycle and its exceptions")
        Component(gateHandler, "Gate Event Handler", "Markdown command file", "Binds the pre tool use event to the hook entry point")
        Component(checkCli, "Check CLI", "Python 3 argparse", "Parses subcommands and reports findings and exit codes")
        Component(hookAdapter, "Hook Adapter", "Python 3", "Turns an agent tool call payload into a file and its resulting content")
        Component(traceChecks, "Trace Checks", "Python 3", "Checks requirement coverage and task labels and task order")
        Component(gateRules, "Gate Rules", "Python 3", "Decides whether a task or a whole feature meets the process rules")
        Component(commandRunner, "Command Runner", "Python 3 subprocess", "Runs a declared verification command and observes its result")
        Component(evidenceLedger, "Evidence Ledger", "Python 3", "Appends evidence entries and regenerates the review summary")
        Component(artefactParser, "Artefact Parser", "Python 3", "Reads the verification plan and task labels and evidence tables")
        Component(evidenceTemplate, "Evidence Template", "Markdown template", "Holds the starting content of an evidence document")
    }

    ContainerDb(featureArtefacts, "Feature Artefacts", "Markdown files in git", "Stores the plan and tasks and evidence of one feature")
    System_Ext(codingAgent, "Coding Agent", "Carries out the lifecycle stages")
    System_Ext(specKit, "Spec Kit", "Provides the lifecycle and composes presets into its commands")
    System_Ext(projectTestTooling, "Project Test Tooling", "The adopting project's own test frameworks and verification commands")

    Rel(codingAgent, processRules, "Reads the rules in", "File read")
    Rel(codingAgent, checkCli, "Runs checks and recordings through", "Shell command")
    Rel(specKit, gateHandler, "Dispatches the pre tool use event to", "Event dispatcher")
    Rel(gateHandler, checkCli, "Names the hook subcommand of", "Script frontmatter")
    Rel(checkCli, hookAdapter, "Passes the tool call payload to")
    Rel(hookAdapter, gateRules, "Requests a gate decision from")
    Rel(checkCli, traceChecks, "Delegates plan and tasks checks to")
    Rel(checkCli, gateRules, "Delegates gate and compliance checks to")
    Rel(checkCli, commandRunner, "Delegates test runs to")
    Rel(checkCli, evidenceLedger, "Delegates exceptions and decisions to")
    Rel(commandRunner, projectTestTooling, "Executes the declared command in", "Subprocess")
    Rel(commandRunner, evidenceLedger, "Records the outcome through")
    Rel(traceChecks, artefactParser, "Reads artefacts through")
    Rel(gateRules, artefactParser, "Reads artefacts through")
    Rel(evidenceLedger, evidenceTemplate, "Creates the document from", "File read")
    Rel(evidenceLedger, featureArtefacts, "Appends to tdd-evidence.md in", "File write")
    Rel(artefactParser, featureArtefacts, "Reads spec.md and plan.md and tasks.md and tdd-evidence.md from", "File read")
```

| Component | Responsibility | Technology | Status | Source location |
|-----------|----------------|------------|--------|-----------------|
| Process Rules | The single statement of the process: deriving verification intent, the cycle, test integrity, failure classification, exceptions, when to ask a person, and what may be reported. Read by all four wrapped commands | Markdown, extension template | New | `templates/tdd-process-rules.md` |
| Gate Event Handler | Carries the `scripts:` frontmatter that Spec Kit's event dispatcher resolves for the `pre_tool_use` event. Not registered as a command | Markdown command file | New | `commands/speckit.integrated-tdd.gate.md` |
| Check CLI | Entry point: subcommand parsing, feature directory resolution, text and JSON output, exit codes | Python 3, `argparse` | New | `scripts/python/tdd_check.py` (`main`, subcommand handlers) |
| Hook Adapter | The only agent-specific code: reads the Claude Code `PreToolUse` payload, computes the content the edit would produce, and finds tasks newly marked complete | Python 3 | New | `scripts/python/tdd_check.py` (hook section) |
| Trace Checks | Rules C1 to C3: requirement coverage, task labelling, test-before-behaviour order | Python 3 | New | `scripts/python/tdd_check.py` (trace section) |
| Gate Rules | Rules G1 to G9 per task and C4 to C7 per feature; derives obligation status | Python 3 | New | `scripts/python/tdd_check.py` (rules section) |
| Command Runner | Resolves a declared command, substitutes the selector, executes it, checks the expected failure text, and fingerprints the test files | Python 3, `subprocess`, `hashlib` | New | `scripts/python/tdd_check.py` (run section) |
| Evidence Ledger | The only writer of `tdd-evidence.md`: appends records, exceptions, expectation changes and decisions, chains check values, and regenerates the Summary | Python 3 | New | `scripts/python/tdd_check.py` (ledger section) |
| Artefact Parser | Reads requirement ids from `spec.md`, the Verification Plan from `plan.md`, task lines from `tasks.md` and the tables of `tdd-evidence.md` | Python 3, `re` | New | `scripts/python/tdd_check.py` (parsing section) |
| Evidence Template | The headings and empty tables a new `tdd-evidence.md` starts from | Markdown, extension template | New | `templates/tdd-evidence-template.md` |

## Flows

All flows are drawn at container level, because each one crosses the coding agent, the two
packages and the feature's files. Messages to the extension are subcommands of the
[check script](./contracts/check-cli.md).

### Flow 1: Verification intent is derived during plan and tasks (User Story 1)

```mermaid
sequenceDiagram
    autonumber
    actor developer as Developer
    participant codingAgent as Coding Agent
    participant tddPreset as Integrated TDD Preset
    participant tddExtension as Integrated TDD Extension
    participant featureArtefacts as Feature Artefacts

    developer->>codingAgent: Run the plan command
    codingAgent->>tddPreset: Read the composed plan command
    tddPreset-->>codingAgent: Core plan steps plus Verification Plan steps
    codingAgent->>tddExtension: Read tdd-process-rules
    codingAgent->>featureArtefacts: Read spec.md requirements and scenarios and edge cases
    opt A requirement is ambiguous in a way that changes what a test asserts
        codingAgent->>developer: Ask for clarification
        developer-->>codingAgent: Answer
    end
    codingAgent->>featureArtefacts: Write Verification Plan to plan.md
    codingAgent->>tddExtension: plan
    alt Every FR has an obligation or an exemption
        tddExtension-->>codingAgent: exit 0
    else Coverage gap or no verification command
        tddExtension-->>codingAgent: exit 1 with C1 findings
        codingAgent->>featureArtefacts: Add the missing obligations or exemptions
        codingAgent->>tddExtension: plan
        tddExtension-->>codingAgent: exit 0
    end
    codingAgent-->>developer: Plan complete with verification coverage
    developer->>codingAgent: Run the tasks command
    codingAgent->>featureArtefacts: Write tasks.md with VO and NT labels and test tasks first
    codingAgent->>tddExtension: tasks
    tddExtension-->>codingAgent: exit 0
    codingAgent-->>developer: Tasks complete
```

**Covers**: FR-002, FR-006 to FR-015, SC-001; User Story 1 acceptance scenarios 1 to 5.
**Notes**: The check is repeated until it passes; the stage does not report completion on
a failing check. Proportion (FR-013) is the agent's judgement on how many obligations a
requirement needs, and the check only requires that each requirement has at least one or
an exemption.

### Flow 2: One task through Red, Green, Refactor (User Story 2)

```mermaid
sequenceDiagram
    autonumber
    actor developer as Developer
    participant codingAgent as Coding Agent
    participant tddExtension as Integrated TDD Extension
    participant projectTestTooling as Project Test Tooling
    participant featureArtefacts as Feature Artefacts

    developer->>codingAgent: Run the implement command
    codingAgent->>tddExtension: plan and tasks
    tddExtension-->>codingAgent: exit 0
    codingAgent->>tddExtension: run --phase baseline --command suite
    tddExtension->>projectTestTooling: Execute the broad command
    projectTestTooling-->>tddExtension: Exit status and output
    tddExtension->>featureArtefacts: Append baseline record to tdd-evidence.md
    loop Each obligation of the task
        codingAgent->>codingAgent: Write the test for the obligation
        codingAgent->>tddExtension: run --phase red --expect text
        tddExtension->>projectTestTooling: Execute the focused command
        projectTestTooling-->>tddExtension: Non-zero exit and output
        tddExtension->>featureArtefacts: Append valid red record with fingerprint
        tddExtension-->>codingAgent: exit 0
        codingAgent->>codingAgent: Make the minimum implementation change
        codingAgent->>tddExtension: run --phase green
        tddExtension->>projectTestTooling: Execute the focused command
        projectTestTooling-->>tddExtension: Zero exit
        tddExtension->>featureArtefacts: Append valid green record
        tddExtension-->>codingAgent: exit 0
        opt The code is refactored
            codingAgent->>tddExtension: run --phase refactor
            tddExtension->>projectTestTooling: Execute the focused command
            projectTestTooling-->>tddExtension: Zero exit
            tddExtension->>featureArtefacts: Append valid refactor record
        end
    end
    codingAgent->>tddExtension: gate --task
    tddExtension-->>codingAgent: exit 0
    codingAgent->>featureArtefacts: Mark the task X in tasks.md
    codingAgent-->>developer: Progress report with no approval requested
```

**Covers**: FR-017 to FR-022, FR-024 to FR-028, FR-053, FR-062, SC-003, SC-007; User Story
2 acceptance scenarios 1 to 5 and 7.
**Notes**: A broad `checkpoint` run follows the last task of each phase and is not shown.
The edit that marks the task complete passes through the runtime event shown in Flow 3. No output is stored beyond the
matched expected text.

### Flow 3: A task is marked complete without evidence (User Story 2, failure path)

```mermaid
sequenceDiagram
    autonumber
    participant codingAgent as Coding Agent
    participant specKit as Spec Kit
    participant tddExtension as Integrated TDD Extension
    participant featureArtefacts as Feature Artefacts

    codingAgent->>specKit: PreToolUse for an Edit of tasks.md
    specKit->>tddExtension: hook with the tool call payload
    tddExtension->>featureArtefacts: Read plan.md and tasks.md and tdd-evidence.md
    alt No task changes from open to X
        tddExtension-->>specKit: exit 0
        specKit-->>codingAgent: Edit allowed
    else A newly completed task passes the gate
        tddExtension-->>specKit: exit 0
        specKit-->>codingAgent: Edit allowed
    else A newly completed task fails the gate
        tddExtension-->>specKit: exit 2 with findings by rule
        specKit-->>codingAgent: Edit refused with the findings
        codingAgent->>codingAgent: Meet the rule or record an exception with a rationale
    end
```

**Covers**: FR-059, FR-060, FR-061; the edge case for a task reaching completion without
its evidence.
**Notes**: Spec Kit here is its generated event dispatcher, `.specify/events.py`, which
Claude Code calls from `.claude/settings.json`. The handler runs no tests and returns
within the 30 second event timeout. An edit to `tdd-evidence.md` takes the same path and is
always refused. Edits made through a shell command do not raise this event; the final
`gate --all` in the implement stage and the compliance check catch them afterwards.

### Flow 4: A test changes between Red and Green (User Story 3)

```mermaid
sequenceDiagram
    autonumber
    actor developer as Developer
    participant codingAgent as Coding Agent
    participant tddExtension as Integrated TDD Extension
    participant projectTestTooling as Project Test Tooling
    participant featureArtefacts as Feature Artefacts

    codingAgent->>tddExtension: run --phase green
    tddExtension->>projectTestTooling: Execute the focused command
    projectTestTooling-->>tddExtension: Zero exit
    tddExtension->>featureArtefacts: Append green record with a changed fingerprint
    codingAgent->>tddExtension: gate --task
    tddExtension-->>codingAgent: exit 1 with G5 test changed after its red run
    alt The test was weakened only to pass
        codingAgent->>codingAgent: Restore the test and fix the implementation
        codingAgent->>tddExtension: run --phase green
        tddExtension-->>codingAgent: exit 0 with the original fingerprint
    else The expectation was wrong against the requirements
        opt The change alters intended behaviour
            codingAgent->>developer: Ask for approval with the justification
            developer-->>codingAgent: Approval
        end
        codingAgent->>tddExtension: expectation --requirement --justification
        tddExtension->>featureArtefacts: Append expectation change with the new fingerprint
    end
    codingAgent->>tddExtension: gate --task
    tddExtension-->>codingAgent: exit 0
```

**Covers**: FR-029, FR-031, FR-032, FR-035, SC-004; User Story 3 acceptance scenarios 1
and 2.
**Notes**: The fingerprint shows that a test changed, not whether the change weakened it.
Whether assertions are meaningful (FR-030) and whether test doubles hide boundary failures
(FR-033) are rules the agent follows from the process rules and a reviewer assesses; no
check claims to decide them.

### Flow 5: A blocked run, an exception and a decision (User Story 4)

```mermaid
sequenceDiagram
    autonumber
    actor developer as Developer
    participant codingAgent as Coding Agent
    participant tddExtension as Integrated TDD Extension
    participant projectTestTooling as Project Test Tooling
    participant featureArtefacts as Feature Artefacts

    codingAgent->>tddExtension: run --phase green
    tddExtension->>projectTestTooling: Execute the focused command
    projectTestTooling-->>tddExtension: Non-zero exit
    tddExtension->>featureArtefacts: Append failing record as unclassified
    tddExtension-->>codingAgent: exit 1 with the output tail
    codingAgent->>codingAgent: Investigate the cause
    alt Implementation defect or assertion failure
        codingAgent->>tddExtension: classify --as defect
        codingAgent->>codingAgent: Fix before dependent work
        codingAgent->>tddExtension: run --phase green
        tddExtension-->>codingAgent: exit 0
    else Environment failure
        codingAgent->>tddExtension: classify --as environment
        codingAgent->>tddExtension: exception --kind environment-blocked --rationale
        tddExtension->>featureArtefacts: Append exception and regenerate the summary
        codingAgent-->>developer: Report the task as blocked and not verified
    else Test-first does not suit the change and the trade-off is consequential
        codingAgent->>tddExtension: decision open --question --tasks
        tddExtension->>featureArtefacts: Append open decision
        codingAgent->>developer: Ask for the decision and list the tasks held back
        codingAgent->>codingAgent: Continue with tasks the decision does not affect
        developer-->>codingAgent: Decision
        codingAgent->>tddExtension: decision resolve --answer --by
        codingAgent->>tddExtension: exception --kind --rationale --alternative --approved-by
        tddExtension->>featureArtefacts: Append resolution and exception
    end
```

**Covers**: FR-023, FR-026, FR-036 to FR-040, FR-052, FR-065, SC-006; User Story 4
acceptance scenarios 1 to 5.
**Notes**: While a decision is open, gate rule G2 fails for every task it lists, so the
runtime event refuses to mark them complete. When every remaining task is listed, the
agent stops and reports. An `environment-blocked` exception leaves the task incomplete.

### Flow 6: A reviewer reads what was verified (User Story 5)

```mermaid
sequenceDiagram
    autonumber
    actor reviewer as Technical Lead or Reviewer
    participant codingAgent as Coding Agent
    participant tddExtension as Integrated TDD Extension
    participant featureArtefacts as Feature Artefacts

    codingAgent->>tddExtension: gate --all at the close of the implement stage
    tddExtension->>featureArtefacts: Read plan.md and tasks.md and tdd-evidence.md
    tddExtension-->>codingAgent: Findings for every completed task
    codingAgent->>tddExtension: status
    tddExtension->>featureArtefacts: Regenerate the Summary of tdd-evidence.md
    tddExtension-->>codingAgent: Review view
    codingAgent-->>reviewer: Report of verified and unverified requirements with reasons
    reviewer->>featureArtefacts: Read the Summary of tdd-evidence.md
    featureArtefacts-->>reviewer: Status and tests and latest result per obligation
    reviewer->>featureArtefacts: Follow an obligation to plan.md and tasks.md
    featureArtefacts-->>reviewer: Requirements and scenario and expected outcome and tasks
```

**Covers**: FR-034, FR-041 to FR-045, FR-047, FR-051, FR-054, FR-063, SC-005; User Story 5
acceptance scenarios 1, 2, 4 and 5.
**Notes**: The reviewer runs nothing. The Summary is rewritten on every write to the
evidence document, so it cannot lag behind the records. It refers to requirements, tasks
and tests by identifier and copies none of their content.

### Flow 7: The extension is installed into a project (User Story 6)

```mermaid
sequenceDiagram
    autonumber
    actor reviewer as Technical Lead or Reviewer
    participant specKit as Spec Kit
    participant tddExtension as Integrated TDD Extension
    participant tddPreset as Integrated TDD Preset
    participant codingAgent as Coding Agent

    reviewer->>specKit: specify extension add integrated-tdd
    specKit->>tddExtension: Validate extension.yml and copy the package
    specKit->>codingAgent: Add one PreToolUse entry to the agent settings
    specKit-->>reviewer: Extension installed with no new command
    reviewer->>specKit: specify preset add integrated-tdd
    specKit->>tddPreset: Validate preset.yml and copy the package
    specKit->>specKit: Compose the wrappers and addenda with other presets by priority
    specKit->>codingAgent: Regenerate the plan and tasks and analyze and implement skills
    specKit-->>reviewer: Preset installed
```

**Covers**: FR-001, FR-003, FR-005, FR-046, FR-048, FR-050, SC-002, SC-009; User Story 6
acceptance scenarios 2, 5 and 6.
**Notes**: Nothing in the project's test, lint or CI configuration is read or written at
installation. Removal reverses steps 2, 3, 6 and 8 through Spec Kit's own remove commands.
The project's verification commands enter at the plan stage, in Flow 1.

### Flow 8: An evaluator checks a finished run (User Story 7)

```mermaid
sequenceDiagram
    autonumber
    actor reviewer as Technical Lead or Reviewer
    actor developer as Developer
    participant codingAgent as Coding Agent
    participant tddExtension as Integrated TDD Extension
    participant featureArtefacts as Feature Artefacts

    reviewer->>developer: Hand over an example story and its expected behaviour
    developer->>codingAgent: Drive the story through the standard lifecycle
    codingAgent->>featureArtefacts: Produce the plan and tasks and evidence and code
    reviewer->>tddExtension: compliance
    tddExtension->>featureArtefacts: Read spec.md and plan.md and tasks.md and tdd-evidence.md
    alt The run followed the process
        tddExtension-->>reviewer: COMPLIANT and exit 0
    else The run only added test files
        tddExtension-->>reviewer: NON-COMPLIANT with findings by rule and exit 1
    end
    reviewer->>featureArtefacts: Compare the artefacts with the expected behaviour of the story
```

**Covers**: FR-055 to FR-058, FR-064, SC-010, SC-011; User Story 7 acceptance scenarios 1
to 4.
**Notes**: The compliance check is the gate rules applied to the whole feature, so it
cannot disagree with what the gate enforced. It is not called by any lifecycle command. A
run that only added test files has completed behaviour tasks with no valid red record,
which fails rule C5 through G3.

## Data

```mermaid
erDiagram
    REQUIREMENT }|..o{ VERIFICATION_OBLIGATION : "is verified by"
    REQUIREMENT ||--o| VERIFICATION_EXEMPTION : "is exempted by"
    VERIFICATION_OBLIGATION }o..o{ TASK : "is satisfied by"
    TASK |o..o{ TEST_EXECUTION_RECORD : "is worked on in"
    VERIFICATION_OBLIGATION }o..o{ TEST_EXECUTION_RECORD : "is evidenced by"
    VERIFICATION_COMMAND ||..o{ TEST_EXECUTION_RECORD : produces
    EXECUTABLE_TEST |o..o{ TEST_EXECUTION_RECORD : "is run in"
    TASK ||..o{ TDD_EXCEPTION : "is excused by"
    VERIFICATION_OBLIGATION }o..o{ TDD_EXCEPTION : "is covered by"
    TASK ||..o{ EXPECTATION_CHANGE : "is changed under"
    REQUIREMENT }|..o{ EXPECTATION_CHANGE : justifies
    TASK }|..o{ DECISION : "is held back by"

    REQUIREMENT {
        string id PK "FR or SC or acceptance scenario or edge case or design constraint"
    }
    VERIFICATION_COMMAND {
        string id PK
        string command "may contain a select placeholder"
        string scope "focused or broad"
        string source
    }
    VERIFICATION_OBLIGATION {
        string id PK "VO and a number"
        string requirement_ids FK "one or more"
        string scenario
        string expected_outcome "independent of the implementation"
        string level "unit or integration or contract or end-to-end or other"
        string origin "planned or discovered"
    }
    VERIFICATION_EXEMPTION {
        string requirement_id PK, FK
        string reason "not null"
        string alternative
    }
    TASK {
        string id PK
        boolean complete
        string obligation_ids FK "VO labels"
        string no_test_reason "NT label"
    }
    EXECUTABLE_TEST {
        string selector PK
    }
    TEST_EXECUTION_RECORD {
        int seq PK
        datetime time
        string task_id FK
        string obligation_ids FK
        string phase "baseline or red or green or refactor or checkpoint"
        string command_id FK
        string selector FK
        string result "pass or fail"
        boolean valid
        string classification "assertion or defect or environment or unreliable or unclassified"
        string files
        string fingerprint
        string note
        string check "chained with the previous record"
    }
    TDD_EXCEPTION {
        string id PK
        string task_id FK
        string obligation_ids FK
        string kind
        string rationale "not null"
        string alternative
        boolean needs_approval
        string approved_by
        datetime time
    }
    EXPECTATION_CHANGE {
        string id PK
        string task_id FK
        string requirement_ids FK "one or more"
        string files
        string justification "not null"
        boolean alters_behaviour
        string approved_by
        string new_fingerprint
        datetime time
    }
    DECISION {
        string id PK
        string question
        string task_ids FK "one or more"
        string status "open or resolved"
        string answer
        string decided_by
        datetime opened
        datetime resolved
    }
```

| Entity | Status | Stored in | Notes |
|--------|--------|-----------|-------|
| REQUIREMENT | Existing | Feature Artefacts: `spec.md`, and design constraints named in `plan.md` | Owned by Spec Kit. Read only; shown with its key |
| VERIFICATION_COMMAND | New | Feature Artefacts: `plan.md`, Verification Plan | At least one row required |
| VERIFICATION_OBLIGATION | New | Feature Artefacts: `plan.md`, Verification Plan | Identifiers are never reused. Status is derived, not stored |
| VERIFICATION_EXEMPTION | New | Feature Artefacts: `plan.md`, Verification Plan | Keyed by the requirement it exempts |
| TASK | Changed | Feature Artefacts: `tasks.md` | Owned by Spec Kit. Gains the `[VO-nnn]` and `[NT: reason]` labels |
| EXECUTABLE_TEST | Existing | The adopting project's source tree | Not stored by this feature; referred to by selector. Shown with its key |
| TEST_EXECUTION_RECORD | New | Feature Artefacts: `tdd-evidence.md` | Append-only, written only by the check script |
| TDD_EXCEPTION | New | Feature Artefacts: `tdd-evidence.md` | Approval required when flagged |
| EXPECTATION_CHANGE | New | Feature Artefacts: `tdd-evidence.md` | Approval required when it alters behaviour |
| DECISION | New | Feature Artefacts: `tdd-evidence.md` | Not named as an entity in the specification; modelled for FR-065 |

Lists of identifiers are held in one table cell, which is how a many-to-many relationship
is stored in Markdown, so no join entities appear. Review Evidence from the data model is a
generated view and is left out as a derived object.

## Architecture Impact

No project-level views exist, so every row is an addition.

| View | Change | Element | Detail |
|------|--------|---------|--------|
| Context | Add | Integrated TDD (the system) | The preset and extension together, with the feature artefacts they keep |
| Context | Add | Developer (person) | Runs the standard lifecycle commands, answers clarification requests, approves consequential exceptions and behaviour-altering expectation changes |
| Context | Add | Technical Lead or Reviewer (person) | Installs and removes the packages, reads the evidence at review, runs the compliance check when evaluating |
| Context | Add | Coding Agent (external system) | Carries out the lifecycle stages, runs the check script, and has its tool calls gated. Claude Code in the first release |
| Context | Add | Spec Kit (external system) | Composes the preset into core commands and templates, registers the extension, dispatches the runtime event |
| Context | Add | Project Test Tooling (external system) | The adopting project's own verification commands, executed by the extension |
| Context | Add | Project Quality Controls (external system) | The adopting project's linting, static analysis, security scanning and CI. No relationship with the system: it neither calls them nor is called by them, and they stay in force beside it |
| Containers | Add | Integrated TDD Preset | Markdown, Spec Kit preset. Wraps four core commands and appends to two core templates |
| Containers | Add | Integrated TDD Extension | Python 3 standard library and Markdown, Spec Kit extension. Process rules, evidence template, check script, runtime event handler |
| Containers | Add | Feature Artefacts | Markdown files in git. One feature's `spec.md`, `plan.md`, `tasks.md` and `tdd-evidence.md` |
| Containers | Add | Spec Kit to Integrated TDD Preset | Composes into the core commands and templates. Preset wrap and append |
| Containers | Add | Spec Kit to Integrated TDD Extension | Dispatches the pre tool use event to. Event dispatcher |
| Containers | Add | Coding Agent to Spec Kit | Runs the composed lifecycle commands of. Skill prompt |
| Containers | Add | Coding Agent to Integrated TDD Extension | Reads the rules in, and runs checks and recordings through. File read, shell command |
| Containers | Add | Coding Agent to Feature Artefacts | Writes verification intent and task labels to. File edit |
| Containers | Add | Integrated TDD Preset to Integrated TDD Extension | Directs the agent to the rules and checks in. File path |
| Containers | Add | Integrated TDD Extension to Feature Artefacts | Reads the artefacts from, and appends evidence to. File read and write |
| Containers | Add | Integrated TDD Extension to Project Test Tooling | Executes declared verification commands in. Subprocess |
| ERD | Add | VERIFICATION_COMMAND, VERIFICATION_OBLIGATION, VERIFICATION_EXEMPTION | New entities in `plan.md`, with the relationships shown above |
| ERD | Add | TEST_EXECUTION_RECORD, TDD_EXCEPTION, EXPECTATION_CHANGE, DECISION | New entities in `tdd-evidence.md`, with the relationships shown above |
| ERD | Add | REQUIREMENT, TASK, EXECUTABLE_TEST | Entities owned by Spec Kit or the adopting project, added to the view because the new entities refer to them. TASK gains `obligation_ids` and `no_test_reason` |
