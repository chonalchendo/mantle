"""Tests for mantle.cli.product_design."""

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
    """Create a minimal .mantle/ with state.md at CHALLENGE."""
    (tmp_path / ".mantle").mkdir()
    st = ProjectState(
        project="test-project",
        status=Status.CHALLENGE,
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    body = (
        "## Summary\n\n"
        "Feedback loops are too slow"
        " — Persistent context eliminates ramp-up time\n\n"
        "## Current Focus\n\n"
        "Challenge completed"
        " — run /mantle:design-product next.\n\n"
        "## Blockers\n\n"
        "_Anything preventing progress?_\n"
    )
    vault.write_note(tmp_path / ".mantle" / "state.md", st, body)
    return tmp_path


_DEFAULTS: dict[str, object] = {
    "vision": "Persistent AI context that eliminates ramp-up",
    "principles": (
        "Context must persist across sessions",
        "Every stage decomposes into building blocks",
    ),
    "building_blocks": (
        "Structured idea capture",
        "Challenge sessions",
        "Product design workflow",
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
}


# -- run_save_product_design --------------------------------------


class TestRunSaveProductDesign:
    def test_prints_success(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_save_product_design,
        )

        run_save_product_design(
            **_DEFAULTS,
            project_dir=project,  # type: ignore[arg-type]
        )
        captured = capsys.readouterr()

        assert "Product design saved" in captured.out

    def test_prints_vision(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_save_product_design,
        )

        run_save_product_design(
            **_DEFAULTS,
            project_dir=project,  # type: ignore[arg-type]
        )
        captured = capsys.readouterr()

        assert "Persistent AI context" in captured.out

    def test_prints_building_block_count(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_save_product_design,
        )

        run_save_product_design(
            **_DEFAULTS,
            project_dir=project,  # type: ignore[arg-type]
        )
        captured = capsys.readouterr()

        assert "Building blocks: 3" in captured.out

    def test_prints_next_step(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_save_product_design,
        )

        run_save_product_design(
            **_DEFAULTS,
            project_dir=project,  # type: ignore[arg-type]
        )
        captured = capsys.readouterr()

        assert "/mantle:design-system" in captured.out

    def test_warns_on_existing(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_save_product_design,
        )

        run_save_product_design(
            **_DEFAULTS,
            project_dir=project,  # type: ignore[arg-type]
        )

        with pytest.raises(SystemExit, match="1"):
            run_save_product_design(
                **_DEFAULTS,
                project_dir=project,  # type: ignore[arg-type]
            )

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_overwrite_succeeds(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_save_product_design,
        )

        run_save_product_design(
            **_DEFAULTS,
            project_dir=project,  # type: ignore[arg-type]
        )
        run_save_product_design(
            **_DEFAULTS,  # type: ignore[arg-type]
            overwrite=True,
            project_dir=project,
        )

        from mantle.core.product_design import (
            load_product_design,
        )

        loaded = load_product_design(project)
        assert loaded.vision == (
            "Persistent AI context that eliminates ramp-up"
        )

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.product_design import (
            run_save_product_design,
        )

        run_save_product_design(**_DEFAULTS)  # type: ignore[arg-type]
        captured = capsys.readouterr()

        assert "Product design saved" in captured.out


# -- CLI wiring ---------------------------------------------------


class TestCLIWiring:
    def test_save_product_design_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-product-design",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "vision" in result.stdout.lower()
        assert "principles" in result.stdout.lower()
        assert "building-blocks" in result.stdout.lower()
