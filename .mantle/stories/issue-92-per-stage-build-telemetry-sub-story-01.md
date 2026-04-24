---
issue: 92
title: Core stages module — StageMark, StageWindow, record_stage, read_stages, windows_for_session
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a Mantle maintainer evaluating per-stage model choices, I want a standalone stage-marking primitive that records `{stage, at}` events to a per-session JSONL, so that every LLM-invoking Mantle command (inside or outside `/mantle:build`) can attribute its token usage to a named stage.

## Depends On

None — independent. Foundation module other stories build on.

## Approach

Create a new `core/stages.py` module that owns the stage-mark primitive: two Pydantic models (`StageMark`, `StageWindow`), one side-effecting writer (`record_stage`), one reader (`read_stages`), and one pure window-builder (`windows_for_session`). Follows the deep-module pattern in `core/telemetry.py` — a narrow public interface over JSONL append/parse + stdlib `datetime`. Co-locates storage at `.mantle/telemetry/stages-<session_id>.jsonl` alongside the existing `baseline-*.md/.json` artefacts so the telemetry folder is the single home for time-series data.

## Implementation

### src/mantle/core/stages.py (new file)

Module docstring: "Stage-mark primitive — per-session JSONL of named stage-begin events."

Imports: `json`, `datetime` (from datetime), `Path` (from pathlib), `pydantic`, `mantle.core.telemetry` (for `current_session_id`).

Constants:

```python
_TELEMETRY_SUBDIR = "telemetry"
_STAGES_FILENAME_FMT = "stages-{session_id}.jsonl"
```

Models:

```python
class StageMark(pydantic.BaseModel, frozen=True):
    """One stage-begin event parsed from stages-<session_id>.jsonl.

    Attributes:
        stage: Stage name (e.g. 'shape', 'implement', 'verify').
        at: Wall-clock timestamp of the stage-begin event.
    """

    stage: str
    at: datetime


class StageWindow(pydantic.BaseModel, frozen=True):
    """Half-open [start, end) window attributed to a stage.

    Attributes:
        stage: Stage name.
        start: Start of the window (inclusive).
        end: End of the window (exclusive). Set to the next mark's
            `at`, or to the session-end timestamp for the last mark.
    """

    stage: str
    start: datetime
    end: datetime
```

Functions (all public):

```python
def record_stage(stage: str, project_dir: Path | None = None) -> None:
    \"\"\"Append a StageMark record for the current Claude Code session.

    Resolves the session id via telemetry.current_session_id. Creates
    `<project_dir>/.mantle/telemetry/` if absent. Silently no-ops
    (returns None) when no session id is resolvable — matches the
    behaviour of `build-start` so template edits never block a
    shell-mode caller outside Claude Code.

    Args:
        stage: Non-empty stage name. Validated only as 'non-empty';
            typos are caught by the parity harness at snapshot review.
        project_dir: Project directory. Defaults to cwd.
    \"\"\"
```

Behaviour: strip the stage argument; if empty after stripping, raise `ValueError("stage must be non-empty")`. Attempt `telemetry.current_session_id(project_dir)`; on `RuntimeError`, return (no-op). Build path `<project_dir>/.mantle/telemetry/stages-<session_id>.jsonl`; `mkdir(parents=True, exist_ok=True)` on its parent. Append one line: `json.dumps({"stage": stage, "at": datetime.now(UTC).isoformat()}) + "\n"`. Use `open(..., "a", encoding="utf-8")`.

```python
def read_stages(
    session_id: str,
    project_dir: Path | None = None,
) -> tuple[StageMark, ...]:
    \"\"\"Parse the per-session stage-mark JSONL in chronological order.\"\"\"
```

Behaviour: construct the same path. If absent, return `()`. Read line-by-line; for each non-empty line, try `json.loads` → `StageMark(**record)`; on `json.JSONDecodeError`, `pydantic.ValidationError`, `TypeError`, `KeyError` silently skip (matches `telemetry._parse_assistant_line`). Return tuple in file order (which is chronological because append-only).

