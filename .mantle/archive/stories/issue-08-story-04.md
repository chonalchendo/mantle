---
issue: 8
title: CLI compile commands (cli/compile.py + main.py)
status: done
failure_log: null
tags:
  - type/story
  - status/done
---

## Implementation

Add the `mantle compile` and `mantle compile --if-stale` CLI commands that wrap `core.compiler.compile()` and `core.compiler.compile_if_stale()` with Rich output.

### src/mantle/cli/compile.py

```python
"""Compile command — render vault context into Claude Code commands."""
```

#### Function

- `run_compile(*, if_stale: bool = False, project_dir: Path | None = None, target_dir: Path | None = None) -> None` — Default `project_dir` to `Path.cwd()`. If `if_stale` is True, call `compiler.compile_if_stale()` — if it returns `None`, print "Already up to date." and return. Otherwise (or if `if_stale` is False), call `compiler.compile()`. Print Rich confirmation with count of compiled templates. Handle `FileNotFoundError` (no `.mantle/` or `state.md`) by printing error and raising `SystemExit(1)`.

#### Output format

On compile:
```
Compiled 1 template(s) to ~/.claude/commands/mantle/

  - status.md

  Commands are ready. Run /mantle:status in Claude Code.
```

On up to date:
```
Already up to date — no recompilation needed.
```

On missing project:
```
Error: no .mantle/ directory found. Run mantle init first.
```

### src/mantle/cli/main.py (modify)

Add `compile` command with cyclopts parameters:

- `--if-stale` (bool, default False) — Only recompile when source files have changed.
- `--path` (Path | None, default None) — Project directory. Defaults to cwd.
- `--target` (Path | None, default None) — Output directory. Defaults to `~/.claude/commands/mantle/`.

Import `from mantle.cli import compile as compile_cmd` (avoid shadowing built-in `compile`). Delegate to `compile_cmd.run_compile`.

#### Import naming

```python
from mantle.cli import (
    ...
    compile as compile_cmd,
    ...
)
```

Use `compile_cmd` alias to avoid shadowing the `compile` built-in. The function name stays `compile_command` for the cyclopts decorator.

### Design decisions

- **Single command with `--if-stale` flag, not two separate commands.** `mantle compile` always recompiles. `mantle compile --if-stale` is the staleness-aware variant for hooks. One command, one job — the flag modifies behaviour, it doesn't change the job.
- **`--target` is optional and rarely used.** Default `~/.claude/commands/mantle/` is correct for all normal usage. The flag exists for testing and unusual setups.
- **Import alias for `compile`.** Python's `compile` built-in is used by the language itself. Importing the CLI module as `compile_cmd` avoids subtle shadowing bugs.

## Tests

### tests/cli/test_compile.py

Test fixtures create a `tmp_path` with `.mantle/` and `state.md`. Use a temporary target directory to avoid writing to real `~/.claude/`.

- **run_compile**: prints "Compiled" with template count on success
- **run_compile**: prints compiled template names in output
- **run_compile**: with `if_stale=True`, prints "Already up to date" when unchanged
- **run_compile**: with `if_stale=True`, compiles when sources changed
- **run_compile**: errors and raises `SystemExit(1)` when `.mantle/` missing
- **run_compile**: defaults to cwd when `project_dir` is None
- **CLI wiring**: `mantle compile --help` exits 0 and mentions "if-stale"
