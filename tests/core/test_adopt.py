"""Tests for mantle.core.adopt."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest

from mantle.core import product_design, system_design, vault
from mantle.core.adopt import (
    AdoptionExistsError,
    adoption_exists,
    save_adoption,
)
from mantle.core.state import (
    InvalidTransitionError,
    ProjectState,
    Status,
)

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"

_DEFAULTS: dict[str, object] = {
    "vision": "Persistent AI context that eliminates ramp-up",
    "principles": [
        "Context must persist across sessions",
        "Every stage decomposes into building blocks",
    ],
    "building_blocks": [
        "Structured idea capture",
        "Challenge sessions",
    ],
    "prior_art": [
        "Obsidian vault for persistent notes",
        "Claude Code slash commands",
    ],
    "composition": (
        "Slash commands drive a staged workflow whose"
        " outputs accumulate in an Obsidian vault"
    ),
    "target_users": "Solo developers using Claude Code",
    "success_metrics": [
        "Ship MVP in 2 weeks",
        "5 active users in first month",
    ],
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


# ── save_adoption ────────────────────────────────────────────────


class TestSaveAdoption:
    def test_writes_product_design_frontmatter(self, project: Path) -> None:
        pd_note, _ = save_adoption(project, **_DEFAULTS)

        assert pd_note.vision == (
            "Persistent AI context that eliminates ramp-up"
        )
        assert pd_note.principles == (
            "Context must persist across sessions",
            "Every stage decomposes into building blocks",
        )
        assert pd_note.building_blocks == (
            "Structured idea capture",
            "Challenge sessions",
        )

    def test_writes_system_design_frontmatter(self, project: Path) -> None:
        _, sd_note = save_adoption(project, **_DEFAULTS)

        assert sd_note.author == MOCK_EMAIL
        assert sd_note.created == date.today()

    def test_product_design_round_trips(self, project: Path) -> None:
        save_adoption(project, **_DEFAULTS)
        loaded = product_design.load_product_design(project)

        assert loaded.vision == (
            "Persistent AI context that eliminates ramp-up"
        )
        assert loaded.principles == (
            "Context must persist across sessions",
            "Every stage decomposes into building blocks",
        )

    def test_system_design_round_trips(self, project: Path) -> None:
        save_adoption(project, **_DEFAULTS)
        loaded_note, loaded_body = system_design.load_system_design(project)

        assert loaded_note.author == MOCK_EMAIL
        assert "## Architecture" in loaded_body

    def test_transitions_state_to_adopted(self, project: Path) -> None:
        save_adoption(project, **_DEFAULTS)
        note = vault.read_note(
            project / ".mantle" / "state.md",
            ProjectState,
        )

        assert note.frontmatter.status == Status.ADOPTED

    def test_state_body_contains_adoption_complete(self, project: Path) -> None:
        save_adoption(project, **_DEFAULTS)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "Adoption complete" in text

    def test_state_body_contains_next_step(self, project: Path) -> None:
        save_adoption(project, **_DEFAULTS)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "/mantle:plan-issues" in text

    def test_state_timestamps_refreshed(self, project: Path) -> None:
        save_adoption(project, **_DEFAULTS)
        note = vault.read_note(
            project / ".mantle" / "state.md",
            ProjectState,
        )

        assert note.frontmatter.updated == date.today()
        assert note.frontmatter.updated_by == MOCK_EMAIL

    def test_stamps_author_with_git_identity(self, project: Path) -> None:
        pd_note, sd_note = save_adoption(project, **_DEFAULTS)

        assert pd_note.author == MOCK_EMAIL
        assert pd_note.updated_by == MOCK_EMAIL
        assert sd_note.author == MOCK_EMAIL
        assert sd_note.updated_by == MOCK_EMAIL

    def test_raises_adoption_exists_on_product_design(
        self, project: Path
    ) -> None:
        (project / ".mantle" / "product-design.md").write_text("existing")

        with pytest.raises(AdoptionExistsError):
            save_adoption(project, **_DEFAULTS)

    def test_raises_adoption_exists_on_system_design(
        self, project: Path
    ) -> None:
        (project / ".mantle" / "system-design.md").write_text("existing")

        with pytest.raises(AdoptionExistsError):
            save_adoption(project, **_DEFAULTS)

    def test_overwrite_succeeds_when_docs_exist(self, project: Path) -> None:
        (project / ".mantle" / "product-design.md").write_text("existing")
        (project / ".mantle" / "system-design.md").write_text("existing")

        pd_note, sd_note = save_adoption(project, **_DEFAULTS, overwrite=True)

        assert pd_note.vision == (
            "Persistent AI context that eliminates ramp-up"
        )
        assert sd_note.author == MOCK_EMAIL

    def test_raises_invalid_transition_when_not_idea(
        self, tmp_path: Path
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

        with pytest.raises(InvalidTransitionError):
            save_adoption(tmp_path, **_DEFAULTS)


# ── adoption_exists ──────────────────────────────────────────────


class TestAdoptionExists:
    def test_false_when_no_design_docs(self, project: Path) -> None:
        assert adoption_exists(project) is False

    def test_true_when_product_design_exists(self, project: Path) -> None:
        (project / ".mantle" / "product-design.md").write_text("existing")

        assert adoption_exists(project) is True

    def test_true_when_system_design_exists(self, project: Path) -> None:
        (project / ".mantle" / "system-design.md").write_text("existing")

        assert adoption_exists(project) is True
