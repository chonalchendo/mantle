"""Shared test fixtures for the mantle suite.

Named scenario fixtures describe a specific ``.mantle/`` state so tests
read as specifications of that state rather than walls of setup.
Naming convention: ``vault_with_<state>`` or ``<noun>_after_<event>``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from mantle.core import issues, vault

if TYPE_CHECKING:
    from pathlib import Path


_LEARNING_BODY_TEMPLATE = """\
## What went well

- Good thing happened

## Harder than expected

- {harder}

## Wrong assumptions

- {wrong}

## Recommendations

- {rec}
"""


def _write_learning(
    project_dir: Path,
    *,
    issue: int,
    title: str,
    confidence_delta: str,
    harder: str,
    wrong: str,
    rec: str,
) -> None:
    """Write a synthetic learning file under ``.mantle/learnings/``."""
    learnings_dir = project_dir / ".mantle" / "learnings"
    learnings_dir.mkdir(parents=True, exist_ok=True)
    slug = title.lower().replace(" ", "-")
    path = learnings_dir / f"issue-{issue:02d}-{slug}.md"
    body = _LEARNING_BODY_TEMPLATE.format(harder=harder, wrong=wrong, rec=rec)
    frontmatter = (
        "---\n"
        f"issue: {issue}\n"
        f"title: {title}\n"
        "author: test@example.com\n"
        "date: '2026-01-01'\n"
        f"confidence_delta: '{confidence_delta}'\n"
        "tags:\n"
        "- type/learning\n"
        "- phase/reviewing\n"
        "---\n\n"
    )
    path.write_text(frontmatter + body, encoding="utf-8")


def _write_issue(
    project_dir: Path,
    *,
    issue: int,
    title: str,
    slice_: tuple[str, ...],
) -> None:
    """Write a synthetic issue file under ``.mantle/issues/``."""
    note = issues.IssueNote(
        title=title,
        status="planned",
        slice=slice_,
        tags=("type/issue", "status/planned"),
    )
    slug = title.lower().replace(" ", "-")
    path = project_dir / ".mantle" / "issues" / f"issue-{issue:02d}-{slug}.md"
    vault.write_note(path, note, "## Why\nx\n")


@pytest.fixture
def vault_with_learnings(tmp_path: Path) -> Path:
    """Vault state with two learnings and two matching issues.

    A ``core/`` testing learning (+1 confidence) and a ``cli/``
    worktree learning (-1 confidence), each paired with a matching
    issue file — the canonical scenario for pattern/theme rendering
    tests.

    Args:
        tmp_path: Pytest-provided temporary directory.

    Returns:
        The project directory containing the populated ``.mantle/``.
    """
    _write_learning(
        tmp_path,
        issue=47,
        title="testing-woes",
        confidence_delta="+1",
        harder="pytest fixtures broke",
        wrong="Assumed mock matched prod",
        rec="Use real database",
    )
    _write_issue(tmp_path, issue=47, title="testing-woes", slice_=("core",))
    _write_learning(
        tmp_path,
        issue=48,
        title="cli-trouble",
        confidence_delta="-1",
        harder="worktree merge was harder",
        wrong="Assumed branch was clean",
        rec="Use worktree isolation",
    )
    _write_issue(tmp_path, issue=48, title="cli-trouble", slice_=("cli",))
    return tmp_path
