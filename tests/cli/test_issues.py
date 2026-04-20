"""Tests for mantle.cli.issues."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from typing import TYPE_CHECKING

import pytest
from dirty_equals import IsList, IsPartialDict

from mantle.core import acceptance
from mantle.core import issues as core_issues
from mantle.core.state import ProjectState, Status
from mantle.core.vault import write_note

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
    """Create a minimal .mantle/ with state.md and issues dir."""
    (tmp_path / ".mantle").mkdir()
    (tmp_path / ".mantle" / "issues").mkdir()
    state = ProjectState(
        project="test-project",
        status=Status.SYSTEM_DESIGN,
        created=date(2025, 1, 1),
        created_by=MOCK_EMAIL,
        updated=date(2025, 1, 1),
        updated_by=MOCK_EMAIL,
    )
    body = (
        "## Summary\n\n"
        "Test project\n\n"
        "## Current Focus\n\n"
        "Designing the system.\n\n"
        "## Blockers\n\n"
        "_Anything preventing progress?_\n"
    )
    write_note(tmp_path / ".mantle" / "state.md", state, body)
    return tmp_path


# ── run_save_issue ──────────────────────────────────────────────


class TestRunSaveIssue:
    def test_creates_issue_file(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core", "tests"),
            content="## What to build\n\nBuild it.\n",
            project_dir=project,
        )

        assert (
            project / ".mantle" / "issues" / "issue-01-context-engine.md"
        ).exists()

    def test_prints_confirmation(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core", "tests"),
            content="## What to build\n\nBuild it.\n",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "issue-01-context-engine.md" in captured.out
        assert "Context engine" in captured.out

    def test_prints_slice(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core", "tests"),
            content="## What to build\n\nBuild it.\n",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "core, tests" in captured.out

    def test_prints_blocked_by(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core",),
            content="Build it.\n",
            blocked_by=(2, 5),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Blocked by:" in captured.out
        assert "issue-02" in captured.out
        assert "issue-05" in captured.out

    def test_omits_blocked_by_when_empty(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core",),
            content="Build it.\n",
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Blocked by:" not in captured.out

    def test_passes_skills_required_to_save_issue(
        self,
        project: Path,
    ) -> None:
        from mantle.cli.issues import run_save_issue
        from mantle.core import issues as core_issues

        run_save_issue(
            title="Context engine",
            slice=("core",),
            content="Build it.\n",
            skills_required=("google-python-style", "pytest"),
            project_dir=project,
        )

        issue_path = (
            project / ".mantle" / "issues" / "issue-01-context-engine.md"
        )
        note, _ = core_issues.load_issue(issue_path)
        assert note.skills_required == ("google-python-style", "pytest")

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="Context engine",
            slice=("core",),
            content="Build it.\n",
        )
        captured = capsys.readouterr()

        assert "issue-01-context-engine.md" in captured.out

    def test_handles_issue_exists_error(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_save_issue

        run_save_issue(
            title="First",
            slice=("core",),
            content="Build it.\n",
            project_dir=project,
        )

        with pytest.raises(SystemExit, match="1"):
            run_save_issue(
                title="Second",
                slice=("core",),
                content="Build it again.\n",
                issue=1,
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_handles_invalid_transition(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        (tmp_path / ".mantle").mkdir()
        (tmp_path / ".mantle" / "issues").mkdir()
        state = ProjectState(
            project="test-project",
            status=Status.IDEA,
            created=date(2025, 1, 1),
            created_by=MOCK_EMAIL,
            updated=date(2025, 1, 1),
            updated_by=MOCK_EMAIL,
        )
        body = (
            "## Summary\n\nTest\n\n"
            "## Current Focus\n\nIdea phase.\n\n"
            "## Blockers\n\nNone.\n"
        )
        write_note(tmp_path / ".mantle" / "state.md", state, body)

        from mantle.cli.issues import run_save_issue

        with pytest.raises(SystemExit, match="1"):
            run_save_issue(
                title="Test",
                slice=("core",),
                content="Build it.\n",
                project_dir=tmp_path,
            )

        captured = capsys.readouterr()
        assert "Cannot plan issues" in captured.err


# ── run_set_slices ──────────────────────────────────────────────


class TestRunSetSlices:
    def test_updates_slices(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_set_slices

        run_set_slices(
            slices=("core", "cli", "tests"),
            project_dir=project,
        )

        from mantle.core.state import load_state

        loaded = load_state(project)
        assert loaded.slices == ("core", "cli", "tests")

    def test_prints_confirmation(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_set_slices

        run_set_slices(
            slices=("ingestion", "transformation", "api", "storage"),
            project_dir=project,
        )
        captured = capsys.readouterr()

        assert "Project slices defined (4)" in captured.out
        assert "ingestion, transformation, api, storage" in captured.out

    def test_defaults_to_cwd(
        self,
        project: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(project)

        from mantle.cli.issues import run_set_slices

        run_set_slices(slices=("core",))
        captured = capsys.readouterr()

        assert "Project slices defined" in captured.out


# ── CLI wiring ──────────────────────────────────────────────────


class TestCLIWiring:
    def test_save_issue_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-issue",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "title" in result.stdout.lower()
        assert "slice" in result.stdout.lower()

    def test_save_issue_help_mentions_skills_required(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "save-issue",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "skills-required" in result.stdout

    def test_set_slices_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "set-slices",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "slice" in result.stdout.lower()


# ── Acceptance criteria CLI (flip-ac, list-acs, migrate-acs) ────


def _write_issue_with_acs(
    project_dir: Path,
    issue: int,
    criteria: tuple[acceptance.AcceptanceCriterion, ...],
    *,
    body: str = "## What to build\n\nBuild it.\n\n",
) -> Path:
    """Persist an issue with structured acceptance criteria."""
    note = core_issues.IssueNote(
        title=f"Test issue {issue}",
        status="implementing",
        slice=("core",),
        tags=("type/issue", "status/implementing"),
        acceptance_criteria=criteria,
    )
    full_body = acceptance.replace_ac_section(
        body,
        acceptance.render_ac_section(criteria),
    )
    slug = f"test-issue-{issue}"
    path = project_dir / ".mantle" / "issues" / f"issue-{issue:02d}-{slug}.md"
    write_note(path, note, full_body)
    return path


class TestRunFlipAc:
    def test_flip_ac_marks_pass(self, project: Path) -> None:
        from mantle.cli.issues import run_flip_ac

        path = _write_issue_with_acs(
            project,
            1,
            (
                acceptance.AcceptanceCriterion(
                    id="ac-01", text="First", passes=False
                ),
            ),
        )

        run_flip_ac(
            issue=1,
            ac_id="ac-01",
            passes=True,
            project_dir=project,
        )

        note, body = core_issues.load_issue(path)
        assert note.acceptance_criteria[0].passes is True
        assert "[x] ac-01: First" in body

    def test_flip_ac_marks_fail(self, project: Path) -> None:
        from mantle.cli.issues import run_flip_ac

        path = _write_issue_with_acs(
            project,
            1,
            (
                acceptance.AcceptanceCriterion(
                    id="ac-01", text="First", passes=True
                ),
            ),
        )

        run_flip_ac(
            issue=1,
            ac_id="ac-01",
            passes=False,
            project_dir=project,
        )

        note, _ = core_issues.load_issue(path)
        assert note.acceptance_criteria[0].passes is False

    def test_flip_ac_waive_requires_reason(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_flip_ac

        _write_issue_with_acs(
            project,
            1,
            (acceptance.AcceptanceCriterion(id="ac-01", text="First"),),
        )

        with pytest.raises(SystemExit):
            run_flip_ac(
                issue=1,
                ac_id="ac-01",
                waive=True,
                project_dir=project,
            )

        captured = capsys.readouterr()
        assert "--reason" in captured.err

    def test_flip_ac_unknown_id_exits_1(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_flip_ac

        _write_issue_with_acs(
            project,
            1,
            (acceptance.AcceptanceCriterion(id="ac-01", text="First"),),
        )

        with pytest.raises(SystemExit) as exc_info:
            run_flip_ac(
                issue=1,
                ac_id="ac-99",
                passes=True,
                project_dir=project,
            )

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ac-99" in captured.err


class TestRunListAcs:
    def test_list_acs_json_matches_frontmatter(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_list_acs

        _write_issue_with_acs(
            project,
            1,
            (
                acceptance.AcceptanceCriterion(
                    id="ac-01", text="First", passes=True
                ),
                acceptance.AcceptanceCriterion(
                    id="ac-02", text="Second", passes=False
                ),
            ),
        )

        run_list_acs(issue=1, json_output=True, project_dir=project)

        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload == IsList(
            IsPartialDict(id="ac-01", passes=True, waived=False),
            IsPartialDict(id="ac-02", passes=False, waived=False),
        )

    def test_list_acs_table_contains_ids(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_list_acs

        _write_issue_with_acs(
            project,
            1,
            (
                acceptance.AcceptanceCriterion(id="ac-01", text="First"),
                acceptance.AcceptanceCriterion(id="ac-02", text="Second"),
            ),
        )

        run_list_acs(issue=1, json_output=False, project_dir=project)

        captured = capsys.readouterr()
        assert "ac-01" in captured.out
        assert "ac-02" in captured.out


class TestRunMigrateAcs:
    def test_migrate_acs_reports_zero_when_nothing_to_do(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_migrate_acs

        run_migrate_acs(project_dir=project)

        captured = capsys.readouterr()
        assert "No issues needed migration" in captured.out

    def test_migrate_acs_migrates_legacy_checkboxes(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_migrate_acs

        # Write issue with legacy markdown checkboxes and empty
        # structured ACs.
        note = core_issues.IssueNote(
            title="Legacy",
            status="implementing",
            slice=("core",),
            tags=("type/issue", "status/implementing"),
        )
        body = (
            "## What to build\n\nBuild.\n\n"
            "## Acceptance criteria\n\n"
            "- [ ] First\n"
            "- [x] Second\n"
        )
        path = project / ".mantle" / "issues" / "issue-01-legacy.md"
        write_note(path, note, body)

        run_migrate_acs(project_dir=project)

        note_after, _ = core_issues.load_issue(path)
        assert len(note_after.acceptance_criteria) == 2
        assert note_after.acceptance_criteria[0].passes is False
        assert note_after.acceptance_criteria[1].passes is True

        captured = capsys.readouterr()
        assert "issue-01" in captured.out

    def test_migrate_acs_dry_run_writes_nothing(
        self,
        project: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.issues import run_migrate_acs

        note = core_issues.IssueNote(
            title="Legacy",
            status="implementing",
            slice=("core",),
            tags=("type/issue", "status/implementing"),
        )
        body = (
            "## What to build\n\nBuild.\n\n"
            "## Acceptance criteria\n\n"
            "- [ ] First\n"
            "- [x] Second\n"
        )
        path = project / ".mantle" / "issues" / "issue-01-legacy.md"
        write_note(path, note, body)
        before = path.read_text()

        run_migrate_acs(dry_run=True, project_dir=project)

        assert path.read_text() == before
        captured = capsys.readouterr()
        assert "dry-run" in captured.out
        assert "issue-01-legacy.md" in captured.out
