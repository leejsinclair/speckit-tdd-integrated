# C4 Diagram Conventions

Rules for every diagram this extension produces. Read this file before writing or
checking any diagram.

## Levels

| Level | Diagram | Mermaid type | Shows | Lives in |
|-------|---------|--------------|-------|----------|
| 1 | System context | `C4Context` | The system as one box, the people who use it, the external systems it talks to | Project: `context.md` |
| 2 | Container | `C4Container` | Deployable/runnable units inside the system (apps, services, databases, queues) | Project: `containers.md` |
| 3 | Component | `C4Component` | Major building blocks inside ONE container | Feature: `architecture.md` |
| - | Sequence | `sequenceDiagram` | One flow through containers or components over time | Feature: `architecture.md` |
| - | Entity relationship | `erDiagram` | Persistent entities, attributes, keys, relationships | Project: `erd.md`; Feature: `architecture.md` |

C4 level 4 (code) is not produced. The source code is the level 4 view.

## C4 rules

- **One level per diagram.** A context diagram never shows containers; a container
  diagram never shows components. Zoom in with a new diagram instead.
- **One container per component diagram.** Neighbouring containers and external
  systems appear only as context around the boundary (`Container`, `ContainerDb`,
  `System_Ext` outside the `Container_Boundary`).
- **Names are stable identifiers.** An element has the same alias and the same label
  in every diagram and document it appears in. Aliases are `lowerCamelCase`
  (`orderApi`, `ordersDb`); labels are the human name (`"Order API"`).
- **Every container and component states its technology** in the technology
  argument (`"TypeScript, Fastify"`, `"PostgreSQL 16"`). Use the choices recorded in
  `plan.md` Technical Context. Write `"TBD"` rather than guessing.
- **Every element has a one-line description** of its responsibility, not its
  implementation.
- **Every relationship is labelled** with a verb phrase in the direction of the arrow
  (`"Places orders using"`, `"Reads from and writes to"`) and, between containers or
  components, the protocol or mechanism (`"JSON/HTTPS"`, `"SQL/TCP"`, `"AMQP"`).
- **Relationships point from the initiator to the target**, not in the direction of
  data flow.
- **No orphans.** Every element takes part in at least one relationship.
- **A database is a container**, not a component. Tables belong in the ER diagram.
- **Keep it readable.** If a diagram passes roughly 15 elements, split it (per
  bounded context, or per container for component views).

## Mermaid C4 syntax

Mermaid's C4 support is marked experimental. Use only this subset, which is stable
across renderers including GitHub:

