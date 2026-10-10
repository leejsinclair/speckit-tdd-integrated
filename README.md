# Integrated TDD for Spec Kit

Requirements-driven test-driven development built into the standard
[Spec Kit](https://github.com/github/spec-kit) stages. A developer runs the commands they
already use. The plan states how each requirement will be verified, the task list puts test
work ahead of the behaviour it verifies, implementation proceeds through Red, Green,
Refactor with evidence from real test runs, and a task cannot be marked complete without
that evidence.

It is delivered as two Spec Kit packages from this repository:

| Package | What it does |
|---------|--------------|
| Extension `integrated-tdd` | Supplies the process rules, one deterministic check script (Python standard library only) and a runtime event that refuses the edit marking a task complete while its gate fails |
| Preset `integrated-tdd` | Wraps the core plan, tasks, analyze and implement commands, and appends a Verification Plan section to the plan template and label conventions to the tasks template |

No command is added. Nothing in the project's test, lint or CI configuration is read or
changed, and no test framework is required: a test run is judged by its exit status and by
text in its output.

## Requirements

- Spec Kit CLI 0.15.0 or later, the first release with extension runtime events. Built
  and tested with 1.0.2.dev0.
- Python 3.9 or later.
- Claude Code for full enforcement. The process rules and the checks name no agent; the
  hard stop needs an agent whose runtime Spec Kit can attach a pre-tool-use event to.
- Linux or macOS. Windows is untested.

## Install

Install the extension first, then the preset, from a release archive. The address below
is that of the `v0.1.0` tag, which exists once the release is published:

```bash
specify extension add integrated-tdd --from https://github.com/leejsinclair/speckit-tdd-integrated/archive/refs/tags/v0.1.0.zip
specify preset add integrated-tdd --from https://github.com/leejsinclair/speckit-tdd-integrated/archive/refs/tags/v0.1.0.zip
```

Install from a release archive, not from a working copy. A release archive holds only the
shipped files. Spec Kit copies a preset's whole source directory, so `--dev` on a clone of
this repository also copies its `.git`, `.specify`, `.claude` and `specs` directories into
the project. Use `--dev` only when developing the packages themselves.

The order matters. Spec Kit installs the preset without the extension and gives no
warning; each wrapped command then says the extension is missing and carries on as core
Spec Kit does.

## Remove

```bash
specify preset remove integrated-tdd
specify extension remove integrated-tdd
```

Removal returns the four commands to their core content and takes the event out of
`.claude/settings.json`. Existing feature directories are left as they are: `plan.md`,
`tasks.md` and `tdd-evidence.md` stay readable Markdown. Spec Kit rewrites the whitespace of
`.claude/settings.json` when it adds and removes the event, and keeps a copy of the
extension's directory under `.specify/extensions/.backup/`.

## What changes in an existing Spec Kit project

Installing changes five things about how Spec Kit behaves. Each is deliberate.

| Change | Why |
|--------|-----|
| `plan.md` gains a Verification Plan section: the project's test commands, verification obligations and exemptions | Verification is decided from the requirements and the design before implementation, so tests do not merely restate what the code does |
| Test tasks in `tasks.md` are mandatory for behaviour, where core Spec Kit generates them only on request, and every task carries a `[VO-nnn]` or `[NT: reason]` label | Each obligation needs a task that writes its failing test ahead of the task that delivers the behaviour, and the labels are what the checks trace |
| A task cannot be marked complete in `tasks.md` through the agent's edit tools until its gate passes | A rule that is checked and not enforced is skipped under pressure. A failed check blocks; it is not a note for review |
| `.claude/settings.json` gains one `PreToolUse` entry, managed by Spec Kit | It is how the gate runs at the moment a task is marked complete, without anyone invoking it |
| The feature directory gains `tdd-evidence.md`, which the agent's edit tools cannot change directly | Evidence is written only by the script that ran the tests, so a recorded result always comes from a real execution |

A feature whose `plan.md` was written before installation has no Verification Plan and is
not under the process. The tasks, analyze and implement stages say so at their start and in
their final report, name `/speckit-plan` as the way to bring it under the process, and
carry on as core Spec Kit does.

## How it works

| Stage | Added to the stage | Check |
|-------|--------------------|-------|
| `/speckit-plan` | The Verification Plan: commands from the project's own tooling, obligations derived from requirements, acceptance scenarios, edge cases and design constraints, exemptions with reasons. Material ambiguity is put to the developer | `plan` |
| `/speckit-tasks` | Every task labelled; a test task ahead of each behaviour task | `tasks` |
| `/speckit-analyze` | The findings of both checks in the analysis report. Nothing is modified | `plan`, `tasks` |
| `/speckit-implement` | A baseline, then Red, Green, Refactor per task through `run`, failures classified, exceptions and decisions recorded, a broad checkpoint per phase, the gate before each task is marked complete, and a final report of what is and is not verified | `run`, `gate` |

The agent's instructions are in
[`templates/tdd-process-rules.md`](templates/tdd-process-rules.md). The checks are
[`scripts/python/tdd_check.py`](scripts/python/tdd_check.py). A reviewer reads the Summary
at the top of a feature's `tdd-evidence.md`.

## Observable criteria for successful operation

Each of these can be checked from a feature's artefacts, without reading its code. The
compliance check reads most of them; it is an evaluation aid and is not a step in normal
work, and no lifecycle command runs it. How to drive the stories and read the results is in
[docs/evaluation.md](docs/evaluation.md), the stories are in
[`examples/stories/`](examples/stories/), and two finished runs, one that followed the
process and one that only added tests, are in [`examples/runs/`](examples/runs/).

| Criterion | Where to see it | Success criterion |
|-----------|-----------------|-------------------|
| Every functional requirement and acceptance scenario has an obligation or an exemption with a reason, before implementation begins | `tdd_check.py plan` exits 0 | SC-001 |
| A story completes with the six standard commands only | No other command appears in the session | SC-002 |
| Every implemented behaviour has a failing run followed by a passing run, both recorded by the script, or a recorded exception with a rationale | `tdd-evidence.md`; `compliance` rules C5 | SC-003 |
| No test is weakened, skipped or removed to obtain a pass without a recorded justification, and an approval where behaviour changes | Expectation changes table; gate rules G5 and G8 | SC-004 |
| A reviewer who took no part can say, for any requirement, whether it is verified, by which tests and with what result, in under two minutes | The Summary in `tdd-evidence.md`; `tdd_check.py status` | SC-005 |
| Every blocked test, unresolved failure and exception appears in the evidence and none is reported as verified | `status`; `compliance` rule C7 | SC-006 |
| Routine cycles make no approval request; requests occur only for ambiguity, consequential trade-offs and exceptions beyond the agent's authority | The conversation | SC-007 |
| The plan's verification commands are the project's own, on at least three projects that differ in language and test framework | Verification commands table, Source column | SC-008 |
| The project's own lint, static analysis, security and CI configuration is untouched and still gates | `git diff` of the project's configuration; its own commands | SC-009 |
| Each example story produces its defined expected behaviour | The story's checklist | SC-010 |
| A run that only added test files is reported non-compliant, and the same result is given each time | `compliance` on `examples/runs/tests-only` | SC-011 |

SC-012, the view of developers and reviewers on understandability and overhead, needs
feedback from trial use and cannot be checked from artefacts.

## Known limits

These are limits of the first release. None is presented as covered.

- **Shell edits bypass the hard stop.** The event guards the agent's Edit, Write and
  MultiEdit tools. An edit to `tasks.md` made through a shell command is not seen at the
  time. The end-of-stage `gate --all` and the compliance check report it afterwards.
- **An approver's name is not verified.** The script records the name it is given. The
  wrapped implement command tells the agent to record an approval only after the developer
  has given it in the conversation, and the name is visible to the reviewer.
- **`plan.md` is not guarded.** Removing its Verification Plan heading takes the feature out
  of the guard. The compliance check reports the missing section afterwards.
- **A declared command is trusted.** A command added to the Verification commands table
  counts as declared whatever it runs. The table's Source column and the diff of `plan.md`
  show a reviewer where each command came from.
- **Only named test files are fingerprinted.** The fingerprint covers the test files named
  on a failing-first record. A change to any other existing test is forbidden by the
  process rules and visible in the diff, and is not detected by a check.
- **The check value is not a signature.** The chained value on each evidence row shows a
  casual edit. It does not resist an agent that recomputes it.
- **Full enforcement is on Claude Code only.** Other agents get the rules and the checks,
  and no hard stop until a payload adapter is added for them.
- **A composed command can keep the wrapper after removal.** When another preset wraps the
  same command, Spec Kit stores its composed text and does not recompose it when this
  preset is removed. The leftover note says to carry on as core Spec Kit when the check
  script is absent, so it is inert. Removing and re-adding the other preset refreshes it.
- **The archive install commands were not run against a published tag.** The path tested
  is a release tree made by `git archive` and installed with `--dev`. The `--from` form
  shown under Install uses Spec Kit's documented option and is untried here.
- **Large features slow down.** `gate --all`, `status` and `compliance` scan every record
  per task or obligation and take longer than two seconds at about ten times the stated
  scale of 200 tasks and 1,000 records.
- **Windows is untested.**
- **No bundle.** The two packages are installed by two commands.

## Releasing

Both manifests declare the version; the tag must match (`v0.1.0` for `0.1.0`). Pushing a tag
runs `.github/workflows/release.yml`, which builds the zip and attaches it to a GitHub
release. The same zip can be built locally from any tag, local or on GitHub:

```bash
tools/release-zip.sh v0.1.0        # writes dist/speckit-tdd-integrated-0.1.0.zip
```

The script refuses a tag whose manifests declare another version. The zip holds only the
files not marked `export-ignore` in `.gitattributes`, which is what GitHub's own tag archive
holds too, so the install URLs under Install work with either.

## Development

```bash
python3 -B -m unittest discover -s tests
uvx ruff check .
npx -y markdownlint-cli2
```

The design is in [`specs/001-integrated-tdd/`](specs/001-integrated-tdd/): the
specification, plan, research, data model and contracts. Fixture features under
`tests/fixtures/features/` are generated by `tests/fixtures/make_features.py`.

Background on Spec Kit's customisation mechanisms is in
[speckit-overview.md](speckit-overview.md). The approach takes
[spec-kit-tdd](https://github.com/d0whc3r/spec-kit-tdd) as its reference and differs from it
in adding no command.

## Licence

MIT. See [LICENSE](LICENSE).
