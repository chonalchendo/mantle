"""Save-product-design command — capture product design in .mantle/product-design.md."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import product_design

console = Console()


def run_save_product_design(
    *,
    vision: str,
    principles: tuple[str, ...],
    building_blocks: tuple[str, ...],
    prior_art: tuple[str, ...],
    composition: str,
    target_users: str,
    success_metrics: tuple[str, ...],
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Capture a product design and write it to .mantle/product-design.md.

    Args:
        vision: One-sentence product vision.
        principles: Non-negotiable truths that constrain the
            solution space.
        building_blocks: Essential primitives that must be correct.
        prior_art: Existing pieces to combine or adopt.
        composition: How the building blocks assemble into a
            coherent product.
        target_users: Specific user profile and context.
        success_metrics: Measurable outcomes (2-5 items).
        overwrite: Replace existing product-design.md if True.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If product-design.md already exists and
            overwrite is False.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        result = product_design.create_product_design(
            project_dir,
            vision=vision,
            principles=principles,
            building_blocks=building_blocks,
            prior_art=prior_art,
            composition=composition,
            target_users=target_users,
            success_metrics=success_metrics,
            overwrite=overwrite,
        )
    except product_design.ProductDesignExistsError:
        console.print(
            "[yellow]Warning:[/yellow] product-design.md"
            " already exists. Use --overwrite to replace."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(
        "[green]Product design saved to .mantle/product-design.md[/green]"
    )
    console.print()
    console.print(f"  Vision:          {result.vision}")
    console.print(f"  Building blocks: {len(result.building_blocks)}")
    console.print()
    console.print(
        "  Next: run [bold]/mantle:design-system[/bold] to define the how"
    )


def run_revise_product_design(
    *,
    vision: str,
    principles: tuple[str, ...],
    building_blocks: tuple[str, ...],
    prior_art: tuple[str, ...],
    composition: str,
    target_users: str,
    success_metrics: tuple[str, ...],
    change_topic: str,
    change_summary: str,
    change_rationale: str,
    project_dir: Path | None = None,
) -> None:
    """Revise product design and print confirmation.

    Args:
        vision: Updated product vision.
        principles: Updated non-negotiable truths.
        building_blocks: Updated essential primitives.
        prior_art: Updated existing pieces to adopt.
        composition: Updated assembly description.
        target_users: Updated user profile.
        success_metrics: Updated measurable outcomes.
        change_topic: Short slug for the decision log.
        change_summary: What changed.
        change_rationale: Why it changed.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If product-design.md does not exist.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        _, decision_path = product_design.update_product_design(
            project_dir,
            vision=vision,
            principles=principles,
            building_blocks=building_blocks,
            prior_art=prior_art,
            composition=composition,
            target_users=target_users,
            success_metrics=success_metrics,
            change_topic=change_topic,
            change_summary=change_summary,
            change_rationale=change_rationale,
        )
    except FileNotFoundError:
        console.print(
            "[yellow]Warning:[/yellow]"
            " product-design.md does not exist."
            " Run /mantle:design-product first."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(
        "[green]Product design revised in .mantle/product-design.md[/green]"
    )
    console.print()
    console.print(f"  Change:   {change_topic}")
    console.print(f"  Decision: {decision_path.name}")
    console.print()
    console.print("  Next: review the revision in .mantle/product-design.md")
