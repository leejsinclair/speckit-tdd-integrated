# Behaviour Checklist: 001-cart-total

**Specification**: [spec.md](../spec.md) | **Verification Plan**: [plan.md](../plan.md#verification-plan) | **Tasks**: [tasks.md](../tasks.md)

## US1-AS1

> **Given** a cart with prices 5, 10 and 20, **When** the total is requested, **Then** the result is 35.

- **BI-001** Expresses: FR-001, SC-001, US1-AS1. Verified by: VO-001.
  - **Given** a cart with prices 5, 10 and 20
  - **When** the total is requested
  - **Then** the result is 35

## US1-AS2

> **Given** a cart with a single price of 7, **When** the total is requested, **Then** the result is 7.

- **BI-002** Expresses: US1-AS2. Verified by: VO-002.
  - **Given** a cart with a single price of 7
  - **When** the total is requested
  - **Then** the result is 7

## US1-AS3

> **Given** a cart containing a free item priced 0 alongside a priced item, **When** the total is requested, **Then** the free item adds nothing to the total.

- **BI-003** Expresses: FR-004, US1-AS3. Verified by: VO-003.
  - **Given** a cart containing a free item priced 0 alongside a priced item
  - **When** the total is requested
  - **Then** the free item adds nothing to the total
  - **And** no error is raised

## US2-AS1

> **Given** an empty cart, **When** the total is requested, **Then** the result is 0.

- **BI-004** Expresses: FR-002, SC-002, US2-AS1. Verified by: VO-004.
  - **Given** an empty cart
  - **When** the total is requested
  - **Then** the result is 0

## US3-AS1

> **Given** a cart with prices 10 and -3, **When** the total is requested, **Then** a `ValueError` is raised and no total is returned.

- **BI-005** Expresses: FR-003, FR-005, US3-AS1. Verified by: VO-005.
  - **Given** a cart with prices 10 and -3
  - **When** the total is requested
  - **Then** a `ValueError` is raised
  - **And** no total is returned

## US3-AS2

> **Given** a cart whose only price is negative, **When** the total is requested, **Then** a `ValueError` is raised.

- **BI-006** Expresses: US3-AS2. Verified by: VO-006.
  - **Given** a cart whose only price is negative
  - **When** the total is requested
  - **Then** a `ValueError` is raised

## Other behaviours

- **BI-007** Expresses: SC-003. Verified by: VO-007.
  - **Given** a cart with a negative price first, in the middle or last, and other prices that would offset it
  - **When** the total is requested
  - **Then** a `ValueError` is raised in every position

- **BI-008** Expresses: FR-004. Verified by: VO-003.
  - **Given** a cart where every price is 0
  - **When** the total is requested
  - **Then** the result is 0 and no error is raised
