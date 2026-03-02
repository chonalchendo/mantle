"""Tests for mantle.core.skills."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pydantic
import pytest

from mantle.core import vault
from mantle.core.skills import (
    SkillExistsError,
    SkillNote,
    VaultNotConfiguredError,
    _match_skill_slug,
    create_skill,
    detect_gaps,
    list_skills,
    load_relevant_skills,
    load_skill,
    skill_exists,
    suggest_gap_message,
    update_skill,
)
from mantle.core.state import ProjectState, Status

MOCK_EMAIL = "test@example.com"

SAMPLE_CONTENT = """\
## Context

Async Python patterns using asyncio for concurrent I/O-bound services.

## Core Knowledge

Use `asyncio.TaskGroup` for structured concurrency instead of `gather()`.
Always use `async with` for resource management.
Prefer `asyncio.run()` as the single entry point.

## Examples

```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(fetch_url(url))
```

## Decision Criteria

Use asyncio for I/O-bound concurrency.
Use multiprocessing for CPU-bound work.
Use threading only for legacy blocking I/O code.

## Anti-patterns

- Use `TaskGroup` instead of `gather()` for structured concurrency.
- Use `asyncio.run()` instead of manual event loop management.
- Use `async with` instead of manual `close()` calls."""


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.skills.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ with config pointing to a vault."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()

    vault_path = tmp_path / "vault"
    (vault_path / "skills").mkdir(parents=True)

    config_body = "## Config\n"
    from mantle.core.project import _ConfigFrontmatter

    fm = _ConfigFrontmatter(personal_vault=str(vault_path))
    vault.write_note(mantle / "config.md", fm, config_body)

    return tmp_path


def _write_state(
    project_dir: Path,
    skills_required: tuple[str, ...] = (),
) -> None:
    """Write a state.md with given skills_required."""
    st = ProjectState(
        project="test-project",
        status=Status.IDEA,
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
        skills_required=skills_required,
    )
    vault.write_note(
        project_dir / ".mantle" / "state.md",
        st,
        "## Summary\n",
    )


@pytest.fixture
def project_with_state(project: Path) -> Path:
    """Project with state.md containing skills_required."""
    _write_state(
        project,
        skills_required=(
            "Python asyncio",
            "WebSocket protocol",
        ),
    )
    return project


@pytest.fixture
def project_no_vault(tmp_path: Path) -> Path:
    """Create a .mantle/ with no personal_vault configured."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()

    from mantle.core.project import _ConfigFrontmatter

    fm = _ConfigFrontmatter()
    vault.write_note(mantle / "config.md", fm, "## Config\n")

    return tmp_path


def _create_skill(
    project_dir: Path, **overrides: object
) -> tuple[SkillNote, Path]:
    """Create a skill with sensible defaults."""
    defaults: dict[str, object] = {
        "name": "Python asyncio",
        "description": (
            "Async Python patterns using asyncio. "
            "Use when building concurrent I/O-bound services."
        ),
        "proficiency": "7/10",
        "content": SAMPLE_CONTENT,
        "related_skills": (),
        "projects": (),
    }
    defaults.update(overrides)
    return create_skill(project_dir, **defaults)


# ── create_skill ─────────────────────────────────────────────────


