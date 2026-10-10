# TDD Evidence: 001-demo

<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->

## Summary

_Generated from the tables below on 2026-10-10T14:00:00Z._

| Obligation | Requirements | Status | Tests | Latest result |
|------------|--------------|--------|-------|---------------|
| VO-001 | FR-001, US1-AS1 | verified | assert, pass | pass (#3) |
| VO-002 | FR-002, US1-AS2, SC-001, DC-01, EC-01 | verified | assert, pass | pass (#5) |

**Not verified**: FR-003 (exempt: see plan).

**Open decisions**: none. **Exceptions**: none. **Expectation changes**: none.

**Pre-existing failures**: none.

## Baseline

| Seq | Command | Result | Pre-existing failures |
|-----|---------|--------|-----------------------|
| 1 | suite | fail | test_old_total fails |

## Test execution records

| Seq | Time | Task | Obligations | Phase | Command | Selector | Result | Valid | Classification | Files | Fingerprint | Note | Check |
|-----|------|------|-------------|-------|---------|----------|--------|-------|----------------|-------|-------------|------|-------|
| 1 | 2026-10-10T13:01:00Z | - | - | baseline | suite | - | fail | yes | unclassified | - | - | test_old_total fails | 8ced6e |
| 2 | 2026-10-10T13:02:00Z | T011 | VO-001 | red | unit | assert | fail | yes | assertion | tests/test_cart.py | f4164d | expected: AssertionError | fd8160 |
| 3 | 2026-10-10T13:03:00Z | T012 | VO-001 | green | unit | pass | pass | yes | - | tests/test_cart.py | f4164d | - | ee785e |
| 4 | 2026-10-10T13:04:00Z | T013 | VO-002 | red | unit | assert | fail | yes | assertion | tests/test_cart.py | f4164d | expected: AssertionError | 331ffe |
| 5 | 2026-10-10T13:05:00Z | T014 | VO-002 | green | unit | pass | pass | yes | - | tests/test_cart.py | f4164d | - | dd24eb |
| 6 | 2026-10-10T13:06:00Z | - | - | checkpoint | suite | - | fail | no | unclassified | - | - | - | 70cddd |

## Exceptions

| ID | Time | Task | Obligations | Kind | Rationale | Alternative verification | Needs approval | Approved by |
|----|------|------|-------------|------|-----------|--------------------------|----------------|-------------|

## Expectation changes

| ID | Time | Task | Files | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|-------|--------------|---------------|------------------|-------------|-----------------|

## Decisions

| ID | Opened | Question | Tasks | Status | Answer | Decided by | Resolved |
|----|--------|----------|-------|--------|--------|------------|----------|
