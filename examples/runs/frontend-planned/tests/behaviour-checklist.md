# Behaviour Checklist: 001-basket-badge

**Specification**: [spec.md](../spec.md) | **Verification Plan**: [plan.md](../plan.md#verification-plan) | **Tasks**: [tasks.md](../tasks.md)

## US1-AS1

> **Given** the basket holds three items, **When** the shopper views any page, **Then** the basket icon shows a badge reading 3.

- **BI-001** Expresses: FR-001, US1-AS1. Verified by: VO-001.
  - **Given** the basket holds three items
  - **When** the shopper opens the home page
  - **Then** the basket icon shows a badge reading 3
  - **And** the same badge reading 3 is shown on a product page

## US1-AS2

> **Given** the basket holds no items, **When** the shopper views any page, **Then** the basket icon shows no badge.

- **BI-002** Expresses: FR-002, US1-AS2. Verified by: VO-002.
  - **Given** the basket holds no items
  - **When** the shopper opens the home page
  - **Then** the basket icon shows no badge, not even a badge reading 0

## US1-AS3

> **Given** the basket holds 120 items, **When** the shopper views any page, **Then** the badge reads 99+.

- **BI-003** Expresses: FR-003, US1-AS3. Verified by: VO-003.
  - **Given** the basket holds 120 items
  - **When** the shopper opens the home page
  - **Then** the badge reads 99+

## US2-AS1

> **Given** the basket holds three items, **When** the shopper adds one more, **Then** the badge reads 4 without the page being reloaded.

- **BI-004** Expresses: FR-004, US2-AS1, SC-001. Verified by: VO-004.
  - **Given** the basket holds three items and the shopper is on a product page
  - **When** the shopper adds one more item
  - **Then** the badge reads 4 within one second
  - **And** the page has not been reloaded

## US2-AS2

> **Given** the basket holds one item, **When** the shopper removes it, **Then** the badge disappears without the page being reloaded.

- **BI-005** Expresses: FR-004, US2-AS2. Verified by: VO-005.
  - **Given** the basket holds one item and the shopper is on the basket page
  - **When** the shopper removes that item
  - **Then** the badge disappears
  - **And** the page has not been reloaded

## Other behaviours

- **BI-006** Expresses: EC-01. Verified by: VO-003.
  - **Given** a basket of exactly 99 items
  - **When** the shopper opens the home page
  - **Then** the badge reads 99
  - **And** with 100 items the badge reads 99+
