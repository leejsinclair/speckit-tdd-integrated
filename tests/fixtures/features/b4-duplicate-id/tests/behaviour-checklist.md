# Behaviour Checklist: 001-demo

## US1-AS1

> **Given** an empty cart, **When** it is totalled, **Then** the total is zero.

- **BI-001** Expresses: FR-001, US1-AS1. Verified by: VO-001.
  - **Given** an empty cart
  - **When** the shopper asks for the total
  - **Then** the total is zero

## US1-AS2

> **Given** a cart with two items, **When** it is totalled, **Then** the total is their sum.

- **BI-002** Expresses: FR-002, US1-AS2, SC-001. Verified by: VO-002.
  - **Given** a cart with two items priced 3 and 4
  - **When** the shopper asks for the total
  - **Then** the total is 7

## Other behaviours

- **BI-001** Expresses: FR-003. Verified by: exemption FR-003.
  - **Given** the cart page is shown
  - **When** the shopper looks at it
  - **Then** it follows the shop's visual layout
