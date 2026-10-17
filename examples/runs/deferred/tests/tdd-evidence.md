# TDD Evidence: 001-cart-total

<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->

## Summary

_Generated from the tables below on 2026-10-16T22:11:33Z._

| Obligation | Requirements | Status | Tests | Latest result |
|------------|--------------|--------|-------|---------------|
| VO-001 | FR-001, US1-AS1 | verified | assert, pass | pass (#3) |
| VO-002 | FR-002, US1-AS2, SC-001, DC-01, EC-01 | deferred | import | fail (#5) |
| VO-003 | EC-01 | deferred | - | - |

| Behaviour item | Scenario | Obligations | Status | Tests |
|----------------|----------|-------------|--------|-------|
| BI-001 | US1-AS1 | VO-001 | verified | assert, pass |
| BI-002 | US1-AS2 | VO-002 | planned | import |
| BI-003 | - | MV-001 | manual (pass) | - |
| BI-004 | - | VO-003 | planned | - |

Not verified by tests

- VO-002 deferred: needs the cart queue, which this environment cannot reach (DF-01)
- VO-003 deferred: the zero-price case needs a slow integration run that is not available here (DF-02)
- MV-001 manual: pass by A Person

Counts: verified 1, deferred 2, manual checks 0 open, 1 passed

**Not verified**: FR-002 (VO-002 deferred), US1-AS2 (VO-002 deferred), SC-001 (VO-002 deferred), DC-01 (VO-002 deferred), EC-01 (VO-002 deferred, VO-003 deferred), FR-003 (exempt: see plan), BI-002 (planned), BI-003 (manual (pass)), BI-004 (planned).

**Open decisions**: none. **Exceptions**: none. **Expectation changes**: none.

**Item changes**: none.

**Pre-existing failures**: none.

## Baseline

| Seq | Command | Result | Pre-existing failures |
|-----|---------|--------|-----------------------|
| 1 | suite | pass | - |

## Test execution records

| Seq | Time | Task | Obligations | Phase | Command | Selector | Result | Valid | Classification | Files | Fingerprint | Note | Check |
|-----|------|------|-------------|-------|---------|----------|--------|-------|----------------|-------|-------------|------|-------|
| 1 | 2026-10-16T22:11:29Z | - | - | baseline | suite | - | pass | yes | - | - | - | - | d35e05 |
| 2 | 2026-10-16T22:11:29Z | T011 | VO-001 | red | unit | assert | fail | yes | assertion | tests/test_cart.py | 4befad | expected: AssertionError | 5e8a6a |
| 3 | 2026-10-16T22:11:29Z | T012 | VO-001 | green | unit | pass | pass | yes | - | tests/test_cart.py | 4befad | - | 836516 |
| 4 | 2026-10-16T22:11:29Z | - | - | checkpoint | suite | - | pass | yes | - | - | - | - | d48ef2 |
| 5 | 2026-10-16T22:11:29Z | T013 | VO-002 | red | unit | import | fail | no | environment | tests/test_cart.py | 4befad | failed for a different reason; the queue the cart module needs is not reachable here | ecfc8b |

## Exceptions

| ID | Time | Task | Obligations | Kind | Rationale | Alternative verification | Needs approval | Approved by |
|----|------|------|-------------|------|-----------|--------------------------|----------------|-------------|

## Expectation changes

| ID | Time | Task | Files | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|-------|--------------|---------------|------------------|-------------|-----------------|

## Decisions

| ID | Opened | Question | Tasks | Status | Answer | Decided by | Resolved |
|----|--------|----------|-------|--------|--------|------------|----------|

## Behaviour items at baseline

| Item | Verified by | Fingerprint | Seq |
|------|-------------|-------------|-----|
| BI-001 | VO-001 | e891c4 | 1 |
| BI-002 | VO-002 | cff7cd | 1 |
| BI-003 | MV-001 | f0c436 | 1 |
| BI-004 | VO-003 | e7f956 | 1 |

## Behaviour item changes

| ID | Time | Item | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|--------------|---------------|------------------|-------------|-----------------|

## Deferrals

| ID | Time | Obligations | Reason | Basis | Needs approval | Approved by | Check |
|----|------|-------------|--------|-------|----------------|-------------|-------|
| DF-01 | 2026-10-16T22:11:29Z | VO-002 | needs the cart queue, which this environment cannot reach | environment failure #5 | no | - | 6936f9 |
| DF-02 | 2026-10-16T22:11:33Z | VO-003 | the zero-price case needs a slow integration run that is not available here | other | yes | A Person | 61044f |

## Manual results

| ID | Time | Check | Result | Recorded by | Note | Check value |
|----|------|-------|--------|-------------|------|-------------|
| MR-01 | 2026-10-16T22:11:33Z | MV-001 | pass | A Person | compared with the design on 2026-10-17 | ba0057 |
