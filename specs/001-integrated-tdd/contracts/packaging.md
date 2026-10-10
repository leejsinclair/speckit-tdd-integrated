# Contract: packaging and installation

**Feature**: `001-integrated-tdd` | **Research**: [research.md](../research.md)

What the repository ships and what installing it changes in an adopting project. Field
names follow the manifest validation in Spec Kit CLI 1.0.2.dev0 (research findings 1, 2
and 4).

## Packages

Two packages share one repository and one version number, with both manifests at the
repository root so that one tag archive installs either.

| Package | Manifest | Installed to | Purpose |
|---------|----------|--------------|---------|
| Extension `integrated-tdd` | `extension.yml` | `.specify/extensions/integrated-tdd/` | Process rules, evidence template, check script, runtime event |
| Preset `integrated-tdd` | `preset.yml` | `.specify/presets/integrated-tdd/` | Wraps four core commands and appends to two core templates |

Install order is extension first, then preset. `.extensionignore` keeps `preset/`,
`preset.yml`, `tests/`, `examples/`, `docs/`, `specs/`, `stories/`, `.specify/` and `.claude/`
out of the extension install. What a preset install copies is research assumption A9.

## Extension manifest

```yaml
schema_version: "1.0"

extension:
  id: "integrated-tdd"
  name: "Integrated TDD"
  version: "0.1.0"
  description: "Requirements-driven test-driven development inside the standard Spec Kit stages, with real test evidence and a hard stop on unverified tasks"
  category: "process"
  effect: "read-write"
  author: "Lee Sinclair"
  license: "MIT"

requires:
  speckit_version: ">=1.0.0"
  tools:
    - name: "python3"
      description: "Runs the deterministic checks and the runtime event handler"
      required: true

provides:
  templates:
    - name: "tdd-process-rules"
      file: "templates/tdd-process-rules.md"
      description: "The agent-neutral process rules read by the wrapped lifecycle commands"
    - name: "tdd-evidence-template"
      file: "templates/tdd-evidence-template.md"
      description: "Starting content of a feature's tdd-evidence.md"
  scripts:
    - name: "tdd-check"
      file: "scripts/python/tdd_check.py"
      description: "Deterministic checks, test execution recording, task gate and compliance check"
      runtimes: ["python"]

events:
  pre_tool_use:
    command: "speckit.integrated-tdd.gate"
    matcher: "Edit|Write|MultiEdit"
    timeout: 30
```

| Point | Contract |
|-------|----------|
| Commands | `provides.commands` is absent. The extension registers no slash command or skill |
| Lifecycle hooks | None. The `hooks:` key is absent |
| Event handler | `commands/speckit.integrated-tdd.gate.md`, not listed in the manifest. Its frontmatter is `scripts:` with the single entry `py: scripts/python/tdd_check.py hook`. Its body says it is run by the agent runtime and is not a command to invoke |
| `speckit_version` | To be raised to the first Spec Kit release that supports extension `events:`, once that release is identified (research assumption A8) |

## Preset manifest

```yaml
schema_version: "1.0"

preset:
  id: "integrated-tdd"
  name: "Integrated TDD Lifecycle"
  version: "0.1.0"
  description: "Makes the plan, tasks, analyze and implement stages derive verification intent from requirements and follow Red, Green, Refactor with recorded evidence"
  author: "Lee Sinclair"
  license: "MIT"

requires:
  speckit_version: ">=1.0.0"
  extensions:
    - "integrated-tdd"

provides:
  templates:
    - type: "template"
      name: "plan-template"
      file: "preset/templates/plan-addendum.md"
      description: "Adds the Verification Plan section"
      strategy: "append"
    - type: "template"
      name: "tasks-template"
      file: "preset/templates/tasks-addendum.md"
      description: "Adds the task label conventions"
      strategy: "append"
    - type: "command"
      name: "speckit.plan"
      file: "preset/commands/speckit.plan.md"
      description: "Wraps plan to fill and check the Verification Plan"
      strategy: "wrap"
    - type: "command"
      name: "speckit.tasks"
      file: "preset/commands/speckit.tasks.md"
      description: "Wraps tasks to label tasks and order test work first"
      strategy: "wrap"
    - type: "command"
      name: "speckit.analyze"
      file: "preset/commands/speckit.analyze.md"
      description: "Wraps analyze to report verification coverage findings"
      strategy: "wrap"
    - type: "command"
      name: "speckit.implement"
      file: "preset/commands/speckit.implement.md"
      description: "Wraps implement to follow the cycle, record evidence and gate task completion"
      strategy: "wrap"
```

| Point | Contract |
|-------|----------|
| Wrapper shape | Each wrapper has text above `{CORE_TEMPLATE}` declaring what the stage must also produce, and a procedure below it. Each tells the agent to read `.specify/extensions/integrated-tdd/templates/tdd-process-rules.md` first |
| Paths | Wrappers spell out `.specify/extensions/integrated-tdd/...` in full, because preset files are not path-rewritten |
| Missing extension | Each wrapper begins by checking that the check script exists. When it does not, the wrapper says so and the stage carries on as core Spec Kit would |
| Other commands | References to other commands use Spec Kit's `__SPECKIT_COMMAND_<NAME>__` tokens |
| Coexistence | The wrappers and addenda compose with other presets on the same commands and templates, in either priority order |

## Effect on an adopting project

| Action | Files added or changed | Files that must be unchanged |
|--------|------------------------|------------------------------|
| Add extension | `.specify/extensions/integrated-tdd/`; registry entries; one `PreToolUse` entry in `.claude/settings.json`; `.specify/events.py` if not already present | Every other entry in `.claude/settings.json`; all existing skills; other extensions |
| Add preset | `.specify/presets/integrated-tdd/`; the four composed core skills are regenerated | Every other skill; other presets' contributions to the same commands |
| Run the lifecycle | A Verification Plan section in each new `plan.md`; labels in each new `tasks.md`; one `tdd-evidence.md` per feature | The project's test configuration, CI configuration, linters, hooks and source layout |
| Remove preset | The four core skills return to their content without this preset | Existing feature artefacts, which stay readable Markdown |
| Remove extension | The directory, registry entries and the `PreToolUse` entry are removed | Existing feature artefacts, including `tdd-evidence.md` |

The extension never installs a test framework, edits test configuration, changes CI, or
adds a check the project already runs (FR-046, FR-048, FR-050).

## Repository deliverables outside the packages

| Path | Content | Requirement |
|------|---------|-------------|
| `README.md` | Install and removal, the changes to existing behaviour, observable criteria for successful operation, known limits | FR-004, FR-055 |
| `examples/stories/` | Example stories, each with its expected process behaviour: normal development, a regression, a material ambiguity, a test failure, a justified exception, a case where weakening a test is the easy route, and a small low-risk change | FR-056, FR-064 |
| `examples/runs/compliant/`, `examples/runs/tests-only/` | Artefact sets from a run that followed the process and a run that only added test files | FR-057, SC-011 |
| `docs/evaluation.md` | How to drive the stories by hand, run the compliance check, and use the evidence columns for later comparison against baseline data | FR-058, FR-064 |
