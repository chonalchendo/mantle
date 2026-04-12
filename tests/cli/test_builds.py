"""Tests for mantle.cli.builds."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

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


def test_build_finish_correlates_stories_by_mtime_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_dir = _make_project(tmp_path)
    session_id = "sess-mtime"
    ts = datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)

    # Stub
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

    # Two story files, mtime set near each sidechain cluster start
    story1 = project_dir / ".mantle" / "stories" / "issue-54-story-01.md"
    story2 = project_dir / ".mantle" / "stories" / "issue-54-story-02.md"
    story1.write_text("story 1\n", encoding="utf-8")
    story2.write_text("story 2\n", encoding="utf-8")
    import os as _os

    mtime1 = (ts + timedelta(seconds=5)).timestamp()
    mtime2 = (ts + timedelta(seconds=105)).timestamp()
    _os.utime(story1, (mtime1, mtime1))
    _os.utime(story2, (mtime2, mtime2))

    # Session with two clusters (around marker 1 and marker 2)
    projects_root = tmp_path / "projects"
    slug = projects_root / "-slug"
    slug.mkdir(parents=True)
    session_file = slug / f"{session_id}.jsonl"
    records = [
        _assistant_record("m1", None, session_id, ts, is_sidechain=False),
        _assistant_record(
            "s1a",
            "m1",
            session_id,
            ts + timedelta(seconds=10),
            is_sidechain=True,
        ),
        _assistant_record(
            "s1b",
            "s1a",
            session_id,
            ts + timedelta(seconds=20),
            is_sidechain=True,
        ),
        _assistant_record(
            "m2",
            "m1",
            session_id,
            ts + timedelta(seconds=100),
            is_sidechain=False,
        ),
        _assistant_record(
            "s2a",
            "m2",
            session_id,
            ts + timedelta(seconds=110),
            is_sidechain=True,
        ),
        _assistant_record(
            "s2b",
            "s2a",
            session_id,
            ts + timedelta(seconds=120),
            is_sidechain=True,
        ),
    ]
    _write_jsonl(session_file, records)
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_root))

    builds.run_build_finish(54, project_dir=project_dir)

    text = stub.read_text(encoding="utf-8")
    assert "story_id: 1" in text
    assert "story_id: 2" in text
