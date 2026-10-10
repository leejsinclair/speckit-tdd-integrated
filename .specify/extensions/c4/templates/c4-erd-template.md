# Data Model: [SYSTEM NAME]

**View**: Entity relationship | **Last updated**: [DATE] | **Updated for**: [###-feature-name or "initial"]
**Related views**: [System context](./context.md) | [Containers](./containers.md)

<!--
  ACTION REQUIRED: Replace the example diagram and tables with the real data model.
  This is the whole-system model. Each feature's data-model.md and architecture.md
  describe the slice that feature adds or changes.
  If the system has more than one database, use one "## [Database name]" section
  with its own diagram per database container in containers.md.
-->

## [Database container name]

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_LINE : contains
    PRODUCT ||--o{ ORDER_LINE : "is ordered in"

    CUSTOMER {
        uuid id PK
        string email UK "not null"
        string name
        datetime created_at
    }
    ORDER {
        uuid id PK
        uuid customer_id FK
        string status "pending, paid, shipped, cancelled"
        decimal total_amount
        datetime placed_at
    }
    ORDER_LINE {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        int quantity "greater than zero"
        decimal unit_price
    }
    PRODUCT {
        uuid id PK
        string sku UK
        string name
        decimal price
    }
```

## Entities

| Entity | Purpose | Owning container | Introduced by |
|--------|---------|------------------|---------------|
| [ENTITY_1] | [What it represents] | [Container that writes it] | [###-feature-name] |

## Change Log

| Date | Feature | Change |
|------|---------|--------|
| [DATE] | [###-feature-name] | [Entity / attribute / relationship added, changed or removed] |
