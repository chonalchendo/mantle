"""Token-cost audit of Markdown prompt files using tiktoken."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

import tiktoken

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_ENCODING = "cl100k_base"


# ── Data model ──────────────────────────────────────────────────


@dataclass(frozen=True)
class AuditEntry:
    """One file's token-count result in an audit."""

    path: Path
    tokens: int
    percent_of_total: float


# ── Public API ──────────────────────────────────────────────────


def count_tokens_in_file(
    path: Path,
    encoding_name: str = DEFAULT_ENCODING,
) -> int:
    """Return the token count for the file's UTF-8 contents."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(path.read_text(encoding="utf-8")))


def audit_directory(
    commands_dir: Path,
    encoding_name: str = DEFAULT_ENCODING,
) -> list[AuditEntry]:
    """Count tokens for every .md file in commands_dir, sorted descending.

    Uses rglob to traverse subdirectories recursively.
    """
    paths = sorted(commands_dir.rglob("*.md"))
    counts = [(p, count_tokens_in_file(p, encoding_name)) for p in paths]
    total = sum(c for _, c in counts) or 1  # avoid div-by-zero on empty dir
    entries = [
        AuditEntry(path=p, tokens=c, percent_of_total=c / total * 100)
        for p, c in counts
    ]
    entries.sort(key=lambda e: e.tokens, reverse=True)
    return entries


def audit_paths(
    paths: list[Path],
    encoding_name: str = DEFAULT_ENCODING,
) -> dict[str, list[AuditEntry]]:
    """Audit each root path and group results by surface label.

    Surface label is the basename of each path (e.g., 'mantle' for
    claude/commands/mantle, 'skills' for /Users/conal/test-vault/skills).
    Returns an insertion-ordered dict so report ordering is stable.

    Percent-of-total within each surface is computed against that
    surface's total, not the overall total, so sub-tables rank
    intra-surface cost.

    Args:
        paths: List of directory paths to audit.
        encoding_name: tiktoken encoding name.

    Returns:
        Insertion-ordered dict mapping surface label to list of AuditEntry.
    """
    used_labels: dict[str, str] = {}  # label -> original path str
    result: dict[str, list[AuditEntry]] = {}

    for path in paths:
        label = path.name or str(path)
        # Disambiguate if two paths share a basename
        if label in used_labels and used_labels[label] != str(path):
            label = str(path)
        used_labels[label] = str(path)
        result[label] = audit_directory(path, encoding_name)

    return result


def format_report(
    per_surface: dict[str, list[AuditEntry]],
    heading: str = "Before",
    encoding_name: str = DEFAULT_ENCODING,
    today: date | None = None,
) -> str:
    """Return the full audit report Markdown for one or more surfaces.

    Emits one ``### <surface>`` sub-section under ``## <heading>`` per
    surface. Each sub-section has its own ranked table, per-surface total,
    and per-surface top-3. Ends with an overall total line.

    Args:
        per_surface: Dict mapping surface label to list of AuditEntry.
        heading: Section heading (default: "Before").
        encoding_name: tiktoken encoding name used for the measurement note.
        today: Date for the report header. Defaults to ``date.today()``.

    Returns:
        Full report as a Markdown string.
    """
    today_iso = (today or date.today()).isoformat()
    lines: list[str] = [
        f"# Mantle token audit — {today_iso}",
        "",
        f"Measured with tiktoken (encoding: {encoding_name},"
        " ~97% Claude BPE proxy).",
        "",
        f"## {heading}",
        "",
    ]

    grand_total_tokens = 0
    grand_total_files = 0

    for surface, entries in per_surface.items():
        lines.append(f"### {surface}")
        lines.append("")
        lines.append("| Rank | File | Tokens | % of total |")
        lines.append("| ---- | ---- | ------:| ----------:|")

        for rank, entry in enumerate(entries, start=1):
            name = entry.path.stem
            lines.append(
                f"| {rank} | {name} | {entry.tokens:,} |"
                f" {entry.percent_of_total:.1f}% |"
            )

        surface_total = sum(e.tokens for e in entries)
        n = len(entries)
        grand_total_tokens += surface_total
        grand_total_files += n

        lines.append("")
        lines.append(
            f"**Total ({surface}):** {surface_total:,} tokens"
            f" across {n} file(s)."
        )

        if entries:
            top3_names = ", ".join(f"{e.path.stem}.md" for e in entries[:3])
            lines.append("")
            lines.append(
                f"**Top 3 candidates for rewrite ({surface}):** {top3_names}"
            )

        lines.append("")

    lines.append(
        f"**Total (all surfaces):** {grand_total_tokens:,} tokens"
        f" across {grand_total_files} files."
    )
    lines.append("")
    return "\n".join(lines)


def append_after_section(
    report_path: Path,
    per_surface_after: dict[str, list[AuditEntry]],
) -> None:
    """Append 'After' and 'Delta summary' sections to an existing report.

    Parses the existing Before tables (one per surface) to compute
    per-file before→after deltas. Appends an ``## After`` section with
    per-surface sub-tables and a ``## Delta summary`` with per-surface
    and overall totals.

    Args:
        report_path: Path to the existing report file.
        per_surface_after: Dict mapping surface label to after AuditEntry list.

    Raises:
        ValueError: If report_path already contains an ``## After`` section,
            or if the Before token table cannot be parsed for any surface.
    """
    existing = report_path.read_text(encoding="utf-8")
    if "## After" in existing:
        raise ValueError(
            f"{report_path} already contains an '## After' section."
            " Re-running --append would corrupt the report."
        )

    # Parse before tokens per surface
    before_per_surface = _parse_before_tokens_per_surface(
        existing, report_path, list(per_surface_after.keys())
    )

    lines: list[str] = ["", "## After", ""]

    grand_total_before = 0
    grand_total_after = 0
    delta_summary_bullets: list[str] = []

    for surface, after_entries in per_surface_after.items():
        before_tokens = before_per_surface.get(surface, {})

        lines.append(f"### {surface}")
        lines.append("")
        lines.append("| Rank | File | Before | After | Saved | % saved |")
        lines.append("| ---- | ---- | ------:| -----:| -----:| -------:|")

        surface_before_total = 0
        surface_after_total = 0
        surface_top3_saved = 0
        surface_top3_before = 0

        for rank, entry in enumerate(after_entries, start=1):
            name = entry.path.stem
            before = before_tokens.get(name, 0)
            after = entry.tokens
            saved = before - after
            pct_saved = (saved / before * 100) if before else 0.0
            lines.append(
                f"| {rank} | {name} | {before:,} | {after:,} |"
                f" {saved:,} | {pct_saved:.1f}% |"
            )
            surface_before_total += before
            surface_after_total += after
            if rank <= 3:
                surface_top3_saved += saved
                surface_top3_before += before

        surface_saved = surface_before_total - surface_after_total
        surface_pct = (
            (surface_saved / surface_before_total * 100)
            if surface_before_total
            else 0.0
        )
        surface_top3_pct = (
            (surface_top3_saved / surface_top3_before * 100)
            if surface_top3_before
            else 0.0
        )

        lines.append("")
        grand_total_before += surface_before_total
        grand_total_after += surface_after_total

        delta_summary_bullets.append(
            f"- **{surface}**: top-3 saved {surface_top3_saved:,} tokens"
            f" ({surface_top3_pct:.1f}%), total saved {surface_saved:,}"
            f" tokens ({surface_pct:.1f}% reduction)."
        )

    grand_saved = grand_total_before - grand_total_after
    grand_pct = (
        (grand_saved / grand_total_before * 100) if grand_total_before else 0.0
    )

    lines += [
        "## Delta summary",
        "",
    ]
    lines += delta_summary_bullets
    lines += [
        f"- **Overall:** {grand_saved:,} tokens saved"
        f" ({grand_pct:.1f}% reduction).",
        "",
    ]

    report_path.write_text(
        existing.rstrip("\n") + "\n" + "\n".join(lines),
        encoding="utf-8",
    )


# ── Private helpers ─────────────────────────────────────────────


def _parse_before_tokens_per_surface(
    text: str,
    report_path: Path,
    surfaces: list[str],
) -> dict[str, dict[str, int]]:
    """Extract per-surface file → token count maps from a Before report.

    Scopes parsing to each ``### <surface>`` section to avoid cross-surface
    collisions when file names repeat across surfaces.

    Args:
        text: Full report text.
        report_path: Path for error messages.
        surfaces: Surface labels to parse (in order).

    Returns:
        Dict mapping surface label to {filename_stem: token_count}.

    Raises:
        ValueError: If no table rows can be parsed from the file.
    """
    result: dict[str, dict[str, int]] = {}
    # Match rows like: | 1 | build | 1,234 | 12.3% |
    row_pattern = re.compile(
        r"^\|\s*\d+\s*\|\s*(\S+)\s*\|\s*([\d,]+)\s*\|", re.MULTILINE
    )

    # Split text into per-surface sections by ### headings
    section_pattern = re.compile(r"^### (.+)$", re.MULTILINE)
    section_starts = [
        (m.group(1).strip(), m.start()) for m in section_pattern.finditer(text)
    ]
    # Build section ranges
    sections: dict[str, str] = {}
    for i, (name, start) in enumerate(section_starts):
        end = (
            section_starts[i + 1][1]
            if i + 1 < len(section_starts)
            else len(text)
        )
        sections[name] = text[start:end]

    found_any = False
    for surface in surfaces:
        section_text = sections.get(surface, "")
        surface_tokens: dict[str, int] = {}
        for match in row_pattern.finditer(section_text):
            name = match.group(1)
            tokens = int(match.group(2).replace(",", ""))
            surface_tokens[name] = tokens
            found_any = True
        result[surface] = surface_tokens

    if not found_any:
        raise ValueError(
            f"Could not parse Before token table from {report_path}"
        )
    return result
