"""Tests for mantle.core.state."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pydantic
import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core.state import (
    InvalidTransitionError,
    ProjectState,
    Status,
    create_initial_state,
    load_state,
    resolve_git_identity,
    transition,
    update_slices,
    update_tracking,
    valid_transitions,
)
from mantle.core.vault import write_note

MOCK_EMAIL = "test@example.com"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ directory."""
    (tmp_path / ".mantle").mkdir()
    return tmp_path


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _write_state(
    project_dir: Path,
    *,
    status: Status = Status.IDEA,
    body: str = "## Summary\n\nTest body.\n",
    **overrides: object,
) -> None:
    """Write a state.md for testing."""
    defaults = {
        "project": "test-project",
        "status": status,
        "confidence": "0/10",
        "created": date(2025, 1, 1),
        "created_by": MOCK_EMAIL,
        "updated": date(2025, 1, 1),
        "updated_by": MOCK_EMAIL,
    }
    defaults.update(overrides)
    state = ProjectState(**defaults)
    path = project_dir / ".mantle" / "state.md"
    write_note(path, state, body)


# ── create_initial_state ─────────────────────────────────────────


class TestCreateInitialState:
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_creates_state_with_idea_status(
        self, _mock: object, project: Path
    ) -> None:
        state = create_initial_state(project, "my-project")

        assert state.status == Status.IDEA
        assert state.project == "my-project"
        assert state.created == date.today()
        assert state.created_by == MOCK_EMAIL

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip_with_load(self, _mock: object, project: Path) -> None:
        create_initial_state(project, "my-project")
        loaded = load_state(project)

        assert loaded.project == "my-project"
        assert loaded.status == Status.IDEA

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_body_has_expected_sections(
        self, _mock: object, project: Path
    ) -> None:
        create_initial_state(project, "my-project")
        path = project / ".mantle" / "state.md"
        text = path.read_text()

        assert "## Summary" in text
        assert "## Current Focus" in text
        assert "## Blockers" in text
        assert "## Recent Decisions" in text
        assert "## Next Steps" in text


# ── load_state ───────────────────────────────────────────────────


class TestLoadState:
    def test_reads_state(self, project: Path) -> None:
        _write_state(project, status=Status.PLANNING)
        state = load_state(project)

        assert state.status == Status.PLANNING
        assert state.project == "test-project"

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_state(tmp_path)


# ── transition ───────────────────────────────────────────────────


