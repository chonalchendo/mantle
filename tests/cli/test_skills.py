"""Tests for mantle.cli.skills."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from mantle.core import vault
from mantle.core.project import _ConfigFrontmatter

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"

SAMPLE_CONTENT = "## Context\n\nSample skill knowledge."


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a .mantle/ with config pointing to a vault."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()

    vault_path = tmp_path / "vault"
    (vault_path / "skills").mkdir(parents=True)

    fm = _ConfigFrontmatter(personal_vault=str(vault_path))
    vault.write_note(mantle / "config.md", fm, "## Config\n")

    return tmp_path


@pytest.fixture
def project_no_vault(tmp_path: Path) -> Path:
    """Create a .mantle/ with no personal_vault configured."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()

    fm = _ConfigFrontmatter()
    vault.write_note(mantle / "config.md", fm, "## Config\n")

    return tmp_path


def _save_skill(project_dir: Path, **overrides: object) -> None:
    from mantle.cli.skills import run_save_skill

    defaults: dict[str, object] = {
        "name": "Python asyncio",
        "description": (
            "Async Python patterns using asyncio. "
            "Use when building concurrent I/O-bound services."
        ),
        "proficiency": "7/10",
        "content": SAMPLE_CONTENT,
    }
    defaults.update(overrides)
    run_save_skill(project_dir=project_dir, **defaults)


# ── run_save_skill ──────────────────────────────────────────────


class TestRunSaveSkill:
    """Tests for run_save_skill()."""

    def test_prints_skill_saved(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(project)
        captured = capsys.readouterr()

        assert "Skill saved" in captured.out

    def test_prints_skill_name(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(project)
        captured = capsys.readouterr()

        assert "Python asyncio" in captured.out

    def test_prints_description(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(project)
        captured = capsys.readouterr()

        assert "Async Python patterns" in captured.out

    def test_prints_proficiency(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(project)
        captured = capsys.readouterr()

        assert "7/10" in captured.out

    def test_prints_next_step(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(project)
        captured = capsys.readouterr()

        assert "/mantle:add-skill" in captured.out

    def test_warns_on_existing(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(project)

        with pytest.raises(SystemExit, match="1"):
            _save_skill(project)

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_overwrite_succeeds(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(project)
        _save_skill(project, overwrite=True, proficiency="9/10")

        captured = capsys.readouterr()
        assert "Skill saved" in captured.out

    def test_errors_on_vault_not_configured(
        self,
        project_no_vault: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit, match="1"):
            _save_skill(project_no_vault)

        captured = capsys.readouterr()
        assert "vault not configured" in captured.out.lower()

    def test_errors_on_bad_proficiency(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit, match="1"):
            _save_skill(project, proficiency="high")

        captured = capsys.readouterr()
        assert "proficiency" in captured.out.lower()

    def test_save_skill_with_tags(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(
            project,
            tags=("topic/python-asyncio", "domain/concurrency"),
        )
        captured = capsys.readouterr()

        assert "Skill saved" in captured.out

        # Verify tags were written to the skill file.
        from mantle.core import skills

        skill_path = project / "vault" / "skills" / "python-asyncio.md"
        note, _ = skills.load_skill(skill_path)
        assert "topic/python-asyncio" in note.tags
        assert "domain/concurrency" in note.tags
        assert "type/skill" in note.tags

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.skills import run_save_skill

        run_save_skill(
            name="Python asyncio",
            description="Test.",
            proficiency="5/10",
            content=SAMPLE_CONTENT,
        )
        captured = capsys.readouterr()

        assert "Skill saved" in captured.out


# ── list-skills command ──────────────────────────────────────────


class TestListSkillsCommand:
    """Tests for list-skills command with --tag filtering."""

    def test_tag_flag_filters_output(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(
            project,
            name="Python asyncio",
            tags=("type/skill", "topic/python"),
        )
        _save_skill(
            project,
            name="Docker compose",
            description="Docker container orchestration.",
            tags=("type/skill", "domain/devops"),
        )
        # Clear save output before testing list command
        capsys.readouterr()

        from mantle.cli.main import list_skills_command

        list_skills_command(tag="topic/python", path=project)
        captured = capsys.readouterr()

        assert "python-asyncio" in captured.out
        assert "docker-compose" not in captured.out

    def test_tag_flag_empty_prints_message(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(
            project,
            name="Python asyncio",
            tags=("type/skill", "topic/python"),
        )

        from mantle.cli.main import list_skills_command

        list_skills_command(tag="domain/web", path=project)
        captured = capsys.readouterr()

        assert "No skills matching tag 'domain/web'" in captured.out

    def test_list_skills_shows_descriptions(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(
            project,
            name="Python asyncio",
            description="Async Python patterns.",
        )
        capsys.readouterr()

        from mantle.cli.main import list_skills_command

        list_skills_command(path=project)
        captured = capsys.readouterr()

        assert "python-asyncio" in captured.out
        assert "Async Python patterns." in captured.out
        # Verify the slug-description format
        assert "python-asyncio \u2014 Async Python patterns." in captured.out

    def test_list_skills_with_tag_shows_descriptions(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _save_skill(
            project,
            name="Python asyncio",
            description="Async Python patterns.",
            tags=("type/skill", "topic/python"),
        )
        _save_skill(
            project,
            name="Docker compose",
            description="Docker container orchestration.",
            tags=("type/skill", "domain/devops"),
        )
        capsys.readouterr()

        from mantle.cli.main import list_skills_command

        list_skills_command(tag="topic/python", path=project)
        captured = capsys.readouterr()

        assert "python-asyncio \u2014 Async Python patterns." in captured.out
        assert "docker-compose" not in captured.out

    def test_list_skills_help_mentions_tag(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "list-skills",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "--tag" in result.stdout


# ── CLI wiring ──────────────────────────────────────────────────


class TestCLIWiring:
    """Tests for save-skill CLI integration."""

    def test_save_skill_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-skill",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        out = result.stdout.lower()
        assert "name" in out
        assert "description" in out
        assert "content" in out