class TestCreateSkill:
    """Tests for create_skill()."""

    def test_correct_frontmatter(self, project: Path) -> None:
        note, _ = _create_skill(project)

        assert note.name == "Python asyncio"
        assert note.description == (
            "Async Python patterns using asyncio. "
            "Use when building concurrent I/O-bound services."
        )
        assert note.type == "skill"
        assert note.proficiency == "7/10"
        assert note.related_skills == ()
        assert note.projects == ()
        assert note.last_used == date.today()
        assert note.author == MOCK_EMAIL
        assert note.created == date.today()
        assert note.updated == date.today()
        assert note.updated_by == MOCK_EMAIL
        assert note.tags == ("type/skill",)

    def test_file_created_at_vault_skills(self, project: Path) -> None:
        _, path = _create_skill(project)

        assert path.exists()
        assert path.name == "python-asyncio.md"
        assert path.parent.name == "skills"

    def test_round_trip_frontmatter(self, project: Path) -> None:
        created, path = _create_skill(project)
        loaded, _ = load_skill(path)

        assert loaded.name == created.name
        assert loaded.description == created.description
        assert loaded.type == created.type
        assert loaded.proficiency == created.proficiency
        assert loaded.related_skills == created.related_skills
        assert loaded.projects == created.projects
        assert loaded.author == created.author
        assert loaded.tags == created.tags

    def test_round_trip_preserves_content(self, project: Path) -> None:
        _, path = _create_skill(project)
        _, body = load_skill(path)

        assert "## Context" in body
        assert "asyncio.TaskGroup" in body
        assert "## Anti-patterns" in body

    def test_body_has_related_skills_wikilinks(self, project: Path) -> None:
        _, path = _create_skill(
            project,
            related_skills=("Python", "FastAPI"),
        )
        _, body = load_skill(path)

        assert "## Related Skills" in body
        assert "- [[Python]]" in body
        assert "- [[FastAPI]]" in body

    def test_body_has_projects_wikilinks(self, project: Path) -> None:
        _, path = _create_skill(
            project,
            projects=("mantle", "webapp"),
        )
        _, body = load_skill(path)

        assert "## Projects" in body
        assert "- [[mantle]]" in body
        assert "- [[webapp]]" in body

    def test_body_omits_related_skills_when_empty(self, project: Path) -> None:
        _, path = _create_skill(project, related_skills=())
        _, body = load_skill(path)

        assert "## Related Skills" not in body

    def test_body_omits_projects_when_empty(self, project: Path) -> None:
        _, path = _create_skill(project, projects=())
        _, body = load_skill(path)

        assert "## Projects" not in body

    def test_body_contains_authored_content_verbatim(
        self, project: Path
    ) -> None:
        _, path = _create_skill(project)
        _, body = load_skill(path)

        assert SAMPLE_CONTENT in body

    def test_raises_on_existing(self, project: Path) -> None:
        _create_skill(project)

        with pytest.raises(SkillExistsError):
            _create_skill(project)

    def test_overwrite_replaces_existing(self, project: Path) -> None:
        _create_skill(project)
        note, _ = _create_skill(
            project,
            proficiency="9/10",
            overwrite=True,
        )

        assert note.proficiency == "9/10"

    def test_stamps_git_identity(self, project: Path) -> None:
        note, _ = _create_skill(project)

        assert note.author == MOCK_EMAIL
        assert note.updated_by == MOCK_EMAIL

    def test_default_tags(self, project: Path) -> None:
        note, _ = _create_skill(project)

        assert note.tags == ("type/skill",)

    def test_raises_vault_not_configured(self, project_no_vault: Path) -> None:
        with pytest.raises(VaultNotConfiguredError):
            _create_skill(project_no_vault)

    def test_raises_on_invalid_proficiency(self, project: Path) -> None:
        with pytest.raises(ValueError, match="Invalid proficiency"):
            _create_skill(project, proficiency="high")

    def test_slugifies_spaces_to_hyphens(self, project: Path) -> None:
        _, path = _create_skill(project, name="Python asyncio")

        assert path.name == "python-asyncio.md"

    def test_slugifies_to_lowercase(self, project: Path) -> None:
        _, path = _create_skill(project, name="WebSocket Protocol")

        assert path.name == "websocket-protocol.md"


# ── load_skill ───────────────────────────────────────────────────


class TestLoadSkill:
    """Tests for load_skill()."""

    def test_reads_saved_frontmatter(self, project: Path) -> None:
        _, path = _create_skill(project)
        loaded, _ = load_skill(path)

        assert loaded.name == "Python asyncio"
        assert loaded.description == (
            "Async Python patterns using asyncio. "
            "Use when building concurrent I/O-bound services."
        )

    def test_reads_saved_body(self, project: Path) -> None:
        _, path = _create_skill(project)
        _, body = load_skill(path)

        assert "## Context" in body
        assert "asyncio" in body

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_skill(tmp_path / "nonexistent.md")


# ── list_skills ──────────────────────────────────────────────────


class TestListSkills:
    """Tests for list_skills()."""

    def test_empty_when_no_skills(self, project: Path) -> None:
        result = list_skills(project)

        assert result == []

    def test_returns_sorted_paths(self, project: Path) -> None:
        _create_skill(project, name="Zsh scripting")
        _create_skill(project, name="Docker compose")

        result = list_skills(project)

        assert len(result) == 2
        assert result[0].name == "docker-compose.md"
        assert result[1].name == "zsh-scripting.md"

    def test_raises_vault_not_configured(self, project_no_vault: Path) -> None:
        with pytest.raises(VaultNotConfiguredError):
            list_skills(project_no_vault)


