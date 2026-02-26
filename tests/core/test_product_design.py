"""Tests for mantle.core.product_design."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core import decisions, vault
from mantle.core.product_design import (
    ProductDesignExistsError,
    ProductDesignNote,
    create_product_design,
    load_product_design,
    product_design_exists,
    update_product_design,
)
from mantle.core.state import ProjectState, Status

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
    """Create a minimal .mantle/ with state.md at CHALLENGE status."""
    (tmp_path / ".mantle").mkdir()
    _write_state(tmp_path, status=Status.CHALLENGE)
    return tmp_path


@pytest.fixture
def project_from_idea(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with state.md at IDEA status."""
    (tmp_path / ".mantle").mkdir()
    _write_state(tmp_path, status=Status.IDEA)
    return tmp_path


def _write_state(
    project_dir: Path,
    *,
    status: Status = Status.CHALLENGE,
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
    path = project_dir / ".mantle" / "state.md"
    vault.write_note(path, st, body)


def _create_design(project_dir: Path, **overrides: object) -> ProductDesignNote:
    """Create a product design with sensible defaults."""
    defaults: dict[str, object] = {
        "vision": "Persistent AI context that eliminates ramp-up",
        "principles": [
            "Context must persist across sessions",
            "Every stage decomposes into building blocks",
        ],
        "building_blocks": [
            "Structured idea capture",
            "Challenge sessions",
            "Product design workflow",
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
    }
    defaults.update(overrides)
    return create_product_design(project_dir, **defaults)


# -- create_product_design ----------------------------------------


class TestCreateProductDesign:
    def test_correct_frontmatter(self, project: Path) -> None:
        result = _create_design(project)

        assert result.vision == (
            "Persistent AI context that eliminates ramp-up"
        )
        assert result.principles == (
            "Context must persist across sessions",
            "Every stage decomposes into building blocks",
        )
        assert result.building_blocks == (
            "Structured idea capture",
            "Challenge sessions",
            "Product design workflow",
        )
        assert result.prior_art == (
            "Obsidian vault for persistent notes",
            "Claude Code slash commands",
        )
        assert result.composition == (
            "Slash commands drive a staged workflow whose"
            " outputs accumulate in an Obsidian vault"
        )
        assert result.target_users == ("Solo developers using Claude Code")
        assert result.success_metrics == (
            "Ship MVP in 2 weeks",
            "5 active users in first month",
        )

    def test_file_created(self, project: Path) -> None:
        _create_design(project)

        assert (project / ".mantle" / "product-design.md").exists()

    def test_round_trip(self, project: Path) -> None:
        created = _create_design(project)
        loaded = load_product_design(project)

        assert loaded.vision == created.vision
        assert loaded.principles == created.principles
        assert loaded.building_blocks == created.building_blocks
        assert loaded.prior_art == created.prior_art
        assert loaded.composition == created.composition
        assert loaded.target_users == created.target_users
        assert loaded.success_metrics == created.success_metrics

    def test_body_has_populated_sections(self, project: Path) -> None:
        _create_design(project)
        path = project / ".mantle" / "product-design.md"
        text = path.read_text()

        assert "## Vision" in text
        assert "Persistent AI context" in text
        assert "## Principles" in text
        assert "- Context must persist across sessions" in text
        assert "- Every stage decomposes into building blocks" in text
        assert "## Building Blocks" in text
        assert "- Structured idea capture" in text
        assert "- Challenge sessions" in text
        assert "- Product design workflow" in text
        assert "## Prior Art" in text
        assert "- Obsidian vault for persistent notes" in text
        assert "- Claude Code slash commands" in text
        assert "## Composition" in text
        assert "outputs accumulate in an Obsidian vault" in text
        assert "## Target Users" in text
        assert "Solo developers using Claude Code" in text
        assert "## Success Metrics" in text
        assert "- Ship MVP in 2 weeks" in text
        assert "- 5 active users in first month" in text
        assert "## Open Questions" in text

    def test_raises_on_existing(self, project: Path) -> None:
        _create_design(project)

        with pytest.raises(ProductDesignExistsError):
            _create_design(project)

    def test_overwrite_works(self, project: Path) -> None:
        _create_design(project)
        result = _create_design(
            project,
            vision="New vision",
            overwrite=True,
        )

        assert result.vision == "New vision"

    def test_git_identity_stamp(self, project: Path) -> None:
        result = _create_design(project)

        assert result.author == MOCK_EMAIL
        assert result.updated_by == MOCK_EMAIL

    def test_default_tags(self, project: Path) -> None:
        result = _create_design(project)

        assert result.tags == (
            "type/product-design",
            "phase/design",
        )

    def test_state_transitions_to_product_design(
        self, project: Path
    ) -> None:
        _create_design(project)
        note = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.status == Status.PRODUCT_DESIGN

    def test_state_current_focus_updated(
        self, project: Path
    ) -> None:
        _create_design(project)
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "Product design complete" in text
        assert "/mantle:design-system" in text

    def test_state_timestamps_refreshed(
        self, project: Path
    ) -> None:
        _create_design(project)
        note = vault.read_note(project / ".mantle" / "state.md", ProjectState)

        assert note.frontmatter.updated == date.today()
        assert note.frontmatter.updated_by == MOCK_EMAIL

    def test_works_from_idea_status(
        self, project_from_idea: Path
    ) -> None:
        result = _create_design(project_from_idea)

        assert result.vision == (
            "Persistent AI context that eliminates ramp-up"
        )
        note = vault.read_note(
            project_from_idea / ".mantle" / "state.md",
            ProjectState,
        )
        assert note.frontmatter.status == Status.PRODUCT_DESIGN


# -- load_product_design ------------------------------------------


class TestLoadProductDesign:
    def test_reads_saved(self, project: Path) -> None:
        _create_design(project)
        loaded = load_product_design(project)

        assert loaded.vision == (
            "Persistent AI context that eliminates ramp-up"
        )

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_product_design(tmp_path)


# -- product_design_exists ----------------------------------------


class TestProductDesignExists:
    def test_false_before(self, project: Path) -> None:
        assert product_design_exists(project) is False

    def test_true_after(self, project: Path) -> None:
        _create_design(project)

        assert product_design_exists(project) is True


# -- ProductDesignNote model --------------------------------------


class TestProductDesignNote:
    def test_frozen(self) -> None:
        note = ProductDesignNote(
            vision="Test vision",
            principles=("p",),
            building_blocks=("b",),
            prior_art=("a",),
            composition="compose",
            target_users="Devs",
            success_metrics=("metric",),
            author="a@b.com",
            created=date.today(),
            updated=date.today(),
            updated_by="a@b.com",
        )

        with pytest.raises(pydantic.ValidationError):
            note.vision = "Changed"  # type: ignore[misc]


# -- update_product_design ----------------------------------------

ORIGINAL_AUTHOR = "original@example.com"


@pytest.fixture
def project_with_design(tmp_path: Path) -> Path:
    """Create .mantle/ at SYSTEM_DESIGN with existing product design."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "decisions").mkdir()
    _write_state(tmp_path, status=Status.SYSTEM_DESIGN)

    note = ProductDesignNote(
        vision="Original vision",
        principles=("Original principle",),
        building_blocks=("Original block",),
        prior_art=("Original art",),
        composition="Original composition",
        target_users="Original users",
        success_metrics=("Original metric",),
        author=ORIGINAL_AUTHOR,
        created=date(2025, 6, 1),
        updated=date(2025, 6, 1),
        updated_by=ORIGINAL_AUTHOR,
    )
    from mantle.core.product_design import _build_product_design_body

    vault.write_note(
        mantle / "product-design.md",
        note,
        _build_product_design_body(note),
    )
    return tmp_path


def _update_design(
    project_dir: Path,
    **overrides: object,
) -> tuple[ProductDesignNote, Path]:
    """Update a product design with sensible defaults."""
    defaults: dict[str, object] = {
        "vision": "Revised vision",
        "principles": ["Revised principle"],
        "building_blocks": ["Revised block"],
        "prior_art": ["Revised art"],
        "composition": "Revised composition",
        "target_users": "Revised users",
        "success_metrics": ["Revised metric"],
        "change_topic": "revise-product-vision",
        "change_summary": "Reframed the product vision",
        "change_rationale": "Better alignment with user needs",
    }
    defaults.update(overrides)
    return update_product_design(project_dir, **defaults)


class TestUpdateProductDesign:
    def test_revised_vision(
        self, project_with_design: Path
    ) -> None:
        note, _ = _update_design(project_with_design)

        assert note.vision == "Revised vision"

    def test_revised_principles(
        self, project_with_design: Path
    ) -> None:
        note, _ = _update_design(project_with_design)

        assert note.principles == ("Revised principle",)

    def test_revised_building_blocks(
        self, project_with_design: Path
    ) -> None:
        note, _ = _update_design(project_with_design)

        assert note.building_blocks == ("Revised block",)

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
        loaded = load_product_design(project_with_design)

        assert loaded.vision == "Revised vision"
        assert loaded.principles == ("Revised principle",)
        assert loaded.building_blocks == ("Revised block",)
        assert loaded.prior_art == ("Revised art",)
        assert loaded.composition == "Revised composition"
        assert loaded.target_users == "Revised users"
        assert loaded.success_metrics == ("Revised metric",)

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

        assert entry.topic == "revise-product-vision"
        assert entry.scope == "product-design"

    def test_decision_entry_body(
        self, project_with_design: Path
    ) -> None:
        _, decision_path = _update_design(project_with_design)
        _, body = decisions.load_decision(decision_path)

        assert "Reframed the product vision" in body
        assert "Better alignment with user needs" in body

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
            vision="Third vision",
            change_topic="revise-product-vision",
            change_summary="Another revision",
            change_rationale="Further refinement",
        )

        paths = decisions.list_decisions(project_with_design)
        assert len(paths) == 2
