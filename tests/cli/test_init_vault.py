"""Tests for mantle.cli.init_vault."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from mantle.core.project import MANTLE_DIR

MOCK_EMAIL = "test@example.com"


def _create_project(root: Path) -> None:
    """Create a minimal .mantle/ with config.md."""
    mantle = root / MANTLE_DIR
    mantle.mkdir()
    (mantle / "config.md").write_text(
        "---\npersonal_vault: null\ntags:\n  - type/config\n---\n\n## Config\n"
    )


# ── CLI run_init_vault ───────────────────────────────────────────


class TestRunInitVault:
    def test_prints_success(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _create_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        from mantle.cli.init_vault import run_init_vault

        vault = tmp_path / "vault"
        run_init_vault(vault)
        captured = capsys.readouterr()

        assert "Created personal vault" in captured.out
        assert "skills/" in captured.out
        assert "knowledge/" in captured.out
        assert "inbox/" in captured.out

    def test_prints_warning_on_existing(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _create_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        vault = tmp_path / "vault"
        for d in ("skills", "knowledge", "inbox", "projects"):
            (vault / d).mkdir(parents=True)

        from mantle.cli.init_vault import run_init_vault

        run_init_vault(vault)
        captured = capsys.readouterr()

        assert "already exists" in captured.out

    def test_prints_error_when_not_initialized(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(tmp_path)

        from mantle.cli.init_vault import run_init_vault

        vault = tmp_path / "vault"

        with pytest.raises(SystemExit):
            run_init_vault(vault)


# ── CLI wiring ───────────────────────────────────────────────────


class TestCLIWiring:
    def test_init_vault_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mantle.cli.main",
                "init-vault",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "vault" in result.stdout.lower()
