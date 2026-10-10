#!/usr/bin/env bash
# Set up a development environment for this repository. Safe to re-run.
set -euo pipefail

missing=0
need() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "ok       $1"
  else
    echo "MISSING  $1  ($2)"
    missing=1
  fi
}

echo "Checking tools:"
need specify "Spec Kit CLI, used to install and resolve the packages"
need npx "Node.js, used to run the Mermaid CLI and the Playwright MCP server"
need jq "used by the hooks in .claude/settings.json"
need claude "Claude Code CLI, used to register MCP servers"
need python3 "used by scripts/python/c4_layout.py and its tests"

if [ "$missing" -ne 0 ]; then
  echo "Install the missing tools and run this script again." >&2
  exit 1
fi

echo
echo "Registering MCP servers:"
if claude mcp get playwright >/dev/null 2>&1; then
  echo "ok       playwright (already registered)"
else
  claude mcp add playwright -- npx @playwright/mcp@latest
fi

echo
echo "Enabling git hooks:"
git -C "$(dirname "$0")/.." config core.hooksPath .githooks
echo "ok       core.hooksPath = .githooks (pre-commit runs the tests)"
