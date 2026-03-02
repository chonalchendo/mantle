---
issue: 17
title: CLI save-skill command
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Add the `mantle save-skill` CLI command that wraps `core.skills.create_skill()` with Rich output and error handling. The `--content` parameter carries the authored skill knowledge and `--description` carries the activation summary. Follows the `cli/idea.py` pattern.

### src/mantle/cli/skills.py

```python
"""Save-skill command — create or update a skill node in the personal vault."""
```

#### Function

- `run_save_skill(*, name, description, proficiency, content, related_skills=(), projects=(), overwrite=False, project_dir=None) -> None` — Call `skills.create_skill()`, print Rich confirmation with skill name, description, and vault path. Handle `SkillExistsError` by printing warning and raising `SystemExit(1)`. Handle `VaultNotConfiguredError` by printing error and raising `SystemExit(1)`. Handle `ValueError` (bad proficiency) by printing error and raising `SystemExit(1)`. Default `project_dir` to `Path.cwd()`.

#### Output format

```
Skill saved to <vault>/skills/<slug>.md

  Name:        <name>
  Description: <description>
  Proficiency: <proficiency>

  Next: run /mantle:add-skill to track more skills
```

On existing:
```
Warning: <slug>.md already exists. Use --overwrite to replace.
```

On vault not configured:
```
Error: Personal vault not configured. Run mantle init-vault <path> first.
```

On bad proficiency:
```
Error: Invalid proficiency format. Use "N/10" (e.g. "7/10").
```

### src/mantle/cli/main.py (modify)

Add `save-skill` command with cyclopts parameters:

- `--name` (str, required)
- `--description` (str, required) — what this skill covers + when it's relevant
- `--proficiency` (str, required)
- `--content` (str, required) — the authored skill knowledge
- `--related-skills` (tuple[str, ...], default empty, repeatable)
- `--projects` (tuple[str, ...], default empty, repeatable)
- `--overwrite` (bool, default False)
- `--path` (Path | None, default None)

Import `from mantle.cli import skills` and delegate to `skills.run_save_skill()`.

## Tests

### tests/cli/test_skills.py

- **run_save_skill**: prints "Skill saved" on success
- **run_save_skill**: prints skill name in output
- **run_save_skill**: prints description in output
- **run_save_skill**: prints proficiency in output
- **run_save_skill**: prints next step mentioning `/mantle:add-skill`
- **run_save_skill**: warns and raises `SystemExit(1)` on existing
- **run_save_skill**: `overwrite=True` succeeds when exists
- **run_save_skill**: errors and raises `SystemExit(1)` when vault not configured
- **run_save_skill**: errors and raises `SystemExit(1)` on bad proficiency
- **run_save_skill**: defaults to cwd when `project_dir` is None
- **CLI wiring**: `mantle save-skill --help` exits 0 and mentions "name", "description", and "content"
