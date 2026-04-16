"""Tests for mantle.cli.main.update_skills_command."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest

from mantle.core import vault
from mantle.core.project import _ConfigFrontmatter
from mantle.core.skills import create_skill
from mantle.core.state import ProjectState, Status, load_state

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


def _write_state(project_dir: Path) -> None:
    """Write a minimal state.md with no skills required."""
    st = ProjectState(
        project="test-project",
        status=Status.IDEA,
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    vault.write_note(
        project_dir / ".mantle" / "state.md",
        st,
        "## Summary\n",
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Project with .mantle/, vault, pyproject.toml, and an issue."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()

    vault_path = tmp_path / "vault"
    (vault_path / "skills").mkdir(parents=True)

    fm = _ConfigFrontmatter(personal_vault=str(vault_path))
    vault.write_note(mantle / "config.md", fm, "## Config\n")

    _write_state(tmp_path)

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nrequires-python = ">=3.14"\n',
        encoding="utf-8",
    )

    issues_dir = mantle / "issues"
    issues_dir.mkdir(parents=True)
    (issues_dir / "issue-01-test.md").write_text(
        "---\ntitle: Test\nstatus: planned\n---\n"
        "Uses Python asyncio for async I/O.\n"
    )

    return tmp_path


def _add_skill(project_dir: Path, name: str) -> None:
    """Create a skill with minimal boilerplate."""
    create_skill(
        project_dir,
        name=name,
        description=f"Description of {name}.",
        proficiency="7/10",
        content=f"## Context\n\n{name} knowledge.",
    )


class TestUpdateSkillsCommand:
    """Tests for update-skills CLI command output contract."""

    def test_reports_baseline_group_on_stderr(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Baseline group is printed on stderr when active."""
        _add_skill(project, "python-314")

        from mantle.cli.main import update_skills_command

        update_skills_command(issue=1, path=project)
        captured = capsys.readouterr()

        assert "Baseline skills (always loaded): python-314" in captured.err

    def test_reports_issue_matched_group_on_stderr(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Issue-matched group is printed on stderr when detected."""
        _add_skill(project, "python-314")
        _add_skill(project, "Python asyncio")

        from mantle.cli.main import update_skills_command

        update_skills_command(issue=1, path=project)
        captured = capsys.readouterr()

        assert "Issue-matched skills (from body scan):" in captured.err
        assert "Python asyncio" in captured.err

    def test_stdout_stays_empty(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Stdout stays empty — piping contract."""
        _add_skill(project, "python-314")
        _add_skill(project, "Python asyncio")

        from mantle.cli.main import update_skills_command

        update_skills_command(issue=1, path=project)
        captured = capsys.readouterr()

        assert captured.out == ""

    def test_no_new_skills_message_on_stderr(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Without baseline or detected skills, falls through to no-op msg."""
        mantle = tmp_path / ".mantle"
        mantle.mkdir()
        vault_path = tmp_path / "vault"
        (vault_path / "skills").mkdir(parents=True)
        fm = _ConfigFrontmatter(personal_vault=str(vault_path))
        vault.write_note(mantle / "config.md", fm, "## Config\n")
        _write_state(tmp_path)

        issues_dir = mantle / "issues"
        issues_dir.mkdir(parents=True)
        (issues_dir / "issue-01-test.md").write_text(
            "---\ntitle: Test\nstatus: planned\n---\nNothing matchable.\n"
        )

        from mantle.cli.main import update_skills_command

        update_skills_command(issue=1, path=tmp_path)
        captured = capsys.readouterr()

        assert "No new skills detected." in captured.err
        loaded = load_state(tmp_path)
        assert loaded.skills_required == ()
