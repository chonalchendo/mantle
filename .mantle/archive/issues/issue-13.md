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
skills_required: []
tags:
- type/issue
- status/completed
acceptance_criteria:
- id: ac-01
  text: '`/mantle:implement` triggers `mantle implement --issue N` which runs the
    Python orchestration loop'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: The loop iterates over stories for the specified issue in order
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Each story gets a fresh Claude Code invocation with compiled context (`claude
    --print`)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Tests are run after each story implementation (`python -m pytest`)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: On test failure, error output is fed back to Claude Code for one retry attempt
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: If retry also fails, the story is marked "blocked" with failure details in
    `failure_log`
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: The loop stops on a blocked story (does not continue to next story)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: 'Each successful story results in an atomic git commit with message format
    `feat(issue-{N}): {story title}`'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-09
  text: 'Story status is updated: planned → in-progress → completed (or blocked)'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-10
  text: Stories already marked "completed" are skipped on re-run
  passes: false
  waived: false
  waiver_reason: null
- id: ac-11
  text: Project state (state.md) is updated with current_issue and current_story
  passes: false
  waived: false
  waiver_reason: null
- id: ac-12
  text: Tests mock `subprocess.run` for Claude Code, pytest, and git; verify loop
    logic, retry behaviour, state transitions, and skip-completed
  passes: false
  waived: false
  waiver_reason: null
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

- [ ] ac-01: `/mantle:implement` triggers `mantle implement --issue N` which runs the Python orchestration loop
- [ ] ac-02: The loop iterates over stories for the specified issue in order
- [ ] ac-03: Each story gets a fresh Claude Code invocation with compiled context (`claude --print`)
- [ ] ac-04: Tests are run after each story implementation (`python -m pytest`)
- [ ] ac-05: On test failure, error output is fed back to Claude Code for one retry attempt
- [ ] ac-06: If retry also fails, the story is marked "blocked" with failure details in `failure_log`
- [ ] ac-07: The loop stops on a blocked story (does not continue to next story)
- [ ] ac-08: Each successful story results in an atomic git commit with message format `feat(issue-{N}): {story title}`
- [ ] ac-09: Story status is updated: planned → in-progress → completed (or blocked)
- [ ] ac-10: Stories already marked "completed" are skipped on re-run
- [ ] ac-11: Project state (state.md) is updated with current_issue and current_story
- [ ] ac-12: Tests mock `subprocess.run` for Claude Code, pytest, and git; verify loop logic, retry behaviour, state transitions, and skip-completed

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
