"""Tests for mantle top-level CLI --help panel grouping."""

from __future__ import annotations

import pytest
from rich.console import Console

from mantle.cli import main as main_module
from mantle.cli.groups import GROUPS


def _render_help() -> str:
    """Render 'mantle --help' via a deterministic recording Console."""
    console = Console(
        width=120,
        force_terminal=True,
        highlight=False,
        color_system=None,
        legacy_windows=False,
        record=True,
    )
    with pytest.raises(SystemExit):
        main_module.app("--help", console=console)
    return console.export_text()


_EXPECTED_PANEL_ORDER = [
    "Setup & plumbing",
    "Idea & Validation",
    "Design",
    "Planning",
    "Implementation",
    "Review & Verification",
    "Capture",
    "Knowledge",
]


_EXPECTED_COMMAND_PANELS: dict[str, str] = {
    # setup
    "init": "Setup & plumbing",
    "init-vault": "Setup & plumbing",
    "install": "Setup & plumbing",
    "compile": "Setup & plumbing",
    "where": "Setup & plumbing",
    "introspect-project": "Setup & plumbing",
    "set-slices": "Setup & plumbing",
    "storage": "Setup & plumbing",
    "migrate-storage": "Setup & plumbing",
    "show-hook-example": "Setup & plumbing",
    # idea
    "save-idea": "Idea & Validation",
    "save-challenge": "Idea & Validation",
    "save-brainstorm": "Idea & Validation",
    "save-research": "Idea & Validation",
    "save-scout": "Idea & Validation",
    # design
    "save-product-design": "Design",
    "save-revised-product-design": "Design",
    "save-system-design": "Design",
    "save-revised-system-design": "Design",
    "save-adoption": "Design",
    "save-decision": "Design",
    "save-verification-strategy": "Design",
    # planning
    "save-issue": "Planning",
    "save-shaped-issue": "Planning",
    "save-story": "Planning",
    "update-skills": "Planning",
    "transition-issue-approved": "Planning",
    "transition-issue-implementing": "Planning",
    "transition-issue-implemented": "Planning",
    "transition-issue-verified": "Planning",
    # impl
    "update-story-status": "Implementation",
    "collect-changed-files": "Implementation",
    "collect-issue-files": "Implementation",
    "collect-issue-diff-stats": "Implementation",
    "build-start": "Implementation",
    "build-finish": "Implementation",
    # review
    "save-review-result": "Review & Verification",
    "load-review-result": "Review & Verification",
    # capture
    "save-bug": "Capture",
    "save-inbox-item": "Capture",
    "save-session": "Capture",
    "update-bug-status": "Capture",
    "update-inbox-status": "Capture",
    # knowledge
    "save-learning": "Knowledge",
    "save-distillation": "Knowledge",
    "load-distillation": "Knowledge",
    "list-distillations": "Knowledge",
    "save-skill": "Knowledge",
    "list-skills": "Knowledge",
    "list-tags": "Knowledge",
    "show-patterns": "Knowledge",
}


def _panel_marker(title: str) -> str:
    """Return the unique box-drawing header marker for a Rich panel."""
    return f"─ {title} ─"


def test_all_eight_panels_render_in_order() -> None:
    """All eight panel titles appear in declared sort_key order."""
    text = _render_help()
    positions = [text.find(_panel_marker(t)) for t in _EXPECTED_PANEL_ORDER]
    for title, pos in zip(_EXPECTED_PANEL_ORDER, positions, strict=True):
        assert pos != -1, f"panel title not rendered: {title!r}"
    assert positions == sorted(positions), (
        f"panels rendered out of order: "
        f"{list(zip(_EXPECTED_PANEL_ORDER, positions, strict=True))}"
    )


def test_every_command_assigned_to_expected_panel() -> None:
    """Each command name appears after its expected panel header."""
    text = _render_help()

    # Build panel → (start, end) text ranges in render order.
    panel_positions = [
        (p, text.find(_panel_marker(p))) for p in _EXPECTED_PANEL_ORDER
    ]
    for title, pos in panel_positions:
        assert pos != -1, f"panel missing: {title!r}"

    panel_ranges: dict[str, tuple[int, int]] = {}
    for i, (title, pos) in enumerate(panel_positions):
        end = (
            panel_positions[i + 1][1]
            if i + 1 < len(panel_positions)
            else len(text)
        )
        panel_ranges[title] = (pos, end)

    for cmd, expected_panel in _EXPECTED_COMMAND_PANELS.items():
        start, end = panel_ranges[expected_panel]
        segment = text[start:end]
        assert cmd in segment, (
            f"command {cmd!r} not found under panel {expected_panel!r}; "
            f"segment was:\n{segment}"
        )


def test_no_command_ungrouped() -> None:
    """Every registered top-level command has a group from GROUPS."""
    group_values = set(GROUPS.values())
    names = [n for n in main_module.app if not n.startswith("-")]
    assert names, "expected top-level commands to be registered"

    for name in names:
        cmd = main_module.app[name]
        cmd_groups = getattr(cmd, "group", None)
        assert cmd_groups, f"command has no group assigned: {name}"
        assert any(g in group_values for g in cmd_groups), (
            f"command {name} group {cmd_groups!r} not in GROUPS"
        )


def test_groups_registry_keys_and_order() -> None:
    """GROUPS keys and sort_key values match the expected taxonomy."""
    expected = {
        "setup": (1, "Setup & plumbing"),
        "idea": (2, "Idea & Validation"),
        "design": (3, "Design"),
        "planning": (4, "Planning"),
        "impl": (5, "Implementation"),
        "review": (6, "Review & Verification"),
        "capture": (7, "Capture"),
        "knowledge": (8, "Knowledge"),
    }
    assert set(GROUPS.keys()) == set(expected.keys())
    for key, (sort_key, name) in expected.items():
        grp = GROUPS[key]
        assert grp.name == name, f"{key}: name mismatch"
        assert grp.sort_key == sort_key, f"{key}: sort_key mismatch"
