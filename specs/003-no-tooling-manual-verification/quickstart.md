# Quickstart: validating verification only where it is possible

**Feature**: `003-no-tooling-manual-verification` | **Plan**: [plan.md](./plan.md)

Runnable scenarios that show the feature works end to end. Formats and rules are in the
[data model](./data-model.md) and the [check script changes](./contracts/check-cli-changes.md);
this guide does not repeat them.

## Prerequisites

- Python 3.9 or later, `uvx` (for Ruff) and `npx` (for markdownlint).
- Spec Kit CLI 1.1.3 (`specify --version`).
- Claude Code, for scenario 6.
- A throwaway directory outside this repository, for example `/tmp/no-tooling`.

`CHECK` stands for `python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py`
in an installed project, and `python3 scripts/python/tdd_check.py` in this repository.

## 1. Structural validation

```bash
python3 -m unittest discover -s tests
uvx ruff check . && uvx ruff format --check .
npx markdownlint-cli2
```

Expected: all tests pass, including the pre-existing 585 except any that asserted the
behaviour this feature replaces (SC-006); Ruff and markdownlint report nothing.

## 2. No test tooling (User Story 1)

In a copy of `examples/runs/no-tooling/` (created by this feature):

```bash
CHECK plan          # plan: passed (no test tooling recorded)
CHECK tasks         # tasks: passed
CHECK gate --all    # exit 0
CHECK status        # "No test tooling: nothing is verified by tests", deferred N
CHECK compliance    # COMPLIANT, with notices
```

Then add a command row and remove the `None` row. `CHECK run --phase baseline --command
unit` is now demanded before any other run, and `gate --all` applies G3 and G4 again
(SC-004). Add a command row and keep `None`: `plan` reports the contradiction (EC-02).

## 3. A deferred obligation (User Story 2)

In a copy of `examples/runs/deferred/`:

```bash
CHECK run --phase red --task T003 --vo VO-002 --command integration --tests tests/q.py --expect "refused"
CHECK classify 7 environment
CHECK defer --vo VO-002 --reason "needs queue"      # deferred VO-002 as DF-01 (environment failure #7)
CHECK gate --task T003                              # exit 0
CHECK status                                        # VO-002 deferred: needs queue
CHECK compliance                                    # COMPLIANT with a notice
CHECK defer --vo VO-001 --reason "too slow"         # basis other: waits for approval
CHECK gate --task T001                              # G12 T001 DF-02 needs approval
CHECK approve DF-02 --by "A Person"                 # the gate passes
```

Then make the test pass and record a `green` run: VO-002 reads `verified` and leaves the
deferred list (FR-011).

## 4. Manual verification (User Story 3)

```bash
CHECK plan                                          # M1 and M2 pass
CHECK status                                        # MV-001 manual: open
CHECK manual --check MV-001 --result pass --by "A Person"
CHECK status                                        # MV-001 manual: pass by A Person
CHECK compliance                                    # COMPLIANT in every case, including fail
```

Break the table (an empty Steps cell, a duplicate id, a `Covers` id that does not exist):
`plan` reports M1 and M2 with the row.

## 5. Older features (FR-022)

Run `plan`, `gate --all`, `status` and `compliance` on `examples/runs/compliant/` from 0.2.0. The
output and exit codes are unchanged.

## 6. Agent-driven story (User Story 4)

Follow `examples/stories/09-new-project-no-framework.md` in an empty project with Claude Code
(Haiku, then Sonnet). Expected: all five stages complete, no framework is chosen or
installed, and the final report says nothing was verified by tests.

## 7. Documentation (User Story 4)

Give the README and `templates/tdd-process-rules.md` to a reader and ask the three
questions of User Story 4. The answers come from the text.

## 8. Installation regression

Install the extension and preset into a throwaway project with `specify extension add --dev`
and `specify preset add --dev`, run scenario 2 there, then remove both (`--force` for the
extension). Expected: the same results as in this repository; removal leaves core Spec Kit
working.

## Validation results

Observed results of running the scenarios and checks above, recorded as the work is done.

