"""Tests for /mantle:implement prompt file."""

from pathlib import Path

COMMANDS_DIR = (
    Path(__file__).resolve().parents[2] / "claude" / "commands" / "mantle"
)
IMPLEMENT_PROMPT = COMMANDS_DIR / "implement.md"


def test_implement_md_contains_transition_implementing():
    """implement.md contains transition-issue-implementing command."""
    content = IMPLEMENT_PROMPT.read_text()
    assert "transition-issue-implementing" in content
