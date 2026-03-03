---
issue: 13
title: CLI implement command and /mantle:implement static command
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## User Story

As a developer, I want `/mantle:implement` to trigger `mantle implement --issue N` so that I can start the implementation loop from a Claude Code session with a single command.

## Approach

Add `mantle implement` as a CLI command following the same wrapper pattern as `save-issue` and `save-story` — a thin function in `cli/implement.py` that calls `core/orchestrator.implement()` from story 3, with Rich-formatted progress output. Create the static command `implement.md` that triggers it. Register the command in `main.py`. This is story 4 of 4: the user-facing layer.

## Implementation

### src/mantle/cli/implement.py (new file)

```python
"""CLI wrapper for implementation orchestration."""
```

#### Function

- `run_implement(*, issue, project_dir=None) -> None` — Resolve `project_dir` (default to `Path.cwd()`), call `orchestrator.implement(project_dir, issue=issue)`. Wrap the call with Rich console output:
  - Print header: `"Implementing issue {issue}..."`
  - Catch and display any `InvalidTransitionError` with a user-friendly message suggesting the correct workflow state.
  - Catch and display `FileNotFoundError` for missing `.mantle/` or issue files.
  - Let the orchestrator's own print statements show per-story progress.

#### Imports

```python
from mantle.core import orchestrator
```

### src/mantle/cli/main.py (modify)

#### Imports

Add `implement` to the CLI imports:

```python
from mantle.cli import (
    ...
    implement,
    ...
)
```

#### New command

Register `implement` command:

```python
@app.command(name="implement")
def implement_command(
    issue: Annotated[int, Parameter(name="--issue", help="Issue number to implement.")],
    path: Annotated[Path | None, Parameter(name="--path", help="Project directory. Defaults to cwd.")] = None,
) -> None:
    """Run the implementation loop for an issue."""
    implement.run_implement(issue=issue, project_dir=path)
```

### claude/commands/mantle/implement.md (new file)

Static command prompt that triggers the Python orchestration loop.

#### Content

```markdown
You are starting the implementation phase for a Mantle project.

**Step 1 — Check prerequisites**

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell user to run `mantle init`)
- Status is `planning` or `implementing` (valid states for implementation)
- If status is earlier, tell user the current status and suggest the appropriate next command

**Step 2 — Select issue**

Ask the user which issue to implement. Read `.mantle/issues/` to show available issues.
If the user provided an issue number with the command, use that.

Display:
> **Issue {NN}**: {title}
> **Stories**: {story_count} planned
> **Status**: {issue status}

Confirm with the user before proceeding.

**Step 3 — Run the orchestrator**

Execute:

\```bash
mantle implement --issue {N}
\```

This triggers the Python orchestration loop which:
1. Iterates over stories in order
2. Invokes Claude Code per story with compiled context
3. Runs tests after each story
4. Retries once with error feedback on test failure
5. Creates atomic git commits per story
6. Stops on blocked stories

**Step 4 — Report results**

After the loop completes, summarise:
- Stories completed
- Stories blocked (if any) — show the failure_log
- Next steps (fix blocked story and re-run, or proceed to `/mantle:verify`)
```

#### Persona

Orchestrator that delegates implementation to the Python loop. Does not implement code itself — it triggers `mantle implement` and reports results.

#### Tone

Brief, operational. The heavy lifting is in the Python loop, not this command.

#### Design decisions

- **Static command, not compiled.** The implement command reads issue number from the user and delegates to the CLI. No vault state needs to be baked in at compile time.
- **Minimal logic in the command prompt.** The command's job is to confirm the issue with the user and invoke `mantle implement`. All orchestration logic lives in Python (core/orchestrator.py).
- **Prerequisite check in the prompt.** The prompt verifies state before invoking the CLI, matching the pattern from `plan-issues.md` and `plan-stories.md`. This gives a friendlier error than a Python traceback.

## Tests

### tests/cli/test_implement.py (new file)

Tests use `tmp_path` with `.mantle/` structure including state.md at `planning` status and an issue file. Mock `orchestrator.implement` to avoid subprocess calls.

- **run_implement**: calls `orchestrator.implement` with correct issue number
- **run_implement**: defaults project_dir to cwd when None
- **run_implement**: handles InvalidTransitionError with user-friendly message
- **run_implement**: handles FileNotFoundError with user-friendly message
- **implement_command**: registered in app as "implement"

### Verification (no automated tests)

- The `implement.md` file exists at `claude/commands/mantle/implement.md`
- Running `mantle install` copies `implement.md` to `~/.claude/commands/mantle/`
