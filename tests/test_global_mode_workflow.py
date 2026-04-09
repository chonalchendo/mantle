"""Integration test: prompts in global storage mode resolve via mantle where."""

from __future__ import annotations

import contextlib
import io
from typing import TYPE_CHECKING

import pytest

from mantle.cli import storage as cli_storage
from mantle.core import migration, project

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def global_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Initialise a project in global storage mode under a fake home."""
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

    project_dir = tmp_path / "workrepo"
    project_dir.mkdir()
    project.init_project(project_dir, project_name="workrepo")
    migration.migrate_to_global(project_dir)

    return project_dir


def test_where_returns_global_path_after_migration(
    global_project: Path,
) -> None:
    """mantle where prints the resolved global path for a migrated project."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cli_storage.run_where(project_dir=global_project)

    output = buf.getvalue().strip()
    resolved_path = project.resolve_mantle_dir(global_project)

    assert output == str(resolved_path.resolve())
    assert ".mantle/projects/" in output
    assert resolved_path.exists()


def test_global_project_state_md_readable_via_resolved_path(
    global_project: Path,
) -> None:
    """After resolution, state.md is readable from the global location."""
    resolved = project.resolve_mantle_dir(global_project)
    state_md = resolved / "state.md"
    assert state_md.is_file()
    assert "workrepo" in state_md.read_text()


def test_global_project_local_mantle_is_absent(
    global_project: Path,
) -> None:
    """After migration, the project dir contains no .mantle/ folder
    at all."""
    local_mantle = global_project / ".mantle"
    assert not local_mantle.exists()
