# Know Your Spec

A [Spec Kit](https://github.com/github/spec-kit) extension: a Comprehension Checkpoint that
quizzes the developer on a finished `spec.md`, one question at a time, to test genuine
understanding before moving on to planning.

## Why

Spec Kit's lifecycle is `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` →
`/speckit-implement`. It's easy for a spec to get written — by the developer, or drafted by an AI
assistant from a short description — without the developer actually having internalized what it
says. Know Your Spec closes that gap: immediately after a spec is finished, it asks five
questions about the spec's own content, coaches the developer until they demonstrate real
understanding, and never blocks or persists anything.

## What it does

| Stage | Runs | What happens |
|---|---|---|
| `/speckit-specify` | Spec Kit | Unmodified — this extension doesn't touch spec generation itself |
| *(immediately after)* | Automatic (`after_specify` hook, mandatory) | The Comprehension Checkpoint fires: five questions, one at a time, at fixed increasing difficulty (Recognise → Explain → Apply → Trace → Evaluate) |
| `/speckit-plan`, `/speckit-tasks`, `/speckit-implement` | Spec Kit | Unmodified — the checkpoint is advisory only and never gates any later stage |

Each question is judged on semantic understanding, not exact wording. A wrong or incomplete
answer gets a coaching hint (pointing at the relevant `spec.md` heading, never revealing the
answer outright) and a newly-worded question at the same difficulty level — with no limit on
retries. A developer stuck on one question can explicitly skip or reveal just that question
without ending the session. Before any question is asked, its expected answer and source heading
are derived privately; if `spec.md` doesn't yet establish enough content to truthfully support a
question at some level, the checkpoint proposes a repair or clarification and asks for explicit
approval before applying it — it never quizzes on information the spec never actually
established, and never edits `spec.md` without being asked first.

Nothing about a session — questions, answers, judgments, retries, the completion summary — is
ever written to `spec.md` or any other file. The only way this extension ever touches the repo is
an explicitly developer-approved repair to `spec.md`'s own content, decided before the quiz
begins.

### The spec page (optional)

Before question 1 the checkpoint asks once: "Open the spec on a page in your browser, or stay in
chat?" If you choose the page, it starts a small local server and gives you an address. The page
shows `spec.md` rendered — headings you can link to, a preview of each requirement where it is
referenced (hover `FR-003`), and a notice when the file changes — so a coaching hint can link
straight to the heading it points at. The quiz itself stays in the conversation.

- The page is read-only: it has no route that changes anything.
- It answers only at the address it gave you, which carries a one-time key.
- It listens on every network interface (`0.0.0.0`), so the page works when the project runs in
  a container or on a remote machine and the port is forwarded to your PC: forward the port and
  open the address as given. This also means other machines on the same network can reach the
  port; without the key they get a refusal. To keep it to the one machine, start it yourself
  with `--host 127.0.0.1`.
- Mermaid diagrams in the spec are drawn in the browser. For that, a page whose spec has a
  diagram loads one script, `mermaid@11` from the jsDelivr CDN, so drawing needs an internet
  connection; without one the diagram's source is shown. A spec with no diagram loads nothing
  from the internet.
- It needs `python3` (3.11 or later, standard library only). Without it the offer is skipped and
  the checkpoint is exactly as described above.
- It keeps nothing in the repository. While it runs, it holds its address in the system's
  temporary folder (or, if that is inside the project, somewhere outside it); it stops when the checkpoint ends, or after an hour without use.

You can also run it yourself:

```bash
python3 .specify/extensions/know-your-spec/scripts/python/specpage.py serve --spec specs/<feature>/spec.md
```

## Install

```bash
specify extension add --dev /path/to/speckit-preset-know-your-spec
```

or, once published:

```bash
specify extension add --from https://github.com/leejsinclair/speckit-preset-know-your-spec/archive/refs/tags/v1.1.2.zip
```

This registers `speckit.know-your-spec.check` (alias `speckit.kys-check`), wires the mandatory
`after_specify` hook, and installs the spec page helper under
`.specify/extensions/know-your-spec/scripts/` — no config file is materialized, since the checkpoint's mechanics (five
questions, fixed difficulty order, uncapped retries, zero persistence) are fixed, not tunable.

## Usage

Normally you don't invoke this directly — it fires automatically right after `/speckit-specify`
completes. You can also run it manually at any time against the active feature's `spec.md`:

```bash
/speckit-know-your-spec-check
# or the shorter alias:
/speckit-kys-check
```

## Repository layout

```text
extension.yml              Manifest: id, command, hook
commands/                  The Comprehension Checkpoint command
scripts/python/specpage.py The read-only spec page (standard library only)
.extensionignore           Excludes specs/, tests/, .specify/, .claude/ from installs
tests/
├── run.sh                 Runs both test tiers
├── deterministic/         Manifest/command-file structural checks; runs tests/unit/
├── unit/                  The spec page's renderer and server (python3 -m unittest)
└── judgment/              claude -p evals against hand-authored ground truth
    ├── fixtures/          This repo's own spec.md + synthetic specs exercising edge cases
    ├── expected/          Hand-authored ground truth (questions, answers, headings)
    └── probes/            Single-turn behavioral probes (coaching, skip/reveal, repair approval)
specs/                     This project's own Spec Kit artifacts (spec/plan/tasks) — dev-only
```

## Testing

```bash
tests/run.sh
```

Runs the deterministic tier (always) followed by the judgment tier (requires the `claude` CLI
with API access; skipped with a message if unavailable). See
[`specs/001-know-your-spec/research.md`](specs/001-know-your-spec/research.md) §13 for why this
feature uses a hybrid derivation-quality-eval + single-turn-probe design rather than a fully
simulated multi-turn session per fixture.

## Documentation

- [`specs/001-know-your-spec/spec.md`](specs/001-know-your-spec/spec.md) — the feature
  specification (user stories, requirements, success criteria).
- [`specs/001-know-your-spec/plan.md`](specs/001-know-your-spec/plan.md),
  [`research.md`](specs/001-know-your-spec/research.md),
  [`data-model.md`](specs/001-know-your-spec/data-model.md),
  [`contracts/`](specs/001-know-your-spec/contracts/) — the implementation plan and the 14
  architectural decisions behind it.
- [`specs/001-know-your-spec/quickstart.md`](specs/001-know-your-spec/quickstart.md) — an
  end-to-end validation walkthrough covering every scenario this extension supports.

## License

MIT — see [LICENSE](LICENSE).
