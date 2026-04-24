#!/usr/bin/env bash
# Mantle SessionStart hook — compile context and auto-display briefing.
# No-op when not in a Mantle project directory.

set -euo pipefail

# Only run in directories with .mantle/
if [ ! -d ".mantle" ]; then
    exit 0
fi

# Read session_id from Claude Code's JSON stdin payload and persist it.
# This keeps .mantle/.session-id current so telemetry uses the right UUID.
if [ ! -t 0 ]; then
    PAYLOAD=$(cat || true)
    SESSION_ID=""
    if [ -n "$PAYLOAD" ]; then
        if command -v jq >/dev/null 2>&1; then
            SESSION_ID=$(printf '%s' "$PAYLOAD" | jq -r '.session_id // empty' 2>/dev/null || true)
        fi
        if [ -z "$SESSION_ID" ] && command -v python3 >/dev/null 2>&1; then
            SESSION_ID=$(printf '%s' "$PAYLOAD" | python3 -c 'import json,sys
try:
    d=json.load(sys.stdin)
    print(d.get("session_id",""))
except Exception:
    pass' 2>/dev/null || true)
        fi
    fi
    if [ -n "$SESSION_ID" ]; then
        TMP=$(mktemp ".mantle/.session-id.XXXXXX") || TMP=""
        if [ -n "$TMP" ]; then
            printf '%s' "$SESSION_ID" > "$TMP"
            mv "$TMP" ".mantle/.session-id"
        fi
    fi
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
