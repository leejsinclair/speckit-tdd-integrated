# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Two [Spec Kit](https://github.com/github/spec-kit) packages in one repo, both with
their manifest at the repository root so a single GitHub tag archive installs either:

- **Extension `c4`** (`extension.yml`, `commands/`, `templates/`, `scripts/python/c4_layout.py`,
  `config-template.yml`):
  adds the `speckit.c4.system`, `speckit.c4.feature` and `speckit.c4.validate`
  commands, two optional hooks, and the diagram templates and conventions.
- **Preset `c4-model`** (`preset.yml`, `preset/`): wraps the core `speckit.plan`
  command and appends sections to the core spec and plan templates. It needs the
  extension; `requires.extensions` only warns, it does not install it.

There is no build step. Most files are manifests or Markdown that an AI agent reads
as a prompt or template. `scripts/python/c4_layout.py` is a single-file Python helper
(standard library only) that the commands run to compare and measure C4 diagram
layouts. It has a `unittest` suite in `tests/`. "Correct" means: the tests and
linters pass, Spec Kit installs the packages, the composed commands read sensibly,
and every Mermaid block renders.

## Commands

One-time setup on a new machine (checks for `specify`, `npx`, `jq`, `claude` and
`python3`, registers the Playwright MCP server, and sets `core.hooksPath` to
`.githooks` so the tests run before each commit; safe to re-run):

```bash
./scripts/setup-dev.sh
```

Verify changes in a throwaway project outside this repo (use the scratchpad
directory, never `.specify/` inside this repo). `<repo>` is the absolute path of this
repository's root (`git rev-parse --show-toplevel`):

```bash
specify init <tmp-project> --integration claude
cd <tmp-project>
specify extension add --dev <repo>
specify preset add --dev <repo>

specify extension list && specify preset list
specify preset resolve spec-template     # core content + "## System Context"
specify preset resolve plan-template     # core content + "## Architecture"
specify preset resolve speckit.plan      # core command wrapped by preset/commands/speckit.plan.md
```

`--dev` copies the package, so after an edit re-run the extension add with `--force`,
and for the preset run `specify preset remove c4-model` then add it again.

Test the layout helper (standard library only; no Mermaid CLI needed, because the
fixtures in `tests/fixtures/` hold pre-rendered SVGs):

```bash
python3 -B -m unittest discover -s tests                 # all tests
python3 -B -m unittest discover -s tests -k Fidelity     # one group
C4_LAYOUT_MMDC="npx -y @mermaid-js/mermaid-cli" python3 -B -m unittest discover -s tests
python3 tests/make_fixtures.py "npx -y @mermaid-js/mermaid-cli"
```

The first form also runs from `.githooks/pre-commit` and in
`.github/workflows/tests.yml` (pull requests and pushes to `main`, Python 3.9 and
latest). The third form also renders the fixtures again and fails if the renderer's layout
has changed. The fourth regenerates the candidate files, SVGs and `expected.json`
after an intended change to the script; read the diff before keeping it.

Run all repository linters:

```bash
uvx ruff check .
uvx bandit -c bandit.yml -r scripts tests
npx -y markdownlint-cli2
```

The pre-commit hook runs these after the tests, skipping Ruff and Bandit if `uvx`
is unavailable and Markdown lint if `npx` is unavailable. GitHub Actions requires
all three.

Render every Mermaid block in a Markdown file (one SVG per block; a parse error
fails the command):

```bash
npx -y @mermaid-js/mermaid-cli -i templates/c4-container-template.md -o <tmp>/out.svg
```

Install from the published tag, as a user would:

```bash
specify extension add c4 --from https://github.com/leejsinclair/speckit-c4Model/archive/refs/tags/v0.2.0.zip
specify preset add --from https://github.com/leejsinclair/speckit-c4Model/archive/refs/tags/v0.2.0.zip
```

`specify extension add` cannot install a local zip file; use `--dev` for a local
tree or `--from <url>` for an archive. There is no `specify extension validate`
command; manifest validation only happens during `add`.

## Architecture

**What gets generated in a user's project.** Project-level living documents
(`docs/architecture/context.md`, `containers.md`, `erd.md`) written by
`speckit.c4.system`, and a per-feature `specs/<feature>/architecture.md` (C4
component views, one sequence diagram per flow, the feature ER diagram, and an
Architecture Impact table) written by `/speckit.plan` when the preset is installed,
or by `speckit.c4.feature` without it. The Architecture Impact table is the hand-off:
`speckit.c4.system` merges it into the project-level views after implementation.
The preset's plan wrapper must not edit the project-level views.

**`templates/c4-conventions.md` is the single source of rules.** All three commands
and the preset's plan wrapper tell the agent to read it first. Change a diagram rule
there, not in the individual commands. When a rule changes, update the example
diagrams in the other `templates/c4-*.md` files and in `README.md` so they still
follow it.

