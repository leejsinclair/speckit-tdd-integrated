---
name: "speckit-know-your-spec-check"
description: "Comprehension Checkpoint: five questions on spec.md's established content, one at a time, fixed increasing difficulty, coached retries, session-only."
argument-hint: "(no arguments needed — checks the active feature's spec.md)"
compatibility: "Requires spec-kit project structure with .specify/ directory; installed via the know-your-spec extension (specify extension add --dev .)"
metadata:
  author: "Lee Sinclair"
  source: "commands/speckit.know-your-spec.check.md"
aliases: ["speckit-kys-check"]
user-invocable: true
disable-model-invocation: false
---

## User Input

```text
$ARGUMENTS
```

This command needs no arguments beyond the active feature context (`.specify/feature.json`,
resolved the same way `check-prerequisites.sh` resolves it for other Spec Kit commands). If
`$ARGUMENTS` contains something anyway, read it for extra context but do not require it.

## Purpose

Run the Comprehension Checkpoint against the active feature's `spec.md`: five questions, one at a
time, at fixed increasing difficulty, judged on semantic understanding and coached until the
developer demonstrates it — never on exact wording, never with an attempt cap, and never leaving
anything behind in the repository except a developer-approved repair to `spec.md` itself. Invoked
automatically by the `after_specify` hook immediately after a spec is written, and independently
re-runnable on demand against any existing spec.

**Trigger awareness**: this may be hook-triggered (fired automatically right after
`/speckit-specify` completed) or explicit/manual. Either way the behavior below is identical —
there is no different silent-exit behavior for the automatic case, since this checkpoint has
nothing to skip quietly (unlike an assessment that might be a no-op with nothing new to report,
every finished spec has content to quiz on).

## Step 0 — Locate the spec

Resolve the active feature's `spec.md` the same way `.specify/scripts/bash/check-prerequisites.sh`
resolves it (via `.specify/feature.json`). If no `spec.md` can be resolved for the active feature,
say so plainly and stop — do not fabricate a session against a spec that doesn't exist.

## Step 1 — Derive privately, before showing anything

Before presenting question 1, work out all five questions internally. Do not show this work to
the developer — it is preparation, not part of the conversation.

For each of the five fixed difficulty levels, in this fixed order:

1. **Recognise** — the spec's purpose, a canonical term it defines, or its primary actor.
2. **Explain** — a documented user-story relationship, business rule, or happy-path ordering.
3. **Apply** — the requirements applied to a concrete scenario.
4. **Trace** — an edge case, failure condition, or acceptance path through documented behavior.
5. **Evaluate** — reconciling an implication or potential inconsistency across requirements, user
   scenarios, and success criteria.

For each level, derive:

- The question text.
- The specific `spec.md` heading whose established content the question is drawn from
  (`source_heading`).
- The expected answer that content supports (`expected_answer`) — kept private; never shown to
  the developer, even on a wrong answer.

Derive every question **solely** from content `spec.md` actually establishes — its requirements,
user stories, edge cases, or success criteria. Never invent a question the spec doesn't actually
support, and never ask about code, frameworks, libraries, database schema names, or endpoint
definitions — those belong to `plan.md`, not this checkpoint; a spec written to Spec Kit's own
"no implementation details" standard shouldn't contain that material to draw from in the first
place, but do not introduce it yourself even so.

### Format (Recognise / Explain only — questions 1 and 2)

Use multiple-choice **only** when the content supports genuinely plausible, mutually exclusive
options — i.e. distractors a developer who skimmed the spec could plausibly pick, not obviously
wrong filler. When the Recognise or Explain-level content doesn't lend itself to that (too open-
ended, no natural set of alternatives), use a free-text question instead for that level. This is
a judgment call made independently per question — question 1 could be multiple-choice while
question 2 is free-text, or vice versa, or both, or neither.

Questions 3 through 5 (Apply, Trace, Evaluate) are **always** free-text — never multiple-choice.

### If content is missing or ambiguous

If the content needed to truthfully support a question at some level is absent or ambiguous in
`spec.md`, do not invent a question anyway and do not silently edit the spec. Instead, draft a
proposed repair or clarification for that section, to be presented in Step 2.

## Step 2 — Propose any needed repairs, as one batch, before question 1

If Step 1 produced one or more proposed repairs, present all of them together now, before asking
anything — never interleaved with the quiz itself. For each proposed repair, show what would
change and why it's needed, then ask for explicit approval before touching `spec.md`.

- **If approved**: apply that repair to `spec.md` now. The corresponding question is then asked
  from this newly-established content.
- **If declined**: do not apply it. For that difficulty level, check whether different,
  already-established content elsewhere in the spec can truthfully support a question instead.
  - If yes, derive and use that alternative instead (silently — no need to explain the swap).
  - If no alternative exists anywhere in the spec, say so plainly when that level comes up in the
    quiz loop (Step 3) rather than asking an untruthful question or padding the session with
    something ungrounded. Do not fabricate a question at that level.

If Step 1 produced no repairs, skip this step entirely.

## Step 2a — Offer the spec page, once, before question 1

The developer may read `spec.md` on a page in their browser while they answer: the spec rendered
with its headings as link targets and a preview of each requirement where it is referenced. The
page is read-only. The questions, the answers and the judging all stay here in the conversation.

The page is served by `.specify/extensions/know-your-spec/scripts/python/specpage.py`, run with
`python3`. If that file or `python3` is missing, skip this step without mentioning it — the
checkpoint is complete without the page.

