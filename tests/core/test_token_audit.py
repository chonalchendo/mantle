"""Tests for mantle.core.token_audit."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest
import tiktoken

if TYPE_CHECKING:
    from pathlib import Path

from inline_snapshot import snapshot

from mantle.core import token_audit

FIXED_DATE = date(2026, 4, 22)

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

    def test_rglob_traverses_subdirectories(self, tmp_path: Path) -> None:
        """audit_directory traverses nested subdirectories via rglob."""
        root = tmp_path / "root"
        root.mkdir()
        (root / "a.md").write_text("hello", encoding="utf-8")
        sub = root / "sub"
        sub.mkdir()
        (sub / "b.md").write_text("world", encoding="utf-8")

        entries = token_audit.audit_directory(root)
        names = {e.path.stem for e in entries}
        assert names == {"a", "b"}


# ── audit_paths ─────────────────────────────────────────────────


class TestAuditPaths:
    def test_groups_by_surface_basename(self, tmp_path: Path) -> None:
        """Two root paths are grouped under their basename keys."""
        cmds = tmp_path / "cmds"
        cmds.mkdir()
        (cmds / "a.md").write_text("hello", encoding="utf-8")
        (cmds / "b.md").write_text("world", encoding="utf-8")

        skills = tmp_path / "skills"
        skills.mkdir()
        (skills / "x.md").write_text("foo", encoding="utf-8")
        (skills / "y.md").write_text("bar", encoding="utf-8")
        (skills / "z.md").write_text("baz", encoding="utf-8")

        result = token_audit.audit_paths([cmds, skills])

        assert set(result.keys()) == {"cmds", "skills"}
        assert len(result["cmds"]) == 2
        assert len(result["skills"]) == 3

    def test_token_counts_per_surface(self, tmp_path: Path) -> None:
        """Token counts sum correctly within each surface."""
        cmds = tmp_path / "cmds"
        cmds.mkdir()
        (cmds / "a.md").write_text("hello", encoding="utf-8")

        skills = tmp_path / "skills"
        skills.mkdir()
        (skills / "x.md").write_text("foo bar baz", encoding="utf-8")

        result = token_audit.audit_paths([cmds, skills])

        cmds_total = sum(e.tokens for e in result["cmds"])
        skills_total = sum(e.tokens for e in result["skills"])

        enc = tiktoken.get_encoding("cl100k_base")
        assert cmds_total == len(enc.encode("hello"))
        assert skills_total == len(enc.encode("foo bar baz"))

    def test_uses_rglob(self, tmp_path: Path) -> None:
        """audit_paths finds files in nested subdirectories."""
        root = tmp_path / "root"
        root.mkdir()
        (root / "a.md").write_text("hello", encoding="utf-8")
        sub = root / "sub"
        sub.mkdir()
        (sub / "b.md").write_text("world", encoding="utf-8")

        result = token_audit.audit_paths([root])

        assert len(result["root"]) == 2

    def test_empty_surface(self, tmp_path: Path) -> None:
        """A path with no .md files returns an empty list under its key."""
        empty = tmp_path / "empty"
        empty.mkdir()

        result = token_audit.audit_paths([empty])

        assert "empty" in result
        assert result["empty"] == []

    def test_per_surface_percent_of_total(self, tmp_path: Path) -> None:
        """Percent-of-total is computed per-surface, not globally."""
        cmds = tmp_path / "cmds"
        cmds.mkdir()
        (cmds / "big.md").write_text("word " * 10, encoding="utf-8")
        (cmds / "small.md").write_text("x", encoding="utf-8")

        skills = tmp_path / "skills"
        skills.mkdir()
        (skills / "only.md").write_text("hello world", encoding="utf-8")

        result = token_audit.audit_paths([cmds, skills])

        # skills surface has one file → must be 100%
        assert abs(result["skills"][0].percent_of_total - 100.0) < 0.01

        # cmds percents should sum to 100
        cmds_pct = sum(e.percent_of_total for e in result["cmds"])
        assert abs(cmds_pct - 100.0) < 0.01


# ── format_report ───────────────────────────────────────────────


class TestFormatReport:
    def test_snapshot_multi_surface(self, tmp_path: Path) -> None:
        """Multi-surface report renders per-surface sub-sections."""
        cmds = tmp_path / "cmds"
        cmds.mkdir()
        (cmds / "small.md").write_text("hi", encoding="utf-8")
        (cmds / "large.md").write_text(
            "the quick brown fox jumps over the lazy dog " * 5,
            encoding="utf-8",
        )

        skills = tmp_path / "skills"
        skills.mkdir()
        (skills / "alpha.md").write_text("hello world foo", encoding="utf-8")
        (skills / "beta.md").write_text("bar", encoding="utf-8")

        per_surface = token_audit.audit_paths([cmds, skills])
        report = token_audit.format_report(per_surface, today=FIXED_DATE)

        assert report == snapshot("""\
