---
issue: 13
title: Core orchestrator — implementation loop with retry and git commits
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## User Story

As a developer, I want `mantle implement --issue N` to iterate over stories, invoke Claude Code for each, run tests, retry once on failure, create atomic git commits, and update vault state so that implementation is automated and resumable.

## Approach

Add the `implement()` function to `core/orchestrator.py` (created in story 2). This is the main loop described in the system design pseudocode. It uses `claude_cli.for_story()` (story 1) to build subprocess invocations and `compile_story_context()` / `update_story_status()` (story 2) for context and state. This is story 3 of 4: the core loop that ties everything together.

## Implementation

### src/mantle/core/orchestrator.py (modify)

#### Main loop

- `implement(project_dir, *, issue) -> None` — Run the implementation loop for an issue. Steps:

  1. **Transition state** to `IMPLEMENTING` via `state.transition()` if not already implementing. If already in `IMPLEMENTING` state (resuming), skip the transition.
  2. **Update tracking** — set `current_issue` via `update_project_tracking()`.
  3. **Load stories** for the issue via `stories.list_stories()`, then `stories.load_story()` for each.
  4. **Iterate stories** in order:
     - **Skip completed**: if `story.status == "completed"`, continue to next.
     - **Mark in-progress**: call `update_story_status(status="in-progress")`.
     - **Update tracking**: set `current_story` to the story number.
     - **Compile context**: call `compile_story_context()`.
     - **Invoke Claude Code**: build invocation via `claude_cli.for_story(context, system_prompt=..., worktree=...)`, run via `subprocess.run(cmd.to_args(), capture_output=True, text=True, check=False)`.
     - **Handle Claude Code failure** (non-zero exit, not test failure): mark story `"blocked"` with stderr as `failure_log`, print error, break.
     - **Run tests**: `subprocess.run(["python", "-m", "pytest"], capture_output=True, text=True, check=False)`.
     - **On test failure — retry once**:
       - Compile retry context via `compile_retry_context(context, test_stderr)`.
       - Invoke Claude Code again with retry context.
       - Re-run tests.
       - If retry also fails: mark story `"blocked"` with test stderr as `failure_log`, print error, break.
     - **On success**:
       - Git commit: `subprocess.run(["git", "add", "-A"])` then `subprocess.run(["git", "commit", "-m", f"feat(issue-{issue}): {story.title}"])`.
       - Mark story `"completed"` via `update_story_status()`.
       - Print success message.
  5. **Clear tracking** — set `current_story=None` via `update_project_tracking()`.
  6. **Print summary** — number of stories completed, blocked, or skipped.

#### Internal helpers

- `_extract_story_number(story_path) -> int` — Extract the story number from a story filename (e.g. `issue-01-story-03.md` -> `3`). Uses regex `r"story-(\d+)\.md"`.

- `_run_tests(project_dir) -> subprocess.CompletedProcess` — Run `python -m pytest` and return the result. Separated for testability (single mock target).

- `_git_commit(message) -> subprocess.CompletedProcess` — Run `git add -A` then `git commit -m <message>`. Returns the commit result. Separated for testability.

#### Resumability invariants (from system design)

- **Completed stories are skipped**: `story.status == "completed"` → `continue`.
- **In-progress stories are re-run**: treated same as `"planned"` — re-invokes Claude Code from scratch.
- **Blocked stories stop the loop**: `story.status == "blocked"` → break (user must fix and reset to `"planned"`).
- **A story is only marked `"completed"` after tests pass AND git commit succeeds.** This makes the loop idempotent.

#### Imports (additional)

```python
import subprocess
from mantle.core import claude_cli
```

Added to existing imports from story 2.

#### Design decisions

- **`git add -A` before commit.** Claude Code may create new files. Using `-A` captures all changes. This is safe because each story runs in a worktree dedicated to this issue.
- **Claude Code non-zero exit is distinct from test failure.** Non-zero exit (crash, timeout, permission error) marks the story blocked immediately — no retry. Only test failures get the retry-with-feedback loop, because test failures are diagnosable from the error output.
- **Blocked stories stop the loop.** Stories within an issue build on each other. If story 2 fails, story 3 likely depends on story 2's output. Continuing would produce cascading failures.
- **State transition is conditional.** The orchestrator checks if already in `IMPLEMENTING` before transitioning. This supports resuming — re-running `implement` after a partial run shouldn't fail on the state transition.
- **`_run_tests` and `_git_commit` as helpers.** These are thin wrappers around `subprocess.run` but exist as separate functions so tests can mock them independently without mocking all subprocess calls.

## Tests

### tests/core/test_orchestrator.py (modify — add loop tests)

Tests use `tmp_path` with full `.mantle/` structure. Mock `subprocess.run` for Claude Code, pytest, and git. Mock `state.resolve_git_identity()`. Create 2-3 story files with known content.

#### implement — happy path

- **implement**: iterates stories in order and marks each completed
- **implement**: invokes Claude Code via subprocess for each story
- **implement**: runs pytest after each Claude Code invocation
- **implement**: creates git commit after successful tests with correct message format
- **implement**: commit message follows `feat(issue-{N}): {story title}` format
- **implement**: transitions state to IMPLEMENTING
- **implement**: sets current_issue in state tracking
- **implement**: sets current_story for each story being implemented
- **implement**: clears current_story after loop completes

#### implement — skip completed

- **implement**: skips stories with status "completed"
- **implement**: does not invoke Claude Code for completed stories
- **implement**: processes remaining non-completed stories after skipping

#### implement — retry on test failure

- **implement**: retries once when tests fail
- **implement**: passes error output to compile_retry_context
- **implement**: invokes Claude Code a second time with retry context
- **implement**: re-runs tests after retry
- **implement**: marks story completed if retry succeeds

#### implement — blocked on failure

- **implement**: marks story "blocked" when retry also fails
- **implement**: sets failure_log with test error output
- **implement**: stops loop after blocking a story (does not continue to next)
- **implement**: marks story "blocked" when Claude Code exits non-zero (no retry)

#### implement — resumability

- **implement**: skips completed stories on re-run
- **implement**: re-runs in-progress stories (treats as planned)
- **implement**: does not fail on state transition if already IMPLEMENTING
