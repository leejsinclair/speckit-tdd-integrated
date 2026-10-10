# TDD Evidence: 001-demo

<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->

## Summary

_Generated from the tables below on 2026-10-10T14:00:00Z._

## Baseline

| Seq | Command | Result | Pre-existing failures |
|-----|---------|--------|-----------------------|
| 1 | suite | fail | test_old_total fails |

## Test execution records

| Seq | Time | Task | Obligations | Phase | Command | Selector | Result | Valid | Classification | Files | Fingerprint | Note | Check |
|-----|------|------|-------------|-------|---------|----------|--------|-------|----------------|-------|-------------|------|-------|
| 1 | 2026-10-10T13:01:00Z | - | - | baseline | suite | - | fail | yes | unclassified | - | - | test_old_total fails | 8ced6e |
| 2 | 2026-10-10T13:02:00Z | T011 | VO-001 | red | unit | assert | fail | yes | assertion | tests/test_cart.py | f4164d | expected: AssertionError | fd8160 |
| 3 | 2026-10-10T13:03:00Z | T012 | VO-001 | green | unit | pass | pass | yes | - | tests/test_cart.py | d48469 | - | 3696c3 |
| 4 | 2026-10-10T13:04:00Z | T013 | VO-002 | red | unit | assert | fail | yes | assertion | tests/test_cart.py | f4164d | expected: AssertionError | aa9f15 |
| 5 | 2026-10-10T13:05:00Z | T014 | VO-002 | green | unit | pass | pass | yes | - | tests/test_cart.py | f4164d | - | ff8341 |

## Exceptions

| ID | Time | Task | Obligations | Kind | Rationale | Alternative verification | Needs approval | Approved by |
|----|------|------|-------------|------|-----------|--------------------------|----------------|-------------|

## Expectation changes

| ID | Time | Task | Files | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|-------|--------------|---------------|------------------|-------------|-----------------|
| XC-01 | 2026-10-10T13:31:00Z | T012 | tests/test_cart.py | FR-001 | The expected total was mistyped | yes | Lee Sinclair | d48469 |

## Decisions

| ID | Opened | Question | Tasks | Status | Answer | Decided by | Resolved |
|----|--------|----------|-------|--------|--------|------------|----------|
