"""Tests for mantle.core.verify and issue status transitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mantle.core import issues as issues_mod
from mantle.core import project, vault, verify
from mantle.core.issues import InvalidTransitionError, IssueNote
from mantle.core.verify import (
    VerificationStrategyNotFoundError,
)

if TYPE_CHECKING:
    from pathlib import Path


# ── Helpers ──────────────────────────────────────────────────────


def _init_mantle(tmp_path: Path) -> Path:
    """Create minimal .mantle/ with config.md and issues/."""
    mantle = tmp_path / ".mantle"
    mantle.mkdir()
    (mantle / "issues").mkdir()
    (mantle / "config.md").write_text(
        "---\ntags:\n- type/config\n---\n\n"
        "## Verification Strategy\n\n"
        "## Personal Vault\n",
        encoding="utf-8",
    )
    return tmp_path


def _write_issue(
    project_root: Path,
    issue_number: int,
    *,
    status: str = "planned",
    verification: str | None = None,
) -> Path:
    """Write a minimal issue file."""
    note = IssueNote(
        title=f"Issue {issue_number}",
        status=status,
        slice=("core",),
        verification=verification,
        tags=("type/issue", f"status/{status}"),
    )
    title = f"Issue {issue_number}"
    slug = title.lower().replace(" ", "-")
    path = (
        project_root
        / ".mantle"
        / "issues"
        / f"issue-{issue_number:02d}-{slug}.md"
    )
    vault.write_note(path, note, "## Acceptance Criteria\n\n- Done\n")
    return path


@pytest.fixture
def mantle_project(tmp_path: Path) -> Path:
    """Project with .mantle/ directory structure."""
    return _init_mantle(tmp_path)


# ── load_strategy ────────────────────────────────────────────────


class TestLoadStrategy:
    def test_from_config(self, mantle_project: Path) -> None:
        """Strategy loaded from config when no issue override."""
        _write_issue(mantle_project, 1)
        project.update_config(
            mantle_project,
            verification_strategy="Run tests and check coverage",
        )

        strategy, is_override = verify.load_strategy(mantle_project, 1)

        assert strategy == "Run tests and check coverage"
        assert is_override is False

    def test_per_issue_override(self, mantle_project: Path) -> None:
        """Per-issue verification takes precedence over config."""
        _write_issue(
            mantle_project,
            2,
            verification="Manual smoke test",
        )
        project.update_config(
            mantle_project,
            verification_strategy="Run tests and check coverage",
        )

        strategy, is_override = verify.load_strategy(mantle_project, 2)

        assert strategy == "Manual smoke test"
        assert is_override is True

    def test_not_found(self, mantle_project: Path) -> None:
        """Raises when neither config nor issue has strategy."""
        _write_issue(mantle_project, 3)

        with pytest.raises(VerificationStrategyNotFoundError):
            verify.load_strategy(mantle_project, 3)


# ── save_strategy ────────────────────────────────────────────────


class TestSaveStrategy:
    def test_persists_to_config(self, mantle_project: Path) -> None:
        """Strategy is persisted and readable from config."""
        verify.save_strategy(mantle_project, "Run full test suite")

        config = project.read_config(mantle_project)
        assert config["verification_strategy"] == "Run full test suite"


# ── build_report ─────────────────────────────────────────────────


class TestBuildReport:
    def test_all_pass(self) -> None:
        """Report with all passing results has passed=True."""
        report = verify.build_report(
            issue_number=1,
            title="Feature A",
            results=[
                ("Tests pass", True, None),
                ("Linter clean", True, "No warnings"),
            ],
            strategy_used="Standard",
            is_override=False,
        )

        assert report.passed is True
        assert len(report.results) == 2
        assert report.issue == 1

    def test_some_fail(self) -> None:
        """Report with mixed results has passed=False."""
        report = verify.build_report(
            issue_number=2,
            title="Feature B",
            results=[
                ("Tests pass", True, None),
                ("Coverage >= 80%", False, "Coverage is 72%"),
            ],
            strategy_used="Standard",
            is_override=False,
        )

        assert report.passed is False


# ── format_report ────────────────────────────────────────────────


class TestFormatReport:
    def test_markdown_output(self) -> None:
        """Formatted report contains checkmarks and crosses."""
        report = verify.build_report(
            issue_number=5,
            title="Widget feature",
            results=[
                ("Tests pass", True, None),
                ("Coverage >= 80%", False, "Coverage is 72%"),
            ],
            strategy_used="Standard",
            is_override=False,
        )

        text = verify.format_report(report)

        assert "\u2713 Tests pass" in text
        assert "\u2717 Coverage >= 80%" in text
        assert "Coverage is 72%" in text
        assert "FAILED" in text
        assert "Issue 5" in text


# ── transition_to_verified ───────────────────────────────────────


class TestTransitionToVerified:
    def test_from_implemented(self, mantle_project: Path) -> None:
        """Issue with status 'implemented' transitions to verified."""
        _write_issue(mantle_project, 10, status="implemented")

        path = issues_mod.transition_to_verified(mantle_project, 10)

        note, _ = issues_mod.load_issue(path)
        assert note.status == "verified"
        assert "status/verified" in note.tags

    def test_invalid_status(self, mantle_project: Path) -> None:
        """Issue with status 'planned' cannot transition."""
        _write_issue(mantle_project, 11, status="planned")

        with pytest.raises(InvalidTransitionError):
            issues_mod.transition_to_verified(mantle_project, 11)


# ── introspect_project ──────────────────────────────────────────


class TestIntrospectProject:
    def test_detects_pytest_from_claude_md(self, tmp_path: Path) -> None:
        """Detects test command from CLAUDE.md."""
        (tmp_path / "CLAUDE.md").write_text(
            "## Development\n\n- Run tests: `uv run pytest`\n",
            encoding="utf-8",
        )

        result = verify.introspect_project(tmp_path)

        assert result["test_command"] == "uv run pytest"

    def test_detects_just_check_from_claude_md(self, tmp_path: Path) -> None:
        """Detects check command from CLAUDE.md."""
        (tmp_path / "CLAUDE.md").write_text(
            "## Development\n\n- Run all checks: `just check`\n",
            encoding="utf-8",
        )

        result = verify.introspect_project(tmp_path)

        assert result["check_command"] == "just check"

    def test_detects_from_justfile(self, tmp_path: Path) -> None:
        """Detects test command from Justfile recipe."""
        (tmp_path / "Justfile").write_text(
            "test:\n    uv run pytest\n",
            encoding="utf-8",
        )

        result = verify.introspect_project(tmp_path)

        assert result["test_command"] is not None

    def test_detects_ruff_from_pyproject(self, tmp_path: Path) -> None:
        """Detects lint command from pyproject.toml [tool.ruff]."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.ruff]\nline-length = 80\n",
            encoding="utf-8",
        )

        result = verify.introspect_project(tmp_path)

        assert result["lint_command"] is not None

    def test_no_files_returns_none_values(self, tmp_path: Path) -> None:
        """Empty project returns None for all commands."""
        result = verify.introspect_project(tmp_path)

        assert result["test_command"] is None
        assert result["lint_command"] is None
        assert result["check_command"] is None
        assert result["type_check_command"] is None

    def test_claude_md_takes_priority(self, tmp_path: Path) -> None:
        """CLAUDE.md test command wins over Justfile."""
        (tmp_path / "CLAUDE.md").write_text(
            "- Run tests: `uv run pytest`\n",
            encoding="utf-8",
        )
        (tmp_path / "Justfile").write_text(
            "test:\n    make test\n",
            encoding="utf-8",
        )

        result = verify.introspect_project(tmp_path)

        assert result["test_command"] == "uv run pytest"


