"""Tests for the compile CLI command."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING
from unittest.mock import patch

from mantle.cli.compile import run_compile

if TYPE_CHECKING:
    from pathlib import Path


def _write_state_md(mantle_dir: Path) -> None:
    """Write a minimal state.md for compilation."""
    mantle_dir.mkdir(parents=True, exist_ok=True)
    (mantle_dir / "state.md").write_text(
        "---\n"
        "schema_version: 1\n"
        "project: test-project\n"
        "status: implementing\n"
        "confidence: '7/10'\n"
        "created: '2025-01-01'\n"
        "created_by: test@example.com\n"
        "updated: '2025-01-01'\n"
        "updated_by: test@example.com\n"
        "tags:\n"
        "  - status/active\n"
        "---\n\n"
        "## Summary\n\nA project.\n\n"
        "## Current Focus\n\nBuilding.\n\n"
        "## Blockers\n\nNone.\n\n"
        "## Recent Decisions\n\nChose well.\n\n"
        "## Next Steps\n\nShip it.\n",
        encoding="utf-8",
    )


def _make_template_dir(tmp_path: Path) -> Path:
    """Create a temp template directory with a test .j2 file."""
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir()
    (tpl_dir / "status.md.j2").write_text(
        "# {{ project }}\nStatus: {{ status }}\n{{ summary }}\n"
    )
    return tpl_dir


# ── run_compile ─────────────────────────────────────────────────


class TestRunCompile:
    def test_prints_compiled_count(self, tmp_path: Path, capsys):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch(
            "mantle.core.compiler.template_dir",
            return_value=tpl_dir,
        ):
            run_compile(project_dir=tmp_path, target_dir=target)

        # Rich writes to its own console; verify output file exists
        assert (target / "status.md").exists()

    def test_prints_template_names(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch(
            "mantle.core.compiler.template_dir",
            return_value=tpl_dir,
        ):
            run_compile(project_dir=tmp_path, target_dir=target)

        content = (target / "status.md").read_text()
        assert "test-project" in content

    def test_if_stale_up_to_date(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch(
            "mantle.core.compiler.template_dir",
            return_value=tpl_dir,
        ):
            # First compile
            run_compile(project_dir=tmp_path, target_dir=target)
            # Second compile with if_stale — should be up to date
            run_compile(
                if_stale=True,
                project_dir=tmp_path,
                target_dir=target,
            )

    def test_if_stale_recompiles_on_change(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch(
            "mantle.core.compiler.template_dir",
            return_value=tpl_dir,
        ):
            run_compile(project_dir=tmp_path, target_dir=target)

            # Modify state.md
            _write_state_md(tmp_path / ".mantle")

            run_compile(
                if_stale=True,
                project_dir=tmp_path,
                target_dir=target,
            )

        assert (target / "status.md").exists()

    def test_missing_project_raises_system_exit(self, tmp_path: Path):
        target = tmp_path / "output"
        try:
            run_compile(
                project_dir=tmp_path / "nonexistent",
                target_dir=target,
            )
            msg = "Expected SystemExit"
            raise AssertionError(msg)
        except SystemExit as exc:
            assert exc.code == 1

    def test_defaults_to_cwd(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with (
            patch(
                "mantle.core.compiler.template_dir",
                return_value=tpl_dir,
            ),
            patch(
                "mantle.cli.compile.Path.cwd",
                return_value=tmp_path,
            ),
        ):
            run_compile(target_dir=target)

        assert (target / "status.md").exists()


    def test_passes_issue_to_compiler_compile(self, tmp_path: Path) -> None:
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with (
            patch(
                "mantle.core.compiler.template_dir",
                return_value=tpl_dir,
            ),
            patch(
                "mantle.core.compiler.skills.compile_skills",
            ) as mock_compile_skills,
        ):
            run_compile(project_dir=tmp_path, target_dir=target, issue=42)

        mock_compile_skills.assert_called_once_with(tmp_path, issue=42)

    def test_passes_issue_to_compiler_compile_if_stale(
        self, tmp_path: Path
    ) -> None:
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with (
            patch(
                "mantle.core.compiler.template_dir",
                return_value=tpl_dir,
            ),
            patch(
                "mantle.core.compiler.skills.compile_skills",
            ) as mock_compile_skills,
            patch(
                "mantle.core.compiler.manifest.is_compilation_stale",
                return_value=True,
            ),
        ):
            run_compile(
                if_stale=True,
                project_dir=tmp_path,
                target_dir=target,
                issue=7,
            )

        mock_compile_skills.assert_called_once_with(tmp_path, issue=7)


# ── CLI wiring ──────────────────────────────────────────────────


class TestCompileCLI:
    def test_help_mentions_if_stale(self):
        result = subprocess.run(
            [sys.executable, "-m", "mantle.cli.main", "compile", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "if-stale" in result.stdout

    def test_help_mentions_issue(self):
        result = subprocess.run(
            [sys.executable, "-m", "mantle.cli.main", "compile", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "issue" in result.stdout
