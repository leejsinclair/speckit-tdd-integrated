# Architecture: [FEATURE NAME]

**Feature**: `[###-feature-name]` | **Date**: [DATE]
**Feature docs**: [Spec](./spec.md) | [Plan](./plan.md) |
[Data model](./data-model.md) | [Contracts](./contracts/)
**System views**: [Context]([relative path to context.md]) |
[Containers]([relative path to containers.md]) | [ERD]([relative path to erd.md])

<!--
  ACTION REQUIRED: Replace every example below with this feature's real design.
  Follow the C4 conventions document. Remove a section's example and write
  "Not applicable: [reason]" when the feature genuinely has nothing for it
  (for example, no persistent data).
-->

## Components

<!--
  One subsection and one C4Component diagram per container this feature adds or
  changes. Show the components this feature touches plus the neighbours they talk to.
-->

### [Container name]

```mermaid
C4Component
    title Component View for Order API - [FEATURE NAME]

    Container(webApp, "Web App", "TypeScript, React", "Storefront and checkout user interface")

    Container_Boundary(orderApi, "Order API") {
        Component(orderController, "Order Controller", "Fastify route", "Validates and routes order requests")
        Component(orderService, "Order Service", "TypeScript module", "Applies ordering rules and coordinates payment")
        Component(paymentGateway, "Payment Gateway", "TypeScript module", "Wraps the payment provider API")
        Component(orderRepository, "Order Repository", "TypeScript, Kysely", "Persists and loads orders")
    }

    ContainerDb(ordersDb, "Orders Database", "PostgreSQL 16", "Stores customers, products and orders")
    System_Ext(paymentProvider, "Payment Provider", "Authorises and captures card payments")

    Rel(webApp, orderController, "Submits orders to", "JSON/HTTPS")
    Rel(orderController, orderService, "Delegates to")
    Rel(orderService, paymentGateway, "Authorises payment through")
    Rel(orderService, orderRepository, "Saves orders using")
    Rel(paymentGateway, paymentProvider, "Calls", "JSON/HTTPS")
    Rel(orderRepository, ordersDb, "Reads from and writes to", "SQL/TCP")
```

| Component | Responsibility | Technology | Status | Source location |
|-----------|----------------|------------|--------|-----------------|
| [Component 1] | [What it does] | [Technology] | [New / Changed / Existing] | [path/in/repo] |

## Flows

<!--
  One sequence diagram per user story's primary path, plus any alternate or failure
  path that shapes the design. Participants must be elements from the C4 views.
-->

### Flow 1: [Flow name] (User Story [N])

```mermaid
sequenceDiagram
    autonumber
    actor customer as Customer
    participant webApp as Web App
    participant orderApi as Order API
    participant paymentProvider as Payment Provider
    participant ordersDb as Orders Database

    customer->>webApp: Confirm order
    webApp->>orderApi: POST /orders
    orderApi->>paymentProvider: Authorise payment
    alt Payment authorised
        paymentProvider-->>orderApi: Authorisation id
        orderApi->>ordersDb: Insert order and order lines
        ordersDb-->>orderApi: Order id
        orderApi-->>webApp: 201 Created + order id
        webApp-->>customer: Show confirmation
    else Payment declined
        paymentProvider-->>orderApi: Declined
        orderApi-->>webApp: 402 Payment Required
        webApp-->>customer: Show payment error
    end
```

**Covers**: [FR-### list, acceptance scenarios]
**Notes**: [Timeouts, retries, idempotency, ordering guarantees worth stating]

## Data

<!--
  ER diagram of the entities in this feature's data-model.md, plus existing entities
  they relate to (show those with keys only). Mark each entity New / Changed /
  Existing in the table.
-->

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_LINE : contains

    CUSTOMER {
        uuid id PK
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
```

| Entity | Status | Stored in | Notes |
|--------|--------|-----------|-------|
| [ENTITY_1] | [New / Changed / Existing] | [Database container] | [Migration or constraint notes] |

## Architecture Impact

<!--
  Every change this feature makes to the project-level views. This table is what
  gets merged into context.md, containers.md and erd.md once the feature is built.
  Write "None" in the Change column of a single row if a view is unaffected.
-->

| View | Change | Element | Detail |
|------|--------|---------|--------|
| Context | [Add / Change / Remove / None] | [Person or external system] | [What and why] |
| Containers | [Add / Change / Remove / None] | [Container or relationship] | [What and why] |
| ERD | [Add / Change / Remove / None] | [Entity, attribute or relationship] | [What and why] |
