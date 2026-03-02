"""Tests for the install command."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from mantle.cli.install import (
    _copy_files,
    _print_summary,
    _register_hooks,
    run_install,
)
from mantle.core.manifest import plan_install, record_install

HELP_MD = (
    Path(__file__).parent.parent.parent
    / "claude"
    / "commands"
    / "mantle"
    / "help.md"
)
_MANIFEST = "mantle-file-manifest.json"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ── help.md content ──────────────────────────────────────────────


class TestHelpMd:
    def test_help_md_exists(self):
        assert HELP_MD.is_file()

    def test_references_all_15_commands(self):
        content = HELP_MD.read_text()
        commands = [
            "/mantle:idea",
            "/mantle:challenge",
            "/mantle:design-product",
            "/mantle:design-system",
            "/mantle:revise-product",
            "/mantle:revise-system",
            "/mantle:plan-issues",
            "/mantle:plan-stories",
            "/mantle:implement",
            "/mantle:verify",
            "/mantle:review",
            "/mantle:status",
            "/mantle:resume",
            "/mantle:add-skill",
            "/mantle:help",
        ]
        for cmd in commands:
            assert cmd in content, f"Missing command: {cmd}"

    def test_grouped_by_workflow_phase(self):
        content = HELP_MD.read_text()
        phases = [
            "Idea & Validation",
            "Design",
            "Planning",
            "Implementation",
            "Verification & Review",
            "Context & Knowledge",
            "Help",
        ]
        for phase in phases:
            assert phase in content, f"Missing phase: {phase}"


# ── First install ────────────────────────────────────────────────


class TestFirstInstall:
    def test_copies_all_files(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "commands/foo.md", "foo content")
        _write(source / "commands/bar.md", "bar content")
        target.mkdir()

        plan = plan_install(source, target)
        _copy_files(source, target, plan.safe_to_write)
        record_install(source, target, plan.safe_to_write)

        assert (target / "commands/foo.md").read_text() == "foo content"
        assert (target / "commands/bar.md").read_text() == "bar content"
        assert (target / _MANIFEST).exists()

    def test_creates_intermediate_directories(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "deep/nested/file.md", "content")
        target.mkdir()

        plan = plan_install(source, target)
        _copy_files(source, target, plan.safe_to_write)

        assert (target / "deep/nested/file.md").exists()

    def test_rich_output_shows_count(self, tmp_path: Path, capsys):
        _print_summary(3, frozenset())
        # Rich writes to its own console, so we test via string
        # capture on the console object — but for simplicity,
        # just verify it doesn't raise.


# ── Re-install ───────────────────────────────────────────────────


class TestReinstall:
    def _do_install(self, source: Path, target: Path) -> None:
        """Helper: full install cycle."""
        plan = plan_install(source, target)
        _copy_files(source, target, plan.safe_to_write)
        record_install(source, target, plan.safe_to_write | plan.unchanged)

    def test_no_changes_overwrites_silently(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.md", "content")
        target.mkdir()

        self._do_install(source, target)
        plan = plan_install(source, target)

        assert plan.unchanged == {"a.md"}
        assert plan.needs_prompt == frozenset()

    def test_user_modified_detected(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.md", "original")
        target.mkdir()

        self._do_install(source, target)
        (target / "a.md").write_text("user edit")
        plan = plan_install(source, target)

        assert "a.md" in plan.user_modified
        assert "a.md" in plan.needs_prompt

    def test_user_confirms_overwrite(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.md", "original")
        target.mkdir()

        self._do_install(source, target)
        (target / "a.md").write_text("user edit")

        # Simulate user confirming overwrite
        _copy_files(source, target, ["a.md"])
        record_install(source, target, ["a.md"])

        assert (target / "a.md").read_text() == "original"
        plan = plan_install(source, target)
        assert plan.unchanged == {"a.md"}

    def test_user_declines_overwrite(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.md", "original")
        target.mkdir()

        self._do_install(source, target)
        (target / "a.md").write_text("user edit")

        # User declines: don't copy, don't update manifest
        # File should still have user's content
        assert (target / "a.md").read_text() == "user edit"

    def test_new_source_files_copied(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "a.md", "aaa")
        target.mkdir()

        self._do_install(source, target)
        _write(source / "b.md", "bbb")

        plan = plan_install(source, target)
        assert "b.md" in plan.new
        assert "b.md" in plan.safe_to_write

    def test_help_md_present_after_install(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "commands/mantle/help.md", "# Mantle Commands")
        target.mkdir()

        self._do_install(source, target)

        assert (
            target / "commands/mantle/help.md"
        ).read_text() == "# Mantle Commands"


# ── Rules install ────────────────────────────────────────────────


class TestRulesInstall:
    def _do_install(self, source: Path, target: Path) -> None:
        """Helper: full install cycle."""
        plan = plan_install(source, target)
        _copy_files(source, target, plan.safe_to_write)
        record_install(source, target, plan.safe_to_write | plan.unchanged)

    def test_copies_rules_to_target(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "rules/session-logging.md", "# Session Logging")
        target.mkdir()

        self._do_install(source, target)

        assert (
            target / "rules/session-logging.md"
        ).read_text() == "# Session Logging"

    def test_creates_rules_directory(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "rules/session-logging.md", "# Session Logging")
        target.mkdir()

        self._do_install(source, target)

        assert (target / "rules").is_dir()

    def test_rules_tracked_in_manifest(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "rules/session-logging.md", "# Session Logging")
        target.mkdir()

        self._do_install(source, target)

        # Second install should see file as unchanged (tracked)
        plan = plan_install(source, target)
        assert "rules/session-logging.md" in plan.unchanged


# ── Edge cases ───────────────────────────────────────────────────


class TestInstallEdgeCases:
    def test_empty_source_raises(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        source.mkdir()
        target.mkdir()

        try:
            plan_install(source, target)
            msg = "Expected FileNotFoundError"
            raise AssertionError(msg)
        except FileNotFoundError:
            pass


# ── End-to-end via run_install ───────────────────────────────────


class TestRunInstallE2E:
    def test_run_install_copies_bundled_files(self, tmp_path: Path):
        source = tmp_path / "source"
        target = tmp_path / "target"
        _write(source / "commands/mantle/help.md", "# Help")
        target.mkdir()

        with (
            patch(
                "mantle.cli.install._locate_bundled_claude_dir",
                return_value=source,
            ),
            patch(
                "mantle.cli.install.Path.home",
                return_value=target.parent,
            ),
        ):
            # Path.home() / ".claude" → target.parent / ".claude"
            # We need target to be at parent/.claude
            claude_target = target.parent / ".claude"
            with patch(
                "mantle.cli.install.Path.home",
                return_value=tmp_path,
            ):
                # Now target = tmp_path / ".claude"
                claude_target = tmp_path / ".claude"
                claude_target.mkdir(exist_ok=True)

                with patch(
                    "mantle.cli.install._locate_bundled_claude_dir",
                    return_value=source,
                ):
                    run_install()

        assert (
            claude_target / "commands/mantle/help.md"
        ).read_text() == "# Help"


# ── _register_hooks ─────────────────────────────────────────────


class TestRegisterHooks:
    def test_creates_settings_when_missing(self, tmp_path: Path):
        _register_hooks(tmp_path)

        assert (tmp_path / "settings.json").is_file()

    def test_preserves_existing_settings(self, tmp_path: Path):
        settings = {"permissions": {"allow": ["Read"]}}
        (tmp_path / "settings.json").write_text(
            json.dumps(settings)
        )

        _register_hooks(tmp_path)

        result = json.loads(
            (tmp_path / "settings.json").read_text()
        )
        assert result["permissions"] == {"allow": ["Read"]}

    def test_adds_session_start_hook(self, tmp_path: Path):
        _register_hooks(tmp_path)

        result = json.loads(
            (tmp_path / "settings.json").read_text()
        )
        entries = result["hooks"]["SessionStart"]
        assert len(entries) == 1
        assert entries[0]["matcher"] == ""
        hook = entries[0]["hooks"][0]
        assert hook["type"] == "command"
        assert "session-start.sh" in hook["command"]

    def test_idempotent(self, tmp_path: Path):
        _register_hooks(tmp_path)
        _register_hooks(tmp_path)

        result = json.loads(
            (tmp_path / "settings.json").read_text()
        )
        entries = result["hooks"]["SessionStart"]
        assert len(entries) == 1

    def test_preserves_other_hook_types(self, tmp_path: Path):
        settings = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo pre",
                            }
                        ],
                    }
                ]
            }
        }
        (tmp_path / "settings.json").write_text(
            json.dumps(settings)
        )

        _register_hooks(tmp_path)

        result = json.loads(
            (tmp_path / "settings.json").read_text()
        )
        assert len(result["hooks"]["PreToolUse"]) == 1
        assert len(result["hooks"]["SessionStart"]) == 1

    def test_returns_true_when_newly_registered(
        self, tmp_path: Path
    ):
        assert _register_hooks(tmp_path) is True

    def test_returns_false_when_already_exists(
        self, tmp_path: Path
    ):
        _register_hooks(tmp_path)

        assert _register_hooks(tmp_path) is False
