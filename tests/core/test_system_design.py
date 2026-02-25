"""Tests for mantle.core.system_design."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import vault
from mantle.core.state import (
    InvalidTransitionError,
    ProjectState,
    Status,
)
from mantle.core.system_design import (
    SystemDesignExistsError,
    load_system_design,
    save_system_design,
    system_design_exists,
)

MOCK_EMAIL = "test@example.com"
CONTENT = (
    "## Architecture\n\n"
    "Layered architecture with core, CLI, and API layers.\n\n"
    "## Technology Choices\n\n"
    "Python 3.14, Pydantic, cyclopts\n"
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state at product-design."""
    (tmp_path / ".mantle").mkdir()
    _write_state(tmp_path, status=Status.PRODUCT_DESIGN)
    return tmp_path


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _write_state(
    project_dir: Path,
    *,
    status: Status = Status.PRODUCT_DESIGN,
    body: str | None = None,
) -> None:
    """Write a state.md for testing."""
    st = ProjectState(
        project="test-project",
        status=status,
        confidence="0/10",
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    if body is None:
        body = (
            "## Summary\n\n"
            "Test project summary\n\n"
            "## Current Focus\n\n"
            "Product design complete"
            " — run /mantle:design-system next.\n\n"
            "## Blockers\n\n"
            "_Anything preventing progress?_\n"
        )
    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, st, body)


# ── save_system_design ─────────────────────────────────────────


class TestSaveSystemDesign:
    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_correct_frontmatter(
        self, _m1: object, _m2: object, project: Path
    ) -> None:
        note = save_system_design(project, CONTENT)

        assert note.author == MOCK_EMAIL
        assert note.created == date.today()
        assert note.updated == date.today()
        assert note.updated_by == MOCK_EMAIL

    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_file_created(
        self, _m1: object, _m2: object, project: Path
    ) -> None:
        save_system_design(project, CONTENT)

        assert (project / ".mantle" / "system-design.md").exists()

    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_transitioned(
        self, _m1: object, _m2: object, project: Path
    ) -> None:
        save_system_design(project, CONTENT)
        st = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert st.frontmatter.status == Status.SYSTEM_DESIGN

    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_state_body_updated(
        self, _m1: object, _m2: object, project: Path
    ) -> None:
        save_system_design(project, CONTENT)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "System design complete" in text
        assert "/mantle:plan-issues" in text

    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_git_identity_stamped(
        self, _m1: object, _m2: object, project: Path
    ) -> None:
        note = save_system_design(project, CONTENT)

        assert note.author == MOCK_EMAIL
        assert note.updated_by == MOCK_EMAIL

    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_default_tags(
        self, _m1: object, _m2: object, project: Path
    ) -> None:
        note = save_system_design(project, CONTENT)

        assert note.tags == (
            "type/system-design",
            "phase/system-design",
        )

    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_raises_on_duplicate_without_overwrite(
        self, _m1: object, _m2: object, project: Path
    ) -> None:
        save_system_design(project, CONTENT)

        # Reset state to allow second transition
        _write_state(project, status=Status.PRODUCT_DESIGN)

        with pytest.raises(SystemDesignExistsError):
            save_system_design(project, "New content")

    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_overwrite_works(
        self, _m1: object, _m2: object, project: Path
    ) -> None:
        save_system_design(project, CONTENT)

        # Reset state to allow second transition
        _write_state(project, status=Status.PRODUCT_DESIGN)

        note = save_system_design(project, "Updated content", overwrite=True)
        _, body = load_system_design(project)

        assert note.author == MOCK_EMAIL
        assert "Updated content" in body

    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_invalid_transition_propagates(
        self, _m1: object, _m2: object, tmp_path: Path
    ) -> None:
        (tmp_path / ".mantle").mkdir()
        _write_state(tmp_path, status=Status.IDEA)

        with pytest.raises(InvalidTransitionError):
            save_system_design(tmp_path, CONTENT)

        # Document should NOT be saved
        assert not (tmp_path / ".mantle" / "system-design.md").exists()


# ── load_system_design ─────────────────────────────────────────


class TestLoadSystemDesign:
    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reads_saved(self, _m1: object, _m2: object, project: Path) -> None:
        save_system_design(project, CONTENT)
        note, body = load_system_design(project)

        assert note.author == MOCK_EMAIL
        assert "Architecture" in body

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_system_design(tmp_path)


# ── system_design_exists ───────────────────────────────────────


class TestSystemDesignExists:
    def test_false_before(self, project: Path) -> None:
        assert system_design_exists(project) is False

    @patch(
        "mantle.core.system_design.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_true_after(self, _m1: object, _m2: object, project: Path) -> None:
        save_system_design(project, CONTENT)

        assert system_design_exists(project) is True
