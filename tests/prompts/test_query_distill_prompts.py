"""Tests for /mantle:query and /mantle:distill prompt files."""

from pathlib import Path

COMMANDS_DIR = Path(__file__).resolve().parents[2] / "claude" / "commands" / "mantle"
QUERY_PROMPT = COMMANDS_DIR / "query.md"
DISTILL_PROMPT = COMMANDS_DIR / "distill.md"


def test_query_prompt_exists():
    """query.md exists in the mantle commands directory."""
    assert QUERY_PROMPT.is_file(), f"Expected {QUERY_PROMPT} to exist"


def test_query_prompt_has_frontmatter():
    """query.md contains argument-hint and allowed-tools frontmatter."""
    content = QUERY_PROMPT.read_text()
    assert "argument-hint" in content
    assert "allowed-tools" in content


def test_query_prompt_mentions_citations():
    """query.md instructs Claude to cite sources."""
    content = QUERY_PROMPT.read_text().lower()
    assert "cite" in content or "source" in content


def test_query_prompt_mentions_distillations():
    """query.md references checking existing distillations."""
    content = QUERY_PROMPT.read_text()
    assert "distillation" in content or "list-distillations" in content


def test_distill_prompt_exists():
    """distill.md exists in the mantle commands directory."""
    assert DISTILL_PROMPT.is_file(), f"Expected {DISTILL_PROMPT} to exist"


def test_distill_prompt_has_frontmatter():
    """distill.md contains argument-hint and allowed-tools frontmatter."""
    content = DISTILL_PROMPT.read_text()
    assert "argument-hint" in content
    assert "allowed-tools" in content


def test_distill_prompt_mentions_wikilinks():
    """distill.md instructs Claude to include wikilinks."""
    content = DISTILL_PROMPT.read_text()
    assert "wikilink" in content or "[[" in content


def test_distill_prompt_mentions_staleness():
    """distill.md references staleness or source tracking."""
    content = DISTILL_PROMPT.read_text().lower()
    assert "stale" in content or "source_count" in content or "source_paths" in content


def test_distill_prompt_invokes_save():
    """distill.md contains a mantle save-distillation CLI call."""
    content = DISTILL_PROMPT.read_text()
    assert "mantle save-distillation" in content
