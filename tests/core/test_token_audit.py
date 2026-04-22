"""Tests for mantle.core.token_audit."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import tiktoken

if TYPE_CHECKING:
    from pathlib import Path

from inline_snapshot import snapshot

from mantle.core import token_audit

# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def cmd_dir(tmp_path: Path) -> Path:
    """Create a small commands directory with three .md files."""
    d = tmp_path / "cmds"
    d.mkdir()
    # Content chosen so token counts are stable and clearly ordered
    (d / "small.md").write_text("hi", encoding="utf-8")
    (d / "medium.md").write_text("hello world foo bar", encoding="utf-8")
    (d / "large.md").write_text(
        "the quick brown fox jumps over the lazy dog " * 5,
        encoding="utf-8",
    )
    return d


# ── count_tokens_in_file ────────────────────────────────────────


class TestCountTokensInFile:
    def test_encodes_content(self, tmp_path: Path) -> None:
        """Token count matches tiktoken directly."""
        f = tmp_path / "sample.md"
        content = "hello world"
        f.write_text(content, encoding="utf-8")

        expected = len(tiktoken.get_encoding("cl100k_base").encode(content))
        assert token_audit.count_tokens_in_file(f) == expected


# ── audit_directory ─────────────────────────────────────────────


class TestAuditDirectory:
    def test_sorts_descending(self, cmd_dir: Path) -> None:
        """Results are sorted by token count, largest first."""
        entries = token_audit.audit_directory(cmd_dir)

        counts = [e.tokens for e in entries]
        assert counts == sorted(counts, reverse=True)

    def test_percents_sum_to_100(self, cmd_dir: Path) -> None:
        """Percent-of-total values sum to approximately 100."""
        entries = token_audit.audit_directory(cmd_dir)

        total = sum(e.percent_of_total for e in entries)
        assert abs(total - 100.0) < 0.01

    def test_empty_dir_returns_empty_list(self, tmp_path: Path) -> None:
        """Empty directory returns an empty list without error."""
        d = tmp_path / "empty"
        d.mkdir()

        assert token_audit.audit_directory(d) == []

    def test_all_files_present(self, cmd_dir: Path) -> None:
        """All three .md files appear in the results."""
        entries = token_audit.audit_directory(cmd_dir)

        names = {e.path.stem for e in entries}
        assert names == {"small", "medium", "large"}


# ── format_report ───────────────────────────────────────────────


class TestFormatReport:
    def test_snapshot(self, cmd_dir: Path) -> None:
        """Report format matches snapshot."""
        entries = token_audit.audit_directory(cmd_dir)
        report = token_audit.format_report(entries)

        assert report == snapshot("""\
# Mantle command token audit — 2026-04-22

Measured with tiktoken (encoding: cl100k_base, ~97% Claude BPE proxy).

## Before

| Rank | Command | Tokens | % of total |
| ---- | ------- | ------:| ----------:|
| 1 | large | 46 | 90.2% |
| 2 | medium | 4 | 7.8% |
| 3 | small | 1 | 2.0% |

**Total:** 51 tokens across 3 command(s).

**Top 3 candidates for rewrite:** large.md, medium.md, small.md
""")

    def test_custom_heading(self, cmd_dir: Path) -> None:
        """Custom heading appears in output."""
        entries = token_audit.audit_directory(cmd_dir)
        report = token_audit.format_report(entries, heading="After")

        assert "## After" in report

    def test_top3_line_present(self, cmd_dir: Path) -> None:
        """Top-3 candidates line is included."""
        entries = token_audit.audit_directory(cmd_dir)
        report = token_audit.format_report(entries)

        assert "**Top 3 candidates for rewrite:**" in report

    def test_total_line_present(self, cmd_dir: Path) -> None:
        """Total token count line is included."""
        entries = token_audit.audit_directory(cmd_dir)
        report = token_audit.format_report(entries)

        assert "**Total:**" in report


# ── append_after_section ────────────────────────────────────────


class TestAppendAfterSection:
    def test_appends_and_computes_delta(
        self, cmd_dir: Path, tmp_path: Path
    ) -> None:
        """After+Delta sections are appended with correct savings."""
        # Write an initial Before report
        before_entries = token_audit.audit_directory(cmd_dir)
        report_path = tmp_path / "audit.md"
        report_path.write_text(
            token_audit.format_report(before_entries),
            encoding="utf-8",
        )

        # Simulate reduced counts (halve large.md's content)
        reduced_dir = tmp_path / "reduced"
        reduced_dir.mkdir()
        for entry in before_entries:
            original = entry.path.read_text(encoding="utf-8")
            # Write half the content so tokens drop
            (reduced_dir / entry.path.name).write_text(
                original[: len(original) // 2], encoding="utf-8"
            )

        after_entries = token_audit.audit_directory(reduced_dir)
        token_audit.append_after_section(report_path, after_entries)

        result = report_path.read_text(encoding="utf-8")
        assert result == snapshot("""\
# Mantle command token audit — 2026-04-22

Measured with tiktoken (encoding: cl100k_base, ~97% Claude BPE proxy).

## Before

| Rank | Command | Tokens | % of total |
| ---- | ------- | ------:| ----------:|
| 1 | large | 46 | 90.2% |
| 2 | medium | 4 | 7.8% |
| 3 | small | 1 | 2.0% |

**Total:** 51 tokens across 3 command(s).

**Top 3 candidates for rewrite:** large.md, medium.md, small.md

## After

| Rank | Command | Before | After | Saved | % saved |
| ---- | ------- | ------:| -----:| -----:| -------:|
| 1 | large | 46 | 23 | 23 | 50.0% |
| 2 | medium | 4 | 2 | 2 | 50.0% |
| 3 | small | 1 | 1 | 0 | 0.0% |

## Delta summary

- Top-3 commands: 25 tokens saved (49.0% reduction).
- Total: 25 tokens saved (49.0% reduction).
""")

    def test_raises_on_unreadable_report(self, tmp_path: Path) -> None:
        """ValueError raised when Before table is missing."""
        bad_report = tmp_path / "bad.md"
        bad_report.write_text("# No table here\n", encoding="utf-8")

        with pytest.raises(ValueError, match="Could not parse"):
            token_audit.append_after_section(bad_report, [])

    def test_raises_if_after_section_already_exists(
        self, cmd_dir: Path, tmp_path: Path
    ) -> None:
        """ValueError raised when report already has an After section."""
        entries = token_audit.audit_directory(cmd_dir)
        report_path = tmp_path / "audit.md"
        report_path.write_text(
            token_audit.format_report(entries), encoding="utf-8"
        )
        token_audit.append_after_section(report_path, entries)

        with pytest.raises(ValueError, match="already contains"):
            token_audit.append_after_section(report_path, entries)
