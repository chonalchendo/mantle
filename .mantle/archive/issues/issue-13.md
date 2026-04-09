---
title: Implementation orchestration loop (/mantle:implement)
status: completed
slice:
- core
- claude-code
- tests
story_count: 5
verification: null
blocked_by: []
tags:
- type/issue
- status/completed
---

## Parent PRD

product-design.md, system-design.md

## What to build

The Python orchestration loop triggered by `/mantle:implement`. For a given issue, the loop iterates over stories, compiles context for each, invokes Claude Code as a subprocess with a fresh context window, runs tests, retries once with error feedback on failure, creates atomic git commits, and updates vault state. Stories already marked "completed" are skipped on re-run.

This includes:
- `src/mantle/core/orchestrator.py` — the implementation loop: story iteration, context compilation per story, Claude Code subprocess invocation (`claude --print`), test execution, retry-with-feedback, atomic git commits, state updates (in-progress → completed or blocked)
- `claude/commands/mantle/implement.md` — static command that triggers the Python orchestration loop via `mantle implement --issue N`
- Context compilation for each story: project state + system design + current issue + current story + relevant skills (budgeted)
- Retry logic: on test failure, compile retry context with error output, invoke Claude Code once more, re-run tests; if retry fails, mark story "blocked" with failure_log and stop

## Acceptance criteria

- [ ] `/mantle:implement` triggers `mantle implement --issue N` which runs the Python orchestration loop
- [ ] The loop iterates over stories for the specified issue in order
- [ ] Each story gets a fresh Claude Code invocation with compiled context (`claude --print`)
- [ ] Tests are run after each story implementation (`python -m pytest`)
- [ ] On test failure, error output is fed back to Claude Code for one retry attempt
- [ ] If retry also fails, the story is marked "blocked" with failure details in `failure_log`
- [ ] The loop stops on a blocked story (does not continue to next story)
- [ ] Each successful story results in an atomic git commit with message format `feat(issue-{N}): {story title}`
- [ ] Story status is updated: planned → in-progress → completed (or blocked)
- [ ] Stories already marked "completed" are skipped on re-run
- [ ] Project state (state.md) is updated with current_issue and current_story
- [ ] Tests mock `subprocess.run` for Claude Code, pytest, and git; verify loop logic, retry behaviour, state transitions, and skip-completed

## Implementation notes

- Create a dataclass or enum in `core/` that codifies the Claude Code CLI flags (e.g. `--print`, `--allowedTools`, `--worktree`, `--system-prompt`, `--max-budget-usd`, `--no-session-persistence`, `--model`, `--permission-mode`, `--output-format`). The orchestrator should build subprocess invocations from this structured reference rather than hardcoding flag strings directly in `subprocess.run()` calls. This keeps the CLI contract in one place and makes it easy to update if Claude Code's flags change. See the "Claude Code Flags Reference" table in `system-design.md` for the full list.

## Blocked by

- Blocked by issue-12 (needs stories to implement)

## User stories addressed

- User story 22: Python orchestration loop with fresh context per story
- User story 23: Atomic git commit per completed story
- User story 24: Auto-skip completed stories on re-run
- User story 25: Retry once with error feedback on test failure
- User story 26: Mark story "blocked" with failure details if retry fails
