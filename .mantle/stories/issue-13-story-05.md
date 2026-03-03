---
issue: 13
title: Replace subprocess orchestration with native Agent-based execution
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## User Story

As a developer, I want the implementation orchestrator to use Claude Code's native Agent tool instead of spawning `claude --print` subprocesses, so that each story implementation gets a fresh 200k context window with full tool access, no cold-start overhead, and the ability to interact with the user when blocked.

## Problem

The current approach shells out to `claude --print` via `subprocess.run()`. This is "Claude outside Claude" — the inner process has no access to the outer session's context, tools, MCP servers, or conversation history. It starts cold every time, re-reading CLAUDE.md and rediscovering the project. The outer process cannot observe progress, redirect, or intervene. The Python loop reimplements orchestration capabilities that Claude Code already provides natively through its Agent tool.

The GSD project (23.8k stars) demonstrates a proven alternative: a prompt-based orchestrator that spawns native Agent subagents with fresh 200k context windows. The orchestrator stays lean (~10-15% context) while each agent gets full tool access and context budget. No subprocess management, no environment mismatch risks, no cold starts.

## Approach

Rewrite `/mantle:implement` from a thin CLI trigger into the actual orchestrator. The command prompt reads stories, iterates in order, spawns Agent subagents per story (passing file paths, not compiled content), verifies tests, handles retries, commits, and updates story status via a CLI subcommand. Python utilities for state management stay in tested Python code, exposed through the CLI. The subprocess invocation builder (`claude_cli.py`) and Python implementation loop (`orchestrator.implement()`) are deleted.

This is story 5 of issue 13: a refactoring that replaces stories 3-4's subprocess approach while keeping stories 1-2's state management utilities.

## Implementation

### What gets deleted

- **`src/mantle/core/claude_cli.py`** — No longer needed. There are no subprocess invocations to build.
- **`tests/core/test_claude_cli.py`** — Tests for deleted module.
- **`src/mantle/cli/implement.py`** — Replaced by the prompt-based orchestrator. No Python CLI wrapper needed.
- **`tests/cli/test_implement.py`** — Tests for deleted module.
- **`orchestrator.implement()`** — The loop moves into the `implement.md` prompt.
- **`orchestrator.compile_story_context()`** — Agents read files themselves (pass paths, not content). This function only existed to build a single prompt string for `claude --print`.
- **`orchestrator.compile_retry_context()`** — The retry prompt is simple enough to express inline in `implement.md`.
- **`orchestrator._run_tests()`** — The prompt runs tests directly via Bash.
- **`orchestrator._git_commit()`** — The prompt commits directly via Bash.

### What stays

- **`orchestrator.update_story_status()`** — YAML frontmatter editing is fragile in prompts. This tested Python function reliably updates status and tags. Exposed via a new CLI subcommand.

### src/mantle/core/orchestrator.py (trim)

Remove everything except `update_story_status()`. The module docstring should be updated to reflect its new role as a story state management utility. Remove imports that are no longer needed (`claude_cli`, `system_design`, `subprocess`).

```python
"""Story state management for implementation orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mantle.core import stories, vault

if TYPE_CHECKING:
    from pathlib import Path


def update_story_status(
    project_dir: Path,
    *,
    issue: int,
    story_num: int,
    status: str,
    failure_log: str | None = None,
) -> None:
    """Update a story's status and optionally its failure_log."""
    ...  # existing implementation unchanged
```

### src/mantle/cli/main.py (modify)

Remove the `implement` command registration and `implement` import. Add an `update-story-status` subcommand that wraps `orchestrator.update_story_status()`.

```python
@app.command(name="update-story-status")
def update_story_status_command(
    issue: Annotated[
        int,
        Parameter(
            name="--issue",
            help="Parent issue number.",
        ),
    ],
    story: Annotated[
        int,
        Parameter(
            name="--story",
            help="Story number within the issue.",
        ),
    ],
    status: Annotated[
        str,
        Parameter(
            name="--status",
            help="New status: planned, in-progress, completed, blocked.",
        ),
    ],
    failure_log: Annotated[
        str | None,
        Parameter(
            name="--failure-log",
            help="Error details (when marking blocked).",
        ),
    ] = None,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Update a story's status."""
    project_dir = path or Path.cwd()
    orchestrator.update_story_status(
        project_dir,
        issue=issue,
        story_num=story,
        status=status,
        failure_log=failure_log,
    )
```

Follows the same pattern as `update-bug-status`.

### claude/commands/mantle/implement.md (rewrite)

This becomes the full orchestrator. It replaces the Python loop with Claude Code's native capabilities.

