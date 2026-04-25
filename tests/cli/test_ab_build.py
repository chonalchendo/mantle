"""Tests for mantle CLI ab-build-compare command."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from mantle.cli import groups as cli_groups
from mantle.cli import main as main_module

if TYPE_CHECKING:
    from pathlib import Path


# ── Fixture helpers ──────────────────────────────────────────────


def _assistant_record(
    uuid: str,
    parent_uuid: str | None,
    session_id: str,
    timestamp: datetime,
    model: str = "claude-opus-4-5",
    is_sidechain: bool = False,
    input_tokens: int = 100,
    output_tokens: int = 50,
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


def _write_cost_policy(project_dir: Path, model: str = "claude-opus-4-5") -> None:
    """Write a minimal .mantle/cost-policy.md with a prices block."""
    mantle_dir = project_dir / ".mantle"
    mantle_dir.mkdir(parents=True, exist_ok=True)
    cost_policy = mantle_dir / "cost-policy.md"
    cost_policy.write_text(
        f"---\nprices:\n"
        f"  {model}:\n"
        f"    input: 15.0\n"
        f"    output: 75.0\n"
        f"    cache_read: 1.5\n"
        f"    cache_write: 18.75\n"
        "---\n",
        encoding="utf-8",
    )


def _write_build_file(path: Path, session_id: str, issue: int = 1) -> None:
    """Write a minimal build report file with session_id frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nissue: {issue}\nsession_id: {session_id}\nstatus: complete\n---\n",
        encoding="utf-8",
    )


def _setup_session_jsonl(
    projects_dir: Path,
    session_id: str,
    base_ts: datetime,
    with_subagent: bool = False,
    subagent_meta_agent_type: str | None = "story-implementer",
    subagent_has_meta: bool = True,
) -> None:
    """Create a minimal Claude projects directory structure with session JSONL."""
    slug_dir = projects_dir / "-test-project"
    slug_dir.mkdir(parents=True, exist_ok=True)

    # Parent session JSONL
    session_file = slug_dir / f"{session_id}.jsonl"
    records = [
        _assistant_record("u1", None, session_id, base_ts),
        _assistant_record(
            "u2", "u1", session_id, base_ts + timedelta(seconds=10)
        ),
    ]
    _write_jsonl(session_file, records)

    if with_subagent:
        # Sub-agent directory + JSONL
        subagent_dir = slug_dir / session_id / "subagents"
        subagent_dir.mkdir(parents=True, exist_ok=True)
        agent_jsonl = subagent_dir / "agent-001.jsonl"
        sub_records = [
            _assistant_record(
                "s1", None, session_id, base_ts + timedelta(seconds=5),
                is_sidechain=True,
            ),
        ]
        _write_jsonl(agent_jsonl, sub_records)

        if subagent_has_meta and subagent_meta_agent_type is not None:
            meta_file = subagent_dir / "agent-001.meta.json"
            meta_file.write_text(
                json.dumps({"agentType": subagent_meta_agent_type}),
                encoding="utf-8",
            )


# ── test_run_ab_build_compare_prints_report_to_stdout ────────────


