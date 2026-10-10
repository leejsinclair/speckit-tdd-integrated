---
description: Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation, including verification coverage findings.
strategy: wrap
---

<!-- markdownlint-disable-file MD041 -->

> **Integrated TDD: verification coverage is part of the analysis.**
>
> First check that `.specify/extensions/integrated-tdd/scripts/python/tdd_check.py`
> exists. If it does not exist, the `integrated-tdd` extension is not installed: say so
> in the analysis report, ignore the rest of this note and the "Verification coverage
> findings" section at the end of this command, and carry on as core Spec Kit would.
>
> Otherwise read `.specify/extensions/integrated-tdd/templates/tdd-process-rules.md` in
> full. The analysis report must also include the findings of the two verification
> checks, as "Verification coverage findings" at the end of this command describes. This
> stage stays read-only: it reports and modifies nothing.

{CORE_TEMPLATE}

## Verification coverage findings

This section adds to the analysis report. Skip it when the extension is not installed, as
the note at the top of this command says.

1. **If the feature's `plan.md` has no Verification Plan**, the feature was planned before
   the process applied and is not under it. Report that as a gap at the start of the
   analysis report and again in its summary, name `__SPECKIT_COMMAND_PLAN__` as the way
   to bring the feature under the process, run neither check, and carry on as the core
   analysis. Do not describe the feature's work as verified.

2. **Otherwise run both checks** from the repository root:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py plan
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py tasks
   ```

   The first checks the Verification Plan against the specification: every functional
   requirement and acceptance scenario has an obligation or an exemption (C1), and every
   obligation and exemption is complete and names known requirements. The second checks
   the task list against the Verification Plan: every task is labelled (G1), and every
   obligation has a test task ahead of a behaviour task (C2, C3).

3. **Report the findings.** Add each finding to the analysis report under a "Verification
   coverage" heading, exactly as the check printed it, with the rule identifier, and count
   it among the report's issues. When both checks exit 0, say so in one line.

4. **Modify nothing.** Do not correct `plan.md` or `tasks.md` here. Name the stage that
   corrects each finding: `__SPECKIT_COMMAND_PLAN__` for the Verification Plan and
   `__SPECKIT_COMMAND_TASKS__` for the task list.
