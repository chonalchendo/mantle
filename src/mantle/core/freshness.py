"""Freshness warnings for file-based context.

Attaches human-readable staleness caveats to context items so AI
agents know to verify claims against current code before acting.

Ported from Claude Code's ``memoryAge.ts`` pattern — models are
poor at date arithmetic, so "47 days ago" triggers staleness
reasoning better than a raw ISO timestamp.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def age_days(path: Path) -> int:
    """Days since a file was last modified.

    Floor-rounded: 0 for today, 1 for yesterday. Negative inputs
    (future mtime, clock skew) clamp to 0.

    Args:
        path: Path to the file.

    Returns:
        Non-negative integer day count.
    """
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    now = datetime.now(tz=UTC)
    delta = (now - mtime).total_seconds()
    return max(0, math.floor(delta / 86_400))


def age_label(path: Path) -> str:
    """Human-readable age string for a file.

    Args:
        path: Path to the file.

    Returns:
        ``"today"``, ``"yesterday"``, or ``"N days ago"``.
    """
    d = age_days(path)
    if d == 0:
        return "today"
    if d == 1:
        return "yesterday"
    return f"{d} days ago"


def freshness_caveat(path: Path, *, threshold_days: int = 2) -> str:
    """Staleness caveat for files older than the threshold.

    Returns an empty string for fresh files (within threshold).
    For stale files, returns a plain-text warning that the content
    may be outdated and should be verified against current code.

    Args:
        path: Path to the file.
        threshold_days: Minimum age in days before a caveat is
            generated.  Defaults to 2.

    Returns:
        Warning string, or empty string if the file is fresh.
    """
    d = age_days(path)
    if d < threshold_days:
        return ""
    label = age_label(path)
    return (
        f"This context is from {label}. "
        f"It may reference code, files, or patterns that have since "
        f"changed. Verify against current code before acting on it."
    )
