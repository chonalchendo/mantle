"""Lifecycle hook dispatch — user-supplied shell scripts.

Mantle invokes ``<mantle-dir>/hooks/on-<event>.sh`` on lifecycle events.
The seam is deliberately opaque: mantle never imports tracker libraries,
never stores credentials, and never interprets the script's exit code
beyond "success" vs "warn-and-continue".
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import TYPE_CHECKING

import yaml

from mantle.core import project

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

HOOK_TIMEOUT_SECONDS = 30


def dispatch(
    event: str,
    *,
    issue: int,
    status: str,
    title: str,
    project_dir: Path,
) -> None:
    """Invoke the on-<event>.sh hook if present.

    Positional args passed to the script (in order): issue number, new
    status, issue title.  Env vars exported to the script: the caller's
    existing env plus every key/value under ``hooks_env:`` in
    ``<mantle-dir>/config.md`` frontmatter.

    Missing script: silent no-op.  Non-zero exit / timeout / OSError:
    warn-and-continue.  This function never raises.

    Args:
        event: Event name (e.g. ``"issue-shaped"``).  Resolves to
            ``<mantle-dir>/hooks/on-<event>.sh``.
        issue: Issue number to pass as ``$1``.
        status: Issue status to pass as ``$2``.
        title: Issue title to pass as ``$3``.
        project_dir: Project directory containing ``.mantle/``.
    """
    hooks_dir = project.resolve_mantle_dir(project_dir) / "hooks"
    script = hooks_dir / f"on-{event}.sh"
    if not script.is_file():
        return

    env = os.environ.copy()
    env.update(_load_hooks_env(project_dir))

    try:
        subprocess.run(
            [str(script), str(issue), status, title],
            env=env,
            timeout=HOOK_TIMEOUT_SECONDS,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "Hook on-%s.sh exited %s (continuing). stderr: %s",
            event,
            exc.returncode,
            (exc.stderr or "").strip(),
        )
    except subprocess.TimeoutExpired:
        logger.warning(
            "Hook on-%s.sh timed out after %ss (continuing).",
            event,
            HOOK_TIMEOUT_SECONDS,
        )
    except OSError as exc:
        logger.warning(
            "Hook on-%s.sh failed to execute: %s (continuing).",
            event,
            exc,
        )


def _load_hooks_env(project_dir: Path) -> dict[str, str]:
    """Return the ``hooks_env:`` dict from config.md frontmatter, or empty.

    Reads the raw YAML frontmatter block directly rather than going
    through ``vault.read_note`` so that a malformed or missing file
    degrades silently to an empty dict (seam principle: hooks never
    block the workflow).

    Args:
        project_dir: Project directory containing ``.mantle/``.

    Returns:
        Mapping of env-var names to values, stringified.  Empty on any
        failure to parse or locate the file.
    """
    config_path = project.resolve_mantle_dir(project_dir) / "config.md"
    if not config_path.is_file():
        return {}
    text = config_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    _, _, rest = text.partition("---\n")
    front, _, _ = rest.partition("\n---")
    try:
        data = yaml.safe_load(front) or {}
    except yaml.YAMLError:
        return {}
    raw = data.get("hooks_env") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items()}
