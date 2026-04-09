"""Tests for mantle.core.migration."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from mantle.core import migration, project
from mantle.core.project import _slugify_name

# Deterministic identity for tests: fake git remote URL.
FAKE_REMOTE = "https://github.com/user/my-project.git"
FAKE_HASH = hashlib.sha256(FAKE_REMOTE.encode()).hexdigest()[:12]


def _mock_subprocess_run(*args: object, **kwargs: object) -> object:
    """Mock subprocess.run to return a deterministic remote URL."""
    return subprocess.CompletedProcess(
        args=[], returncode=0, stdout=FAKE_REMOTE + "\n", stderr=""
    )


def _create_mantle_dir(project_dir: Path) -> Path:
    """Create a realistic .mantle/ directory with config and files."""
    mantle = project_dir / ".mantle"
    mantle.mkdir(parents=True)
    for sub in ("issues", "sessions", "stories"):
        (mantle / sub).mkdir()

    # Write a config.md with frontmatter
    fm = {
        "personal_vault": None,
        "tags": ["type/config"],
    }
    yaml_str = yaml.dump(fm, default_flow_style=False, sort_keys=False)
    (mantle / "config.md").write_text(
        f"---\n{yaml_str}---\n\n{project.CONFIG_BODY}"
    )

    # Add a sample file to verify copy
    (mantle / "issues" / "issue-01-test.md").write_text("# Test issue\n")
    (mantle / "state.md").write_text("# State\n")

    return mantle


def _expected_identity() -> str:
    """Compute the expected identity string for the fake remote."""
    slug = _slugify_name(FAKE_REMOTE)
    return f"{slug}-{FAKE_HASH}"


# ── migrate_to_global ───────────────────────────────────────────


class TestMigrateToGlobal:
    @patch(
        "subprocess.run",
        side_effect=_mock_subprocess_run,
    )
    def test_creates_target(
        self,
        _mock: object,
        tmp_path: Path,
    ) -> None:
        """Verify files are copied to the global path."""
        proj = tmp_path / "myproject"
        proj.mkdir()
        _create_mantle_dir(proj)
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch.object(Path, "home", return_value=fake_home):
            target = migration.migrate_to_global(proj)

        identity = _expected_identity()
        expected = fake_home / ".mantle" / "projects" / identity
        assert target == expected
        assert target.is_dir()
        assert (target / "issues" / "issue-01-test.md").exists()
        assert (target / "state.md").exists()

    @patch(
        "subprocess.run",
        side_effect=_mock_subprocess_run,
    )
    def test_removes_local_dir_entirely(
        self,
        _mock: object,
        tmp_path: Path,
    ) -> None:
        """Verify local .mantle/ is gone entirely after migration."""
        proj = tmp_path / "myproject"
        proj.mkdir()
        _create_mantle_dir(proj)
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch.object(Path, "home", return_value=fake_home):
            migration.migrate_to_global(proj)

        assert not (proj / ".mantle").exists()

    @patch(
        "subprocess.run",
        side_effect=_mock_subprocess_run,
    )
    def test_target_exists_raises(
        self,
        _mock: object,
        tmp_path: Path,
    ) -> None:
        """Verify FileExistsError if target already exists."""
        proj = tmp_path / "myproject"
        proj.mkdir()
        _create_mantle_dir(proj)
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        identity = _expected_identity()
        target = fake_home / ".mantle" / "projects" / identity
        target.mkdir(parents=True)

        with (
            patch.object(Path, "home", return_value=fake_home),
            pytest.raises(FileExistsError),
        ):
            migration.migrate_to_global(proj)


# ── migrate_to_local ────────────────────────────────────────────


class TestMigrateToLocal:
    @patch(
        "subprocess.run",
        side_effect=_mock_subprocess_run,
    )
    def test_copies_back(
        self,
        _mock: object,
        tmp_path: Path,
    ) -> None:
        """Verify files are restored to local path."""
        proj = tmp_path / "myproject"
        proj.mkdir()
        _create_mantle_dir(proj)
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch.object(Path, "home", return_value=fake_home):
            migration.migrate_to_global(proj)
            result = migration.migrate_to_local(proj)

        assert result == proj / ".mantle"
        assert (result / "issues" / "issue-01-test.md").exists()
        assert (result / "state.md").exists()

    @patch(
        "subprocess.run",
        side_effect=_mock_subprocess_run,
    )
    def test_removes_global(
        self,
        _mock: object,
        tmp_path: Path,
    ) -> None:
        """Verify global directory removed after migration."""
        proj = tmp_path / "myproject"
        proj.mkdir()
        _create_mantle_dir(proj)
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch.object(Path, "home", return_value=fake_home):
            target = migration.migrate_to_global(proj)
            migration.migrate_to_local(proj)

        assert not target.exists()


# ── roundtrip ───────────────────────────────────────────────────


class TestRoundtrip:
    @patch(
        "subprocess.run",
        side_effect=_mock_subprocess_run,
    )
    def test_roundtrip(
        self,
        _mock: object,
        tmp_path: Path,
    ) -> None:
        """Migrate to global then back, verify contents match."""
        proj = tmp_path / "myproject"
        proj.mkdir()
        _create_mantle_dir(proj)

        # Capture original file contents
        original_issue = (
            proj / ".mantle" / "issues" / "issue-01-test.md"
        ).read_text()
        original_state = (proj / ".mantle" / "state.md").read_text()

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch.object(Path, "home", return_value=fake_home):
            migration.migrate_to_global(proj)
            migration.migrate_to_local(proj)

        local = proj / ".mantle"
        assert (
            local / "issues" / "issue-01-test.md"
        ).read_text() == original_issue
        assert (local / "state.md").read_text() == original_state
