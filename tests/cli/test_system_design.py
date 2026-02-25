"""Tests for mantle.cli.system_design."""

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


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state at product-design."""
    (tmp_path / ".mantle").mkdir()
    st = ProjectState(
        project="test-project",
        status=Status.PRODUCT_DESIGN,
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    body = (
        "## Summary\n\n"
        "Test project summary\n\n"
        "## Current Focus\n\n"
        "Product design complete"
        " — run /mantle:design-system next.\n\n"
        "## Blockers\n\n"
        "_Anything preventing progress?_\n"
    )
    vault.write_note(tmp_path / ".mantle" / "state.md", st, body)
    return tmp_path


CONTENT = "## Architecture\n\nLayered design.\n"


# ── run_save_system_design ─────────────────────────────────────


class TestRunSaveSystemDesign:
    def test_prints_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.system_design import (
            run_save_system_design,
        )

        run_save_system_design(
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "System design saved" in captured.out

    def test_prints_next_step(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.system_design import (
            run_save_system_design,
        )

        run_save_system_design(
            content=CONTENT,
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "/mantle:plan-issues" in captured.out

    def test_warns_on_existing(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.system_design import (
            run_save_system_design,
        )

        run_save_system_design(
            content=CONTENT,
            project_dir=project,
        )

        # Reset state to product-design for second attempt
        st = ProjectState(
            project="test-project",
            status=Status.PRODUCT_DESIGN,
            created=date(2025, 1, 1),
            created_by=MOCK_EMAIL,
            updated=date(2025, 1, 1),
            updated_by=MOCK_EMAIL,
        )
        body = "## Summary\n\nTest\n\n## Current Focus\n\nTest\n"
        vault.write_note(project / ".mantle" / "state.md", st, body)

        with pytest.raises(SystemExit, match="1"):
            run_save_system_design(
                content="New content",
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_warns_on_invalid_transition(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / ".mantle").mkdir()
        st = ProjectState(
            project="test-project",
            status=Status.IDEA,
            created=date(2025, 1, 1),
            created_by=MOCK_EMAIL,
            updated=date(2025, 1, 1),
            updated_by=MOCK_EMAIL,
        )
        body = "## Summary\n\nTest\n\n## Current Focus\n\nTest\n"
        vault.write_note(tmp_path / ".mantle" / "state.md", st, body)

        from mantle.cli.system_design import (
            run_save_system_design,
        )

        with pytest.raises(SystemExit, match="1"):
            run_save_system_design(
                content=CONTENT,
                project_dir=tmp_path,
            )

        captured = capsys.readouterr()
        assert "design-product" in captured.out

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.system_design import (
            run_save_system_design,
        )

        run_save_system_design(content=CONTENT)
        captured = capsys.readouterr()

        assert "System design saved" in captured.out


# ── CLI wiring ──────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_system_design_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-system-design",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "content" in result.stdout.lower()
