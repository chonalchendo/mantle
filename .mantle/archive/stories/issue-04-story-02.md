---
issue: 4
title: CLI save-challenge command
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Add the `mantle save-challenge` CLI command that wraps `core.challenge.save_challenge()` with Rich output and error handling.

### src/mantle/cli/challenge.py

```python
"""Save-challenge command — persist a challenge session transcript."""
```

#### Function

- `run_save_challenge(*, transcript, project_dir=None) -> None` — Call `challenge.save_challenge()`, print Rich confirmation with filename, date, and author. Suggest `/mantle:design-product` as next step. Handle `IdeaNotFoundError` by printing warning and raising `SystemExit(1)`. Default `project_dir` to `Path.cwd()`.

#### Output format

```
Challenge saved to 2026-02-24-challenge.md

  Date:   2026-02-24
  Author: conal@example.com

  Next: run /mantle:design-product to define the product
```

On missing idea:
```
Warning: No idea.md found. Run /mantle:idea first.
```

### src/mantle/cli/main.py (modify)

Add `save-challenge` command with cyclopts parameters:

- `--transcript` (str, required) — Full challenge session transcript
- `--path` (Path | None, default None) — Project directory

Import `from mantle.cli import challenge` and delegate to `challenge.run_save_challenge()`.

## Tests

- **run_save_challenge**: prints "Challenge saved" on success
- **run_save_challenge**: prints filename in output
- **run_save_challenge**: prints next step mentioning `/mantle:design-product`
- **run_save_challenge**: warns and raises `SystemExit(1)` on missing idea
- **run_save_challenge**: defaults to cwd when `project_dir` is None
- **CLI wiring**: `mantle save-challenge --help` exits 0 and mentions "transcript"
