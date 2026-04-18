"""Integration tests for shipped lifecycle hook example scripts.

Each example is written to a tmp directory, external CLIs (curl, acli)
are stubbed via PATH, and the script is executed end-to-end with the
mantle positional-args contract.
"""

from __future__ import annotations

import os
import stat
import subprocess
from importlib import resources
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _write_example_to(tmp_path: Path, name: str) -> Path:
    """Copy a shipped example script into tmp_path and make it executable."""
    content = (
        resources.files("mantle.assets.hook_examples") / f"{name}.sh"
    ).read_text(encoding="utf-8")
    script = tmp_path / "on-issue-shaped.sh"
    script.write_text(content)
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _stub_binary(tmp_path: Path, name: str) -> None:
    """Create a no-op shim on PATH for an external CLI/curl."""
    stub = tmp_path / name
    stub.write_text("#!/usr/bin/env bash\necho STUB $@\nexit 0\n")
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)


def test_linear_example_runs_structurally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linear example executes with stubbed curl and required env set."""
    _write_example_to(tmp_path, "linear")
    _stub_binary(tmp_path, "curl")
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("LINEAR_API_KEY", "test-key")
    monkeypatch.setenv("LINEAR_TEAM_ID", "test-team")
    result = subprocess.run(
        [str(tmp_path / "on-issue-shaped.sh"), "42", "shaped", "demo"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_jira_example_runs_structurally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Jira example executes with stubbed acli and required env set."""
    _write_example_to(tmp_path, "jira")
    _stub_binary(tmp_path, "acli")
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "PLAT")
    result = subprocess.run(
        [str(tmp_path / "on-issue-shaped.sh"), "42", "shaped", "demo"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_slack_example_runs_structurally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Slack example executes with stubbed curl and required env set."""
    _write_example_to(tmp_path, "slack")
    _stub_binary(tmp_path, "curl")
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://example.invalid/hook")
    result = subprocess.run(
        [str(tmp_path / "on-issue-shaped.sh"), "42", "shaped", "demo"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_unset_required_env_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without LINEAR_API_KEY, `:` parameter expansion exits non-zero."""
    _write_example_to(tmp_path, "linear")
    _stub_binary(tmp_path, "curl")
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    monkeypatch.delenv("LINEAR_TEAM_ID", raising=False)
    result = subprocess.run(
        [str(tmp_path / "on-issue-shaped.sh"), "42", "shaped", "demo"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "LINEAR_API_KEY" in result.stderr
