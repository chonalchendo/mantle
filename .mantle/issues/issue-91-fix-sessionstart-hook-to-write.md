---
title: Fix SessionStart hook to write .mantle/.session-id from payload
status: verified
slice:
- claude-code
- tests
story_count: 1
verification: null
blocked_by: []
skills_required:
- python-314
tags:
- type/issue
- status/verified
acceptance_criteria: []
---

## Parent PRD

product-design.md, system-design.md

## Why

Build telemetry has been silently broken since 2026-04-17. All 15 build files in `.mantle/builds/` (issues 56, 61–65, 74, 76–78, 80–84, 88) carry the same stale session UUID, `datetime.min` timestamps, empty `stories:` list, and "No story runs detected." Bug filed in `.mantle/bugs/2026-04-24-build-telemetry-silently-recor.md`.

Root cause: `core/telemetry.py:current_session_id()` resolves `CLAUDE_SESSION_ID` env var → `.mantle/.session-id` fallback → raise. Claude Code doesn't set `CLAUDE_SESSION_ID` in the environment, so resolution always falls through to the file. The fallback file's docstring claims the SessionStart hook writes it from the hook payload, but `claude/hooks/session-start.sh` only does `mantle compile` + `MANTLE_DIR` export + briefing display. It never reads stdin and never writes `.mantle/.session-id`. The file just holds whatever was put there once 8 days ago.

Two reasons this fix is high-leverage:
1. Issue 89 (A/B harness) depends on telemetry actually capturing per-story model + token + duration data. Cannot ship without this fix.
2. The session-identity primitive being repaired here is the same one identified in the GSD scout (decision 4 of brainstorm `2026-04-22-gsd-scout-backlog-reshape.md`) as the foundation for issue 85 (cross-repo). Fixing the hook now lays the groundwork for 85's shape session.

## What to build

Patch `claude/hooks/session-start.sh` to:
1. Read the SessionStart hook JSON payload from stdin.
2. Extract the `session_id` field (and any other useful identity fields Claude Code provides — `transcript_path`, `cwd`).
3. Write the `session_id` to `<project_dir>/.mantle/.session-id`, atomically (temp file + rename).
4. Continue to do the existing work (compile, MANTLE_DIR export, briefing).

The shell needs to be careful: SessionStart's stdin payload is JSON, so use `jq` if available with a graceful fallback for environments without `jq`. The hook must remain a no-op when not in a Mantle project directory.

Optional follow-on (not required for this issue): once the file is being maintained, update `core/telemetry.py:current_session_id()` docstring so it accurately describes the resolution chain.

## Acceptance criteria

- [ ] ac-01: `claude/hooks/session-start.sh` reads JSON from stdin and extracts the `session_id` field.
- [ ] ac-02: The hook writes the session id to `<project_dir>/.mantle/.session-id` atomically (temp file + rename), preserving the existing no-op behaviour outside Mantle projects.
- [ ] ac-03: After running `mantle install --global` and starting a fresh Claude Code session, `.mantle/.session-id` contains the current session UUID, not a stale one.
- [ ] ac-04: A subsequent `mantle build-start --issue NN` followed by some real story work and `mantle build-finish --issue NN` produces a build file with the current session's UUID, real started/finished timestamps, and one entry per story run.
- [ ] ac-05: A test exercises the hook script end-to-end (feed JSON on stdin, assert the file is written with the right value) using a temp working directory.
- [ ] ac-06: `just check` passes.

## Blocked by

None. Blocks issue 89 (A/B harness) — the harness needs telemetry to actually capture data.

## User stories addressed

- As a Mantle maintainer, I want every `/mantle:build` run to write real telemetry so that A/B comparisons and per-stage cost tracking actually have data.
- As a future me running issue 89's A/B harness, I want the prerequisite session-identity primitive working so the harness has something to read.

## Notes

- Bug source: `.mantle/bugs/2026-04-24-build-telemetry-silently-recor.md`.
- Adjacent to brainstorm `2026-04-22-gsd-scout-backlog-reshape.md` decision 4 — fixing this also lays the foundation for issue 85's cross-repo session-identity work.