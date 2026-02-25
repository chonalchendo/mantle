"""Save-product-design command — capture product design in .mantle/product-design.md."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import product_design

console = Console()


def run_save_product_design(
    *,
    vision: str,
    features: tuple[str, ...],
    target_users: str,
    success_metrics: tuple[str, ...],
    genuine_edge: str,
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Capture a product design and write it to .mantle/product-design.md.

    Args:
        vision: One-sentence product vision.
        features: Key capabilities (3-7 items).
        target_users: Specific user profile and context.
        success_metrics: Measurable outcomes (2-5 items).
        genuine_edge: What makes this different from alternatives.
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
            features=features,
            target_users=target_users,
            success_metrics=success_metrics,
            genuine_edge=genuine_edge,
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
    console.print(f"  Vision:   {result.vision}")
    console.print(f"  Features: {len(result.features)}")
    console.print()
    console.print(
        "  Next: run [bold]/mantle:design-system[/bold] to define the how"
    )
