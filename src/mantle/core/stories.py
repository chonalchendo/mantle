"""Story planning — implementable stories with test specifications."""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING

import pydantic

from mantle.core import issues, state, vault

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


class StoryNote(pydantic.BaseModel, frozen=True):
    """Story frontmatter schema.

    Attributes:
        issue: Parent issue number.
        title: Short title for the story.
        status: Story lifecycle status.
        failure_log: Error details when story is blocked.
        tags: Mantle tags for categorization.
    """

    issue: int
    title: str
    status: str = "planned"
    failure_log: str | None = None
    tags: tuple[str, ...] = ("type/story", "status/planned")


# ── Exception ────────────────────────────────────────────────────


class StoryExistsError(Exception):
    """Raised when a story file already exists at the target path.

    Attributes:
        path: Path to the existing story file.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Story already exists at {path}")


# ── Public API ───────────────────────────────────────────────────


def save_story(
    project_dir: Path,
    content: str,
    *,
    issue: int,
    title: str,
    overwrite: bool = False,
    story: int | None = None,
) -> tuple[StoryNote, Path]:
    """Save story to .mantle/stories/issue-NN-story-NN.md.

    Auto-assigns the next story number for the issue unless ``story``
    is provided. Raises if file exists and ``overwrite`` is False.
    Updates the parent issue's story_count and state.md Current Focus.

    Args:
        project_dir: Directory containing .mantle/.
        content: Full story body (markdown).
        issue: Parent issue number.
        title: Short title for the story.
        overwrite: Replace existing story file.
        story: Explicit story number (for overwrites). Auto-assigns
            when None.

    Returns:
        Tuple of (StoryNote frontmatter, path to saved file).

    Raises:
        StoryExistsError: If file exists and overwrite is False.
    """
    if story is None:
        story = next_story_number(project_dir, issue=issue)

    story_path = _story_path(project_dir, issue, story)

    if story_path.exists() and not overwrite:
        raise StoryExistsError(story_path)

    note = StoryNote(issue=issue, title=title)

    vault.write_note(story_path, note, content)

    story_count = _update_issue_story_count(project_dir, issue)

    identity = state.resolve_git_identity()
    _update_state_body(project_dir, identity, issue, story_count)

    return note, story_path


def load_story(path: Path) -> tuple[StoryNote, str]:
    """Read a story file.

    Takes absolute path (composable with list_stories).

    Args:
        path: Absolute path to the story file.

    Returns:
        Tuple of (StoryNote frontmatter, body text).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    note = vault.read_note(path, StoryNote)
    return note.frontmatter, note.body


def list_stories(project_dir: Path, *, issue: int) -> list[Path]:
    """All story paths for a given issue, sorted by filename.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number to list stories for.

    Returns:
        List of paths to story files. Empty if none.
    """
    stories_dir = project_dir / ".mantle" / "stories"
    if not stories_dir.is_dir():
        return []
    return sorted(stories_dir.glob(f"issue-{issue:02d}-story-*.md"))


def next_story_number(project_dir: Path, *, issue: int) -> int:
    """Return the next story number for an issue (highest + 1).

    Scans .mantle/stories/ for story files matching the issue and
    returns max(story_number) + 1. Returns 1 if no stories exist.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number to scan stories for.

    Returns:
        The next available story number.
    """
    pattern = re.compile(r"issue-\d+-story-(\d+)\.md")
    highest = 0
    for path in list_stories(project_dir, issue=issue):
        match = pattern.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def story_exists(project_dir: Path, *, issue: int, story: int) -> bool:
    """True if the story file exists.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.
        story: Story number.

    Returns:
        True if the story file exists.
    """
    return _story_path(project_dir, issue, story).exists()


def count_stories(project_dir: Path, *, issue: int) -> int:
    """Number of stories for the given issue.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.

    Returns:
        Count of story files for the issue.
    """
    return len(list_stories(project_dir, issue=issue))


# ── Internal helpers ─────────────────────────────────────────────


def _story_path(project_dir: Path, issue: int, story: int) -> Path:
    """Compute story file path.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number.
        story: Story number.

    Returns:
        Path for the story file.
    """
    return (
        project_dir
        / ".mantle"
        / "stories"
        / f"issue-{issue:02d}-story-{story:02d}.md"
    )


def _update_issue_story_count(project_dir: Path, issue: int) -> int:
    """Update the parent issue's story_count field.

    Args:
        project_dir: Directory containing .mantle/.
        issue: Issue number to update.

    Returns:
        The updated story count.
    """
    issue_path = issues._issue_path(project_dir, issue)
    note_obj = vault.read_note(issue_path, issues.IssueNote)
    story_count = count_stories(project_dir, issue=issue)
    updated = note_obj.frontmatter.model_copy(
        update={"story_count": story_count},
    )
    vault.write_note(issue_path, updated, note_obj.body)
    return story_count


def _update_state_body(
    project_dir: Path,
    identity: str,
    issue: int,
    story_count: int,
) -> None:
    """Update state.md Current Focus after saving stories.

    Does not transition state — stays in PLANNING.

    Args:
        project_dir: Directory containing .mantle/.
        identity: Git email for the updated_by field.
        issue: Issue number stories were planned for.
        story_count: Number of stories planned for the issue.
    """
    state_path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(state_path, state.ProjectState)

    body = re.sub(
        r"(## Current Focus\n\n).*?(?=\n##|\Z)",
        rf"\1Issue {issue} — {story_count} stories planned."
        r" Run /mantle:plan-stories for more"
        r" or /mantle:implement to start building."
        "\n",
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
