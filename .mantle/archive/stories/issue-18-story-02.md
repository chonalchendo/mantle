---
issue: 18
title: CLI save-research command
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Add the `mantle save-research` CLI command that wraps `core.research.save_research()` with Rich output and error handling. Follows the `cli/challenge.py` pattern.

### src/mantle/cli/research.py

```python
"""Save-research command — persist a research note."""
```

#### Function

- `run_save_research(*, focus, confidence, content, project_dir=None) -> None` — Call `research.save_research()`, print Rich confirmation with filename, date, author, focus, and confidence. Suggest next steps: another `/mantle:research` angle or `/mantle:design-product`. Handle `IdeaNotFoundError` by printing warning and raising `SystemExit(1)`. Handle `ValueError` (invalid focus or confidence) by printing error and raising `SystemExit(1)`. Default `project_dir` to `Path.cwd()`.

#### Output format

```
Research saved to 2026-02-25-feasibility.md

  Date:       2026-02-25
  Author:     conal@example.com
  Focus:      feasibility
  Confidence: 7/10

  Next: run /mantle:research for another angle
        or /mantle:design-product to define the product
```

On missing idea:
```
Warning: No idea.md found. Run /mantle:idea first.
```

On invalid focus/confidence:
```
Error: <ValueError message>
```

### src/mantle/cli/main.py (modify)

Add `save-research` command with cyclopts parameters:

- `--focus` (str, required) — Research focus angle
- `--confidence` (str, required) — Confidence rating (e.g. "7/10")
- `--content` (str, required) — Research note content
- `--path` (Path | None, default None) — Project directory

Import `from mantle.cli import research` and delegate to `research.run_save_research()`.

## Tests

### tests/cli/test_research.py

- **run_save_research**: prints "Research saved" on success
- **run_save_research**: prints filename in output
- **run_save_research**: prints focus and confidence in output
- **run_save_research**: prints next steps mentioning `/mantle:research` and `/mantle:design-product`
- **run_save_research**: warns and raises `SystemExit(1)` on missing idea
- **run_save_research**: prints error and raises `SystemExit(1)` on invalid focus
- **run_save_research**: defaults to cwd when `project_dir` is None
- **CLI wiring**: `mantle save-research --help` exits 0 and mentions "focus"
