---
description: Execute the implementation planning workflow using the plan template to generate design artifacts, including C4 component, sequence and ER diagrams.
strategy: wrap
handoffs:
  - label: Create Tasks
    agent: speckit.tasks
    prompt: Break the plan into tasks
    send: true
  - label: Create Checklist
    agent: speckit.checklist
    prompt: Create a checklist for the following domain...
---

<!-- markdownlint-disable-file MD041 -->

> **C4 Model preset: additional Phase 1 deliverable.** This planning run must also
> produce the feature's architecture document, `architecture.md`, as described in
> "C4 Architecture Diagrams" at the end of this command. It is a Phase 1 output
> alongside `data-model.md`, `contracts/` and `quickstart.md`: generate it before
> the post-design Constitution Check, the post-execution hooks and the Completion
> Report, and treat the command as incomplete without it.

{CORE_TEMPLATE}

## C4 Architecture Diagrams

This section adds a step to **Phase 1: Design & Contracts**. Run it after
`data-model.md` and `contracts/` are written, because the diagrams are derived from
them.

**Locations.** Read `.specify/extensions/c4/c4-config.yml` if it exists; otherwise
use `architecture_dir: docs/architecture`, `feature_file: architecture.md` and
`mermaid_cli: mmdc`.
`ARCH_DIR` is `architecture_dir` from the repository root. `FEATURE_ARCH` is
`<feature_file>` in the feature directory, next to IMPL_PLAN.

**If `.specify/extensions/c4/templates/` does not exist**, the `c4` extension is not
installed. Skip this section, leave the plan's `## Architecture` section as
`Not generated: c4 extension not installed`, and say so in the Completion Report.

1. **Read the rules**: read `.specify/extensions/c4/templates/c4-conventions.md` in
   full. Every diagram must follow it.

2. **Load the system views**: read `ARCH_DIR/context.md`, `ARCH_DIR/containers.md`
   and `ARCH_DIR/erd.md` when they exist and reuse their element aliases, labels and
   technologies exactly. If they do not exist, treat every container and entity as
   new.

3. **Generate `FEATURE_ARCH`** from
   `.specify/extensions/c4/templates/c4-feature-architecture-template.md`:
   - **Header**: feature name, branch, date, and relative links to the spec, plan,
     data model, contracts and the three system views. Drop links to artifacts this
     run did not produce.
   - **Components**: one `C4Component` diagram and component table per container
     this feature adds or changes, consistent with Technical Context and the source
     tree in Project Structure. Choose each diagram's declaration order with the
     "Layout optimisation" procedure in the conventions, using
     `python3 .specify/extensions/c4/scripts/python/c4_layout.py optimise` with
     `--mmdc "<mermaid_cli>"`.
   - **Flows**: one `sequenceDiagram` per user story's primary path, in priority
     order, plus architecturally significant alternate or failure paths. Message
     labels match `contracts/`. Name the user story and the requirements covered.
   - **Data**: one `erDiagram` with every entity in `data-model.md`, with
     attributes, keys and relationships. Write `Not applicable: [reason]` if the
     feature has no persistent data.
   - **Architecture Impact**: every difference between these diagrams and the system
     views.
   - Leave no placeholder text and none of the template's example content.

4. **Fill the plan's `## Architecture` section** in IMPL_PLAN: correct relative
   links and a one-line impact per view.

5. **Fill the spec's `## System Context` section** in FEATURE_SPEC only if it still
   contains unfilled placeholders: set the link to `ARCH_DIR/context.md` and list
   the people and external systems from the spec. Make no other change to the spec.

6. **Extend the outputs**:
   - Add `architecture.md` to the documentation tree under "Project Structure" in
     IMPL_PLAN, as a Phase 1 output.
   - Include `FEATURE_ARCH` among the generated artifacts in the Completion Report,
     with the count of component, sequence and ER diagrams and, per component
     diagram, whether its layout was rendered and already sufficient, rendered and
     optimised, or not checked.

Do not edit the project-level views in `ARCH_DIR` during planning. They are updated
from the Architecture Impact table by `__SPECKIT_COMMAND_C4_SYSTEM__` once the
feature is implemented.
