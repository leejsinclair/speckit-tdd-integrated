# TDD Evidence: 001-cart-total

<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->

## Summary

_Generated from the tables below on 2026-10-10T12:50:02Z._

| Obligation | Requirements | Status | Tests | Latest result |
|------------|--------------|--------|-------|---------------|
| VO-001 | FR-001, US1-AS1, SC-001 | verified | tests.test_cart.CartTotalTests.test_totals_two_prices | pass (#3) |
| VO-002 | FR-002, US1-AS2 | verified | tests.test_cart.CartTotalTests.test_empty_cart_totals_zero, tests.test_cart.CartTotalTests | pass (#6) |

**Not verified**: FR-003 (exempt: see plan).

**Open decisions**: none. **Exceptions**: none. **Expectation changes**: none.

**Pre-existing failures**: none.

## Baseline

| Seq | Command | Result | Pre-existing failures |
|-----|---------|--------|-----------------------|
| 1 | suite | pass | - |

## Test execution records

| Seq | Time | Task | Obligations | Phase | Command | Selector | Result | Valid | Classification | Files | Fingerprint | Note | Check |
|-----|------|------|-------------|-------|---------|----------|--------|-------|----------------|-------|-------------|------|-------|
| 1 | 2026-10-10T12:50:01Z | - | - | baseline | suite | - | pass | yes | - | - | - | - | dbf0fb |
| 2 | 2026-10-10T12:50:02Z | T001 | VO-001 | red | unit | tests.test_cart.CartTotalTests.test_totals_two_prices | fail | yes | assertion | tests/test_cart.py | b70c09 | expected: has no attribute 'cart_total' | fc430a |
| 3 | 2026-10-10T12:50:02Z | T002 | VO-001 | green | unit | tests.test_cart.CartTotalTests.test_totals_two_prices | pass | yes | - | tests/test_cart.py | b70c09 | - | 9fad95 |
| 4 | 2026-10-10T12:50:02Z | T003 | VO-002 | red | unit | tests.test_cart.CartTotalTests.test_empty_cart_totals_zero | fail | yes | assertion | tests/test_cart.py | a9a576 | expected: IndexError | 83069a |
| 5 | 2026-10-10T12:50:02Z | T004 | VO-002 | green | unit | tests.test_cart.CartTotalTests.test_empty_cart_totals_zero | pass | yes | - | tests/test_cart.py | a9a576 | - | df7007 |
| 6 | 2026-10-10T12:50:02Z | T004 | VO-002 | refactor | unit | tests.test_cart.CartTotalTests | pass | yes | - | tests/test_cart.py | a9a576 | - | 9db0a7 |
| 7 | 2026-10-10T12:50:02Z | - | - | checkpoint | suite | - | pass | yes | - | - | - | - | 1285af |

## Exceptions

| ID | Time | Task | Obligations | Kind | Rationale | Alternative verification | Needs approval | Approved by |
|----|------|------|-------------|------|-----------|--------------------------|----------------|-------------|

## Expectation changes

| ID | Time | Task | Files | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|-------|--------------|---------------|------------------|-------------|-----------------|

## Decisions

| ID | Opened | Question | Tasks | Status | Answer | Decided by | Resolved |
|----|--------|----------|-------|--------|--------|------------|----------|
