---
date: '2026-04-24'
author: 110059232+chonalchendo@users.noreply.github.com
summary: Build telemetry silently records empty sessions because SessionStart hook
  never writes .mantle/.session-id
severity: high
status: open
related_issue: issue-89
related_files:
- claude/hooks/session-start.sh
- src/mantle/core/telemetry.py
- .mantle/.session-id
- .mantle/telemetry/baseline-2026-04-21.md
fixed_by: null
tags:
- type/bug
- severity/high
- status/open
---

## Description

All build telemetry files in .mantle/builds/ since 2026-04-17 (15 builds across issues 56, 61-65, 74, 76-78, 80-84, 88) carry the same stale session_id (9ce5d361-af31-4f0c-a965-c332e939c7fc), datetime.min timestamps, empty stories list, and 'No story runs detected in this build' summary. Root cause: core/telemetry.py:current_session_id() resolves CLAUDE_SESSION_ID env var → .mantle/.session-id fallback → raise. Claude Code does NOT set CLAUDE_SESSION_ID in the env (only CLAUDECODE=1, CLAUDE_CODE_ENTRYPOINT, etc.), so resolution always falls through to the fallback file. The fallback file's docstring claims 'the Mantle SessionStart hook writes from the hook payload', but claude/hooks/session-start.sh does mantle compile + MANTLE_DIR export + cat the briefing — it never reads stdin and never writes .mantle/.session-id. The fallback file (last modified 2026-04-16) holds whatever was put there once and is now 8 days stale, pointing to a session whose JSONL contains no markers for any current issue. Downstream effect: every build-finish parses an unrelated old session, finds zero matching story turns, and writes an empty report. The 84 retrospective baseline (.mantle/telemetry/baseline-2026-04-21.md) is still <fill> everywhere because every attempt to populate it produces the same empty data.

## Reproduction

1. Open a fresh Claude Code session in this repo. 2. Run env | grep CLAUDE_SESSION_ID — empty. 3. Run cat .mantle/.session-id and stat it — same UUID, last modified 2026-04-16. 4. Run mantle build-start --issue 88 then mantle build-finish --issue 88. 5. Read the resulting .mantle/builds/build-88-*.md — empty stories list, datetime.min timestamps, stale UUID.

## Expected Behaviour

build-finish writes a report with the current session's UUID, real started/finished timestamps, and one entry per story run captured during the build (with model, tokens, duration).

## Actual Behaviour

Every build file from 2026-04-17 onwards has identical session_id 9ce5d361-..., started/finished as 0001-01-01T00:00:00, empty stories list, and a 'No story runs detected' summary.