# Mantle token audit — 2026-04-22

Measured with tiktoken (encoding: cl100k_base, ~97% Claude BPE proxy).

## Before

### cmds

| Rank | File | Tokens | % of total |
| ---- | ---- | ------:| ----------:|
| 1 | large | 46 | 97.9% |
| 2 | small | 1 | 2.1% |

**Total (cmds):** 47 tokens across 2 file(s).

**Top 3 candidates for rewrite (cmds):** large.md, small.md

### skills

| Rank | File | Tokens | % of total |
| ---- | ---- | ------:| ----------:|
| 1 | alpha | 3 | 75.0% |
| 2 | beta | 1 | 25.0% |

**Total (skills):** 4 tokens across 2 file(s).

**Top 3 candidates for rewrite (skills):** alpha.md, beta.md

**Total (all surfaces):** 51 tokens across 4 files.
""")

    def test_snapshot_single_surface(self, cmd_dir: Path) -> None:
        """Single-surface dict still renders a readable report."""
        per_surface = token_audit.audit_paths([cmd_dir])
        report = token_audit.format_report(per_surface, today=FIXED_DATE)

        assert report == snapshot("""\
# Mantle token audit — 2026-04-22

Measured with tiktoken (encoding: cl100k_base, ~97% Claude BPE proxy).

## Before

### cmds

| Rank | File | Tokens | % of total |
| ---- | ---- | ------:| ----------:|
| 1 | large | 46 | 90.2% |
| 2 | medium | 4 | 7.8% |
| 3 | small | 1 | 2.0% |

**Total (cmds):** 51 tokens across 3 file(s).

**Top 3 candidates for rewrite (cmds):** large.md, medium.md, small.md

**Total (all surfaces):** 51 tokens across 3 files.
""")

    def test_h1_title_no_command_word(self, cmd_dir: Path) -> None:
        """H1 title uses 'token audit', not 'command token audit'."""
        per_surface = token_audit.audit_paths([cmd_dir])
        report = token_audit.format_report(per_surface)

        assert "# Mantle token audit" in report
        assert "command token audit" not in report

    def test_per_surface_subsections(self, tmp_path: Path) -> None:
        """Each surface gets its own ### sub-heading."""
        a = tmp_path / "surface_a"
        a.mkdir()
        (a / "f.md").write_text("hi", encoding="utf-8")
        b = tmp_path / "surface_b"
        b.mkdir()
        (b / "g.md").write_text("hello", encoding="utf-8")

        per_surface = token_audit.audit_paths([a, b])
        report = token_audit.format_report(per_surface)

        assert "### surface_a" in report
        assert "### surface_b" in report

    def test_overall_total_line(self, tmp_path: Path) -> None:
        """Overall total line appears at the end of the report."""
        a = tmp_path / "surf"
        a.mkdir()
        (a / "f.md").write_text("hello", encoding="utf-8")

        per_surface = token_audit.audit_paths([a])
        report = token_audit.format_report(per_surface)

        assert "**Total (all surfaces):**" in report

    def test_custom_heading(self, cmd_dir: Path) -> None:
        """Custom heading appears in output."""
        per_surface = token_audit.audit_paths([cmd_dir])
        report = token_audit.format_report(per_surface, heading="After")

        assert "## After" in report


# ── append_after_section ────────────────────────────────────────