# ── skill_exists ─────────────────────────────────────────────────


class TestSkillExists:
    """Tests for skill_exists()."""

    def test_false_before_creation(self, project: Path) -> None:
        assert skill_exists(project, "Python asyncio") is False

    def test_true_after_creation(self, project: Path) -> None:
        _create_skill(project)

        assert skill_exists(project, "Python asyncio") is True

    def test_raises_vault_not_configured(self, project_no_vault: Path) -> None:
        with pytest.raises(VaultNotConfiguredError):
            skill_exists(project_no_vault, "Python asyncio")


# ── update_skill ─────────────────────────────────────────────────


class TestUpdateSkill:
    """Tests for update_skill()."""

    def test_updates_description(self, project: Path) -> None:
        _create_skill(project)
        result = update_skill(
            project,
            "Python asyncio",
            description="Updated description.",
        )

        assert result.description == "Updated description."

    def test_updates_proficiency(self, project: Path) -> None:
        _create_skill(project)
        result = update_skill(
            project,
            "Python asyncio",
            proficiency="9/10",
        )

        assert result.proficiency == "9/10"

    def test_updates_content_in_body(self, project: Path) -> None:
        _, path = _create_skill(project)
        update_skill(
            project,
            "Python asyncio",
            content="## New Content\n\nAll new knowledge.",
        )
        _, body = load_skill(path)

        assert "## New Content" in body
        assert "All new knowledge." in body

    def test_updates_related_skills(self, project: Path) -> None:
        _, path = _create_skill(project)
        result = update_skill(
            project,
            "Python asyncio",
            related_skills=("Python", "FastAPI"),
        )

        assert result.related_skills == ("Python", "FastAPI")
        _, body = load_skill(path)
        assert "- [[Python]]" in body

    def test_updates_projects(self, project: Path) -> None:
        _, path = _create_skill(project)
        result = update_skill(
            project,
            "Python asyncio",
            projects=("mantle",),
        )

        assert result.projects == ("mantle",)
        _, body = load_skill(path)
        assert "- [[mantle]]" in body

    def test_refreshes_timestamps(self, project: Path) -> None:
        _create_skill(project)
        result = update_skill(
            project,
            "Python asyncio",
            description="Updated.",
        )

        assert result.updated == date.today()
        assert result.updated_by == MOCK_EMAIL

    def test_refreshes_last_used(self, project: Path) -> None:
        _create_skill(project)
        result = update_skill(
            project,
            "Python asyncio",
            description="Updated.",
        )

        assert result.last_used == date.today()

    def test_preserves_unchanged_fields(self, project: Path) -> None:
        _create_skill(project)
        result = update_skill(
            project,
            "Python asyncio",
            description="Updated.",
        )

        assert result.name == "Python asyncio"
        assert result.proficiency == "7/10"

    def test_preserves_content_when_not_provided(self, project: Path) -> None:
        _, path = _create_skill(project)
        update_skill(
            project,
            "Python asyncio",
            description="Updated.",
        )
        _, body = load_skill(path)

        assert "## Context" in body
        assert "asyncio.TaskGroup" in body

    def test_raises_when_skill_missing(self, project: Path) -> None:
        with pytest.raises(FileNotFoundError):
            update_skill(
                project,
                "Nonexistent Skill",
                description="Nope",
            )


# ── SkillNote model ──────────────────────────────────────────────


class TestSkillNote:
    """Tests for SkillNote data model."""

    def test_frozen(self) -> None:
        note = SkillNote(
            name="Test",
            description="Test description.",
            proficiency="5/10",
            last_used=date.today(),
            author="a@b.com",
            created=date.today(),
            updated=date.today(),
            updated_by="a@b.com",
        )

        with pytest.raises(pydantic.ValidationError):
            note.name = "Changed"  # type: ignore[misc]


# ── _match_skill_slug ────────────────────────────────────────────


