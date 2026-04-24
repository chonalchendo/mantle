"""Policy tests: every LLM-invoking template emits mantle stage-begin, skipped templates do not."""

from __future__ import annotations

import re
from pathlib import Path

# Templates that intentionally skip stage-begin (wiring / non-reasoning commands).
_SKIP: frozenset[str] = frozenset(
    {
        "help",
        "resume",
        "status",
        "add-issue",
        "add-skill",
        "bug",
        "inbox",
        "query",
    }
)


def _commands_dir() -> Path:
    """Return the claude/commands/mantle directory path."""
    return (
        Path(__file__).resolve().parents[2] / "claude" / "commands" / "mantle"
    )


def _template_stems() -> list[tuple[str, Path]]:
    """Yield (stem, path) for each template on disk."""
    d = _commands_dir()
    out: list[tuple[str, Path]] = []
    for p in sorted(d.iterdir()):
        if p.suffix == ".md":
            out.append((p.stem, p))
        elif p.name.endswith(".md.j2"):
            out.append((p.name.removesuffix(".md.j2"), p))
    return out


def _body_without_frontmatter(text: str) -> str:
    """Strip the leading YAML frontmatter block (if present)."""
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[2]
    return text


def test_every_non_skipped_template_begins_with_stage_begin() -> None:
    """Every instrumented template must invoke mantle stage-begin before any other mantle call."""
    for stem, path in _template_stems():
        if stem in _SKIP:
            continue
        body = _body_without_frontmatter(path.read_text(encoding="utf-8"))
        stage_begin = body.find("mantle stage-begin ")
        assert stage_begin != -1, (
            f"Template {stem!r} is missing `mantle stage-begin ...` as an instrumented "
            f"stage marker. Either add it or move {stem!r} into the skip list in "
            f"tests/parity/test_stage_begin_coverage.py."
        )
        # Every other `mantle <other-cmd>` call must come after stage-begin.
        for m in re.finditer(r"mantle (\w[\w-]*)", body):
            if m.group(1) == "stage-begin":
                continue
            assert m.start() > stage_begin, (
                f"Template {stem!r} calls `mantle {m.group(1)}` at offset {m.start()}, "
                f"before `mantle stage-begin` at offset {stage_begin}. Move the "
                f"stage-begin line earlier."
            )


def test_skip_list_templates_have_no_stage_begin() -> None:
    """Templates in the skip list must not emit stage-begin (would pollute telemetry)."""
    for stem, path in _template_stems():
        if stem not in _SKIP:
            continue
        body = _body_without_frontmatter(path.read_text(encoding="utf-8"))
        assert "mantle stage-begin " not in body, (
            f"Template {stem!r} is in the skip list but emits `mantle stage-begin`. "
            f"Remove the line or promote {stem!r} out of the skip list."
        )
