"""Tests for mantle.core.telemetry."""

from __future__ import annotations

import json
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


# ── read_meta ────────────────────────────────────────────────────


def test_read_meta_parses_agent_type(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "agent-123.jsonl"
    meta_path = tmp_path / "agent-123.meta.json"
    meta_path.write_text(
        json.dumps({"agentType": "story-implementer", "otherField": "ignored"}),
        encoding="utf-8",
    )

    result = telemetry.read_meta(jsonl_path)

    assert result is not None
    assert result.agent_type == "story-implementer"


def test_read_meta_missing_returns_none(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "agent-123.jsonl"
    # No sidecar written

    result = telemetry.read_meta(jsonl_path)

    assert result is None


def test_read_meta_malformed_returns_none(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "agent-123.jsonl"
    meta_path = tmp_path / "agent-123.meta.json"
    meta_path.write_text("{invalid json", encoding="utf-8")

    result = telemetry.read_meta(jsonl_path)

    assert result is None


def test_read_meta_missing_agent_type_returns_none(tmp_path: Path) -> None:
    jsonl_path = tmp_path / "agent-123.jsonl"
    meta_path = tmp_path / "agent-123.meta.json"
    meta_path.write_text("{}", encoding="utf-8")

    result = telemetry.read_meta(jsonl_path)

    assert result is None


# ── find_subagent_files ──────────────────────────────────────────


def test_find_subagent_files_returns_sorted(tmp_path: Path) -> None:
    """Files sorted by first-turn timestamp ascending (T0 before T1)."""
    projects_root = tmp_path / "projects"
    session_id = "sess-abc"
    subagents_dir = projects_root / "slug" / session_id / "subagents"
    subagents_dir.mkdir(parents=True)

    t0 = datetime(2026, 4, 1, 10, 0, 0, tzinfo=UTC)
    t1 = datetime(2026, 4, 1, 11, 0, 0, tzinfo=UTC)

    # Write agent-b with earlier timestamp T0, agent-a with later T1
    agent_b = subagents_dir / "agent-bbb.jsonl"
    agent_a = subagents_dir / "agent-aaa.jsonl"
    _write_jsonl(agent_b, [_assistant_record("u1", None, session_id, t0)])
    _write_jsonl(agent_a, [_assistant_record("u2", None, session_id, t1)])

    result = telemetry.find_subagent_files(session_id, projects_root)

    assert result == (agent_b, agent_a)


def test_find_subagent_files_empty_when_absent(tmp_path: Path) -> None:
    """Returns empty tuple when parent dir exists but has no subagents/."""
    projects_root = tmp_path / "projects"
    session_id = "sess-xyz"
    # Create parent session dir but no subagents subdirectory
    (projects_root / "slug" / session_id).mkdir(parents=True)

    result = telemetry.find_subagent_files(session_id, projects_root)

    assert result == ()


# ── read_subagent ────────────────────────────────────────────────


def test_read_subagent_parses_sidechain_turns(tmp_path: Path) -> None:
    """read_subagent returns turns preserving is_sidechain=True."""
    jsonl_path = tmp_path / "agent-xyz.jsonl"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    records = [
        _assistant_record("t1", None, "s", ts, is_sidechain=True),
        _assistant_record(
            "t2", "t1", "s", ts + timedelta(seconds=5), is_sidechain=True
        ),
        _assistant_record(
            "t3", "t2", "s", ts + timedelta(seconds=10), is_sidechain=True
        ),
    ]
    _write_jsonl(jsonl_path, records)

    turns = telemetry.read_subagent(jsonl_path)

    assert len(turns) == 3
    assert all(t.is_sidechain for t in turns)


# ── group_stories ────────────────────────────────────────────────


def _make_subagent_pair(
    directory: Path,
    agent_id: str,
    agent_type: str,
    session_id: str,
    start_ts: datetime,
    turn_count: int = 2,
) -> Path:
    """Write a sub-agent JSONL + meta.json pair and return the JSONL path."""
    jsonl_path = directory / f"agent-{agent_id}.jsonl"
    meta_path = directory / f"agent-{agent_id}.meta.json"
    records = [
        _assistant_record(
            f"{agent_id}-{i}",
            f"{agent_id}-{i - 1}" if i > 0 else None,
            session_id,
            start_ts + timedelta(seconds=i * 10),
            is_sidechain=True,
        )
        for i in range(turn_count)
    ]
    _write_jsonl(jsonl_path, records)
    meta_path.write_text(
        json.dumps({"agentType": agent_type}), encoding="utf-8"
    )
    return jsonl_path


def test_group_stories_from_subagent_paths(tmp_path: Path) -> None:
    """Three sub-agents with known types map to implement/simplify/verify."""
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    p1 = _make_subagent_pair(tmp_path, "aaa", "story-implementer", "s", ts)
    p2 = _make_subagent_pair(
        tmp_path, "bbb", "refactorer", "s", ts + timedelta(hours=1)
    )
    p3 = _make_subagent_pair(
        tmp_path, "ccc", "general-purpose", "s", ts + timedelta(hours=2)
    )

    runs = telemetry.group_stories(subagent_paths=(p1, p2, p3))

    assert len(runs) == 3
    stages = [r.stage for r in runs]
    assert stages == ["implement", "simplify", "verify"]


def test_group_stories_unknown_agent_type_yields_stage_none(
    tmp_path: Path,
) -> None:
    """Unknown agentType in sidecar → StoryRun with stage=None."""
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    path = _make_subagent_pair(tmp_path, "aaa", "custom-thing", "s", ts)

    runs = telemetry.group_stories(subagent_paths=(path,))

    assert len(runs) == 1
    assert runs[0].stage is None


def test_group_stories_from_stage_windows(tmp_path: Path) -> None:
    """Parent turns windowed by StageWindow produce correct StoryRuns."""
    from mantle.core import stages

    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    t0 = ts
    t1 = ts + timedelta(seconds=10)
    t2 = ts + timedelta(seconds=20)
    t3 = ts + timedelta(seconds=30)
    t4 = ts + timedelta(seconds=40)

    parent_turns = tuple(
        telemetry.Turn(
            uuid=f"u{i}",
            parent_uuid=None,
            session_id="s",
            timestamp=t,
            model="claude-opus-4-6",
            is_sidechain=False,
            usage=telemetry.Usage(input_tokens=1, output_tokens=1),
        )
        for i, t in enumerate([t0, t1, t2, t3])
    )

    windows = (
        stages.StageWindow(stage="shape", start=t0, end=t2),
        stages.StageWindow(stage="plan_stories", start=t2, end=t4),
    )

    runs = telemetry.group_stories(
        parent_turns=parent_turns, stage_windows=windows
    )

    assert len(runs) == 2
    assert runs[0].stage == "shape"
    assert runs[0].turn_count == 2
    assert runs[1].stage == "plan_stories"
    assert runs[1].turn_count == 2


def test_group_stories_window_with_no_turns_is_skipped(tmp_path: Path) -> None:
    """Windows that cover no parent turns do not emit a StoryRun."""
    from mantle.core import stages

    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    # Window covers [ts+100, ts+200) — no parent turns in that range
    windows = (
        stages.StageWindow(
            stage="verify",
            start=ts + timedelta(seconds=100),
            end=ts + timedelta(seconds=200),
        ),
    )

    runs = telemetry.group_stories(parent_turns=(), stage_windows=windows)

    assert runs == ()


def test_group_stories_half_open_windows(tmp_path: Path) -> None:
    """Turn at window.end is excluded; turn at window.start is included."""
    from mantle.core import stages

    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
    t_start = ts
    t_end = ts + timedelta(seconds=30)
    t_at_start = t_start
    t_at_end = t_end  # should be excluded
    t_before_end = t_end - timedelta(seconds=1)  # should be included

    parent_turns = (
        telemetry.Turn(
            uuid="u_start",
            parent_uuid=None,
            session_id="s",
            timestamp=t_at_start,
            model="claude-opus-4-6",
            is_sidechain=False,
            usage=telemetry.Usage(input_tokens=1, output_tokens=1),
        ),
        telemetry.Turn(
            uuid="u_before_end",
            parent_uuid=None,
            session_id="s",
            timestamp=t_before_end,
            model="claude-opus-4-6",
            is_sidechain=False,
            usage=telemetry.Usage(input_tokens=1, output_tokens=1),
        ),
        telemetry.Turn(
            uuid="u_at_end",
            parent_uuid=None,
            session_id="s",
            timestamp=t_at_end,
            model="claude-opus-4-6",
            is_sidechain=False,
            usage=telemetry.Usage(input_tokens=1, output_tokens=1),
        ),
    )

    windows = (stages.StageWindow(stage="implement", start=t_start, end=t_end),)

    runs = telemetry.group_stories(
        parent_turns=parent_turns, stage_windows=windows
    )

    assert len(runs) == 1
    assert runs[0].turn_count == 2  # u_start + u_before_end, not u_at_end


def test_group_stories_results_sorted_by_started(tmp_path: Path) -> None:
    """Mix of sub-agent + window runs sorted ascending by started."""
    from mantle.core import stages

    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    # Sub-agent starting at ts+2h
    late_path = _make_subagent_pair(
        tmp_path, "late", "story-implementer", "s", ts + timedelta(hours=2)
    )
    # Sub-agent starting at ts+1h
    early_path = _make_subagent_pair(
        tmp_path, "early", "refactorer", "s", ts + timedelta(hours=1)
    )

    # Window run starting at ts (earliest)
    parent_turn = telemetry.Turn(
        uuid="p1",
        parent_uuid=None,
        session_id="s",
        timestamp=ts,
        model="claude-opus-4-6",
        is_sidechain=False,
        usage=telemetry.Usage(input_tokens=1, output_tokens=1),
    )
    windows = (
        stages.StageWindow(
            stage="shape", start=ts, end=ts + timedelta(minutes=30)
        ),
    )

    runs = telemetry.group_stories(
        parent_turns=(parent_turn,),
        subagent_paths=(late_path, early_path),
        stage_windows=windows,
    )

    assert len(runs) == 3
    started_times = [r.started for r in runs]
    assert started_times == sorted(started_times)


def test_group_stories_empty_returns_empty() -> None:
    """All three args empty → empty tuple."""
    runs = telemetry.group_stories()

    assert runs == ()


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
    runs = telemetry.group_stories()
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
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

    with pytest.raises(RuntimeError) as exc:
        telemetry.current_session_id(tmp_path)

    assert "CLAUDE_SESSION_ID" in str(exc.value)


def test_current_session_id_falls_back_to_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    mantle_dir = tmp_path / ".mantle"
    mantle_dir.mkdir()
    (mantle_dir / ".session-id").write_text("sess-from-file\n")

    assert telemetry.current_session_id(tmp_path) == "sess-from-file"


def test_current_session_id_env_preferred_over_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CLAUDE_SESSION_ID", "sess-from-env")
    mantle_dir = tmp_path / ".mantle"
    mantle_dir.mkdir()
    (mantle_dir / ".session-id").write_text("sess-from-file")

    assert telemetry.current_session_id(tmp_path) == "sess-from-env"


def test_current_session_id_empty_file_falls_through_to_raise(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    mantle_dir = tmp_path / ".mantle"
    mantle_dir.mkdir()
    (mantle_dir / ".session-id").write_text("   \n")

    with pytest.raises(RuntimeError):
        telemetry.current_session_id(tmp_path)
