---
issue: 92
title: 'CLI: mantle stage-begin command'
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a Mantle command template author, I want a single-line `mantle stage-begin <name>` CLI command, so that I can emit a stage mark from any `/mantle:*` template without knowing the internals of the telemetry module.

## Depends On

Story 1 — uses `core.stages.record_stage`.

## Approach

Register one new cyclopts command under `GROUPS["impl"]` in `src/mantle/cli/main.py`, following the exact pattern of the sibling `build-start` / `build-finish` commands (lines 1721-1760). No flags, one positional argument. Body is a three-line delegator to `stages.record_stage`.

## Implementation

### src/mantle/cli/main.py (modify)

Add an import near the other `mantle.core` imports (grouped by package):

```python
from mantle.core import stages
```

Add the command. Place it adjacent to `build-start` and `build-finish` (after line ~1760) so the impl group is visually cohesive:

```python
@app.command(name=\"stage-begin\", group=GROUPS[\"impl\"])
def stage_begin_command(
    name: Annotated[
        str,
        Parameter(
            help=\"Stage name (e.g. 'shape', 'implement', 'verify').\",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name=\"--path\",
            help=\"Project directory. Defaults to cwd.\",
        ),
    ] = None,
) -> None:
    \"\"\"Mark the start of a named stage in the current session.\"\"\"
    stages.record_stage(name, project_dir=path)
```

#### Design decisions

- **Single positional arg, not `--name`**: the command is called from shell-mode templates like `mantle stage-begin shape`. Positional is shorter and matches the ergonomics of `git commit -m`.
- **Optional `--path`**: matches every other `impl`-group command; lets tests drive without chdir. Defaults to cwd.
- **No validation beyond `record_stage`'s non-empty check**: parity harness catches typos in template strings at snapshot-review time — the CLI doesn't need to enforce a stage allow-list.
- **Under `GROUPS[\"impl\"]`**: same group as `build-start` / `build-finish`. These are implementation-plumbing commands, not user-facing ones.

## Tests

### tests/cli/test_stage_begin.py (new file)

Use `pytest`, `tmp_path`, and cyclopts's test-ready app wiring (mirror `tests/cli/test_builds.py` if it exists; otherwise call the function directly).

- **test_stage_begin_writes_mark**: monkeypatch `CLAUDE_SESSION_ID`; call `stage_begin_command('shape', path=tmp_path)`; assert `tmp_path/.mantle/telemetry/stages-<sid>.jsonl` exists and contains one JSON line with `stage == 'shape'`.
- **test_stage_begin_noop_outside_session**: no `CLAUDE_SESSION_ID`, no `.session-id` file; `stage_begin_command('shape', path=tmp_path)` returns None without error and writes nothing.
- **test_stage_begin_rejects_empty**: `stage_begin_command('', path=tmp_path)` raises `ValueError`.
- **test_stage_begin_roundtrip**: record three stages via `stage_begin_command`; call `core.stages.read_stages(sid, tmp_path)`; assert three marks in chronological order.

#### Test fixture requirements

- `tmp_path` for every filesystem call — never touch `~/.claude/` or real `.mantle/`.
- `monkeypatch.setenv('CLAUDE_SESSION_ID', 'test-sid')` to avoid touching real hook state.
- No subprocess spawning — call the function directly.