```markdown
You are the implementation orchestrator for a Mantle project.

**Step 1 — Check prerequisites**

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell user to run `mantle init`)
- Status is `planning` or `implementing`
- If status is earlier, tell user the current status and suggest the appropriate next command

**Step 2 — Select issue**

Ask the user which issue to implement. Read `.mantle/issues/` to show available issues.
If the user provided an issue number with the command, use that.

Display:
> **Issue {NN}**: {title}
> **Stories**: {story_count} planned
> **Status**: {issue status}

Confirm with the user before proceeding.

**Step 3 — Load stories**

Read all story files for the issue from `.mantle/stories/issue-{NN}-story-*.md`.
Sort by story number. For each story, note its status.

- **completed** → skip (print "Skipping story {N} — already completed")
- **blocked** → stop (print "Story {N} is blocked — stopping". Show the failure_log)
- **planned** or **in-progress** → implement (continue to step 4)

**Step 4 — Implement each story**

For each story to implement, in order:

4a. Mark in-progress:
```bash
mantle update-story-status --issue {N} --story {M} --status in-progress
```

4b. Spawn an Agent to implement the story. Use `subagent_type: "smart"`. Pass file paths — the agent reads files itself with its fresh context window.

Prompt:
> Implement the following story. Follow all project conventions from CLAUDE.md.
> Run tests after implementation and fix any failures.
>
> Read these files for context:
> - `.mantle/system-design.md` (if it exists — skip if not found)
> - `.mantle/issues/issue-{NN}.md`
> - `.mantle/stories/issue-{NN}-story-{MM}.md`
>
> After implementing, run `uv run pytest` and fix any test failures before finishing.

4c. After the agent returns, verify tests pass:
```bash
uv run pytest
```

4d. If tests fail — retry once:
- Capture the test output
- Spawn a new Agent with the test errors and instructions to fix:

> The previous implementation attempt for this story failed tests.
> Here is the error output:
>
> ```
> {test output}
> ```
>
> Read the story at `.mantle/stories/issue-{NN}-story-{MM}.md` and the existing code.
> Diagnose the failure, fix the issues, and ensure all tests pass.
> Run `uv run pytest` to verify.

- Re-run tests after the retry agent returns
- If still failing:
```bash
mantle update-story-status --issue {N} --story {M} --status blocked --failure-log "{error summary}"
```
Print "Story {M} blocked: tests failed after retry" and stop the loop.

4e. On success — commit and mark completed:
```bash
git add -A && git commit -m "feat(issue-{N}): {story title}"
mantle update-story-status --issue {N} --story {M} --status completed
```
Print "Story {M} ({title}) completed" and continue to the next story.

**Step 5 — Report results**

After the loop completes, summarise:
- Stories completed
- Stories skipped (already completed)
- Stories blocked (if any) — show the failure_log
- Next steps (fix blocked story and re-run, or proceed to `/mantle:verify`)
```

#### Design decisions

- **Prompt-based orchestration, not Python loop.** Claude Code's Agent tool provides fresh 200k context windows with full tool access. `subprocess.run(claude --print)` starts cold, has no tool access, cannot interact with the user, and cannot access MCP servers. The prompt-based approach is both simpler and more capable.
- **Pass paths, not content.** Following GSD's pattern: "Pass paths only — agents read files themselves." This keeps the orchestrator lean and gives agents maximum context budget for implementation.
- **`subagent_type: "smart"` for story agents.** The `smart` agent understands intent and chooses the right approach — read code, plan if needed, then implement. This is better than `implementer` (single-file focused) for stories that may span multiple files.
- **State management stays in Python.** YAML frontmatter editing requires matching the Pydantic schema and updating tags atomically. The `update-story-status` CLI subcommand uses tested Python code. This follows the existing `update-bug-status` pattern.
- **`compile_story_context()` deleted.** No longer needed — agents read files directly. The context compilation existed only to build a monolithic prompt string for `claude --print`.
- **`claude_cli.py` deleted entirely.** No subprocess invocations means no invocation builder. If subprocess orchestration is ever needed for CI/CD, it can be rebuilt. YAGNI until then.
- **Retry is inline, not a utility function.** `compile_retry_context()` was 10 lines that concatenated strings. The implement.md prompt expresses this inline more naturally than calling a Python utility via Bash.
- **No state.md transition from the prompt.** The prompt reads `state.md` to check prerequisites but does not transition state itself. State transitions are a future concern — the story status tracking is sufficient for resumability (skip completed, stop on blocked).

## Tests

### tests/core/test_orchestrator.py (trim)

Remove all tests for deleted functions: `compile_story_context`, `compile_retry_context`, `implement` (happy path, skip completed, retry, blocked, resumability). Keep tests for `update_story_status`.

Remaining tests:
- **update_story_status**: updates status in frontmatter
- **update_story_status**: updates tags to reflect new status
- **update_story_status**: sets failure_log when provided
- **update_story_status**: clears failure_log when not provided
- **update_story_status**: preserves story body content

### tests/cli/test_main.py or tests/cli/test_orchestrator.py (new or modify)

Test the `update-story-status` CLI subcommand:
- **update-story-status**: calls `orchestrator.update_story_status` with correct args
- **update-story-status**: defaults project_dir to cwd when --path not provided
- **update-story-status**: passes failure_log when provided
- **update-story-status**: registered in app as "update-story-status"

### Verification (no automated tests)

- The `implement.md` file exists at `claude/commands/mantle/implement.md`
- Running `/mantle:implement` in a Claude Code session spawns Agent subagents per story
- Agents receive file paths and read context themselves
- Story statuses are updated correctly via `mantle update-story-status`
- Tests are run after each agent and retried once on failure
- Atomic git commits are created per successful story
