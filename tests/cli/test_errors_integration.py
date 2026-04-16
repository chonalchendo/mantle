"""Integration tests for CLI error migration — stderr + hint shape."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mantle.cli import compile as compile_cmd
from mantle.cli import stories as stories_cmd

if TYPE_CHECKING:
    from pathlib import Path


class TestErrorsGoToStderr:
    def test_compile_outside_project_exits_with_hint(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            compile_cmd.run_compile(project_dir=tmp_path)

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Error:" in captured.err
        assert "mantle init" in captured.err

    def test_update_story_status_missing_story_exits_with_hint(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / ".mantle" / "stories").mkdir(parents=True)

        with pytest.raises(SystemExit) as exc:
            stories_cmd.run_update_story_status(
                issue=1,
                story=99,
                status="in-progress",
                project_dir=tmp_path,
            )

        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Error:" in captured.err
        assert "mantle list-stories" in captured.err
