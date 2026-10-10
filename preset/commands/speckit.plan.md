---
description: Execute the implementation planning workflow using the plan template to generate design artifacts, including the Verification Plan that states how each requirement will be verified.
strategy: wrap
---

<!-- markdownlint-disable-file MD041 -->

> **Integrated TDD: additional Phase 1 deliverable.**
>
> First check that `.specify/extensions/integrated-tdd/scripts/python/tdd_check.py`
> exists. If it does not exist, the `integrated-tdd` extension is not installed: say so
> now and again in the Completion Report, ignore the rest of this note and the
> "Verification Plan" section at the end of this command, and carry on as core Spec Kit
> would.
>
> Otherwise read `.specify/extensions/integrated-tdd/templates/tdd-process-rules.md` in
> full before planning. This planning run must also fill the `## Verification Plan`
> section of the plan, as described in "Verification Plan" at the end of this command.
> It is a Phase 1 output alongside `data-model.md`, `contracts/` and `quickstart.md`:
> fill it before the post-design Constitution Check, the post-execution hooks and the
> Completion Report, and do not report the plan complete while its check fails.

{CORE_TEMPLATE}

## Verification Plan

This section adds a step to **Phase 1: Design & Contracts**. Run it after `data-model.md`
and `contracts/` are written, because verification takes account of them. Skip it when
the extension is not installed, as the note at the top of this command says.

`IMPL_PLAN` already ends with a `## Verification Plan` section holding three tables. Keep
the heading, the three sub-headings and the three header rows exactly as they are, and
replace the example rows. Follow the "Verification intent" rules in the process rules.

1. **Verification commands**: find how the project already runs its tests, in its package
   scripts, Makefile, CI configuration or contributor documentation. Record each command
   with a short id, the command line in backticks (with `{select}` where a test selector
   goes), a scope of `focused` or `broad`, and where the project defines it. Declare at
   least one `broad` command. If the project has no runnable test command, leave the table
   empty, tell the developer this is a gap to resolve, and do not invent a command or
   choose a test framework.

2. **Verification obligations**: for every functional requirement (`FR-`) and every
   acceptance scenario (`USn-ASm`, scenario `m` of user story `n`) in FEATURE_SPEC, write
   the scenarios that verify it and what must be observed, stated without reference to the
   implementation. Add obligations for edge cases and failure conditions, and for the
   interfaces, data integrity rules, security requirements and integration boundaries in
   the design, in proportion to the scope, risk and complexity of the change. Choose a
   level for each. Number them `VO-001`, `VO-002`, ... and set Origin to `planned`. For a
   small, low-risk change write one obligation per requirement and per acceptance
   scenario, and no more: not one per assertion, and not for a property the specification
   does not state.

3. **Verification exemptions**: for a requirement that cannot sensibly be verified
   automatically, add a row with the reason and how it is verified instead. Write a single
   `None` row when there are no exemptions.

4. **Material ambiguity**: if a requirement is ambiguous, or contradicts another, in a way
   that changes what a test should assert, stop and ask the developer. Do not choose an
   interpretation. Leave that requirement without an obligation until the question is
   answered, record the answer under `## Clarifications` in FEATURE_SPEC, and then write
   the obligation.

5. **Check**: from the repository root run

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py plan
   ```

   Each finding names a rule and a requirement or obligation. Correct the Verification
   Plan and run the check again until it exits 0. Do not report the plan complete while it
   exits non-zero: say which findings remain and why, for example a question waiting for
   the developer or a project with no test command.

In the Completion Report, state the number of obligations and exemptions, the verification
commands found and where they came from, and the result of the check.
