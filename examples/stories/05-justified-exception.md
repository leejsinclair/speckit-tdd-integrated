# Story 05: justified exception

A change that does not suit test-first development.

## Story text

```text
Refactor the shop library's total calculation to use a single loop instead of three
passes, with no change in behaviour.
```

## Setup

The project has existing tests that cover the calculation, so that they can be run before
and after the change.

## Expected behaviour

- [ ] No new failing test is demanded. The change is recorded as an exception of kind
      `behaviour-preserving` with a rationale and an alternative verification.
- [ ] The existing tests covering the behaviour were run before the change (a `baseline` or
      `green` run) and after it (a `refactor` run), with the same command and selector.
- [ ] Where existing coverage was too thin to show behaviour was preserved, a test was
      added first.
- [ ] If the trade-off was consequential, or the kind was `legacy`, `exploratory` or
      `other`, or the alternative was `none`, the developer was asked and an approver is
      recorded. Otherwise no approval was requested.
- [ ] `compliance` prints `COMPLIANT`.
