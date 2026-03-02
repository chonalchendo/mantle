"""Project adoption — reverse-engineer design artifacts from existing codebases."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

from mantle.core import product_design, state, vault
from mantle.core.product_design import ProductDesignNote
from mantle.core.system_design import SystemDesignNote

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


# ── Exception ────────────────────────────────────────────────────


class AdoptionExistsError(Exception):
    """Raised when design docs already exist and overwrite is False.

    Attributes:
        path: Path to the first conflicting file found.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Design documents already exist: {path}")


# ── Public API ───────────────────────────────────────────────────


def save_adoption(
    project_dir: Path,
    *,
    vision: str,
    principles: Sequence[str],
    building_blocks: Sequence[str],
    prior_art: Sequence[str],
    composition: str,
    target_users: str,
    success_metrics: Sequence[str],
    system_design_content: str,
    overwrite: bool = False,
) -> tuple[ProductDesignNote, SystemDesignNote]:
    """Write both design documents and transition to ADOPTED.

    Checks for existing docs first, transitions state (fail fast),
    then writes product-design.md and system-design.md.

    Args:
        project_dir: Directory containing .mantle/.
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

    Returns:
        Tuple of (ProductDesignNote, SystemDesignNote).

    Raises:
        AdoptionExistsError: If design docs exist and overwrite
            is False.
        InvalidTransitionError: If state is not IDEA.
    """
    pd_path = project_dir / ".mantle" / "product-design.md"
    sd_path = project_dir / ".mantle" / "system-design.md"

    if not overwrite:
        if pd_path.exists():
            raise AdoptionExistsError(pd_path)
        if sd_path.exists():
            raise AdoptionExistsError(sd_path)

    # Fail fast: validate transition before writing files
    state.transition(project_dir, state.Status.ADOPTED)

    identity = state.resolve_git_identity()
    today = date.today()

    pd_note = ProductDesignNote(
        vision=vision,
        principles=tuple(principles),
        building_blocks=tuple(building_blocks),
        prior_art=tuple(prior_art),
        composition=composition,
        target_users=target_users,
        success_metrics=tuple(success_metrics),
        author=identity,
        created=today,
        updated=today,
        updated_by=identity,
    )
    vault.write_note(
        pd_path,
        pd_note,
        product_design._build_product_design_body(pd_note),
    )

    sd_note = SystemDesignNote(
        author=identity,
        created=today,
        updated=today,
        updated_by=identity,
    )
    vault.write_note(sd_path, sd_note, system_design_content)

    _update_state_body(project_dir, identity)

    return pd_note, sd_note


def adoption_exists(project_dir: Path) -> bool:
    """Check whether adoption design docs already exist.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        True if either product-design.md or system-design.md
        exists.
    """
    pd = project_dir / ".mantle" / "product-design.md"
    sd = project_dir / ".mantle" / "system-design.md"
    return pd.exists() or sd.exists()


# ── Internal helpers ─────────────────────────────────────────────


def _update_state_body(
    project_dir: Path,
    identity: str,
) -> None:
    """Update state.md Current Focus with adoption next step.

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        (
            r"\1Adoption complete"
            " — run /mantle:plan-issues next.\n"
        ),
        note.body,
        count=1,
        flags=re.DOTALL,
    )

    updated = note.frontmatter.model_copy(
        update={
            "updated": date.today(),
            "updated_by": identity,
        },
    )

    vault.write_note(state_path, updated, body)
