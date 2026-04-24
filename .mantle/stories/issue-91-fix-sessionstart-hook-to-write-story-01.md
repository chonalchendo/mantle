---
issue: 91
title: Patch session-start hook to write .mantle/.session-id from stdin payload
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle maintainer, I want every `/mantle:build` run to write real telemetry so that A/B comparisons and per-stage cost tracking actually have data.

## Depends On

None — independent (single story).

## Approach

Extend the existing `claude/hooks/session-start.sh` with a small, fail-soft block that reads stdin (when present), extracts `session_id` via `jq` if available else `python3`, and writes `.mantle/.session-id` atomically via `mktemp` + `mv`. Extend the existing `tests/hooks/test_session_start.py` (`TestSessionStartHook`) with stdin-feeding tests for both extraction paths and the no-op edge cases. Follows the existing hook pattern (`set -euo pipefail` plus `|| true` guards on every failable command) and the existing test pattern (`_run_hook` helper using `subprocess.run` with cwd=tmp_path).

## Implementation

### claude/hooks/session-start.sh (modify)

Insert a new block immediately after the `[ ! -d ".mantle" ]` guard at line 8 and before the `mantle compile --if-stale` call at line 13. The block must:

1. Skip if stdin is a TTY: `[ -t 0 ] && PAYLOAD_PRESENT=0 || PAYLOAD_PRESENT=1` (or `if [ ! -t 0 ]`).
2. When a payload is present, read it: `PAYLOAD=$(cat || true)`.
3. Extract `session_id` with `jq` first, fallback to `python3`:
   ```bash
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
   ```
4. If `SESSION_ID` is non-empty, write atomically:
   ```bash
   if [ -n "$SESSION_ID" ]; then
       TMP=$(mktemp ".mantle/.session-id.XXXXXX") || TMP=""
       if [ -n "$TMP" ]; then
           printf '%s' "$SESSION_ID" > "$TMP"
           mv "$TMP" ".mantle/.session-id"
       fi
   fi
   ```

The whole block must never abort the hook — every failable command ends in `|| true` or is wrapped in an `if [ -n ... ]` check. `mktemp` places the temp file inside `.mantle/` (same filesystem as the destination) so `mv` is a true atomic rename.

#### Design decisions

- **jq before python3 fallback**: jq is the standard tool in shell hooks; python3 is the safety net since the project requires Python 3.14+ anyway. Order matters because jq is faster and produces no extra process overhead beyond what shell already needs.
- **Atomic via `mktemp` + `mv` in same dir**: required by AC-02. Same-directory mktemp guarantees `mv` is rename-atomic on POSIX — no partially-written file is ever visible at the destination path.
- **TTY guard skips interactive runs**: the hook also fires for `claude` started with no stdin payload (e.g. local invocation outside Claude Code). `[ -t 0 ]` cleanly skips that case without touching the file.
- **Pull complexity down**: `core/telemetry.py:current_session_id()` continues to read `.mantle/.session-id` exactly as today. The hook absorbs all the parse/atomic-write complexity; callers see only the file.

### tests/hooks/test_session_start.py (modify)

Extend `_run_hook` with an optional `input` keyword (passes through to `subprocess.run(..., input=input)`). Add 4 new tests inside the existing `TestSessionStartHook` class:

```python
def test_writes_session_id_from_stdin_payload(self, tmp_path: Path) -> None:
    (tmp_path / ".mantle").mkdir()
    payload = '{"session_id": "abc-123-def", "transcript_path": "/x", "cwd": "/y"}'
    result = _run_hook(tmp_path, input=payload)
    assert result.returncode == 0
    assert (tmp_path / ".mantle" / ".session-id").read_text() == "abc-123-def"

def test_writes_session_id_with_jq_unavailable(self, tmp_path: Path) -> None:
    (tmp_path / ".mantle").mkdir()
    # Build a PATH containing python3 but not jq.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    py = shutil.which("python3")
    assert py is not None
    (bin_dir / "python3").symlink_to(py)
    env = {"PATH": str(bin_dir), "HOME": os.environ.get("HOME", "")}
    payload = '{"session_id": "fallback-uuid"}'
    result = _run_hook(tmp_path, input=payload, env=env)
    assert result.returncode == 0
    assert (tmp_path / ".mantle" / ".session-id").read_text() == "fallback-uuid"

def test_no_session_file_when_payload_empty(self, tmp_path: Path) -> None:
    (tmp_path / ".mantle").mkdir()
    result = _run_hook(tmp_path, input="")
    assert result.returncode == 0
    assert not (tmp_path / ".mantle" / ".session-id").exists()

def test_no_session_file_when_payload_not_json(self, tmp_path: Path) -> None:
    (tmp_path / ".mantle").mkdir()
    result = _run_hook(tmp_path, input="not json at all")
    assert result.returncode == 0
    assert not (tmp_path / ".mantle" / ".session-id").exists()
```

Update `_run_hook` signature:

```python
def _run_hook(
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    input: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_BASH, str(HOOK_SCRIPT)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
        input=input,
    )
```

#### Design decisions

- **Reuse existing helper, don't fork a parallel runner**: `_run_hook` is already the canonical way to invoke the hook in tests. Adding one keyword arg keeps the test infrastructure flat.
- **No mock of `mantle compile` / `mantle where`**: those calls already end in `|| true` in the hook, so they no-op silently when `mantle` is unreachable on the test PATH; tests don't need to stub them.
- **No atomicity test**: mktemp+mv into the same dir is the standard POSIX recipe for atomic writes. Verifying atomicity reliably from a single-threaded test is impractical and adds noise without buying coverage.

## Tests

### tests/hooks/test_session_start.py (modify)

- **test_writes_session_id_from_stdin_payload**: feeds valid JSON `{"session_id": "abc-123-def"}` to hook stdin; asserts `.mantle/.session-id` exists and contains `"abc-123-def"` exactly.
- **test_writes_session_id_with_jq_unavailable**: builds a PATH with `python3` but no `jq`; feeds same payload; asserts file is still written via the python3 fallback.
- **test_no_session_file_when_payload_empty**: feeds empty stdin; asserts hook exits 0 and `.mantle/.session-id` is not created (preserves no-op when no payload arrives).
- **test_no_session_file_when_payload_not_json**: feeds non-JSON garbage; asserts hook exits 0 and `.mantle/.session-id` is not created (graceful degradation, set -euo pipefail not violated).