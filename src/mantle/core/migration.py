"""Migrate .mantle/ storage between local and global locations."""

from __future__ import annotations

import shutil
from pathlib import Path

from mantle.core import project


def migrate_to_global(
    project_dir: Path,
    *,
    remove_local: bool = True,
) -> Path:
    """Move .mantle/ from in-repo to global storage.

    Copies the local ``.mantle/`` directory to
    ``~/.mantle/projects/<identity>/`` and optionally removes the
    old directory entirely.  The directory's existence at
    ``~/.mantle/projects/<identity>/`` is the signal that a project
    is in global-storage mode — no in-repo marker is required, so
    after migration the project dir contains no ``.mantle/`` folder
    at all.

    Args:
        project_dir: Root directory of the project.
        remove_local: If True, remove the local ``.mantle/``
            directory entirely after the copy.

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

    if remove_local:
        shutil.rmtree(source)

    return target


def migrate_to_local(
    project_dir: Path,
    *,
    remove_global: bool = True,
) -> Path:
    """Move .mantle/ from global storage back to in-repo.

    Resolves the global directory for this project, copies its
    contents to ``project_dir / .mantle``, and optionally removes
    the global directory.

    Args:
        project_dir: Root directory of the project.
        remove_global: If True, remove the global directory
            after copying.

    Returns:
        Path to the local .mantle/ directory.
    """
    global_dir = project.resolve_mantle_dir(project_dir)
    local = project_dir / project.MANTLE_DIR

    # Remove any pre-existing local .mantle/ so copytree can write.
    if local.exists():
        shutil.rmtree(local)

    shutil.copytree(global_dir, local)

    if remove_global:
        shutil.rmtree(global_dir)

    return local