def test_run_ab_build_compare_prints_report_to_stdout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Command prints a valid A/B report to stdout when no --output given."""
    projects_dir = tmp_path / "projects"
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_dir))

    _write_cost_policy(tmp_path)

    base_ts = datetime(2026, 4, 10, 12, 0, 0, tzinfo=UTC)
    sid_a = "session-baseline-001"
    sid_b = "session-candidate-001"

    _setup_session_jsonl(projects_dir, sid_a, base_ts)
    _setup_session_jsonl(
        projects_dir, sid_b, base_ts + timedelta(minutes=30)
    )

    builds_dir = tmp_path / ".mantle" / "builds"
    baseline_file = builds_dir / "build-baseline.md"
    candidate_file = builds_dir / "build-candidate.md"
    _write_build_file(baseline_file, sid_a, issue=10)
    _write_build_file(candidate_file, sid_b, issue=10)

    with pytest.raises(SystemExit) as exc_info:
        main_module.app(
            [
                "ab-build-compare",
                "--baseline",
                str(baseline_file),
                "--candidate",
                str(candidate_file),
                "--path",
                str(tmp_path),
            ]
        )
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    output = captured.out
    assert "# A/B build comparison" in output
    assert "## Grand Totals" in output
    assert "## Quality" in output
    # No sentinel substrings
    for sentinel in ("<fill>", "TBD", "pending", "<x>", "<y>"):
        assert sentinel not in output, f"sentinel {sentinel!r} found in output"


# ── test_run_ab_build_compare_writes_to_output_path ─────────────


def test_run_ab_build_compare_writes_to_output_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Command writes report to --output path and logs Report written."""
    projects_dir = tmp_path / "projects"
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_dir))

    _write_cost_policy(tmp_path)

    base_ts = datetime(2026, 4, 10, 12, 0, 0, tzinfo=UTC)
    sid_a = "session-baseline-002"
    sid_b = "session-candidate-002"

    _setup_session_jsonl(projects_dir, sid_a, base_ts)
    _setup_session_jsonl(
        projects_dir, sid_b, base_ts + timedelta(minutes=30)
    )

    builds_dir = tmp_path / ".mantle" / "builds"
    baseline_file = builds_dir / "build-baseline.md"
    candidate_file = builds_dir / "build-candidate.md"
    _write_build_file(baseline_file, sid_a, issue=10)
    _write_build_file(candidate_file, sid_b, issue=10)

    output_file = tmp_path / "compare.md"

    with pytest.raises(SystemExit) as exc_info:
        main_module.app(
            [
                "ab-build-compare",
                "--baseline",
                str(baseline_file),
                "--candidate",
                str(candidate_file),
                "--output",
                str(output_file),
                "--path",
                str(tmp_path),
            ]
        )
    assert exc_info.value.code == 0

    assert output_file.exists()
    file_contents = output_file.read_text(encoding="utf-8")
    assert "# A/B build comparison" in file_contents

    captured = capsys.readouterr()
    assert "Report written" in captured.out


# ── test_run_ab_build_compare_errors_on_missing_session_id ───────


def test_run_ab_build_compare_errors_on_missing_session_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Command prints Error and returns when baseline has no session_id."""
    projects_dir = tmp_path / "projects"
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_dir))

    _write_cost_policy(tmp_path)

    builds_dir = tmp_path / ".mantle" / "builds"
    baseline_file = builds_dir / "build-no-session.md"
    candidate_file = builds_dir / "build-candidate.md"

    # Baseline has no session_id
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    baseline_file.write_text(
        "---\nissue: 10\nstatus: complete\n---\n",
        encoding="utf-8",
    )
    _write_build_file(candidate_file, "some-session", issue=10)

    with pytest.raises(SystemExit) as exc_info:
        main_module.app(
            [
                "ab-build-compare",
                "--baseline",
                str(baseline_file),
                "--candidate",
                str(candidate_file),
                "--path",
                str(tmp_path),
            ]
        )
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "Error" in captured.out
    assert "session_id" in captured.out


# ── test_run_ab_build_compare_errors_on_missing_prices_block ─────


def test_run_ab_build_compare_errors_on_missing_prices_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Command prints Error and returns when cost-policy.md lacks prices."""
    projects_dir = tmp_path / "projects"
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_dir))

    # Write cost-policy.md without a prices block
    mantle_dir = tmp_path / ".mantle"
    mantle_dir.mkdir(parents=True, exist_ok=True)
    (mantle_dir / "cost-policy.md").write_text(
        "---\npresets: {}\n---\n",
        encoding="utf-8",
    )

    base_ts = datetime(2026, 4, 10, 12, 0, 0, tzinfo=UTC)
    sid_a = "session-baseline-003"
    sid_b = "session-candidate-003"

    _setup_session_jsonl(projects_dir, sid_a, base_ts)
    _setup_session_jsonl(
        projects_dir, sid_b, base_ts + timedelta(minutes=30)
    )

    builds_dir = tmp_path / ".mantle" / "builds"
    baseline_file = builds_dir / "build-baseline.md"
    candidate_file = builds_dir / "build-candidate.md"
    _write_build_file(baseline_file, sid_a, issue=10)
    _write_build_file(candidate_file, sid_b, issue=10)

    output_file = tmp_path / "compare.md"

    with pytest.raises(SystemExit) as exc_info:
        main_module.app(
            [
                "ab-build-compare",
                "--baseline",
                str(baseline_file),
                "--candidate",
                str(candidate_file),
                "--output",
                str(output_file),
                "--path",
                str(tmp_path),
            ]
        )
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "Error" in captured.out
    assert "prices" in captured.out
    # No report file written
    assert not output_file.exists()


