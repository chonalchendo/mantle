"""Archive completed issues and their related artifacts."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from mantle.core import issues, learning, project, stories

if TYPE_CHECKING:
    from pathlib import Path


def archive_issue(project_dir: Path, issue: int) -> list[Path]:
    """Move an issue and its artifacts to .mantle/archive/.

    Moves the issue file, stories, shaped doc, and learning into
    a mirror directory structure under .mantle/archive/.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number to archive.

    Returns:
        List of destination paths for all moved files.
    """
    mantle_dir = project.resolve_mantle_dir(project_dir)
    archive_dir = mantle_dir / "archive"
    moved: list[Path] = []

    # Collect all files to move: (source, dest_subdir)
    candidates: list[tuple[Path, str]] = []

    # Issue file
    issue_path = issues.find_issue_path(project_dir, issue)
    if issue_path and issue_path.exists():
        candidates.append((issue_path, "issues"))

    # Stories
    for story_path in stories.list_stories(project_dir, issue=issue):
        candidates.append((story_path, "stories"))

    # Shaped doc
    shaped_dir = mantle_dir / "shaped"
    if shaped_dir.is_dir():
        for path in shaped_dir.glob(f"issue-{issue:02d}*-shaped.md"):
            candidates.append((path, "shaped"))

    # Learning
    learning_path = learning.find_learning_path(project_dir, issue)
    if learning_path and learning_path.exists():
        candidates.append((learning_path, "learnings"))

    # Move all files
    for src, subdir in candidates:
        dest_dir = archive_dir / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        shutil.move(str(src), str(dest))
        moved.append(dest)

    return moved
