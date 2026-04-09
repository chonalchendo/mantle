"""Tests for mantle.cli.storage."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from mantle.core import project

if TYPE_CHECKING:
    from pathlib import Path


def _create_project(root: Path, storage_mode: str | None = None) -> None:
    """Create a minimal .mantle/ with config.md."""
    mantle = root / project.MANTLE_DIR
    mantle.mkdir()
    for subdir in project.SUBDIRS:
        (mantle / subdir).mkdir()

    fm_parts = [
        "---",
        "personal_vault: null",
        "auto_push: false",
    ]
    if storage_mode is not None:
        fm_parts.append(f"storage_mode: {storage_mode}")
    else:
        fm_parts.append("storage_mode: null")
    fm_parts.append("tags:")
    fm_parts.append("  - type/config")
    fm_parts.append("---")
    fm_parts.append("")
    fm_parts.append(project.CONFIG_BODY)

    (mantle / "config.md").write_text("\n".join(fm_parts))


# ── run_storage ────────────────────────────────────────────────


class TestStorage:
    def test_storage_set_global(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _create_project(tmp_path)

        from mantle.cli.storage import run_storage

        run_storage(mode="global", project_dir=tmp_path)
        captured = capsys.readouterr()

        assert "Storage mode set to global" in captured.out
        config = project.read_config(tmp_path)
        assert config["storage_mode"] == "global"

    def test_storage_set_local(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _create_project(tmp_path, storage_mode="global")

        from mantle.cli.storage import run_storage

        run_storage(mode="local", project_dir=tmp_path)
        captured = capsys.readouterr()

        assert "Storage mode set to local" in captured.out
        config = project.read_config(tmp_path)
        assert config["storage_mode"] == "local"

    def test_storage_already_set(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _create_project(tmp_path, storage_mode="global")

        from mantle.cli.storage import run_storage

        run_storage(mode="global", project_dir=tmp_path)
        captured = capsys.readouterr()

        assert "already" in captured.out

    def test_storage_invalid_mode(
        self,
        tmp_path: Path,
    ) -> None:
        _create_project(tmp_path)

        from mantle.cli.storage import run_storage

        with pytest.raises(SystemExit):
            run_storage(mode="invalid", project_dir=tmp_path)


# ── run_migrate_storage ────────────────────────────────────────


class TestMigrateStorage:
    def test_migrate_storage_global(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _create_project(tmp_path)
        # Use a fake home to avoid touching real ~/.mantle
        fake_home = tmp_path / "fakehome"
        fake_home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

        from mantle.cli.storage import run_migrate_storage

        run_migrate_storage(direction="global", project_dir=tmp_path)
        captured = capsys.readouterr()

        assert "Migrated to global storage:" in captured.out

    def test_migrate_storage_local(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _create_project(tmp_path, storage_mode="global")
        # Set up a fake global directory
        fake_home = tmp_path / "fakehome"
        fake_home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

        # First migrate to global to set up the state
        from mantle.cli.storage import run_migrate_storage

        run_migrate_storage(direction="global", project_dir=tmp_path)

        # Now migrate back to local
        run_migrate_storage(direction="local", project_dir=tmp_path)
        captured = capsys.readouterr()

        assert "Migrated to local storage:" in captured.out

    def test_migrate_storage_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _create_project(tmp_path)
        fake_home = tmp_path / "fakehome"
        fake_home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

        from mantle.cli.storage import run_migrate_storage

        # First migration succeeds — afterwards .mantle/ is gone.
        run_migrate_storage(direction="global", project_dir=tmp_path)

        # Simulate a re-init in a repo that already has a global
        # dir: rebuild .mantle/ locally and attempt migration again.
        # The global target still exists, so it must raise.
        _create_project(tmp_path)

        with pytest.raises(SystemExit):
            run_migrate_storage(direction="global", project_dir=tmp_path)

        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_migrate_storage_invalid_direction(
        self,
        tmp_path: Path,
    ) -> None:
        _create_project(tmp_path)

        from mantle.cli.storage import run_migrate_storage

        with pytest.raises(SystemExit):
            run_migrate_storage(direction="invalid", project_dir=tmp_path)


# ── run_where ──────────────────────────────────────────────────


class TestWhere:
    def test_where_local_mode(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _create_project(tmp_path)

        from mantle.cli.storage import run_where

        run_where(project_dir=tmp_path)
        captured = capsys.readouterr()

        expected = str((tmp_path / project.MANTLE_DIR).resolve())
        assert captured.out.strip() == expected

    def test_where_global_mode(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _create_project(tmp_path)
        fake_home = tmp_path / "fakehome"
        fake_home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

        identity = project.project_identity(tmp_path)
        global_dir = fake_home / ".mantle" / "projects" / identity
        global_dir.mkdir(parents=True)

        from mantle.cli.storage import run_where

        run_where(project_dir=tmp_path)
        captured = capsys.readouterr()

        prefix = str(fake_home / ".mantle" / "projects") + "/"
        assert captured.out.strip().startswith(prefix)

    def test_where_default_cwd(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _create_project(tmp_path)
        monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)

        from mantle.cli.storage import run_where

        run_where()
        captured = capsys.readouterr()

        expected = str((tmp_path / project.MANTLE_DIR).resolve())
        assert captured.out.strip() == expected

    def test_where_output_is_clean(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _create_project(tmp_path)

        from mantle.cli.storage import run_where

        run_where(project_dir=tmp_path)
        captured = capsys.readouterr()

        assert "\x1b" not in captured.out
        assert captured.out.count("\n") == 1

    def test_where_no_config(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from mantle.cli.storage import run_where

        run_where(project_dir=tmp_path)
        captured = capsys.readouterr()

        expected = str((tmp_path / project.MANTLE_DIR).resolve())
        assert captured.out.strip() == expected


# ── CLI wiring ─────────────────────────────────────────────────


class TestCLIWiring:
    def test_storage_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "storage",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "storage" in result.stdout.lower()

    def test_migrate_storage_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "migrate-storage",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "migrate" in result.stdout.lower()

    def test_where_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "where",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert (
            "where" in result.stdout.lower()
            or "resolved" in result.stdout.lower()
        )
