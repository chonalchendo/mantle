"""Tests for mantle.cli.product_design."""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from typing import TYPE_CHECKING

import pytest

from mantle.core import vault
from mantle.core.product_design import (
    ProductDesignNote,
    _build_product_design_body,
)
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

    def test_save_revised_product_design_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-revised-product-design",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "change-topic" in result.stdout.lower()


# -- run_revise_product_design -----------------------------------

_REVISE_DEFAULTS: dict[str, object] = {
    "vision": "Revised vision",
    "principles": ("Revised principle",),
    "building_blocks": ("Revised block",),
    "prior_art": ("Revised art",),
    "composition": "Revised composition",
    "target_users": "Revised users",
    "success_metrics": ("Revised metric",),
    "change_topic": "reframe-vision",
    "change_summary": "Reframed the product vision",
    "change_rationale": "Better alignment with user needs",
}


@pytest.fixture
def project_with_design(tmp_path: Path) -> Path:
    """Create .mantle/ at SYSTEM_DESIGN with existing product design."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "decisions").mkdir()
    st = ProjectState(
        project="test-project",
        status=Status.SYSTEM_DESIGN,
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

    note = ProductDesignNote(
        vision="Original vision",
        principles=("Original principle",),
        building_blocks=("Original block",),
        prior_art=("Original art",),
        composition="Original composition",
        target_users="Original users",
        success_metrics=("Original metric",),
        author=MOCK_EMAIL,
        created=date(2025, 6, 1),
        updated=date(2025, 6, 1),
        updated_by=MOCK_EMAIL,
    )
    vault.write_note(
        mantle / "product-design.md",
        note,
        _build_product_design_body(note),
    )
    return tmp_path


class TestRunReviseProductDesign:
    def test_prints_success(
        self,
        project_with_design: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_revise_product_design,
        )

        run_revise_product_design(
            **_REVISE_DEFAULTS,
            project_dir=project_with_design,  # type: ignore[arg-type]
        )
        captured = capsys.readouterr()

        assert "Product design revised" in captured.out

    def test_prints_change_topic(
        self,
        project_with_design: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_revise_product_design,
        )

        run_revise_product_design(
            **_REVISE_DEFAULTS,
            project_dir=project_with_design,  # type: ignore[arg-type]
        )
        captured = capsys.readouterr()

        assert "reframe-vision" in captured.out

    def test_prints_decision_filename(
        self,
        project_with_design: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_revise_product_design,
        )

        run_revise_product_design(
            **_REVISE_DEFAULTS,
            project_dir=project_with_design,  # type: ignore[arg-type]
        )
        captured = capsys.readouterr()

        assert "reframe-vision" in captured.out
        assert ".md" in captured.out

    def test_warns_on_missing(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.product_design import (
            run_revise_product_design,
        )

        with pytest.raises(SystemExit, match="1"):
            run_revise_product_design(
                **_REVISE_DEFAULTS,
                project_dir=tmp_path,  # type: ignore[arg-type]
            )

        captured = capsys.readouterr()
        assert "does not exist" in captured.out
        assert "/mantle:design-product" in captured.out

    def test_defaults_to_cwd(
        self,
        project_with_design: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project_with_design)

        from mantle.cli.product_design import (
            run_revise_product_design,
        )

        run_revise_product_design(
            **_REVISE_DEFAULTS,  # type: ignore[arg-type]
        )
        captured = capsys.readouterr()

        assert "Product design revised" in captured.out
