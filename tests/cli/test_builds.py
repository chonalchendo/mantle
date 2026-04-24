"""Tests for mantle.cli.builds."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from inline_snapshot import snapshot

from mantle.cli import builds

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


# ── Helpers ──────────────────────────────────────────────────────


def _assistant_record(
    uuid: str,
    parent_uuid: str | None,
    session_id: str,
    timestamp: datetime,
    is_sidechain: bool = False,
) -> dict:
    """Build a minimal assistant JSONL record."""
    return {
        "type": "assistant",
        "isSidechain": is_sidechain,
        "sessionId": session_id,
        "parentUuid": parent_uuid,
        "uuid": uuid,
        "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
        "message": {
            "model": "claude-opus-4-6",
            "id": f"msg_{uuid}",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 20,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
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


def _make_project(tmp_path: Path) -> Path:
    """Create a minimal project with a .mantle/ directory."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "builds").mkdir()
    (tmp_path / ".mantle" / "stories").mkdir()
    return tmp_path


def _normalize(body: str) -> str:
    """Normalise ISO-8601 timestamps to <TS> for stable snapshot comparison."""
    return re.sub(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?",
        "<TS>",
        body,
    )


# ── run_build_start ──────────────────────────────────────────────


def test_build_start_writes_stub(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dir = _make_project(tmp_path)
    monkeypatch.setenv("CLAUDE_SESSION_ID", "sess-xyz")

    builds.run_build_start(54, project_dir=project_dir)

    build_files = list(
        (project_dir / ".mantle" / "builds").glob("build-54-*.md")
    )
    assert len(build_files) == 1
    text = build_files[0].read_text(encoding="utf-8")
    assert "issue: 54" in text
    assert "status: in-progress" in text
    assert "session_id: sess-xyz" in text


def test_build_start_without_session_id_warns_and_exits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_dir = _make_project(tmp_path)
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

    builds.run_build_start(54, project_dir=project_dir)

    build_files = list(
        (project_dir / ".mantle" / "builds").glob("build-54-*.md")
    )
    assert build_files == []
    captured = capsys.readouterr()
    assert "Warning" in captured.out or "warning" in captured.out.lower()


# ── run_build_finish ─────────────────────────────────────────────


def test_build_finish_parses_jsonl_and_overwrites_stub(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dir = _make_project(tmp_path)
    session_id = "sess-finish"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    # Pre-create a stub from a prior build-start
    stub = project_dir / ".mantle" / "builds" / "build-54-20260412-1000.md"
    stub.write_text(
        "---\n"
        "issue: 54\n"
        f"started: {ts.isoformat()}\n"
        f"session_id: {session_id}\n"
        "status: in-progress\n"
        "---\n",
        encoding="utf-8",
    )

    # Fake CLAUDE_PROJECTS_DIR with one session file (1 main + 2 sidechain)
    projects_root = tmp_path / "projects"
    slug = projects_root / "-slug"
    slug.mkdir(parents=True)
    session_file = slug / f"{session_id}.jsonl"
    records = [
        _assistant_record("m1", None, session_id, ts, is_sidechain=False),
        _assistant_record(
            "s1",
            "m1",
            session_id,
            ts + timedelta(seconds=10),
            is_sidechain=True,
        ),
        _assistant_record(
            "s2",
            "s1",
            session_id,
            ts + timedelta(seconds=20),
            is_sidechain=True,
        ),
    ]
    _write_jsonl(session_file, records)
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_root))

    builds.run_build_finish(54, project_dir=project_dir)

    text = stub.read_text(encoding="utf-8")
    assert "status: complete" in text
    assert "## Summary" in text


def test_build_finish_with_no_stub_warns_cleanly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_dir = _make_project(tmp_path)

    builds.run_build_finish(54, project_dir=project_dir)

    build_files = list(
        (project_dir / ".mantle" / "builds").glob("build-54-*.md")
    )
    assert build_files == []
    captured = capsys.readouterr()
    assert "Warning" in captured.out or "warning" in captured.out.lower()


