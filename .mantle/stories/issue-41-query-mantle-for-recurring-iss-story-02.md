---
issue: 41
title: CLI command and prompt — expose show-patterns and /mantle:patterns
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want to run `/mantle:patterns` (and `mantle show-patterns` directly) to surface recurring themes from past learnings and confidence-delta trends per slice, so that I can spot friction points without manually re-reading every learning.

## Depends On

Story 1 — this story imports and calls `mantle.core.patterns.analyze_patterns` and `mantle.core.patterns.render_report`.

## Approach

Mirror the thin-CLI pattern used by other read-only mantle commands (see `cli/learning.py` for a reference `run_X` function; see `cli/main.py` function registration). The CLI resolves the project dir, calls core, and prints the rendered markdown — no formatting logic lives in CLI. A dedicated Claude Code prompt at `claude/commands/mantle/patterns.md` runs the CLI and presents the output unmodified, with a one-line follow-up offer to distill.

## Implementation

### src/mantle/cli/patterns.py (new file)

```python
\"\"\"Show-patterns command — surface recurring themes from learnings.\"\"\"

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import patterns

console = Console()


def run_show_patterns(*, project_dir: Path | None = None) -> None:
    \"\"\"Analyze vault patterns and print the markdown report.

    Args:
        project_dir: Project directory. Defaults to cwd.
    \"\"\"
    if project_dir is None:
        project_dir = Path.cwd()

    report = patterns.analyze_patterns(project_dir)
    console.print(patterns.render_report(report))
```

No error handling beyond what core raises — `analyze_patterns` tolerates an empty vault and returns a report whose rendered form tells the user to run retrospectives.

### src/mantle/cli/main.py (modify)

Register a `show-patterns` command adjacent to the other read-only `show-*` / `list-*` commands. Follow the same shape as nearby registrations (e.g., `list_skills_command`, `list_distillations_command`): a thin wrapper that calls `run_show_patterns`. No arguments.

```python
@app.command(name="show-patterns")
def show_patterns_command() -> None:
    \"\"\"Surface recurring themes and confidence trends from past learnings.\"\"\"
    patterns_cli.run_show_patterns()
```

Import the new module as `from mantle.cli import patterns as patterns_cli` (module alias to avoid shadowing `mantle.core.patterns` semantics at the call site).

### claude/commands/mantle/patterns.md (new file)

Short, focused prompt. No task-tracking scaffolding (this is a one-shot read-only command). Structure:

```markdown
---
description: Surface recurring themes and confidence trends from past learnings
allowed-tools: Bash(mantle show-patterns)
---

Surface recurring patterns from accumulated `.mantle/learnings/`.

## Step 1 — Run the analysis

Run:

    mantle show-patterns

Present the output verbatim to the user. Do not editorialise — the report is
already shaped.

## Step 2 — Offer a distillation

If the report shows three or more themes with at least two hits each, offer:

> This report groups {N} themes. Want to save an interpretation as a
> distillation so future planning sessions can start from it? Run
> `/mantle:distill patterns` if so.

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "patterns"

Keep the log under ~200 words.
```

#### Design decisions

- **No TaskCreate scaffolding in the prompt**: this is a one-shot read-only command like `/mantle:status`; step tracking adds noise.
- **Prompt restricts `allowed-tools` to the single CLI invocation**: keeps the surface narrow.
- **Module alias in `main.py`**: `cli.patterns` imported as `patterns_cli` avoids confusion with `core.patterns` at call sites within `main.py`.
- **No `--json` or `--topic` flag yet**: ACs don't require them. Add later if needed.

## Tests

### tests/cli/test_patterns.py (new file)

Use `tmp_path`. Build a minimal `.mantle/` fixture with two learnings and two issues. Invoke via cyclopts's in-process runner (consistent with other `tests/cli/test_*.py`).

- **test_show_patterns_prints_themes_and_trend_table**: fixture vault with one "testing" and one "worktree" learning → captured stdout contains `## Themes`, `### Testing`, `### Worktree`, and `| Slice |` header.
- **test_show_patterns_empty_vault_prints_guidance**: fixture vault with no learnings → stdout contains the "No learnings found" guidance string.
- **test_show_patterns_cli_entry_point_registered**: `App` dispatches `show-patterns` to `run_show_patterns` (assert via a light monkeypatch that `run_show_patterns` is called with the expected `project_dir`). Follows the pattern used in existing `test_main.py` registration checks if present; otherwise a smoke test that invoking the command exits 0.

### tests/test_workflows.py (modify, only if a workflow test exists for the full prompt → CLI wiring; otherwise skip)

Inspect the file. If there is a pattern like "invoke every registered command", add `show-patterns` to its inventory. Otherwise, no change.