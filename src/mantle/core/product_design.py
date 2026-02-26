"""Product design — first-principles decomposition into building blocks."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import decisions, state, vault

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


# -- Data model ---------------------------------------------------


class ProductDesignNote(pydantic.BaseModel, frozen=True):
    """Product-design.md frontmatter schema.

    Attributes:
        vision: One-sentence product vision.
        principles: Non-negotiable truths that constrain the
            solution space.
        building_blocks: Essential primitives that must be correct.
        prior_art: Existing pieces to combine or adopt.
        composition: How the building blocks assemble into a
            coherent product.
        target_users: Specific user profile and context.
        success_metrics: Measurable outcomes (2-5 items).
        author: Git email of the author.
        created: Date the design was captured.
        updated: Date of the last edit.
        updated_by: Git email of the last editor.
        tags: Mantle tags for categorization.
    """

    vision: str
    principles: tuple[str, ...]
    building_blocks: tuple[str, ...]
    prior_art: tuple[str, ...]
    composition: str
    target_users: str
    success_metrics: tuple[str, ...]
    author: str
    created: date
    updated: date
    updated_by: str
    tags: tuple[str, ...] = ("type/product-design", "phase/design")


# -- Exception ----------------------------------------------------


class ProductDesignExistsError(Exception):
    """Raised when product-design.md already exists and overwrite is False.

    Attributes:
        path: Path to the existing product-design.md file.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Product design already exists: {path}")


# -- Body builder -------------------------------------------------


def _build_product_design_body(note: ProductDesignNote) -> str:
    """Build the markdown body from product design content.

    Args:
        note: The product design note with content to render.

    Returns:
        Formatted markdown body string.
    """
    principles = "\n".join(f"- {p}" for p in note.principles)
    blocks = "\n".join(f"- {b}" for b in note.building_blocks)
    prior = "\n".join(f"- {a}" for a in note.prior_art)
    metrics = "\n".join(f"- {m}" for m in note.success_metrics)
    return (
        f"## Vision\n\n{note.vision}\n\n"
        f"## Principles\n\n{principles}\n\n"
        f"## Building Blocks\n\n{blocks}\n\n"
        f"## Prior Art\n\n{prior}\n\n"
        f"## Composition\n\n{note.composition}\n\n"
        f"## Target Users\n\n{note.target_users}\n\n"
        f"## Success Metrics\n\n{metrics}\n\n"
        "## Open Questions\n\n"
        "_What do you still need to learn?_\n"
    )


# -- Public API ---------------------------------------------------


def create_product_design(
    project_dir: Path,
    *,
    vision: str,
    principles: Sequence[str],
    building_blocks: Sequence[str],
    prior_art: Sequence[str],
    composition: str,
    target_users: str,
    success_metrics: Sequence[str],
    overwrite: bool = False,
) -> ProductDesignNote:
    """Write .mantle/product-design.md, update state body, and transition.

    Args:
        project_dir: Directory containing .mantle/.
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

    Returns:
        The created ProductDesignNote.

    Raises:
        ProductDesignExistsError: If product-design.md exists
            and overwrite is False.
    """
    design_path = project_dir / ".mantle" / "product-design.md"

    if design_path.exists() and not overwrite:
        raise ProductDesignExistsError(design_path)

    identity = state.resolve_git_identity()
    today = date.today()

    note = ProductDesignNote(
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

    vault.write_note(design_path, note, _build_product_design_body(note))
    _update_state_body(project_dir, identity)

    current = state.load_state(project_dir)
    if current.status != state.Status.PRODUCT_DESIGN:
        state.transition(project_dir, state.Status.PRODUCT_DESIGN)

    return note


def load_product_design(project_dir: Path) -> ProductDesignNote:
    """Read .mantle/product-design.md and return the design note.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        The current ProductDesignNote.

    Raises:
        FileNotFoundError: If product-design.md does not exist.
    """
    path = project_dir / ".mantle" / "product-design.md"
    note = vault.read_note(path, ProductDesignNote)
    return note.frontmatter


def product_design_exists(project_dir: Path) -> bool:
    """Check whether .mantle/product-design.md exists.

    Args:
        project_dir: Directory containing .mantle/.

    Returns:
        True if product-design.md exists, False otherwise.
    """
    return (project_dir / ".mantle" / "product-design.md").exists()


def update_product_design(
    project_dir: Path,
    *,
    vision: str,
    principles: Sequence[str],
    building_blocks: Sequence[str],
    prior_art: Sequence[str],
    composition: str,
    target_users: str,
    success_metrics: Sequence[str],
    change_topic: str,
    change_summary: str,
    change_rationale: str,
) -> tuple[ProductDesignNote, Path]:
    """Update .mantle/product-design.md and log the revision.

    Overwrites the existing product design with revised content,
    preserving the original author and creation date. Creates a
    decision log entry capturing what changed and why.

    Args:
        project_dir: Directory containing .mantle/.
        vision: Updated product vision.
        principles: Updated non-negotiable truths.
        building_blocks: Updated essential primitives.
        prior_art: Updated existing pieces to adopt.
        composition: Updated assembly description.
        target_users: Updated user profile.
        success_metrics: Updated measurable outcomes.
        change_topic: Short slug for the decision log filename
            (e.g. "reframe-product-vision").
        change_summary: What changed (1-2 sentences).
        change_rationale: Why it changed (1-2 sentences).

    Returns:
        Tuple of (updated ProductDesignNote, path to decision
        log entry).

    Raises:
        FileNotFoundError: If product-design.md does not exist.
    """
    current = load_product_design(project_dir)

    identity = state.resolve_git_identity()
    today = date.today()

    note = ProductDesignNote(
        vision=vision,
        principles=tuple(principles),
        building_blocks=tuple(building_blocks),
        prior_art=tuple(prior_art),
        composition=composition,
        target_users=target_users,
        success_metrics=tuple(success_metrics),
        author=current.author,
        created=current.created,
        updated=today,
        updated_by=identity,
    )

    design_path = project_dir / ".mantle" / "product-design.md"
    vault.write_note(
        design_path, note, _build_product_design_body(note)
    )

    _, decision_path = decisions.save_decision(
        project_dir,
        topic=change_topic,
        decision=change_summary,
        alternatives=["Keep current design"],
        rationale=change_rationale,
        reversal_trigger=(
            "Revert if change no longer serves product goals."
        ),
        confidence="7/10",
        reversible="high",
        scope="product-design",
    )

    return note, decision_path


# -- Internal helpers ---------------------------------------------


def _update_state_body(project_dir: Path, identity: str) -> None:
    """Update state.md body with product design focus and refresh timestamps.

    Overwrites Current Focus section content using regex (not fragile
    placeholder search).

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        (
            r"\1Product design complete"
            r" — run /mantle:design-system next.\n"
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
