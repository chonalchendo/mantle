"""Tests for mantle.cli.hooks."""

from __future__ import annotations

import pytest

from mantle.cli import hooks as cli_hooks


def test_show_hook_example_prints_linear(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Linear example starts with shebang and mentions linear."""
    cli_hooks.run_show_hook_example(name="linear")
    out = capsys.readouterr().out
    assert out.startswith("#!/usr/bin/env bash")
    assert "linear" in out.lower()


def test_show_hook_example_prints_jira(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Jira example's setup header mentions acli."""
    cli_hooks.run_show_hook_example(name="jira")
    out = capsys.readouterr().out
    assert "acli" in out


def test_show_hook_example_prints_slack(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Slack example mentions SLACK_WEBHOOK_URL."""
    cli_hooks.run_show_hook_example(name="slack")
    out = capsys.readouterr().out
    assert "SLACK_WEBHOOK_URL" in out


def test_show_hook_example_unknown_exits_non_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Unknown example name exits 1 and lists available names."""
    with pytest.raises(SystemExit) as exc:
        cli_hooks.run_show_hook_example(name="bogus")
    assert exc.value.code == 1
    err = capsys.readouterr().out
    assert "linear" in err
