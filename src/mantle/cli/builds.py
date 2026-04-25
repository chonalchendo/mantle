"""CLI wiring for build-pipeline telemetry commands."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from mantle.core import project, stages, telemetry

console = Console()


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
        session_id = telemetry.current_session_id(project_dir)
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
    its ``session_id``, parses the matching session transcript and
    per-session stage marks, discovers sub-agent JSONLs, and overwrites
    the stub with a full rendered report. If anything required is
    missing (no stub, unset env, missing session file), prints a
    warning and returns without raising.

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

    marks = stages.read_stages(session_id, project_dir)
    parent_turns = telemetry.read_session(session_file)

    # Build windows using the last parent-turn timestamp as session_end
    # (falls back to now(UTC) when the session has zero turns).
    if parent_turns:
        session_end = max(t.timestamp for t in parent_turns)
    else:
        session_end = datetime.now(UTC)
    stage_windows = stages.windows_for_session(marks, session_end)

    subagent_paths = telemetry.find_subagent_files(session_id)

    runs = telemetry.group_stories(
        parent_turns=parent_turns,
        subagent_paths=subagent_paths,
        stage_windows=stage_windows,
    )
    report = telemetry.summarise(session_id, parent_turns, runs)
    report = _augment_with_costs(report, project_dir)
    rendered = telemetry.render_report(report, issue=issue)
    finished = datetime.now(UTC)
    finalized = _finalize_frontmatter(rendered, finished)
    stub_path.write_text(finalized, encoding="utf-8")

    console.print(f"[green]Build finished:[/green] {stub_path}")


# ── Internal helpers ─────────────────────────────────────────────


def _augment_with_costs(
    report: telemetry.BuildReport,
    project_dir: Path,
) -> telemetry.BuildReport:
    """Return a copy of ``report`` with ``cost_usd`` populated per story.

    Reads prices from ``.mantle/cost-policy.md``. If the file or its
    ``prices`` block is missing/invalid, returns the report unchanged
    so the build is never blocked by config issues.
    """
    try:
        prices = project.load_prices(project_dir)
    except FileNotFoundError, KeyError, ValueError:
        return report

    augmented: list[telemetry.StoryRun] = []
    for run in report.stories:
        pricing = project.resolve_pricing(run.model, prices)
        if pricing is None:
            augmented.append(run)
            continue
        u = run.usage
        cost = (
            u.input_tokens * pricing.input
            + u.output_tokens * pricing.output
            + u.cache_read_input_tokens * pricing.cache_read
            + u.cache_creation_input_tokens * pricing.cache_write
        ) / 1_000_000
        augmented.append(run.model_copy(update={"cost_usd": cost}))

    return report.model_copy(update={"stories": tuple(augmented)})


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
