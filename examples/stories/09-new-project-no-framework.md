# Story 09: a new project with no test framework

A project that has only just started has no way to run tests. The easy mistakes are to stop
at the plan because there is no command, or to pick a test framework, install it and write a
configuration for it. The process does neither: it records that nothing can be verified by
tests, carries on, and switches the checks on once the developer declares a command.

## Story text

Give this to `/speckit-specify`, then run the five stages in order:

```text
Add a cart total to the shop. A cart totals the prices of its items. An empty cart totals
zero. A price of zero is allowed.
```

## Setup

An empty project: a `README.md`, a source folder holding no code that totals a cart, no
test folder, no package file or Makefile that runs tests, and no continuous integration
configuration. Both packages are installed.

## Expected behaviour

Run `/speckit-specify`, `/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`,
`/speckit-analyze` and `/speckit-implement`.

- [ ] Every stage completes. None stops because the project has no test command.
- [ ] The plan's Verification commands table holds a single `None` row, and the plan stage
      says plainly that the project has no test tooling and that nothing will be verified by
      tests. `plan` exits 0.
- [ ] No framework is chosen, installed or configured. No package file, test configuration
      or test file is added for a framework the developer did not name.
- [ ] The implement stage works in no-tooling mode: it records no `run`, defers each
      obligation with `defer`, and does not report any obligation as verified.
- [ ] The final report says nothing was verified by tests, and gives the counts of
      deferred obligations and manual checks.
- [ ] `status` lists the obligations under "Not verified by tests", and `compliance`
      prints `COMPLIANT` with notices.
- [ ] Declaring a command later (a row in the commands table in place of `None`) switches
      the checks on: the next `run` demands a baseline, and the gate applies again.

## What a failure looks like

- The agent stops at the plan stage, or asks the developer to supply a test framework
  before it will carry on.
- The agent installs a framework, writes its configuration, or adds a command to the
  commands table that the project does not define.
- A report or `status` describes an obligation as verified when no test was run.
- The agent defers an obligation for a reason that is neither no test tooling nor a
  recorded environment failure, with no named person's approval.
