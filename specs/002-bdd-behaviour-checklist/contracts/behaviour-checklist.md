# Contract: the behaviour checklist

**Feature**: `002-bdd-behaviour-checklist` | **Data model**: [data-model.md](../data-model.md)

The behaviour checklist is `tests/behaviour-checklist.md` in the feature directory. The
coding agent writes it during the plan stage; the check script reads it and never writes
it. This contract fixes what the script reads. Everything outside the elements below
(prose, comments, blank lines) is ignored by the script and may be used for the reader.

## 1. The template

Shipped by the extension as `templates/behaviour-checklist-template.md` and installed at
`.specify/extensions/integrated-tdd/templates/behaviour-checklist-template.md`. The plan
stage copies it, replaces `<feature directory name>`, and replaces the example sections.

```markdown
# Behaviour Checklist: <feature directory name>

<!--
  Written by the plan stage from spec.md and the Verification Plan in plan.md, before
  tasks and implementation. Read by tdd_check.py; the rules are in the "Behaviour
  checklist" section of tdd-process-rules.md.
  - One "## USn-ASm" section per acceptance scenario of spec.md, in order, opening with
    the scenario's text from spec.md as a block quote, word for word.
  - One "## Other behaviours" section, when needed, for items that refine no scenario.
  - Items state what can be observed from outside: what a user sees or can do, what a
    caller receives, what is stored and can be read back, what is refused. They name no
    file, module, function, class, table, endpoint or screen component.
  - No checkboxes and no status: what is verified is derived from tdd-evidence.md.
-->

**Specification**: [spec.md](../spec.md) | **Verification Plan**: [plan.md](../plan.md#verification-plan) | **Tasks**: [tasks.md](../tasks.md)

## US1-AS1

> **Given** [the scenario's context, copied from spec.md], **When** [its action], **Then** [its outcome]

- **BI-001** Expresses: FR-001, US1-AS1. Verified by: VO-001.
  - **Given** [the context, in the specification's terms, with concrete values]
  - **When** [the action]
  - **Then** [an observable outcome]
  - **And** [a further outcome of the same action]

## Other behaviours

- **BI-002** Expresses: FR-002, EC-01. Verified by: VO-002.
  - **Given** [the context]
  - **When** [the action]
  - **Then** [the observable outcome]
```

## 2. Elements the script reads

Lines inside fenced code blocks are ignored, as in `tasks.md`.

| Element | Pattern | Notes |
|---------|---------|-------|
| Scenario section | A line `## USn-ASm`, optionally followed by text after a colon, for example `## US1-AS1: empty cart` | The id is the part before the colon |
| Other behaviours section | The line `## Other behaviours` | At most once, after every scenario section |
| Scenario quote | The consecutive lines starting with `>` that follow a scenario section heading, with blank lines allowed between the heading and the quote | Required in every scenario section, before its first item |
| Item line | `- **BI-nnn** Expresses: <ids>. Verified by: <links>.` at the start of a line | `nnn` is three or more digits. The two labels are fixed and in this order; each list ends at the next `.` followed by a space or the end of the line |
| Clause line | An indented list entry `- **Given** <text>`, `- **When** <text>`, `- **Then** <text>` or `- **And** <text>`, below an item line | Belongs to the nearest item line above it |
| Verified-by link | `VO-nnn`, or `exemption <requirement id>` | Comma-separated |
| Other `##` headings | Any other second-level heading | A finding (B4): every item belongs to a recognised section |

## 3. Normalisation

Used to compare a quote with the specification (B6) and to fingerprint an item's clauses:

1. Remove a leading `>` and the space after it, and a leading list number such as `1.` and the
   space after it on the specification side.
2. Remove `**` and `__`.
3. Replace every run of white space, including line breaks, with one space, and trim.

Nothing else changes: case, punctuation and wording are compared as written.

## 4. Rules

Each finding is printed as `<rule id> <subject>: <reason>`, as for every other check.

| Rule | Subject | Fails when |
|------|---------|-----------|
| `CHECKLIST` | `tests/behaviour-checklist.md` | The rules apply to the feature and the file does not exist or cannot be read |
| B1 | The `FR-` or `USn-ASm` id | An `FR-` requirement or acceptance scenario of `spec.md` is in no item's Expresses list |
| B2 | The item id | The Verified by list is empty; it names a `VO-` id not in the Verification obligations table; or it names `exemption <id>` where `<id>` is not a row of the Verification exemptions table |
| B3 | The `VO-` id | An obligation in the Verification obligations table is in no item's Verified by list |
| B4 | The item id, or the line number | The id does not match `BI-` and three or more digits, or is used twice; the Expresses list is empty; Given, When or Then is missing, repeated, or out of order (an And clause may follow any of them); an item line is outside a section; a heading is not a recognised section; a scenario section has no items; or the file holds a task-list checkbox (`- [ ]`, `- [x]`) or a line starting `Status:` or `**Status**` |
| B5 | The item id | A clause holds a path-shaped token that is not in `spec.md`, or a code-shaped token that is in `plan.md` or `tasks.md` and not in `spec.md` (section 5) |
| B6 | The item id, or the scenario id | An Expresses id with an `FR-`, `SC-` or `USn-ASm` prefix is not in `spec.md`; an `EC-` id does not occur in `spec.md` as a whole word, compared case-sensitively; an Expresses id has any other prefix than those and `EC-`; a scenario section names a scenario that is not in `spec.md` or appears twice; a scenario section's quote is missing or, normalised, differs from the scenario's normalised text; an item in a scenario section does not name that scenario, or names another scenario; an item in Other behaviours names a scenario |
| B7 | The task id | A `test` task names only obligations that no item names. Reported by `tasks` |

B1 to B6 are reported by `plan`; B7 by `tasks`. Both still report their 001 findings
first, in the same form.

## 5. Tokens for B5

A clause's text is split on white space; leading and trailing punctuation other than `/`,
`_`, `(` and `)` is removed from each token, and backticks are noted and then removed.

| Shape | A token is this shape when it |
|-------|-------------------------------|
| Path-shaped | contains `/` with a non-space character on both sides, or ends in `.` and one of: `c cc cpp cs css go h html java js json jsx kt md php py rb rs scss sh sql swift toml ts tsx vue xml yaml yml` |
| Code-shaped | contains `_`, `::` or `->`; ends in `()`; starts with a lower-case letter and contains an upper-case letter (lower camel case); or was written in backticks |

"In `spec.md`", "in `plan.md`" and "in `tasks.md`" mean the token occurs in that file's
text as a whole word, compared case-sensitively.

Examples, for a specification that never mentions them:

| Clause text | Finding |
|-------------|---------|
| `**Then** src/cart.py returns 0` | B5: `src/cart.py` is path-shaped |
| `**When** cart_total() is called` | B5, when `cart_total()` appears in the plan or task list |
| `**When** the shopper asks for the total` | None |
| `**Then** tasks.md is unchanged`, in a specification that names `tasks.md` | None: the file is part of the boundary the specification describes |

## 6. What the format does not check

These are rules for the agent and for the reviewer, stated in the process rules, and not
decided by the script (spec Assumptions):

- that an item keeps its scenario's wording as closely as its added detail allows, and that
  together a scenario's items state every outcome it states, none weaker (FR-016);
- that no two items describe the same behaviour (FR-015);
- that an item introduces no behaviour the specification does not state (FR-013), beyond
  what B1, B2, B3 and B6 catch;
- implementation wording that B5's token shapes do not catch.
