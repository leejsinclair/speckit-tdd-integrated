# Research: Integrated Test-Driven Development for Spec Kit

**Feature**: `001-integrated-tdd` | **Date**: 2026-10-10 | **Plan**: [plan.md](./plan.md)

## Sources examined

Constitution Principle V requires design decisions to rest on the current Spec Kit source.
The findings below come from these sources, and each finding says which one.

| Source | Version | How it was examined |
|--------|---------|---------------------|
| Installed Spec Kit CLI (`specify_cli`) | 1.0.2.dev0, git commit `51e52be` of `github/spec-kit` | Source read in the installed package: `extensions/__init__.py`, `presets/__init__.py`, `events.py`, `integrations/claude/__init__.py`, `integrations/base.py`, `bundler/models/manifest.py`, `core_pack/` |
| Core commands and templates | Same | `core_pack/commands/{plan,tasks,implement}.md`, `core_pack/templates/tasks-template.md` |
| Bundled extensions and presets | Same | `core_pack/extensions/git/extension.yml`, `core_pack/presets/lean/preset.yml` |
| This project's installed customisations | c4 0.2.0, c4-model 0.2.0, know-your-spec 1.1.2 | `.specify/extensions/*/extension.yml`, `.specify/presets/c4-model/preset.yml`, `.specify/extensions.yml`, the composed `.claude/skills/speckit-plan/SKILL.md` |
| Reference extension `d0whc3r/spec-kit-tdd` | 1.1.2 | `extension.yml`, `docs/Architecture.md` and the repository file tree, fetched from GitHub |