# ── generate_structured_strategy ────────────────────────────────


class TestGenerateStructuredStrategy:
    def test_all_detected(self) -> None:
        """All sections populated when all commands detected."""
        introspection = {
            "test_command": "uv run pytest",
            "lint_command": "ruff check .",
            "check_command": "just check",
            "type_check_command": "mypy src/",
        }

        result = verify.generate_structured_strategy(introspection)

        assert "uv run pytest" in result
        assert "ruff check ." in result
        assert "mypy src/" in result
        assert "## Test Command" in result
        assert "## Lint/Format Check" in result
        assert "## Type Check" in result
        assert "## Acceptance Criteria Verification" in result

    def test_none_values_show_not_detected(self) -> None:
        """None values produce 'Not detected' in output."""
        introspection = {
            "test_command": None,
            "lint_command": None,
            "check_command": None,
            "type_check_command": None,
        }

        result = verify.generate_structured_strategy(introspection)

        assert "Not detected" in result

    def test_partial_detection(self) -> None:
        """Partial detection produces correct structure."""
        introspection = {
            "test_command": "uv run pytest",
            "lint_command": None,
            "check_command": None,
            "type_check_command": None,
        }

        result = verify.generate_structured_strategy(introspection)

        assert "uv run pytest" in result
        assert "## Test Command" in result
        assert "## Lint/Format Check" in result
        assert "## Type Check" in result
        assert "Not detected" in result
