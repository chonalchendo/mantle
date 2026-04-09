---
issue: 2
title: Vault read/write module (core/vault.py)
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Build the foundational vault read/write module that all other modules depend on for reading and writing markdown notes with YAML frontmatter.

### src/mantle/core/vault.py

```python
"""Vault read/write for markdown notes with YAML frontmatter."""
```

#### Data model

```python
@dataclass(frozen=True, slots=True)
class Note(Generic[T]):
    """A markdown note with typed frontmatter."""
    frontmatter: T
    body: str
```

`T` is a Pydantic `BaseModel` subclass. The `Note` wrapper is a frozen dataclass (not Pydantic) to avoid double-validation overhead.

#### Error hierarchy

```python
class VaultError(Exception):
    """Base exception for vault operations."""

class NoteParseError(VaultError):
    """YAML frontmatter could not be parsed."""

class NoteValidationError(VaultError):
    """Frontmatter parsed but failed Pydantic schema validation."""
```

#### Functions

- `read_note(path: Path, schema: type[T]) -> Note[T]` — Read a markdown file, parse YAML frontmatter with `yaml.safe_load`, validate against the Pydantic schema `T`, return `Note[T]`. Raises `NoteParseError` for invalid YAML, `NoteValidationError` for schema failures, `FileNotFoundError` if the file doesn't exist.

- `write_note(path: Path, frontmatter: BaseModel, body: str) -> None` — Serialize frontmatter via `model_dump()` + `yaml.dump()`, write `---\n{yaml}\n---\n\n{body}` to the file. Creates parent directories if needed. Overwrites existing file.

#### Internal details

- YAML parsing: `yaml.safe_load` (from PyYAML). Not OmegaConf — its interpolation/merge features are unnecessary for note frontmatter.
- YAML writing: `yaml.dump(default_flow_style=False, sort_keys=False, allow_unicode=True)`.
- Frontmatter delimiter: `---` on its own line. Standard YAML frontmatter format.
- Body separator: blank line after closing `---` fence.
- The module does NOT handle Obsidian CLI integration. That is deferred to a future issue. Filesystem only.

### Dependency changes in pyproject.toml

- Add `pyyaml>=6.0` to runtime dependencies (currently only in dev deps)
- Remove `omegaconf>=2.3` from runtime dependencies (no longer needed)

## Tests

All tests use `tmp_path` fixture for isolated file operations.

- **read_note**: reads a valid note with YAML frontmatter and returns `Note[T]` with correct frontmatter fields and body
- **read_note**: returns empty string body when note has frontmatter only (no body content)
- **read_note**: raises `NoteParseError` for malformed YAML (e.g., tabs, unclosed quotes)
- **read_note**: raises `NoteValidationError` when YAML is valid but doesn't match the Pydantic schema (e.g., missing required field)
- **read_note**: raises `FileNotFoundError` for nonexistent file
- **read_note**: handles frontmatter with `null` values correctly
- **read_note**: handles frontmatter with list values (e.g., `tags: [a, b]`)
- **write_note**: writes a note that `read_note` can round-trip (write then read back, fields match)
- **write_note**: creates parent directories if they don't exist
- **write_note**: overwrites an existing file
- **write_note**: serializes Pydantic model frontmatter correctly (including None values, lists, nested models)
- **write_note**: body content is preserved exactly (including leading/trailing whitespace, blank lines)
- **Note**: is frozen (cannot assign to `.frontmatter` or `.body`)
- **Error hierarchy**: `NoteParseError` and `NoteValidationError` are both subclasses of `VaultError`
