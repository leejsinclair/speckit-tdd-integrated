# Changelog

## 1.1.2 - 2026-10-08

- The command now stops the spec page by the helper's full installed path; the short form it
  used before would not have run.
- The page's runtime file is never written inside the project, even when `TMPDIR` points there:
  the helper uses a place outside it, or refuses to start (`no-runtime-dir`).
- `specs/001-know-your-spec/` now covers the page: User Story 4, FR-018 to FR-024, SC-006 to
  SC-008, and matching updates to the plan, tasks and contracts.

## 1.1.1 - 2026-10-08

- The spec page listens on every interface (`0.0.0.0`) by default, so a port forwarded from a
  container or remote machine reaches it. `--host 127.0.0.1` restores the old behaviour.

## 1.1.0 - 2026-10-08

- Optional read-only spec page. Before question 1 the checkpoint asks once whether to open
  `spec.md` on a page in the browser; coaching hints then link straight to the heading they point
  at. The quiz stays in the conversation.
- New helper `scripts/python/specpage.py` (standard library only): serves behind a
  one-time key, has no route that changes anything, and keeps nothing in the repository.
- Mermaid diagrams in the spec are drawn on the page by `mermaid@11`, loaded from the jsDelivr
  CDN only when the spec has a diagram. If it cannot be loaded, the diagram's source is shown.
- `python3` is declared as an optional tool. Without it the checkpoint behaves as in 1.0.0.

## 1.0.0 - 2026-09-22

Initial release.

- `speckit.know-your-spec.check` command (alias `speckit.kys-check`): a five-question
  Comprehension Checkpoint against `spec.md`, at fixed increasing difficulty (Recognise → Explain
  → Apply → Trace → Evaluate), judged semantically, coached with uncapped retries, explicit
  per-question skip/reveal, and a session-only completion summary.
- Mandatory `after_specify` hook — fires automatically immediately after a spec is finished, with
  no confirmation prompt.
- Developer-approval-gated repair/clarification flow for `spec.md` sections too thin or ambiguous
  to truthfully support a question, batched as one consolidated request before question 1.
- Zero persistence: nothing about a checkpoint session is ever written to `spec.md` or any other
  repository file, aside from an explicitly approved content repair.
- No config file, no companion preset — the checkpoint's mechanics are fixed by design.
