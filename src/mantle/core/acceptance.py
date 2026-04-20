"""Structured acceptance criteria — schema, rendering, parsing, flipping.

This module owns the pure logic for acceptance criteria on an issue:
a frozen Pydantic schema, a canonical markdown view, a migration parser
for legacy checkbox bodies, and a tuple-level flip helper. It has no
filesystem or CLI dependencies — ``core/issues.py`` wires this into
``save_issue`` / ``transition_to_approved``.
"""

from __future__ import annotations

import re

import pydantic

# ── Data model ───────────────────────────────────────────────────


class AcceptanceCriterion(pydantic.BaseModel, frozen=True):
    """Single acceptance criterion with explicit pass/fail state.

    Attributes:
        id: Stable identifier, e.g. ``ac-01``.
        text: Human-readable criterion text.
        passes: Whether verification has confirmed the criterion.
        waived: Whether the criterion is explicitly waived.
        waiver_reason: Free-text reason when ``waived`` is True.
    """

    id: str
    text: str
    passes: bool = False
    waived: bool = False
    waiver_reason: str | None = None


# ── Exceptions ───────────────────────────────────────────────────


class CriterionNotFoundError(Exception):
    """Raised when a criterion id is not present in the tuple.

    Attributes:
        ac_id: The criterion id that was not found.
    """

    def __init__(self, ac_id: str) -> None:
        self.ac_id = ac_id
        super().__init__(f"Acceptance criterion '{ac_id}' not found")


class DuplicateCriterionIdError(Exception):
    """Raised when a tuple of criteria has a repeated id.

    Attributes:
        ac_id: The duplicated criterion id.
    """

    def __init__(self, ac_id: str) -> None:
        self.ac_id = ac_id
        super().__init__(f"Duplicate acceptance criterion id '{ac_id}'")


# ── Rendering ────────────────────────────────────────────────────


def render_ac_section(
    criteria: tuple[AcceptanceCriterion, ...],
) -> str:
    """Render the canonical ``## Acceptance criteria`` markdown block.

    Produces one checkbox line per criterion. A criterion whose
    ``passes`` or ``waived`` is True renders ``[x]``; waived entries
    with ``passes=False`` also gain a ``(waived)`` suffix.

    Args:
        criteria: Structured acceptance criteria.

    Returns:
        Markdown section starting with ``## Acceptance criteria`` and
        ending with a trailing newline. Empty input yields a
        ``_None defined._`` placeholder.
    """
    if not criteria:
        return "## Acceptance criteria\n\n_None defined._\n"
    lines = ["## Acceptance criteria", ""]
    for c in criteria:
        box = "[x]" if c.passes or c.waived else "[ ]"
        suffix = " (waived)" if c.waived and not c.passes else ""
        lines.append(f"- {box} {c.id}: {c.text}{suffix}")
    lines.append("")
    return "\n".join(lines)


_AC_SECTION_RE = re.compile(
    r"(?ms)^##\s+Acceptance\s+criteria\b.*?(?=^##\s|\Z)"
)


def replace_ac_section(body: str, rendered: str) -> str:
    """Swap the ``## Acceptance criteria`` section, appending if absent.

    Args:
        body: Full issue markdown body.
        rendered: Output of :func:`render_ac_section`.

    Returns:
        Body with the AC section replaced in place when it exists, or
        appended (separated by a blank line) when it does not.
    """
    if _AC_SECTION_RE.search(body):
        return _AC_SECTION_RE.sub(rendered.rstrip() + "\n\n", body, count=1)
    separator = "\n\n" if body and not body.endswith("\n\n") else ""
    return body + separator + rendered


# ── Parsing (migration) ──────────────────────────────────────────


_CHECKBOX_RE = re.compile(r"^\s*-\s*\[(?P<box>[ xX])\]\s*(?P<text>.+?)\s*$")


def parse_ac_section(
    body: str,
) -> tuple[AcceptanceCriterion, ...]:
    """Extract legacy markdown checkboxes from body for migration.

    Scans lines under ``## Acceptance criteria`` (until the next
    top-level heading) and returns structured criteria with
    auto-assigned ids ``ac-01..N``. ``passes`` is set from the checkbox
    state.

    Args:
        body: Full issue markdown body.

    Returns:
        Tuple of criteria, in document order. ``()`` when the section
        is missing or empty.
    """
    match = _AC_SECTION_RE.search(body)
    if not match:
        return ()
    section = match.group(0)
    lines = section.splitlines()[1:]  # skip the heading
    items: list[AcceptanceCriterion] = []
    for line in lines:
        m = _CHECKBOX_RE.match(line)
        if not m:
            continue
        raw_text = m.group("text").strip()
        # Strip any pre-existing 'ac-NN: ' prefix so re-parse is a
        # no-op. Also strip a trailing ' (waived)' marker.
        cleaned = re.sub(r"^ac-\d{2}:\s*", "", raw_text)
        cleaned = re.sub(r"\s*\(waived\)\s*$", "", cleaned)
        passes = m.group("box").lower() == "x"
        items.append(
            AcceptanceCriterion(
                id=f"ac-{len(items) + 1:02d}",
                text=cleaned,
                passes=passes,
            )
        )
    return tuple(items)


# ── Tuple-level mutation ─────────────────────────────────────────


def flip_criterion(
    criteria: tuple[AcceptanceCriterion, ...],
    ac_id: str,
    *,
    passes: bool,
    waived: bool = False,
    waiver_reason: str | None = None,
) -> tuple[AcceptanceCriterion, ...]:
    """Return a new tuple with the matching criterion updated.

    Args:
        criteria: Input tuple.
        ac_id: Criterion id to update.
        passes: New ``passes`` value.
        waived: New ``waived`` value.
        waiver_reason: New ``waiver_reason`` value.

    Returns:
        A new tuple with one criterion replaced.

    Raises:
        CriterionNotFoundError: If ``ac_id`` is not present.
    """
    found = False
    out: list[AcceptanceCriterion] = []
    for c in criteria:
        if c.id == ac_id:
            out.append(
                c.model_copy(
                    update={
                        "passes": passes,
                        "waived": waived,
                        "waiver_reason": waiver_reason,
                    }
                )
            )
            found = True
        else:
            out.append(c)
    if not found:
        raise CriterionNotFoundError(ac_id)
    return tuple(out)


# ── Predicates ───────────────────────────────────────────────────


def all_pass_or_waived(
    criteria: tuple[AcceptanceCriterion, ...],
) -> bool:
    """True when every criterion either passes or is waived.

    An empty tuple returns True — issues without structured ACs cannot
    block approval.

    Args:
        criteria: Input tuple.

    Returns:
        True if no criterion is pending.
    """
    return all(c.passes or c.waived for c in criteria)


def assert_unique_ids(
    criteria: tuple[AcceptanceCriterion, ...],
) -> None:
    """Raise :class:`DuplicateCriterionIdError` if any id repeats.

    Args:
        criteria: Input tuple.

    Raises:
        DuplicateCriterionIdError: If two criteria share an id.
    """
    seen: set[str] = set()
    for c in criteria:
        if c.id in seen:
            raise DuplicateCriterionIdError(c.id)
        seen.add(c.id)
