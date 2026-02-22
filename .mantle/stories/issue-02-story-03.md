---
issue: 2
title: Init command (mantle init)
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Build the `mantle init` command that creates `.mantle/` in a project repo with all required structure and prints an onboarding message.

### src/mantle/core/project.py

```python
"""Project initialization and structure constants."""
```

#### Constants

```python
MANTLE_DIR = ".mantle"

SUBDIRS: tuple[str, ...] = (
    "decisions",
    "sessions",
    "issues",
    "stories",
)
```

#### File template data

Module-level constants for the initial files created by `init_project`:

- `CONFIG_FRONTMATTER: dict[str, object]` — `personal_vault: None`, `verification_strategy: None`, `tags: ["type/config"]`
- `CONFIG_BODY: str` — Markdown with sections for Verification Strategy and Personal Vault (placeholder text)
- `TAGS_FRONTMATTER: dict[str, object]` — `tags: ["type/config"]`
- `TAGS_BODY: str` — Full tag taxonomy (type/*, phase/*, status/*, confidence/* categories)
- `GITIGNORE_CONTENT: str` — Excludes compiled commands (`*.compiled.md`), temp files (`*.tmp`, `*.bak`)

These constants are importable by other modules that need canonical template data.

#### Function

```python
def init_project(project_dir: Path, project_name: str) -> Path:
    """Create .mantle/ directory structure with initial files.

    Does NOT check whether .mantle/ already exists. The caller
    is responsible for idempotency checks and user-facing messaging.

    Returns:
        Path to the created .mantle/ directory.

    Raises:
        FileExistsError: If .mantle/ already exists (via mkdir).
    """
```

Logic:
1. `mkdir .mantle/` (no `exist_ok` — raises FileExistsError as safety net)
2. Create subdirectories: decisions/, sessions/, issues/, stories/
3. Write config.md via `vault.write_note()` using CONFIG_FRONTMATTER and CONFIG_BODY
4. Write tags.md via `vault.write_note()` using TAGS_FRONTMATTER and TAGS_BODY
5. Write .gitignore directly via `Path.write_text()` (not a note, no frontmatter)
6. Call `state.create_initial_state(project_dir, project_name)` for state.md
7. Return the .mantle/ path

### src/mantle/cli/init.py

```python
"""Init command — create .mantle/ in a project repository."""
```

#### Function

```python
def run_init(project_dir: Path | None = None) -> None:
    """Initialize .mantle/ in the current project repository."""
```

Logic:
1. Default `project_dir` to `Path.cwd()` if None
2. Check if `.mantle/` exists — if yes, print yellow warning and return (idempotency)
3. Derive `project_name` from `project_dir.name`
4. Call `core.project.init_project(project_dir, project_name)`
5. Call `_print_onboarding()` — Rich-formatted message with next steps:
   - "Mantle initialized in .mantle/"
   - "Run /mantle:idea to log your first idea"
   - "Run /mantle:help to see all commands"
   - "Want cross-project skills? Run: mantle init-vault ~/vault"

### Wire into cli/main.py

Import and register `init` command:

```python
@app.command
def init() -> None:
    """Initialize .mantle/ in the current project repository."""
    run_init()
```

## Tests

All tests use `tmp_path`. Mock `state.create_initial_state` and `vault.write_note` where needed to isolate tests.

- **First init**: creates .mantle/ directory at project root
- **First init**: creates subdirectories: decisions/, sessions/, issues/, stories/
- **First init**: creates state.md (via create_initial_state)
- **First init**: creates config.md with correct frontmatter (personal_vault: null, verification_strategy: null, tags)
- **First init**: creates tags.md with tag taxonomy content (all 4 categories present)
- **First init**: creates .gitignore with compiled/temp exclusion rules
- **First init**: returns path to .mantle/ directory
- **Idempotency**: if .mantle/ exists, `run_init` prints warning and does not modify anything
- **Idempotency**: existing files in .mantle/ are not overwritten
- **Onboarding message**: output contains "/mantle:idea" and "/mantle:help"
- **Onboarding message**: output mentions "init-vault"
- **Project name**: derived from directory name (e.g., `tmp_path.name`)
- **Template constants**: CONFIG_FRONTMATTER has expected keys
- **Template constants**: TAGS_BODY contains all tag categories (type, phase, status, confidence)
- **Template constants**: GITIGNORE_CONTENT is non-empty
- **CLI wiring**: `mantle init --help` shows help text (subprocess test)
