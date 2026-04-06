"""Tests for /mantle:build prompt file."""

from pathlib import Path

COMMANDS_DIR = Path(__file__).resolve().parents[2] / "claude" / "commands" / "mantle"
BUILD_PROMPT = COMMANDS_DIR / "build.md"


def test_build_md_contains_transition_implementing():
    """build.md Step 6 section contains transition-issue-implementing command."""
    content = BUILD_PROMPT.read_text()
    assert "transition-issue-implementing" in content


def test_build_md_contains_transition_implemented():
    """build.md Step 6 section contains transition-issue-implemented command."""
    content = BUILD_PROMPT.read_text()
    assert "transition-issue-implemented" in content
