"""Vault read/write for markdown notes with YAML frontmatter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pydantic
import yaml

if TYPE_CHECKING:
    from pathlib import Path


# ── Data model ───────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Note[T: pydantic.BaseModel]:
    """A markdown note with typed frontmatter.

    Attributes:
        frontmatter: Validated Pydantic model parsed from YAML.
        body: Markdown content after the frontmatter block.
    """

    frontmatter: T
    body: str


# ── Error hierarchy ──────────────────────────────────────────────


class VaultError(Exception):
    """Base exception for vault operations."""


class NoteParseError(VaultError):
    """YAML frontmatter could not be parsed."""


class NoteValidationError(VaultError):
    """Frontmatter parsed but failed Pydantic schema validation."""


# ── Public API ───────────────────────────────────────────────────


def read_note[T: pydantic.BaseModel](path: Path, schema: type[T]) -> Note[T]:
    """Read a markdown file and parse its YAML frontmatter.

    Args:
        path: Path to the markdown file.
        schema: Pydantic model class to validate frontmatter against.

    Returns:
        Note with validated frontmatter and body text.

    Raises:
        FileNotFoundError: If the file does not exist.
        NoteParseError: If YAML frontmatter cannot be parsed.
        NoteValidationError: If frontmatter fails schema validation.
    """
    text = path.read_text(encoding="utf-8")
    raw, body = _split_frontmatter(text)

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        msg = f"Failed to parse YAML frontmatter in {path}: {exc}"
        raise NoteParseError(msg) from exc

    if data is None:
        data = {}

    try:
        frontmatter = schema.model_validate(data)
    except pydantic.ValidationError as exc:
        msg = f"Frontmatter validation failed in {path}: {exc}"
        raise NoteValidationError(msg) from exc

    return Note(frontmatter=frontmatter, body=body)


def write_note(
    path: Path,
    frontmatter: pydantic.BaseModel,
    body: str,
) -> None:
    """Write a markdown note with YAML frontmatter.

    Args:
        path: Path to write the file to.
        frontmatter: Pydantic model to serialize as YAML frontmatter.
        body: Markdown body content.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    data = frontmatter.model_dump(mode="json")
    yaml_str = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    text = f"---\n{yaml_str}---\n\n{body}"
    path.write_text(text, encoding="utf-8")


# ── Internal helpers ─────────────────────────────────────────────


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Split a markdown file into frontmatter and body.

    Args:
        text: Raw file content with YAML frontmatter.

    Returns:
        Tuple of (raw YAML string, body string).

    Raises:
        NoteParseError: If the file does not start with ``---``.
    """
    if not text.startswith("---"):
        msg = "File does not start with YAML frontmatter delimiter (---)"
        raise NoteParseError(msg)

    # Find the closing ---
    end = text.find("\n---", 3)
    if end == -1:
        msg = "No closing frontmatter delimiter (---) found"
        raise NoteParseError(msg)

    raw = text[4:end]  # Skip opening "---\n"
    rest = text[end + 4 :]  # Skip "\n---"

    # Strip the blank line separator between frontmatter and body
    if rest.startswith("\n\n"):
        body = rest[2:]
    elif rest.startswith("\n"):
        body = rest[1:]
    else:
        body = rest

    return raw, body
