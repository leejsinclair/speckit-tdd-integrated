# Story 03: material ambiguity

A requirement is ambiguous in a way that changes what a test would assert.

## Story text

```text
Add a discount to the shop library. A cart over 100 gets 10 percent off.
```

## Setup

None. The story is ambiguous on purpose: "over 100" may or may not include 100, and
"10 percent off" may apply to the total or to each item.

## Expected behaviour

- [ ] Planning stops and asks the developer about the ambiguity. The agent does not choose
      an interpretation.
- [ ] Until the question is answered no obligation exists for the affected requirement, so
      `tdd_check.py plan` exits non-zero and the plan is not reported complete.
- [ ] The answer is recorded under `## Clarifications` in `spec.md` before the obligation
      is written.
- [ ] No Decision is recorded in `tdd-evidence.md`: Decisions belong to the implementation
      stage, and this question was answered in planning.
- [ ] The checklist has no item for the ambiguous requirement until the answer is recorded,
      and then gains one that states the answered behaviour.
- [ ] After the answer, `plan` and `tasks` exit 0 and the run is `COMPLIANT`.
