# Changelog

All notable changes to this project are recorded here. Versions follow semantic versioning.

## Unreleased

### 0.1.0

First release: the `integrated-tdd` extension and preset.

Added

- Preset `integrated-tdd`, wrapping the core `speckit.plan`, `speckit.tasks`,
  `speckit.analyze` and `speckit.implement` commands and appending a Verification Plan
  section to the plan template and label conventions to the tasks template. No command is
  added.
- Extension `integrated-tdd`, with the agent-neutral process rules, the evidence template,
  one standard-library-only check script (`tdd_check.py`, Python 3.9 or later) and a
  `pre_tool_use` event that refuses the edit marking a task complete while its gate fails.
- Check script subcommands: `plan`, `tasks`, `gate`, `status`, `compliance`, `run`,
  `classify`, `exception`, `expectation`, `decision`, `approve` and `hook`.
- Gate rules G1 to G9 and compliance rules C1 to C7.
- `tdd-evidence.md`, one document per feature, written only by the script, with a chained
  check value on each record and a generated Summary.
- Seven example stories under `examples/stories/`, two example runs under `examples/runs/`
  and `docs/evaluation.md`.

Known limits are listed in the README. Notable: the hard stop covers Edit, Write and
MultiEdit and not shell edits; `gate --all`, `status` and `compliance` slow down well beyond
the stated scale of 200 tasks and 1,000 records; and full enforcement is on Claude Code only.

Spec Kit version: requires 0.15.0 or later, the first release with extension runtime
events. Run against 1.0.2.dev0.
