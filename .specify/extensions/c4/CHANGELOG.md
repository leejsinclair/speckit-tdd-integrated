# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/). The extension and the preset share
one version number.

## [Unreleased]

## [0.2.0] - 2026-10-10

### Added

- Layout optimisation for C4 diagrams. `scripts/python/c4_layout.py` (Python 3 standard
  library only) checks that a reorder leaves elements, boundaries and relationships
  unchanged, generates candidate declaration orders, and measures rendered SVGs.
  It stops early when the diagram as written is already readable.
- "Layout optimisation" section in the conventions, used by `speckit.c4.system`,
  `speckit.c4.feature`, `speckit.c4.validate` and the preset's plan wrapper.
- `mermaid_cli` setting for the command that runs the Mermaid CLI.
- `unittest` suite and pre-rendered fixtures for `scripts/python/c4_layout.py` in `tests/`.
- The tests run in a pre-commit hook (`.githooks/`, enabled by
  `scripts/setup-dev.sh`) and in GitHub Actions on pull requests and pushes to
  `main`.
- Ruff, Bandit and markdownlint-cli2 configuration, with checks in the pre-commit
  hook and GitHub Actions. Development-only lint configuration is excluded from
  extension packages.

## [0.1.0] - 2026-10-08

### Added

- Extension `c4`: commands `speckit.c4.system`, `speckit.c4.feature` and
  `speckit.c4.validate`; optional `after_plan` and `after_implement` hooks;
  templates for the C4 context view, container view, ER view and per-feature
  architecture document; shared diagram conventions.
- Preset `c4-model`: wraps `speckit.plan` to generate `architecture.md` in
  Phase 1, and appends a System Context section to the spec template and an
  Architecture section to the plan template.