### T004. The 0.2.0 compatibility guard fails when a stored output is wrong

The guard test passes against the real `tests/fixtures/golden_0_2_0.json`, written from commit
`542368c` (855 outputs: five commands on 171 fixtures). A scratch copy of the golden file,
outside the repository, with one stored output changed (`valid-minimal status`, one word),
is read by the test through `TDD_GOLDEN_0_2_0_FILE`.

```text
$ cd tests && python3 -B -m unittest test_compatibility.CompatibilityTests.test_current_script_matches_0_2_0_outputs
Ran 1 test in 64.825s
OK

$ TDD_GOLDEN_0_2_0_FILE=<scratch>/golden_tampered.json python3 -B -m unittest test_compatibility.CompatibilityTests.test_current_script_matches_0_2_0_outputs
AssertionError: Lists differ: ['valid-minimal status: expected 0 ...'] != []
Ran 1 test in 64.468s
FAILED (failures=1)
```

The baseline suite before any change of this feature: `Ran 585 tests in 129.889s OK`.

### T032. Performance with 50 deferrals and 50 manual checks

`DeferralPerformanceCase` in `tests/test_performance.py` builds the 200-task, 1,000-record
feature with the first 50 obligations deferred (approved, basis other) and 50 recorded manual
checks, and applies the same two limits (2 s for a check, 1 s for the hook).

- Scale 1: all 10 tests pass (about 2 s in all).
- `TDD_PERF_LIMIT_SCALE=0.001`: 7 tests fail on their time limits (`plan`, `tasks`,
  `gate --all`, `status`, `compliance` and both hook tests), so each limit is reachable.
- `TDD_PERF_SCALE=10`: `gate --all` took 35.40 s and `compliance` 36.98 s against the 2 s
  limit; the other tests passed. This is the slowdown at about ten times the stated scale
  that the README's Known limits already record, and it is not new to deferrals and manual
  checks.

### T034. Whole suite, lint and Python 3.9

- `python3 -m unittest discover -s tests`: `Ran 788 tests in 219.090s`, `OK`.
- The same under Python 3.9.25: `Ran 788 tests in 166.341s`, `OK`.
- `uvx ruff check .`: `All checks passed!`.
- `uvx ruff format --check .`: `2 files would be reformatted`: `tests/test_evidence_location.py`
  and `tests/test_performance.py`. In `test_performance.py` the lines it would change are ones
  written before this feature; the code added here is formatted. Existing tests are not edited
  (SC-006), so both are left for the maintainer.
- `npx markdownlint-cli2`: `Summary: 0 issues in 0 files` (82 files).

### T035. Scenarios 2 to 5 against the examples

Each was run in a scratch copy of the example. The check script is called from this repository.

- **2, no test tooling** (`examples/runs/no-tooling/`): `plan: passed (no test tooling
  recorded)`, `tasks: passed`, `gate: passed, 5 completed tasks`, `status` prints "No test
  tooling: nothing is verified by tests" with both obligations deferred, and `compliance`
  prints `COMPLIANT` with three notices. Declaring a command in place of `None`: `plan:
  passed`, then `run` refuses without a baseline and `gate --all` reports G3 and G4 again.
  Keeping `None` beside a command: `PLAN None: the commands table records no test tooling
  and also declares a command: keep one`. All as expected.
- **3, a deferred obligation** (`examples/runs/deferred/`): `defer --vo VO-001 --reason "too
  slow"` prints `deferred VO-001 as DF-03 (needs approval: other)`; `gate --task T011`
  reports `G12 T011 DF-03: needs approval and has no approver`; after `approve --id DF-03
  --by "A Person"` it passes. `compliance` prints `COMPLIANT` with the notices. One
  difference from the scenario text: the quickstart's `approve DF-02` is written
  `approve --id DF-02` in the real syntax, and a passing `green` run for `VO-002` leaves it
  `deferred`, because the run has no valid failing-first record before it. It reads `verified`
  only with a valid red and green pair.
