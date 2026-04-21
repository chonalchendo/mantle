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

BATCH_2_FILES = (
    "design-product.md",
    "design-system.md",
    "distill.md",
    "fix.md",
    "idea.md",
    "implement.md",
    "plan-issues.md",
)

BATCH_3_FILES = (
    "plan-stories.md",
    "query.md",
    "research.md",
    "retrospective.md",
    "review.md",
    "revise-product.md",
    "revise-system.md",
)

BATCH_4_FILES = (
    "scout.md",
    "shape-issue.md",
    "simplify.md",
    "verify.md",
)

# Files in claude/commands/mantle/ that are NOT swept by issue 44:
# - help.md: pure help text, no Read tool usage
# - resume.md.j2 / status.md.j2: compiled templates run through jinja
#   and substituted at install time; literal `.mantle/` mentions in
#   their bodies are documentation, not Read targets
EXCLUDED_FROM_FULL_AUDIT = frozenset(
    {
        "help.md",
        "resume.md.j2",
        "status.md.j2",
    }
)


def _assert_no_hardcoded_reads(files: tuple[str, ...]) -> None:
    offenders = []
    for name in files:
        text = (PROMPTS_DIR / name).read_text()
        for match in HARDCODED_READ_RE.finditer(text):
            line_num = text[: match.start()].count("\n") + 1
            offenders.append(f"{name}:{line_num}: {match.group(0)}")
    assert not offenders, "Hardcoded reads found:\n" + "\n".join(offenders)


def _assert_includes_resolve_prelude(files: tuple[str, ...]) -> None:
    # Accept either the bare form `MANTLE_DIR=$(mantle where)` or the
    # session-hook-aware fallback form
    # `MANTLE_DIR="${MANTLE_DIR:-$(mantle where)}"` used by build.md
    # (see issue 82 — session-start hook exports MANTLE_DIR).
    accepted = (
        "MANTLE_DIR=$(mantle where)",
        'MANTLE_DIR="${MANTLE_DIR:-$(mantle where)}"',
    )
    missing = [
        name
        for name in files
        if not any(
            form in (PROMPTS_DIR / name).read_text() for form in accepted
        )
    ]
    assert not missing, "Missing resolve prelude in: " + ", ".join(missing)


def test_batch_1_no_hardcoded_mantle_reads() -> None:
    """Story 2 sweep: batch 1 prompts have no Read .mantle/ targets."""
    _assert_no_hardcoded_reads(BATCH_1_FILES)


def test_batch_1_includes_resolve_prelude() -> None:
    """Each batch-1 prompt declares MANTLE_DIR=$(mantle where)."""
    _assert_includes_resolve_prelude(BATCH_1_FILES)


def test_batch_2_no_hardcoded_mantle_reads() -> None:
    """Story 3 sweep: batch 2 prompts have no Read .mantle/ targets."""
    _assert_no_hardcoded_reads(BATCH_2_FILES)


def test_batch_2_includes_resolve_prelude() -> None:
    """Each batch-2 prompt declares MANTLE_DIR=$(mantle where)."""
    _assert_includes_resolve_prelude(BATCH_2_FILES)


def test_batch_3_no_hardcoded_mantle_reads() -> None:
    """Story 4 sweep: batch 3 prompts have no Read .mantle/ targets."""
    _assert_no_hardcoded_reads(BATCH_3_FILES)


def test_batch_3_includes_resolve_prelude() -> None:
    """Each batch-3 prompt declares MANTLE_DIR=$(mantle where)."""
    _assert_includes_resolve_prelude(BATCH_3_FILES)


def test_batch_4_no_hardcoded_mantle_reads() -> None:
    """Story 5 sweep: batch 4 prompts have no Read .mantle/ targets."""
    _assert_no_hardcoded_reads(BATCH_4_FILES)


def test_batch_4_includes_resolve_prelude() -> None:
    """Each batch-4 prompt declares MANTLE_DIR=$(mantle where)."""
    _assert_includes_resolve_prelude(BATCH_4_FILES)


def test_full_tree_no_hardcoded_mantle_reads() -> None:
    """Regression guard: no `Read .mantle/` anywhere under claude/commands/mantle/.

    Walks every prompt file (excluding pure help text and compiled
    jinja templates) and asserts the HARDCODED_READ_RE finds nothing.
    """
    offenders = []
    for path in sorted(PROMPTS_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.name in EXCLUDED_FROM_FULL_AUDIT:
            continue
        text = path.read_text()
        for match in HARDCODED_READ_RE.finditer(text):
            line_num = text[: match.start()].count("\n") + 1
            offenders.append(f"{path.name}:{line_num}: {match.group(0)}")
    assert not offenders, (
        "Hardcoded `Read .mantle/` references found:\n" + "\n".join(offenders)
    )
