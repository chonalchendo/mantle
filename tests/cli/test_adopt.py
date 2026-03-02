"""Tests for mantle.cli.adopt."""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from typing import TYPE_CHECKING

import pytest

from mantle.core import vault
from mantle.core.state import ProjectState, Status

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"

_DEFAULTS: dict[str, object] = {
    "vision": "Persistent AI context that eliminates ramp-up",
    "principles": (
        "Context must persist across sessions",
        "Every stage decomposes into building blocks",
    ),
    "building_blocks": (
        "Structured idea capture",
        "Challenge sessions",
    ),
    "prior_art": (
        "Obsidian vault for persistent notes",
        "Claude Code slash commands",
    ),
    "composition": (
        "Slash commands drive a staged workflow whose"
        " outputs accumulate in an Obsidian vault"
    ),
    "target_users": "Solo developers using Claude Code",
    "success_metrics": (
        "Ship MVP in 2 weeks",
        "5 active users in first month",
    ),
    "system_design_content": ("## Architecture\n\nLayered design.\n"),
}


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state at IDEA."""
    (tmp_path / ".mantle").mkdir()
    st = ProjectState(
        project="test-project",
        status=Status.IDEA,
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    body = (
        "## Summary\n\n"
        "Test project summary\n\n"
        "## Current Focus\n\n"
        "_What are you working on right now?_\n\n"
        "## Blockers\n\n"
        "_Anything preventing progress?_\n"
    )
    vault.write_note(tmp_path / ".mantle" / "state.md", st, body)
    return tmp_path


# ── run_save_adoption ────────────────────────────────────────────


class TestRunSaveAdoption:
    def test_prints_adoption_complete(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.adopt import run_save_adoption

        run_save_adoption(**_DEFAULTS, project_dir=project)
        captured = capsys.readouterr()

        assert "Adoption complete" in captured.out

    def test_prints_vision(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.adopt import run_save_adoption

        run_save_adoption(**_DEFAULTS, project_dir=project)
        captured = capsys.readouterr()

        assert "eliminates ramp-up" in captured.out

    def test_prints_building_block_count(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.adopt import run_save_adoption

        run_save_adoption(**_DEFAULTS, project_dir=project)
        captured = capsys.readouterr()

        assert "2 building blocks" in captured.out

    def test_prints_next_step(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.adopt import run_save_adoption

        run_save_adoption(**_DEFAULTS, project_dir=project)
        captured = capsys.readouterr()

        assert "/mantle:plan-issues" in captured.out

    def test_warns_on_existing_docs(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.adopt import run_save_adoption

        (project / ".mantle" / "product-design.md").write_text("existing")

        with pytest.raises(SystemExit, match="1"):
            run_save_adoption(**_DEFAULTS, project_dir=project)

        captured = capsys.readouterr()
        assert "already exist" in captured.out

    def test_errors_on_wrong_state(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / ".mantle").mkdir()
        st = ProjectState(
            project="test-project",
            status=Status.PLANNING,
            created=date(2025, 1, 1),
            created_by=MOCK_EMAIL,
            updated=date(2025, 1, 1),
            updated_by=MOCK_EMAIL,
        )
        body = (
            "## Summary\n\nTest\n\n"
            "## Current Focus\n\nTest\n\n"
            "## Blockers\n\n_None_\n"
        )
        vault.write_note(tmp_path / ".mantle" / "state.md", st, body)

        from mantle.cli.adopt import run_save_adoption

        with pytest.raises(SystemExit, match="1"):
            run_save_adoption(**_DEFAULTS, project_dir=tmp_path)

        captured = capsys.readouterr()
        assert "planning" in captured.out
        assert "adoption requires" in captured.out

    def test_overwrite_succeeds(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.adopt import run_save_adoption

        (project / ".mantle" / "product-design.md").write_text("existing")
        (project / ".mantle" / "system-design.md").write_text("existing")

        run_save_adoption(
            **_DEFAULTS,
            overwrite=True,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Adoption complete" in captured.out

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.adopt import run_save_adoption

        run_save_adoption(**_DEFAULTS)
        captured = capsys.readouterr()

        assert "Adoption complete" in captured.out


# ── CLI wiring ───────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_adoption_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-adoption",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "vision" in result.stdout.lower()
