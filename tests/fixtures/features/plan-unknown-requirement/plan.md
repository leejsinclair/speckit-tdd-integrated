# Implementation Plan: Cart totals

## Summary

Add a cart total.

## Verification Plan

### Verification commands

| ID | Command | Scope | Source |
|----|---------|-------|--------|
| unit | `sh tests/fixtures/bin/fake_test.sh {select}` | focused | tests/fixtures/bin |
| suite | `sh tests/fixtures/bin/fake_test.sh pass` | broad | tests/fixtures/bin |

### Verification obligations

| ID | Requirements | Scenario | Expected outcome | Level | Origin |
|----|--------------|----------|------------------|-------|--------|
| VO-001 | FR-001, US1-AS1, FR-099 | An empty cart is totalled | The total is zero and no error is raised | unit | planned |
| VO-002 | FR-002, US1-AS2, SC-001, DC-01, EC-01 | A cart with a zero-priced item is totalled through the public interface | The total is the sum of the prices | integration | planned |

### Verification exemptions

| Requirement | Reason | Alternative verification |
|-------------|--------|--------------------------|
| FR-003 | Visual layout has no stable automated check in this project | Reviewed against the design at code review |

## Project Structure

Single project.