# ── test_run_ab_build_compare_renders_unattributed_bucket ────────


def test_run_ab_build_compare_renders_attributed_stages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Report contains stage cost sections for attributed sub-agents."""
    projects_dir = tmp_path / "projects"
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_dir))

    _write_cost_policy(tmp_path)

    base_ts = datetime(2026, 4, 10, 12, 0, 0, tzinfo=UTC)
    sid_a = "session-baseline-004"
    sid_b = "session-candidate-004"

    # Both builds have a story-implementer sub-agent -> stage=implement
    _setup_session_jsonl(
        projects_dir, sid_a, base_ts, with_subagent=True,
        subagent_meta_agent_type="story-implementer",
    )
    _setup_session_jsonl(
        projects_dir, sid_b, base_ts + timedelta(minutes=30),
        with_subagent=True,
        subagent_meta_agent_type="story-implementer",
    )

    builds_dir = tmp_path / ".mantle" / "builds"
    baseline_file = builds_dir / "build-baseline.md"
    candidate_file = builds_dir / "build-candidate.md"
    _write_build_file(baseline_file, sid_a, issue=10)
    _write_build_file(candidate_file, sid_b, issue=10)

    with pytest.raises(SystemExit) as exc_info:
        main_module.app(
            [
                "ab-build-compare",
                "--baseline",
                str(baseline_file),
                "--candidate",
                str(candidate_file),
                "--path",
                str(tmp_path),
            ]
        )
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    output = captured.out
    # story-implementer -> implement stage
    assert "## Cost — implement" in output
    assert "## Cost — Unattributed" not in output


def test_run_ab_build_compare_renders_unattributed_bucket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture,
) -> None:
    """Report contains Unattributed bucket when meta.json is missing."""
    projects_dir = tmp_path / "projects"
    monkeypatch.setenv("CLAUDE_PROJECTS_DIR", str(projects_dir))

    _write_cost_policy(tmp_path)

    base_ts = datetime(2026, 4, 10, 12, 0, 0, tzinfo=UTC)
    sid_a = "session-baseline-005"
    sid_b = "session-candidate-005"

    # Sub-agent with no meta.json -> stage=None -> Unattributed
    _setup_session_jsonl(
        projects_dir, sid_a, base_ts, with_subagent=True,
        subagent_has_meta=False,
    )
    _setup_session_jsonl(
        projects_dir, sid_b, base_ts + timedelta(minutes=30),
        with_subagent=True,
        subagent_has_meta=False,
    )

    builds_dir = tmp_path / ".mantle" / "builds"
    baseline_file = builds_dir / "build-baseline.md"
    candidate_file = builds_dir / "build-candidate.md"
    _write_build_file(baseline_file, sid_a, issue=10)
    _write_build_file(candidate_file, sid_b, issue=10)

    with pytest.raises(SystemExit) as exc_info:
        main_module.app(
            [
                "ab-build-compare",
                "--baseline",
                str(baseline_file),
                "--candidate",
                str(candidate_file),
                "--path",
                str(tmp_path),
            ]
        )
    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "## Cost — Unattributed" in captured.out


# ── test_ab_build_compare_command_registered_in_review_group ─────


def test_ab_build_compare_command_registered_in_review_group() -> None:
    """ab-build-compare command is registered under the review group."""
    group_values = set(cli_groups.GROUPS.values())
    assert "ab-build-compare" in main_module.app

    cmd = main_module.app["ab-build-compare"]
    cmd_groups = getattr(cmd, "group", None)
    assert cmd_groups, "ab-build-compare has no group assigned"
    assert any(g in group_values for g in cmd_groups), (
        f"ab-build-compare group {cmd_groups!r} not in GROUPS"
    )
    review_group = cli_groups.GROUPS["review"]
    assert any(g == review_group for g in cmd_groups), (
        f"ab-build-compare not in review group; got {cmd_groups!r}"
    )