1. **Ask once per session**: "Open the spec on a page in your browser, or stay in chat?" Say
   that this only changes where they read the spec, not the checkpoint. Do not ask again later
   in the session.
2. **Page chosen:**
   - run `python3 .specify/extensions/know-your-spec/scripts/python/specpage.py serve --spec
     <path to spec.md> --status`;
   - if `running` is false, start it in the background with the same command minus `--status`,
     and read `address` and `anchors` from the one JSON line it prints; if a page is already
     running, use the `address` and `anchors` that `--status` returned and ask the developer to
     reload it;
   - give the developer the address exactly as printed, including its `?t=` part;
   - **never open, fetch or post to the page address yourself** — it is for the developer only.
3. **The page cannot start** (a non-zero exit with `refusals`, such as `port-unavailable`): say
   why in one line and carry on in chat. Never let the page delay or prevent question 1.
4. **Chat chosen**, or no clear choice: carry on in chat.

Then go to question 1.

## Step 3 — The question loop

Ask the five questions one at a time, strictly in the fixed order Recognise → Explain → Apply →
Trace → Evaluate. Never present a question at an earlier difficulty level than the one before it,
and never skip ahead out of order.

For each level:

1. Present the question (per the format determined in Step 1/2).
2. Wait for the developer's answer. Do not present anything else — no hints, no next question —
   until they respond.
3. Judge the answer against the private `expected_answer` for **semantic understanding**, not
   exact wording. A developer who explains the same idea in their own words has answered
   correctly.
4. If the answer strays into implementation detail (code, frameworks, libraries, database schema,
   endpoint definitions) instead of addressing the spec-level question, that is out of scope for
   this checkpoint — it belongs to planning, not here. Do not grade it as correct or incorrect
   as-is; coach the developer back toward spec-level content and re-ask the same question (this
   does not count as one of the newly-worded retries below, since the developer hasn't actually
   attempted the spec-level question yet).
5. **If correct/complete**: mark this question `passed`. Move on to the next difficulty level
   (step 1 of the loop, next level) — or to Step 4 if this was question 5.
6. **If incorrect/incomplete**:
   - Explain the specific gap in their answer, without revealing the complete expected answer.
   - Point them to the relevant `source_heading` in `spec.md`. If the spec page is running, also
     give a link straight to that heading: the page address followed by `#` and that heading's
     value in `anchors` (for example `http://127.0.0.1:8100/?t=…#edge-cases`). Take the anchor
     from `anchors`; never make one up.
   - Present a **newly-worded** question at the *same* difficulty level — never the identical
     phrasing twice in a row.
   - Let the developer answer again. Repeat this sub-step with no limit on the number of
     attempts. A retry never counts as, or replaces, one of the five levels — the session always
     has exactly five levels to get through, however many retries any one of them takes.
   - At any point while stuck on a question, the developer may explicitly ask to **skip** or have
     the answer **revealed**. If they do: reveal the expected answer if asked, mark this question
     `skipped` (not `passed`), and move on to the next difficulty level. This is distinct from
     ending the whole session — only this one question is affected.
   - At any point, the developer may instead ask to **stop the whole session**. If they do, end
     immediately — see Step 5 (early exit).

## Step 4 — Completion summary

Once all five difficulty levels have been resolved (each is either `passed` or `skipped`),
present a concise, spoken-in-conversation-only summary distinguishing which questions were passed
from which were skipped (e.g. by level: Recognise ✓ passed, Explain ✓ passed, Apply ⤼ skipped,
Trace ✓ passed, Evaluate ✓ passed). Do not write this summary, or any part of the session, to
`spec.md` or any other file.

If you started the spec page in Step 2a, stop it now with
`python3 .specify/extensions/know-your-spec/scripts/python/specpage.py serve --spec <path to
spec.md> --stop`.

## Step 5 — Early exit

The developer can end the session at any point before completion, for any reason, simply by
saying so. If they do: acknowledge it and stop immediately. Do not write a partial summary, a
partial record, or anything else about the session to any file — there is nothing to clean up,
because nothing was ever written in the first place. If you started the spec page in Step 2a,
stop it with `python3 .specify/extensions/know-your-spec/scripts/python/specpage.py serve --spec
<path to spec.md> --stop`.

## Invariants (apply throughout every step above)

- **Never persist.** This entire checkpoint — every question, every answer, every judgment,
  every retry count, the completion summary — exists only in this conversation. Never write any
  of it to `spec.md` or to any other file in the repository, under any circumstance, for any
  reason (including "helpfully" saving a transcript or notes). The **only** exception is an
  explicitly developer-approved repair to `spec.md`'s own established content from Step 2 — that
  is a deliberate edit to the spec's substance, not checkpoint bookkeeping, and it only ever
  happens with the developer's explicit prior approval. The spec page (Step 2a) does not change
  this: it only shows `spec.md`, it has no way to change anything, and it keeps nothing in the
  repository — while it runs it holds its own address in the system's temporary folder and
  removes it when it stops.
- **Never block.** This command's outcome — whether it completes, is exited early, or is never
  run at all — must never gate or be required by any other Spec Kit command. Running `/speckit-
  plan`, `/speckit-tasks`, or `/speckit-implement` afterward behaves identically whether or not
  this checkpoint ever ran or how it went.
- **Never advance silently.** A difficulty level is only ever left behind via an answer actually
  judged to demonstrate understanding, or an explicit skip/reveal — never on an unaddressed wrong
  answer, and never without the developer's answer (or skip request) actually being processed.
