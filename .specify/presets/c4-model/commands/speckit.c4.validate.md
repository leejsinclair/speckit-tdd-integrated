---
description: "Check architecture diagrams for Mermaid syntax, C4 rule and consistency problems without changing files"
---

# Validate Architecture Diagrams

Check the current feature's architecture document and the project-level views
against the C4 conventions and against the documents they are derived from.

**This command is read-only. Do not create or modify any project file.** Report
findings and let the user decide what to fix.

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). It may limit
the check to the feature or to the project-level views.

## Configuration

Read `.specify/extensions/c4/c4-config.yml` if it exists. Use these defaults for any
key that is missing or when the file is absent:

- `architecture_dir`: `docs/architecture`
- `feature_file`: `architecture.md`
- `mermaid_cli`: `mmdc`

## Steps

1. **Read the rules.** Read `templates/c4-conventions.md` in full.

2. **Locate the documents.** Run the prerequisites script from the repository root
   and parse `FEATURE_DIR`, `FEATURE_SPEC` and `IMPL_PLAN`:
   - **Bash**: `.specify/scripts/bash/check-prerequisites.sh --json --paths-only`
   - **PowerShell**: `.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly`

   The documents to check are `FEATURE_DIR/<feature_file>` and `context.md`,
   `containers.md` and `erd.md` under `architecture_dir`. Check the ones that
   exist. If none exist, report that there is nothing to validate, name the command
   that creates each (`__SPECKIT_COMMAND_C4_FEATURE__`,
   `__SPECKIT_COMMAND_C4_SYSTEM__`), and stop.

3. **Syntax.** For every Mermaid block in those documents:
   - If the `mermaid_cli` command is available, extract each block to a temporary
     file outside the repository and run `<mermaid_cli> -i <file> -o <file>.svg`. A
     non-zero exit is a syntax finding; quote the parser message.
   - Otherwise review the block by hand: it starts with a valid diagram type, every
     macro and arrow is in the allowed subset from the conventions, brackets and
     quotes balance, and every alias used in a relationship is declared. State in
     the report that syntax was reviewed manually, not parsed.

4. **Rendered readability.** When the C4 diagrams were rendered in step 3, measure
   them with `python3 scripts/python/c4_layout.py score <file>.svg ...` and inspect the
   renderings as well as the source. Report an **INFO** finding, quoting the counts,
   when a relationship crosses an unrelated element or label, labels overlap,
   relationship lines cross or coincide, or routes are unnecessarily long. Label
   overlap counts are estimates: confirm every finding in the rendering. Syntax
   validity alone does not establish readability. If rendering or Python is
   unavailable, say that layout was not measured or not visually checked. This
   step only reads and writes temporary files outside the repository.

5. **C4 rules.** Check each C4 diagram against the conventions:
   - one level per diagram, and one container per component diagram;
   - every container and component has a technology and a description;
   - every relationship has a label, and a protocol between containers;
   - no element without a relationship;
   - no leftover template placeholders (`[SYSTEM NAME]`, `[Component 1]`) or
     template example content.

6. **Consistency across views.**
   - People and external systems in `containers.md` match `context.md`.
   - Every container boundary in a feature component diagram is a container in
     `containers.md`, or is listed as `Add` in the feature's Architecture Impact
     table.
   - An element has the same alias, label and technology everywhere it appears.
   - Every database container has a section in `erd.md`.

7. **Consistency with the feature documents.**
   - Every sequence participant is an element in a C4 view.
   - Every user story in `FEATURE_SPEC` has at least one sequence diagram, and each
     diagram names the story it covers.
   - Sequence message labels correspond to operations in `contracts/`.
   - The feature ER diagram contains every entity in `data-model.md`, with matching
     attributes and relationships, and nothing that `data-model.md` lacks.
   - Every `FK` attribute has a relationship line and the reverse.
   - Technologies match `IMPL_PLAN` Technical Context.
   - The Architecture Impact table accounts for every difference between the
     feature diagrams and the project-level views.

8. **Links.** `FEATURE_SPEC` and `IMPL_PLAN` link to the architecture documents, the
   feature architecture document links back to them, and every relative link
   resolves to a file that exists.

## Report

Output a findings table, most severe first:

| ID | Severity | Document | Diagram or section | Finding | Suggested fix |
|----|----------|----------|--------------------|---------|---------------|

Severity levels:

- **ERROR**: the diagram will not render, or it contradicts the spec, plan, data
  model or contracts.
- **WARNING**: a C4 convention is broken or two views disagree.
- **INFO**: readability or completeness suggestion.

Follow the table with the count per severity, the documents checked, and whether
syntax was parsed with the Mermaid CLI or reviewed manually, and whether layout was
measured. If there are no findings, say
so plainly. If there are findings, offer to fix them with
`__SPECKIT_COMMAND_C4_FEATURE__` or `__SPECKIT_COMMAND_C4_SYSTEM__`; do not apply
fixes from this command.
