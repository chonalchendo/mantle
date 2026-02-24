---
issue: 3
title: CLI save-idea command
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Add the `mantle save-idea` CLI command that wraps `core.idea.create_idea()` with Rich output and error handling.

### src/mantle/cli/idea.py

```python
"""Save-idea command — capture a structured idea in .mantle/idea.md."""
```

#### Function

- `run_save_idea(*, hypothesis, target_user, success_criteria, overwrite=False, project_dir=None) -> None` — Call `idea.create_idea()`, print Rich confirmation with hypothesis and criteria count, suggest `/mantle:challenge` as next step. Handle `IdeaExistsError` by printing warning and raising `SystemExit(1)`. Default `project_dir` to `Path.cwd()`.

#### Output format

```
Idea captured in .mantle/idea.md

  Hypothesis: <hypothesis>
  Criteria:   <count>

  Next: run /mantle:challenge to stress-test your idea
```

On existing idea:
```
Warning: idea.md already exists. Use --overwrite to replace.
```

### src/mantle/cli/main.py (modify)

Add `save-idea` command with cyclopts parameters:

- `--hypothesis` (str, required) — Core belief or value proposition
- `--target-user` (str, required) — Who this idea is for
- `--success-criteria` (tuple[str, ...], required, repeatable) — Measurable outcomes
- `--overwrite` (bool, default False) — Replace existing idea.md
- `--path` (Path | None, default None) — Project directory

Import `from mantle.cli import idea` and delegate to `idea.run_save_idea()`.

## Tests

- **run_save_idea**: prints "Idea captured" on success
- **run_save_idea**: prints hypothesis in output
- **run_save_idea**: prints criteria count in output
- **run_save_idea**: prints next step mentioning `/mantle:challenge`
- **run_save_idea**: warns and raises `SystemExit(1)` on existing idea
- **run_save_idea**: `overwrite=True` succeeds when idea exists
- **run_save_idea**: defaults to cwd when `project_dir` is None
- **CLI wiring**: `mantle save-idea --help` exits 0 and mentions "hypothesis"
