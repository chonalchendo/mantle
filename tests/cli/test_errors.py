"""Tests for mantle.cli.errors."""

from __future__ import annotations

import pytest

from mantle.cli import errors


class TestPrintError:
    def test_print_error_writes_to_stderr_only(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        errors.print_error("msg", hint="hint")
        captured = capsys.readouterr()

        assert "Error:" in captured.err
        assert "hint" in captured.err
        assert captured.out == ""

    def test_print_error_includes_message_and_hint_on_separate_lines(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        errors.print_error("something went wrong", hint="try again later")
        captured = capsys.readouterr()

        lines = captured.err.splitlines()
        # message and hint should appear on separate lines
        assert any("something went wrong" in line for line in lines)
        assert any("try again later" in line for line in lines)
        # they should not be on the same line
        assert not any(
            "something went wrong" in line and "try again later" in line
            for line in lines
        )

    def test_hint_is_keyword_only(self) -> None:
        with pytest.raises(TypeError):
            errors.print_error("m", "h")  # type: ignore[call-arg]


class TestExitWithError:
    def test_exit_with_error_raises_systemexit_with_default_code_1(
        self,
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            errors.exit_with_error("m", hint="h")

        assert exc.value.code == 1

    def test_exit_with_error_respects_custom_code(self) -> None:
        with pytest.raises(SystemExit) as exc:
            errors.exit_with_error("m", hint="h", code=2)

        assert exc.value.code == 2

    def test_exit_with_error_prints_before_exit(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit):
            errors.exit_with_error("something failed", hint="do this to fix it")

        captured = capsys.readouterr()
        assert "something failed" in captured.err
        assert "do this to fix it" in captured.err
