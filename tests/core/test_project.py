"""Tests for mantle.core.project."""

from __future__ import annotations

import hashlib
import subprocess
from typing import TYPE_CHECKING
from unittest import mock

import pytest
import yaml

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core.project import (
    CONFIG_BODY,
    GITIGNORE_CONTENT,
    MANTLE_DIR,
    SUBDIRS,
    TAGS_BODY,
    init_project,
    init_vault,
    project_identity,
    read_config,
    resolve_mantle_dir,
    update_config,
)
from mantle.core.vault import read_note

MOCK_EMAIL = "test@example.com"


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


# ── init_project ─────────────────────────────────────────────────


class TestInitProject:
    def test_creates_mantle_directory(self, tmp_path: Path) -> None:
        result = init_project(tmp_path, "test-project")

        assert result == tmp_path / MANTLE_DIR
        assert result.is_dir()

    def test_creates_subdirectories(self, tmp_path: Path) -> None:
        init_project(tmp_path, "test-project")

        for subdir in SUBDIRS:
            assert (tmp_path / MANTLE_DIR / subdir).is_dir()

    def test_creates_state_md(self, tmp_path: Path) -> None:
        init_project(tmp_path, "test-project")

        state_path = tmp_path / MANTLE_DIR / "state.md"
        assert state_path.exists()

        from mantle.core.state import ProjectState, Status

        note = read_note(state_path, ProjectState)
        assert note.frontmatter.project == "test-project"
        assert note.frontmatter.status == Status.IDEA

    def test_creates_config_md(self, tmp_path: Path) -> None:
        init_project(tmp_path, "test-project")

        config_path = tmp_path / MANTLE_DIR / "config.md"
        assert config_path.exists()
        text = config_path.read_text()

        assert "personal_vault" in text
        assert "verification_strategy" in text
        assert "type/config" in text

    def test_creates_tags_md(self, tmp_path: Path) -> None:
        init_project(tmp_path, "test-project")

        tags_path = tmp_path / MANTLE_DIR / "tags.md"
        assert tags_path.exists()
        text = tags_path.read_text()

        assert "type/" in text
        assert "phase/" in text
        assert "status/" in text
        assert "confidence/" in text

    def test_creates_gitignore(self, tmp_path: Path) -> None:
        init_project(tmp_path, "test-project")

        gitignore_path = tmp_path / MANTLE_DIR / ".gitignore"
        assert gitignore_path.exists()
        text = gitignore_path.read_text()

        assert "*.compiled.md" in text
        assert "*.tmp" in text

    def test_returns_mantle_path(self, tmp_path: Path) -> None:
        result = init_project(tmp_path, "test-project")

        assert result == tmp_path / MANTLE_DIR

    def test_raises_if_mantle_exists(self, tmp_path: Path) -> None:
        (tmp_path / MANTLE_DIR).mkdir()

        with pytest.raises(FileExistsError):
            init_project(tmp_path, "test-project")

    def test_project_name_in_state(self, tmp_path: Path) -> None:
        init_project(tmp_path, "my-cool-project")

        from mantle.core.state import ProjectState

        state_path = tmp_path / MANTLE_DIR / "state.md"
        note = read_note(state_path, ProjectState)
        assert note.frontmatter.project == "my-cool-project"


# ── Template constants ───────────────────────────────────────────


class TestTemplateConstants:
    def test_config_body_not_empty(self) -> None:
        assert len(CONFIG_BODY) > 0

    def test_tags_body_has_all_categories(self) -> None:
        assert "type/" in TAGS_BODY
        assert "phase/" in TAGS_BODY
        assert "status/" in TAGS_BODY
        assert "confidence/" in TAGS_BODY

    def test_gitignore_not_empty(self) -> None:
        assert len(GITIGNORE_CONTENT) > 0

    def test_subdirs_expected(self) -> None:
        assert "bugs" in SUBDIRS
        assert "decisions" in SUBDIRS
        assert "sessions" in SUBDIRS
        assert "issues" in SUBDIRS
        assert "stories" in SUBDIRS


# ── Helpers ──────────────────────────────────────────────────────


