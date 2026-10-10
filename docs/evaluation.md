# Evaluating Integrated TDD

How to judge whether the extension does what it claims on your own projects. The agent is
driven by a person: nothing here automates a coding agent.

## What you need

- A throwaway project with its own test command, with both packages installed
  ([README](../README.md#install)).
- The example stories in [`examples/stories/`](../examples/stories/). Each holds the text
  to give `/speckit-specify`, any setup to do first, and a checklist of observable items.
- Claude Code in the project.

## Driving a story

For each story, in a clean copy of the project, run the six standard commands in order and
answer a question or approval request as a developer would:

```text
/speckit-specify <the story text>
/speckit-clarify
/speckit-plan
/speckit-tasks
/speckit-analyze
/speckit-implement
```

Do this for every story in one project, and for stories 01, 05 and 07 in each of two more
projects that differ in language and test framework. That is 13 runs. Keep each project's
lint and CI configuration in place, and run its own quality commands before the first
command and again after the last: they must still run and still gate as they did.

## Reading the result

From the repository root of the project:

```bash
python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py compliance
python3 .specify/extensions/integrated-tdd/scripts/python/tdd_check.py status
```

`compliance` prints `COMPLIANT` or `NON-COMPLIANT` and lists each finding as
`<rule> <subject>: <reason>`:

| Rule | Passes when |
|------|-------------|
| C1 | Every requirement and acceptance scenario has an obligation or an exemption |
| C2 | Every obligation is named by a test task and by a behaviour task |
| C3 | A test task comes before the first behaviour task |
| C4 | The chain of check values in the record table is intact |
| C5 | Every completed task passes the gate rules G1 to G9 |
| C6 | A baseline comes first, and the latest checkpoint passed or its failure is pre-existing and reported |
| C7 | No obligation is planned or in progress, and the stored Summary matches the regenerated view |

`status` prints, for each obligation, its requirements, derived status
(planned, in progress, verified, blocked or failed), the tests that ran and the latest
result, followed by what is not verified and why, exceptions, expectation changes, open
decisions and failures that were present before the work began.

Then work through the story's checklist from the artefacts: the plan, the task list and
`tdd-evidence.md`.

## What a compliant verdict does and does not show

It shows that the recorded process was followed: the evidence came from real runs through
the script, each behaviour had a failing run for the expected reason before a passing run,
tests were not changed unrecorded between the two, and nothing is left unreported.

It does not show that the tests' assertions are meaningful or that the requirements are
right. Those are what a reviewer judges, and `status` is the place to start. The example
runs in [`examples/runs/`](../examples/runs/) show the difference between a run that
followed the process and one that only added tests.

## Comparing with your baseline

`tdd-evidence.md` keeps the columns later comparison needs. Where you hold baseline data
for the same kind of work, compare it with:

| Measure | Taken from |
|---------|------------|
| Review effort | The time a reviewer needs to answer, for a requirement chosen at random, whether it is verified, by which tests and with what result. The Summary at the top of the evidence is the starting point; the target in the specification is under two minutes |
| Escaped defects | Defects found after merge, matched to the requirement and its obligation. An obligation with `verified` status that a defect escaped through points at a weak assertion |
| Test reliability | Records classified `unreliable` and failures classified `environment`, by time and by test selector |
| Rework | Expectation Changes (a test changed after its failing run), exceptions raised late, and tasks with several `red` records for one obligation. The Time, Task, Phase, Result and Classification columns carry each |

## Limits

Reductions in review effort, defects and rework need baseline data the adopting team
holds. The extension makes the comparison possible and does not run it.
