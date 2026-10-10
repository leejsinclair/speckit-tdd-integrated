---
description: "Create or update the project-level C4 context view, container view and ER diagram"
---

# Update System Architecture Views

Maintain the living, project-level architecture documents: the C4 system context,
the C4 container view and the whole-system ER diagram.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). It may name a
feature to merge, restrict the update to one view, or describe the system when
nothing can be derived yet.

## Configuration

Read `.specify/extensions/c4/c4-config.yml` if it exists. Use these defaults for any
key that is missing or when the file is absent:

- `architecture_dir`: `docs/architecture`
- `feature_file`: `architecture.md`
- `mermaid_cli`: `mmdc`

Below, `ARCH_DIR` is `architecture_dir` resolved from the repository root.

## Steps

1. **Read the rules.** Read `templates/c4-conventions.md` in full. Every diagram you
   write must follow it.

2. **Decide the mode.**
   - **Bootstrap**: none of `ARCH_DIR/context.md`, `ARCH_DIR/containers.md`,
     `ARCH_DIR/erd.md` exist.
   - **Merge**: at least one exists.

3. **Find the feature to merge, if any.** Run the prerequisites script from the
   repository root and parse `FEATURE_DIR`:
   - **Bash**: `.specify/scripts/bash/check-prerequisites.sh --json --paths-only`
   - **PowerShell**: `.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly`

   If the user input names a different feature, use that feature's directory
   instead. If the script fails or there is no current feature, continue without
   one.

4. **Gather evidence.**
   - **Bootstrap**: read `.specify/memory/constitution.md`, the project README, and
     for every feature directory under `specs/` its `spec.md`, `plan.md`,
     `data-model.md` and architecture document. Inspect the repository's top-level
     source layout, deployment and infrastructure files, and database schema or
     migration files to confirm which containers and entities actually exist.
   - **Merge**: read the existing views, then the feature's architecture document
     (`FEATURE_DIR/<feature_file>`) and its **Architecture Impact** table. If the
     feature has no architecture document, derive the changes from its `plan.md`
     and `data-model.md`. If there is no feature at all, re-check the views against
     the repository and correct drift.

5. **Write `ARCH_DIR/context.md`.** Create from
   `templates/c4-context-template.md` or update in place. The system is one box.
   Include every person and external system the evidence supports, and nothing it
   does not.

6. **Write `ARCH_DIR/containers.md`.** Create from
   `templates/c4-container-template.md` or update in place. People and external
   systems must match `context.md` exactly. Fill the container and communication
   tables. In the container table's "Component views" column, link to each feature
   architecture document that details that container.

7. **Write `ARCH_DIR/erd.md`.** Create from `templates/c4-erd-template.md` or update
   in place, with one section and diagram per database container. If the system has
   no persistent data, write the file with the header and
   `Not applicable: [reason]`.

8. **Preserve and record.**
   - Edit existing files in place. Keep hand-written prose and existing aliases;
     treat existing declaration order as the baseline.
   - For the context and container diagrams, follow the "Layout optimisation"
     procedure in the conventions, using `python3 scripts/python/c4_layout.py optimise`
     with `--mmdc "<mermaid_cli>"`. Retain the baseline when it is already
     sufficient or the rendered result is not clearer. Do not move elements between
     groups or boundaries.
   - Never remove an element only because the current feature does not mention it.
     Remove an element when the Architecture Impact table says `Remove` or the
     repository shows it is gone.
   - Update "Last updated" and "Updated for" in each file you change, and add a
     Change Log row to `containers.md` and `erd.md` describing the change.

9. **Self-check.** Re-read the three files against the conventions: no placeholder
   text or template examples left, context and container views agree on people and
   external systems, every database container in `containers.md` has a section in
   `erd.md`.

## Report

List the files created or changed and, per file, the elements added, changed and
removed. For the context and container diagrams, say whether the layout was rendered
and already sufficient, rendered and optimised (how many candidates, which order was
chosen), or not checked. State anything you inferred without direct evidence so the user can confirm
it. If you could not determine the system's containers at all, say so and ask the
user to describe them rather than inventing them.