**How Spec Kit transforms these files at install time** (this is why paths and names
look the way they do):

- Command names must be exactly three segments, `speckit.<extension-id>.<name>`.
- In extension command files, `templates/<name>.md` is rewritten to
  `.specify/extensions/c4/templates/<name>.md`. The preset's wrapper is not
  rewritten, so it spells out the `.specify/extensions/c4/templates/...` path.
- In extension command files, `scripts/<name>` is rewritten to
  `.specify/extensions/c4/scripts/<name>`. Shipped scripts live under
  `scripts/<runtime>/` (`scripts/python/`), as in Spec Kit's bundled extensions.
  The preset's wrapper and `templates/c4-conventions.md` are not rewritten, so
  they spell out the full path.
- Refer to other commands with tokens such as `__SPECKIT_COMMAND_C4_SYSTEM__`, never
  a literal slash name. Each agent integration renders the token its own way
  (`/speckit-c4-system` in Claude Code, `/speckit.c4.system` elsewhere).
- `preset/commands/speckit.plan.md` uses `strategy: wrap`. `{CORE_TEMPLATE}` is
  replaced with the core plan command, which keeps the core `scripts:` frontmatter
  and hook blocks. Text above it declares `architecture.md` as an extra Phase 1
  deliverable; text below it is the procedure.
- The two preset templates use `strategy: append`, so their sections always land at
  the end of the core template. Nothing can be inserted mid-document.
- Resolution order is project overrides > presets > extensions > core. The
  extension's templates all use new `c4-*` names and shadow nothing in core.
- Hooks must stay `optional: true` with no `condition`; core command templates skip
  hooks that carry a condition.
- Commands locate the feature with `.specify/scripts/bash/check-prerequisites.sh
  --json --paths-only` and read settings from `.specify/extensions/c4/c4-config.yml`,
  with defaults in `extension.yml` under `config.defaults`.

**Packaging.** `.extensionignore` keeps `preset/` and `preset.yml` out of the
extension install. Presets have no ignore file, so a preset install also copies the
extension's files; they are inert. `scripts/python/c4_layout.py` ships with the extension;
`scripts/setup-dev.sh` is excluded by name. Any new top-level folder that should not ship
with the extension needs an `.extensionignore` entry.

**Mermaid C4 layout.** Mermaid's C4 renderer has no automatic layout; element
positions follow declaration order. `docs/c4-layout-evaluation.md` records measured
comparisons of orderings for the template examples and found
`UpdateLayoutConfig` row settings had no effect in Mermaid CLI 12.0.0. Read it
before changing the order of declarations in a template example, and judge a layout
change from a rendered image, not from the source. To measure one, run
`python3 scripts/python/c4_layout.py optimise <file.md> --out <tmp> --mmdc "npx -y @mermaid-js/mermaid-cli"`;
the procedure is the "Layout optimisation" section of `templates/c4-conventions.md`.

## Releasing

The extension and preset share one version number.

1. Set the same version in `extension.yml` and `preset.yml`, and add a
   `CHANGELOG.md` entry.
2. Update the two tag URLs in the Install section of `README.md`.
3. Commit, then `git tag vX.Y.Z && git push origin main vX.Y.Z`. GitHub's tag
   archive is the release artifact; there is nothing to build or upload.

## Working rules

These come from a review of past sessions (kept locally in `insights/`, which is
git-ignored).

- **Git.** Commit and push only when asked, and to the branch named. Do not create a
  new branch unless asked; if a branch seems safer, ask first. Check `git status`
  before committing and leave out ignored or runtime files.
- **Verify the real result.** After changing a manifest, command or template,
  reinstall into a throwaway project and read the composed output. After changing
  any Mermaid block, render it and look at the image. Say plainly what was not
  verified; an agent run of `/speckit.specify` then `/speckit.plan` is a separate
  check from an install check.
- **Scope.** Do not add unrequested content or sections, and do not leave out part
  of what was asked without asking first.
- **Research-only requests** ("just research and plan") mean no edits to the repo.
- **Check structure against upstream.** Before finishing a change to `extension.yml`,
  `preset.yml`, the folder layout or what ships, compare it with the current Spec Kit
  references: <https://github.com/github/spec-kit/tree/main/extensions> (API
  reference, development and publishing guides, `template/`, and the bundled `git`
  extension as a worked example) and
  <https://github.com/github/spec-kit/tree/main/presets> (`README.md`,
  `ARCHITECTURE.md`, `PUBLISHING.md`, `scaffold/`). Fetch them with
  `gh api repos/github/spec-kit/contents/<path> -H "Accept: application/vnd.github.raw"`.
  Where the guides and the CLI source disagree, the source in `src/specify_cli/`
  decides; say which one you followed. Report any deviation you keep on purpose.
- **Processes.** Never stop a process with a broad `pkill -f <pattern>`; kill by PID
  or port, as its own command.
