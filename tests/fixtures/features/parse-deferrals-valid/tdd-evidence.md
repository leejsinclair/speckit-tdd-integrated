# TDD Evidence: 001-demo

<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->

## Summary

_Generated from the tables below on 2026-10-10T14:02:11Z._

| Obligation | Requirements | Status | Tests | Latest result |
|------------|--------------|--------|-------|---------------|
| VO-001 | FR-001, US1-AS1 | verified | assert, pass | pass (#3) |
| VO-002 | FR-002, US1-AS2, SC-001, DC-01, EC-01 | planned | - | - |

**Not verified**: FR-002 (VO-002 planned), US1-AS2 (VO-002 planned), SC-001 (VO-002 planned), DC-01 (VO-002 planned), EC-01 (VO-002 planned), FR-003 (exempt: see plan).

**Open decisions**: none. **Exceptions**: none. **Expectation changes**: none.

**Pre-existing failures**: none.

## Baseline

| Seq | Command | Result | Pre-existing failures |
|-----|---------|--------|-----------------------|
| 1 | suite | pass | - |

## Test execution records

| Seq | Time | Task | Obligations | Phase | Command | Selector | Result | Valid | Classification | Files | Fingerprint | Note | Check |
|-----|------|------|-------------|-------|---------|----------|--------|-------|----------------|-------|-------------|------|-------|
| 1 | 2026-10-10T13:01:00Z | - | - | baseline | suite | - | pass | yes | - | - | - | - | 44242b |
| 2 | 2026-10-10T13:02:00Z | T011 | VO-001 | red | unit | assert | fail | yes | assertion | tests/test_cart.py | f4164d | expected: AssertionError | fa1cc4 |
| 3 | 2026-10-10T13:03:00Z | T012 | VO-001 | green | unit | pass | pass | yes | - | tests/test_cart.py | f4164d | - | f03d9c |
| 4 | 2026-10-10T13:04:00Z | T013 | VO-002 | red | unit | assert | fail | yes | environment | tests/test_cart.py | d48469 | expected: AssertionError | 97bca0 |

## Exceptions

| ID | Time | Task | Obligations | Kind | Rationale | Alternative verification | Needs approval | Approved by |
|----|------|------|-------------|------|-----------|--------------------------|----------------|-------------|

## Expectation changes

| ID | Time | Task | Files | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|-------|--------------|---------------|------------------|-------------|-----------------|

## Decisions

| ID | Opened | Question | Tasks | Status | Answer | Decided by | Resolved |
|----|--------|----------|-------|--------|--------|------------|----------|

## Deferrals

| ID | Time | Obligations | Reason | Basis | Needs approval | Approved by | Check |
|----|------|-------------|--------|-------|----------------|-------------|-------|
| DF-01 | 2026-10-10T13:40:00Z | VO-002 | needs queue | environment failure #4 | no | - | 9da6f5 |
| DF-02 | 2026-10-10T13:42:00Z | VO-001 | too slow | other | yes | A Person | 981e14 |

## Manual results

| ID | Time | Check | Result | Recorded by | Note | Check value |
|----|------|-------|--------|-------------|------|-------------|
| MR-01 | 2026-10-10T13:41:00Z | MV-001 | fail | A Person | the header overlaps | f8407e |
| MR-02 | 2026-10-10T13:43:00Z | MV-001 | pass | A Person | fixed | b73e3a |