def test_build_finish_with_missing_session_file_warns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project_dir = _make_project(tmp_path)
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    stub = project_dir / ".mantle" / "builds" / "build-54-20260412-1000.md"
    stub_body = (
        "---\n"
        "issue: 54\n"
        f"started: {ts.isoformat()}\n"
        "session_id: unknown-sess\n"
        "status: in-progress\n"
        "---\n"
    )
    stub.write_text(stub_body, encoding="utf-8")

    projects_root = tmp_path / "projects"
    projects_root.mkdir()
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_root))

    builds.run_build_finish(54, project_dir=project_dir)

    captured = capsys.readouterr()
    assert "Warning" in captured.out or "warning" in captured.out.lower()
    # Stub should not have been rewritten with a complete report
    assert "## Summary" not in stub.read_text(encoding="utf-8")


def test_run_build_finish_roundtrip_with_subagents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Roundtrip: parent turns + subagent JSONL + stage mark → full report."""
    project_dir = _make_project(tmp_path)
    session_id = "test-sid"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    # Write build stub
    stub = project_dir / ".mantle" / "builds" / "build-99-20260412-1000.md"
    stub.write_text(
        "---\n"
        "issue: 99\n"
        f"started: {ts.isoformat()}\n"
        f"session_id: {session_id}\n"
        "status: in-progress\n"
        "---\n",
        encoding="utf-8",
    )

    # Set up parent session JSONL (2 assistant turns)
    projects_root = tmp_path / "projects"
    slug = projects_root / "-slug"
    slug.mkdir(parents=True)
    session_file = slug / f"{session_id}.jsonl"
    parent_records = [
        _assistant_record("p1", None, session_id, ts + timedelta(minutes=5)),
        _assistant_record("p2", "p1", session_id, ts + timedelta(minutes=10)),
    ]
    _write_jsonl(session_file, parent_records)

    # Set up subagent JSONL + meta.json (story-implementer)
    subagents_dir = slug / session_id / "subagents"
    subagents_dir.mkdir(parents=True)
    agent_jsonl = subagents_dir / "agent-1.jsonl"
    agent_meta = subagents_dir / "agent-1.meta.json"
    subagent_records = [
        _assistant_record(
            "a1",
            None,
            "sub-sess",
            ts + timedelta(minutes=6),
            is_sidechain=True,
        ),
        _assistant_record(
            "a2",
            "a1",
            "sub-sess",
            ts + timedelta(minutes=8),
            is_sidechain=True,
        ),
    ]
    _write_jsonl(agent_jsonl, subagent_records)
    agent_meta.write_text(
        json.dumps({"agentType": "story-implementer"}), encoding="utf-8"
    )

    # Write stage mark for "shape" before the parent turns
    telemetry_dir = project_dir / ".mantle" / "telemetry"
    telemetry_dir.mkdir(parents=True)
    stages_file = telemetry_dir / f"stages-{session_id}.jsonl"
    stage_record = {"stage": "shape", "at": ts.isoformat()}
    stages_file.write_text(json.dumps(stage_record) + "\n", encoding="utf-8")

    monkeypatch.setenv("CLAUDE_SESSION_ID", session_id)
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_root))

    builds.run_build_finish(99, project_dir=project_dir)

    text = stub.read_text(encoding="utf-8")
    normalized = _normalize(text)
    assert normalized == snapshot("""\
---
issue: 99
session_id: test-sid
started: <TS>
finished: <TS>
stories:
  - story_id: null
    stage: shape
    model: claude-opus-4-6
    started: <TS>
    finished: <TS>
    duration_s: 0.0
    turn_count: 1
    input_tokens: 10
    output_tokens: 20
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
  - story_id: null
    stage: implement
    model: claude-opus-4-6
    started: <TS>
    finished: <TS>
    duration_s: 120.0
    turn_count: 2
    input_tokens: 20
    output_tokens: 40
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
build_finished: <TS>
status: complete
---

## Summary

### shape

| Story | Model | Duration (s) | Turns | In tok | Out tok |
|-------|-------|--------------|-------|--------|---------|
| — | claude-opus-4-6 | 0.0 | 1 | 10 | 20 |

