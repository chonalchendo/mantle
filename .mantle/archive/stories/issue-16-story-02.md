---
issue: 16
title: CLI wiring + Claude Code review command
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want to run `/mantle:review` in Claude Code and be guided through a checklist-based review of acceptance criteria with pass/fail from verification, so that I have a final quality gate before marking work as done.

## Approach

Follows the verify command pattern — a static markdown command (`claude/commands/mantle/review.md`) that orchestrates the interactive review session, calling `mantle` CLI subcommands for status transitions. CLI module (`cli/review.py`) provides thin wrappers for `transition-issue-approved` and `transition-issue-implementing` subcommands, wired through `cli/main.py`.

## Implementation

### src/mantle/cli/review.py (new file)

- `run_transition_to_approved(*, issue: int, project_dir: Path | None) -> None`: Calls `issues.transition_to_approved()`, prints confirmation with rich. Catches `InvalidTransitionError` and exits with error message. Follows pattern of `cli/verify.py:run_transition_to_verified`.
- `run_transition_to_implementing(*, issue: int, project_dir: Path | None) -> None`: Calls `issues.transition_to_implementing()`, prints confirmation. Same error handling pattern.

### src/mantle/cli/main.py (modify)

- Import `from mantle.cli import review`
- Add `@app.command(name="transition-issue-approved")` wired to `review.run_transition_to_approved`
- Add `@app.command(name="transition-issue-implementing")` wired to `review.run_transition_to_implementing`
- Both follow the exact parameter pattern of `transition-issue-verified` (--issue, --path)

### claude/commands/mantle/review.md (new file)

- Static command with `argument-hint: [issue-number]` frontmatter
- Step 1: Check prerequisites — read `.mantle/state.md`, verify project exists
- Step 2: Select issue — use `$ARGUMENTS` or ask user. Prefer issues with `verified` status.
- Step 3: Load verification results — read the issue file, extract acceptance criteria, check pass/fail from most recent `/mantle:verify` run (read issue status and criteria)
- Step 4: Present review checklist — display each criterion with pass/fail from verification, ask user to mark each as approved or needs-changes with optional comments
- Step 5: Collect feedback — for each criterion, prompt user for approved/needs-changes + comment
- Step 6: Handle outcome:
  - All approved: run `mantle transition-issue-approved --issue <N>`, tell user issue is approved
  - Any needs-changes: run `mantle transition-issue-implementing --issue <N>`, list items needing changes with comments, suggest next steps

#### Design decisions

- **Static command, not compiled**: The review command doesn't need vault state compilation — it reads issue files directly during the session. Matches the verify command pattern.
- **Two separate CLI subcommands**: One for approved, one for implementing. Follows the one-command-one-job principle and matches the transition-issue-verified pattern.
- **Interactive checklist in the prompt**: The Claude Code command guides the human through each criterion one at a time. This is the review UX — AI presents, human decides.

## Tests

### tests/cli/test_review.py (new file)

- **test_transition_to_approved_success**: Calls run function on verified issue, check output contains confirmation
- **test_transition_to_approved_invalid_status**: Non-verified issue prints error, raises SystemExit
- **test_transition_to_implementing_success**: Calls run function on verified issue, check output
- **test_transition_to_implementing_invalid_status**: Non-implementing-eligible issue prints error