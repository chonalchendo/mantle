#!/usr/bin/env bash
# Mantle SessionStart hook — compile context and auto-display briefing.
# No-op when not in a Mantle project directory.

set -euo pipefail

# Only run in directories with .mantle/
if [ ! -d ".mantle" ]; then
    exit 0
fi

# Compile templates if vault state has changed (stderr for progress)
mantle compile --if-stale >/dev/null 2>&1 || true

# Export MANTLE_DIR for subsequent tool calls in this session.
# CLAUDE_ENV_FILE is provided by Claude Code for SessionStart hooks;
# each line appended here is sourced before every Bash tool call.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    MANTLE_DIR_VALUE="$(mantle where 2>/dev/null || true)"
    if [ -n "$MANTLE_DIR_VALUE" ]; then
        printf 'export MANTLE_DIR=%q\n' "$MANTLE_DIR_VALUE" >> "$CLAUDE_ENV_FILE"
    fi
fi

# Auto-display the compiled briefing
RESUME_PATH="$HOME/.claude/commands/mantle/resume.md"
if [ -f "$RESUME_PATH" ]; then
    cat "$RESUME_PATH"
fi
