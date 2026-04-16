"""Save-skill command — create or update a skill node in the personal vault."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import skills

console = Console()


def run_save_skill(
    *,
    name: str,
    description: str,
    proficiency: str,
    content: str,
    when_to_use: str = "",
    related_skills: tuple[str, ...] = (),
    projects: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Create a skill node in the personal vault.

    Args:
        name: Human-readable skill name.
        description: What this skill covers and when it's relevant.
        proficiency: Self-assessment in "N/10" format.
        content: Authored skill knowledge (markdown).
        when_to_use: Trigger conditions for auto-invocation.
        related_skills: Related skill names.
        projects: Project names using this skill.
        tags: Content tags (e.g. ``topic/python``, ``domain/web``).
        overwrite: Replace existing skill if True.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: On existing skill, vault not configured,
            or invalid proficiency.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = skills.create_skill(
            project_dir,
            name=name,
            description=description,
            proficiency=proficiency,
            content=content,
            when_to_use=when_to_use,
            related_skills=related_skills,
            projects=projects,
            tags=tags,
            overwrite=overwrite,
        )
    except skills.SkillExistsError as exc:
        console.print(
            f"[yellow]Warning:[/yellow] {exc.path.name} "
            "already exists. Use --overwrite to replace."
        )
        raise SystemExit(1) from None
    except skills.VaultNotConfiguredError:
        errors.exit_with_error(
            "Personal vault not configured.",
            hint=(
                "Set vault_path in ~/.mantle/config.yaml"
                " or run 'mantle init-vault'"
            ),
        )
    except ValueError as exc:
        errors.exit_with_error(
            str(exc),
            hint=errors.UNEXPECTED_BUG_HINT,
        )

    console.print(f"Skill saved to {path}")
    console.print()
    console.print(f"  Name:        {note.name}")
    console.print(f"  Description: {note.description}")
    console.print(f"  Proficiency: {note.proficiency}")
    console.print()
    console.print(
        "  Next: run [bold]/mantle:add-skill[/bold] to track more skills"
    )
