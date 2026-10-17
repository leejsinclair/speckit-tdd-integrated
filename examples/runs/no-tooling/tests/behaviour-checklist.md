# Behaviour Checklist: 001-cart-total

**Specification**: [spec.md](../spec.md) | **Verification Plan**: [plan.md](../plan.md#verification-plan) | **Tasks**: [tasks.md](../tasks.md)

## US1-AS1

> **Given** an empty cart, **When** it is totalled, **Then** the total is zero.

- **BI-001** Expresses: FR-001, US1-AS1. Verified by: VO-001.
  - **Given** an empty cart
  - **When** it is totalled
  - **Then** the total is zero

## US1-AS2

> **Given** a cart with two items, **When** it is totalled, **Then** the total is their sum.

- **BI-002** Expresses: FR-002, US1-AS2, SC-001. Verified by: VO-002.
  - **Given** a cart with two items
  - **When** it is totalled
  - **Then** the total is the sum of their prices

## Other behaviours

- **BI-003** Expresses: FR-003. Verified by: exemption FR-003.
  - **Given** the cart page
  - **When** a shopper opens it
  - **Then** it follows the shop's visual layout