- **4, manual verification**: the open check reads `MV-001 manual: open` and `Counts: ...
  manual checks 1 open`; after `manual ... --result pass` it reads `manual: pass by A Person`
  and `1 passed`; after a `fail` result `compliance` still prints `COMPLIANT`. Breaking the
  table gives `M1 MV-001: steps is empty` and `M2 MV-001: covers FR-999 is not in spec.md`.
- **5, older features**: `plan`, `gate --all`, `status` and `compliance` on
  `examples/runs/compliant/` all exit 0, and the compatibility tests compare the output with
  the 0.2.0 golden file.

### T036. Installation regression

A release tree from `git archive HEAD` was installed into a throwaway project made with
`specify init --here --force --non-interactive --integration claude --script sh`, using
`specify extension add --dev` and `specify preset add --dev` (both v0.3.0, enabled).

- The composed skills carry the new wrapper text: `speckit-plan`, `speckit-tasks`,
  `speckit-analyze` and `speckit-implement` name `tdd_check.py`, and the plan and implement
  skills hold the Manual verification and "When verification is not possible" wording.
- Scenario 2 in that project, from a copy of `examples/runs/no-tooling/`: `plan: passed (no
  test tooling recorded)`, `tasks: passed`, `gate: passed, 5 completed tasks`, `COMPLIANT`
  with the three notices. The same as in this repository.
- After `specify preset remove integrated-tdd` and `specify extension remove integrated-tdd
  --force`, `speckit-plan/SKILL.md` has no `tdd_check.py` reference, the core skills are
  still present, and the extension is no longer listed.
- The command forms differ from the scenario text: `--dev` takes the path
  (`specify extension add --dev <path>`), and `specify init` takes `--integration claude`,
  not `--ai`.

### T037. Story 09 with Claude Code

Driven with `claude -p --effort low --permission-mode acceptEdits --allowedTools=Bash`, one
invocation per stage, in an empty project (a README and an empty `src/`) with both packages
installed from `git archive` of the working tree at the T036 commit. Haiku and Sonnet, in that
order. All twelve invocations exited 0.

**First pass** (story text without a language): the specify, clarify, plan, tasks and analyze
stages completed for both models, and `plan` and `compliance` passed. `/speckit-implement`
stopped before the first task for both, changed no file and marked no task. The stated reason
was that no language was chosen (T001 asked the developer to choose the stack); each said it
would not choose a framework. The stop was for the missing language and not for the missing
test command, so no wrapper was changed. Story 09 now names the language in its text and says
why.

**Second pass** (story text "written in Python in `src/cart.py`"):

- **Haiku**: all six stages completed. `plan` passed with the `None` row; `compliance` printed
  `COMPLIANT` with the no-tooling notice and one deferral notice per obligation (VO-001 to
  VO-009). Implement wrote `src/cart.py` and marked 11 of 20 tasks; it did not write the nine
  test tasks and asked the developer whether to declare a test command or accept a `unittest`
  placeholder. No framework was installed, no test file was written, and no evidence document
  exists. Its `tasks.md` named the standard library `unittest` as a placeholder, "chosen
  because no framework is declared": a departure from "the process never chooses a
  framework", although nothing was installed or configured. It is recorded here for the
  maintainer.
- **Sonnet**: all six stages completed. The plan has the `None` row and seven obligations;
  `compliance` printed `COMPLIANT` with notices; implement wrote `src/cart.py` and
  `tests/test_cart.py` (five plain-`assert` tests, no framework), marked 12 of 15 tasks, and
  reported the requirements as not verified by tests. It ticked two example lines in
  `tasks.md` by mistake and reverted them. It gave a test command only as a suggestion.
- **Final report wording** (Sonnet): "**Not verified:** ... are all listed as not verified"
  and "If you want real evidence, add a test command to the plan's Verification commands
  table ... I did not choose one for you." (Haiku): "either declare a test command in
  `plan.md`'s Verification commands table ... Then the nine test tasks can be written and run
  through the Red, Green, Refactor cycle."
- **Framework chosen or installed**: no, for both. `gate --all` passed for both.
