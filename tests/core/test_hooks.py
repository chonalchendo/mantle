"""Tests for mantle.core.hooks lifecycle dispatch."""

from __future__ import annotations

import logging
import stat
from typing import TYPE_CHECKING

from mantle.core import hooks, project

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _init_project(tmp_path: Path) -> Path:
    """Initialize a minimal .mantle/ for hook tests."""
    project.init_project(tmp_path, "test-project")
    return tmp_path


def _write_hook(project_dir: Path, event: str, body: str) -> Path:
    """Write an executable on-<event>.sh script under .mantle/hooks/."""
    hooks_dir = project_dir / ".mantle" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    script = hooks_dir / f"on-{event}.sh"
    script.write_text("#!/usr/bin/env bash\n" + body)
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def test_missing_script_is_silent_noop(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING, logger="mantle.core.hooks")
    _init_project(tmp_path)
    hooks.dispatch(
        "issue-shaped",
        issue=42,
        status="shaped",
        title="demo",
        project_dir=tmp_path,
    )
    assert caplog.records == []


def test_dispatch_invokes_script_with_positional_args(
    tmp_path: Path,
) -> None:
    _init_project(tmp_path)
    marker = tmp_path / "marker.txt"
    _write_hook(
        tmp_path,
        "issue-shaped",
        f'echo "$1|$2|$3" > {marker}\n',
    )
    hooks.dispatch(
        "issue-shaped",
        issue=42,
        status="shaped",
        title="My Title",
        project_dir=tmp_path,
    )
    assert marker.read_text().strip() == "42|shaped|My Title"


def test_dispatch_exports_hooks_env(tmp_path: Path) -> None:
    _init_project(tmp_path)
    config = tmp_path / ".mantle" / "config.md"
    config.write_text(
        "---\n"
        "hooks_env:\n"
        "  JIRA_BASE_URL: https://example.atlassian.net\n"
        "  TEAM: platform\n"
        "tags: [type/config]\n"
        "---\n\n## Body\n"
    )
    marker = tmp_path / "env.txt"
    _write_hook(
        tmp_path,
        "issue-shaped",
        f'echo "$JIRA_BASE_URL|$TEAM" > {marker}\n',
    )
    hooks.dispatch(
        "issue-shaped",
        issue=1,
        status="shaped",
        title="x",
        project_dir=tmp_path,
    )
    assert marker.read_text().strip() == (
        "https://example.atlassian.net|platform"
    )


def test_non_zero_exit_warns_and_does_not_raise(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.WARNING, logger="mantle.core.hooks")
    _init_project(tmp_path)
    _write_hook(tmp_path, "issue-shaped", "exit 7\n")
    hooks.dispatch(
        "issue-shaped",
        issue=1,
        status="shaped",
        title="x",
        project_dir=tmp_path,
    )
    assert any(
        "exited 7" in r.message and r.levelname == "WARNING"
        for r in caplog.records
    )


def test_timeout_warns_and_does_not_raise(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    caplog.set_level(logging.WARNING, logger="mantle.core.hooks")
    _init_project(tmp_path)
    _write_hook(tmp_path, "issue-shaped", "sleep 10\n")
    monkeypatch.setattr(hooks, "HOOK_TIMEOUT_SECONDS", 0.2)
    hooks.dispatch(
        "issue-shaped",
        issue=1,
        status="shaped",
        title="x",
        project_dir=tmp_path,
    )
    assert any(
        "timed out" in r.message and r.levelname == "WARNING"
        for r in caplog.records
    )


def test_malformed_config_degrades_to_empty_env(tmp_path: Path) -> None:
    _init_project(tmp_path)
    config = tmp_path / ".mantle" / "config.md"
    config.write_text("---\nnot: [valid\nyaml\n---\nbody\n")
    marker = tmp_path / "env.txt"
    _write_hook(
        tmp_path,
        "issue-shaped",
        f'echo "${{JIRA_BASE_URL:-unset}}" > {marker}\n',
    )
    hooks.dispatch(
        "issue-shaped",
        issue=1,
        status="shaped",
        title="x",
        project_dir=tmp_path,
    )
    assert marker.read_text().strip() == "unset"
