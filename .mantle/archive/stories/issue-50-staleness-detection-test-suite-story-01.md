---
issue: 50
title: Add tests/test_staleness_regressions.py with compile-lifecycle, CLI-ordering,
  archive-side-effect tests
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a maintainer, I want regression tests that catch side-effect ordering bugs before they reach human review, so that the recurring pattern from issues 46, 47, and 49 doesn't repeat.

## Depends On

None — independent (test-only addition).

## Approach

Add one new top-level test module `tests/test_staleness_regressions.py` containing three `TestClass` groups that exercise multi-step command sequences identified in the parent issue's acceptance criteria. Follows the existing top-level workflow-test pattern (`tests/test_workflows.py`) and the test-conventions documented in `CLAUDE.md` (pytest, `tmp_path` isolation, real CLI invocation via subprocess for end-to-end ordering, direct `core.*` calls when testing the side-effect API surface).

## Implementation

### tests/test_staleness_regressions.py (new file)

Single new file — no production code changes. Add at the top of the file:

```python
"""Regression tests for cross-command side-effect ordering bugs.

These tests exercise multi-step CLI sequences where one command's side
effects affect another. They catch the recurring pattern from issues 46,
47, and 49 where commands fail because prior commands archived or moved
files unexpectedly.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path
```

Add a private helper used by all three test classes:

```python
def _make_mantle_fixture(
    tmp_path: Path,
    *,
    issue: int = 50,
    issue_title: str = "Test issue",
    extra_skills: tuple[str, ...] = (),
) -> Path:
    """Scaffold a minimal but realistic .mantle/ in tmp_path.

    Writes:
      - .mantle/state.md (status=implementing, project=test-project)
      - .mantle/issues/issue-<NN>-<slug>.md with one acceptance criterion
      - .mantle/stories/ (empty dir)
      - test-vault/skills/<name>.md for each name in extra_skills

    Returns the .mantle path.
    """
```

Then three test classes:

```python
class TestCompileLifecycle:
    """Compile-modify-recompile regression tests for skill indexes."""

    def test_compile_creates_index_for_new_skill(self, tmp_path: Path) -> None:
        # 1. fixture with one skill that has tag "topic/finance"
        # 2. mantle compile
        # 3. assert index file for "topic/finance" exists in vault/indexes/
        ...

    def test_compile_updates_index_when_skill_modified(self, tmp_path: Path) -> None:
        # 1. fixture, compile, capture index content
        # 2. modify skill (add a second tag)
        # 3. compile again
        # 4. assert index for new tag exists; old index updated
        ...

    def test_compile_deletes_orphaned_index_when_skill_removed(self, tmp_path: Path) -> None:
        # 1. fixture with one skill that has tag "topic/scraping"
        # 2. compile -> index exists
        # 3. delete the skill file
        # 4. compile again
        # 5. assert orphaned topic/scraping index is removed
        # NOTE: This test is expected to surface the issue-49 bug. If it
        # currently fails, mark with @pytest.mark.xfail(reason="issue-49
        # orphan cleanup not implemented") and file a follow-up bug — DO
        # NOT silently fix orphan cleanup as part of this issue.

class TestCommandOrdering:
    """save-review-result vs transition-issue-approved ordering."""

    def test_save_review_result_succeeds_before_transition_approved(
        self, tmp_path: Path
    ) -> None:
        # 1. fixture with a verified issue
        # 2. mantle save-review-result --issue NN --result pass --content "..."
        # 3. assert exit code 0 and review file exists in .mantle/reviews/
        ...

    def test_save_review_result_after_archival_fails_gracefully(
        self, tmp_path: Path
    ) -> None:
        # 1. fixture with a verified issue
        # 2. mantle transition-issue-approved --issue NN  (archives it)
        # 3. mantle save-review-result --issue NN --result pass --content "..."
        # 4. assert NON-ZERO exit code, stderr mentions issue not found OR archive
        # 5. document the observed behaviour as the contract; if exit code
        #    is 0 (silent success), the test fails — file follow-up bug.

class TestArchiveSideEffects:
    """find_issue_path and downstream commands after archive_issue."""

    def test_find_issue_path_returns_none_after_archive(
        self, tmp_path: Path
    ) -> None:
        # 1. fixture with one issue
        # 2. archive_issue(project_dir, NN)
        # 3. assert find_issue_path returns None (current contract)
        # 4. assert archived file exists at .mantle/archive/issues/...
        ...

    def test_save_learning_after_archive_fails_clearly(
        self, tmp_path: Path
    ) -> None:
        # 1. fixture with one issue, archive it
        # 2. mantle save-learning --issue NN --content "..."
        # 3. assert non-zero exit OR explicit lookup in archive/issues/
        ...

    def test_update_story_status_after_archive_fails_clearly(
        self, tmp_path: Path
    ) -> None:
        # 1. fixture with one issue + one story, archive issue
        # 2. mantle update-story-status --issue NN --story 1 --status completed
        # 3. assert non-zero exit OR clear error message (not a silent no-op)
        ...
```

#### Design decisions

- **Single file, three classes**: matches the shaped approach (Approach A — small batch, low churn). New top-level slot mirrors `tests/test_workflows.py` (which is for CI workflows; this is for app-level workflows).
- **subprocess for CLI ordering, direct core.* calls for side-effect API**: ordering bugs from issues 46/47 lived in the CLI/prompt layer, so the CLI-ordering tests must exercise the real `python -m mantle ...` entry point. The pure side-effect tests (e.g., `find_issue_path` after archive) are faster and cleaner via direct import.
- **Use `subprocess.run([sys.executable, "-m", "mantle", ...], cwd=tmp_path, ...)`**: avoids dependency on the installed `mantle` binary (issue-46 learning called this out — installed-vs-working-tree divergence). Set `cwd=tmp_path` so all `.mantle/` resolution targets the fixture.
- **Helper minimalism**: `_make_mantle_fixture` writes only the baseline; each test adds what it needs (extra skills, story files) with inline `(.mantle / ...).write_text(...)` calls. Avoids fixture-factory bloat (Approach C explicitly out of scope).
- **xfail for known-unfixed bugs**: if `test_compile_deletes_orphaned_index_when_skill_removed` exposes the issue-49 bug, mark it `@pytest.mark.xfail` with a clear reason. Do NOT fix orphan cleanup as part of this issue (separate bug).
- **No conftest.py or new pytest plugins**: keep this self-contained; per "Does not" in shape doc.
- **Imports module then call**: `from mantle.core import issues, archive` then `issues.find_issue_path(...)`, per CLAUDE.md import rules.

## Tests

Test file IS the new file above. Each test is one behaviour, named explicitly. No mocks of internal functions — only filesystem fixtures via `tmp_path`. Verification:

- Run `uv run pytest tests/test_staleness_regressions.py -v` to confirm every test runs and either passes, or fails-as-xfail with a clear reason that documents a known bug.
- Run `just check` and confirm the full suite still passes.