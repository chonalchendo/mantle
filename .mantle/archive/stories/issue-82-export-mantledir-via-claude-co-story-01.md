---
issue: 82
title: Export MANTLE_DIR via CLAUDE_ENV_FILE in session-start hook + build.md fallback
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user on API billing, I want `MANTLE_DIR` resolved once per Claude Code session so that high-frequency commands like `/mantle:build` do not repeatedly pay the latency and token cost of re-running `mantle where` to resolve a session-stable path.

## Depends On

None — single-story issue.

## Approach

Follow Claude Code's documented `CLAUDE_ENV_FILE` mechanism for SessionStart hooks: any `export VAR=value` line appended to `$CLAUDE_ENV_FILE` during SessionStart is sourced before every subsequent Bash tool call in that session. The existing `claude/hooks/session-start.sh` is the right seam — it already gates on `.mantle/` presence and runs `mantle compile --if-stale`. Add one new block that appends `export MANTLE_DIR=$(mantle where)` to `$CLAUDE_ENV_FILE` when that var is set. On the prompt side, update `claude/commands/mantle/build.md` Step 1 to use `${MANTLE_DIR:-$(mantle where)}` so the hook-exported value is reused when present and the prompt falls back gracefully when it is not. Tests extend the existing `tests/hooks/test_session_start.py` suite using its `_run_hook` helper, passing a fake `CLAUDE_ENV_FILE` in the environment and asserting the file contents.

## Implementation

### claude/hooks/session-start.sh (modify)

After the `mantle compile --if-stale` line and before the resume-briefing `cat` block, insert:

```bash
# Export MANTLE_DIR for subsequent tool calls in this session.
# CLAUDE_ENV_FILE is provided by Claude Code for SessionStart hooks;
# each line appended here is sourced before every Bash tool call.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    MANTLE_DIR_VALUE="$(mantle where 2>/dev/null || true)"
    if [ -n "$MANTLE_DIR_VALUE" ]; then
        printf 'export MANTLE_DIR=%q\n' "$MANTLE_DIR_VALUE" >> "$CLAUDE_ENV_FILE"
    fi
fi
```

Rationale for each decision:

- **`${CLAUDE_ENV_FILE:-}` default-empty**: keeps `set -u` safety if ever added. Right now the script runs under `set -euo pipefail`, so referencing an unset var is already an error — the `:-}` form makes the gate safe.
- **`mantle where 2>/dev/null || true`**: `mantle where` could theoretically fail (missing install, corrupt state). In that case we silently skip the export rather than aborting the hook, because failing the SessionStart would make the whole session unusable.
- **`printf '%q'` quoting**: protects against paths with spaces or special chars when the file is later sourced.
- **Single appended line, not file overwrite**: CLAUDE_ENV_FILE may already contain other hooks' exports; we append, never truncate.

### claude/commands/mantle/build.md (modify)

In Step 1 — Prerequisites, change the single line:

```
    MANTLE_DIR=\$(mantle where)
```

to:

```
    MANTLE_DIR=\"\${MANTLE_DIR:-\$(mantle where)}\"
```

Leave the surrounding text unchanged. The downstream instruction (\"All subsequent Read/Grep/Glob calls in this prompt must use `\$MANTLE_DIR/...`\") stays as-is and becomes the motivation for AC-02: when `MANTLE_DIR` is already in the environment, the subprocess call to `mantle where` is skipped.

### tests/hooks/test_session_start.py (modify)

Add two new test methods to `TestSessionStartHook`:

- `test_exports_mantle_dir_to_claude_env_file(tmp_path)`:
  - Create `.mantle/` in `tmp_path`
  - Create an empty file `tmp_path / \"env_file\"`
  - Set `CLAUDE_ENV_FILE=<that path>` in the env passed to `_run_hook`
  - Run the hook
  - Assert the file contains exactly one line matching `export MANTLE_DIR=...`
  - Assert the captured path is a valid absolute directory (the result of `mantle where` in `tmp_path`, which resolves to `tmp_path/.mantle`).

- `test_does_not_write_when_claude_env_file_unset(tmp_path)`:
  - Create `.mantle/` in `tmp_path`
  - Pass env WITHOUT `CLAUDE_ENV_FILE`
  - Assert exit code 0 (hook does not crash)
  - Assert `tmp_path` contains no unexpected files beyond `.mantle/`

Both tests run the real `mantle where` subprocess — they are integration tests of the bundled bash script, not unit tests of a Python helper. Use `inline_snapshot` only if asserting the exact exported line format (the absolute path captured by `mantle where` depends on `tmp_path` and will differ per run, so a regex/prefix check is cleaner than a snapshot here — prefer a plain assertion).

#### Design decisions

- **Extend existing test class, don't create a new file**: the hook already has a test module; keeping tests co-located under `TestSessionStartHook` avoids duplication.
- **Integration test, not unit test**: the hook is a bash script. Subprocess invocation with a real `mantle where` call exercises the full contract. The existing tests in the file use the same pattern.
- **No inline_snapshot for this case**: the absolute path in `$(mantle where)` varies per `tmp_path`; capturing it would produce a brittle snapshot. Use a structural assertion (line starts with `export MANTLE_DIR=` and the path exists).

## Tests

### tests/hooks/test_session_start.py (modify)

- **test_exports_mantle_dir_to_claude_env_file**: hook writes exactly one `export MANTLE_DIR=<path>` line to `$CLAUDE_ENV_FILE` when it is set and `.mantle/` exists.
- **test_does_not_write_when_claude_env_file_unset**: hook exits 0 and writes no env file when `CLAUDE_ENV_FILE` is unset.