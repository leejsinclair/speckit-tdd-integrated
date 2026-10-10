# Story 01: normal development

Expected to be the most common case: a new behaviour with clear requirements, in a project
with a working test command.

## Story text

Give this to `/speckit-specify`:

```text
Add a cart total to the shop library. cart_total(prices) returns the sum of the item
prices in a cart. An empty cart totals zero. A negative price is rejected with a
ValueError.
```

## Setup

A project with its own test command and at least one passing test, installed with both
packages. Nothing else.

## Expected behaviour

Run `/speckit-specify`, `/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`,
`/speckit-analyze` and `/speckit-implement`. Then run `compliance` and `status`
(see [docs/evaluation.md](../../docs/evaluation.md)).

- [ ] No command other than those six was needed.
- [ ] `plan.md` has a Verification Plan whose commands are the project's own, with the
      place each is defined.
- [ ] Every `FR-` requirement and every acceptance scenario has an obligation or an
      exemption with a reason, and `tdd_check.py plan` exits 0.
- [ ] Every task is labelled, and each obligation has a test task ahead of its behaviour
      task. `tdd_check.py tasks` exits 0.
- [ ] `tdd-evidence.md` opens with a baseline record. Each obligation shows a valid `red`
      record before a valid `green` record, both from real runs.
- [ ] A broad `checkpoint` was recorded at the end of each phase and not after every change.
- [ ] No approval request was made to the developer during routine cycles.
- [ ] `compliance` prints `COMPLIANT`.