class TestTransition:
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_idea_to_challenge(self, _mock: object, project: Path) -> None:
        _write_state(project, status=Status.IDEA)
        result = transition(project, Status.CHALLENGE)

        assert result.status == Status.CHALLENGE

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_idea_to_product_design(self, _mock: object, project: Path) -> None:
        _write_state(project, status=Status.IDEA)
        result = transition(project, Status.PRODUCT_DESIGN)

        assert result.status == Status.PRODUCT_DESIGN

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_idea_to_research(self, _mock: object, project: Path) -> None:
        _write_state(project, status=Status.IDEA)
        result = transition(project, Status.RESEARCH)

        assert result.status == Status.RESEARCH

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_challenge_to_research(self, _mock: object, project: Path) -> None:
        _write_state(project, status=Status.CHALLENGE)
        result = transition(project, Status.RESEARCH)

        assert result.status == Status.RESEARCH

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_research_to_product_design(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(project, status=Status.RESEARCH)
        result = transition(project, Status.PRODUCT_DESIGN)

        assert result.status == Status.PRODUCT_DESIGN

    def test_research_to_implementing_invalid(self, project: Path) -> None:
        _write_state(project, status=Status.RESEARCH)

        with pytest.raises(InvalidTransitionError):
            transition(project, Status.IMPLEMENTING)

    def test_idea_to_implementing_invalid(self, project: Path) -> None:
        _write_state(project, status=Status.IDEA)

        with pytest.raises(InvalidTransitionError):
            transition(project, Status.IMPLEMENTING)

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_implementing_to_planning_backward(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(project, status=Status.IMPLEMENTING)
        result = transition(project, Status.PLANNING)

        assert result.status == Status.PLANNING

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_verifying_to_implementing_backward(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(project, status=Status.VERIFYING)
        result = transition(project, Status.IMPLEMENTING)

        assert result.status == Status.IMPLEMENTING

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_reviewing_to_implementing_backward(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(project, status=Status.REVIEWING)
        result = transition(project, Status.IMPLEMENTING)

        assert result.status == Status.IMPLEMENTING

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_idea_to_adopted(self, _mock: object, project: Path) -> None:
        _write_state(project, status=Status.IDEA)
        result = transition(project, Status.ADOPTED)

        assert result.status == Status.ADOPTED

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_adopted_to_planning(self, _mock: object, project: Path) -> None:
        _write_state(project, status=Status.ADOPTED)
        result = transition(project, Status.PLANNING)

        assert result.status == Status.PLANNING

    def test_adopted_to_implementing_invalid(self, project: Path) -> None:
        _write_state(project, status=Status.ADOPTED)

        with pytest.raises(InvalidTransitionError):
            transition(project, Status.IMPLEMENTING)

    def test_challenge_to_adopted_invalid(self, project: Path) -> None:
        _write_state(project, status=Status.CHALLENGE)

        with pytest.raises(InvalidTransitionError):
            transition(project, Status.ADOPTED)

    def test_product_design_to_adopted_invalid(self, project: Path) -> None:
        _write_state(project, status=Status.PRODUCT_DESIGN)

        with pytest.raises(InvalidTransitionError):
            transition(project, Status.ADOPTED)

    def test_adopted_to_completed_invalid(self, project: Path) -> None:
        _write_state(project, status=Status.ADOPTED)

        with pytest.raises(InvalidTransitionError):
            transition(project, Status.COMPLETED)

    def test_completed_is_terminal(self, project: Path) -> None:
        _write_state(project, status=Status.COMPLETED)

        with pytest.raises(InvalidTransitionError):
            transition(project, Status.IDEA)

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_updates_timestamp_and_identity(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(
            project,
            status=Status.IDEA,
            updated=date(2020, 1, 1),
            updated_by="old@example.com",
        )
        result = transition(project, Status.CHALLENGE)

        assert result.updated == date.today()
        assert result.updated_by == MOCK_EMAIL

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_preserves_body(self, _mock: object, project: Path) -> None:
        body = "## Summary\n\nCustom body content.\n"
        _write_state(project, status=Status.IDEA, body=body)

        transition(project, Status.CHALLENGE)

        from mantle.core.vault import read_note

        path = project / ".mantle" / "state.md"
        note = read_note(path, ProjectState)
        assert note.body == body


# ── update_tracking ──────────────────────────────────────────────


class TestUpdateTracking:
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_sets_tracking_fields(self, _mock: object, project: Path) -> None:
        _write_state(project)
        result = update_tracking(project, current_issue=2, current_story=3)

        assert result.current_issue == 2
        assert result.current_story == 3

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_preserves_status(self, _mock: object, project: Path) -> None:
        _write_state(project, status=Status.PLANNING)
        result = update_tracking(project, current_issue=1)

        assert result.status == Status.PLANNING


# ── valid_transitions ────────────────────────────────────────────


class TestValidTransitions:
    def test_idea_targets(self) -> None:
        result = valid_transitions(Status.IDEA)
        assert result == frozenset(
            {
                Status.CHALLENGE,
                Status.RESEARCH,
                Status.PRODUCT_DESIGN,
                Status.ADOPTED,
            }
        )

    def test_completed_is_empty(self) -> None:
        result = valid_transitions(Status.COMPLETED)
        assert result == frozenset()

    def test_all_statuses_have_entries(self) -> None:
        for status in Status:
            result = valid_transitions(status)
            assert isinstance(result, frozenset)


# ── resolve_git_identity ─────────────────────────────────────────


class TestResolveGitIdentity:
    @patch("subprocess.run")
    def test_returns_email(self, mock_run: object) -> None:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "user@example.com\n"

        assert resolve_git_identity() == "user@example.com"

    @patch("subprocess.run")
    def test_raises_on_failure(self, mock_run: object) -> None:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""

        with pytest.raises(RuntimeError):
            resolve_git_identity()


# ── InvalidTransitionError ────────────────────────────────────────────


class TestInvalidTransitionError:
    def test_stores_attributes(self) -> None:
        targets = frozenset({Status.CHALLENGE, Status.PRODUCT_DESIGN})
        exc = InvalidTransitionError(Status.IDEA, Status.IMPLEMENTING, targets)

        assert exc.current == Status.IDEA
        assert exc.target == Status.IMPLEMENTING
        assert exc.valid_targets == targets

    def test_str_readable(self) -> None:
        targets = frozenset({Status.CHALLENGE})
        exc = InvalidTransitionError(Status.IDEA, Status.IMPLEMENTING, targets)
        msg = str(exc)

        assert "idea" in msg
        assert "implementing" in msg
        assert "challenge" in msg

    def test_terminal_state_message(self) -> None:
        exc = InvalidTransitionError(Status.COMPLETED, Status.IDEA, frozenset())
        msg = str(exc)

        assert "terminal state" in msg


# ── ProjectState model ───────────────────────────────────────────


class TestProjectState:
    def test_frozen(self) -> None:
        state = ProjectState(
            project="test",
            status=Status.IDEA,
            created=date.today(),
            created_by="a@b.com",
            updated=date.today(),
            updated_by="a@b.com",
        )

        with pytest.raises(pydantic.ValidationError):
            state.status = Status.CHALLENGE  # type: ignore[misc]

    def test_schema_version_defaults_to_one(self) -> None:
        state = ProjectState(
            project="test",
            status=Status.IDEA,
            created=date.today(),
            created_by="a@b.com",
            updated=date.today(),
            updated_by="a@b.com",
        )

        assert state.schema_version == 1

    def test_schema_version_round_trips(self, project: Path) -> None:
        _write_state(project)
        loaded = load_state(project)

        assert loaded.schema_version == 1

    def test_loads_without_schema_version_field(self, project: Path) -> None:
        """Old state.md files without schema_version still parse."""
        path = project / ".mantle" / "state.md"
        path.write_text(
            "---\n"
            "project: legacy\n"
            "status: idea\n"
            "confidence: '0/10'\n"
            "created: 2025-01-01\n"
            "created_by: a@b.com\n"
            "updated: 2025-01-01\n"
            "updated_by: a@b.com\n"
            "---\n\n"
            "## Summary\n\nLegacy project.\n",
            encoding="utf-8",
        )
        loaded = load_state(project)

        assert loaded.schema_version == 1
        assert loaded.project == "legacy"

    def test_slices_defaults_to_empty_tuple(self) -> None:
        state = ProjectState(
            project="test",
            status=Status.IDEA,
            created=date.today(),
            created_by="a@b.com",
            updated=date.today(),
            updated_by="a@b.com",
        )

        assert state.slices == ()

    def test_slices_accepts_tuple_of_strings(self) -> None:
        state = ProjectState(
            project="test",
            status=Status.IDEA,
            created=date.today(),
            created_by="a@b.com",
            updated=date.today(),
            updated_by="a@b.com",
            slices=("core", "cli", "tests"),
        )

        assert state.slices == ("core", "cli", "tests")


# ── update_slices ───────────────────────────────────────────────


class TestUpdateSlices:
    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_sets_slices(self, _mock: object, project: Path) -> None:
        _write_state(project)
        result = update_slices(project, ("core", "cli", "tests"))

        assert result.slices == ("core", "cli", "tests")

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_round_trip_preserves_slices(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(project)
        update_slices(project, ("ingestion", "api", "storage"))
        loaded = load_state(project)

        assert loaded.slices == ("ingestion", "api", "storage")

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_updates_timestamp_and_identity(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(
            project,
            updated=date(2020, 1, 1),
            updated_by="old@example.com",
        )
        result = update_slices(project, ("core",))

        assert result.updated == date.today()
        assert result.updated_by == MOCK_EMAIL

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_preserves_existing_fields(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(project, status=Status.PLANNING)
        result = update_slices(project, ("core",))

        assert result.status == Status.PLANNING
        assert result.project == "test-project"

    @patch(
        "mantle.core.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_overwrites_previous_slices(
        self, _mock: object, project: Path
    ) -> None:
        _write_state(project)
        update_slices(project, ("core", "cli"))
        result = update_slices(project, ("api", "storage"))

        assert result.slices == ("api", "storage")


# ── Status enum ──────────────────────────────────────────────────


class TestStatusEnum:
    def test_has_eleven_values(self) -> None:
        assert len(Status) == 11

    def test_values(self) -> None:
        values = {s.value for s in Status}
        expected = {
            "idea",
            "challenge",
            "research",
            "product-design",
            "system-design",
            "adopted",
            "planning",
            "implementing",
            "verifying",
            "reviewing",
            "completed",
        }
        assert values == expected
