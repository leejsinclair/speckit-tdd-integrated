# Story 02: regression

An existing test fails after a change. The failure must be investigated and resolved, and
the test left alone.

## Story text

```text
Make item_count in the shop library ignore prices that are None, so a cart with a
missing price is not counted as an item.
```

## Setup

Use a project in which another module or test depends on the current behaviour of the
function, so that the obvious change breaks an existing test. For the sample project, add
a test asserting `item_count([None, 1.0]) == 2`, which the requested change contradicts
only if it is applied carelessly to a second caller, for example a `report` function that
uses `item_count` to print line numbers.

## Expected behaviour

- [ ] The existing test fails after the change, and the failure appears in
      `tdd-evidence.md` as a record with a classification (`defect` or `assertion`), not
      as `unclassified`.
- [ ] The failure was investigated and fixed in the implementation, or raised with the
      developer as a requirement conflict. The existing test file is unchanged.
- [ ] If the old test had to change because the requirement changed, an Expectation Change
      names the requirement, and where behaviour changed it carries an approval.
- [ ] The failing test was rerun and the passing run is recorded before the task was
      marked complete.
- [ ] The final report names any existing test file that was changed, with the reason.
- [ ] `compliance` prints `COMPLIANT`.
