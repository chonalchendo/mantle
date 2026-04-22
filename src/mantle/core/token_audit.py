"""Token-cost audit of Markdown prompt files using tiktoken."""

from __future__ import annotations

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
    """One file's token-count result in an audit.

    Attributes:
        path: Absolute or relative path to the audited file.
        tokens: Token count measured by tiktoken.
        percent_of_total: Share of total tokens as a percentage.
    """

    path: Path
    tokens: int
    percent_of_total: float


# ── Public API ──────────────────────────────────────────────────


def count_tokens_in_file(
    path: Path,
    encoding_name: str = DEFAULT_ENCODING,
) -> int:
    """Return the token count for the file's UTF-8 contents.

    Args:
        path: Path to the text file to count.
        encoding_name: tiktoken encoding name (default: cl100k_base).

    Returns:
        Number of tokens in the file.
    """
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(path.read_text(encoding="utf-8")))


def audit_directory(
    commands_dir: Path,
    encoding_name: str = DEFAULT_ENCODING,
) -> list[AuditEntry]:
    """Count tokens for every .md file in commands_dir, sorted descending.

    Args:
        commands_dir: Directory containing Markdown prompt files.
        encoding_name: tiktoken encoding name (default: cl100k_base).

    Returns:
        List of AuditEntry objects sorted by token count descending.
        Returns an empty list if no .md files are found.
    """
    paths = sorted(commands_dir.glob("*.md"))
    counts = [(p, count_tokens_in_file(p, encoding_name)) for p in paths]
    total = sum(c for _, c in counts) or 1  # avoid div-by-zero on empty dir
    entries = [
        AuditEntry(path=p, tokens=c, percent_of_total=c / total * 100)
        for p, c in counts
    ]
    entries.sort(key=lambda e: e.tokens, reverse=True)
    return entries


def format_report(
    entries: list[AuditEntry],
    heading: str = "Before",
    encoding_name: str = DEFAULT_ENCODING,
) -> str:
    """Return the full audit report Markdown.

    Produces a heading, measurement note, ranked table, total, and
    top-3 candidates for rewrite.

    Args:
        entries: Audit results from audit_directory().
        heading: Section heading label (default: "Before").
        encoding_name: Encoding name shown in the measurement note.

    Returns:
        Full Markdown report as a string.
    """
    today = date.today().isoformat()
    lines: list[str] = [
        f"# Mantle command token audit — {today}",
        "",
        f"Measured with tiktoken"
        f" (encoding: {encoding_name}, ~97% Claude BPE proxy).",
        "",
        f"## {heading}",
        "",
        "| Rank | Command | Tokens | % of total |",
        "| ---- | ------- | ------:| ----------:|",
    ]

    for rank, entry in enumerate(entries, start=1):
        name = entry.path.stem
        lines.append(
            f"| {rank} | {name} | {entry.tokens:,} |"
            f" {entry.percent_of_total:.1f}% |"
        )

    total_tokens = sum(e.tokens for e in entries)
    n = len(entries)
    lines.append("")
    lines.append(f"**Total:** {total_tokens:,} tokens across {n} command(s).")

    if entries:
        top3_names = ", ".join(f"{e.path.stem}.md" for e in entries[:3])
        lines.append("")
        lines.append(f"**Top 3 candidates for rewrite:** {top3_names}")

    lines.append("")
    return "\n".join(lines)


def append_after_section(
    report_path: Path,
    after_entries: list[AuditEntry],
) -> None:
    """Append 'After' and 'Delta summary' sections to an existing report.

    Parses the existing Before table to compute per-file before→after
    deltas.  Appends:

    - ``## After`` — ranked table with Before / After / Saved / % saved
      columns.
    - ``## Delta summary`` — bullets for top-3 and total savings.

    Args:
        report_path: Path to an existing Before-only report file.
        after_entries: Audit results from a post-rewrite audit_directory()
            call.

    Raises:
        ValueError: If report_path cannot be parsed to extract Before
            token counts.
    """
    before_tokens = _parse_before_tokens(report_path)

    lines: list[str] = [
        "",
        "## After",
        "",
        "| Rank | Command | Before | After | Saved | % saved |",
        "| ---- | ------- | ------:| -----:| -----:| -------:|",
    ]

    total_before = 0
    total_after = 0
    top3_saved = 0

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
        total_before += before
        total_after += after
        if rank <= 3:
            top3_saved += saved

    total_saved = total_before - total_after
    total_pct = (total_saved / total_before * 100) if total_before else 0.0
    top3_total = sum(
        before_tokens.get(e.path.stem, 0) for e in after_entries[:3]
    )
    top3_pct = (top3_saved / top3_total * 100) if top3_total else 0.0

    lines += [
        "",
        "## Delta summary",
        "",
        f"- Top-3 commands: {top3_saved:,} tokens saved"
        f" ({top3_pct:.1f}% reduction).",
        f"- Total: {total_saved:,} tokens saved ({total_pct:.1f}% reduction).",
        "",
    ]

    existing = report_path.read_text(encoding="utf-8")
    report_path.write_text(
        existing.rstrip("\n") + "\n" + "\n".join(lines),
        encoding="utf-8",
    )


# ── Private helpers ─────────────────────────────────────────────


def _parse_before_tokens(report_path: Path) -> dict[str, int]:
    """Extract command → token count from the Before table in a report.

    Args:
        report_path: Path to an existing Before report file.

    Returns:
        Mapping from command stem (without .md) to token count.

    Raises:
        ValueError: If no table rows can be parsed from the file.
    """
    import re

    text = report_path.read_text(encoding="utf-8")
    # Match rows like: | 1 | build | 1,234 | 12.3% |
    pattern = re.compile(
        r"^\|\s*\d+\s*\|\s*(\S+)\s*\|\s*([\d,]+)\s*\|", re.MULTILINE
    )
    results: dict[str, int] = {}
    for match in pattern.finditer(text):
        name = match.group(1)
        tokens = int(match.group(2).replace(",", ""))
        results[name] = tokens

    if not results:
        raise ValueError(
            f"Could not parse Before token table from {report_path}"
        )
    return results
