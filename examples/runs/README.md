# Example runs

Two finished runs of the same small feature, for evaluating the compliance check
(FR-057, SC-011), and one planned feature with a screen. The runs start from
[`sample-project/`](sample-project/), a tiny shop library with its own tests, a specification,
a Verification Plan, a behaviour checklist and a labelled task list.

| Directory | Holds |
|-----------|-------|
| `compliant/` | `spec.md`, `plan.md`, `tasks.md`, `tests/behaviour-checklist.md` and `tests/tdd-evidence.md`: the layout of a feature planned with 0.2.0 |
| `tests-only/` | `spec.md`, `plan.md`, `tasks.md` and `tdd-evidence.md` at the top of the directory: the layout of a 0.1.0 feature, which the check still reads |
| `frontend-planned/` | `spec.md`, `plan.md` and `tests/behaviour-checklist.md` of a basket badge on a screen, planned and not implemented. `plan` passes. Its items state what the user sees and can do, and name no component, selector or file |
| `sample-project/` | The project as it was before either run |

```bash
python3 scripts/python/tdd_check.py compliance --feature-dir examples/runs/compliant
python3 scripts/python/tdd_check.py compliance --feature-dir examples/runs/tests-only
python3 scripts/python/tdd_check.py plan --feature-dir examples/runs/frontend-planned
python3 scripts/python/tdd_check.py status --scenarios --feature-dir examples/runs/frontend-planned
```

| Run | Verdict | What it shows |
|-----|---------|---------------|
| `compliant/` | `COMPLIANT` | A baseline, then for each obligation a failing run for the expected reason followed by a passing run, a refactor run, a broad checkpoint, and every task complete with its gate passing |
| `tests-only/` | `NON-COMPLIANT` | The same tests and code, and every task marked complete, but no failing-first run, no exception and no checkpoint. The check chain is intact: the records were made through the script, so the finding is the missing process and not tampering |

## How each was made

Both were produced by really running, so every record in `tdd-evidence.md` comes from an
actual execution of `make test` or `python3 -B -m unittest`. Nothing was written by hand.
Times in the records are those of the runs.

**`compliant/`** was regenerated for 0.2.0 by a real run: a copy of `sample-project/` with
both packages installed, driven through `/speckit-specify` (with the text of story 01),
`/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-analyze` and
`/speckit-implement` with Claude Code (`claude -p`, one invocation per command). Its
`spec.md`, `plan.md`, `tasks.md`, `tests/behaviour-checklist.md` and
`tests/tdd-evidence.md` are the files that run produced, copied with one repeated blank line in `tasks.md` removed for the Markdown linter. The run recorded
a baseline, a failing run for the expected reason followed by a passing run where the
behaviour was new, and an exception of kind `no-meaningful-red` for each obligation whose
test passed on its first run because an earlier implementation already covered it. The
check script's `compliance` prints `COMPLIANT` for it, and `sample-project/specs/` was
updated to the planning artefacts of that run, with every task unticked.

**`tests-only/`** is the 0.1.0 example, produced by running the check script against a copy
of the earlier `sample-project/`:

1. `run --phase baseline --command suite`.
2. The code and both tests were written together.
3. `run --phase green` for each of the four tasks. No `red` run was made, no exception
   recorded and no checkpoint taken. Every task was then ticked.

In `tests-only/` the compliance check reports, by rule: **C5**, the completed tasks fail
G3 (no valid failing-first record and no exception); **C6**, no checkpoint record; **C7**,
both obligations are still in progress. It reports no **C4** finding, because the run went
through the script and its check chain is valid.

The check is an evaluation aid and is not run by any lifecycle command (FR-064).
