---
issue: 19
title: CLI save-adoption command
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Add the `mantle save-adoption` CLI command that wraps `core.adopt.save_adoption()` with Rich output and error handling. This is called by the `/mantle:adopt` Claude command after the interactive synthesis session.

### src/mantle/cli/adopt.py

```python
"""Save-adoption command — write adopted design artifacts to .mantle/."""
```

#### Function

- `run_save_adoption(*, vision, principles, building_blocks, prior_art, composition, target_users, success_metrics, system_design_content, overwrite=False, project_dir=None) -> None` — Call `adopt.save_adoption()`, print Rich confirmation with vision and artifact summary, suggest `/mantle:plan-issues` as next step. Handle `AdoptionExistsError` by printing warning and raising `SystemExit(1)`. Handle `InvalidTransitionError` by printing current state and raising `SystemExit(1)`. Default `project_dir` to `Path.cwd()`.

#### Output format

```
Adoption complete — design artifacts saved to .mantle/

  Vision:       <vision>
  Features:     <building_block count> building blocks
  System design: saved

  Next: run /mantle:plan-issues to break down the work
```

On existing docs:
```
Warning: design documents already exist. Use --overwrite to replace.
```

On wrong state:
```
Error: project is at '<status>' — adoption requires 'idea' status.
Run mantle init to start a new project, then /mantle:adopt.
```

### src/mantle/cli/main.py (modify)

Add `save-adoption` command with cyclopts parameters:

- `--vision` (str, required)
- `--principles` (tuple[str, ...], required, repeatable)
- `--building-blocks` (tuple[str, ...], required, repeatable)
- `--prior-art` (tuple[str, ...], required, repeatable)
- `--composition` (str, required)
- `--target-users` (str, required)
- `--success-metrics` (tuple[str, ...], required, repeatable)
- `--system-design-content` (str, required)
- `--overwrite` (bool, default False)
- `--path` (Path | None, default None)

Import `from mantle.cli import adopt` and delegate to `adopt.run_save_adoption`.

## Tests

### tests/cli/test_adopt.py

- **run_save_adoption**: prints "Adoption complete" on success
- **run_save_adoption**: prints vision in output
- **run_save_adoption**: prints building block count in output
- **run_save_adoption**: prints next step mentioning `/mantle:plan-issues`
- **run_save_adoption**: warns and raises `SystemExit(1)` on existing docs
- **run_save_adoption**: errors and raises `SystemExit(1)` on wrong state
- **run_save_adoption**: `overwrite=True` succeeds when docs exist
- **run_save_adoption**: defaults to cwd when `project_dir` is None
- **CLI wiring**: `mantle save-adoption --help` exits 0 and mentions "vision"
