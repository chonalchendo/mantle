"""Resolve baseline skills from project-level constraints."""

from __future__ import annotations

import re
import tomllib
import warnings
from typing import TYPE_CHECKING

from mantle.core import skills

if TYPE_CHECKING:
    from pathlib import Path


def _python_baseline_for_version(requires_python: str) -> tuple[str, ...]:
    """Map a requires-python spec to baseline skill names.

    Pure function — no filesystem access.  Handles specifiers like
    ``">=3.14"``, ``"~=3.14"``, ``">=3.14,<4"``, ``"3.14.*"``.
    Returns empty tuple for unparseable or pre-3.14 specs.

    Args:
        requires_python: Value of ``pyproject.toml`` ``requires-python``.

    Returns:
        Tuple of baseline skill names for the detected version.
    """
    if not requires_python:
        return ()
    # Grab the first ``major.minor`` token anywhere in the spec string.
    match = re.search(r"(\d+)\.(\d+)", requires_python)
    if match is None:
        return ()
    major = int(match.group(1))
    minor = int(match.group(2))
    if major == 3 and minor >= 14:
        return ("python-314",)
    return ()


def resolve_baseline_skills(project_dir: Path) -> tuple[str, ...]:
    """Return vault-present baseline skills for the project's constraints.

    Reads ``project_dir/pyproject.toml``, parses ``requires-python``,
    maps to baseline skill names via ``_python_baseline_for_version``,
    then filters to skills that actually exist in the personal vault.
    Emits a warning for each baseline skill that is missing from the
    vault but continues without failing.

    Args:
        project_dir: Directory containing ``pyproject.toml``.

    Returns:
        Tuple of vault-present baseline skill names.  Empty on any
        failure path (no pyproject, unreadable TOML, vault not
        configured, unrecognised version).
    """
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.is_file():
        return ()
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError, OSError:
        return ()
    requires_python = data.get("project", {}).get("requires-python", "")
    if not requires_python:
        return ()
    candidates = _python_baseline_for_version(requires_python)
    if not candidates:
        return ()
    try:
        present: list[str] = []
        for name in candidates:
            if skills.skill_exists(project_dir, name):
                present.append(name)
            else:
                warnings.warn(
                    f'Baseline skill "{name}" not found in vault — skipping.',
                    stacklevel=2,
                )
        return tuple(present)
    except skills.VaultNotConfiguredError:
        return ()
