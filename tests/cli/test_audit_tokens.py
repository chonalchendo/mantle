"""Tests for mantle.cli.audit_tokens."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot

if TYPE_CHECKING:
    from pathlib import Path

from mantle.cli import audit_tokens

FIXED_DATE = date(2026, 4, 22)

# ── Fixtures ────────────────────────────────────────────────────


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    """Create a commands directory under a tmp project root."""
    d = tmp_path / "claude" / "commands" / "mantle"
    d.mkdir(parents=True)
    (d / "build.md").write_text("build command content", encoding="utf-8")
    (d / "review.md").write_text("review command", encoding="utf-8")
    return tmp_path


@pytest.fixture
def two_surface_dirs(tmp_path: Path) -> tuple[Path, Path]:
    """Create two separate surface directories."""
    cmds = tmp_path / "cmds"
    cmds.mkdir()
    (cmds / "a.md").write_text("hello world", encoding="utf-8")
    (cmds / "b.md").write_text("foo bar", encoding="utf-8")

    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "x.md").write_text("alpha beta gamma", encoding="utf-8")

    return cmds, skills


# ── run_audit_tokens ────────────────────────────────────────────


class TestRunAuditTokens:
    def test_single_path_default_writes_report(
        self,
        prompt_dir: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Default path writes a report containing audit content."""
        monkeypatch.chdir(prompt_dir)
        out_path = tmp_path / "report.md"

        audit_tokens.run_audit_tokens(path=None, out=out_path)

        report = out_path.read_text(encoding="utf-8")
        assert "# Mantle token audit" in report
        assert "## Before" in report
        assert "**Total (all surfaces):**" in report

    def test_multi_path_report_contains_both_surfaces(
        self,
        two_surface_dirs: tuple[Path, Path],
        tmp_path: Path,
    ) -> None:
        """Report with two paths contains both surface sub-sections."""
        cmds, skills = two_surface_dirs
        out_path = tmp_path / "report.md"

        audit_tokens.run_audit_tokens(path=[cmds, skills], out=out_path)

        report = out_path.read_text(encoding="utf-8")
        assert "### cmds" in report
        assert "### skills" in report
        assert "**Total (all surfaces):**" in report

    def test_multi_path_snapshot(
        self,
        two_surface_dirs: tuple[Path, Path],
        tmp_path: Path,
    ) -> None:
        """Multi-path report matches snapshot."""
        cmds, skills = two_surface_dirs
        out_path = tmp_path / "report.md"

        audit_tokens.run_audit_tokens(
            path=[cmds, skills], out=out_path, today=FIXED_DATE
        )

        report = out_path.read_text(encoding="utf-8")
        assert report == snapshot("""\
# Mantle token audit — 2026-04-22

Measured with tiktoken (encoding: cl100k_base, ~97% Claude BPE proxy).

## Before

### cmds

| Rank | File | Tokens | % of total |
| ---- | ---- | ------:| ----------:|
| 1 | a | 2 | 50.0% |
| 2 | b | 2 | 50.0% |

**Total (cmds):** 4 tokens across 2 file(s).

**Top 3 candidates for rewrite (cmds):** a.md, b.md

### skills

| Rank | File | Tokens | % of total |
| ---- | ---- | ------:| ----------:|
| 1 | x | 3 | 100.0% |

**Total (skills):** 3 tokens across 1 file(s).

**Top 3 candidates for rewrite (skills):** x.md

**Total (all surfaces):** 7 tokens across 3 files.
""")

    def test_append_requires_out(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--append without --out raises SystemExit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            audit_tokens.run_audit_tokens(append=True, out=None)

        assert exc_info.value.code == 1

    def test_prints_report_path(
        self,
        prompt_dir: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Success message printed with report path."""
        monkeypatch.chdir(prompt_dir)
        out_path = tmp_path / "report.md"

        audit_tokens.run_audit_tokens(path=None, out=out_path)

        captured = capsys.readouterr()
        assert str(out_path) in captured.out

    def test_append_mode(
        self,
        two_surface_dirs: tuple[Path, Path],
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--append mode appends After section to existing report."""
        cmds, skills = two_surface_dirs
        out_path = tmp_path / "report.md"

        # First write a Before report
        audit_tokens.run_audit_tokens(path=[cmds, skills], out=out_path)

        # Now append with same dirs (delta will be zero, but structure valid)
        audit_tokens.run_audit_tokens(
            path=[cmds, skills], out=out_path, append=True
        )

        report = out_path.read_text(encoding="utf-8")
        assert "## After" in report
        assert "## Delta summary" in report
