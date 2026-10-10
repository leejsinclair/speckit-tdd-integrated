# System Context: [SYSTEM NAME]

**C4 level**: 1 - System context | **Last updated**: [DATE] |
**Updated for**: [###-feature-name or "initial"]
**Related views**: [Containers](./containers.md) | [Data model](./erd.md)

<!--
  ACTION REQUIRED: Replace the example diagram and tables with the real system.
  Show the system as ONE box. Do not show containers, technologies or internals.
-->

## Diagram

```mermaid
C4Context
    title System Context for [SYSTEM NAME]

    Person(supportAgent, "Support Agent", "Resolves order and payment issues")
    Person(customer, "Customer", "Buys products through the storefront")

    System(system, "[SYSTEM NAME]", "Lets customers browse products and place orders")

    System_Ext(emailService, "Email Service", "Delivers transactional email")
    System_Ext(paymentProvider, "Payment Provider", "Authorises and captures card payments")

    Rel(customer, system, "Browses products and places orders using")
    Rel(supportAgent, system, "Looks up and amends orders using")
    Rel(system, paymentProvider, "Requests payment authorisation from")
    Rel(system, emailService, "Sends order notifications through")
    Rel(emailService, customer, "Delivers email to")
```

## People

| Person | Description | Goals |
|--------|-------------|-------|
| [Person 1] | [Who they are] | [What they need from the system] |

## External Systems

| System | Description | Direction | Owned by |
|--------|-------------|-----------|----------|
| [External system 1] | [What it does for us] | [Outbound / Inbound / Both] | [Team or vendor] |

## Scope

**In scope**: [What the system is responsible for]

**Out of scope**: [What is deliberately left to people or external systems]
