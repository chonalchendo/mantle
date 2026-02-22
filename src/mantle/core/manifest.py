"""File hash manifest for tracking installed file state.

Tracks which files mantle installed into a target directory so that
re-installs can detect user modifications and avoid silent overwrites.
The manifest file location and format are internal implementation
details.
"""

from __future__ import annotations

import enum
import hashlib
import json
from typing import TYPE_CHECKING

import pydantic

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

_MANIFEST_FILENAME = "mantle-file-manifest.json"


# ── Public types ─────────────────────────────────────────────────


class FileStatus(enum.Enum):
    """How a managed file relates to its source and installed copy."""

    NEW = "new"
    """Source file with no corresponding manifest entry."""

    UNCHANGED = "unchanged"
    """Source, manifest, and installed file all match."""

    SOURCE_CHANGED = "source_changed"
    """Source changed since last install; user did not modify."""

    USER_MODIFIED = "user_modified"
    """User modified the installed file; source is unchanged."""

    CONFLICT = "conflict"
    """Both source and installed file changed since last install."""

    REMOVED = "removed"
    """In manifest but no longer in source."""


class InstallPlan(pydantic.BaseModel, frozen=True):
    """Categorised comparison of source files against installed state.

    Files are grouped by status. Each value is a frozenset of
    relative path strings (forward-slash separated).
    """

    new: frozenset[str] = frozenset()
    unchanged: frozenset[str] = frozenset()
    source_changed: frozenset[str] = frozenset()
    user_modified: frozenset[str] = frozenset()
    conflict: frozenset[str] = frozenset()
    removed: frozenset[str] = frozenset()

    @property
    def safe_to_write(self) -> frozenset[str]:
        """Files that can be written without prompting the user."""
        return self.new | self.source_changed

    @property
    def needs_prompt(self) -> frozenset[str]:
        """Files requiring user confirmation before overwriting."""
        return self.user_modified | self.conflict


# ── Internal manifest model ──────────────────────────────────────


class _FileManifest(pydantic.BaseModel):
    """Persisted manifest (internal format)."""

    version: int = 1
    files: dict[str, str] = {}


# ── Public API ───────────────────────────────────────────────────


def hash_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file's contents.

    Args:
        path: Absolute path to the file.

    Returns:
        Hex-encoded SHA-256 digest.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def plan_install(source_dir: Path, target_dir: Path) -> InstallPlan:
    """Compare source files against the installed state in target_dir.

    Reads the existing manifest from target_dir (if any), hashes all
    source files and their installed counterparts, and categorises
    each file by its status.

    Args:
        source_dir: Directory containing the canonical source files
            to install (scanned recursively).
        target_dir: Directory where files are installed (e.g.
            ``~/.claude/``). The manifest is stored within this
            directory.

    Returns:
        An InstallPlan with files grouped by status.

    Raises:
        FileNotFoundError: If source_dir does not exist or is empty.
    """
    if not source_dir.is_dir():
        msg = f"Source directory does not exist: {source_dir}"
        raise FileNotFoundError(msg)

    source_hashes = _hash_directory(source_dir)
    if not source_hashes:
        msg = f"Source directory is empty: {source_dir}"
        raise FileNotFoundError(msg)

    manifest = _read_manifest(target_dir / _MANIFEST_FILENAME)

    new: set[str] = set()
    unchanged: set[str] = set()
    source_changed: set[str] = set()
    user_modified: set[str] = set()
    conflict: set[str] = set()
    removed: set[str] = set()

    for rel_path, source_hash in source_hashes.items():
        if rel_path not in manifest.files:
            new.add(rel_path)
            continue

        recorded_hash = manifest.files[rel_path]
        installed_path = target_dir / rel_path
        installed_hash = (
            hash_file(installed_path) if installed_path.exists() else None
        )

        src_matches_record = source_hash == recorded_hash
        user_touched = installed_hash != recorded_hash

        if src_matches_record and not user_touched:
            unchanged.add(rel_path)
        elif src_matches_record and user_touched:
            user_modified.add(rel_path)
        elif not src_matches_record and not user_touched:
            source_changed.add(rel_path)
        else:
            conflict.add(rel_path)

    for rel_path in manifest.files:
        if rel_path not in source_hashes:
            removed.add(rel_path)

    return InstallPlan(
        new=frozenset(new),
        unchanged=frozenset(unchanged),
        source_changed=frozenset(source_changed),
        user_modified=frozenset(user_modified),
        conflict=frozenset(conflict),
        removed=frozenset(removed),
    )


def record_install(
    source_dir: Path,
    target_dir: Path,
    installed: Iterable[str],
) -> None:
    """Update the manifest to reflect a completed install.

    Hashes each source file and writes a new manifest to
    target_dir. Only the files listed in ``installed`` are
    recorded.

    This should be called after the caller has finished copying
    files.

    Args:
        source_dir: Directory containing the canonical source files.
        target_dir: Directory where files were installed.
        installed: Relative paths of files that were actually
            installed (or should continue to be tracked).
    """
    source_hashes = _hash_directory(source_dir)
    files: dict[str, str] = {}
    for rel_path in installed:
        if rel_path in source_hashes:
            files[rel_path] = source_hashes[rel_path]

    manifest = _FileManifest(files=files)
    _write_manifest(manifest, target_dir / _MANIFEST_FILENAME)


# ── Internal helpers ─────────────────────────────────────────────


def _hash_directory(directory: Path) -> dict[str, str]:
    """Hash all files in a directory recursively.

    Returns:
        Mapping of relative_path -> SHA-256 hash.
    """
    result: dict[str, str] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(directory))
            result[rel] = hash_file(path)
    return result


def _read_manifest(path: Path) -> _FileManifest:
    """Load manifest from JSON file.

    Returns an empty manifest if the file doesn't exist.
    """
    if not path.exists():
        return _FileManifest()
    data = json.loads(path.read_text())
    return _FileManifest.model_validate(data)


def _write_manifest(manifest: _FileManifest, path: Path) -> None:
    """Write manifest to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2) + "\n")
