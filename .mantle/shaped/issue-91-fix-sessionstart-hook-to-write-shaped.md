---
issue: 91
title: Fix SessionStart hook to write .mantle/.session-id from payload
approaches:
- jq with python3 fallback (chosen)
- new mantle write-session-id CLI command (rejected — overkill for a one-line atomic
  write)
chosen_approach: jq with python3 fallback
appetite: small batch
open_questions: []
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-24'
updated: '2026-04-24'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Why

`claude/hooks/session-start.sh` does not read its stdin payload, so `.mantle/.session-id` is never refreshed. `core/telemetry.py:current_session_id()` falls back to that file when `CLAUDE_SESSION_ID` is unset (which it always is in Claude Code), so every build since 2026-04-17 carries the same stale UUID. Fixing the hook unblocks issue 89 (A/B harness needs real telemetry) and lays the foundation for issue 85 (cross-repo session identity).

## Approaches considered

### A — jq with python3 fallback (chosen)

Modify `claude/hooks/session-start.sh` to read stdin (when a payload is present), extract `session_id` via `jq -r '.session_id // empty'` if `jq` is on PATH, else fall back to `python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])"`. Write atomically via `mktemp` + `mv` into `.mantle/.session-id`. The whole block is wrapped so a malformed payload never breaks the hook (it preserves no-op behaviour). Extend `tests/hooks/test_session_start.py` with stdin-feeding tests for both the jq path and the python3-fallback path.

- Appetite: small batch (~15 LOC of bash + ~3 small tests)
- Tradeoffs: keeps everything in shell — easy to read alongside the existing hook; no new files; reuses the existing `_run_hook` helper for tests.
- Rabbit holes: `set -euo pipefail` is active; any failable command in the new block must end in `|| true`. mktemp must place the temp file on the same filesystem as the destination (`.mantle/`) so the `mv` is rename-atomic.
- No-gos: does not change `current_session_id()` docstring (optional follow-on per issue body); does not extract `transcript_path`/`cwd` (ACs only require `session_id`).

### B — new `mantle write-session-id` CLI command (rejected)

Add a CLI subcommand that the hook invokes via `mantle write-session-id < payload`. Pydantic validates the JSON, atomicwrites handles the atomic file write.

- Appetite: small batch but materially larger.
- Reject: a permanent CLI surface for what is effectively one shell line is over-engineered. Pull complexity down (`software-design-principles`) — into the hook, not into a new CLI.

## Chosen approach: A

A is the smallest appetite that satisfies all ACs and matches the issue body's explicit hint ('use jq if available with a graceful fallback').

## Code design

### Strategy

Extend `claude/hooks/session-start.sh` with a single new block — placed after the `.mantle/` existence check, before the `mantle compile` call so the file is updated as early as possible:

1. If stdin is a TTY (interactive), skip — there is no payload.
2. Read stdin into a variable: `payload=$(cat)`.
3. If `payload` is non-empty:
   - Try `jq -r '.session_id // empty' <<<"$payload" 2>/dev/null` first.
   - Fall back to `python3 -c '...'` if `jq` returns empty or is missing.
4. If the extracted `session_id` is non-empty:
   - `tmp=$(mktemp '.mantle/.session-id.XXXXXX')`
   - `printf '%s' "$session_id" > "$tmp"` then `mv "$tmp" '.mantle/.session-id'`
5. The whole block uses `|| true` and explicit empty checks so it never aborts the hook.

Tests added to `tests/hooks/test_session_start.py` (extending the existing `TestSessionStartHook` class):

- `test_writes_session_id_from_stdin_payload` — feeds `{\"session_id\":\"abc-123\"}`, asserts `.mantle/.session-id` reads `abc-123`.
- `test_writes_session_id_with_jq_unavailable` — strips `jq` from PATH so the python3 fallback runs; asserts the file is still written.
- `test_no_session_file_when_payload_empty` — runs hook with empty stdin; asserts `.mantle/.session-id` is not created.
- `test_no_session_file_when_payload_not_json` — feeds garbage; asserts the hook still exits 0 and does not write the file.

The existing `_run_hook` helper takes an optional `input=` keyword so tests can pass stdin without changing the helper signature significantly (a small extension).

### Fits architecture by

- Lives entirely in the `claude-code` slice (`claude/hooks/session-start.sh`) and the `tests` slice (`tests/hooks/test_session_start.py`). No `core/` or `cli/` change required.
- Honours the existing 'no-op outside Mantle project' contract — the new block runs after the `[ ! -d \".mantle\" ] && exit 0` guard.
- Honours `set -euo pipefail` by wrapping every failable command in `|| true` and explicit empty checks.
- Pulls complexity down (software-design-principles): callers (Claude Code session-start lifecycle) don't need to know about `.mantle/.session-id` at all.
- Defines errors out (software-design-principles): malformed payload, missing jq, and non-TTY-but-empty stdin all degrade to a no-op rather than raising.

### Does not

- Does not modify `core/telemetry.py:current_session_id()` docstring (issue body explicitly defers this as optional follow-on).
- Does not extract `transcript_path` or `cwd` from the payload (ACs only require `session_id`).
- Does not add `jq` as a hard dependency — `python3` is already required by the project, so it's a safe fallback.
- Does not validate the UUID shape of `session_id` — Claude Code is the source of truth; trust the boundary.
- Does not change `mantle install --global` itself — the hook ships in the same place; no installer change needed.
- Does not migrate or migrate-test the old fallback file — it just gets overwritten on the next session start.

## Open questions

None.