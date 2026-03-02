---
issue: 8
title: Compilation staleness detection (extend core/manifest.py)
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Extend `src/mantle/core/manifest.py` with functions for tracking compilation source file hashes and detecting staleness. The compilation manifest is a separate file from the install manifest — it tracks which vault files (state.md, product-design.md, etc.) and template files were used in the last compilation, so `compile --if-stale` can skip work when nothing changed.

### src/mantle/core/manifest.py (modify)

#### New constants

```python
_COMPILE_MANIFEST_FILENAME = ".compile-manifest.json"
```

#### New functions

- `hash_paths(paths: Iterable[Path]) -> dict[str, str]` — Hash multiple files. Skips files that don't exist (missing optional vault files like product-design.md shouldn't error). Returns dict mapping `str(path)` → SHA-256 hex digest. Uses existing `hash_file()` internally.

- `save_compilation_manifest(manifest_path: Path, hashes: dict[str, str]) -> None` — Persist source file hashes after a successful compilation. Writes a `_FileManifest` (reuses existing internal model) to the given path.

- `load_compilation_manifest(manifest_path: Path) -> dict[str, str]` — Read stored compilation hashes. Returns empty dict if manifest doesn't exist.

- `is_compilation_stale(manifest_path: Path, current_hashes: dict[str, str]) -> bool` — Compare current source hashes against stored manifest. Returns `True` if manifest doesn't exist, if any hash differs, or if the set of tracked files changed. Returns `False` only when all hashes match exactly.

#### Reuses

- `hash_file()` — existing, unchanged
- `_FileManifest` — existing internal model (version + files dict), unchanged
- `_read_manifest()` / `_write_manifest()` — existing internal helpers, unchanged

#### Design decisions

- **Separate manifest file.** The install manifest (`mantle-file-manifest.json`) tracks what's installed in `~/.claude/`. The compilation manifest (`.compile-manifest.json`) tracks vault source files. Different concerns, different lifecycles, different locations.
- **Reuse `_FileManifest` model.** Same shape (path → hash mapping). No reason to create a new model.
- **`hash_paths` skips missing files.** Optional vault files (product-design.md, system-design.md) may not exist yet. Their absence is a valid state, not an error. If a file is added later, the hashes won't match and compilation will re-run.
- **Full-set comparison in `is_compilation_stale`.** If the set of source files changes (new template added, vault file created), that's a staleness signal even if existing files haven't changed.

## Tests

### tests/core/test_manifest.py (modify)

Add new tests alongside existing install manifest tests.

- **hash_paths**: hashes multiple files correctly
- **hash_paths**: skips non-existent files
- **hash_paths**: returns empty dict for empty input
- **save_compilation_manifest**: creates manifest file
- **save_compilation_manifest**: round-trips with `load_compilation_manifest`
- **load_compilation_manifest**: returns empty dict when file missing
- **is_compilation_stale**: True when no manifest exists
- **is_compilation_stale**: False when hashes match exactly
- **is_compilation_stale**: True when a file hash changes
- **is_compilation_stale**: True when a new file is added to current hashes
- **is_compilation_stale**: True when a file is removed from current hashes
