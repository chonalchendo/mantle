---
issue: 44
title: Sweep batch 4 (scout, shape-issue, simplify, verify) plus integration test
  and full grep audit
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user, I want `/mantle:scout`, `/mantle:shape-issue`, `/mantle:simplify`, and `/mantle:verify` to find the right `.mantle/` directory automatically AND to know that the entire prompt sweep is complete with zero remaining hardcoded `.mantle/` Read references across the whole `claude/commands/mantle/` tree.

## Depends On

Stories 1, 2, 3, 4 (the CLI must exist; the audit can only meaningfully assert zero remaining hardcoded reads after every sweep batch has landed).

## Approach

Final sweep batch (4 files) plus the end-to-end integration test that proves a global-mode project resolves correctly through the new CLI command, plus a full-tree grep audit that fails the test suite if any prompt regresses.

## Implementation

### Universal pattern (identical to Stories 2, 3, 4)

At the top of Step 1, insert the resolve-path prelude:

```markdown
First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.
```

### claude/commands/mantle/scout.md (modify)

Sweep all `.mantle/state.md`, `.mantle/product-design.md`, `.mantle/system-design.md`, `.mantle/scouts/` Read targets.

### claude/commands/mantle/shape-issue.md (modify)

Sweep all `.mantle/state.md`, `.mantle/issues/`, `.mantle/product-design.md`, `.mantle/system-design.md`, `.mantle/shaped/`, `.mantle/learnings/` Read targets.

### claude/commands/mantle/simplify.md (modify)

Sweep all `.mantle/state.md`, `.mantle/issues/`, `.mantle/stories/` Read targets.

### claude/commands/mantle/verify.md (modify)

Sweep all `.mantle/state.md`, `.mantle/issues/`, `.mantle/stories/`, `.mantle/verification.md` Read targets.

### tests/test_global_mode_workflow.py (new file)

End-to-end integration test that proves the full prompt-→-CLI loop works in global storage mode.

```python
"""Integration test: prompts in global mode resolve via mantle where."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from mantle.core import migration, project


@pytest.fixture
def global_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Initialise a project in global storage mode under a fake home."""
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

    project_dir = tmp_path / "workrepo"
    project_dir.mkdir()
    project.init_project(project_dir, project_name="workrepo")
    project.update_config(project_dir, storage_mode="global")
    migration.migrate_to_global(project_dir)

    return project_dir


def test_where_returns_global_path_after_migration(
    global_project: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """mantle where prints the resolved global path for a migrated project."""
    from mantle.cli.storage import run_where
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_where(project_dir=global_project)

    output = buf.getvalue().strip()
    resolved = Path(output)
    assert resolved.is_absolute()
    assert ".mantle/projects/" in output
    assert resolved.exists()


def test_global_project_state_md_readable_via_resolved_path(
    global_project: Path,
) -> None:
    """After resolution, state.md is readable from the global location."""
    resolved = project.resolve_mantle_dir(global_project)
    state_md = resolved / "state.md"
    assert state_md.is_file()
    assert "workrepo" in state_md.read_text()


def test_global_project_has_no_local_mantle_dir(global_project: Path) -> None:
    """After migration, the project directory must contain no .mantle/.

    This is the whole point of global storage mode — work repos cannot have
    any .mantle/ artifact. If migration left a stub, the global-mode user's
    constraint is violated.
    """
    assert not (global_project / ".mantle").exists()
```

### tests/test_prompt_sweep.py (modify, finalise)

Add the batch-4 tests AND a full-tree audit test:

- **test_batch_4_no_hardcoded_mantle_reads**: Same regex check, scoped to `scout.md`, `shape-issue.md`, `simplify.md`, `verify.md`.
- **test_batch_4_includes_resolve_prelude**: Asserts each contains `MANTLE_DIR=$(mantle where)`.
- **test_full_tree_no_hardcoded_mantle_reads**: Walks every `.md` file under `claude/commands/mantle/` (using `PROMPTS_DIR.glob('*.md')`) and applies the `HARDCODED_READ_RE` regex. Excludes `help.md` (pure help text), `resume.md.j2` and `status.md.j2` (compiled templates that legitimately include literal `.mantle/` mentions in their bodies — these are run-time-substituted by `mantle compile`, not Read targets). The set of excluded files is hard-coded and small. The test fails with a list of every offending file:line pair so a future regression points the developer at the exact location.

Constants to add:

```python
BATCH_4_FILES = (
    "scout.md",
    "shape-issue.md",
    "simplify.md",
    "verify.md",
)

EXCLUDED_FROM_FULL_AUDIT = frozenset({
    "help.md",
    "resume.md.j2",
    "status.md.j2",
})
```

#### Design decisions

- **Real `migrate_to_global`**: Uses the actual migration code path so the test catches any future regression in the resolver-vs-migrator contract, not just the resolver in isolation.
- **`is_absolute` + `exists`**: Two assertions because a relative path under the fake home would still `exist` (passing accidentally) and an absolute path that does not exist would mean the migration silently dropped state.
- **`assert not (global_project / ".mantle").exists()`**: Codifies the global-mode contract from the issue description ("work repos cannot have ANY `.mantle/` artifact"). If a future change re-introduces a `.mantle/` stub for backwards compatibility, this test fails loudly.
- **Full-tree audit instead of per-batch only**: Per-batch checks catch regressions in the swept files; the full-tree audit catches regressions in OTHER files (e.g. a future PR adds a new `.mantle/state.md` Read to `build.md` without going through `mantle where`).

## Tests

(Tests are listed inline above — both `tests/test_global_mode_workflow.py` (new) and the additions to `tests/test_prompt_sweep.py` (modify) are part of this story.)
