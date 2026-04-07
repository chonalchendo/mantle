"""Migrate .mantle/ storage between local and global locations."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

from mantle.core import project


def migrate_to_global(
    project_dir: Path,
    *,
    remove_local: bool = True,
) -> Path:
    """Move .mantle/ from in-repo to global storage.

    Copies the local ``.mantle/`` directory to
    ``~/.mantle/projects/<identity>/``, updates the config in the
    new location, and optionally removes the old directory (leaving
    a stub ``config.md`` so ``resolve_mantle_dir`` can find it).

    Args:
        project_dir: Root directory of the project.
        remove_local: If True, remove old .mantle/ contents but
            leave a stub config.md with ``storage_mode: global``.

    Returns:
        Path to the new global .mantle/ directory.

    Raises:
        FileExistsError: If the global target already exists.
    """
    identity = project.project_identity(project_dir)
    target = Path.home() / project.GLOBAL_MANTLE_ROOT / identity

    if target.exists():
        msg = f"Global storage already exists at {target}"
        raise FileExistsError(msg)

    source = project_dir / project.MANTLE_DIR
    shutil.copytree(source, target)

    # Update config in the NEW (global) location.
    _update_config_at(target, storage_mode="global")

    if remove_local:
        # Remove everything under .mantle/ except rebuild
        # a stub config.md.
        shutil.rmtree(source)
        source.mkdir()
        _write_stub_config(source, storage_mode="global")

    return target


def migrate_to_local(
    project_dir: Path,
    *,
    remove_global: bool = True,
) -> Path:
    """Move .mantle/ from global storage back to in-repo.

    Reads the current config to locate the global directory,
    copies its contents to ``project_dir / .mantle``, updates
    the config to ``storage_mode: local``, and optionally
    removes the global directory.

    Args:
        project_dir: Root directory of the project.
        remove_global: If True, remove the global directory
            after copying.

    Returns:
        Path to the local .mantle/ directory.
    """
    global_dir = project.resolve_mantle_dir(project_dir)
    local = project_dir / project.MANTLE_DIR

    # Remove the stub local .mantle/ so copytree can write.
    if local.exists():
        shutil.rmtree(local)

    shutil.copytree(global_dir, local)

    # Update config in the LOCAL location.
    _update_config_at(local, storage_mode="local")

    if remove_global:
        shutil.rmtree(global_dir)

    return local


# ── Internal helpers ────────────────────────────────────────────


def _update_config_at(
    mantle_dir: Path,
    **kwargs: Any,
) -> None:
    """Update config.md frontmatter inside a .mantle/ directory.

    Unlike ``project.update_config`` which takes a project root,
    this operates directly on the .mantle/ directory itself.

    Args:
        mantle_dir: The .mantle/ directory containing config.md.
        **kwargs: Key-value pairs to update in frontmatter.
    """
    config_path = mantle_dir / "config.md"
    fm, body = project._read_frontmatter_and_body(config_path)
    fm.update(kwargs)
    project._write_frontmatter_and_body(config_path, fm, body)


def _write_stub_config(
    mantle_dir: Path,
    *,
    storage_mode: str,
) -> None:
    """Write a minimal config.md stub with the given storage mode.

    Args:
        mantle_dir: The .mantle/ directory to write into.
        storage_mode: Value for the ``storage_mode`` field.
    """
    fm: dict[str, Any] = {"storage_mode": storage_mode}
    yaml_str = yaml.dump(
        fm,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )
    text = f"---\n{yaml_str}---\n\n{project.CONFIG_BODY}"
    (mantle_dir / "config.md").write_text(text, encoding="utf-8")
