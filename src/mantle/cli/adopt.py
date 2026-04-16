"""Save-adoption command — write adopted design artifacts to .mantle/."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import adopt
from mantle.core.state import InvalidTransitionError

console = Console()


def run_save_adoption(
    *,
    vision: str,
    principles: tuple[str, ...],
    building_blocks: tuple[str, ...],
    prior_art: tuple[str, ...],
    composition: str,
    target_users: str,
    success_metrics: tuple[str, ...],
    system_design_content: str,
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Save adoption artifacts and print confirmation.

    Args:
        vision: One-sentence product vision.
        principles: Non-negotiable truths from the codebase.
        building_blocks: Irreducible primitives the project
            depends on.
        prior_art: Dependencies and ecosystem tools in use.
        composition: How the building blocks assemble.
        target_users: Inferred user profile.
        success_metrics: Measurable outcomes.
        system_design_content: Full system design markdown body.
        overwrite: Replace existing docs if True.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If design docs exist without overwrite, or
            if state transition is invalid.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        pd_note, _ = adopt.save_adoption(
            project_dir,
            vision=vision,
            principles=principles,
            building_blocks=building_blocks,
            prior_art=prior_art,
            composition=composition,
            target_users=target_users,
            success_metrics=success_metrics,
            system_design_content=system_design_content,
            overwrite=overwrite,
        )
    except adopt.AdoptionExistsError:
        console.print(
            "[yellow]Warning:[/yellow] design documents"
            " already exist. Use --overwrite to replace."
        )
        raise SystemExit(1) from None
    except InvalidTransitionError as exc:
        errors.exit_with_error(
            (
                f"project is at '{exc.current.value}'"
                f" — adoption requires 'idea' status."
            ),
            hint=(
                "Back up .mantle/ and re-run 'mantle init'"
                " if you want to restart"
            ),
        )

    console.print()
    console.print(
        "[green]Adoption complete — design artifacts saved to .mantle/[/green]"
    )
    console.print()
    console.print(f"  Vision:          {pd_note.vision}")
    console.print(
        f"  Features:        {len(pd_note.building_blocks)} building blocks"
    )
    console.print("  System design:   saved")
    console.print()
    console.print(
        "  Next: run [bold]/mantle:plan-issues[/bold] to break down the work"
    )
