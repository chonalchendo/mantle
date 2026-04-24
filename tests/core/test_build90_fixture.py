"""Regression test using real build-90 sub-agent data from tests/fixtures/."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from mantle.core import telemetry

# Path to the checked-in fixture directory (relative to project root).
_FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "build-90-session"

_SESSION_ID = "514d3e78-4614-4206-a4c1-4f26dafe9e10"


def test_build90_produces_three_implement_one_simplify_one_verify() -> None:
    """Real build-90 session data yields 3 implement + 1 simplify + 1 verify."""
    subagent_paths = telemetry.find_subagent_files(
        _SESSION_ID,
        projects_root=_FIXTURE_ROOT,
    )

    assert len(subagent_paths) == 5, (
        f"Expected 5 sub-agent files, found {len(subagent_paths)}"
    )

    runs = telemetry.group_stories(
        parent_turns=(),
        subagent_paths=subagent_paths,
        stage_windows=(),
    )

    stage_counts = Counter(run.stage for run in runs)
    assert stage_counts == Counter({"implement": 3, "simplify": 1, "verify": 1})
