# TDD Evidence: 001-cart-total

<!-- Written by tdd_check.py. Do not edit by hand: use the script's subcommands. -->

## Summary

_Generated from the tables below on 2026-10-16T09:58:22Z._

| Obligation | Requirements | Status | Tests | Latest result |
|------------|--------------|--------|-------|---------------|
| VO-001 | FR-001, SC-001, US1-AS1 | verified | tests.test_cart | pass (#3) |
| VO-002 | US1-AS2 | verified | tests.test_cart | pass (#5) |
| VO-003 | FR-004, US1-AS3, EC-01 | verified | tests.test_cart | pass (#7) |
| VO-004 | FR-002, SC-002, US2-AS1 | verified | tests.test_cart | pass (#9) |
| VO-005 | FR-003, FR-005, US3-AS1 | verified | tests.test_cart | pass (#11) |
| VO-006 | US3-AS2, EC-03 | verified | tests.test_cart | pass (#13) |
| VO-007 | SC-003, EC-02 | verified | tests.test_cart | pass (#15) |

| Behaviour item | Scenario | Obligations | Status | Tests |
|----------------|----------|-------------|--------|-------|
| BI-001 | US1-AS1 | VO-001 | verified | tests.test_cart |
| BI-002 | US1-AS2 | VO-002 | verified | tests.test_cart |
| BI-003 | US1-AS3 | VO-003 | verified | tests.test_cart |
| BI-004 | US2-AS1 | VO-004 | verified | tests.test_cart |
| BI-005 | US3-AS1 | VO-005 | verified | tests.test_cart |
| BI-006 | US3-AS2 | VO-006 | verified | tests.test_cart |
| BI-007 | - | VO-007 | verified | tests.test_cart |
| BI-008 | - | VO-003 | verified | tests.test_cart |

**Not verified**: none.

**Open decisions**: none. **Exceptions**: EX-01 no-meaningful-red on T004 for VO-002; EX-02 no-meaningful-red on T006 for VO-003; EX-03 no-meaningful-red on T008 for VO-004; EX-04 no-meaningful-red on T012 for VO-006; EX-05 no-meaningful-red on T014 for VO-007. **Expectation changes**: none.

**Item changes**: none.

**Pre-existing failures**: none.

## Baseline

| Seq | Command | Result | Pre-existing failures |
|-----|---------|--------|-----------------------|
| 1 | suite | pass | - |

## Test execution records

| Seq | Time | Task | Obligations | Phase | Command | Selector | Result | Valid | Classification | Files | Fingerprint | Note | Check |
|-----|------|------|-------------|-------|---------|----------|--------|-------|----------------|-------|-------------|------|-------|
| 1 | 2026-10-16T09:57:28Z | - | - | baseline | suite | - | pass | yes | - | - | - | - | 8b1b40 |
| 2 | 2026-10-16T09:57:32Z | T002 | VO-001 | red | unit-one | tests.test_cart | fail | yes | assertion | tests/test_cart.py | 1b045d | expected: has no attribute 'cart_total' | b3b945 |
| 3 | 2026-10-16T09:57:41Z | T003 | VO-001 | green | unit-one | tests.test_cart | pass | yes | - | tests/test_cart.py | 1b045d | - | 1807ad |
| 4 | 2026-10-16T09:57:46Z | T004 | VO-002 | red | unit-one | tests.test_cart | pass | no | - | tests/test_cart.py | 3bf346 | passed on first run: investigate | f65cdf |
| 5 | 2026-10-16T09:57:54Z | T005 | VO-002 | green | unit-one | tests.test_cart | pass | yes | - | - | - | - | e466d8 |
| 6 | 2026-10-16T09:58:01Z | T006 | VO-003 | red | unit-one | tests.test_cart | pass | no | - | tests/test_cart.py | b9538d | passed on first run: investigate | 25bbdf |
| 7 | 2026-10-16T09:58:01Z | T007 | VO-003 | green | unit-one | tests.test_cart | pass | yes | - | - | - | - | f09d3b |
| 8 | 2026-10-16T09:58:01Z | T008 | VO-004 | red | unit-one | tests.test_cart | pass | no | - | tests/test_cart.py | b9538d | passed on first run: investigate | 4bf628 |
| 9 | 2026-10-16T09:58:02Z | T009 | VO-004 | green | unit-one | tests.test_cart | pass | yes | - | - | - | - | 4e0e74 |
| 10 | 2026-10-16T09:58:08Z | T010 | VO-005 | red | unit-one | tests.test_cart | fail | yes | assertion | tests/test_cart.py | 2a4ad7 | expected: AssertionError: ValueError not raised | 463c16 |
| 11 | 2026-10-16T09:58:14Z | T011 | VO-005 | green | unit-one | tests.test_cart | pass | yes | - | tests/test_cart.py | 2a4ad7 | - | 2c989d |
| 12 | 2026-10-16T09:58:14Z | T012 | VO-006 | red | unit-one | tests.test_cart | pass | no | - | tests/test_cart.py | 33807d | passed on first run: investigate | b3b368 |
| 13 | 2026-10-16T09:58:14Z | T013 | VO-006 | green | unit-one | tests.test_cart | pass | yes | - | - | - | - | acf0c0 |
| 14 | 2026-10-16T09:58:15Z | T014 | VO-007 | red | unit-one | tests.test_cart | pass | no | - | tests/test_cart.py | 33807d | passed on first run: investigate | 2fed02 |
| 15 | 2026-10-16T09:58:15Z | T015 | VO-007 | green | unit-one | tests.test_cart | pass | yes | - | - | - | - | 3e2f35 |
| 16 | 2026-10-16T09:58:22Z | - | - | checkpoint | suite | - | pass | yes | - | - | - | - | 259af1 |

## Exceptions

| ID | Time | Task | Obligations | Kind | Rationale | Alternative verification | Needs approval | Approved by |
|----|------|------|-------------|------|-----------|--------------------------|----------------|-------------|
| EX-01 | 2026-10-16T09:57:54Z | T004 | VO-002 | no-meaningful-red | The sum written for VO-001 already returns a single price as the total, so the test passes on first run | Test is written and passes; green run recorded on T005 | no | - |
| EX-02 | 2026-10-16T09:58:01Z | T006 | VO-003 | no-meaningful-red | Summing the prices already satisfies this behaviour, so the test passes on first run | Test is written and passes; green run recorded on T007 | no | - |
| EX-03 | 2026-10-16T09:58:02Z | T008 | VO-004 | no-meaningful-red | Summing the prices already satisfies this behaviour, so the test passes on first run | Test is written and passes; green run recorded on T009 | no | - |
| EX-04 | 2026-10-16T09:58:14Z | T012 | VO-006 | no-meaningful-red | The negative-price validation written for VO-005 already rejects this case, so the test passes on first run | Test is written and passes; green run recorded on T013 | no | - |
| EX-05 | 2026-10-16T09:58:15Z | T014 | VO-007 | no-meaningful-red | The negative-price validation written for VO-005 already rejects this case, so the test passes on first run | Test is written and passes; green run recorded on T015 | no | - |

## Expectation changes

| ID | Time | Task | Files | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|-------|--------------|---------------|------------------|-------------|-----------------|

## Decisions

| ID | Opened | Question | Tasks | Status | Answer | Decided by | Resolved |
|----|--------|----------|-------|--------|--------|------------|----------|

## Behaviour items at baseline

| Item | Verified by | Fingerprint | Seq |
|------|-------------|-------------|-----|
| BI-001 | VO-001 | 556b31 | 1 |
| BI-002 | VO-002 | a33838 | 1 |
| BI-003 | VO-003 | 4741eb | 1 |
| BI-004 | VO-004 | 459fc2 | 1 |
| BI-005 | VO-005 | 8e052c | 1 |
| BI-006 | VO-006 | af0bd0 | 1 |
| BI-007 | VO-007 | 0e28e7 | 1 |
| BI-008 | VO-003 | b3a089 | 1 |

## Behaviour item changes

| ID | Time | Item | Requirements | Justification | Alters behaviour | Approved by | New fingerprint |
|----|------|------|--------------|---------------|------------------|-------------|-----------------|
