# Behaviour Checklist: 001-demo

## US1-AS1: empty cart

> **Given** an empty cart, **When** it is totalled, **Then** the total is zero.

- **BI-001** Expresses: FR-001, US1-AS1. Verified by: VO-001.
  - **Given** an empty cart
  - **When** the shopper asks for the total
  - **Then** the total is zero
  - **And** no error is shown

## US1-AS2

> **Given** a cart with two items, **When** it is totalled, **Then** the total is their sum.

- **BI-002** Expresses: FR-002, US1-AS2. Verified by: VO-002.
  - **Given** a cart with two items priced 3 and 4
  - **When** the shopper asks for the total
  - **Then** the total is 7

## Other behaviours

- **BI-003** Expresses: FR-003, EC-01. Verified by: VO-002, exemption FR-003.
  - **Given** an item priced 0
  - **When** the cart is totalled
  - **Then** the zero price is accepted

```markdown
- **BI-099** Expresses: FR-001. Verified by: VO-001.
- [ ] a checkbox in a fence
```
