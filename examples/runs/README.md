# Example runs

Two finished runs of the same small feature, for evaluating the compliance check
(FR-057, SC-011). Both start from [`sample-project/`](sample-project/), a tiny shop library
with its own tests, a specification, a Verification Plan and a labelled task list. Each
holds the four artefacts the check reads: `spec.md`, `plan.md`, `tasks.md` and
`tdd-evidence.md`.

```bash
python3 scripts/python/tdd_check.py compliance --feature-dir examples/runs/compliant
python3 scripts/python/tdd_check.py compliance --feature-dir examples/runs/tests-only
```

| Run | Verdict | What it shows |
|-----|---------|---------------|
| `compliant/` | `COMPLIANT` | A baseline, then for each obligation a failing run for the expected reason followed by a passing run, a refactor run, a broad checkpoint, and every task complete with its gate passing |
| `tests-only/` | `NON-COMPLIANT` | The same tests and code, and every task marked complete, but no failing-first run, no exception and no checkpoint. The check chain is intact: the records were made through the script, so the finding is the missing process and not tampering |

## How each was made

Both were produced by really running the check script against a copy of
`sample-project/`, so every record in `tdd-evidence.md` comes from an actual execution of
`make test` or `python3 -B -m unittest`. Nothing was written by hand. Times in the records
are those of the runs.

**`compliant/`**:

1. `run --phase baseline --command suite`.
2. A test for VO-001 was added, then `run --phase red` with the expected failure text
   `has no attribute 'cart_total'`. `cart_total` was implemented as the minimum that
   satisfies it, and `run --phase green` followed.
3. A test for VO-002 was added, then `run --phase red` with the expected text
   `IndexError`: the first implementation took its first element, so an empty cart failed.
   The implementation was corrected and `run --phase green`, then `--phase refactor`,
   followed.
4. `run --phase checkpoint --command suite`, then the README was edited (the `[NT: reason]`
   task) and every task was ticked.

**`tests-only/`**:

1. `run --phase baseline --command suite`.
2. The code and both tests were written together.
3. `run --phase green` for each of the four tasks. No `red` run was made, no exception
   recorded and no checkpoint taken. Every task was then ticked.

In `tests-only/` the compliance check reports, by rule: **C5**, the completed tasks fail
G3 (no valid failing-first record and no exception); **C6**, no checkpoint record; **C7**,
both obligations are still in progress. It reports no **C4** finding, because the run went
through the script and its check chain is valid.

The check is an evaluation aid and is not run by any lifecycle command (FR-064).
