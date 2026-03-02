"""Compile vault context into concrete markdown commands via Jinja2."""

from __future__ import annotations

import re
from importlib import resources
from pathlib import Path
from typing import Any

from mantle.core import manifest, session, state, templates, vault

# ── Public API ───────────────────────────────────────────────────


def collect_context(project_dir: Path) -> dict[str, Any]:
    """Read vault state and build a context dict for templates.

    Reads ``state.md`` frontmatter fields and body sections into a
    flat dict. Body sections are extracted via heading parsing.

    Args:
        project_dir: Directory containing ``.mantle/``.

    Returns:
        Flat dict with frontmatter fields and body section content.

    Raises:
        FileNotFoundError: If ``state.md`` does not exist.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    fm = note.frontmatter
    context: dict[str, Any] = {
        "project": fm.project,
        "status": fm.status.value,
        "confidence": fm.confidence,
        "current_issue": fm.current_issue,
        "current_story": fm.current_story,
        "skills_required": list(fm.skills_required),
    }

    sections = _parse_body_sections(note.body)
    context.update(sections)

    context.update(_collect_session_context(project_dir))

    return context


def source_paths(project_dir: Path) -> list[Path]:
    """Return all vault files that affect compilation output.

    Always includes ``state.md``. Conditionally includes optional
    vault files and all bundled ``.j2`` template files.

    Args:
        project_dir: Directory containing ``.mantle/``.

    Returns:
        List of absolute paths to source files.
    """
    mantle_dir = project_dir / ".mantle"
    paths: list[Path] = [mantle_dir / "state.md"]

    for name in ("idea.md", "product-design.md", "system-design.md"):
        candidate = mantle_dir / name
        if candidate.is_file():
            paths.append(candidate)

    sessions_dir = mantle_dir / "sessions"
    if sessions_dir.is_dir():
        session_files = sorted(sessions_dir.glob("*.md"))
        if session_files:
            paths.append(session_files[-1])

    tpl_dir = template_dir()
    if tpl_dir.is_dir():
        paths.extend(sorted(p for p in tpl_dir.iterdir() if p.suffix == ".j2"))

    return paths


def template_dir() -> Path:
    """Resolve the bundled template directory inside the package.

    In an installed wheel, the ``claude/`` tree lives inside the
    package.  During development (editable install), it lives at
    the project root.  This function checks both locations.

    Returns:
        Path to the ``commands/mantle/`` directory containing
        ``.j2`` template files.
    """
    # Installed package path
    ref = resources.files("mantle").joinpath("claude", "commands", "mantle")
    pkg_path = Path(str(ref))
    if pkg_path.is_dir():
        return pkg_path

    # Development fallback: <package>/../../claude/commands/mantle
    dev_path = Path(str(resources.files("mantle"))).parent.parent
    dev_path = dev_path / "claude" / "commands" / "mantle"
    if dev_path.is_dir():
        return dev_path

    return pkg_path  # Return the expected path even if missing


def compile(
    project_dir: Path,
    target_dir: Path | None = None,
) -> list[str]:
    """Compile vault context into concrete markdown commands.

    Reads vault state, renders all ``.j2`` templates, writes output
    to the target directory, and saves a compilation manifest.

    Args:
        project_dir: Directory containing ``.mantle/``.
        target_dir: Output directory for compiled commands.
            Defaults to ``~/.claude/commands/mantle/``.

    Returns:
        List of compiled template names (without ``.j2`` extension).

    Raises:
        FileNotFoundError: If ``.mantle/`` or ``state.md`` is
            missing.
    """
    if target_dir is None:
        target_dir = _default_target_dir()

    target_dir.mkdir(parents=True, exist_ok=True)

    context = collect_context(project_dir)
    tpl_dir = template_dir()
    tpl_names = templates.find_templates(tpl_dir)

    compiled: list[str] = []
    for tpl_name in tpl_names:
        rendered = templates.render_template(tpl_dir, tpl_name, context)
        out_name = tpl_name.removesuffix(".j2")
        (target_dir / out_name).write_text(rendered, encoding="utf-8")
        compiled.append(out_name)

    paths = source_paths(project_dir)
    hashes = manifest.hash_paths(paths)
    manifest.save_compilation_manifest(_manifest_path(project_dir), hashes)

    return compiled


def compile_if_stale(
    project_dir: Path,
    target_dir: Path | None = None,
) -> list[str] | None:
    """Compile only when source files have changed.

    Args:
        project_dir: Directory containing ``.mantle/``.
        target_dir: Output directory for compiled commands.

    Returns:
        List of compiled template names if compilation ran,
        or ``None`` if sources are up to date.
    """
    paths = source_paths(project_dir)
    current_hashes = manifest.hash_paths(paths)
    mpath = _manifest_path(project_dir)

    if not manifest.is_compilation_stale(mpath, current_hashes):
        return None

    return compile(project_dir, target_dir)


# ── Internal helpers ─────────────────────────────────────────────


def _collect_session_context(
    project_dir: Path,
) -> dict[str, Any]:
    """Retrieve latest session fields for template context.

    Resolves git identity to filter sessions to the current user.
    Falls back to unfiltered latest session when git identity is
    unavailable.

    Args:
        project_dir: Directory containing ``.mantle/``.

    Returns:
        Dict with ``has_session``, ``latest_session_body``,
        ``latest_session_date``, and ``latest_session_commands``.
    """
    try:
        identity = state.resolve_git_identity()
        result = session.latest_session(project_dir, author=identity)
    except RuntimeError:
        result = session.latest_session(project_dir)

    if result is None:
        return {
            "has_session": False,
            "latest_session_body": "",
            "latest_session_date": "",
            "latest_session_commands": [],
        }

    note, body = result
    return {
        "has_session": True,
        "latest_session_body": body,
        "latest_session_date": note.date.strftime("%Y-%m-%d %H:%M"),
        "latest_session_commands": list(note.commands_used),
    }


def _parse_body_sections(body: str) -> dict[str, str]:
    """Parse a markdown body into a dict of section_name -> content.

    Splits on ``## `` headings. Keys are lowercased with spaces
    replaced by underscores.

    Args:
        body: Markdown body text.

    Returns:
        Mapping of normalised heading names to section content.
    """
    sections: dict[str, str] = {}
    # Split on ## headings
    parts = re.split(r"^## ", body, flags=re.MULTILINE)

    for part in parts[1:]:  # Skip content before first heading
        lines = part.split("\n", 1)
        heading = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""
        key = heading.lower().replace(" ", "_")
        sections[key] = content

    return sections


def _default_target_dir() -> Path:
    """Return the default compilation output directory."""
    return Path.home() / ".claude" / "commands" / "mantle"


def _manifest_path(project_dir: Path) -> Path:
    """Return the path to the compilation manifest."""
    return project_dir / ".mantle" / ".compile-manifest.json"
