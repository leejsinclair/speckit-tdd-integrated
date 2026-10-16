# Recorded tool-call payloads

These are the `PreToolUse` payloads Claude Code 2.1.296 sent during installation test T016
(see `specs/001-integrated-tdd/research.md`, Installation test results). They were captured
by a second, temporary hook that copied its standard input to a file.

| File | Tool | Source |
|------|------|--------|
| `edit-evidence.json` | Edit | Recorded |
| `write-evidence.json` | Write | Recorded |
| `edit-tasks.json` | Edit | Recorded |
| `write-tasks.json` | Write | Recorded |
| `edit-unrelated.json` | Edit | Recorded |
| `edit-evidence-in-tests.json` | Edit | Hand-written from `edit-evidence.json`, with the path under `tests/` |
| `multiedit-evidence.json` | MultiEdit | Hand-written |
| `multiedit-tasks.json` | MultiEdit | Hand-written |

Changes made to the recorded files: the absolute path of the throwaway project is replaced
by the token `{ROOT}`, which `tests/support.py` substitutes, and the session, prompt and
tool-use identifiers and the transcript path are replaced by fixed values.

The Claude Code version tested has no `MultiEdit` tool, so nothing could be recorded for
it. The two `multiedit-*.json` files are hand-written from the recorded `edit-tasks.json`,
with `tool_name` set to `MultiEdit` and `tool_input` holding `file_path` and an `edits`
list of `old_string`, `new_string` and `replace_all`, the shape the tool had in the
versions that shipped it. The extension's event matcher still names `MultiEdit` so that
those versions are covered.
