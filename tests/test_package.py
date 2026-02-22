"""Tests for package skeleton and project standards."""

import re
import subprocess
from pathlib import Path

import mantle

REPO_ROOT = Path(__file__).parent.parent


def test_package_importable():
    assert mantle is not None


def test_version_is_semver():
    pattern = r"^\d+\.\d+\.\d+$"
    assert re.match(pattern, mantle.__version__)


def test_cli_help_lists_install():
    result = subprocess.run(
        ["uv", "run", "mantle", "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "install" in result.stdout.lower()


def test_install_help_outputs_text():
    result = subprocess.run(
        ["uv", "run", "mantle", "install", "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "mount" in result.stdout.lower() or "install" in result.stdout.lower()


def test_claude_md_exists():
    assert (REPO_ROOT / "CLAUDE.md").is_file()


def test_gitignore_exists():
    assert (REPO_ROOT / ".gitignore").is_file()
