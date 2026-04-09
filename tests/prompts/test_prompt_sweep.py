"""Audit tests for hardcoded .mantle/ reads in Claude Code prompts."""

from __future__ import annotations

import re
from pathlib import Path

PROMPTS_DIR = (
    Path(__file__).parent.parent.parent / "claude" / "commands" / "mantle"
)

# Match "Read .mantle/" or "Read `.mantle/" — Read-tool targets only.
# Allows backticks/space between Read and the path.
HARDCODED_READ_RE = re.compile(r"Read[^\n]*?\.mantle/")

BATCH_1_FILES = (
    "adopt.md",
    "add-issue.md",
    "add-skill.md",
    "brainstorm.md",
    "bug.md",
    "build.md",
    "challenge.md",
)


def test_batch_1_no_hardcoded_mantle_reads() -> None:
    """Story 2 sweep: batch 1 prompts have no Read .mantle/ targets."""
    offenders = []
    for name in BATCH_1_FILES:
        text = (PROMPTS_DIR / name).read_text()
        for match in HARDCODED_READ_RE.finditer(text):
            line_num = text[: match.start()].count("\n") + 1
            offenders.append(f"{name}:{line_num}: {match.group(0)}")
    assert not offenders, "Hardcoded reads found:\n" + "\n".join(offenders)


def test_batch_1_includes_resolve_prelude() -> None:
    """Each batch-1 prompt declares MANTLE_DIR=$(mantle where)."""
    missing = []
    for name in BATCH_1_FILES:
        text = (PROMPTS_DIR / name).read_text()
        if "MANTLE_DIR=$(mantle where)" not in text:
            missing.append(name)
    assert not missing, "Missing resolve prelude in: " + ", ".join(missing)


BATCH_2_FILES = (
    "design-product.md",
    "design-system.md",
    "distill.md",
    "fix.md",
    "idea.md",
    "implement.md",
    "plan-issues.md",
)


def test_batch_2_no_hardcoded_mantle_reads() -> None:
    """Story 3 sweep: batch 2 prompts have no Read .mantle/ targets."""
    offenders = []
    for name in BATCH_2_FILES:
        text = (PROMPTS_DIR / name).read_text()
        for match in HARDCODED_READ_RE.finditer(text):
            line_num = text[: match.start()].count("\n") + 1
            offenders.append(f"{name}:{line_num}: {match.group(0)}")
    assert not offenders, "Hardcoded reads found:\n" + "\n".join(offenders)


def test_batch_2_includes_resolve_prelude() -> None:
    """Each batch-2 prompt declares MANTLE_DIR=$(mantle where)."""
    missing = []
    for name in BATCH_2_FILES:
        text = (PROMPTS_DIR / name).read_text()
        if "MANTLE_DIR=$(mantle where)" not in text:
            missing.append(name)
    assert not missing, "Missing resolve prelude in: " + ", ".join(missing)


BATCH_3_FILES = (
    "plan-stories.md",
    "query.md",
    "research.md",
    "retrospective.md",
    "review.md",
    "revise-product.md",
    "revise-system.md",
)


def test_batch_3_no_hardcoded_mantle_reads() -> None:
    """Story 4 sweep: batch 3 prompts have no Read .mantle/ targets."""
    offenders = []
    for name in BATCH_3_FILES:
        text = (PROMPTS_DIR / name).read_text()
        for match in HARDCODED_READ_RE.finditer(text):
            line_num = text[: match.start()].count("\n") + 1
            offenders.append(f"{name}:{line_num}: {match.group(0)}")
    assert not offenders, "Hardcoded reads found:\n" + "\n".join(offenders)


def test_batch_3_includes_resolve_prelude() -> None:
    """Each batch-3 prompt declares MANTLE_DIR=$(mantle where)."""
    missing = []
    for name in BATCH_3_FILES:
        text = (PROMPTS_DIR / name).read_text()
        if "MANTLE_DIR=$(mantle where)" not in text:
            missing.append(name)
    assert not missing, "Missing resolve prelude in: " + ", ".join(missing)
