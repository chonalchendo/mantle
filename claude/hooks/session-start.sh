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

# Auto-display the compiled briefing
RESUME_PATH="$HOME/.claude/commands/mantle/resume.md"
if [ -f "$RESUME_PATH" ]; then
    cat "$RESUME_PATH"
fi
