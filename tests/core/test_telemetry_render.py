"""Tests for telemetry.render_report with per-stage grouping."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from inline_snapshot import snapshot

from mantle.core import telemetry


def _make_story_run(
    stage: str | None,
    story_id: int | None = None,
    model: str = "claude-opus-4-6",
    started_offset_s: int = 0,
    duration_s: float = 60.0,
    input_tokens: int = 100,
    output_tokens: int = 50,
    turn_count: int = 3,
) -> telemetry.StoryRun:
    """Build a minimal StoryRun for render tests."""
    base = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    started = base + timedelta(seconds=started_offset_s)
    finished = started + timedelta(seconds=duration_s)
    return telemetry.StoryRun(
        story_id=story_id,
        model=model,
        started=started,
        finished=finished,
        duration_s=duration_s,
        usage=telemetry.Usage(
            input_tokens=input_tokens, output_tokens=output_tokens
        ),
        turn_count=turn_count,
        stage=stage,
    )


def _make_report(
    stories: tuple[telemetry.StoryRun, ...],
) -> telemetry.BuildReport:
    base = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    return telemetry.BuildReport(
        session_id="sess-test",
        started=base,
        finished=base + timedelta(hours=1),
        stories=stories,
    )


def test_render_report_groups_by_stage() -> None:
    """Four stages rendered with ### sub-headings; None goes to Unattributed."""
    stories = (
        _make_story_run("implement", started_offset_s=0),
        _make_story_run("implement", started_offset_s=100),
        _make_story_run("simplify", started_offset_s=200),
        _make_story_run("verify", started_offset_s=300),
        _make_story_run(None, started_offset_s=400),
    )
    report = _make_report(stories)

    text = telemetry.render_report(report, issue=54)

    assert text == snapshot(
        """\
---
issue: 54
session_id: sess-test
started: 2026-04-12T10:00:00+00:00
finished: 2026-04-12T11:00:00+00:00
stories:
  - story_id: null
    stage: implement
    model: claude-opus-4-6
    started: 2026-04-12T10:00:00+00:00
    finished: 2026-04-12T10:01:00+00:00
    duration_s: 60.0
    turn_count: 3
    input_tokens: 100
    output_tokens: 50
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
  - story_id: null
    stage: implement
    model: claude-opus-4-6
    started: 2026-04-12T10:01:40+00:00
    finished: 2026-04-12T10:02:40+00:00
    duration_s: 60.0
    turn_count: 3
    input_tokens: 100
    output_tokens: 50
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
  - story_id: null
    stage: simplify
    model: claude-opus-4-6
    started: 2026-04-12T10:03:20+00:00
    finished: 2026-04-12T10:04:20+00:00
    duration_s: 60.0
    turn_count: 3
    input_tokens: 100
    output_tokens: 50
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
  - story_id: null
    stage: verify
    model: claude-opus-4-6
    started: 2026-04-12T10:05:00+00:00
    finished: 2026-04-12T10:06:00+00:00
    duration_s: 60.0
    turn_count: 3
    input_tokens: 100
    output_tokens: 50
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
  - story_id: null
    stage: null
    model: claude-opus-4-6
    started: 2026-04-12T10:06:40+00:00
    finished: 2026-04-12T10:07:40+00:00
    duration_s: 60.0
    turn_count: 3
    input_tokens: 100
    output_tokens: 50
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
---

## Summary

### implement

| Story | Model | Duration (s) | Turns | In tok | Out tok |
|-------|-------|--------------|-------|--------|---------|
| — | claude-opus-4-6 | 60.0 | 3 | 100 | 50 |
| — | claude-opus-4-6 | 60.0 | 3 | 100 | 50 |

### simplify

| Story | Model | Duration (s) | Turns | In tok | Out tok |
|-------|-------|--------------|-------|--------|---------|
| — | claude-opus-4-6 | 60.0 | 3 | 100 | 50 |

### verify

| Story | Model | Duration (s) | Turns | In tok | Out tok |
|-------|-------|--------------|-------|--------|---------|
| — | claude-opus-4-6 | 60.0 | 3 | 100 | 50 |

### Unattributed

| Story | Model | Duration (s) | Turns | In tok | Out tok |
|-------|-------|--------------|-------|--------|---------|
| — | claude-opus-4-6 | 60.0 | 3 | 100 | 50 |
"""
    )


def test_render_report_empty_stories() -> None:
    """No story runs → placeholder text (back-compat)."""
    report = _make_report(())

    text = telemetry.render_report(report, issue=99)

    assert "No story runs detected" in text
    assert "## Summary" in text


def test_render_report_all_unattributed() -> None:
    """Only stage=None runs → only Unattributed section, no other ###."""
    stories = (
        _make_story_run(None, started_offset_s=0),
        _make_story_run(None, started_offset_s=60),
    )
    report = _make_report(stories)

    text = telemetry.render_report(report, issue=10)

    assert "### Unattributed" in text
    # No other stage sub-headings
    lines = text.splitlines()
    h3_lines = [line for line in lines if line.startswith("### ")]
    assert h3_lines == ["### Unattributed"]
