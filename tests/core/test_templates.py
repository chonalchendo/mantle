"""Tests for Jinja2 template rendering module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import jinja2
import pytest

from mantle.core.templates import find_templates, render_template

if TYPE_CHECKING:
    from pathlib import Path


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ── render_template ─────────────────────────────────────────────


class TestRenderTemplate:
    def test_renders_simple_variable(self, tmp_path: Path):
        _write(tmp_path / "hello.j2", "Hello {{ name }}!")
        result = render_template(tmp_path, "hello.j2", {"name": "test"})
        assert result == "Hello test!"

    def test_renders_multiple_variables(self, tmp_path: Path):
        _write(
            tmp_path / "multi.j2",
            "Name: {{ name }}\nStatus: {{ status }}\n",
        )
        result = render_template(
            tmp_path, "multi.j2", {"name": "mantle", "status": "active"}
        )
        assert "Name: mantle" in result
        assert "Status: active" in result

    def test_renders_control_flow(self, tmp_path: Path):
        template = (
            "{% for item in items %}- {{ item }}\n{% endfor %}"
            "{% if show_footer %}Done.{% endif %}\n"
        )
        _write(tmp_path / "flow.j2", template)
        result = render_template(
            tmp_path,
            "flow.j2",
            {"items": ["a", "b"], "show_footer": True},
        )
        assert "- a" in result
        assert "- b" in result
        assert "Done." in result

    def test_raises_template_not_found(self, tmp_path: Path):
        with pytest.raises(jinja2.TemplateNotFound):
            render_template(tmp_path, "missing.j2", {})

    def test_raises_undefined_error_for_missing_variable(self, tmp_path: Path):
        _write(tmp_path / "strict.j2", "{{ missing_var }}")
        with pytest.raises(jinja2.UndefinedError):
            render_template(tmp_path, "strict.j2", {})


# ── find_templates ──────────────────────────────────────────────


class TestFindTemplates:
    def test_returns_sorted_j2_filenames(self, tmp_path: Path):
        _write(tmp_path / "b.md.j2", "b")
        _write(tmp_path / "a.md.j2", "a")
        assert find_templates(tmp_path) == ["a.md.j2", "b.md.j2"]

    def test_returns_empty_for_no_templates(self, tmp_path: Path):
        assert find_templates(tmp_path) == []

    def test_returns_empty_for_missing_directory(self, tmp_path: Path):
        assert find_templates(tmp_path / "nonexistent") == []

    def test_ignores_non_j2_files(self, tmp_path: Path):
        _write(tmp_path / "readme.md", "readme")
        _write(tmp_path / "status.md.j2", "status")
        assert find_templates(tmp_path) == ["status.md.j2"]
