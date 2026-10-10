---
description: Execute the implementation plan by processing and executing all tasks defined in tasks.md, each through the Red, Green, Refactor cycle with recorded evidence.
strategy: wrap
---

<!-- markdownlint-disable-file MD041 -->

> **Integrated TDD: tasks are completed through the Red, Green, Refactor cycle.**
>
> First check that `.specify/extensions/integrated-tdd/scripts/python/tdd_check.py`
> exists. If it does not exist, the `integrated-tdd` extension is not installed: say so
> now and again in the Completion Report, ignore the rest of this note and the
> "Test-driven implementation" section at the end of this command, and carry on as core
> Spec Kit would.
>
> Otherwise read `.specify/extensions/integrated-tdd/templates/tdd-process-rules.md` in
> full, then read the `## Verification Plan` section of the feature's `plan.md`.
>
> - **If `plan.md` has no Verification Plan**, the feature was planned before the process
>   applied and is not under it. State this gap now and again in the Completion Report,
>   name `__SPECKIT_COMMAND_PLAN__` as the way to bring the feature under the process, and
>   then carry on as core Spec Kit would. Record no evidence, run no check, and never
>   describe the feature's work as verified.
> - **Otherwise** every task is completed through the cycle in "Test-driven
>   implementation" at the end of this command, which applies throughout "Execute
>   implementation" below. A task is marked `[X]` only after its gate passes: the edit that
>   marks it is refused until then. A refusal is a result to act on, not an obstacle to
>   get round: never mark a task by any other means, and never edit `tdd-evidence.md`,
>   which only the check script writes.

{CORE_TEMPLATE}

## Test-driven implementation

This section governs how every task in the steps above is carried out. Skip it when the
extension is not installed or when `plan.md` has no Verification Plan, as the note at the
top of this command says.

`CHECK` stands for
`python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py`, run from the
repository root. Follow the process rules read at the start. Every test result reported in
this stage comes from `CHECK run`.

1. **Before the first task**, rerun the two planning checks and record a baseline:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py plan
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py tasks
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py run --phase baseline --command <broad command id>
   ```

   If `plan` or `tasks` exits non-zero, stop and report the findings: the plan or the task
   list must be corrected by its own stage first. If the baseline fails, name the tests
   that were already failing with `--note`; they are pre-existing and are kept apart from
   failures this work introduces.

2. **For each task**, by its labels:

   - **A test task** (the first task to name an obligation): write or update the test,
     state the text its failure should show, and record the failing run:

     ```bash
     python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py run --phase red --command <id> --select <selector> \
         --task <task id> --vo <obligation id> --tests <test file> --expect "<expected failure text>"
     ```

     Continue only when the run is recorded as valid. A pass on first run, or a failure
     for another reason, is not a Red step: investigate, correct the test, and run again.

   - **A behaviour task** (a later task naming the obligation): make the minimum change
     that satisfies the failing test, then record the passing run with `--phase green`,
     the task and the obligation. After any tidying, record `--phase refactor`. Run the
     existing tests that cover the area alongside the new one.

   - **A no-test task** (`[NT: reason]`): carry it out. It needs no run.

3. **Before marking a task complete**, check it:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py gate --task <task id>
   ```

   Mark the task `[X]` in `tasks.md` only when the gate passes. If the edit is refused,
   read the findings: each names the rule and what is missing. Meet the rule, or record
   what the process rules allow in its place, and try again.

4. **At the end of each phase** of the task list, record a broad run:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py run --phase checkpoint --command <broad command id>
   ```

   A failing checkpoint is a regression to investigate before the next phase.

5. **At the end of the stage**, after the last task:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py gate --all
   ```

   Every completed task must pass. Resolve each finding before reporting completion.

### A test changed after its Red run

When `gate` reports **G5** for a task, a test file differs between the failing-first run
and the passing run. Do not change the test back and forth to clear the finding, and do
not weaken it to pass.

1. Decide what the change is. A **correction** brings the test into line with the approved
   requirements. Otherwise it **alters intended behaviour**.
2. Record it, naming the requirement it is justified against:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py expectation --task <task id> \
       --tests <test file> --requirement <requirement id> --justification "<why>" [--alters-behaviour]
   ```

3. Where it alters intended behaviour, explain the change to the developer and ask for
   approval. Record the approval only after the developer has given it in the
   conversation, with the developer's name:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py approve --id <XC-nn> --by "<name>"
   ```

   Until then the task stays incomplete (G8). Continue with tasks that do not depend on
   it.

### Failures, exceptions and decisions

Follow "Failures, exceptions and decisions" in the process rules. In this stage:

1. **Classify each failure after investigating it.** A run that fails, other than a valid
   Red step, is recorded as `unclassified`. Find the cause, then record what it is:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py classify --seq <record number> \
       --as <assertion|defect|environment|unreliable> --note "<what was found>"
   ```

   Resolve the failure before starting work that depends on it. An `environment` failure
   blocks the obligation; an `unreliable` test is reported as unreliable and is not rerun
   until it passes.

2. **Record an exception where the cycle does not fit the work**, with the rationale and
   the verification followed instead:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py exception --task <task id> --vo <obligation id> \
       --kind <kind> --rationale "<why>" --alternative "<how it is verified instead>"
   ```

   The passing run is still required of the behaviour task. Exceptions of kind `legacy`,
   `exploratory` or `other`, and any with no alternative verification, need the
   developer's approval: explain the trade-off, ask, and record
   `approve --id <EX-nn> --by "<name>"` only after the developer has approved in the
   conversation. Give `--needs-approval` for any other exception that involves a
   consequential trade-off.

3. **Open a decision when work must wait for a person**, listing the affected task and
   every task that depends on it:

   ```bash
   python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py decision open \
       --question "<what is to be decided>" --tasks <task id> <task id>
   ```

   Hold only the tasks listed and continue with the others. Never proceed on an assumed
   answer. When every remaining task depends on an open decision, stop and report. When
   the developer answers, record `decision resolve --id <DN-nn> --answer "<answer>"
   --by "<name>"` and resume.

4. **Report blocked and failed items as what they are.** In every progress report and in
   the Completion Report, list each blocked test, unresolved failure, exception and open
   decision, with the tasks held back. Never describe such work as verified, and leave its
   tasks unmarked.

### End-of-stage report

After `gate --all`, print the review view and report from it:

```bash
python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py status
```

In the Completion Report, in addition to what the core command asks for:

- State what is verified and what is not, and why, obligation by obligation as `status`
  shows it.
- List every blocked or failed item, every exception, every expectation change and every
  open decision, with the tasks held back. List any change made to an existing test file,
  with its reason.
- State plainly that passing tests do not show that requirements listed as not verified
  are met.
- State that passing tests do not stand in for linting, static analysis, security checks
  or any other validation the project requires: those are run and reported as the project
  already requires.
- Point the reviewer to `tdd-evidence.md` in the feature directory.

Do not describe the stage as complete while `gate --all` exits non-zero or while an
obligation is planned or in progress: say what remains.

Routine cycles involve no approval request to the developer. Never edit `tdd-evidence.md`
directly, and never copy test output into the artefacts.
