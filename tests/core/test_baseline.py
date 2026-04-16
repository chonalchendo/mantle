"""Tests for mantle.core.baseline."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mantle.core import vault
from mantle.core.baseline import (
    _python_baseline_for_version,
    resolve_baseline_skills,
)
from mantle.core.skills import create_skill

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.skills.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


def _write_pyproject(project_dir: Path, requires_python: str | None) -> None:
    """Write a minimal pyproject.toml with optional requires-python."""
    if requires_python is None:
        body = '[project]\nname = "demo"\n'
    else:
        body = (
            f'[project]\nname = "demo"\nrequires-python = "{requires_python}"\n'
        )
    (project_dir / "pyproject.toml").write_text(body, encoding="utf-8")


def _write_config(project_dir: Path, vault_path: Path | None) -> None:
    """Write .mantle/config.md with optional personal_vault."""
    mantle = project_dir / ".mantle"
    mantle.mkdir(exist_ok=True)
    from mantle.core.project import _ConfigFrontmatter

    if vault_path is None:
        fm = _ConfigFrontmatter()
    else:
        fm = _ConfigFrontmatter(personal_vault=str(vault_path))
    vault.write_note(mantle / "config.md", fm, "## Config\n")


def _make_project(
    tmp_path: Path,
    *,
    requires_python: str | None = ">=3.14",
    configure_vault: bool = True,
) -> Path:
    """Build a project dir with pyproject, .mantle/config, optional vault."""
    if requires_python is not None:
        _write_pyproject(tmp_path, requires_python)
    vault_path: Path | None = None
    if configure_vault:
        vault_path = tmp_path / "vault"
        (vault_path / "skills").mkdir(parents=True)
    _write_config(tmp_path, vault_path)
    return tmp_path


def _add_python_314_skill(project_dir: Path) -> None:
    """Create a python-314 skill in the configured vault."""
    create_skill(
        project_dir,
        name="python-314",
        description="Python 3.14 syntax and semantics.",
        proficiency="7/10",
        content="## Context\n\nPython 3.14 baseline knowledge.",
    )


# ── _python_baseline_for_version ────────────────────────────────


class TestPythonBaselineForVersion:
    """Tests for the pure version-band mapping."""

    def test_py314_lower_bound(self) -> None:
        assert _python_baseline_for_version(">=3.14") == ("python-314",)

    def test_py315_lower_bound(self) -> None:
        assert _python_baseline_for_version(">=3.15") == ("python-314",)

    def test_py313_returns_empty(self) -> None:
        assert _python_baseline_for_version(">=3.13") == ()

    def test_compatible_release(self) -> None:
        assert _python_baseline_for_version("~=3.14") == ("python-314",)

    def test_wildcard(self) -> None:
        assert _python_baseline_for_version("3.14.*") == ("python-314",)

    def test_unparseable_returns_empty(self) -> None:
        assert _python_baseline_for_version("garbage") == ()

    def test_empty_returns_empty(self) -> None:
        assert _python_baseline_for_version("") == ()


# ── resolve_baseline_skills ─────────────────────────────────────


class TestResolveBaselineSkills:
    """Tests for the resolver that reads pyproject.toml."""

    def test_no_pyproject(self, tmp_path: Path) -> None:
        _write_config(tmp_path, tmp_path / "vault")
        (tmp_path / "vault" / "skills").mkdir(parents=True)

        assert resolve_baseline_skills(tmp_path) == ()

    def test_pyproject_without_requires_python(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path, requires_python=None)
        _write_pyproject(project_dir, requires_python=None)

        assert resolve_baseline_skills(project_dir) == ()

    def test_malformed_toml(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path, requires_python=None)
        (project_dir / "pyproject.toml").write_text(
            "this is = not ]valid[ toml",
            encoding="utf-8",
        )

        assert resolve_baseline_skills(project_dir) == ()

    def test_py314_with_vault_skill(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path, requires_python=">=3.14")
        _add_python_314_skill(project_dir)

        assert resolve_baseline_skills(project_dir) == ("python-314",)

    def test_py314_without_vault_skill(self, tmp_path: Path) -> None:
        project_dir = _make_project(tmp_path, requires_python=">=3.14")

        with pytest.warns(UserWarning, match="python-314"):
            result = resolve_baseline_skills(project_dir)

        assert result == ()

    def test_vault_not_configured(self, tmp_path: Path) -> None:
        project_dir = _make_project(
            tmp_path,
            requires_python=">=3.14",
            configure_vault=False,
        )

        assert resolve_baseline_skills(project_dir) == ()

    def test_py313_ignored_even_if_vault_has_skill(
        self, tmp_path: Path
    ) -> None:
        project_dir = _make_project(tmp_path, requires_python=">=3.13")
        _add_python_314_skill(project_dir)

        assert resolve_baseline_skills(project_dir) == ()
