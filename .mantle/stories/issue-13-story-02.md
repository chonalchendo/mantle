---
issue: 13
title: Core orchestrator — context compilation and story state management
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## User Story

As a developer building the implementation loop, I want functions to compile story context for Claude Code and update story status so that the orchestrator has clean building blocks for each step of the loop.

## Approach

Create `core/orchestrator.py` with the context-compilation and state-management functions that the implementation loop (story 3) depends on. `compile_story_context()` reads vault files and assembles a prompt. `compile_retry_context()` wraps a failed attempt with error output. `update_story_status()` mutates story frontmatter. This is story 2 of 4: the building blocks the loop calls into.

## Implementation

### src/mantle/core/orchestrator.py (new file)

```python
"""Implementation orchestration loop — story iteration, Claude Code invocation, retry, git commits."""
```

#### Context compilation

- `compile_story_context(project_dir, *, issue, story_path) -> str` — Read vault state and assemble the implementation prompt for a single story. Reads and concatenates:
  1. `system-design.md` body (project architecture and conventions)
  2. The issue file (`issues/issue-NN.md`) — acceptance criteria, what to build
  3. The story file (from `story_path`) — full implementation spec and test spec
  4. A preamble instructing Claude Code to implement the story, run tests, and follow project conventions from CLAUDE.md

  Returns a single string suitable as the `prompt` argument to `claude_cli.for_story()`.

  The function reads files via `vault.read_note()` for frontmattered files and plain `Path.read_text()` for the system design body. If `system-design.md` does not exist, it is omitted (not all projects have one).

- `compile_retry_context(original_context, error_output) -> str` — Wrap the original story context with test failure output for a retry attempt. Prepends a section explaining that the previous implementation attempt failed, includes the test error output, and re-includes the original context. The retry prompt instructs Claude Code to read the existing code, diagnose the failure, fix it, and re-run the tests.

  Format:
  ```
  ## Previous Attempt Failed

  The previous implementation attempt for this story failed tests. Here is the error output:

  ```
  {error_output}
  ```

  Please read the existing code, diagnose the failure, fix the issues, and ensure all tests pass.

  ---

  {original_context}
  ```

#### Story state management

- `update_story_status(project_dir, *, issue, story_num, status, failure_log=None) -> None` — Read the story file, update its `status` and optionally `failure_log` in the frontmatter, and write it back. Uses `stories.load_story()` to read and `vault.write_note()` to write. Updates the `tags` tuple to reflect the new status (replaces `status/planned` with `status/{new_status}`).

  Valid status values: `"planned"`, `"in-progress"`, `"completed"`, `"blocked"`.

- `update_project_tracking(project_dir, *, issue, story_num=None) -> None` — Update `state.md` tracking fields (`current_issue`, `current_story`) via `state.update_tracking()`. When `story_num` is None, clears the `current_story` field (used at end of loop).

#### Imports

```python
from mantle.core import issues, state, stories, vault
```

#### Design decisions

- **Context compilation is string concatenation, not template rendering.** The orchestrator's context is assembled per-story at runtime, not compiled via Jinja2. Jinja2 is for the compiled commands (status, resume). The story context is a straightforward concatenation of vault files with a preamble — no conditional logic, no loops.
- **`compile_retry_context` wraps, not replaces.** The retry prompt includes both the error output AND the original context. Claude Code needs the full story spec to understand what it was trying to build, plus the error details to diagnose the failure.
- **`update_story_status` updates tags.** The status tag in frontmatter (`status/planned`, `status/in-progress`, etc.) is kept in sync with the `status` field. This maintains consistency with how issues and other notes track status via tags.
- **`update_project_tracking` delegates to `state.update_tracking()`.** The orchestrator doesn't directly manipulate `state.md` — it uses the existing `state` module's public API. This keeps the state machine logic centralized.
- **No state transition in this story.** The `PLANNING -> IMPLEMENTING` transition happens in story 3's `implement()` function, not in these building blocks.

## Tests

### tests/core/test_orchestrator.py (new file)

Tests use `tmp_path` with `.mantle/` structure: `state.md`, `system-design.md`, `issues/issue-01.md`, `stories/issue-01-story-01.md`. Mock `state.resolve_git_identity()` to return a fixed email.

#### compile_story_context

- **compile_story_context**: returns string containing the story body content
- **compile_story_context**: returns string containing the issue body content
- **compile_story_context**: returns string containing the system design content
- **compile_story_context**: includes implementation preamble instructing Claude Code
- **compile_story_context**: omits system design gracefully when file doesn't exist
- **compile_story_context**: raises FileNotFoundError when story path doesn't exist

#### compile_retry_context

- **compile_retry_context**: prepends error output section before original context
- **compile_retry_context**: includes the full original context unchanged
- **compile_retry_context**: includes retry instructions (diagnose, fix, re-run tests)

#### update_story_status

- **update_story_status**: changes status field in frontmatter
- **update_story_status**: round-trips correctly (load after update reflects new status)
- **update_story_status**: sets failure_log when provided
- **update_story_status**: leaves failure_log as None when not provided
- **update_story_status**: updates tags to reflect new status
- **update_story_status**: handles transition from "planned" to "in-progress"
- **update_story_status**: handles transition from "in-progress" to "completed"
- **update_story_status**: handles transition from "in-progress" to "blocked" with failure_log

#### update_project_tracking

- **update_project_tracking**: sets current_issue and current_story in state.md
- **update_project_tracking**: clears current_story when story_num is None
