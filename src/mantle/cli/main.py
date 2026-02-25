"""Mantle CLI entry point."""

from pathlib import Path  # noqa: TC003 — needed at runtime for cyclopts
from typing import Annotated

from cyclopts import App, Parameter

from mantle.cli import (
    challenge,
    decisions,
    idea,
    init,
    init_vault,
    install,
    product_design,
    research,
    system_design,
)

app = App(name="mantle", help="AI workflow engine with persistent context.")


@app.command(name="init")
def init_command(
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory to initialize. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Initialize .mantle/ in the current project repository."""
    init.run_init(path)


@app.command(name="init-vault")
def init_vault_command(
    path: Annotated[
        Path,
        Parameter(
            name="--path",
            help="Directory for the personal vault (e.g. ~/vault).",
        ),
    ],
) -> None:
    """Create personal vault and link it to this project."""
    init_vault.run_init_vault(path)


@app.command(name="save-idea")
def save_idea_command(
    problem: Annotated[
        str,
        Parameter(
            name="--problem",
            help="The specific pain or friction that exists.",
        ),
    ],
    insight: Annotated[
        str,
        Parameter(
            name="--insight",
            help="What makes a new solution possible.",
        ),
    ],
    target_user: Annotated[
        str,
        Parameter(
            name="--target-user",
            help="Who this idea is for.",
        ),
    ],
    success_criteria: Annotated[
        tuple[str, ...],
        Parameter(
            name="--success-criteria",
            help="Measurable outcome (repeatable).",
        ),
    ],
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing idea.md.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Capture a structured idea in .mantle/idea.md."""
    idea.run_save_idea(
        problem=problem,
        insight=insight,
        target_user=target_user,
        success_criteria=success_criteria,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-challenge")
def save_challenge_command(
    transcript: Annotated[
        str,
        Parameter(
            name="--transcript",
            help="Full challenge session transcript.",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a challenge session transcript to .mantle/challenges/."""
    challenge.run_save_challenge(
        transcript=transcript,
        project_dir=path,
    )


@app.command(name="save-research")
def save_research_command(
    focus: Annotated[
        str,
        Parameter(
            name="--focus",
            help="Research focus angle.",
        ),
    ],
    confidence: Annotated[
        str,
        Parameter(
            name="--confidence",
            help="Confidence rating (e.g. '7/10').",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Research note content.",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a research note to .mantle/research/."""
    research.run_save_research(
        focus=focus,
        confidence=confidence,
        content=content,
        project_dir=path,
    )


@app.command(name="save-product-design")
def save_product_design_command(
    vision: Annotated[
        str,
        Parameter(
            name="--vision",
            help="One-sentence product vision.",
        ),
    ],
    principles: Annotated[
        tuple[str, ...],
        Parameter(
            name="--principles",
            help="Non-negotiable truth / constraint (repeatable).",
        ),
    ],
    building_blocks: Annotated[
        tuple[str, ...],
        Parameter(
            name="--building-blocks",
            help="Essential primitive (repeatable).",
        ),
    ],
    prior_art: Annotated[
        tuple[str, ...],
        Parameter(
            name="--prior-art",
            help="Existing piece to combine or adopt (repeatable).",
        ),
    ],
    composition: Annotated[
        str,
        Parameter(
            name="--composition",
            help="How the building blocks assemble into a product.",
        ),
    ],
    target_users: Annotated[
        str,
        Parameter(
            name="--target-users",
            help="Specific user profile and context.",
        ),
    ],
    success_metrics: Annotated[
        tuple[str, ...],
        Parameter(
            name="--success-metrics",
            help="Measurable outcome (repeatable).",
        ),
    ],
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing product-design.md.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a product design to .mantle/product-design.md."""
    product_design.run_save_product_design(
        vision=vision,
        principles=principles,
        building_blocks=building_blocks,
        prior_art=prior_art,
        composition=composition,
        target_users=target_users,
        success_metrics=success_metrics,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-system-design")
def save_system_design_command(
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Full system design document body.",
        ),
    ],
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing system-design.md.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a system design document to .mantle/system-design.md."""
    system_design.run_save_system_design(
        content=content,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-decision")
def save_decision_command(
    topic: Annotated[
        str,
        Parameter(
            name="--topic",
            help="Decision topic (used in filename).",
        ),
    ],
    decision: Annotated[
        str,
        Parameter(
            name="--decision",
            help="The decision text.",
        ),
    ],
    alternatives: Annotated[
        tuple[str, ...],
        Parameter(
            name="--alternatives",
            help="Alternative considered (repeatable).",
        ),
    ],
    rationale: Annotated[
        str,
        Parameter(
            name="--rationale",
            help="Why this option was chosen.",
        ),
    ],
    reversal_trigger: Annotated[
        str,
        Parameter(
            name="--reversal-trigger",
            help="What would change this decision.",
        ),
    ],
    confidence: Annotated[
        str,
        Parameter(
            name="--confidence",
            help='Confidence rating (e.g. "8/10").',
        ),
    ],
    reversible: Annotated[
        str,
        Parameter(
            name="--reversible",
            help="Reversibility: high / medium / low.",
        ),
    ],
    scope: Annotated[
        str,
        Parameter(
            name="--scope",
            help="Decision scope.",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a decision record to .mantle/decisions/."""
    decisions.run_save_decision(
        topic=topic,
        decision=decision,
        alternatives=alternatives,
        rationale=rationale,
        reversal_trigger=reversal_trigger,
        confidence=confidence,
        reversible=reversible,
        scope=scope,
        project_dir=path,
    )


@app.command(name="install")
def install_command() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    install.run_install()


if __name__ == "__main__":
    app()
