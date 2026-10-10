---
description: "Generate a feature's C4 component diagrams, sequence diagrams and ER diagram in architecture.md"
---

# Generate Feature Architecture Diagrams

Write the architecture document for the current feature: C4 component views for the
containers it touches, a sequence diagram per flow, an ER diagram of its data, and
the list of changes it makes to the project-level views.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). It may narrow
the scope (for example "only the sequence diagrams") or name extra flows to cover.

## Prerequisites

1. Run the prerequisites script from the repository root and parse `FEATURE_DIR`,
   `FEATURE_SPEC` and `IMPL_PLAN` from its JSON output:
   - **Bash**: `.specify/scripts/bash/check-prerequisites.sh --json --paths-only`
   - **PowerShell**: `.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly`
2. If `FEATURE_SPEC` does not exist, stop and tell the user to run
   `__SPECKIT_COMMAND_SPECIFY__` first.
3. If `IMPL_PLAN` does not exist, stop and tell the user to run
   `__SPECKIT_COMMAND_PLAN__` first. Component and ER diagrams need the technical
   decisions recorded there.

## Configuration

Read `.specify/extensions/c4/c4-config.yml` if it exists. Use these defaults for any
key that is missing or when the file is absent:

- `architecture_dir`: `docs/architecture`
- `feature_file`: `architecture.md`
- `mermaid_cli`: `mmdc`

Below, `ARCH_DIR` is `architecture_dir` resolved from the repository root and
`FEATURE_ARCH` is `FEATURE_DIR/<feature_file>`.

## Steps

1. **Read the rules.** Read `templates/c4-conventions.md` in full. Every diagram you
   write must follow it.

2. **Load the feature.** Read `FEATURE_SPEC` and `IMPL_PLAN`. Read these from
   `FEATURE_DIR` when they exist: `research.md`, `data-model.md`, `quickstart.md`
   and every file under `contracts/`.

3. **Load the system views.** Read `ARCH_DIR/context.md`, `ARCH_DIR/containers.md`
   and `ARCH_DIR/erd.md` when they exist. Reuse their element aliases, labels and
   technologies exactly. If none exist, continue: treat every container and entity
   as new, and say in the final report that `__SPECKIT_COMMAND_C4_SYSTEM__` has not
   been run yet.

4. **Start from the template.** If `FEATURE_ARCH` does not exist, create it from
   `templates/c4-feature-architecture-template.md`. If it exists, update it in place
   and keep any content that is not an unfilled placeholder.

5. **Fill the header.** Set the feature name, branch and date. Write the system view
   links as relative paths from `FEATURE_DIR` to `ARCH_DIR`. Remove the link to
   `data-model.md` or `contracts/` if that artifact does not exist.

6. **Components.** Identify each container this feature adds or changes, from the
   plan's Technical Context and Project Structure. For each one write a subsection
   with one `C4Component` diagram and its component table. Show the components the
   feature touches and the neighbours they call; mark each component New, Changed or
   Existing, and give its source location from the plan's source tree. Once a
   diagram's content is complete, choose its declaration order with the "Layout
   optimisation" procedure in the conventions, using
   `python3 scripts/python/c4_layout.py optimise` with `--mmdc "<mermaid_cli>"`. Do not
   change boundary membership or relationships.

7. **Flows.** Write one `sequenceDiagram` per user story's primary path, in priority
   order. Add an alternate or failure flow where the spec's edge cases or the
   contracts make it architecturally significant. Message labels must match the
   operations in `contracts/`. Fill **Covers** with the functional requirement ids
   and acceptance scenarios the flow realises.

8. **Data.** If `data-model.md` exists, write one `erDiagram` containing every entity
   in it, with all attributes, keys and relationships, plus any existing entity they
   reference (keys only). Fill the entity table. If the feature has no persistent
   data, replace the section body with `Not applicable: [reason]`.

9. **Architecture Impact.** Compare what you drew with the system views and list
   every difference: new people or external systems (Context), new or changed
   containers and container relationships (Containers), new or changed entities,
   attributes and relationships (ERD). One row with `None` for an unaffected view.

10. **Link from the plan.** Make sure `IMPL_PLAN` has an `## Architecture` section
    that links to `FEATURE_ARCH` and the three system views with relative paths and
    summarises the Architecture Impact in one or two sentences. Add the section at
    the end of the file if it is missing; fill it in if it holds placeholders.

11. **Self-check.** Re-read `FEATURE_ARCH` against the conventions: no placeholder
    text or template examples left, every Mermaid block starts with its diagram type,
    every sequence participant exists in a C4 view, every `FK` has a relationship.

## Report

Tell the user the path of `FEATURE_ARCH`, how many component, sequence and ER
diagrams it contains, the Architecture Impact rows that are not `None`, and anything
you could not determine from the feature documents. For each component diagram, say
whether its layout was rendered and already sufficient, rendered and optimised (how
many candidates, which order was chosen), or not checked. Suggest
`__SPECKIT_COMMAND_C4_VALIDATE__` as the next step.