```text
Person(alias, "Label", "Description")
Person_Ext(alias, "Label", "Description")
System(alias, "Label", "Description")
System_Ext(alias, "Label", "Description")
SystemDb_Ext(alias, "Label", "Description")
System_Boundary(alias, "Label") { ... }
Container(alias, "Label", "Technology", "Description")
ContainerDb(alias, "Label", "Technology", "Description")
ContainerQueue(alias, "Label", "Technology", "Description")
Container_Ext(alias, "Label", "Technology", "Description")
Container_Boundary(alias, "Label") { ... }
Component(alias, "Label", "Technology", "Description")
Rel(from, to, "Label")
Rel(from, to, "Label", "Technology")
BiRel(a, b, "Label")
UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

- Start each diagram with its type keyword, then a `title` line.
- Do not use sprites, tags, `AddElementTag`, links, or `UpdateElementStyle`.
- Do not put double quotes, parentheses or commas inside a label or description.
- Layout follows declaration order. Declare people first, then the system or
  boundary, then external systems, then all `Rel` lines.
- Within each peer group and boundary, put the most connected element near its
  directly connected elements; keep branch dependencies close to their caller.
  Avoid alphabetical ordering when it separates related elements.
- Treat declaration order as a presentation choice, not an architecture change.
  Keep elements in their existing peer groups and boundaries, and preserve the
  existing order unless a rendered comparison shows a readability improvement.
- Mermaid C4 layout is experimental. Check proposed ordering in the renderer used
  by the project; do not assume a valid diagram or a layout directive improves it.
  `UpdateLayoutConfig` row settings can be renderer-version dependent.
- Choose the declaration order with the procedure in "Layout optimisation" below.

## Layout optimisation

Mermaid places C4 elements in declaration order, so the order of element lines is
the only layout control. Treat it as something to measure, not predict. Apply this
procedure to each C4 diagram after its content is correct. It never changes what the
diagram says: only whole element lines move, and only within their peer group
(people, the elements of one boundary, external systems).

The helper `.specify/extensions/c4/scripts/python/c4_layout.py` (Python 3, standard library
only) does the mechanical steps. `MERMAID_CLI` is `mermaid_cli` from
`.specify/extensions/c4/c4-config.yml`, default `mmdc`. Write its output to a
temporary directory outside the repository.

```text
python3 .specify/extensions/c4/scripts/python/c4_layout.py optimise <file.md> --block <n> --out <tmp-dir> --mmdc "<MERMAID_CLI>"
python3 .specify/extensions/c4/scripts/python/c4_layout.py check <before> <after>
```

`--block <n>` is the position of the diagram among the C4 blocks in the file.

1. **Check the diagram as written first.** Run `optimise`. It renders and measures
   the existing order before anything else. If the result has
   `"baseline_sufficient": true`, open the one image it lists. If the image is
   readable, stop: keep the order and report the layout as rendered and sufficient.
   If you see a defect the measurements miss (an awkward bend, a label that could
   belong to two lines), run `optimise` again with `--force`.
2. **Compare candidates.** Otherwise `optimise` writes up to five orderings
   (`baseline`, `connected`, `primary-path`, `reversed-peers`, `rows`), renders each
   and ranks them by penalty score, lowest first:

   | Defect | Penalty |
   |--------|--------:|
   | Crossing between two relationship lines (`X`) | 5 |
   | Line through an unrelated element (`N`) | 6 |
   | Relationship label over an unrelated element, label or boundary title (`O`) | 6 |
   | Line through an unrelated relationship label (`T`) | 2 |
   | Line longer than three element widths (`long`) | 2 |
   | Canvas more than 1.5 times the baseline area | 3 |

   Label sizes are estimated, so `O` and `T` are approximate. A candidate marked
   `same_geometry_as_baseline` had no effect in this renderer; discard it.
3. **Look at the images.** Open the baseline and selected images that `optimise`
   lists. Confirm the counted defects are real and that the primary flow reads in
   one direction. The score ranks candidates; the image decides. Keep the baseline
   when the selected candidate is not clearly easier to read.
4. **Refine at most twice.** If one defect dominates the selected candidate, move
   the element that causes it within its peer group, save the result as a new file
   and run `optimise` on it. Stop when a change gains little.
5. **Apply and prove fidelity.** Copy the chosen order into the document, then run
   `check` with the original and the edited file. It must report the same elements,
   boundaries and relationships. Never remove, reverse or add a relationship to
   improve a layout.
6. **Know when ordering cannot help.** If every candidate still has several lines
   through unrelated elements, the diagram shows too much. Split it as "Keep it
   readable" describes and say so in the report.
7. **Report honestly.** For each C4 diagram state one of: rendered and already
   sufficient; rendered, with the number of candidates compared and the order
   chosen; or not checked. If `optimise` reports `"measured": false`, or Python is
   not available, nothing was rendered: follow the ordering rules above, keep any
   existing order, and report the layout as not checked.

## Sequence diagram rules

- One diagram per flow. A flow is one user story's primary path, or a significant
  alternate or failure path. Name the user story in the heading above the diagram.
- **Participants are elements that exist in the C4 views.** Use the same labels.
  People are `actor`; containers, components and external systems are `participant`.
  Declare them explicitly, in left-to-right order of first use.
- Pick one level of abstraction per diagram: container-level for flows that cross
  containers, component-level for flows inside one container.
- `->>` for a synchronous call, `-->>` for its response, `-)` for an asynchronous
  message or event.
- Label every message with what is asked or returned (`POST /orders`,
  `201 Created + orderId`, `OrderPlaced event`), consistent with `contracts/`.
- Use `alt` / `else` for branches, `opt` for optional steps, `loop` for repetition,
  `par` for concurrency. Show the error path that matters, not every error.
- Use `autonumber` so steps can be referenced from prose and tasks.

## ER diagram rules

- Entity names are `UPPER_SNAKE_CASE` singular nouns (`ORDER`, `ORDER_LINE`) and map
  one-to-one to the entities in `data-model.md`.
- Each attribute is `type name` plus a key marker where it applies: `PK`, `FK`, `UK`.
  Add a quoted comment for constraints worth seeing (`"not null"`, `"ISO 4217"`).
- Use logical types (`uuid`, `string`, `int`, `decimal`, `boolean`, `datetime`,
  `json`) unless `plan.md` fixes a database, in which case use its types.
- Every relationship states cardinality on both ends and a verb label:

  ```text
  ||--||   exactly one to exactly one
  ||--o{   one to zero or more
  ||--|{   one to one or more
  }o--o{   many to many (resolve with a join entity when it carries attributes)
  ```

- Identifying relationships (child cannot exist without parent) use a solid line
  `--`; non-identifying relationships use a dashed line `..`.
- Every `FK` attribute has a matching relationship line, and every relationship has
  its `FK` attribute on the many side.
- Purely in-memory or transient objects do not belong in the ER diagram.

## Cross-references

- Links between documents are relative paths, so they work on GitHub and in editors.
- A feature's `architecture.md` links to its `spec.md`, `plan.md` and
  `data-model.md`, and to the project-level `context.md`, `containers.md` and
  `erd.md`.
- A new or changed element in a feature diagram is listed in that file's
  **Architecture Impact** table, which is the input for updating the project-level
  views.
