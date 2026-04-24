"""Self-tests for the parity harness and normalizer."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import pytest

from mantle.core import compiler
from tests.parity import fixtures, harness

if TYPE_CHECKING:
    from pathlib import Path


# ── normalize_prompt_output ──────────────────────────────────────


def test_normalize_replaces_iso_timestamp() -> None:
    text = "Last run: 2026-04-24T12:32:00Z done."
    result = harness.normalize_prompt_output(text)
    assert result == "Last run: <TIMESTAMP> done."


def test_normalize_replaces_iso_date() -> None:
    text = "Updated on 2026-04-24 by user."
    result = harness.normalize_prompt_output(text)
    assert result == "Updated on <DATE> by user."


def test_normalize_replaces_session_uuid() -> None:
    text = "Session: 550e8400-e29b-41d4-a716-446655440000 active."
    result = harness.normalize_prompt_output(text)
    assert result == "Session: <SESSION_ID> active."


def test_normalize_replaces_absolute_path() -> None:
    text_users = "Config at /Users/foo/bar found."
    result_users = harness.normalize_prompt_output(text_users)
    assert result_users == "Config at <PATH> found."

    text_tmp = "Temp file /tmp/x exists."
    result_tmp = harness.normalize_prompt_output(text_tmp)
    assert result_tmp == "Temp file <PATH> exists."


def test_normalize_replaces_git_sha() -> None:
    text_short = "Commit a1b2c3d merged."
    result_short = harness.normalize_prompt_output(text_short)
    assert result_short == "Commit <GIT_SHA> merged."

    text_long = "SHA a1b2c3d4e5f6789012345678901234567890abcd tagged."
    result_long = harness.normalize_prompt_output(text_long)
    assert result_long == "SHA <GIT_SHA> tagged."

    text_bounded = "Identifier a1b2c3d_other should not match."
    result_bounded = harness.normalize_prompt_output(text_bounded)
    assert result_bounded == "Identifier a1b2c3d_other should not match."


def test_normalize_preserves_non_volatile_text() -> None:
    text = (
        "def run_prompt_parity(command: str, fixture: Path) -> ParityResult:"
        " return result"
    )
    result = harness.normalize_prompt_output(text)
    assert result == text


# ── ParityResult ─────────────────────────────────────────────────


def test_parity_result_dataclass_is_frozen() -> None:
    result = harness.ParityResult(
        command="build",
        baseline_text="x",
        current_text="x",
        matches=True,
        diff="",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.matches = False  # type: ignore[misc]


# ── run_prompt_parity ────────────────────────────────────────────


def test_run_prompt_parity_static_command_matches(tmp_path: Path) -> None:
    tpl_dir = compiler.template_dir()
    raw = (tpl_dir / "build.md").read_text(encoding="utf-8")
    expected = harness.normalize_prompt_output(raw)

    result = harness.run_prompt_parity("build", tmp_path, baseline=expected)

    assert result.matches is True
    assert result.diff == ""
    assert result.command == "build"


def test_run_prompt_parity_static_command_mismatch(tmp_path: Path) -> None:
    tpl_dir = compiler.template_dir()
    raw = (tpl_dir / "build.md").read_text(encoding="utf-8")
    expected = harness.normalize_prompt_output(raw)
    altered_baseline = "ALTERED\n" + expected

    result = harness.run_prompt_parity(
        "build", tmp_path, baseline=altered_baseline
    )

    assert result.matches is False
    assert "---" in result.diff
    assert "+++" in result.diff
    assert "@@" in result.diff


# ── build_sandbox_fixture ────────────────────────────────────────


def test_build_sandbox_fixture_creates_mantle_tree(tmp_path: Path) -> None:
    root = fixtures.build_sandbox_fixture(tmp_path)

    assert root is tmp_path
    state_path = tmp_path / ".mantle" / "state.md"
    assert state_path.exists()

    text = state_path.read_text(encoding="utf-8")
    assert "project: sandbox" in text
    assert "status: planning" in text
