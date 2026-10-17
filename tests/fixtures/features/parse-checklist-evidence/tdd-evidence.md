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
| BI-001 | VO-001 | a1b2c3 | 1 |

## Behaviour item changes

| ID | Time | Item | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|--------------|---------------|------------------|-------------|-----------------|
| BX-01 | 2026-10-10T13:31:00Z | BI-001 | FR-001, US1-AS1 | The outcome was mistyped | yes | Lee | d4e5f6 |
