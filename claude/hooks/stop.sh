#!/usr/bin/env bash
# Mantle Stop hook — remind about session logging before ending.
# No-op when not in a Mantle project directory.

set -euo pipefail

# Only run in directories with .mantle/
if [ ! -d ".mantle" ]; then
    exit 0
fi

# Check if a session was logged today
TODAY=$(date +%Y-%m-%d)
SESSION_DIR=".mantle/sessions"

if [ -d "$SESSION_DIR" ]; then
    # Look for a session file from today
    TODAYS_SESSION=$(find "$SESSION_DIR" -name "${TODAY}*.md" -maxdepth 1 2>/dev/null | head -1)
    if [ -n "$TODAYS_SESSION" ]; then
        # Session already logged today — no nudge needed
        exit 0
    fi
fi

# Nudge: no session logged today
echo "Reminder: No session log saved today. Consider saving one before ending."
