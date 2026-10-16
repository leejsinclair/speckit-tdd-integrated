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
