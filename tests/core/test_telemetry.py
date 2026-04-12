"""Tests for mantle.core.telemetry."""

from __future__ import annotations

import json
import warnings
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from mantle.core import telemetry

if TYPE_CHECKING:
    from pathlib import Path


# ── Fixture helpers ──────────────────────────────────────────────


def _assistant_record(
    uuid: str,
    parent_uuid: str | None,
    session_id: str,
    timestamp: datetime,
    model: str = "claude-opus-4-6",
    is_sidechain: bool = False,
    input_tokens: int = 10,
    output_tokens: int = 20,
    cache_read_input_tokens: int = 0,
    cache_creation_input_tokens: int = 0,
) -> dict:
    """Build a minimal assistant JSONL record matching the real schema."""
    return {
        "type": "assistant",
        "isSidechain": is_sidechain,
        "sessionId": session_id,
        "parentUuid": parent_uuid,
        "uuid": uuid,
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "message": {
            "model": model,
            "id": f"msg_{uuid}",
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": cache_read_input_tokens,
                "cache_creation_input_tokens": cache_creation_input_tokens,
                "service_tier": "standard",
            },
        },
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    """Write records as newline-delimited JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for rec in records:
            handle.write(json.dumps(rec))
            handle.write("\n")


# ── find_session_file ────────────────────────────────────────────


def test_find_session_file_success(tmp_path: Path) -> None:
    projects_root = tmp_path / "projects"
    slug_dir = projects_root / "-some-slug"
    slug_dir.mkdir(parents=True)
    session_id = "abc-123"
    session_file = slug_dir / f"{session_id}.jsonl"
    session_file.write_text("", encoding="utf-8")

    result = telemetry.find_session_file(session_id, projects_root)

    assert result == session_file


def test_find_session_file_missing_raises(tmp_path: Path) -> None:
    projects_root = tmp_path / "projects"
    projects_root.mkdir()

    with pytest.raises(FileNotFoundError) as exc:
        telemetry.find_session_file("missing-uuid", projects_root)

    assert "missing-uuid" in str(exc.value)


def test_find_session_file_honours_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    projects_root = tmp_path / "custom-projects"
    slug_dir = projects_root / "-slug"
    slug_dir.mkdir(parents=True)
    session_id = "env-uuid"
    session_file = slug_dir / f"{session_id}.jsonl"
    session_file.write_text("", encoding="utf-8")

    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_root))

    result = telemetry.find_session_file(session_id)

    assert result == session_file


# ── read_session ─────────────────────────────────────────────────


def test_read_session_parses_assistant_turns(tmp_path: Path) -> None:
    session_file = tmp_path / "session.jsonl"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    records = [
        _assistant_record("u1", None, "sess", ts),
        {"type": "user", "sessionId": "sess", "uuid": "u2"},
        _assistant_record("u3", "u1", "sess", ts + timedelta(seconds=5)),
        _assistant_record("u4", "u3", "sess", ts + timedelta(seconds=10)),
    ]
    _write_jsonl(session_file, records)

    turns = telemetry.read_session(session_file)

    assert len(turns) == 3
    assert turns[0].uuid == "u1"
    assert turns[1].uuid == "u3"
    assert turns[2].uuid == "u4"


def test_read_session_skips_malformed_lines(tmp_path: Path) -> None:
    session_file = tmp_path / "session.jsonl"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    session_file.parent.mkdir(parents=True, exist_ok=True)
    with session_file.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(_assistant_record("u1", None, "s", ts)))
        handle.write("\n")
        handle.write('{"type": "assistant", "broken": ')
        handle.write("\n")
        handle.write(
            json.dumps(
                _assistant_record("u2", "u1", "s", ts + timedelta(seconds=1))
            )
        )
        handle.write("\n")

    turns = telemetry.read_session(session_file)

    assert len(turns) == 2
    assert turns[0].uuid == "u1"
    assert turns[1].uuid == "u2"


def test_read_session_parses_usage_fields(tmp_path: Path) -> None:
    session_file = tmp_path / "session.jsonl"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    records = [
        _assistant_record(
            "u1",
            None,
            "sess",
            ts,
            input_tokens=5,
            output_tokens=100,
            cache_read_input_tokens=1234,
            cache_creation_input_tokens=567,
        ),
    ]
    _write_jsonl(session_file, records)

    turns = telemetry.read_session(session_file)

    assert turns[0].usage is not None
    assert turns[0].usage.input_tokens == 5
    assert turns[0].usage.output_tokens == 100
    assert turns[0].usage.cache_read_input_tokens == 1234
    assert turns[0].usage.cache_creation_input_tokens == 567


# ── group_stories ────────────────────────────────────────────────


def test_group_stories_single_sidechain_cluster() -> None:
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    main = telemetry.Turn(
        uuid="m1",
        parent_uuid=None,
        session_id="s",
        timestamp=ts,
        model="claude-opus-4-6",
        is_sidechain=False,
        usage=telemetry.Usage(input_tokens=1, output_tokens=2),
    )
    s1 = telemetry.Turn(
        uuid="s1",
        parent_uuid="m1",
        session_id="s",
        timestamp=ts + timedelta(seconds=10),
        model="claude-opus-4-6",
        is_sidechain=True,
        usage=telemetry.Usage(input_tokens=100, output_tokens=20),
    )
    s2 = telemetry.Turn(
        uuid="s2",
        parent_uuid="s1",
        session_id="s",
        timestamp=ts + timedelta(seconds=20),
        model="claude-opus-4-6",
        is_sidechain=True,
        usage=telemetry.Usage(input_tokens=50, output_tokens=10),
    )
    s3 = telemetry.Turn(
        uuid="s3",
        parent_uuid="s2",
        session_id="s",
        timestamp=ts + timedelta(seconds=30),
        model="claude-opus-4-6",
        is_sidechain=True,
        usage=telemetry.Usage(input_tokens=30, output_tokens=5),
    )

    runs = telemetry.group_stories((main, s1, s2, s3))

    assert len(runs) == 1
    assert runs[0].turn_count == 3
    assert runs[0].usage.input_tokens == 180
    assert runs[0].usage.output_tokens == 35


def test_group_stories_two_clusters() -> None:
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    def turn(
        uuid: str,
        parent: str | None,
        seconds: int,
        sidechain: bool,
    ) -> telemetry.Turn:
        return telemetry.Turn(
            uuid=uuid,
            parent_uuid=parent,
            session_id="s",
            timestamp=ts + timedelta(seconds=seconds),
            model="claude-opus-4-6",
            is_sidechain=sidechain,
            usage=telemetry.Usage(input_tokens=1, output_tokens=1),
        )

    turns = (
        turn("m1", None, 0, False),
        turn("s1a", "m1", 10, True),
        turn("s1b", "s1a", 20, True),
        turn("m2", "m1", 30, False),
        turn("s2a", "m2", 40, True),
        turn("s2b", "s2a", 50, True),
    )

    runs = telemetry.group_stories(turns)

    assert len(runs) == 2
    assert runs[0].turn_count == 2
    assert runs[1].turn_count == 2


def test_group_stories_with_markers_assigns_story_ids() -> None:
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    def turn(
        uuid: str,
        parent: str | None,
        seconds: int,
        sidechain: bool,
    ) -> telemetry.Turn:
        return telemetry.Turn(
            uuid=uuid,
            parent_uuid=parent,
            session_id="s",
            timestamp=ts + timedelta(seconds=seconds),
            model="claude-opus-4-6",
            is_sidechain=sidechain,
            usage=telemetry.Usage(input_tokens=1, output_tokens=1),
        )

    turns = (
        turn("m1", None, 0, False),
        turn("s1a", "m1", 10, True),
        turn("s1b", "s1a", 20, True),
        turn("m2", "m1", 100, False),
        turn("s2a", "m2", 110, True),
        turn("s2b", "s2a", 120, True),
    )

    markers = (
        telemetry.Marker(story_id=1, timestamp=ts + timedelta(seconds=5)),
        telemetry.Marker(story_id=2, timestamp=ts + timedelta(seconds=105)),
    )

    runs = telemetry.group_stories(turns, markers)

    assert len(runs) == 2
    assert runs[0].story_id == 1
    assert runs[1].story_id == 2


def test_group_stories_marker_beyond_window_logs_warning() -> None:
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    def turn(
        uuid: str,
        parent: str | None,
        seconds: int,
        sidechain: bool,
    ) -> telemetry.Turn:
        return telemetry.Turn(
            uuid=uuid,
            parent_uuid=parent,
            session_id="s",
            timestamp=ts + timedelta(seconds=seconds),
            model="claude-opus-4-6",
            is_sidechain=sidechain,
            usage=telemetry.Usage(input_tokens=1, output_tokens=1),
        )

    turns = (
        turn("m1", None, 0, False),
        turn("s1a", "m1", 3600, True),
        turn("s1b", "s1a", 3610, True),
    )

    markers = (
        telemetry.Marker(story_id=1, timestamp=ts + timedelta(seconds=5)),
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        runs = telemetry.group_stories(turns, markers)

    assert runs[0].story_id is None
    assert any(
        issubclass(w.category, telemetry.MarkerWindowWarning) for w in caught
    )


def test_group_stories_aggregates_usage() -> None:
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    s1 = telemetry.Turn(
        uuid="s1",
        parent_uuid="m1",
        session_id="s",
        timestamp=ts + timedelta(seconds=1),
        model="claude-opus-4-6",
        is_sidechain=True,
        usage=telemetry.Usage(input_tokens=100, output_tokens=20),
    )
    s2 = telemetry.Turn(
        uuid="s2",
        parent_uuid="s1",
        session_id="s",
        timestamp=ts + timedelta(seconds=2),
        model="claude-opus-4-6",
        is_sidechain=True,
        usage=telemetry.Usage(input_tokens=50, output_tokens=10),
    )

    runs = telemetry.group_stories((s1, s2))

    assert len(runs) == 1
    assert runs[0].usage.input_tokens == 150
    assert runs[0].usage.output_tokens == 30


def test_group_stories_model_is_mode() -> None:
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    def sc(uuid: str, parent: str, seconds: int, model: str) -> telemetry.Turn:
        return telemetry.Turn(
            uuid=uuid,
            parent_uuid=parent,
            session_id="s",
            timestamp=ts + timedelta(seconds=seconds),
            model=model,
            is_sidechain=True,
            usage=telemetry.Usage(input_tokens=1, output_tokens=1),
        )

    turns = (
        sc("s1", "m1", 1, "opus"),
        sc("s2", "s1", 2, "opus"),
        sc("s3", "s2", 3, "sonnet"),
    )

    runs = telemetry.group_stories(turns)

    assert runs[0].model == "opus"


# ── summarise / empty session ────────────────────────────────────


def test_summarise_computes_wall_bounds() -> None:
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    first = telemetry.Turn(
        uuid="a",
        parent_uuid=None,
        session_id="s",
        timestamp=ts,
        model="claude-opus-4-6",
        is_sidechain=False,
        usage=telemetry.Usage(input_tokens=1, output_tokens=1),
    )
    last = telemetry.Turn(
        uuid="b",
        parent_uuid="a",
        session_id="s",
        timestamp=ts + timedelta(minutes=10),
        model="claude-opus-4-6",
        is_sidechain=False,
        usage=telemetry.Usage(input_tokens=1, output_tokens=1),
    )

    report = telemetry.summarise("s", (first, last), ())

    assert report.session_id == "s"
    assert report.started == ts
    assert report.finished == ts + timedelta(minutes=10)


def test_empty_session_yields_empty_report(tmp_path: Path) -> None:
    session_file = tmp_path / "empty.jsonl"
    session_file.write_text("", encoding="utf-8")

    turns = telemetry.read_session(session_file)
    runs = telemetry.group_stories(turns)
    report = telemetry.summarise("sess", turns, runs)

    assert turns == ()
    assert runs == ()
    assert report.stories == ()
    assert report.started == report.finished


# ── current_session_id ───────────────────────────────────────────


def test_current_session_id_reads_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDE_SESSION_ID", "abc")

    assert telemetry.current_session_id() == "abc"


def test_current_session_id_missing_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

    with pytest.raises(RuntimeError) as exc:
        telemetry.current_session_id()

    assert "CLAUDE_SESSION_ID" in str(exc.value)


# ── render_report ────────────────────────────────────────────────


def test_render_report_emits_yaml_frontmatter() -> None:
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    story1 = telemetry.StoryRun(
        story_id=1,
        model="claude-opus-4-6",
        started=ts,
        finished=ts + timedelta(seconds=60),
        duration_s=60.0,
        usage=telemetry.Usage(input_tokens=100, output_tokens=50),
        turn_count=3,
    )
    story2 = telemetry.StoryRun(
        story_id=2,
        model="claude-sonnet-4-5",
        started=ts + timedelta(seconds=120),
        finished=ts + timedelta(seconds=180),
        duration_s=60.0,
        usage=telemetry.Usage(input_tokens=200, output_tokens=80),
        turn_count=5,
    )
    report = telemetry.BuildReport(
        session_id="sess-1",
        started=ts,
        finished=ts + timedelta(seconds=180),
        stories=(story1, story2),
    )
    markers = (
        telemetry.Marker(story_id=1, timestamp=ts),
        telemetry.Marker(story_id=2, timestamp=ts + timedelta(seconds=120)),
    )

    text = telemetry.render_report(report, issue=54, markers=markers)

    assert text.startswith("---")
    assert "issue: 54" in text
    assert "stories:" in text
    assert "model" in text
    assert "duration_s" in text
    assert "## Summary" in text
    # A markdown table header row
    assert "|" in text.split("## Summary", 1)[1]


def test_render_report_zero_stories() -> None:
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    report = telemetry.BuildReport(
        session_id="sess-empty",
        started=ts,
        finished=ts,
        stories=(),
    )

    text = telemetry.render_report(report, issue=99, markers=())

    assert text.startswith("---")
    assert "issue: 99" in text
    assert "No story runs detected" in text
