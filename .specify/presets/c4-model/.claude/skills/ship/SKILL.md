---
name: ship
description: Run this repo's checks, then commit and push to the branch the user names
---

1. Run the checks that apply to the changed files (see "Commands" in `CLAUDE.md`).
   Stop and report if any fails.
   - Run the repository linters for every change:
     `uvx ruff check .`, `uvx bandit -c bandit.yml -r scripts tests`, and
     `npx -y markdownlint-cli2`.
   - Any change to `scripts/python/c4_layout.py` or `tests/`: run
     `python3 -B -m unittest discover -s tests`.
   - Any changed Markdown file with a Mermaid block: render it with
     `npx -y @mermaid-js/mermaid-cli -i <file> -o <scratchpad>/out.svg`.
   - Any change to `extension.yml`, `preset.yml`, `commands/`, `templates/` or
     `preset/`: install both packages with `--dev` into a throwaway project outside
     this repo and confirm `specify extension list` and `specify preset list` show
     them. Then run `specify preset resolve spec-template`,
     `specify preset resolve plan-template` and `specify preset resolve speckit.plan`
     and read each output: the core content must be intact, with
     `## System Context` appended to the spec template, `## Architecture` appended
     to the plan template, and the C4 text before and after the core plan command.
   - Any change to `extension.yml`, `preset.yml`, the folder layout or
     `.extensionignore`: compare the structure with the upstream Spec Kit references
     as described under "Check structure against upstream" in `CLAUDE.md`.
2. Run `git status`; exclude git-ignored and runtime files.
3. Commit with a concise message describing the change.
4. Push to the branch the user named. If none was named, push the current branch.
   Never create a new branch without asking.
5. Report the commit hash and the branch, and say which checks were run and which
   were not.