```python
def windows_for_session(
    marks: tuple[StageMark, ...],
    session_end: datetime,
) -> tuple[StageWindow, ...]:
    \"\"\"Convert stage marks to half-open windows, closing at session_end.\"\"\"
```

Behaviour: pure function. Sort `marks` by `at`. Produce one window per mark: `start = marks[i].at`; `end = marks[i+1].at` if `i+1 < len(marks)` else `session_end`. If `end <= start` (malformed or clock skew), still emit the window — callers decide how to handle. Return tuple.

#### Design decisions

- **Two models, one file**: `StageMark` is the on-disk event shape; `StageWindow` is the parser-side interval. Separating them stabilises the JSONL format while letting the window consumer interface evolve.
- **Silent no-op on missing session id**: templates will call `mantle stage-begin <name>` at entry; if the user somehow runs the CLI outside a Claude Code session, we must not block — matches `build-start` precedent.
- **Chronological order = file order**: append-only JSONL means file order is chronological; no need to sort in `read_stages`. Sort happens in `windows_for_session` defensively so callers can cheaply merge multiple sources later.
- **Half-open windows**: the `[start, end)` convention avoids double-counting turns at window boundaries in downstream aggregators.
- **`_TELEMETRY_SUBDIR` as a module constant**: hard-coded here and in the parser-side reader; not a config knob — the directory name is infrastructure, not user-tunable.

## Tests

### tests/core/test_stages.py (new file)

Use `tmp_path` for all filesystem isolation. Use `inline_snapshot` for JSONL content capture where shape matters. Use `dirty_equals.IsDatetime` for timestamps in parsed `StageMark` objects.

- **test_record_stage_appends_jsonl**: set `CLAUDE_SESSION_ID` via monkeypatch; call `record_stage('shape', tmp_path)`; assert `tmp_path/.mantle/telemetry/stages-<sid>.jsonl` exists and contains exactly one `{"stage": "shape", "at": "<iso>"}` line. Use `inline_snapshot` on the JSON structure (ignoring `at` via partial match).
- **test_record_stage_appends_multiple**: call three times with different stages; assert three lines in file order `shape`, `plan_stories`, `implement`.
- **test_record_stage_creates_telemetry_dir**: tmp_path with no `.mantle/` at all; `record_stage` must create `.mantle/telemetry/` and succeed.
- **test_record_stage_no_session_id_is_noop**: unset `CLAUDE_SESSION_ID`, no `.mantle/.session-id` file; `record_stage('shape', tmp_path)` returns `None` and writes nothing (no `.mantle/telemetry/` created).
- **test_record_stage_rejects_empty_stage**: `record_stage('', tmp_path)` and `record_stage('   ', tmp_path)` both raise `ValueError`.
- **test_record_stage_uses_session_id_file_fallback**: write `tmp_path/.mantle/.session-id` with a test uuid; unset env; `record_stage('shape', tmp_path)` writes to `stages-<that_uuid>.jsonl`.
- **test_read_stages_empty_when_missing**: `read_stages('no-such-sid', tmp_path)` returns `()`.
- **test_read_stages_parses_in_order**: write three lines to a `stages-<sid>.jsonl`; assert `read_stages` returns tuple of 3 `StageMark`s in file order with correct stage names.
- **test_read_stages_skips_malformed_lines**: file with one valid line, one `garbage json`, one valid line; `read_stages` returns 2 marks.
- **test_read_stages_skips_blank_lines**: file with valid line, blank line, valid line → 2 marks.
- **test_windows_for_session_single_mark**: one mark at T0, session_end T1 → one window `[T0, T1)` with that stage.
- **test_windows_for_session_multiple_marks**: three marks at T0, T1, T2, session_end T3 → three windows `[T0,T1)`, `[T1,T2)`, `[T2,T3)`.
- **test_windows_for_session_sorts_unordered_input**: pass marks in reverse chronological order; assert output is sorted ascending.
- **test_windows_for_session_empty_input**: empty tuple → empty tuple.

Fixture: a small helper `_write_mark(path: Path, stage: str, at: str)` to build JSONL files inline.