"""CLI wiring for the A/B build-comparison command."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from mantle.core import ab_build, issues, project, stages, stories, telemetry

console = Console()


def run_ab_build_compare(
    baseline: Path,
    candidate: Path,
    *,
    output: Path | None = None,
    project_dir: Path | None = None,
) -> None:
    """Load two build files, reconstruct artefacts, and print an A/B report.

    For each build file, reads the ``session_id`` from frontmatter, locates
    the matching Claude Code session JSONL, reconstructs per-stage
    :class:`telemetry.StoryRun` records, and assembles a
    :class:`ab_build.BuildArtefacts` value.  Then calls
    :func:`ab_build.build_comparison` and :func:`ab_build.render_markdown` to
    produce the comparison report.

    Degrades gracefully on several missing-data conditions:

    - Missing ``session_id`` frontmatter → prints red ``Error:`` and returns.
    - Missing session JSONL → prints yellow ``Warning:`` and continues with an
      empty report (zero-filled rows).
    - Missing ``prices:`` block in cost-policy.md → prints red ``Error:`` and
      returns without writing.
    - Missing issue note or stories → passes ``None`` / ``()`` into
      :class:`ab_build.BuildArtefacts`; the harness tolerates this.

    Args:
        baseline: Path to the baseline build report ``.md`` file.
        candidate: Path to the candidate build report ``.md`` file.
        output: Optional path to write the rendered report. When ``None``,
            the report is printed to stdout via Rich.
        project_dir: Project directory containing ``.mantle/``. Defaults
            to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    baseline_art = _load_build_artefacts(baseline, project_dir)
    if baseline_art is None:
        return

    candidate_art = _load_build_artefacts(candidate, project_dir)
    if candidate_art is None:
        return

    try:
        prices = project.load_prices(project_dir)
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] .mantle/cost-policy.md not found. "
            "Cannot compute prices."
        )
        return
    except KeyError:
        console.print(
            "[red]Error:[/red] cost-policy.md has no 'prices' block. "
            "Cannot compute prices."
        )
        return

    comparison = ab_build.build_comparison(baseline_art, candidate_art, prices)
    rendered = ab_build.render_markdown(comparison)

    if output is not None:
        output.write_text(rendered, encoding="utf-8")
        console.print(f"[green]Report written:[/green] {output}")
    else:
        console.print(rendered)


# ── Internal helpers ─────────────────────────────────────────────


def _load_build_artefacts(
    build_file: Path,
    project_dir: Path,
) -> ab_build.BuildArtefacts | None:
    """Parse one build file into a :class:`ab_build.BuildArtefacts`.

    Reads frontmatter, resolves session JSONL, reconstructs stage runs,
    and loads any available issue/story notes.  Returns ``None`` only when
    ``session_id`` is absent from frontmatter (hard error condition).

    Args:
        build_file: Path to the build report ``.md`` file.
        project_dir: Project directory containing ``.mantle/``.

    Returns:
        Populated :class:`ab_build.BuildArtefacts`, or ``None`` when a
        hard error prevents reconstruction.
    """
    frontmatter, _ = project.read_frontmatter_and_body(build_file)

    session_id: str | None = frontmatter.get("session_id")
    if not session_id:
        console.print(
            f"[red]Error:[/red] {build_file} has no session_id in frontmatter"
        )
        return None

    raw_issue = frontmatter.get("issue")
    issue_number: int | None = int(raw_issue) if raw_issue is not None else None

    # Resolve session JSONL — degrade gracefully on missing file
    parent_turns: tuple[telemetry.Turn, ...] = ()
    subagent_paths: tuple[Path, ...] = ()
    stage_windows: tuple[stages.StageWindow, ...] = ()

    try:
        session_file = telemetry.find_session_file(session_id)
        parent_turns = telemetry.read_session(session_file)

        if parent_turns:
            session_end = max(t.timestamp for t in parent_turns)
        else:
            session_end = datetime.now(UTC)

        marks = stages.read_stages(session_id, project_dir)
        stage_windows = stages.windows_for_session(marks, session_end)
        subagent_paths = telemetry.find_subagent_files(session_id)

    except FileNotFoundError as exc:
        console.print(
            f"[yellow]Warning:[/yellow] {exc} "
            "Continuing with empty session data."
        )

    runs = telemetry.group_stories(
        parent_turns=parent_turns,
        subagent_paths=subagent_paths,
        stage_windows=stage_windows,
    )
    report = telemetry.summarise(session_id, parent_turns, runs)

    # Load quality data — tolerate missing files
    issue_note: issues.IssueNote | None = None
    story_notes: list[stories.StoryNote] = []

    if issue_number is not None:
        issue_path = issues.find_issue_path(project_dir, issue_number)
        if issue_path is not None:
            with contextlib.suppress(FileNotFoundError):
                issue_note, _ = issues.load_issue(issue_path)

        with contextlib.suppress(FileNotFoundError):
            story_paths = stories.list_stories(project_dir, issue=issue_number)
            for sp in story_paths:
                with contextlib.suppress(FileNotFoundError):
                    note, _ = stories.load_story(sp)
                    story_notes.append(note)

    return ab_build.BuildArtefacts(
        label=build_file.stem,
        issue=issue_number,
        report=report,
        issue_note=issue_note,
        stories=tuple(story_notes),
    )
