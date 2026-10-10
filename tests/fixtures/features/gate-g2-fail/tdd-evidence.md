# TDD Evidence: 001-demo

<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->

## Summary

_Generated from the tables below on 2026-10-10T14:00:00Z._

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
| 4 | 2026-10-10T13:04:00Z | T013 | VO-002 | red | unit | assert | fail | yes | assertion | tests/test_cart.py | f4164d | expected: AssertionError | 5aa222 |
| 5 | 2026-10-10T13:05:00Z | T014 | VO-002 | green | unit | pass | pass | yes | - | tests/test_cart.py | f4164d | - | 9c2272 |
| 6 | 2026-10-10T13:06:00Z | - | - | checkpoint | suite | - | pass | yes | - | - | - | - | d2168d |

## Exceptions

| ID | Time | Task | Obligations | Kind | Rationale | Alternative verification | Needs approval | Approved by |
|----|------|------|-------------|------|-----------|--------------------------|----------------|-------------|

## Expectation changes

| ID | Time | Task | Files | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|-------|--------------|---------------|------------------|-------------|-----------------|

## Decisions

| ID | Opened | Question | Tasks | Status | Answer | Decided by | Resolved |
|----|--------|----------|-------|--------|--------|------------|----------|
| DN-01 | 2026-10-10T13:32:00Z | Should an empty cart raise or return zero? | T013, T014 | open | - | - | - |
