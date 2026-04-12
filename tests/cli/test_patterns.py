"""Tests for mantle.cli.patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mantle.cli import patterns as cli_patterns

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


LEARNING_BODY_TEMPLATE = """\
## What went well

- Good thing happened

## Harder than expected

- {harder}

## Wrong assumptions

- {wrong}

## Recommendations

- {rec}
"""


def _write_learning(
    project_dir: Path,
    *,
    issue: int,
    title: str = "something",
    confidence_delta: str = "+1",
    harder: str = "testing was harder than expected",
    wrong: str = "assumed scope was small",
    rec: str = "pytest coverage next time",
) -> None:
    """Write a synthetic learning file under .mantle/learnings/."""
    learnings_dir = project_dir / ".mantle" / "learnings"
    learnings_dir.mkdir(parents=True, exist_ok=True)
    path = learnings_dir / f"issue-{issue:02d}-{title}.md"
    body = LEARNING_BODY_TEMPLATE.format(harder=harder, wrong=wrong, rec=rec)
    frontmatter = (
        "---\n"
        f"issue: {issue}\n"
        f"title: {title}\n"
        "author: test@example.com\n"
        "date: '2026-01-01'\n"
        f"confidence_delta: '{confidence_delta}'\n"
        "tags:\n"
        "- type/learning\n"
        "- phase/reviewing\n"
        "---\n\n"
    )
    path.write_text(frontmatter + body, encoding="utf-8")


def _write_issue(
    project_dir: Path,
    *,
    issue: int,
    title: str = "something",
    slice_: tuple[str, ...] = ("core",),
) -> None:
    """Write a synthetic issue file under .mantle/issues/."""
    issues_dir = project_dir / ".mantle" / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    path = issues_dir / f"issue-{issue:02d}-{title}.md"
    slice_yaml = "\n".join(f"- {s}" for s in slice_)
    frontmatter = (
        "---\n"
        f"title: {title}\n"
        "status: planned\n"
        "slice:\n"
        f"{slice_yaml}\n"
        "story_count: 0\n"
        "verification: null\n"
        "blocked_by: []\n"
        "skills_required: []\n"
        "tags:\n"
        "- type/issue\n"
        "- status/planned\n"
        "---\n\n"
        "## Why\nx\n"
    )
    path.write_text(frontmatter, encoding="utf-8")


def test_show_patterns_prints_themes_and_trend_table(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_learning(
        tmp_path,
        issue=47,
        title="testing-woes",
        confidence_delta="+1",
        harder="pytest fixtures were harder than expected",
        wrong="assumed mock matched prod",
        rec="pytest coverage improvements next time",
    )
    _write_issue(tmp_path, issue=47, title="testing-woes", slice_=("core",))
    _write_learning(
        tmp_path,
        issue=48,
        title="worktree-isolation",
        confidence_delta="-1",
        harder="worktree isolation was harder than expected",
        wrong="assumed branch was clean",
        rec="use worktree per issue",
    )
    _write_issue(
        tmp_path, issue=48, title="worktree-isolation", slice_=("cli",)
    )

    cli_patterns.run_show_patterns(project_dir=tmp_path)
    captured = capsys.readouterr()

    assert "## Themes" in captured.out
    assert "Testing" in captured.out
    assert "Worktree" in captured.out
    assert "| Slice |" in captured.out


def test_show_patterns_empty_vault_prints_guidance(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / ".mantle" / "learnings").mkdir(parents=True)
    (tmp_path / ".mantle" / "issues").mkdir(parents=True)

    cli_patterns.run_show_patterns(project_dir=tmp_path)
    captured = capsys.readouterr()

    assert "No learnings found" in captured.out


def test_show_patterns_defaults_to_cwd_when_no_project_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / ".mantle" / "learnings").mkdir(parents=True)
    (tmp_path / ".mantle" / "issues").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)

    cli_patterns.run_show_patterns()
    captured = capsys.readouterr()

    assert "No learnings found" in captured.out
