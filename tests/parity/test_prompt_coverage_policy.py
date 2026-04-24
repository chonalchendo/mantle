"""Policy test: every /mantle:* command must have an explicit coverage classification."""

from __future__ import annotations

from pathlib import Path

import pytest

# Classifications:
# - INTEGRATED: a parity test exists under tests/parity/test_<cmd>_parity.py.
# - UNIT_ONLY: covered by unit tests in tests/core/ or tests/cli/; no parity
#   test needed.
# - DEFERRED: not currently covered; add a parity test when refactor pressure
#   rises.
#
# Every value is a pair (classification, rationale). Rationale is a one-liner
# that explains WHY, not WHAT — readers should understand the trade-off.
_CLASSIFICATIONS: dict[str, tuple[str, str]] = {
    # INTEGRATED
    "build": (
        "INTEGRATED",
        "top-3 token cost; direct refactor target for issues 79/87/88.",
    ),
    "implement": (
        "INTEGRATED",
        "top-3 token cost; direct refactor target for issues 79/87/88.",
    ),
    "plan-stories": (
        "INTEGRATED",
        "top-3 token cost; direct refactor target for issues 79/87/88.",
    ),
    # DEFERRED
    "add-issue": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "add-skill": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "adopt": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "brainstorm": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "bug": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "challenge": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "design-product": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "design-system": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "distill": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "fix": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "help": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "idea": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "inbox": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "patterns": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "plan-issues": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "query": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "refactor": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "research": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "resume": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "retrospective": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "review": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "revise-product": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "revise-system": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "scout": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "shape-issue": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "simplify": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "status": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
    "verify": (
        "DEFERRED",
        "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue.",
    ),
}

_DEFAULT_DEFERRED_RATIONALE = "low refactor pressure; promote to INTEGRATED if it joins the token-cut queue."


def _commands_dir() -> Path:
    """Return the path to the claude/commands/mantle directory."""
    # claude/commands/mantle lives at the repo root during development.
    return (
        Path(__file__).resolve().parents[2] / "claude" / "commands" / "mantle"
    )


def _collect_all_commands() -> set[str]:
    """Collect all command stems from the commands directory."""
    d = _commands_dir()
    names: set[str] = set()
    for p in d.iterdir():
        if p.suffix == ".md":
            names.add(p.stem)
        elif p.name.endswith(".md.j2"):
            names.add(p.name.removesuffix(".md.j2"))
    return names


def test_every_command_has_classification() -> None:
    """Every command file on disk must have an entry in _CLASSIFICATIONS."""
    on_disk = _collect_all_commands()
    missing = on_disk - _CLASSIFICATIONS.keys()
    assert not missing, (
        f"Add these commands to _CLASSIFICATIONS in "
        f"tests/parity/test_prompt_coverage_policy.py: {sorted(missing)}. "
        f"Pick INTEGRATED (write a parity test), UNIT_ONLY (cite the test), "
        f"or DEFERRED (one-line rationale)."
    )


def test_no_orphan_classifications() -> None:
    """Every entry in _CLASSIFICATIONS must correspond to an existing command file."""
    on_disk = _collect_all_commands()
    orphans = _CLASSIFICATIONS.keys() - on_disk
    assert not orphans, (
        f"Remove these stale entries from _CLASSIFICATIONS — the command files "
        f"no longer exist: {sorted(orphans)}."
    )


@pytest.mark.parametrize(
    "classification_value", list(_CLASSIFICATIONS.values())
)
def test_classification_values_are_valid(
    classification_value: tuple[str, str],
) -> None:
    """Each classification must use a valid label and have a non-empty rationale."""
    label, rationale = classification_value
    assert label in {"INTEGRATED", "UNIT_ONLY", "DEFERRED"}, (
        f"Invalid classification label {label!r}; must be INTEGRATED, UNIT_ONLY, or DEFERRED."
    )
    assert rationale.strip(), "Classification rationale must be non-empty."
