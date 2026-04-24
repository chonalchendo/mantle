"""Shared parity helper for prompt-layer regression testing.

Provides :class:`ParityResult`, :func:`normalize_prompt_output`, and
:func:`run_prompt_parity` for comparing rendered prompt output against
a stored baseline.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mantle.core import compiler

if TYPE_CHECKING:
    from pathlib import Path

# ── Compiled normalizer patterns ─────────────────────────────────

# Order matters: timestamp before date so the date inside a timestamp
# does not get matched first and leave the time portion un-replaced.
_RE_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?")
_RE_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_RE_SESSION_UUID = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_RE_ABSOLUTE_PATH = re.compile(r"(?:/Users|/home|/tmp)/\S+")
_RE_GIT_SHA = re.compile(r"\b[0-9a-f]{7,40}\b")


# ── Public API ───────────────────────────────────────────────────


@dataclass(frozen=True)
class ParityResult:
    """Structured outcome of a prompt-parity comparison.

    Attributes:
        command: The command name that was compared.
        baseline_text: The normalized baseline text passed in by the caller.
        current_text: The normalized current prompt text that was rendered.
        matches: True when ``current_text == baseline_text``.
        diff: Unified diff string; empty string on match.
    """

    command: str
    baseline_text: str
    current_text: str
    matches: bool
    diff: str


def normalize_prompt_output(text: str) -> str:
    """Strip volatile fields from a prompt-layer text capture.

    Replaces, in order:

    - ISO-8601 timestamps (e.g., ``2026-04-24T12:32:00Z``) with
      ``<TIMESTAMP>``
    - ISO-8601 dates (``2026-04-24``) with ``<DATE>``
    - Session UUIDs (8-4-4-4-12 hex) with ``<SESSION_ID>``
    - Absolute POSIX paths (``/Users/...``, ``/home/...``, ``/tmp/...``)
      with ``<PATH>``
    - Git SHAs (7-40 lowercase hex, bounded by word boundaries) with
      ``<GIT_SHA>``

    Args:
        text: Raw prompt text to normalize.

    Returns:
        Text with volatile fields replaced by stable placeholders.
    """
    text = _RE_TIMESTAMP.sub("<TIMESTAMP>", text)
    text = _RE_DATE.sub("<DATE>", text)
    text = _RE_SESSION_UUID.sub("<SESSION_ID>", text)
    text = _RE_ABSOLUTE_PATH.sub("<PATH>", text)
    text = _RE_GIT_SHA.sub("<GIT_SHA>", text)
    return text


def run_prompt_parity(
    command: str,
    fixture: Path,
    baseline: str,
) -> ParityResult:
    """Render ``command`` against ``fixture``, normalize, compare to ``baseline``.

    For static commands (any ``claude/commands/mantle/<command>.md`` that is
    not a Jinja template), reads the raw prompt file. For j2-compiled commands
    (e.g. ``resume``, ``status``), runs ``compiler.compile()`` in-process
    against the fixture and reads the rendered output.

    The ``baseline`` argument is expected to already be in normalized form —
    this function normalizes ``current_text`` once before comparing, but does
    **not** double-normalize the baseline.

    Args:
        command: Command name (without ``.md`` extension).
        fixture: Project root directory containing ``.mantle/``.
        baseline: Normalized baseline text to compare against.

    Returns:
        :class:`ParityResult` with a unified diff on mismatch or an empty
        ``diff`` string on match.
    """
    tpl_dir = compiler.template_dir()
    j2_path = tpl_dir / f"{command}.md.j2"

    if j2_path.exists():
        target_dir = fixture / "_parity_compile_out"
        compiler.compile(fixture, target_dir=target_dir)
        raw = (target_dir / f"{command}.md").read_text(encoding="utf-8")
    else:
        raw = (tpl_dir / f"{command}.md").read_text(encoding="utf-8")

    current = normalize_prompt_output(raw)
    matches = current == baseline

    diff_lines = list(
        difflib.unified_diff(
            baseline.splitlines(keepends=True),
            current.splitlines(keepends=True),
            fromfile=f"{command}.md (baseline)",
            tofile=f"{command}.md (current)",
        )
    )
    diff = "".join(diff_lines)

    return ParityResult(
        command=command,
        baseline_text=baseline,
        current_text=current,
        matches=matches,
        diff=diff,
    )