class TestAppendAfterSection:
    def test_appends_multi_surface(self, tmp_path: Path) -> None:
        """After+Delta sections appended correctly for two surfaces."""
        cmds = tmp_path / "cmds"
        cmds.mkdir()
        (cmds / "large.md").write_text(
            "the quick brown fox " * 5, encoding="utf-8"
        )
        (cmds / "small.md").write_text("hi", encoding="utf-8")

        skills = tmp_path / "skills"
        skills.mkdir()
        (skills / "alpha.md").write_text(
            "hello world foo bar baz", encoding="utf-8"
        )

        before_surface = token_audit.audit_paths([cmds, skills])
        report_path = tmp_path / "audit.md"
        report_path.write_text(
            token_audit.format_report(before_surface), encoding="utf-8"
        )

        # Build after dirs with reduced content
        cmds_after = tmp_path / "cmds_after"
        cmds_after.mkdir()
        (cmds_after / "large.md").write_text(
            "the quick brown fox " * 2, encoding="utf-8"
        )
        (cmds_after / "small.md").write_text("hi", encoding="utf-8")

        skills_after = tmp_path / "skills_after"
        skills_after.mkdir()
        (skills_after / "alpha.md").write_text("hello world", encoding="utf-8")

        after_surface = token_audit.audit_paths([cmds_after, skills_after])
        # Remap keys so they match the before surface keys
        after_mapped = {
            "cmds": after_surface["cmds_after"],
            "skills": after_surface["skills_after"],
        }
        token_audit.append_after_section(report_path, after_mapped)

        result = report_path.read_text(encoding="utf-8")
        assert "## After" in result
        assert "## Delta summary" in result
        assert "### cmds" in result
        assert "### skills" in result

    def test_appends_and_snapshot(self, cmd_dir: Path, tmp_path: Path) -> None:
        """After+Delta sections snapshot for single-surface dict."""
        before_entries = token_audit.audit_directory(cmd_dir)
        per_surface_before = {"cmds": before_entries}
        report_path = tmp_path / "audit.md"
        report_path.write_text(
            token_audit.format_report(per_surface_before, today=FIXED_DATE),
            encoding="utf-8",
        )

        # Simulate reduced counts (halve content)
        reduced_dir = tmp_path / "reduced"
        reduced_dir.mkdir()
        for entry in before_entries:
            original = entry.path.read_text(encoding="utf-8")
            (reduced_dir / entry.path.name).write_text(
                original[: len(original) // 2], encoding="utf-8"
            )

        after_entries = token_audit.audit_directory(reduced_dir)
        per_surface_after = {"cmds": after_entries}
        token_audit.append_after_section(report_path, per_surface_after)

        result = report_path.read_text(encoding="utf-8")
        assert result == snapshot("""\
# Mantle token audit — 2026-04-22

Measured with tiktoken (encoding: cl100k_base, ~97% Claude BPE proxy).

## Before

### cmds

| Rank | File | Tokens | % of total |
| ---- | ---- | ------:| ----------:|
| 1 | large | 46 | 90.2% |
| 2 | medium | 4 | 7.8% |
| 3 | small | 1 | 2.0% |

**Total (cmds):** 51 tokens across 3 file(s).

**Top 3 candidates for rewrite (cmds):** large.md, medium.md, small.md

**Total (all surfaces):** 51 tokens across 3 files.

## After

### cmds

| Rank | File | Before | After | Saved | % saved |
| ---- | ---- | ------:| -----:| -----:| -------:|
| 1 | large | 46 | 23 | 23 | 50.0% |
| 2 | medium | 4 | 2 | 2 | 50.0% |
| 3 | small | 1 | 1 | 0 | 0.0% |

## Delta summary

- **cmds**: top-3 saved 25 tokens (49.0%), total saved 25 tokens (49.0% reduction).
- **Overall:** 25 tokens saved (49.0% reduction).
""")

    def test_raises_on_unreadable_report(self, tmp_path: Path) -> None:
        """ValueError raised when Before table is missing."""
        bad_report = tmp_path / "bad.md"
        bad_report.write_text("# No table here\n", encoding="utf-8")

        with pytest.raises(ValueError, match="Could not parse"):
            token_audit.append_after_section(bad_report, {"cmds": []})

    def test_raises_if_after_section_already_exists(
        self, cmd_dir: Path, tmp_path: Path
    ) -> None:
        """ValueError raised when report already has an After section."""
        entries = token_audit.audit_directory(cmd_dir)
        per_surface = {"cmds": entries}
        report_path = tmp_path / "audit.md"
        report_path.write_text(
            token_audit.format_report(per_surface), encoding="utf-8"
        )
        token_audit.append_after_section(report_path, per_surface)

        with pytest.raises(ValueError, match="already contains"):
            token_audit.append_after_section(report_path, per_surface)
