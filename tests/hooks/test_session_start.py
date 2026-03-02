"""Tests for the session-start.sh hook script."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

HOOK_SCRIPT = (
    Path(__file__).parent.parent.parent
    / "claude"
    / "hooks"
    / "session-start.sh"
)

_BASH = shutil.which("bash") or "/bin/bash"


def _run_hook(
    cwd: Path, *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Run the session-start hook in a given directory."""
    return subprocess.run(
        [_BASH, str(HOOK_SCRIPT)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


class TestSessionStartHook:
    def test_exits_zero_without_mantle_dir(self, tmp_path: Path) -> None:
        result = _run_hook(tmp_path)

        assert result.returncode == 0

    def test_no_output_without_mantle_dir(self, tmp_path: Path) -> None:
        result = _run_hook(tmp_path)

        assert result.stdout == ""

    def test_exits_zero_with_mantle_dir(self, tmp_path: Path) -> None:
        (tmp_path / ".mantle").mkdir()
        result = _run_hook(tmp_path)

        assert result.returncode == 0

    def test_outputs_resume_when_exists(self, tmp_path: Path) -> None:
        (tmp_path / ".mantle").mkdir()

        # Set up a fake $HOME with resume.md
        fake_home = tmp_path / "fakehome"
        resume_path = fake_home / ".claude" / "commands" / "mantle"
        resume_path.mkdir(parents=True)
        (resume_path / "resume.md").write_text("Briefing content here.")

        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        # Minimal PATH: system bins for cat, no mantle
        env["PATH"] = "/usr/bin:/bin"

        result = _run_hook(tmp_path, env=env)

        assert "Briefing content here." in result.stdout

    def test_no_output_when_resume_missing(self, tmp_path: Path) -> None:
        (tmp_path / ".mantle").mkdir()

        env = os.environ.copy()
        # Point HOME to a dir without resume.md
        env["HOME"] = str(tmp_path / "empty_home")
        env["PATH"] = "/usr/bin:/bin"

        result = _run_hook(tmp_path, env=env)

        assert result.stdout == ""
