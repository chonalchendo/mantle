"""Tests for the compilation engine."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import patch

from mantle.core import compiler, templates, vault
from mantle.core.session import SessionNote

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"
OTHER_EMAIL = "other@example.com"


def _write_state_md(mantle_dir: Path, body: str | None = None) -> None:
    """Write a minimal state.md to a .mantle/ directory."""
    if body is None:
        body = (
            "## Summary\n\nA test project.\n\n"
            "## Current Focus\n\nBuilding things.\n\n"
            "## Blockers\n\nNone.\n\n"
            "## Recent Decisions\n\nChose Python.\n\n"
            "## Next Steps\n\nWrite tests.\n"
        )
    mantle_dir.mkdir(parents=True, exist_ok=True)
    (mantle_dir / "state.md").write_text(
        "---\n"
        "schema_version: 1\n"
        "project: test-project\n"
        "status: implementing\n"
        "confidence: '7/10'\n"
        "created: '2025-01-01'\n"
        "created_by: test@example.com\n"
        "updated: '2025-01-01'\n"
        "updated_by: test@example.com\n"
        "current_issue: 8\n"
        "current_story: 3\n"
        "skills_required:\n"
        "  - python\n"
        "  - jinja2\n"
        "tags:\n"
        "  - status/active\n"
        "---\n\n" + body,
        encoding="utf-8",
    )


def _make_template_dir(tmp_path: Path) -> Path:
    """Create a temp template directory with a test .j2 file."""
    tpl_dir = tmp_path / "templates"
    tpl_dir.mkdir()
    (tpl_dir / "status.md.j2").write_text(
        "# {{ project }}\nStatus: {{ status }}\n"
        "{{ summary }}\n"
    )
    return tpl_dir


def _write_session(
    project_dir: Path,
    filename: str,
    *,
    author: str = MOCK_EMAIL,
    body: str = "Session body content.",
    commands_used: tuple[str, ...] = (),
) -> None:
    """Write a session file directly for testing."""
    note = SessionNote(
        project="test-project",
        author=author,
        date=datetime(2026, 3, 1, 14, 30),
        commands_used=commands_used,
    )
    path = (
        project_dir / ".mantle" / "sessions" / filename
    )
    vault.write_note(path, note, body)


def _mock_git_identity() -> str:
    return MOCK_EMAIL


# ── collect_context ─────────────────────────────────────────────


class TestCollectContext:
    def test_returns_frontmatter_fields(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        ctx = compiler.collect_context(tmp_path)

        assert ctx["project"] == "test-project"
        assert ctx["status"] == "implementing"
        assert ctx["confidence"] == "7/10"

    def test_returns_parsed_body_sections(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        ctx = compiler.collect_context(tmp_path)

        assert ctx["summary"] == "A test project."
        assert ctx["current_focus"] == "Building things."
        assert ctx["blockers"] == "None."
        assert ctx["recent_decisions"] == "Chose Python."
        assert ctx["next_steps"] == "Write tests."

    def test_body_section_keys_are_lowercased_underscored(
        self, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        ctx = compiler.collect_context(tmp_path)

        assert "current_focus" in ctx
        assert "recent_decisions" in ctx
        assert "next_steps" in ctx

    def test_handles_placeholder_body(self, tmp_path: Path):
        placeholder = (
            "## Summary\n\n"
            "_Describe the project in one or two sentences._\n\n"
            "## Current Focus\n\n"
            "_What are you working on right now?_\n\n"
            "## Blockers\n\n"
            "_Anything preventing progress?_\n\n"
            "## Recent Decisions\n\n"
            "_Key decisions made recently._\n\n"
            "## Next Steps\n\n"
            "_What comes next?_\n"
        )
        _write_state_md(tmp_path / ".mantle", body=placeholder)
        ctx = compiler.collect_context(tmp_path)

        assert "summary" in ctx
        assert "current_focus" in ctx


# ── source_paths ────────────────────────────────────────────────


class TestSourcePaths:
    def test_includes_state_md(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")

        with patch.object(
            compiler, "template_dir", return_value=tmp_path / "empty"
        ):
            paths = compiler.source_paths(tmp_path)

        state_path = tmp_path / ".mantle" / "state.md"
        assert state_path in paths

    def test_includes_product_design_when_exists(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        pd = tmp_path / ".mantle" / "product-design.md"
        pd.write_text("---\ntags: []\n---\n\ncontent")

        with patch.object(
            compiler, "template_dir", return_value=tmp_path / "empty"
        ):
            paths = compiler.source_paths(tmp_path)

        assert pd in paths

    def test_excludes_product_design_when_missing(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")

        with patch.object(
            compiler, "template_dir", return_value=tmp_path / "empty"
        ):
            paths = compiler.source_paths(tmp_path)

        pd = tmp_path / ".mantle" / "product-design.md"
        assert pd not in paths

    def test_includes_j2_template_files(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)

        with patch.object(
            compiler, "template_dir", return_value=tpl_dir
        ):
            paths = compiler.source_paths(tmp_path)

        assert any(str(p).endswith(".j2") for p in paths)


# ── template_dir ────────────────────────────────────────────────


class TestTemplateDir:
    def test_returns_existing_directory(self):
        result = compiler.template_dir()
        assert result.is_dir()

    def test_contains_j2_files(self):
        result = compiler.template_dir()
        j2_files = list(result.glob("*.j2"))
        assert len(j2_files) > 0


# ── compile ─────────────────────────────────────────────────────


class TestCompile:
    def test_renders_template_to_target(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch.object(
            compiler, "template_dir", return_value=tpl_dir
        ):
            result = compiler.compile(tmp_path, target_dir=target)

        assert "status.md" in result
        assert (target / "status.md").exists()

    def test_strips_j2_extension(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch.object(
            compiler, "template_dir", return_value=tpl_dir
        ):
            compiler.compile(tmp_path, target_dir=target)

        assert not (target / "status.md.j2").exists()
        assert (target / "status.md").exists()

    def test_saves_compilation_manifest(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch.object(
            compiler, "template_dir", return_value=tpl_dir
        ):
            compiler.compile(tmp_path, target_dir=target)

        assert (
            tmp_path / ".mantle" / ".compile-manifest.json"
        ).exists()

    def test_returns_compiled_names(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch.object(
            compiler, "template_dir", return_value=tpl_dir
        ):
            result = compiler.compile(tmp_path, target_dir=target)

        assert result == ["status.md"]

    def test_creates_target_dir_if_missing(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "does" / "not" / "exist"

        with patch.object(
            compiler, "template_dir", return_value=tpl_dir
        ):
            compiler.compile(tmp_path, target_dir=target)

        assert target.is_dir()


# ── compile_if_stale ────────────────────────────────────────────


class TestCompileIfStale:
    def test_compiles_when_no_manifest(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch.object(
            compiler, "template_dir", return_value=tpl_dir
        ):
            result = compiler.compile_if_stale(
                tmp_path, target_dir=target
            )

        assert result is not None
        assert "status.md" in result

    def test_returns_none_when_unchanged(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch.object(
            compiler, "template_dir", return_value=tpl_dir
        ):
            compiler.compile(tmp_path, target_dir=target)
            result = compiler.compile_if_stale(
                tmp_path, target_dir=target
            )

        assert result is None

    def test_recompiles_when_source_changes(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        tpl_dir = _make_template_dir(tmp_path)
        target = tmp_path / "output"

        with patch.object(
            compiler, "template_dir", return_value=tpl_dir
        ):
            compiler.compile(tmp_path, target_dir=target)

            # Modify state.md
            _write_state_md(
                tmp_path / ".mantle",
                body=(
                    "## Summary\n\nUpdated.\n\n"
                    "## Current Focus\n\nNew focus.\n\n"
                    "## Blockers\n\nNone.\n\n"
                    "## Recent Decisions\n\nChanged.\n\n"
                    "## Next Steps\n\nMore tests.\n"
                ),
            )

            result = compiler.compile_if_stale(
                tmp_path, target_dir=target
            )

        assert result is not None


# ── _parse_body_sections ────────────────────────────────────────


class TestParseBodySections:
    def test_parses_standard_body(self):
        body = (
            "## Summary\n\nA project.\n\n"
            "## Current Focus\n\nBuilding.\n\n"
            "## Next Steps\n\nTest.\n"
        )
        sections = compiler._parse_body_sections(body)

        assert sections["summary"] == "A project."
        assert sections["current_focus"] == "Building."
        assert sections["next_steps"] == "Test."

    def test_handles_single_section(self):
        body = "## Summary\n\nJust one section.\n"
        sections = compiler._parse_body_sections(body)

        assert sections["summary"] == "Just one section."
        assert len(sections) == 1

    def test_handles_empty_body(self):
        sections = compiler._parse_body_sections("")
        assert sections == {}


# ── collect_context (session fields) ────────────────────────────


class TestCollectContextSessions:
    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_has_session_false_when_no_sessions(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        ctx = compiler.collect_context(tmp_path)

        assert ctx["has_session"] is False

    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_has_session_true_when_sessions_exist(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        _write_session(tmp_path, "2026-03-01-1400.md")
        ctx = compiler.collect_context(tmp_path)

        assert ctx["has_session"] is True

    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_latest_session_body(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        _write_session(
            tmp_path,
            "2026-03-01-1400.md",
            body="Did important work.",
        )
        ctx = compiler.collect_context(tmp_path)

        assert "Did important work." in ctx["latest_session_body"]

    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_latest_session_date_format(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        _write_session(tmp_path, "2026-03-01-1400.md")
        ctx = compiler.collect_context(tmp_path)

        assert ctx["latest_session_date"] == "2026-03-01 14:30"

    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_latest_session_commands(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        _write_session(
            tmp_path,
            "2026-03-01-1400.md",
            commands_used=("idea", "challenge"),
        )
        ctx = compiler.collect_context(tmp_path)

        assert ctx["latest_session_commands"] == [
            "idea",
            "challenge",
        ]

    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_filters_sessions_to_current_user(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        _write_session(
            tmp_path,
            "2026-03-01-1000.md",
            author=OTHER_EMAIL,
            body="Other author session.",
        )
        _write_session(
            tmp_path,
            "2026-03-01-1400.md",
            author=MOCK_EMAIL,
            body="My session.",
        )
        ctx = compiler.collect_context(tmp_path)

        assert "My session." in ctx["latest_session_body"]

    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=RuntimeError("no git"),
    )
    def test_falls_back_when_git_identity_unavailable(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        _write_session(
            tmp_path,
            "2026-03-01-1400.md",
            body="Fallback session.",
        )
        ctx = compiler.collect_context(tmp_path)

        assert ctx["has_session"] is True
        assert "Fallback session." in ctx["latest_session_body"]


# ── source_paths (sessions) ────────────────────────────────────


class TestSourcePathsSessions:
    def test_includes_latest_session(self, tmp_path: Path):
        _write_state_md(tmp_path / ".mantle")
        _write_session(tmp_path, "2026-03-01-1000.md")
        _write_session(tmp_path, "2026-03-01-1400.md")

        with patch.object(
            compiler,
            "template_dir",
            return_value=tmp_path / "empty",
        ):
            paths = compiler.source_paths(tmp_path)

        session_path = (
            tmp_path
            / ".mantle"
            / "sessions"
            / "2026-03-01-1400.md"
        )
        assert session_path in paths

    def test_excludes_sessions_when_dir_empty(
        self, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        sessions_dir = tmp_path / ".mantle" / "sessions"
        sessions_dir.mkdir()

        with patch.object(
            compiler,
            "template_dir",
            return_value=tmp_path / "empty",
        ):
            paths = compiler.source_paths(tmp_path)

        session_paths = [
            p for p in paths if sessions_dir in p.parents
        ]
        assert session_paths == []


# ── resume template ────────────────────────────────────────────


class TestResumeTemplate:
    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_renders_with_session(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        _write_session(
            tmp_path,
            "2026-03-01-1400.md",
            body="Did work on feature X.",
        )
        ctx = compiler.collect_context(tmp_path)
        tpl_dir = compiler.template_dir()

        rendered = templates.render_template(
            tpl_dir, "resume.md.j2", ctx
        )

        assert "test-project" in rendered
        assert "implementing" in rendered
        assert "Did work on feature X." in rendered
        assert "Last Session" in rendered

    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_renders_without_session(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        ctx = compiler.collect_context(tmp_path)
        tpl_dir = compiler.template_dir()

        rendered = templates.render_template(
            tpl_dir, "resume.md.j2", ctx
        )

        assert "test-project" in rendered
        assert "Last Session" not in rendered

    @patch(
        "mantle.core.compiler.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_output_within_token_budget(
        self, _mock: object, tmp_path: Path
    ):
        _write_state_md(tmp_path / ".mantle")
        _write_session(
            tmp_path,
            "2026-03-01-1400.md",
            body="Session notes here.",
        )
        ctx = compiler.collect_context(tmp_path)
        tpl_dir = compiler.template_dir()

        rendered = templates.render_template(
            tpl_dir, "resume.md.j2", ctx
        )

        # ~3K tokens ≈ ~750 words; with short test data
        # this should be well under budget.
        word_count = len(rendered.split())
        assert word_count < 750
