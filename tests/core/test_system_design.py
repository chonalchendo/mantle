"""Tests for mantle.core.system_design."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import decisions, vault
from mantle.core.state import (
    InvalidTransitionError,
    ProjectState,
    Status,
)
from mantle.core.system_design import (
    SystemDesignExistsError,
    SystemDesignNote,
    load_system_design,
    save_system_design,
    system_design_exists,
    update_system_design,
)

MOCK_EMAIL = "test@example.com"
CONTENT = (
    "## Architecture\n\n"
    "Layered architecture with core, CLI, and API layers.\n\n"
    "## Technology Choices\n\n"
    "Python 3.14, Pydantic, cyclopts\n"
)


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
    _write_state(tmp_path, status=Status.PRODUCT_DESIGN)
    return tmp_path


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
    def test_correct_frontmatter(self, project: Path) -> None:
        note = save_system_design(project, CONTENT)

        assert note.author == MOCK_EMAIL
        assert note.created == date.today()
        assert note.updated == date.today()
        assert note.updated_by == MOCK_EMAIL

    def test_file_created(self, project: Path) -> None:
        save_system_design(project, CONTENT)

        assert (project / ".mantle" / "system-design.md").exists()

    def test_state_transitioned(self, project: Path) -> None:
        save_system_design(project, CONTENT)
        st = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert st.frontmatter.status == Status.SYSTEM_DESIGN

    def test_state_body_updated(self, project: Path) -> None:
        save_system_design(project, CONTENT)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "System design complete" in text
        assert "/mantle:plan-issues" in text

    def test_git_identity_stamped(self, project: Path) -> None:
        note = save_system_design(project, CONTENT)

        assert note.author == MOCK_EMAIL
        assert note.updated_by == MOCK_EMAIL

    def test_default_tags(self, project: Path) -> None:
        note = save_system_design(project, CONTENT)

        assert note.tags == (
            "type/system-design",
            "phase/system-design",
        )

    def test_raises_on_duplicate_without_overwrite(
        self, project: Path
    ) -> None:
        save_system_design(project, CONTENT)

        # Reset state to allow second transition
        _write_state(project, status=Status.PRODUCT_DESIGN)

        with pytest.raises(SystemDesignExistsError):
            save_system_design(project, "New content")

    def test_overwrite_works(self, project: Path) -> None:
        save_system_design(project, CONTENT)

        # Reset state to allow second transition
        _write_state(project, status=Status.PRODUCT_DESIGN)

        note = save_system_design(project, "Updated content", overwrite=True)
        _, body = load_system_design(project)

        assert note.author == MOCK_EMAIL
        assert "Updated content" in body

    def test_invalid_transition_propagates(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".mantle").mkdir()
        _write_state(tmp_path, status=Status.IDEA)

        with pytest.raises(InvalidTransitionError):
            save_system_design(tmp_path, CONTENT)

        # Document should NOT be saved
        assert not (tmp_path / ".mantle" / "system-design.md").exists()


# ── load_system_design ─────────────────────────────────────────


class TestLoadSystemDesign:
    def test_reads_saved(self, project: Path) -> None:
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

    def test_true_after(self, project: Path) -> None:
        save_system_design(project, CONTENT)

        assert system_design_exists(project) is True


# ── update_system_design ─────────────────────────────────────────

ORIGINAL_AUTHOR = "original@example.com"
REVISED_CONTENT = (
    "## Architecture\n\n"
    "Revised layered architecture with improved caching.\n\n"
    "## Technology Choices\n\n"
    "Python 3.14, Pydantic v2, cyclopts, Redis\n"
)


@pytest.fixture
def project_with_design(tmp_path: Path) -> Path:
    """Create .mantle/ at SYSTEM_DESIGN with existing system design."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "decisions").mkdir()
    _write_state(tmp_path, status=Status.SYSTEM_DESIGN)

    note = SystemDesignNote(
        author=ORIGINAL_AUTHOR,
        created=date(2025, 6, 1),
        updated=date(2025, 6, 1),
        updated_by=ORIGINAL_AUTHOR,
    )
    vault.write_note(mantle / "system-design.md", note, CONTENT)
    return tmp_path


def _update_design(
    project_dir: Path,
    **overrides: object,
) -> tuple[SystemDesignNote, Path]:
    """Update a system design with sensible defaults."""
    defaults: dict[str, object] = {
        "content": REVISED_CONTENT,
        "change_topic": "add-caching-layer",
        "change_summary": "Added Redis caching to the architecture",
        "change_rationale": "Reduce latency for repeated queries",
    }
    defaults.update(overrides)
    content = defaults.pop("content")
    return update_system_design(
        project_dir, content, **defaults  # type: ignore[arg-type]
    )


class TestUpdateSystemDesign:
    def test_revised_content(
        self, project_with_design: Path
    ) -> None:
        _update_design(project_with_design)
        _, body = load_system_design(project_with_design)

        assert "Revised layered architecture" in body
        assert "Redis" in body

    def test_preserves_original_author_and_created(
        self, project_with_design: Path
    ) -> None:
        note, _ = _update_design(project_with_design)

        assert note.author == ORIGINAL_AUTHOR
        assert note.created == date(2025, 6, 1)

    def test_stamps_updated_with_git_identity(
        self, project_with_design: Path
    ) -> None:
        note, _ = _update_design(project_with_design)

        assert note.updated == date.today()
        assert note.updated_by == MOCK_EMAIL

    def test_round_trip(
        self, project_with_design: Path
    ) -> None:
        _update_design(project_with_design)
        note, body = load_system_design(project_with_design)

        assert note.author == ORIGINAL_AUTHOR
        assert "Revised layered architecture" in body

    def test_creates_decision_log_entry(
        self, project_with_design: Path
    ) -> None:
        _, decision_path = _update_design(project_with_design)

        assert decision_path.exists()
        assert decision_path.parent.name == "decisions"

    def test_decision_entry_topic_and_scope(
        self, project_with_design: Path
    ) -> None:
        _, decision_path = _update_design(project_with_design)
        entry, _ = decisions.load_decision(decision_path)

        assert entry.topic == "add-caching-layer"
        assert entry.scope == "system-design"

    def test_decision_entry_body(
        self, project_with_design: Path
    ) -> None:
        _, decision_path = _update_design(project_with_design)
        _, body = decisions.load_decision(decision_path)

        assert "Added Redis caching" in body
        assert "Reduce latency" in body

    def test_raises_when_missing(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            _update_design(tmp_path)

    def test_does_not_change_state_status(
        self, project_with_design: Path
    ) -> None:
        _update_design(project_with_design)
        note = vault.read_note(
            project_with_design / ".mantle" / "state.md",
            ProjectState,
        )

        assert note.frontmatter.status == Status.SYSTEM_DESIGN

    def test_second_revision_creates_second_decision(
        self, project_with_design: Path
    ) -> None:
        _update_design(project_with_design)
        _update_design(
            project_with_design,
            content="## Third revision\n\nMore changes.\n",
            change_topic="add-caching-layer",
            change_summary="Another revision",
            change_rationale="Further refinement",
        )

        paths = decisions.list_decisions(project_with_design)
        assert len(paths) == 2
