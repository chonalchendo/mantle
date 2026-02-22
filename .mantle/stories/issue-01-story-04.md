---
issue: 1
title: File hash manifest module (core/manifest.py)
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Build the file hash manifest module that tracks installed file hashes for detecting user modifications on upgrade.

### src/mantle/core/manifest.py

```python
"""File hash manifest for tracking installed file state."""
```

#### Data model (Pydantic)

```python
class FileManifest(pydantic.BaseModel):
    """Tracks file hashes for an installation."""
    files: dict[str, str]  # relative_path -> SHA-256 hash
```

#### Functions

- `hash_file(path: Path) -> str` — compute SHA-256 hex digest of a file's contents
- `hash_directory(directory: Path) -> dict[str, str]` — hash all files in a directory recursively, returning relative_path -> hash mapping
- `read_manifest(path: Path) -> FileManifest` — load manifest from JSON file; return empty manifest if file doesn't exist
- `write_manifest(manifest: FileManifest, path: Path) -> None` — write manifest to JSON file
- `compare_manifests(source: FileManifest, installed: FileManifest) -> ComparisonResult` — compare source hashes against installed hashes

#### ComparisonResult (Pydantic model or dataclass)

```python
class ComparisonResult(pydantic.BaseModel):
    """Result of comparing source manifest against installed manifest."""
    new: list[str]            # In source, not in installed manifest
    unchanged: list[str]      # Same hash in source and installed
    source_changed: list[str] # Source hash differs from manifest (update available)
    user_modified: list[str]  # Installed file hash differs from manifest (user edited)
    removed: list[str]        # In manifest, not in source
```

The comparison logic:
1. For each file in source: if not in manifest → `new`
2. For each file in both: if source hash == manifest hash → check installed file:
   - If installed hash == manifest hash → `unchanged`
   - If installed hash != manifest hash → `user_modified`
3. For each file in both: if source hash != manifest hash → `source_changed`
4. For each file in manifest but not source → `removed`

Note: `compare_manifests` takes three inputs conceptually — source hashes, manifest (what was installed), and current installed file hashes. The function should accept `source_hashes: dict[str, str]`, `manifest: FileManifest`, and `installed_dir: Path` (to compute current installed hashes).

## Tests

All tests use `tmp_path` fixture for isolated file operations.

- `hash_file` produces consistent SHA-256 for known content (hash a file with known bytes, verify hex digest)
- `hash_file` produces different hashes for different content
- `hash_directory` returns correct relative paths and hashes for a directory tree
- `hash_directory` handles nested subdirectories
- `hash_directory` returns empty dict for empty directory
- `write_manifest` then `read_manifest` round-trips correctly
- `read_manifest` on nonexistent file returns empty manifest
- `compare_manifests` detects new files (in source, not in manifest)
- `compare_manifests` detects unchanged files (same hash everywhere)
- `compare_manifests` detects user-modified files (installed differs from manifest, source matches manifest)
- `compare_manifests` detects source-changed files (source hash differs from manifest)
- `compare_manifests` detects removed files (in manifest, not in source)
- `compare_manifests` with empty manifest treats all source files as new
- `compare_manifests` with empty source treats all manifest files as removed
