"""CLI wrappers for issue planning operations."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from mantle.cli import errors
from mantle.core import acceptance, issues, state

console = Console()


def run_save_issue(
    *,
    title: str,
    slice: tuple[str, ...],
    content: str,
    blocked_by: tuple[int, ...] = (),
    skills_required: tuple[str, ...] = (),
    verification: str | None = None,
    issue: int | None = None,
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Save issue, print confirmation, suggest next step.

    Args:
        title: Short title for the issue.
        slice: Architectural layers this issue touches.
        content: Full issue body (markdown).
        blocked_by: Issue numbers this issue depends on.
        skills_required: Skill names required to work on this issue.
        verification: Optional per-issue verification override.
        issue: Explicit issue number (for overwrites).
        overwrite: Replace existing issue file.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If issue already exists or transition is invalid.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = issues.save_issue(
            project_dir,
            content,
            title=title,
            slice=slice,
            blocked_by=blocked_by,
            skills_required=skills_required,
            verification=verification,
            issue=issue,
            overwrite=overwrite,
        )
    except issues.IssueExistsError:
        console.print(
            "[yellow]Warning:[/yellow] Issue already"
            " exists. Use --overwrite to replace."
        )
        raise SystemExit(1) from None
    except state.InvalidTransitionError as exc:
        errors.exit_with_error(
            f"Cannot plan issues from '{exc.current.value}' status.",
            hint="Run 'mantle design-product' first",
        )

    console.print()
    console.print(f"[green]Saved {path.name} to .mantle/issues/[/green]")
    console.print(f"  Title: {note.title}")
    console.print(f"  Slice: {', '.join(note.slice)}")
    if note.blocked_by:
        refs = ", ".join(f"issue-{n:02d}" for n in note.blocked_by)
        console.print(f"  Blocked by: {refs}")
    console.print(
        "  Next: run [bold]/mantle:build[/bold] to automate the full"
        " pipeline, [bold]/mantle:shape-issue[/bold] for manual control,"
        " or [bold]/mantle:plan-issues[/bold] for the next issue"
    )


def run_set_slices(
    *,
    slices: tuple[str, ...],
    project_dir: Path | None = None,
) -> None:
    """Set project architectural slices, print confirmation.

    Args:
        slices: Architectural layer names.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    state.update_slices(project_dir, slices)

    console.print()
    console.print(f"[green]Project slices defined ({len(slices)}):[/green]")
    console.print(f"  {', '.join(slices)}")


def run_flip_ac(
    *,
    issue: int,
    ac_id: str,
    passes: bool = True,
    waive: bool = False,
    reason: str | None = None,
    project_dir: Path | None = None,
) -> None:
    """Flip one acceptance criterion to pass/fail or waive it.

    ``--pass`` / ``--fail`` are mutually exclusive with ``--waive``. When
    ``--waive`` is set, ``passes`` stays False but the approval gate
    treats the criterion as resolved.

    Args:
        issue: Issue number to update.
        ac_id: Criterion id (e.g. ``ac-01``).
        passes: New passes value; only honoured when ``waive`` is False.
        waive: Set to True to waive the criterion.
        reason: Required waiver reason when ``waive`` is True.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: On validation failure or unknown criterion id.
    """
    if project_dir is None:
        project_dir = Path.cwd()
    if waive and reason is None:
        errors.exit_with_error(
            "--waive requires --reason",
            hint="Re-run with --reason '<why this is waived>'",
        )

    try:
        updated = issues.flip_acceptance_criterion(
            project_dir,
            issue,
            ac_id,
            passes=passes and not waive,
            waived=waive,
            waiver_reason=reason,
        )
    except acceptance.CriterionNotFoundError as exc:
        errors.exit_with_error(
            str(exc),
            hint="Run `mantle list-acs --issue <N>` to see valid ids.",
        )
    except FileNotFoundError as exc:
        errors.exit_with_error(
            str(exc),
            hint="Check the issue number and try again.",
        )

    match = next(
        (c for c in updated.acceptance_criteria if c.id == ac_id),
        None,
    )
    if match is not None and match.waived:
        state_label = "waived"
    elif match is not None and match.passes:
        state_label = "pass"
    else:
        state_label = "fail"
    console.print(f"[green]issue-{issue:02d}[/green] {ac_id} → {state_label}")


def run_list_acs(
    *,
    issue: int,
    json_output: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Print an issue's acceptance criteria as a table or JSON.

    Claude prompts invoke this with ``--json`` to parse structured
    output; humans see a table.

    Args:
        issue: Issue number to inspect.
        json_output: If True, print a JSON array to stdout.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If the issue cannot be found.
    """
    if project_dir is None:
        project_dir = Path.cwd()
    issue_path = issues.find_issue_path(project_dir, issue)
    if issue_path is None:
        errors.exit_with_error(
            f"Issue {issue} not found",
            hint="Check the issue number and try again.",
        )
    note, _ = issues.load_issue(issue_path)

    if json_output:
        payload = [c.model_dump(mode="json") for c in note.acceptance_criteria]
        console.print_json(data=payload)
        return

    table = Table(title=f"Issue {issue} acceptance criteria")
    table.add_column("id")
    table.add_column("state")
    table.add_column("text")
    for c in note.acceptance_criteria:
        if c.waived:
            state_label = "waived"
        elif c.passes:
            state_label = "pass"
        else:
            state_label = "fail"
        table.add_row(c.id, state_label, c.text)
    console.print(table)


def run_migrate_acs(
    *,
    dry_run: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Backfill markdown-checkbox ACs into structured frontmatter.

    Scans ``.mantle/issues/`` and ``.mantle/archive/issues/``. Issues
    that already have structured ACs are skipped.

    Args:
        dry_run: When True, report would-be migrations without writing.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    if dry_run:
        paths = issues.list_issues(project_dir) + issues.list_archived_issues(
            project_dir
        )
        console.print("[bold]dry-run — no writes[/bold]")
        for path in paths:
            note, body = issues.load_issue(path)
            if note.acceptance_criteria:
                continue
            parsed = acceptance.parse_ac_section(body)
            if parsed:
                console.print(
                    f"would migrate {path.name}: {len(parsed)} criteria"
                )
        return

    results = issues.migrate_all_acs(project_dir)
    if not results:
        console.print("[yellow]No issues needed migration.[/yellow]")
        return
    for number, count in results:
        console.print(f"migrated issue-{number:02d}: {count} criteria")
    console.print(f"[green]Migrated {len(results)} issue(s).[/green]")
