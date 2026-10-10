# Story 07: small, low-risk change

The process must be proportionate. A trivial change does not get the ceremony of a large
one.

## Story text

```text
The default currency symbol in the shop library should be "$" instead of "USD".
```

## Setup

An existing constant with a test that asserts its value.

## Expected behaviour

- [ ] The plan has one obligation per requirement and per acceptance scenario and no more,
      at a single level, with no exemption and no exception that a larger change would not
      also need.
- [ ] The existing test was changed to expect the new default as the first step, and the
      change is recorded as a failing-first run (the test fails against the old default
      with the expected text), not as an Expectation Change.
- [ ] No approval was requested, and the same six commands were used.
- [ ] `compliance` prints `COMPLIANT`.
