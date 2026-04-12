"""Tests for mantle.core.patterns."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from mantle.core import learning, patterns
from mantle.core.patterns import (
    PatternHit,
    _confidence_by_slice,
    _split_sections,
    _theme_for,
    analyze_patterns,
    render_report,
)

if TYPE_CHECKING:
    from pathlib import Path


# ── Fixtures ─────────────────────────────────────────────────────


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
    title: str = "Something",
    confidence_delta: str = "+1",
    harder: str = "Testing was harder than expected",
    wrong: str = "Assumed scope was small",
    rec: str = "Add more test coverage next time",
) -> None:
    """Write a synthetic learning file under .mantle/learnings/."""
    learnings_dir = project_dir / ".mantle" / "learnings"
    learnings_dir.mkdir(parents=True, exist_ok=True)
    slug = title.lower().replace(" ", "-")
    path = learnings_dir / f"issue-{issue:02d}-{slug}.md"
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
    title: str = "Something",
    slice_: tuple[str, ...] = ("core",),
) -> None:
    """Write a synthetic issue file under .mantle/issues/."""
    issues_dir = project_dir / ".mantle" / "issues"
    issues_dir.mkdir(parents=True, exist_ok=True)
    slug = title.lower().replace(" ", "-")
    path = issues_dir / f"issue-{issue:02d}-{slug}.md"
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


# ── analyze_patterns ─────────────────────────────────────────────


def test_analyze_patterns_empty_vault_returns_zero_learnings(
    tmp_path: Path,
) -> None:
    (tmp_path / ".mantle" / "learnings").mkdir(parents=True)
    (tmp_path / ".mantle" / "issues").mkdir(parents=True)

    report = analyze_patterns(tmp_path)

    assert report.total_learnings == 0
    assert report.themes == {}
    assert report.slice_stats == ()


def test_split_sections_extracts_bullets_under_canonical_headings() -> None:
    body = (
        "## What went well\n\n"
        "- A\n"
        "- B\n\n"
        "## Harder than expected\n\n"
        "- harder1\n"
        "- harder2\n\n"
        "## Wrong assumptions\n\n"
        "- wrong1\n\n"
        "## Recommendations\n\n"
        "- rec1\n"
    )
    sections = _split_sections(body)

    assert sections["went_well"] == ["A", "B"]
    assert sections["harder"] == ["harder1", "harder2"]
    assert sections["wrong_assumptions"] == ["wrong1"]
    assert sections["recommendations"] == ["rec1"]


def test_split_sections_ignores_unknown_headings() -> None:
    body = (
        "## What went well\n\n"
        "- Good\n\n"
        "## Unknown section\n\n"
        "- Ignored\n\n"
        "## Harder than expected\n\n"
        "- harder1\n"
    )
    sections = _split_sections(body)
    assert "unknown" not in sections
    assert sections["went_well"] == ["Good"]
    assert sections["harder"] == ["harder1"]


def test_theme_for_buckets_testing_keywords() -> None:
    assert _theme_for("The tests were flaky") == "testing"
    assert _theme_for("pytest fixtures broke") == "testing"
    assert _theme_for("mock did not match prod") == "testing"


def test_theme_for_falls_back_to_other() -> None:
    assert _theme_for("Something completely unrelated") == "other"


def test_analyze_patterns_buckets_across_multiple_learnings(
    tmp_path: Path,
) -> None:
    _write_learning(
        tmp_path,
        issue=47,
        title="testing-woes",
        confidence_delta="+1",
        harder="pytest fixtures were harder than expected",
        wrong="Assumed mock matched prod",
        rec="Use real database in tests",
    )
    _write_issue(tmp_path, issue=47, title="testing-woes")

    _write_learning(
        tmp_path,
        issue=48,
        title="worktree-isolation",
        confidence_delta="-1",
        harder="Branch isolation was harder than expected",
        wrong="Assumed merge would be clean",
        rec="Always use a worktree per issue",
    )
    _write_issue(tmp_path, issue=48, title="worktree-isolation")

    report = analyze_patterns(tmp_path)

    assert report.total_learnings == 2
    assert "testing" in report.themes
    assert "worktree" in report.themes
    testing_hits = report.themes["testing"]
    assert all(isinstance(h, PatternHit) for h in testing_hits)
    assert any(h.issue == 47 for h in testing_hits)


def test_analyze_patterns_drops_went_well_section(tmp_path: Path) -> None:
    _write_learning(
        tmp_path,
        issue=10,
        title="a",
        harder="testing was bad",
        wrong="assumed scope was small",
        rec="pytest more",
    )
    _write_issue(tmp_path, issue=10, title="a")

    report = analyze_patterns(tmp_path)

    for hits in report.themes.values():
        for hit in hits:
            assert hit.section in {
                "harder",
                "wrong_assumptions",
                "recommendations",
            }


def test_confidence_by_slice_averages_per_slice() -> None:
    n1 = learning.LearningNote(
        issue=1,
        title="a",
        author="x",
        date=date(2026, 1, 1),
        confidence_delta="+2",
    )
    n2 = learning.LearningNote(
        issue=2,
        title="b",
        author="x",
        date=date(2026, 1, 1),
        confidence_delta="-1",
    )
    n3 = learning.LearningNote(
        issue=3,
        title="c",
        author="x",
        date=date(2026, 1, 1),
        confidence_delta="+1",
    )
    stats = _confidence_by_slice(
        [
            (n1, ("core",)),
            (n2, ("core",)),
            (n3, ("cli",)),
        ]
    )

    by_slice = {s.slice: s for s in stats}
    assert by_slice["core"].count == 2
    assert by_slice["core"].avg_delta == 0.5
    assert by_slice["cli"].count == 1
    assert by_slice["cli"].avg_delta == 1.0
    # Sorted ascending by avg_delta, tie by slice name.
    assert stats[0].slice == "core"
    assert stats[1].slice == "cli"


def test_confidence_by_slice_ignores_unmatched_issue(tmp_path: Path) -> None:
    # Learning exists but issue file does not — caller filters upstream.
    _write_learning(
        tmp_path,
        issue=99,
        title="orphan",
        confidence_delta="+3",
    )
    # Intentionally: no issue file at issue-99.
    (tmp_path / ".mantle" / "issues").mkdir(parents=True, exist_ok=True)

    report = analyze_patterns(tmp_path)

    assert report.total_learnings == 1
    # Orphan learning has no slice, so slice_stats should exclude it.
    assert report.slice_stats == ()


def test_render_report_produces_markdown_with_themes_and_trend_table(
    tmp_path: Path,
) -> None:
    _write_learning(
        tmp_path,
        issue=47,
        title="testing-woes",
        confidence_delta="+1",
        harder="pytest fixtures broke",
        wrong="Assumed mock matched prod",
        rec="Use real database",
    )
    _write_issue(tmp_path, issue=47, title="testing-woes", slice_=("core",))
    _write_learning(
        tmp_path,
        issue=48,
        title="cli-trouble",
        confidence_delta="-1",
        harder="worktree merge was harder",
        wrong="Assumed branch was clean",
        rec="Use worktree isolation",
    )
    _write_issue(tmp_path, issue=48, title="cli-trouble", slice_=("cli",))

    report = analyze_patterns(tmp_path)
    rendered = render_report(report)

    assert "# Recurring Patterns" in rendered
    assert "Based on 2 learnings" in rendered
    assert "## Themes" in rendered
    # Testing theme title-cased
    assert "### Testing" in rendered
    # Worktree theme title-cased
    assert "### Worktree" in rendered
    assert "## Confidence trend by slice" in rendered
    assert "| Slice | Learnings | Avg Δ confidence |" in rendered
    # core has +1 delta, cli has -1 delta — sorted ascending by delta.
    cli_idx = rendered.find("| cli |")
    core_idx = rendered.find("| core |")
    assert cli_idx < core_idx
    assert "-1.0" in rendered
    assert "+1.0" in rendered


def test_render_report_empty_learnings_returns_guidance_message() -> None:
    report = patterns.PatternReport(
        total_learnings=0,
        themes={},
        slice_stats=(),
    )
    rendered = render_report(report)
    assert rendered == (
        "No learnings found — run /mantle:retrospective after an issue"
        " to start capturing patterns.\n"
    )
