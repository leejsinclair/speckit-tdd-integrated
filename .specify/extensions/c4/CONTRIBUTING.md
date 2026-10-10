# Contributing

This repository holds a Spec Kit extension (`c4`) and a preset (`c4-model`). There
is no application code and no build step: every file is a manifest, or Markdown that
an AI agent reads as a command or a template.

## Setup

You need the [Spec Kit CLI](https://github.com/github/spec-kit) (`specify`) 1.0.0 or
later, Node.js (for `npx`), `uv` (for `uvx`), and `jq`.
[Claude Code](https://claude.com/claude-code) is optional; the repository includes
a project configuration for it.

```bash
git clone https://github.com/leejsinclair/speckit-c4Model
cd speckit-c4Model
./scripts/setup-dev.sh
```

The script checks that `specify`, `npx`, `jq`, `claude` and `python3` are installed,
registers the Playwright MCP server with Claude Code, and turns on the pre-commit
hook. It is safe to re-run. If you do not use Claude Code, skip it, install the
other tools yourself and enable the hook with `git config core.hooksPath .githooks`.

## Where things are

| Path | Contents |
|------|----------|
| `extension.yml`, `commands/`, `templates/`, `config-template.yml` | The `c4` extension |
| `preset.yml`, `preset/` | The `c4-model` preset |
| `templates/c4-conventions.md` | The rules every diagram follows. Change a rule here, then update the example diagrams in the other templates and in `README.md` to match |
| `docs/c4-layout-evaluation.md` | Measured comparison of declaration orders for the Mermaid C4 examples |
| `.claude/`, `CLAUDE.md` | Claude Code skills, hooks and guidance for this repository |
| `scripts/python/c4_layout.py` | Layout helper used by the commands: fidelity check, candidate orderings and SVG measurement. Ships with the extension. Python 3 standard library only; do not add dependencies |
| `scripts/setup-dev.sh` | Development setup; not shipped with the extension |
| `.githooks/`, `.github/workflows/` | Pre-commit hook and GitHub Actions workflow that run the tests |
| `tests/` | `unittest` suite and fixtures for `scripts/python/c4_layout.py`; not shipped with the extension |

Both manifests sit at the repository root so that one GitHub tag archive installs
either package. A new top-level folder that should not be copied into users'
projects needs an entry in `.extensionignore`.

## Checking a change

Install both packages into a throwaway Spec Kit project outside this repository and
read what Spec Kit composes:

```bash
specify init /tmp/c4-check --integration claude
cd /tmp/c4-check
specify extension add --dev /path/to/speckit-c4Model
specify preset add --dev /path/to/speckit-c4Model

specify extension list && specify preset list
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve speckit.plan
```

`--dev` copies the package, so after another edit re-run the extension command with
`--force`, and for the preset run `specify preset remove c4-model` before adding it
again.

If you changed a Mermaid block, render the file. A parse error fails the command:

```bash
npx -y @mermaid-js/mermaid-cli -i templates/c4-container-template.md -o /tmp/c4-check/out.svg
```

Look at the rendered image as well. Mermaid's C4 layout follows declaration order,
so a diagram can parse and still be hard to read.

If you changed `scripts/python/c4_layout.py`, run its tests. They use only the Python
standard library and pre-rendered fixtures, so they need no Mermaid CLI:

```bash
python3 -B -m unittest discover -s tests
```

Run the repository linters before submitting any change:

```bash
uvx ruff check .
uvx bandit -c bandit.yml -r scripts tests
npx -y markdownlint-cli2
```

The tests and linters run before every commit once `./scripts/setup-dev.sh` has
pointed Git at `.githooks/`. The hook skips Ruff and Bandit when `uvx` is missing,
and Markdown lint when `npx` is missing. GitHub Actions always runs all three
linters, plus the tests on Python 3.9 and the latest Python 3, for pull requests
and pushes to `main`.

When a change to the script is meant to alter candidates or measurements, regenerate
the fixtures and review the diff:

```bash
python3 tests/make_fixtures.py "npx -y @mermaid-js/mermaid-cli"
```

## Pull requests

- Keep a change to one concern, and say in the description which of the checks above
  you ran.
- Add an entry to `CHANGELOG.md` under an `Unreleased` heading.
- Do not bump the version or tag a release in a pull request. The maintainer does
  that; the steps are in the Releasing section of `README.md`.
- Command names must stay in the form `speckit.c4.<name>`, and commands refer to
  each other with `__SPECKIT_COMMAND_*__` tokens, not literal slash names.

## License

This project is released under the [MIT License](LICENSE). By contributing, you agree
that your contributions are licensed under the same terms.