**Read, not run.** Everything below was established by reading source. Nothing was installed
or executed against a test project during planning. The section
[Assumptions to confirm by installation test](#assumptions-to-confirm-by-installation-test)
lists what must be proved by running it before the design is relied on.

## Findings about Spec Kit

1. **Extensions cannot change core commands or templates.** `ExtensionManifest` rejects a
   `strategy` key on extension templates and scripts ("always use 'replace' semantics"), and
   extension command names must match `speckit.<extension-id>.<name>`
   (`EXTENSION_COMMAND_NAME_PATTERN`). An extension can add commands, templates, scripts,
   config, lifecycle hooks and agent runtime events.
2. **Presets can change core commands and templates.** `VALID_PRESET_TEMPLATE_TYPES` is
   `template`, `command`, `script`. `VALID_PRESET_STRATEGIES` is `replace`, `prepend`,
   `append`, `wrap`. A `wrap` layer must contain `{CORE_TEMPLATE}`, which is replaced by the
   lower-priority content. Layers from several presets compose bottom-up in priority order
   (lower number wins), so two presets can wrap the same command. The composed command keeps
   the base command's `scripts` frontmatter. This project already runs a composed
   `speckit.plan` produced this way by the `c4-model` preset.
3. **Lifecycle hooks exist before and after every core command.** The core command files
   read `hooks.before_<stage>` and `hooks.after_<stage>` from `.specify/extensions.yml` for
   constitution, specify, clarify, plan, tasks, analyze, checklist, implement, converge and
   taskstoissues. A hook with `optional: false` is executed by the agent without asking; an
   optional hook is only offered. A hook is an instruction the agent reads, so it is not a
   deterministic control. A hook's `command` must be a command, which means a mandatory
   hook needs a registered extension command.
4. **Extensions can register agent runtime events.** `events.py` defines six canonical
   events: `session_start`, `pre_tool_use`, `post_tool_use`, `session_end`,
   `user_prompt_submit` and `stop`. An extension declares them under a top-level `events:`
   key, each with a `command`, an optional `matcher` string and an optional `timeout` in
   seconds. For Claude Code the integration maps `pre_tool_use` to `PreToolUse` and writes
   the hook into `.claude/settings.json`, invoking a generated dispatcher at
   `.specify/events.py`. The dispatcher finds the command's Markdown file, reads the
   `scripts:` block in its frontmatter, runs that script with the agent's hook payload on
   standard input, and exits with the script's return code. Standard error is passed
   through. Events are skipped for a disabled extension, and `extensions/_commands.py` calls
   `refresh_integration_events` when extensions change.
5. **An event's command file does not have to be a registered command.**
   `_find_command_template` first looks in `provides.commands`, then falls back to any
   `commands/<command-name>.md` file in an enabled extension's directory, matched by file
   stem. Manifest validation does not check an event's `command` against
   `provides.commands`. An extension is valid when it provides at least one command, hook,
   event, template or script.
6. **Script variant selection falls back to Python.** `select_script_variant` uses the
   project's script type (`sh` here) when the command declares it, and otherwise falls back
   through the platform shell to `py`. A command that declares only `py:` is run with the
   dispatcher's own Python interpreter.
7. **Core task generation treats tests as optional.** `core_pack/commands/tasks.md` says
   "Tests are OPTIONAL: Only generate test tasks if explicitly requested", and the tasks
   template repeats it. Core `implement.md` says "Follow TDD approach" and "mark the task
   off as [X] in the tasks file", with no check on either.
8. **Bundles exist.** `specify bundle` installs a set of extensions, presets, steps and
   workflows declared in a `bundle.yml`. Only the manifest model's header was read; the full
   schema was not examined.

## Findings about the reference extension

`d0whc3r/spec-kit-tdd` ships four commands (`setup`, `plan`, `run`, `verify`), four
templates and three hooks, and contains Markdown only. Its mandatory `before_implement` hook
runs the red-green-refactor loop as a separate command ahead of `/speckit.implement`. It
keeps three per-feature documents in a `tdd/` directory and one project profile in
`.specify/memory/`. Evidence is written by the agent, and the audit is a fourth command the
developer chooses to run.

Taken from it: deriving the test list from the specification before code is written,
recording red and green evidence per behaviour, a single verified source for the project's
test commands, and keeping "doing" separate from "grading".

Deliberately different, because the specification requires it:

| Reference extension | This feature | Requirement |
|---------------------|--------------|-------------|
| Four new commands | No new developer-facing command | FR-002, FR-005, SC-002 |
| A separate loop command ahead of implement | The cycle runs inside the implement stage | FR-001 |
| Three new per-feature documents and a project profile | One new document | FR-005, FR-063 |
| Evidence written by the agent | Evidence written by a script that runs the tests | FR-022, FR-059 |
| Audit offered after the fact, optional | Completion blocked at the time, per task | FR-060 |
| Markdown only | Markdown plus one deterministic script | FR-059 |

## Decisions

### D1. Delivery mechanism: one preset and one extension

**Decision**: Deliver two packages from one repository. A **preset** `integrated-tdd`
wraps the core `speckit.plan`, `speckit.tasks`, `speckit.implement` and `speckit.analyze`
commands and appends to the core plan and tasks templates. An **extension**
`integrated-tdd` supplies the process rules, the evidence template, the deterministic check
script and the runtime event that enforces the hard stop.

**Rationale**: Finding 1 rules out an extension on its own, because it cannot alter what
`/speckit.implement` tells the agent. Finding 2 shows a preset can, and that it coexists
with other presets wrapping the same command. A preset on its own cannot ship a runtime
event, which finding 4 shows only an extension can. The split also follows the stated
purpose of each mechanism: presets change how existing stages operate, extensions add
capability.

**Alternatives considered**:

- *Extension with mandatory `before_implement` and `after_tasks` hooks, as the reference
  extension does.* Rejected: it needs registered commands, which become new slash commands,
  and it runs the cycle as a second pass beside the implement stage. That is a parallel
  workflow under FR-001.
- *Preset only.* Rejected: no deterministic enforcement is possible, so FR-059 and FR-060
  could not be met.
- *Preset with `replace` strategy on the core commands.* Rejected: it would shadow other
  presets and stop tracking upstream changes to the core commands, against FR-003.

### D2. Where verification intent lives

**Decision**: A `## Verification Plan` section appended to `plan.md` by the preset's
plan-template addendum. It holds three tables: verification commands, verification
obligations and verification exemptions. Tasks in `tasks.md` carry obligation labels.
Obligation status is not stored in either document.

**Rationale**: FR-005 and the specification's assumptions require verification intent to
live in existing artefacts. The plan is where design constraints (FR-008) and testing
levels (FR-011) are known, and it is produced before tasks. Status changes as work
proceeds, so storing it in the plan would duplicate what the evidence already shows
(FR-045).

**Alternatives considered**:

- *A section in `spec.md`.* Rejected: testing levels and technical constraints are design
  matters, and the specification is kept free of them.
- *A separate test-list document, as the reference extension uses.* Rejected: a second new
  mandatory document, against FR-005.

### D3. Evidence is written by the script that runs the tests

**Decision**: The agent never writes a test result. It asks the check script to run a
declared verification command, and the script executes it, observes the exit code and
output, and appends the Test Execution Record to `tdd-evidence.md` itself.

**Rationale**: FR-022 requires results to come from actual execution, and Principle III
says an agent's statement must not stand in for a check that could have been run. If the
agent wrote the record, the record would be the agent's assertion. Having the script run
the command makes "this was really executed" a property of how the record is produced.

**Alternatives considered**:

- *Agent pastes test output into the evidence document.* Rejected: unverifiable, and
  FR-062 forbids storing full output.
- *Parse each test framework's report format.* Rejected: it would tie the extension to
  particular frameworks, against FR-048. Exit code plus an expected-text match is
  framework-neutral.

### D4. What is checked deterministically and what is left to judgement

**Decision**: The script checks conditions that have one right answer. The agent decides
matters of interpretation and tells the script its decision, which is recorded.

| Checked by the script | Decided by the agent or a person |
|-----------------------|----------------------------------|
| Every requirement has an obligation or an exemption | Which scenarios and expected outcomes verify a requirement |
| Every behaviour task names obligations and is ordered after its test task | Which testing level suits a scenario |
| The command run is one the plan declares | Which tests to select for an increment |
| A failing-first run exited non-zero and its output contained the expected failure text | What the intended reason for failure is |
| A passing run exited zero | Whether a failure is an assertion, a defect or environmental |
| The failing-first record precedes the passing record | Whether an assertion checks a meaningful outcome |
| Test files recorded at the failing-first run are unchanged at the passing run, or a change is recorded | Whether a test change alters intended behaviour |
| No open decision covers the task | Whether a trade-off is consequential enough to ask a person |
| An exception has a rationale, and approval where flagged | Whether test-first is practical for a piece of work |

**Rationale**: FR-059 draws this line. The expected-failure text is the bridge for FR-018:
the agent states in advance what the failure should say, and the script confirms the output
says it. A run that fails for a different reason does not match and is not a valid Red step.

**Alternatives considered**:

- *Have the agent grade assertion quality and record a score.* Rejected as a gate: the
  result would not be repeatable. It stays as a rule the agent follows and a reviewer reads.

### D5. The hard stop is a `pre_tool_use` runtime event

**Decision**: The extension declares a `pre_tool_use` event with matcher
`Edit|Write|MultiEdit`. The handler reads the tool payload. When the edit would change a
task from `[ ]` to `[X]` in a `tasks.md` whose directory holds a `plan.md` with a
Verification Plan (whichever feature is active), it runs the task gate and exits
with code 2 and the reasons when the gate fails. It also blocks direct edits to
`tdd-evidence.md`, which only the script may write.

**Rationale**: FR-060 requires that a task cannot be marked complete, and that the check
runs inside the implement stage without being invoked. Finding 4 shows this is Spec Kit's
standard mechanism for running a script at a tool call, and that it is installed and
removed with the extension. A blocked tool call is a hard stop the agent cannot talk its
way past, which an instruction in a command file is not.

**Alternatives considered**:

- *Instruction in the implement wrapper to run the gate before marking a task.* Kept as
  well, so the agent learns the result early, but rejected as the only control: it relies
  on the agent choosing to comply.
- *A `stop` event that blocks the session from ending while a completed task fails the
  gate.* Rejected for the first release: it fires for every session in the project,
  including ones unrelated to implementation, and risks blocking a developer who is doing
  something else.
- *A git pre-commit hook.* Rejected: it acts at commit time and not at task completion, it
  is not installed by Spec Kit, and it would sit beside the project's own hooks (FR-046).

**Known limit**: an edit to `tasks.md` made through a shell command does not pass through
the matched tools. The implement wrapper's end-of-stage gate over every completed task, and
the compliance check, both catch this afterwards. It is recorded as a limit and not
presented as covered.

**Known limit**: `plan.md` is not guarded. Removing its Verification Plan heading makes the
handler treat the feature as not under the process and allow every edit. The compliance
check reports the missing section afterwards; nothing reports it at the time.

### D6. The event handler is an unlisted command file

**Decision**: The handler lives at `commands/speckit.integrated-tdd.gate.md` in the
extension and is not listed under `provides.commands`. Its frontmatter declares
`scripts: py: scripts/python/tdd_check.py hook`.

**Rationale**: Finding 5 shows the dispatcher resolves this file by its stem without it
being a registered command, so no skill or slash command is created. That keeps the set of
commands a developer sees unchanged (SC-002, Principle I).

**Alternatives considered**:

- *List it under `provides.commands`.* This is the fallback if the installation test in
  the assumptions section fails. It would add a `/speckit-integrated-tdd-gate` skill that a
  developer never needs to run, and the plan's Complexity Tracking would record why.

### D7. The project's own verification commands are declared once, in the plan

**Decision**: The Verification Plan's first table lists the project's verification commands
by identifier, for example `unit` and `suite`, each with the command line, an optional
`{select}` placeholder for choosing tests, and a scope of `focused` or `broad`. The agent
fills it during planning from what the project already defines: package scripts, a
Makefile, CI configuration, contributor documentation. The script runs only commands from
this table.

**Rationale**: FR-049 requires the project's own commands. Declaring them once lets the
script reject a record made with any other command, which closes the easiest way to fake a
pass. Scope separates the per-increment subset from the broad suite for FR-028. A missing
table, or a project with no runnable command, fails the planning check and is raised as a
gap, which is the specification's first edge case.

**Alternatives considered**:

- *Detect the test stack automatically, as the reference extension's `setup` command does.*
  Rejected: it needs a new command and per-ecosystem knowledge, against FR-048.
- *A project-level profile file.* Rejected for the first release: a new project artefact.
  The cost is that each feature's plan restates the commands, which the agent copies from
  the previous feature or the project's files.

**Known limit**: the table is in `plan.md`, which the agent can edit, so a command added to
it counts as declared whatever it runs. The script cannot tell a project's real test
command from a trivial one. The Source column and the diff of `plan.md` show a reviewer
where each command came from.

### D8. Test integrity by fingerprint

**Decision**: When a failing-first record is made, the script stores the paths of the test
files named for it and one short hash over their contents. At the passing run it reads the
paths back from that record and hashes the files again. A changed or missing file
makes the gate fail until an Expectation Change is recorded with a justification that names
a requirement, and with approval where the change alters intended behaviour.

**Rationale**: FR-029 and FR-032. A file hash is language-neutral and repeatable. It cannot
tell a weakened assertion from a corrected one, so it does not judge: it forces any change
between Red and Green into the open, where the justification is read by a person.

**Alternatives considered**:

- *Scan for skip markers and deleted assertions.* Rejected: per-framework patterns, against
  FR-048.
- *Mutation testing, as the reference extension offers.* Rejected for the first release as
  disproportionate and tool-specific. It remains possible as a verification command a
  project declares for itself.
- *Fingerprint every existing test file at the baseline.* Rejected: new tests are
  routinely added to existing test files, so ordinary work would fail the check and need
  an Expectation Change each time.

**Known limit**: only the files named on a failing-first record are fingerprinted. An
existing test outside them that is weakened, skipped or removed to obtain a pass is not
detected by a check. The process rules forbid it (FR-029), a failing existing test is a
regression to investigate (FR-027), and a reviewer sees the change in the diff.

### D9. Evidence document format

**Decision**: One file, `tdd-evidence.md`, in the feature directory, created from an
extension template by the script on first use. It is Markdown tables: a generated summary,
a baseline, test execution records, exceptions, expectation changes and decisions. Each
record row ends with a short check value chained from the row before it.

**Rationale**: FR-062 and FR-063 fix the content and the location. Markdown tables are
readable in review and can be parsed with the standard library. The chained check value
lets the compliance check report rows that were edited by hand. The generated summary at
the top answers "what is verified, what is not, and why" for SC-005 without a reviewer
running anything, and because it is derived from the rows beneath it and from `plan.md`,
it holds no independent copy of anything. It can fall behind `plan.md` between writes; the
compliance check reports that, and no check reads the Summary as a source.

**Alternatives considered**:

- *JSON or YAML.* Rejected: poor to review in a pull request.
- *A hidden machine-readable file beside the Markdown.* Rejected: two sources of truth.

**Known limit**: the check value detects casual edits. It is not a signature and does not
resist an agent that deliberately recomputes it.

### D10. Language and test tooling for this project

**Decision**: The check script is a single Python module using only the standard library,
supporting Python 3.9 and later. Its tests use `unittest`. Linting uses Ruff for Python and
markdownlint for Markdown.

**Rationale**: Spec Kit's event dispatcher is Python, so Python is already present wherever
the hard stop works. One script with no dependencies installs by file copy. This matches
the author's existing `c4` extension, which the team already maintains the same way.

**Alternatives considered**:

- *Bash plus PowerShell, as Spec Kit's core scripts.* Rejected: two implementations of rule
  logic that must give identical results, against FR-059.
- *A packaged Python tool.* Rejected: an installation step outside Spec Kit's mechanisms.

### D11. Agent neutrality

**Decision**: Three layers. The process rules are an agent-neutral Markdown template that
the wrapped commands tell the agent to read. The checks are the Python script, which knows
nothing about any agent. The only agent-specific part is the `hook` subcommand's payload
adapter, which turns Claude Code's `PreToolUse` payload into "this file, this resulting
content".

**Rationale**: FR-061. Spec Kit already maps canonical events to other agents' native
hooks, so supporting another agent means adding one payload adapter and nothing else.

**Alternatives considered**:

- *Write the rules into each wrapped command.* Rejected: four paraphrases of one standard.

### D12. Evaluation deliverables

**Decision**: Ship example stories under `examples/stories/`, each with its expected
process behaviour, and a `compliance` subcommand of the check script that reads a finished
feature directory and reports compliant or non-compliant with reasons. Ship two artefact
fixtures, one from a run that followed the process and one that only added test files, and
use both as automated tests of the compliance check. Observable success criteria are stated
in the README.

**Rationale**: FR-055, FR-056, FR-057, FR-064, SC-010 and SC-011. The compliance check is
the same rule engine as the task gate applied to the whole feature, so the two cannot
disagree. It is run by an evaluator and is never part of the lifecycle. For FR-058, the
record table's columns (time, task, phase, result, classification) are the raw data for
later comparison of rework and test reliability.

**Alternatives considered**:

- *Automate driving the agent through the stories.* Rejected by the specification's
  clarification: a person does this.

### D13. A bundle is deferred

**Decision**: The first release documents two install commands, extension first and then
preset. A `bundle.yml` that installs both is not designed yet.

**Rationale**: Finding 8. The bundle schema was not examined, and Principle V forbids
designing on it until it has been. Two commands are an installation cost for the technical
lead, paid once per project, and do not add to what a developer does (SC-002).

## Assumptions to confirm by installation test

Each of these comes from reading source and has not been run. They are the first tasks of
implementation, and each has a fallback.

| # | Assumption | How to confirm | If it fails |
|---|------------|----------------|-------------|
| A1 | A `pre_tool_use` handler that exits 2 makes Claude Code refuse the tool call and shows the handler's standard error to the agent | Install into a throwaway project, attempt to mark a task complete without evidence | No hard stop is possible on Claude Code through Spec Kit; FR-060 and FR-061 cannot be met as designed and the plan returns to the developer |
| A2 | An event resolves a command file that is not listed in `provides.commands` | Install with the handler unlisted and trigger the event | List the handler as a command (D6 fallback) and record it in Complexity Tracking |
| A3 | A command declaring only `py:` runs when the project's script type is `sh` | Same test as A1 | Add a `sh:` wrapper script that calls the Python script |
| A4 | Adding and removing the extension adds and removes the hook in `.claude/settings.json`, leaving the developer's other settings intact | Compare the file before install, after install and after removal | Document a manual step and raise an upstream issue |
| A5 | The preset's wrappers compose with the `c4-model` preset's wrapper on `speckit.plan` in either priority order | `specify preset resolve speckit.plan` with both installed | Document a required priority order |
| A6 | A preset's `requires.extensions` warns when the extension is missing and does not block | Add the preset first | Adjust the install instructions |
| A7 | The dispatcher runs with the project root as working directory, and the payload carries `tool_name`, `tool_input.file_path` and the edit strings | Log the payload in the A1 test | Adapt the payload adapter to the fields observed |
| A8 | Extension `events:` are supported from the Spec Kit version the manifests name as their minimum | Find the first release whose `specify_cli/events.py` validates extension events, from the Spec Kit changelog or tags | Raise `requires.speckit_version` in both manifests to that release |
| A9 | A preset install from this repository copies only what the preset needs, or copies extra files that stay inert | Inspect `.specify/presets/integrated-tdd/` after scenario 2 of the quickstart | Publish a release archive built from the shipped files only, and install from that |

## Unknowns resolved

| Unknown from Technical Context | Resolution |
|--------------------------------|------------|
| Delivery mechanism | D1 |
| Language and dependencies | D10 |
| Storage | D2, D9 |
| How the hard stop is enforced | D5, D6 |
| How the project's test commands are known | D7 |
| Name of the evidence document | `tdd-evidence.md` (D9) |
| Testing approach for this project | D10, and the four levels in the constitution mapped in [quickstart.md](./quickstart.md) |
