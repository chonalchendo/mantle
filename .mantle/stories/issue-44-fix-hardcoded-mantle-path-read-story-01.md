---
issue: 44
title: Add mantle where CLI command
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle developer building a Claude Code prompt, I want a single shell call that returns the absolute path to the project's resolved `.mantle/` directory so that prompts work identically in local and global storage modes.

## Depends On

None — independent (foundation story; sweep stories depend on it).

## Approach

Add a thin CLI wrapper around the existing `project.resolve_mantle_dir()` core function. Lives in `cli/storage.py` as the read-side counterpart to `run_storage` (writes mode) and `run_migrate_storage` (moves files). Follows the same pattern as those existing functions and is registered in `cli/main.py` like every other Mantle subcommand.

## Implementation

### src/mantle/cli/storage.py (modify)

Add a new top-level function:

```python
def run_where(*, project_dir: Path | None = None) -> None:
    """Print the resolved .mantle/ absolute path to stdout.

    Args:
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    resolved = project.resolve_mantle_dir(project_dir).resolve()
    print(resolved)
```

#### Design decisions

- **Plain `print()`, not `console.print()`**: Rich emits ANSI escapes that pollute Bash captures. Output must be plumbing-grade clean so prompts can do `MANTLE_DIR=$(mantle where)` and substitute the variable directly into Read tool paths.
- **`.resolve()`**: Guarantees an absolute path even if `resolve_mantle_dir` returns a relative path like `./.mantle`. Prompts may run from any working directory.
- **No side effects**: Does not create directories, does not check existence. It is a pure resolver. Each consuming prompt handles missing-state messaging itself (most already do — they check whether `.mantle/state.md` exists right after resolving).
- **No `--global`/`--type` flag**: One job per command (product design §7). If the resolver later needs to expose more data, that is a new command.

### src/mantle/cli/main.py (modify)

Register the new command. Insert immediately after the existing `migrate_storage_command` (line 1856) so storage-related commands stay grouped:

```python
@app.command(name="where")
def where_command(
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Print the resolved .mantle/ directory absolute path."""
    storage.run_where(project_dir=path)
```

The `storage` module is already imported at the top of `main.py` (line 31), so no new import is needed.

## Tests

### tests/cli/test_storage.py (modify)

Add a new `TestWhere` class alongside the existing `TestStorage`, `TestMigrateStorage`, and `TestCLIWiring` classes. Reuse the existing `_create_project` helper.

- **test_where_local_mode**: `_create_project(tmp_path)` (no storage_mode set), call `run_where(project_dir=tmp_path)`, capture stdout via `capsys`, assert the trimmed output equals `str((tmp_path / ".mantle").resolve())`.
- **test_where_global_mode**: `_create_project(tmp_path, storage_mode="global")`, monkeypatch `pathlib.Path.home` to a fake home under `tmp_path / "fakehome"` (mirrors the existing `TestMigrateStorage` pattern), call `run_where(project_dir=tmp_path)`, assert stdout starts with `str(fake_home / ".mantle/projects/")` and is an absolute path.
- **test_where_default_cwd**: `_create_project(tmp_path)`, monkeypatch `pathlib.Path.cwd` to return `tmp_path`, call `run_where()` with no `project_dir`, assert output matches the project-local path.
- **test_where_output_is_clean**: `_create_project(tmp_path)`, call `run_where(project_dir=tmp_path)`, assert captured stdout contains no ANSI escape sequences (`"\x1b" not in captured.out`) and is exactly one line (`captured.out.count("\n") == 1`).
- **test_where_no_config**: Pass `tmp_path` with no `.mantle/` directory at all (no `_create_project` call). The resolver should still return the project-local default. Assert output equals `str((tmp_path / ".mantle").resolve())`.

Add a CLI wiring smoke test in the existing `TestCLIWiring` class:

- **test_where_help**: Run `python -m mantle.cli.main where --help` via subprocess, assert returncode 0 and that 'where' or 'resolved' appears in stdout.

All tests use `tmp_path` and a synthesised `HOME` to avoid touching real `~/.mantle/` (mirroring the existing `TestMigrateStorage` pattern at line 116).
