"""Tests for mantle.core.vault."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pydantic
import pytest

from mantle.core.vault import (
    Note,
    NoteParseError,
    NoteValidationError,
    VaultError,
    read_note,
    write_note,
)


# ── Test schemas ─────────────────────────────────────────────────


class SimpleSchema(pydantic.BaseModel):
    """Minimal schema for testing."""

    title: str
    status: str


class SchemaWithOptional(pydantic.BaseModel):
    """Schema with optional and list fields."""

    title: str
    description: str | None = None
    tags: tuple[str, ...] = ()


# ── read_note ────────────────────────────────────────────────────


class TestReadNote:
    def test_reads_valid_note(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        path.write_text(
            "---\ntitle: Hello\nstatus: draft\n---\n\nBody text here.\n"
        )

        note = read_note(path, SimpleSchema)

        assert note.frontmatter.title == "Hello"
        assert note.frontmatter.status == "draft"
        assert note.body == "Body text here.\n"

    def test_empty_body(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        path.write_text("---\ntitle: Hello\nstatus: draft\n---\n\n")

        note = read_note(path, SimpleSchema)

        assert note.frontmatter.title == "Hello"
        assert note.body == ""

    def test_malformed_yaml_raises_parse_error(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "note.md"
        path.write_text("---\ntitle: 'unclosed\n---\n\nBody.\n")

        with pytest.raises(NoteParseError):
            read_note(path, SimpleSchema)

    def test_schema_mismatch_raises_validation_error(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "note.md"
        path.write_text("---\nwrong_key: value\n---\n\nBody.\n")

        with pytest.raises(NoteValidationError):
            read_note(path, SimpleSchema)

    def test_file_not_found(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            read_note(path, SimpleSchema)

    def test_null_values(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        path.write_text(
            "---\ntitle: Hello\ndescription: null\ntags: []\n---\n\n"
        )

        note = read_note(path, SchemaWithOptional)

        assert note.frontmatter.description is None
        assert note.frontmatter.tags == ()

    def test_list_values(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        path.write_text(
            "---\ntitle: Hello\ntags:\n  - foo\n  - bar\n---\n\nBody.\n"
        )

        note = read_note(path, SchemaWithOptional)

        assert note.frontmatter.tags == ("foo", "bar")

    def test_no_frontmatter_delimiter(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        path.write_text("Just plain text, no frontmatter.\n")

        with pytest.raises(NoteParseError):
            read_note(path, SimpleSchema)

    def test_no_closing_delimiter(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        path.write_text("---\ntitle: Hello\nstatus: draft\n")

        with pytest.raises(NoteParseError):
            read_note(path, SimpleSchema)


# ── write_note ───────────────────────────────────────────────────


class TestWriteNote:
    def test_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        fm = SimpleSchema(title="Test", status="active")
        body = "Some body content.\n"

        write_note(path, fm, body)
        note = read_note(path, SimpleSchema)

        assert note.frontmatter.title == "Test"
        assert note.frontmatter.status == "active"
        assert note.body == body

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        path = tmp_path / "a" / "b" / "note.md"
        fm = SimpleSchema(title="Nested", status="draft")

        write_note(path, fm, "Body.\n")

        assert path.exists()

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        fm1 = SimpleSchema(title="First", status="draft")
        fm2 = SimpleSchema(title="Second", status="active")

        write_note(path, fm1, "First body.\n")
        write_note(path, fm2, "Second body.\n")

        note = read_note(path, SimpleSchema)
        assert note.frontmatter.title == "Second"
        assert note.body == "Second body.\n"

    def test_serializes_none_and_lists(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        fm = SchemaWithOptional(
            title="Test", description=None, tags=("a", "b")
        )

        write_note(path, fm, "Body.\n")
        note = read_note(path, SchemaWithOptional)

        assert note.frontmatter.description is None
        assert note.frontmatter.tags == ("a", "b")

    def test_preserves_body_exactly(self, tmp_path: Path) -> None:
        path = tmp_path / "note.md"
        fm = SimpleSchema(title="Test", status="draft")
        body = "\n  Leading whitespace.\n\nBlank line above.\n\n"

        write_note(path, fm, body)
        note = read_note(path, SimpleSchema)

        assert note.body == body


# ── Note dataclass ───────────────────────────────────────────────


class TestNote:
    def test_frozen(self) -> None:
        fm = SimpleSchema(title="Test", status="draft")
        note = Note(frontmatter=fm, body="Body.")

        with pytest.raises(FrozenInstanceError):
            note.frontmatter = fm  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            note.body = "new"  # type: ignore[misc]


# ── Error hierarchy ──────────────────────────────────────────────


class TestErrorHierarchy:
    def test_parse_error_is_vault_error(self) -> None:
        assert issubclass(NoteParseError, VaultError)

    def test_validation_error_is_vault_error(self) -> None:
        assert issubclass(NoteValidationError, VaultError)
