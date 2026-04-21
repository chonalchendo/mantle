"""Tests for mantle.cli.models."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from mantle.cli import models
from mantle.core import project
from mantle.core.project import _FALLBACK_STAGE_MODELS

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "test@example.com"


@pytest.fixture(autouse=True)
def _mock_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock git identity for all tests in this module."""
    monkeypatch.setattr(
        "mantle.core.state.resolve_git_identity",
        lambda: MOCK_EMAIL,
    )


class TestRunModelTier:
    def test_prints_json_to_stdout(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        project.init_project(tmp_path, "test-project")

        models.run_model_tier(project_dir=tmp_path)

        captured = capsys.readouterr()
        payload = json.loads(captured.out)

        assert set(payload.keys()) == {
            "shape",
            "plan_stories",
            "implement",
            "simplify",
            "verify",
            "review",
            "retrospective",
        }
        for value in payload.values():
            assert isinstance(value, str)

    def test_json_matches_load_model_tier(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        project.init_project(tmp_path, "test-project")

        models.run_model_tier(project_dir=tmp_path)

        captured = capsys.readouterr()
        stages = project.load_model_tier(tmp_path)
        assert json.loads(captured.out) == stages.model_dump()

    def test_fallback_when_no_config(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        models.run_model_tier(project_dir=tmp_path)

        captured = capsys.readouterr()
        assert json.loads(captured.out) == _FALLBACK_STAGE_MODELS.model_dump()

    def test_override_applied_in_json(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        project.init_project(tmp_path, "test-project")
        project.update_config(
            tmp_path,
            models={
                "preset": "balanced",
                "overrides": {"implement": "haiku"},
            },
        )

        models.run_model_tier(project_dir=tmp_path)

        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload["implement"] == "haiku"
        assert payload["shape"] == "opus"

    def test_stderr_has_summary_table(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        project.init_project(tmp_path, "test-project")

        models.run_model_tier(project_dir=tmp_path)

        captured = capsys.readouterr()
        assert "Resolved model tier" in captured.err
        assert "shape" in captured.err
