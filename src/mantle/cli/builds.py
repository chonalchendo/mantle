"""CLI wiring for build-pipeline telemetry commands."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from mantle.core import telemetry

console = Console()


_STORY_FILENAME_RE = re.compile(r"issue-\d+-story-(\d+)")


def run_build_start(issue: int, project_dir: Path | None = None) -> None:
    """Record the start of a build run by writing a stub telemetry file.

    Looks up the current Claude Code session id and writes a stub
    file at ``.mantle/builds/build-{issue:02d}-{UTC timestamp}.md``
    with minimal frontmatter. The stub is finalised later by
    :func:`run_build_finish`.

    If ``CLAUDE_SESSION_ID`` is unset (running outside Claude Code),
    prints a warning and returns without creating a stub so that the
    wider pipeline is never blocked.

    Args:
        issue: Issue number being built.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        session_id = telemetry.current_session_id()
    except RuntimeError as exc:
        console.print(
            f"[yellow]Warning:[/yellow] {exc} Build telemetry will be skipped."
        )
        return

    started = datetime.now(UTC)
    stamp = started.strftime("%Y%m%d-%H%M")
    builds_dir = project_dir / ".mantle" / "builds"
    builds_dir.mkdir(parents=True, exist_ok=True)
    stub_path = builds_dir / f"build-{issue:02d}-{stamp}.md"

    body = (
        "---\n"
        f"issue: {issue}\n"
        f"started: {started.isoformat()}\n"
        f"session_id: {session_id}\n"
        "status: in-progress\n"
        "---\n"
    )
    stub_path.write_text(body, encoding="utf-8")

    console.print(f"[green]Build started:[/green] {stub_path.name}")


def run_build_finish(issue: int, project_dir: Path | None = None) -> None:
    """Finalize a build report by parsing the Claude Code session JSONL.

    Locates the most recent in-progress stub for this issue, reads
    its ``session_id``, parses the matching session transcript, and
    overwrites the stub with a full rendered report. If anything
    required is missing (no stub, unset env, missing session file),
    prints a warning and returns without raising.

    Args:
        issue: Issue number being finished.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    builds_dir = project_dir / ".mantle" / "builds"
    stub_path = _find_latest_in_progress_stub(builds_dir, issue)
    if stub_path is None:
        console.print(
            f"[yellow]Warning:[/yellow] No in-progress build stub "
            f"found for issue {issue}. Did build-start run?"
        )
        return

    stub_body = stub_path.read_text(encoding="utf-8")
    session_id = _read_frontmatter_value(stub_body, "session_id")
    if session_id is None:
        console.print(
            f"[yellow]Warning:[/yellow] Stub {stub_path.name} has "
            "no session_id; cannot finalize."
        )
        return

    try:
        session_file = telemetry.find_session_file(session_id)
    except FileNotFoundError as exc:
        console.print(f"[yellow]Warning:[/yellow] {exc} Leaving stub as-is.")
        return

    markers = _derive_mtime_markers(project_dir, issue)
    turns = telemetry.read_session(session_file)
    runs = telemetry.group_stories(turns, markers)
    report = telemetry.summarise(session_id, turns, runs)

    rendered = telemetry.render_report(report, issue=issue, markers=markers)
    finished = datetime.now(UTC)
    finalized = _finalize_frontmatter(rendered, finished)
    stub_path.write_text(finalized, encoding="utf-8")

    console.print(f"[green]Build finished:[/green] {stub_path}")


# ── Internal helpers ─────────────────────────────────────────────


def _find_latest_in_progress_stub(
    builds_dir: Path,
    issue: int,
) -> Path | None:
    """Return the most recent in-progress stub for ``issue``, if any.

    Args:
        builds_dir: The ``.mantle/builds`` directory.
        issue: Issue number.

    Returns:
        Path to the most recent matching stub with
        ``status: in-progress``, or None when no stub exists.
    """
    if not builds_dir.is_dir():
        return None
    candidates = sorted(
        builds_dir.glob(f"build-{issue:02d}-*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        body = path.read_text(encoding="utf-8")
        status = _read_frontmatter_value(body, "status")
        if status == "in-progress":
            return path
    return None


def _read_frontmatter_value(body: str, key: str) -> str | None:
    """Extract a top-level scalar value from a YAML frontmatter block.

    Only the first ``---``-delimited block is inspected. Values are
    returned verbatim with surrounding whitespace stripped. Returns
    None if the key is absent or the body has no frontmatter.

    Args:
        body: Full file body, starting with ``---``.
        key: Frontmatter key to look up.

    Returns:
        The scalar value, or None when not present.
    """
    if not body.startswith("---"):
        return None
    lines = body.splitlines()
    for raw in lines[1:]:
        if raw.strip() == "---":
            break
        if ":" not in raw or raw.startswith(" "):
            continue
        name, _, value = raw.partition(":")
        if name.strip() == key:
            return value.strip()
    return None


def _derive_mtime_markers(
    project_dir: Path,
    issue: int,
) -> tuple[telemetry.Marker, ...]:
    """Derive story markers from ``.mantle/stories/`` file mtimes.

    For each ``issue-{NN}-story-{S}.md`` file, use its mtime as a
    proxy for when the orchestrator spawned the story's agent. This
    is a v1 heuristic but good enough because the orchestrator
    touches each story file via ``update-story-status`` immediately
    before spawning.

    Args:
        project_dir: Project directory.
        issue: Issue number.

    Returns:
        Tuple of Marker records, one per story file found.
    """
    stories_dir = project_dir / ".mantle" / "stories"
    if not stories_dir.is_dir():
        return ()

    markers: list[telemetry.Marker] = []
    for path in sorted(stories_dir.glob(f"issue-{issue:02d}-story-*.md")):
        match = _STORY_FILENAME_RE.search(path.stem)
        if match is None:
            continue
        try:
            story_id = int(match.group(1))
        except ValueError:
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        markers.append(telemetry.Marker(story_id=story_id, timestamp=mtime))
    return tuple(markers)


def _finalize_frontmatter(rendered: str, finished: datetime) -> str:
    """Inject ``finished`` + ``status: complete`` into rendered report.

    The report produced by :func:`telemetry.render_report` already
    contains a frontmatter block; this helper augments it with the
    final-state keys without disturbing the summary section.

    Args:
        rendered: Full rendered build file body.
        finished: Wall-clock time the build completed.

    Returns:
        The body with an additional ``finished`` line and
        ``status: complete`` inserted into the frontmatter.
    """
    lines = rendered.split("\n")
    if not lines or lines[0] != "---":
        return rendered
    try:
        end = next(idx for idx in range(1, len(lines)) if lines[idx] == "---")
    except StopIteration:
        return rendered
    injection = [f"build_finished: {finished.isoformat()}", "status: complete"]
    return "\n".join(lines[:end] + injection + lines[end:])
