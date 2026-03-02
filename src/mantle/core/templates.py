"""Jinja2 template rendering with strict variable checking."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import jinja2

if TYPE_CHECKING:
    from pathlib import Path


def render_template(
    template_dir: Path,
    template_name: str,
    context: dict[str, Any],
) -> str:
    """Load and render a Jinja2 template with the given context.

    Uses ``StrictUndefined`` so that missing variables raise
    immediately rather than rendering as empty strings.

    Args:
        template_dir: Directory containing ``.j2`` template files.
        template_name: Filename of the template to render.
        context: Variable mapping passed to the template.

    Returns:
        The rendered template string.

    Raises:
        jinja2.TemplateNotFound: If the template does not exist.
        jinja2.UndefinedError: If the context is missing a required
            variable.
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template(template_name)
    return template.render(context)


def find_templates(template_dir: Path) -> list[str]:
    """Return sorted list of ``.j2`` filenames in a directory.

    Args:
        template_dir: Directory to scan for templates.

    Returns:
        Sorted list of ``.j2`` filenames. Empty list if the
        directory does not exist or contains no templates.
    """
    if not template_dir.is_dir():
        return []
    return sorted(p.name for p in template_dir.iterdir() if p.suffix == ".j2")
