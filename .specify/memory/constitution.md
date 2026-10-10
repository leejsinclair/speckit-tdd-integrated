<!--
Sync Impact Report
==================
Version change: (unratified template) → 1.0.0
Bump rationale: first ratified version; all placeholders replaced.

Modified principles: none (initial adoption)

Added principles:
- I. Integrate, Don't Add
- II. Developers Stay Accountable
- III. Deterministic Checks, Agent Judgement
- IV. Test-First with Real Evidence
- V. Verify Against Current Spec Kit
- VI. Compatible and Removable

Added sections:
- Additional Constraints
- Development Workflow and Quality Gates
- Governance

Removed sections: none

Template note: the resolved template provides five principle slots; six are defined here.

Dependent artefacts: templates and commands read this file at runtime and were not modified.
- specs/001-integrated-tdd/spec.md: consistent with these principles; no change required.

Follow-up TODOs: none
-->

# speckit-tdd-integrated Constitution

## Core Principles

### I. Integrate, Don't Add

Behaviour MUST be delivered inside the existing Spec Kit lifecycle stages
(Constitution → Specify → Clarify → Plan → Tasks → Analyze → Implement) and their existing
artefacts.

- A developer following the standard lifecycle MUST get the extension's behaviour without invoking
  an additional command.
- A new developer-facing command or a new mandatory document MUST NOT be introduced unless the plan
  records why an existing stage or artefact cannot carry it.
- A parallel workflow that duplicates the Spec Kit lifecycle MUST NOT be introduced.

Rationale: the extension describes how the team works. A process that depends on people remembering
extra steps is skipped under pressure, and every added command is something to learn and maintain.

### II. Developers Stay Accountable

Coding agents may perform the work; developers remain responsible for requirements, design,
implementation and review.

- Material ambiguity or contradiction in requirements MUST be raised with a person and MUST NOT be
  resolved silently by the agent.
- Consequential trade-offs and departures from the defined process MUST be decided by a person and
  recorded with a rationale.
- Routine work MUST proceed without approval requests.
- Generated artefacts MUST be written so that a developer who did not take part can understand and
  assess them, and MUST be kept as persistent, reviewable assets.

Rationale: the purpose of the project is to reduce review effort without reducing understanding.
Evidence nobody can assess does not reduce review effort.

### III. Deterministic Checks, Agent Judgement

A condition that can be verified objectively MUST be verified by a repeatable check that gives the
same result each time it is run on the same input.

- Agent judgement is reserved for interpreting requirements, choosing appropriate verification and
  handling exceptions.
- An agent's statement that a condition holds MUST NOT stand in for a check that could have been
  run.
- A failed check MUST block the work it guards until the condition is met or an exception is
  recorded. It MUST NOT be downgraded to a note.

Rationale: an agent that grades its own compliance provides no independent evidence.

### IV. Test-First with Real Evidence

This project MUST be built the way it asks adopting projects to build.

- For executable components such as scripts and checks, a test MUST be written and seen to fail for
  the intended reason before the behaviour is implemented, then seen to pass.
- Every reported test result MUST come from an actual execution.
- A test MUST NOT be removed, weakened, skipped or bypassed solely to obtain a pass.
- Where test-first development is impractical, the reason and the alternative verification MUST be
  recorded.

Rationale: an extension that enforces test-driven development and was not itself built that way
has no credibility and no evidence that its own checks work.

### V. Verify Against Current Spec Kit

Design and implementation decisions MUST be based on the current Spec Kit source, documentation and
extension infrastructure.

- Manifest schemas, supported artefact types, hook points and installation commands MUST be
  confirmed against the current Spec Kit repository before a design relies on them.
- Implementation detail MUST NOT be fixed in a specification before that examination has been done.
- A capability taken from another extension, a tutorial or prior knowledge MUST be treated as
  unverified until confirmed.

Rationale: Spec Kit's customisation mechanisms change. Designs built on remembered behaviour fail
at installation, which is the most expensive point to discover the error.

### VI. Compatible and Removable

Installing or removing the extension MUST leave existing Spec Kit commands, artefacts and other
installed extensions working.

- Any change to existing workflow behaviour MUST be justified and explicitly documented.
- The adopting project's own test tooling, verification commands, linting, static analysis, security
  scanning and CI MUST remain in force and MUST NOT be replaced, weakened or duplicated.
- A particular language or test framework MUST NOT be required of an adopting project.

Rationale: the extension is used by the author's team and published for others. It is adopted into
projects that already have their own controls, and it has to fit them.

## Additional Constraints

- **Delivery**: the project is delivered through Spec Kit's standard customisation mechanisms
  (extensions, presets, workflows, bundles). The mechanism for each piece of behaviour is chosen in
  planning under Principle V.
- **Audience**: the author's team is the primary user. Where the team's way of working and general
  configurability conflict, the team's way of working takes precedence.
- **Coding agents**: Claude Code is the first supported agent. Process rules and checks MUST be
  defined independently of any one agent so that others can be added without changing them.
- **Proportion**: the effort a process step demands MUST be proportionate to the scope, risk and
  complexity of the change it applies to.
- **No duplication**: information already held by Spec Kit or by the adopting project's tooling
  MUST NOT be copied into new artefacts.

## Development Workflow and Quality Gates

Work on this project follows the Spec Kit lifecycle. A feature's plan MUST include a Constitution
Check against the principles above, and any departure MUST be recorded there with its
justification.

Every customisation MUST be tested at four levels before it is treated as complete:

1. **Structural validation**: manifests, file paths, required files and identifiers are valid.
2. **Installation and registration**: components install, and commands and templates become
   available.
3. **Behavioural testing**: commands are run against representative inputs and the generated
   artefacts are assessed against explicit acceptance criteria.
4. **Regression testing**: other components, existing workflows and removal of the component
   continue to work.

Successful installation MUST NOT be taken as evidence that an agent-driven command behaves
correctly. Behavioural tests MUST assess output quality, requirements traceability, handling of
ambiguity and preservation of developer intent.

A customisation MUST be validated on its own before it is combined with others into a team-wide
process.

## Governance

This constitution takes precedence over other practices in this repository. Where a specification,
plan or task conflicts with it, the constitution prevails until it is amended.

- **Amendment**: a change is proposed as an edit to this file together with the reason for it, and
  takes effect when the project maintainer approves it. An amendment that alters or removes a
  principle MUST state what existing specifications, plans and artefacts need to change as a
  result.
- **Versioning**: this document uses semantic versioning. MAJOR for removing or redefining a
  principle in an incompatible way; MINOR for adding a principle or section, or materially
  expanding guidance; PATCH for clarification and wording.
- **Compliance**: every plan MUST pass its Constitution Check before implementation begins, and
  review of completed work MUST confirm that the principles were followed. A departure is
  acceptable only when it is recorded with a justification and approved by a person.

**Version**: 1.0.0 | **Ratified**: 2026-10-10 | **Last Amended**: 2026-10-10
