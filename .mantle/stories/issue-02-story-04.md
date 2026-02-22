---
issue: 2
title: Init-vault command with auto-config (mantle init-vault)
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Build the `mantle init-vault` command that creates a personal vault directory structure and automatically records the vault path in `.mantle/config.md`. Also build the internal config read/write functions in `core/project.py` (not exposed as CLI commands in v1).

### src/mantle/core/project.py (additions)

Add config read/write functions and init_vault to the existing `core/project.py` module (created in Story 3).

#### Config functions (internal, not user-facing CLI)

```python
def read_config(project_root: Path) -> dict[str, Any]:
    """Load config frontmatter from .mantle/config.md.

    Returns:
        Dictionary of frontmatter key-value pairs.

    Raises:
        FileNotFoundError: If .mantle/ or config.md does not exist.
    """

def update_config(project_root: Path, **kwargs: Any) -> None:
    """Update specific keys in .mantle/config.md frontmatter.

    Reads existing config, merges provided keys, writes back.
    Preserves the markdown body.

    Raises:
        FileNotFoundError: If .mantle/ or config.md does not exist.
    """
```

Internal helpers for YAML frontmatter manipulation:
- `_read_frontmatter_and_body(path) -> tuple[dict, str]` — Split a markdown file into frontmatter dict and body string
- `_write_frontmatter_and_body(path, frontmatter, body) -> None` — Write frontmatter + body back

These helpers use `yaml.safe_load` / `yaml.dump` directly — NOT vault.py's `read_note`/`write_note`. Rationale: config operations need simple key-value updates without Pydantic schema validation, and this avoids a dependency on vault.py for internal config management.

#### init_vault function

```python
def init_vault(vault_path: Path, project_root: Path) -> None:
    """Create personal vault structure and link it to this project.

    Creates skills/, knowledge/, inbox/ at vault_path.
    Records the resolved vault path in .mantle/config.md.

    Args:
        vault_path: Path for the personal vault (expanded and resolved).
        project_root: Directory containing .mantle/.

    Raises:
        FileExistsError: If all three vault subdirectories already exist.
        FileNotFoundError: If .mantle/ does not exist at project_root.
    """
```

Logic:
1. Validate `.mantle/` exists at project_root
2. Expand and resolve vault_path (`expanduser().resolve()`)
3. Idempotency check: if all three subdirectories (skills/, knowledge/, inbox/) already exist, raise `FileExistsError`
4. Create directories with `mkdir(parents=True, exist_ok=True)` — handles partial initialization
5. Call `update_config(project_root, personal_vault=str(resolved_path))` to auto-set config
6. No return value — success is implicit, errors are exceptions

### src/mantle/cli/init_vault.py

```python
"""Init-vault command — create personal vault and link it."""
```

#### Function

```python
def run_init_vault(vault_path: Path) -> None:
    """Create personal vault structure and link to project config."""
```

Logic:
1. Find project root (walk up from cwd looking for `.mantle/`, or just use `Path.cwd()`)
2. Call `core.project.init_vault(vault_path, project_root)`
3. Catch `FileExistsError` → print yellow warning, exit 0
4. Catch `FileNotFoundError` → print red error ("Run mantle init first"), exit 1
5. Print Rich success message:
   - "Created personal vault at {resolved_path}"
   - List directories: skills/, knowledge/, inbox/
   - "Vault path saved to .mantle/config.md"
   - Hint about iCloud sync

### Wire into cli/main.py

```python
@app.command(name="init-vault")
def init_vault(path: Path) -> None:
    """Create personal vault and link it to this project."""
    run_init_vault(path)
```

### No config CLI commands

`config get/set` is deferred to v2. The `read_config()` and `update_config()` functions exist in core for other commands to use programmatically. The only user-facing way to set the personal vault path is `mantle init-vault`.

## Tests

All tests use `tmp_path` for both project root and vault path. Pre-create `.mantle/config.md` in test fixtures.

- **init_vault**: creates skills/, knowledge/, inbox/ directories at vault path
- **init_vault**: handles tilde expansion (~/ → /Users/...)
- **init_vault**: auto-sets personal_vault in .mantle/config.md frontmatter
- **init_vault**: config.md body content is preserved after update
- **init_vault**: raises FileExistsError if all three subdirectories already exist
- **init_vault**: partial init (only skills/ exists) completes without error, creates missing dirs
- **init_vault**: raises FileNotFoundError if .mantle/ does not exist
- **read_config**: returns frontmatter dict from config.md
- **read_config**: returns empty values for unset keys (personal_vault: null → None in dict)
- **read_config**: raises FileNotFoundError if config.md doesn't exist
- **update_config**: updates a single key without affecting others
- **update_config**: adds a new key that didn't exist in frontmatter
- **update_config**: preserves markdown body content
- **update_config**: handles multiple keys in one call
- **CLI run_init_vault**: prints success message with vault path
- **CLI run_init_vault**: prints warning on already-existing vault
- **CLI run_init_vault**: prints error when project not initialized
- **CLI wiring**: `mantle init-vault --help` shows help text (subprocess test)
