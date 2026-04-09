---
issue: 46
title: Move archive side effect from save-learning to transition-to-approved
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a mantle user running `/mantle:build`, I want `mantle save-learning` to only write a learning note — never move files — so that a mid-pipeline learning capture cannot destroy the shaped doc, story files, or issue file that later build steps still need to read.

## Depends On

None — independent.

## Approach

Decouple learning capture from archival by removing the `archive.archive_issue()` side effect from the `save-learning` CLI wrapper and moving it into the `transition-to-approved` CLI wrapper. This preserves the core architectural boundary (core does not import from cli; core/archive.py already imports core/issues so the side effect cannot live in core without introducing a cycle). Single story because the two changes must land together — removing archive from save-learning without adding it elsewhere would leave terminal issues un-archived, breaking AC3.

## Implementation

### src/mantle/cli/learning.py (modify)

Drop the archival side effect entirely.

- Remove the `from mantle.core import archive, learning` line; replace with `from mantle.core import learning`.
- Delete lines 72-79 of the current file — the `moved = archive.archive_issue(project_dir, issue)` call and the conditional "Archived N file(s)" print block.
- Keep everything above line 72 unchanged: the learning save, rich confirmation block, and "Learnings auto-surface in future ..." hint all stay.

#### Design decisions

- **No `--no-archive` flag**: the fix removes the coupling entirely rather than papering over it with an opt-out. New callers can never forget to pass a flag if the flag does not exist.
- **Keep the "Learnings auto-surface" hint**: it documents the read side of the learnings loop, independent of archival.

### src/mantle/cli/review.py (modify)

Add the archive side effect to the approval transition wrapper.

- Add `from mantle.core import archive, issues, review` — insert `archive` into the existing `from mantle.core import issues, review` import on line 14.
- In `run_transition_to_approved` (lines 54-74), after the `_transition(...)` call returns successfully, call `archive.archive_issue(project_dir or Path.cwd(), issue)` and capture the returned list.
- Resolve `project_dir` once at the top of the function (`project_dir = project_dir or Path.cwd()`) so the same value flows into both `_transition` and `archive.archive_issue`. Pass the resolved dir into `_transition` as well.
- If the archive list is non-empty, print a dim summary line matching the wording the CLI already used:
  ```
  console.print()
  console.print(
      f"[dim]Archived {len(moved)} file(s) for issue"
      f" {issue} to .mantle/archive/[/dim]"
  )
  ```
- Do not touch `run_transition_to_implementing` or `run_transition_to_implemented` — archival stays on the terminal transition only.

#### Design decisions

- **Approved, not verified, is the archive point**: `verified → implementing` is an allowed rollback transition (see `_ALLOWED_TRANSITIONS` in core/issues.py). Archiving at verified would orphan files when a failed review bounces the issue back to implementing. `approved` is the only truly terminal status.
- **Side effect lives in cli/, not core/**: `core/archive.py` already imports `core/issues`, so adding an archive call inside `issues.transition_to_approved` would create an import cycle. Keeping the side effect in the CLI wrapper honours CLAUDE.md's "core/ never imports from cli/" boundary.

### src/mantle/cli/main.py (no change expected)

The existing `transition-issue-approved` command already dispatches to `review.run_transition_to_approved`, which is the function we just modified. No main.py edit needed — verify no wiring is missed.

## Tests

### tests/cli/test_learning.py (new file)

New CLI-level test module for `run_save_learning` — the CLI wrapper side effects are currently untested, which is part of why this bug shipped.

- **test_save_learning_does_not_archive_issue_file**: set up a project with an issue at `implementing` status and no learning yet. Call `learning.run_save_learning(...)`. Assert the issue file still exists at its original path in `.mantle/issues/` and nothing was moved to `.mantle/archive/issues/`.
- **test_save_learning_does_not_archive_shaped_doc**: set up a project with an issue + shaped doc under `.mantle/shaped/issue-NN-*-shaped.md`. Call `run_save_learning`. Assert the shaped doc still exists at its original path.
- **test_save_learning_does_not_archive_stories**: set up a project with an issue + two story files under `.mantle/stories/`. Call `run_save_learning`. Assert both story files still exist at their original paths.
- **test_save_learning_mid_pipeline_regression**: the full mid-pipeline scene — issue at `implementing`, shaped doc, two stories, no existing learning. Call `run_save_learning`. Assert the learning file was written AND every pre-existing file (issue, shaped, both stories) is still at its original path. This is the direct regression test for AC4.
- **test_save_learning_writes_learning_file**: baseline happy path — `run_save_learning` still writes `.mantle/learnings/issue-NN.md` with correct content.

Use `tmp_path` fixtures and `mantle.core.learning.save_learning` + direct file writes to set up the pre-state; no subprocess or LLM calls.

### tests/cli/test_review.py (modify)

Add approval-archive coverage.

- **test_transition_to_approved_archives_issue_artifacts**: set up an issue at `verified` status with a shaped doc and two story files. Call `review.run_transition_to_approved(issue=N, project_dir=tmp_path)`. Assert: (1) issue status transitioned to `approved`, (2) the issue file is now under `.mantle/archive/issues/`, (3) the shaped doc is under `.mantle/archive/shaped/`, (4) both story files are under `.mantle/archive/stories/`, (5) none of the originals still exist in the live dirs.
- **test_transition_to_approved_archives_learning_if_present**: same setup plus a pre-existing learning file under `.mantle/learnings/`. Call `run_transition_to_approved`. Assert the learning was moved to `.mantle/archive/learnings/`.
- **test_transition_to_approved_archive_noop_when_nothing_to_archive**: approve an issue that has no shaped doc, no stories, no learning (only the issue file). Call `run_transition_to_approved`. Assert the issue file itself is archived and no error is raised.

### tests/core/test_learning.py (no change)

The core `save_learning` function was already pure. These tests should still pass unchanged.

### tests/core/test_archive.py (no change)

`core/archive.archive_issue` semantics are unchanged. These tests should still pass unchanged.

### claude/commands/mantle/implement.md (verify)

If a workaround comment exists in Step 9 about archival ordering, delete it. Per AC6. If no such comment exists, no-op.