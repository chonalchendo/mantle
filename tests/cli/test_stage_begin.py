"""Tests for mantle CLI stage-begin command."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from mantle.cli.main import stage_begin_command
from mantle.core import stages

if TYPE_CHECKING:
    from pathlib import Path


# ── test_stage_begin_writes_mark ─────────────────────────────────


def test_stage_begin_writes_mark(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sid = "test-sid"
    monkeypatch.setenv("CLAUDE_SESSION_ID", sid)

    stage_begin_command("shape", path=tmp_path)

    jsonl = tmp_path / ".mantle" / "telemetry" / f"stages-{sid}.jsonl"
    assert jsonl.exists()
    lines = [ln for ln in jsonl.read_text(encoding="utf-8").splitlines() if ln]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["stage"] == "shape"
    assert "at" in record


# ── test_stage_begin_noop_outside_session ────────────────────────


def test_stage_begin_noop_outside_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

    result = stage_begin_command("shape", path=tmp_path)

    assert result is None
    assert not (tmp_path / ".mantle" / "telemetry").exists()


# ── test_stage_begin_rejects_empty ───────────────────────────────


def test_stage_begin_rejects_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDE_SESSION_ID", "some-sid")

    with pytest.raises(ValueError, match="stage must be non-empty"):
        stage_begin_command("", path=tmp_path)


# ── test_stage_begin_roundtrip ───────────────────────────────────


def test_stage_begin_roundtrip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sid = "roundtrip-sid"
    monkeypatch.setenv("CLAUDE_SESSION_ID", sid)

    stage_begin_command("shape", path=tmp_path)
    stage_begin_command("plan-stories", path=tmp_path)
    stage_begin_command("implement", path=tmp_path)

    marks = stages.read_stages(sid, tmp_path)

    assert len(marks) == 3
    assert marks[0].stage == "shape"
    assert marks[1].stage == "plan-stories"
    assert marks[2].stage == "implement"
