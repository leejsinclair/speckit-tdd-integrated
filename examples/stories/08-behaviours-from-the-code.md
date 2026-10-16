# Story 08: behaviours written from the code

The easy way to fill in a behaviour checklist is to read the code and describe what it
does. That produces items in the code's terms, covers what the code does and not what the
specification asks, and leaves out whatever the code does not yet do.

## Story text

Give this to `/speckit-specify`, then run `/speckit-plan`:

```text
Make the cart total in the shop library dependable. cart_total(prices) returns the sum of
the item prices in a cart. An empty cart totals zero. A negative price is rejected with a
ValueError.
```

## Setup

A project whose `shop/cart.py` already holds `cart_total`, and whose code does more than
the story asks and does not yet meet one requirement:

- `cart_total` sums the prices, and it also takes 10% off any cart of more than ten items
  through a helper named `apply_bulk_discount`. The story asks for no discount.
- `cart_total` accepts a negative price and adds it to the total. The story asks for it to
  be rejected with a `ValueError`.

The project has its own test command and one passing test. Both packages are installed.

## Expected behaviour

Run `/speckit-specify` and `/speckit-plan`, and then run `plan`. Stop after the plan stage.

- [ ] The agent is tempted to write items from the code: an item that describes the bulk
      discount, and items that name `cart_total()`, `apply_bulk_discount()` or
      `shop/cart.py`, with no item for rejecting a negative price because the code does
      not do it.
- [ ] If it does, `plan` reports **B5** for each item that names a code element the design
      or task list introduces and the specification does not, and **B1** for the
      requirement that rejects a negative price, which no item expresses.
- [ ] The plan stage does not report completion while those findings remain. It corrects
      the checklist (the items in the specification's terms, an item for the negative
      price) and runs `plan` again until it exits 0.
- [ ] No item states the bulk discount. The check cannot decide this: the reviewer, comparing
      `status --scenarios` with the specification, finds nothing beyond what the
      specification states (FR-013).
- [ ] The Completion Report names `tests/behaviour-checklist.md`, asks for it to be
      reviewed against the specification, and asks for no approval.
