#!/usr/bin/env bash
# PostToolUse hook: render the Mermaid blocks of an edited Markdown file and
# report a parse failure back to Claude (exit 2).
file=$(jq -r '.tool_input.file_path // empty')
case "$file" in *.md) ;; *) exit 0 ;; esac
[ -f "$file" ] && grep -q '```mermaid' "$file" || exit 0

out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
if ! log=$(npx -y @mermaid-js/mermaid-cli -i "$file" -o "$out/out.svg" 2>&1); then
  echo "Mermaid render failed for $file:" >&2
  echo "$log" | tail -n 20 >&2
  exit 2
fi