### implement

| Story | Model | Duration (s) | Turns | In tok | Out tok |
|-------|-------|--------------|-------|--------|---------|
| — | claude-opus-4-6 | 120.0 | 2 | 20 | 40 |
""")


def test_run_build_finish_no_stages_no_subagents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only parent JSONL + stub; no stages file; no subagents."""
    project_dir = _make_project(tmp_path)
    session_id = "test-sid-bare"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    stub = project_dir / ".mantle" / "builds" / "build-99-20260412-1000.md"
    stub.write_text(
        "---\n"
        "issue: 99\n"
        f"started: {ts.isoformat()}\n"
        f"session_id: {session_id}\n"
        "status: in-progress\n"
        "---\n",
        encoding="utf-8",
    )

    projects_root = tmp_path / "projects"
    slug = projects_root / "-slug"
    slug.mkdir(parents=True)
    session_file = slug / f"{session_id}.jsonl"
    records = [
        _assistant_record("p1", None, session_id, ts + timedelta(minutes=1)),
    ]
    _write_jsonl(session_file, records)

    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_root))

    builds.run_build_finish(99, project_dir=project_dir)

    text = stub.read_text(encoding="utf-8")
    assert "status: complete" in text
    assert "## Summary" in text
    # No story runs because no subagents and no stage windows
    assert "No story runs detected" in text


def test_run_build_finish_empty_parent_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parent JSONL with zero assistant turns; fallback to datetime.now(UTC)."""
    project_dir = _make_project(tmp_path)
    session_id = "test-sid-empty"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    stub = project_dir / ".mantle" / "builds" / "build-99-20260412-1000.md"
    stub.write_text(
        "---\n"
        "issue: 99\n"
        f"started: {ts.isoformat()}\n"
        f"session_id: {session_id}\n"
        "status: in-progress\n"
        "---\n",
        encoding="utf-8",
    )

    projects_root = tmp_path / "projects"
    slug = projects_root / "-slug"
    slug.mkdir(parents=True)
    # Write a JSONL with only non-assistant records (zero parsed turns)
    session_file = slug / f"{session_id}.jsonl"
    session_file.write_text(
        json.dumps({"type": "user", "content": "hello"}) + "\n", encoding="utf-8"
    )

    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_root))

    # Should not raise; uses datetime.now(UTC) as session_end fallback
    builds.run_build_finish(99, project_dir=project_dir)

    text = stub.read_text(encoding="utf-8")
    assert "status: complete" in text
    assert "## Summary" in text
    assert "No story runs detected" in text


def test_run_build_finish_drops_old_markers_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """stories/ directory files do NOT drive story attribution (Marker gone)."""
    project_dir = _make_project(tmp_path)
    session_id = "test-sid-marker"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    # Story files that the old _derive_mtime_markers would have picked up
    stories_dir = project_dir / ".mantle" / "stories"
    (stories_dir / "issue-99-story-01.md").write_text("s1\n", encoding="utf-8")
    (stories_dir / "issue-99-story-02.md").write_text("s2\n", encoding="utf-8")

    stub = project_dir / ".mantle" / "builds" / "build-99-20260412-1000.md"
    stub.write_text(
        "---\n"
        "issue: 99\n"
        f"started: {ts.isoformat()}\n"
        f"session_id: {session_id}\n"
        "status: in-progress\n"
        "---\n",
        encoding="utf-8",
    )

    projects_root = tmp_path / "projects"
    slug = projects_root / "-slug"
    slug.mkdir(parents=True)
    session_file = slug / f"{session_id}.jsonl"
    records = [
        _assistant_record("p1", None, session_id, ts + timedelta(minutes=1)),
    ]
    _write_jsonl(session_file, records)

    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_root))

    builds.run_build_finish(99, project_dir=project_dir)

    text = stub.read_text(encoding="utf-8")
    # Old mtime-marker approach would have produced story_id: 1 and story_id: 2
    # The new approach should not produce story_id entries from story files alone
    assert "story_id: 1" not in text
    assert "story_id: 2" not in text
    assert "status: complete" in text
