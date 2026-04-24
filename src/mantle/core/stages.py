"""Stage-mark primitive — per-session JSONL of named stage-begin events."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pydantic

from mantle.core import telemetry

# ── Constants ────────────────────────────────────────────────────

_TELEMETRY_SUBDIR = "telemetry"
_STAGES_FILENAME_FMT = "stages-{session_id}.jsonl"


# ── Data models ──────────────────────────────────────────────────


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


# ── Public API ───────────────────────────────────────────────────


def record_stage(stage: str, project_dir: Path | None = None) -> None:
    """Append a StageMark record for the current Claude Code session.

    Resolves the session id via telemetry.current_session_id. Creates
    `<project_dir>/.mantle/telemetry/` if absent. Silently no-ops
    (returns None) when no session id is resolvable — matches the
    behaviour of `build-start` so template edits never block a
    shell-mode caller outside Claude Code.

    Args:
        stage: Non-empty stage name. Validated only as 'non-empty';
            typos are caught by the parity harness at snapshot review.
        project_dir: Project directory. Defaults to cwd.
    """
    stage = stage.strip()
    if not stage:
        raise ValueError("stage must be non-empty")

    if project_dir is None:
        project_dir = Path.cwd()

    try:
        session_id = telemetry.current_session_id(project_dir)
    except RuntimeError:
        return

    jsonl_path = (
        project_dir
        / ".mantle"
        / _TELEMETRY_SUBDIR
        / _STAGES_FILENAME_FMT.format(session_id=session_id)
    )
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    record = {"stage": stage, "at": datetime.now(UTC).isoformat()}
    with jsonl_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def read_stages(
    session_id: str,
    project_dir: Path | None = None,
) -> tuple[StageMark, ...]:
    """Parse the per-session stage-mark JSONL in chronological order.

    Iterates the file line-by-line, returning one StageMark per valid
    record. Malformed lines (invalid JSON, missing fields, wrong types)
    are skipped silently — matches the behaviour of
    telemetry._parse_assistant_line so reports remain producible for
    partially-written files.

    Args:
        session_id: Session identifier used to locate the JSONL file.
        project_dir: Project directory. Defaults to cwd.

    Returns:
        Tuple of parsed StageMark records in file order (chronological,
        because the file is append-only).
    """
    if project_dir is None:
        project_dir = Path.cwd()

    jsonl_path = (
        project_dir
        / ".mantle"
        / _TELEMETRY_SUBDIR
        / _STAGES_FILENAME_FMT.format(session_id=session_id)
    )

    if not jsonl_path.exists():
        return ()

    marks: list[StageMark] = []
    with jsonl_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                marks.append(StageMark(**record))
            except (
                json.JSONDecodeError,
                pydantic.ValidationError,
                TypeError,
                KeyError,
            ):
                continue

    return tuple(marks)


def windows_for_session(
    marks: tuple[StageMark, ...],
    session_end: datetime,
) -> tuple[StageWindow, ...]:
    """Convert stage marks to half-open windows, closing at session_end.

    Sorts marks by `at` defensively so callers can cheaply merge
    multiple sources. Each window is `[marks[i].at, marks[i+1].at)`
    except for the last, which closes at `session_end`.

    If `end <= start` (malformed data or clock skew), the window is
    still emitted — callers decide how to handle degenerate intervals.

    Args:
        marks: Stage-begin events, in any order.
        session_end: Exclusive end timestamp for the final window.

    Returns:
        Tuple of StageWindow records in ascending start order.
    """
    if not marks:
        return ()

    sorted_marks = sorted(marks, key=lambda m: m.at)
    windows: list[StageWindow] = []
    for i, mark in enumerate(sorted_marks):
        end = (
            sorted_marks[i + 1].at if i + 1 < len(sorted_marks) else session_end
        )
        windows.append(StageWindow(stage=mark.stage, start=mark.at, end=end))

    return tuple(windows)