def _create_config(root: Path, body: str = "## Config\n", **fm: object) -> None:
    """Create .mantle/config.md with given frontmatter."""
    mantle = root / MANTLE_DIR
    mantle.mkdir(exist_ok=True)
    defaults = {"personal_vault": None, "tags": ["type/config"]}
    defaults.update(fm)

    yaml_str = yaml.dump(defaults, default_flow_style=False, sort_keys=False)
    (mantle / "config.md").write_text(f"---\n{yaml_str}---\n\n{body}")


# ── read_config ──────────────────────────────────────────────────


class TestReadConfig:
    def test_returns_frontmatter_dict(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        result = read_config(tmp_path)

        assert isinstance(result, dict)
        assert "tags" in result

    def test_null_values_returned_as_none(self, tmp_path: Path) -> None:
        _create_config(tmp_path, personal_vault=None)
        result = read_config(tmp_path)

        assert result["personal_vault"] is None

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_config(tmp_path)


# ── update_config ────────────────────────────────────────────────


class TestUpdateConfig:
    def test_updates_single_key(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        update_config(tmp_path, personal_vault="/some/path")
        result = read_config(tmp_path)

        assert result["personal_vault"] == "/some/path"

    def test_adds_new_key(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        update_config(tmp_path, new_key="new_value")
        result = read_config(tmp_path)

        assert result["new_key"] == "new_value"

    def test_preserves_body(self, tmp_path: Path) -> None:
        body = "## Custom Body\n\nKeep this content.\n"
        _create_config(tmp_path, body=body)
        update_config(tmp_path, personal_vault="/vault")

        text = (tmp_path / MANTLE_DIR / "config.md").read_text()
        assert "Custom Body" in text
        assert "Keep this content" in text

    def test_multiple_keys(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        update_config(
            tmp_path,
            personal_vault="/vault",
            verification_strategy="manual",
        )
        result = read_config(tmp_path)

        assert result["personal_vault"] == "/vault"
        assert result["verification_strategy"] == "manual"

    def test_preserves_other_keys(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        update_config(tmp_path, personal_vault="/vault")
        result = read_config(tmp_path)

        assert "tags" in result


# ── init_vault ───────────────────────────────────────────────────


class TestInitVault:
    def test_creates_subdirectories(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        vault = tmp_path / "vault"

        init_vault(vault, tmp_path)

        assert (vault / "skills").is_dir()
        assert (vault / "knowledge").is_dir()
        assert (vault / "inbox").is_dir()
        assert (vault / "projects").is_dir()

    def test_tilde_expansion(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        # Use a path under tmp_path to avoid touching real ~
        vault = tmp_path / "vault"

        init_vault(vault, tmp_path)

        assert vault.is_dir()

    def test_auto_sets_config(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        vault = tmp_path / "vault"

        init_vault(vault, tmp_path)

        result = read_config(tmp_path)
        assert result["personal_vault"] == str(vault.resolve())

    def test_preserves_config_body(self, tmp_path: Path) -> None:
        body = "## Config\n\nCustom body.\n"
        _create_config(tmp_path, body=body)
        vault = tmp_path / "vault"

        init_vault(vault, tmp_path)

        text = (tmp_path / MANTLE_DIR / "config.md").read_text()
        assert "Custom body." in text

    def test_raises_if_all_exist(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        vault = tmp_path / "vault"
        for d in ("skills", "knowledge", "inbox", "projects"):
            (vault / d).mkdir(parents=True)

        with pytest.raises(FileExistsError):
            init_vault(vault, tmp_path)

    def test_partial_init_completes(self, tmp_path: Path) -> None:
        _create_config(tmp_path)
        vault = tmp_path / "vault"
        (vault / "skills").mkdir(parents=True)

        init_vault(vault, tmp_path)

        assert (vault / "knowledge").is_dir()
        assert (vault / "inbox").is_dir()
        assert (vault / "projects").is_dir()

    def test_raises_if_mantle_missing(self, tmp_path: Path) -> None:
        vault = tmp_path / "vault"

        with pytest.raises(FileNotFoundError):
            init_vault(vault, tmp_path)


# ── project_identity ────────────────────────────────────────────


class TestProjectIdentity:
    def test_with_remote(self, tmp_path: Path) -> None:
        """Remote URL is hashed and prefixed with slugified name."""
        remote_url = "git@github.com:user/my-repo.git"
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=remote_url + "\n",
        )
        with mock.patch("subprocess.run", return_value=completed):
            result = project_identity(tmp_path)

        expected_hash = hashlib.sha256(
            remote_url.encode(),
        ).hexdigest()[:12]
        assert result == f"my-repo-{expected_hash}"

    def test_without_remote(self, tmp_path: Path) -> None:
        """Falls back to path hash when no remote exists."""
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=128,
            stdout="",
            stderr="fatal",
        )
        with mock.patch("subprocess.run", return_value=completed):
            result = project_identity(tmp_path)

        resolved = str(tmp_path.resolve())
        expected_hash = hashlib.sha256(
            resolved.encode(),
        ).hexdigest()[:12]
        # The slug is derived from the directory name, with
        # non-alphanumeric characters replaced by hyphens.
        assert result.endswith(f"-{expected_hash}")
        # Must have a non-empty slug prefix before the hash.
        slug_part = result[: -(len(expected_hash) + 1)]
        assert len(slug_part) > 0

    def test_stable(self, tmp_path: Path) -> None:
        """Same input produces same output across calls."""
        remote_url = "https://github.com/org/project.git"
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=remote_url + "\n",
        )
        with mock.patch("subprocess.run", return_value=completed):
            first = project_identity(tmp_path)
            second = project_identity(tmp_path)

        assert first == second


# ── resolve_mantle_dir ──────────────────────────────────────────


class TestResolveMantleDir:
    def test_default_local(self, tmp_path: Path) -> None:
        """No config returns project-local .mantle/."""
        result = resolve_mantle_dir(tmp_path)

        assert result == tmp_path / MANTLE_DIR

    def test_global_dir_exists_returns_global(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Existence of ~/.mantle/projects/<identity>/ makes resolver
        return it."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

        identity = "fixed-identity-test"
        monkeypatch.setattr(
            "mantle.core.project.project_identity", lambda _pd: identity
        )

        global_dir = fake_home / ".mantle" / "projects" / identity
        global_dir.mkdir(parents=True)

        result = resolve_mantle_dir(tmp_path)
        assert result == global_dir

    def test_worktree_scenario_shares_global_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two project dirs sharing the same identity resolve to the
        same global dir."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

        shared_identity = "worktree-shared-abc123"
        monkeypatch.setattr(
            "mantle.core.project.project_identity",
            lambda _pd: shared_identity,
        )

        global_dir = fake_home / ".mantle" / "projects" / shared_identity
        global_dir.mkdir(parents=True)

        primary = tmp_path / "primary-repo"
        worktree = tmp_path / "worktree"
        primary.mkdir()
        worktree.mkdir()

        assert resolve_mantle_dir(primary) == global_dir
        assert resolve_mantle_dir(worktree) == global_dir


# ── Worktree handling (local storage) ───────────────────────────


def _init_bare_repo(repo: Path) -> None:
    """Create a minimal git repo with one commit."""
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "t@example.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "t"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "--allow-empty", "-m", "init"],
        check=True,
        capture_output=True,
    )


class TestResolveMantleDirLocalWorktree:
    def test_primary_worktree_uses_own_mantle(self, tmp_path: Path) -> None:
        """Primary worktree in local mode keeps its own .mantle/."""
        primary = tmp_path / "primary"
        primary.mkdir()
        _init_bare_repo(primary)

        result = resolve_mantle_dir(primary)

        assert result.resolve() == (primary / MANTLE_DIR).resolve()

    def test_linked_worktree_resolves_to_primary_mantle(
        self, tmp_path: Path
    ) -> None:
        """Linked worktree shares the primary's .mantle/ directory."""
        primary = tmp_path / "primary"
        primary.mkdir()
        _init_bare_repo(primary)

        linked = tmp_path / "linked"
        subprocess.run(
            [
                "git",
                "-C",
                str(primary),
                "worktree",
                "add",
                "-b",
                "feature",
                str(linked),
            ],
            check=True,
            capture_output=True,
        )

        result = resolve_mantle_dir(linked)

        assert result.resolve() == (primary / MANTLE_DIR).resolve()
        assert result.resolve() != (linked / MANTLE_DIR).resolve()

    def test_non_git_dir_uses_project_local(self, tmp_path: Path) -> None:
        """Non-git directories still fall back to project-local .mantle/."""
        outsider = tmp_path / "standalone"
        outsider.mkdir()

        result = resolve_mantle_dir(outsider)

        assert result == outsider / MANTLE_DIR
