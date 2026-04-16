"""Pattern analysis over accumulated learning notes."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pydantic

from mantle.core import issues, learning

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class PatternHit(pydantic.BaseModel, frozen=True):
    """A single bullet from a learning note bucketed into a theme.

    Attributes:
        issue: Issue number the learning belongs to.
        section: Source section name (``harder``,
            ``wrong_assumptions``, ``recommendations``).
        text: The bullet text, trimmed.
    """

    issue: int
    section: str
    text: str


class SliceStat(pydantic.BaseModel, frozen=True):
    """Aggregate confidence statistics for a single slice.

    Attributes:
        slice: Slice name (e.g. ``core``, ``cli``).
        count: Number of learnings matched to this slice.
        avg_delta: Average ``confidence_delta`` across matched
            learnings.
    """

    slice: str
    count: int
    avg_delta: float


class PatternReport(pydantic.BaseModel, frozen=True):
    """Result of analyzing learnings across a project.

    Attributes:
        total_learnings: Count of learning files scanned.
        themes: Map of theme name to ordered ``PatternHit`` tuple.
        slice_stats: Per-slice confidence stats ordered ascending.
    """

    total_learnings: int
    themes: dict[str, tuple[PatternHit, ...]]
    slice_stats: tuple[SliceStat, ...]


# ── Public API ───────────────────────────────────────────────────


def analyze_patterns(project_dir: Path) -> PatternReport:
    """Scan ``.mantle/learnings/`` and return a grouped pattern report.

    Loads every learning, joins against issue metadata by issue
    number, buckets bullets into themes, and computes per-slice
    confidence averages.

    Args:
        project_dir: Directory containing ``.mantle/``.

    Returns:
        ``PatternReport`` summarising themes and slice trends.
    """
    paths = learning.list_learnings(project_dir)

    loaded: list[tuple[learning.LearningNote, str]] = []
    for path in paths:
        note, body = learning.load_learning(path)
        loaded.append((note, body))

    total = len(loaded)
    themes = _bucket_by_theme(loaded)

    issue_slices = _issue_slice_map(project_dir)
    notes_with_slices: list[tuple[learning.LearningNote, tuple[str, ...]]] = []
    for note, _ in loaded:
        slices = issue_slices.get(note.issue)
        if slices is None:
            continue
        notes_with_slices.append((note, slices))

    slice_stats = _confidence_by_slice(notes_with_slices)

    return PatternReport(
        total_learnings=total,
        themes=themes,
        slice_stats=slice_stats,
    )


def render_report(report: PatternReport) -> str:
    """Render a ``PatternReport`` as deterministic markdown.

    Args:
        report: Report produced by :func:`analyze_patterns`.

    Returns:
        Markdown string. When ``report.total_learnings`` is zero the
        returned text is a short guidance message.
    """
    if report.total_learnings == 0:
        return (
            "No learnings found — run /mantle:retrospective after an"
            " issue to start capturing patterns.\n"
        )

    lines: list[str] = []
    lines.append("# Recurring Patterns")
    lines.append("")
    lines.append(f"Based on {report.total_learnings} learnings.")
    lines.append("")
    lines.append("## Themes")
    lines.append("")

    for theme in (*_THEME_ORDER, "other"):
        hits = report.themes.get(theme)
        if not hits:
            continue
        display = "CI" if theme == "ci" else theme.title()
        lines.append(f"### {display} ({len(hits)} hits)")
        for hit in hits:
            section_label = _SECTION_LABEL[hit.section]
            lines.append(f"- issue {hit.issue} ({section_label}): {hit.text}")
        lines.append("")

    lines.append("## Confidence trend by slice")
    lines.append("")
    lines.append("| Slice | Learnings | Avg Δ confidence |")
    lines.append("| --- | ---: | ---: |")
    for stat in report.slice_stats:
        lines.append(f"| {stat.slice} | {stat.count} | {stat.avg_delta:+.1f} |")
    lines.append("")
    lines.append("_Slices with no matched issue are omitted._")
    lines.append("")

    return "\n".join(lines)


# ── Internal helpers ─────────────────────────────────────────────


_SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "went_well": re.compile(r"^##\s+what\s+went\s+well\s*$", re.IGNORECASE),
    "harder": re.compile(r"^##\s+harder\s+than\s+expected\s*$", re.IGNORECASE),
    "wrong_assumptions": re.compile(
        r"^##\s+wrong\s+assumptions\s*$", re.IGNORECASE
    ),
    "recommendations": re.compile(r"^##\s+recommendations\s*$", re.IGNORECASE),
}


_THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "testing": ("test", "pytest", "fixture", "mock", "coverage"),
    "estimation": (
        "estimat",
        "appetite",
        "took longer",
        "underestim",
        "overestim",
    ),
    "scope": ("scope", "out of scope", "out-of-scope"),
    "tooling": (
        "cli",
        " uv ",
        " just ",
        "prek",
        "installed",
        "command not found",
    ),
    "shaping": ("shape", "approach", "rabbit hole", "tradeoff"),
    "worktree": ("worktree", "isolation", "merge", "branch"),
    "ci": (" ci ", "github action", "workflow", "publish"),
    "skills": ("skill", "vault"),
}


_THEME_ORDER: tuple[str, ...] = tuple(_THEME_KEYWORDS.keys())


_SECTION_LABEL: dict[str, str] = {
    "harder": "harder",
    "wrong_assumptions": "wrong",
    "recommendations": "rec",
}


_BUCKET_SECTIONS: tuple[str, ...] = (
    "harder",
    "wrong_assumptions",
    "recommendations",
)


def _split_sections(body: str) -> dict[str, list[str]]:
    """Split a retrospective body into canonical section buckets.

    Parses ``##``-level headings matching the retrospective template
    and collects bullet lines (``- ...``) beneath each. Continuation
    lines for a bullet are joined into the parent bullet. Unknown
    headings are dropped silently.

    Args:
        body: Markdown body of a learning note.

    Returns:
        Mapping from canonical section name to ordered bullets.
    """
    sections: dict[str, list[str]] = {}
    current: str | None = None
    current_bullets: list[str] = []
    pending: list[str] = []

    def flush_pending() -> None:
        if pending and current is not None:
            current_bullets.append(" ".join(pending).strip())
            pending.clear()

    def flush_current() -> None:
        flush_pending()
        if current is not None:
            sections[current] = list(current_bullets)

    for raw_line in body.splitlines():
        stripped = raw_line.strip()

        matched_section = _match_section(raw_line)
        if matched_section is not None:
            flush_current()
            current = matched_section
            current_bullets = []
            continue

        # Heading we don't recognise ends the current section.
        if stripped.startswith("##"):
            flush_current()
            current = None
            current_bullets = []
            continue

        if current is None:
            continue

        if stripped.startswith("- "):
            flush_pending()
            pending.append(stripped[2:].strip())
        elif stripped == "":
            flush_pending()
        elif pending:
            pending.append(stripped)

    flush_current()
    return sections


def _match_section(line: str) -> str | None:
    """Return the canonical section name for a heading line, or ``None``."""
    candidate = line.strip()
    for name, pattern in _SECTION_PATTERNS.items():
        if pattern.match(candidate):
            return name
    return None


def _theme_for(text: str) -> str:
    """Classify a bullet into a theme by keyword match, or ``"other"``."""
    haystack = f" {text.lower()} "
    for theme, keywords in _THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in haystack:
                return theme
    return "other"


def _bucket_by_theme(
    learnings: Iterable[tuple[learning.LearningNote, str]],
) -> dict[str, tuple[PatternHit, ...]]:
    """Group bullets from learnings into theme buckets, sorted by (issue, section, text)."""
    buckets: dict[str, list[PatternHit]] = {}

    for note, body in learnings:
        sections = _split_sections(body)
        for section in _BUCKET_SECTIONS:
            for bullet in sections.get(section, []):
                hit = PatternHit(
                    issue=note.issue,
                    section=section,
                    text=bullet,
                )
                theme = _theme_for(bullet)
                buckets.setdefault(theme, []).append(hit)

    return {
        theme: tuple(sorted(hits, key=lambda h: (h.issue, h.section, h.text)))
        for theme, hits in buckets.items()
    }


def _confidence_by_slice(
    notes_with_slices: Iterable[tuple[learning.LearningNote, tuple[str, ...]]],
) -> tuple[SliceStat, ...]:
    """Compute average confidence delta per slice, sorted ascending by avg_delta."""
    totals: dict[str, list[int]] = {}
    for note, slices in notes_with_slices:
        delta = int(note.confidence_delta)
        for slice_name in slices:
            totals.setdefault(slice_name, []).append(delta)

    stats = [
        SliceStat(
            slice=slice_name,
            count=len(deltas),
            avg_delta=sum(deltas) / len(deltas),
        )
        for slice_name, deltas in totals.items()
    ]
    stats.sort(key=lambda s: (s.avg_delta, s.slice))
    return tuple(stats)


def _issue_slice_map(project_dir: Path) -> dict[int, tuple[str, ...]]:
    """Return a mapping from issue number to slice tuple.

    Scans both live and archived issues so confidence trends cover the
    full project history, not just issues still in ``issues/``. Live
    entries win on collisions.
    """
    pattern = re.compile(r"issue-(\d+)(?:-.*)?\.md")
    mapping: dict[int, tuple[str, ...]] = {}
    paths = list(issues.list_archived_issues(project_dir))
    paths += list(issues.list_issues(project_dir))
    for path in paths:
        match = pattern.match(path.name)
        if match is None:
            continue
        number = int(match.group(1))
        note, _ = issues.load_issue(path)
        mapping[number] = note.slice
    return mapping
