#!/usr/bin/env bash
# Mantle PostToolUse hook — auto-format modified files after Write/Edit.
# No-op when not in a Mantle project directory or no formatter is available.
#
# Claude Code passes hook data as JSON on stdin:
#   { "tool_input": { "file_path": "/path/to/file" }, ... }

set -euo pipefail

# Only run in directories with .mantle/
if [ ! -d ".mantle" ]; then
    exit 0
fi

# Read JSON from stdin and extract file path
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

# Auto-format based on file extension
case "$FILE_PATH" in
    *.py)
        if command -v ruff &>/dev/null; then
            ruff format --quiet "$FILE_PATH" 2>/dev/null || true
            ruff check --fix --quiet "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    *.js|*.ts|*.jsx|*.tsx|*.json|*.css|*.md)
        if command -v prettier &>/dev/null; then
            prettier --write --log-level silent "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    *.go)
        if command -v gofmt &>/dev/null; then
            gofmt -w "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
    *.rs)
        if command -v rustfmt &>/dev/null; then
            rustfmt --quiet "$FILE_PATH" 2>/dev/null || true
        fi
        ;;
esac
