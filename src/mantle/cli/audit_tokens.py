"""Audit-tokens command — measure token cost of prompt files."""

from __future__ import annotations

from datetime import date
from pathlib import Path


def run_audit_tokens(
    *,
    path: list[Path] | None = None,
    out: Path | None = None,
    heading: str = "Before",
    encoding: str = "cl100k_base",
    append: bool = False,
) -> None:
    """Audit token cost of Markdown prompt files and write a ranked report.

    Accepts one or more paths via the repeatable ``--path`` flag. If no
    path is given, defaults to ``claude/commands/mantle`` (back-compat).

    Default output: ``.mantle/audits/<YYYY-MM-DD>-token-audit.md``.
    ``--append`` appends an 'After' + 'Delta summary' section to an
    existing report (requires ``--out`` pointing at that report).

    Args:
        path: List of directories to audit. Defaults to
            ``[Path("claude/commands/mantle")]`` when None or empty.
        out: Output file path. Auto-generated when None.
        heading: Section heading for the Before report (default: "Before").
        encoding: tiktoken encoding name (default: cl100k_base).
        append: If True, append After+Delta sections to an existing report.

    Raises:
        SystemExit: If ``--append`` is given without ``--out``.
    """
    from mantle.core import token_audit

    resolved_paths: list[Path] = path or [Path("claude/commands/mantle")]
    per_surface = token_audit.audit_paths(resolved_paths, encoding)

    if append:
        if out is None:
            print(
                "Error: --append requires --out pointing to an existing report."
            )
            raise SystemExit(1)
        token_audit.append_after_section(out, per_surface)
        print(f"After section appended to {out}")
        return

    report = token_audit.format_report(per_surface, heading, encoding)
    report_path = out or (
        Path(".mantle/audits") / f"{date.today().isoformat()}-token-audit.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"Report written to {report_path}")
