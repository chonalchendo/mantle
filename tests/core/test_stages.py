"""Tests for mantle.core.stages."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from dirty_equals import IsDatetime
from inline_snapshot import snapshot

from mantle.core import stages

if TYPE_CHECKING:
    from pathlib import Path


# ── Helper ───────────────────────────────────────────────────────


def _write_mark(path: Path, stage: str, at: str) -> None:
    """Append one stage-mark JSONL line to *path*."""
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"stage": stage, "at": at}) + "\n")


# ── record_stage ─────────────────────────────────────────────────


def test_record_stage_appends_jsonl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sid = "test-session-abc"
    monkeypatch.setenv("CLAUDE_SESSION_ID", sid)

    stages.record_stage("shape", tmp_path)

    jsonl = tmp_path / ".mantle" / "telemetry" / f"stages-{sid}.jsonl"
    assert jsonl.exists()
    lines = [ln for ln in jsonl.read_text(encoding="utf-8").splitlines() if ln]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record == snapshot(
        {"stage": "shape", "at": IsDatetime(iso_string=True)}
    )


def test_record_stage_appends_multiple(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sid = "test-session-multi"
    monkeypatch.setenv("CLAUDE_SESSION_ID", sid)

    stages.record_stage("shape", tmp_path)
    stages.record_stage("plan_stories", tmp_path)
    stages.record_stage("implement", tmp_path)

    jsonl = tmp_path / ".mantle" / "telemetry" / f"stages-{sid}.jsonl"
    lines = [ln for ln in jsonl.read_text(encoding="utf-8").splitlines() if ln]
    assert len(lines) == 3
    assert json.loads(lines[0])["stage"] == "shape"
    assert json.loads(lines[1])["stage"] == "plan_stories"
    assert json.loads(lines[2])["stage"] == "implement"


def test_record_stage_creates_telemetry_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sid = "test-session-dir"
    monkeypatch.setenv("CLAUDE_SESSION_ID", sid)

    # No .mantle/ directory exists yet
    telemetry_dir = tmp_path / ".mantle" / "telemetry"
    assert not telemetry_dir.exists()

    stages.record_stage("shape", tmp_path)

    assert telemetry_dir.is_dir()


def test_record_stage_no_session_id_is_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    # No .session-id fallback file

    result = stages.record_stage("shape", tmp_path)

    assert result is None
    assert not (tmp_path / ".mantle" / "telemetry").exists()


def test_record_stage_rejects_empty_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDE_SESSION_ID", "some-sid")

    with pytest.raises(ValueError, match="stage must be non-empty"):
        stages.record_stage("", tmp_path)

    with pytest.raises(ValueError, match="stage must be non-empty"):
        stages.record_stage("   ", tmp_path)


def test_record_stage_uses_session_id_file_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fallback_uuid = "fallback-uuid-1234"
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

    session_file = tmp_path / ".mantle" / ".session-id"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(fallback_uuid, encoding="utf-8")

    stages.record_stage("shape", tmp_path)

    jsonl = tmp_path / ".mantle" / "telemetry" / f"stages-{fallback_uuid}.jsonl"
    assert jsonl.exists()


# ── read_stages ──────────────────────────────────────────────────


def test_read_stages_empty_when_missing(tmp_path: Path) -> None:
    result = stages.read_stages("no-such-sid", tmp_path)
    assert result == ()


def test_read_stages_parses_in_order(tmp_path: Path) -> None:
    sid = "read-test-sid"
    jsonl = tmp_path / ".mantle" / "telemetry" / f"stages-{sid}.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)

    _write_mark(jsonl, "shape", "2026-01-01T10:00:00+00:00")
    _write_mark(jsonl, "plan_stories", "2026-01-01T10:05:00+00:00")
    _write_mark(jsonl, "implement", "2026-01-01T10:10:00+00:00")

    result = stages.read_stages(sid, tmp_path)

    assert len(result) == 3
    assert result[0].stage == "shape"
    assert result[1].stage == "plan_stories"
    assert result[2].stage == "implement"


def test_read_stages_skips_malformed_lines(tmp_path: Path) -> None:
    sid = "malformed-sid"
    jsonl = tmp_path / ".mantle" / "telemetry" / f"stages-{sid}.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)

    _write_mark(jsonl, "shape", "2026-01-01T10:00:00+00:00")
    with jsonl.open("a", encoding="utf-8") as fh:
        fh.write("garbage json\n")
    _write_mark(jsonl, "implement", "2026-01-01T10:10:00+00:00")

    result = stages.read_stages(sid, tmp_path)

    assert len(result) == 2
    assert result[0].stage == "shape"
    assert result[1].stage == "implement"


def test_read_stages_skips_blank_lines(tmp_path: Path) -> None:
    sid = "blank-lines-sid"
    jsonl = tmp_path / ".mantle" / "telemetry" / f"stages-{sid}.jsonl"
    jsonl.parent.mkdir(parents=True, exist_ok=True)

    _write_mark(jsonl, "shape", "2026-01-01T10:00:00+00:00")
    with jsonl.open("a", encoding="utf-8") as fh:
        fh.write("\n")
    _write_mark(jsonl, "implement", "2026-01-01T10:10:00+00:00")

    result = stages.read_stages(sid, tmp_path)

    assert len(result) == 2


# ── windows_for_session ──────────────────────────────────────────


def test_windows_for_session_single_mark() -> None:
    t0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 1, 1, 10, 30, 0, tzinfo=UTC)
    mark = stages.StageMark(stage="shape", at=t0)

    result = stages.windows_for_session((mark,), session_end=t1)

    assert len(result) == 1
    assert result[0].stage == "shape"
    assert result[0].start == t0
    assert result[0].end == t1


def test_windows_for_session_multiple_marks() -> None:
    t0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 1, 1, 10, 10, 0, tzinfo=UTC)
    t2 = datetime(2026, 1, 1, 10, 20, 0, tzinfo=UTC)
    t3 = datetime(2026, 1, 1, 10, 30, 0, tzinfo=UTC)
    marks = (
        stages.StageMark(stage="shape", at=t0),
        stages.StageMark(stage="plan_stories", at=t1),
        stages.StageMark(stage="implement", at=t2),
    )

    result = stages.windows_for_session(marks, session_end=t3)

    assert len(result) == 3
    assert result[0] == stages.StageWindow(stage="shape", start=t0, end=t1)
    assert result[1] == stages.StageWindow(
        stage="plan_stories", start=t1, end=t2
    )
    assert result[2] == stages.StageWindow(stage="implement", start=t2, end=t3)


def test_windows_for_session_sorts_unordered_input() -> None:
    t0 = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 1, 1, 10, 10, 0, tzinfo=UTC)
    t2 = datetime(2026, 1, 1, 10, 20, 0, tzinfo=UTC)
    session_end = datetime(2026, 1, 1, 10, 30, 0, tzinfo=UTC)

    # Pass in reverse order
    marks = (
        stages.StageMark(stage="implement", at=t2),
        stages.StageMark(stage="plan_stories", at=t1),
        stages.StageMark(stage="shape", at=t0),
    )

    result = stages.windows_for_session(marks, session_end=session_end)

    assert len(result) == 3
    assert result[0].stage == "shape"
    assert result[0].start == t0
    assert result[1].stage == "plan_stories"
    assert result[1].start == t1
    assert result[2].stage == "implement"
    assert result[2].start == t2


def test_windows_for_session_empty_input() -> None:
    session_end = datetime(2026, 1, 1, 10, 30, 0, tzinfo=UTC)
    result = stages.windows_for_session((), session_end=session_end)
    assert result == ()