class TestMatchSkillSlug:
    """Tests for _match_skill_slug()."""

    def test_finds_matching_path(self, project: Path) -> None:
        _, path = _create_skill(project, name="Python asyncio")

        result = _match_skill_slug("Python asyncio", [path])

        assert result == path

    def test_returns_none_when_no_match(self) -> None:
        paths = [Path("/vault/skills/docker-compose.md")]

        result = _match_skill_slug("Python asyncio", paths)

        assert result is None


# ── detect_gaps ──────────────────────────────────────────────────


class TestDetectGaps:
    """Tests for detect_gaps()."""

    def test_empty_when_skills_required_empty(self, project: Path) -> None:
        _write_state(project, skills_required=())

        result = detect_gaps(project)

        assert result == []

    def test_empty_when_all_matched(self, project_with_state: Path) -> None:
        _create_skill(project_with_state, name="Python asyncio")
        _create_skill(project_with_state, name="WebSocket protocol")

        result = detect_gaps(project_with_state)

        assert result == []

    def test_returns_unmatched_names(self, project_with_state: Path) -> None:
        _create_skill(project_with_state, name="Python asyncio")

        result = detect_gaps(project_with_state)

        assert result == ["WebSocket protocol"]

    def test_matching_is_case_insensitive(self, project: Path) -> None:
        _write_state(
            project,
            skills_required=("PYTHON ASYNCIO",),
        )
        _create_skill(project, name="python asyncio")

        result = detect_gaps(project)

        assert result == []

    def test_matching_normalizes_spaces_to_hyphens(self, project: Path) -> None:
        _write_state(
            project,
            skills_required=("Python asyncio",),
        )
        _create_skill(project, name="Python asyncio")

        result = detect_gaps(project)

        assert result == []

    def test_raises_vault_not_configured(self, project_no_vault: Path) -> None:
        _write_state(
            project_no_vault,
            skills_required=("Python asyncio",),
        )

        with pytest.raises(VaultNotConfiguredError):
            detect_gaps(project_no_vault)


# ── suggest_gap_message ──────────────────────────────────────────


class TestSuggestGapMessage:
    """Tests for suggest_gap_message()."""

    def test_empty_string_for_empty_gaps(self) -> None:
        result = suggest_gap_message([])

        assert result == ""

    def test_lists_each_gap(self) -> None:
        result = suggest_gap_message(["Python asyncio", "WebSocket protocol"])

        assert "Python asyncio" in result
        assert "WebSocket protocol" in result

    def test_includes_add_skill_suggestion(self) -> None:
        result = suggest_gap_message(["Python asyncio"])

        assert "/mantle:add-skill" in result


# ── load_relevant_skills ─────────────────────────────────────────


class TestLoadRelevantSkills:
    """Tests for load_relevant_skills()."""

    def test_empty_when_skills_required_empty(self, project: Path) -> None:
        _write_state(project, skills_required=())

        result = load_relevant_skills(project)

        assert result == []

    def test_loads_matching_skill_with_body(
        self, project_with_state: Path
    ) -> None:
        _create_skill(project_with_state, name="Python asyncio")

        result = load_relevant_skills(project_with_state)

        assert len(result) == 1
        note, body = result[0]
        assert note.name == "Python asyncio"
        assert body  # non-empty

    def test_body_includes_authored_knowledge(
        self, project_with_state: Path
    ) -> None:
        _create_skill(project_with_state, name="Python asyncio")

        result = load_relevant_skills(project_with_state)
        _, body = result[0]

        assert "## Context" in body
        assert "asyncio.TaskGroup" in body
        assert "## Anti-patterns" in body

    def test_skips_missing_skills(self, project_with_state: Path) -> None:
        _create_skill(project_with_state, name="Python asyncio")
        # "WebSocket protocol" not created — should be skipped

        result = load_relevant_skills(project_with_state)

        assert len(result) == 1

    def test_returns_all_matched(self, project_with_state: Path) -> None:
        _create_skill(project_with_state, name="Python asyncio")
        _create_skill(project_with_state, name="WebSocket protocol")

        result = load_relevant_skills(project_with_state)

        assert len(result) == 2
        names = {note.name for note, _ in result}
        assert names == {
            "Python asyncio",
            "WebSocket protocol",
        }

    def test_raises_vault_not_configured(self, project_no_vault: Path) -> None:
        _write_state(
            project_no_vault,
            skills_required=("Python asyncio",),
        )

        with pytest.raises(VaultNotConfiguredError):
            load_relevant_skills(project_no_vault)
