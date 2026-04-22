"""Audit-tokens command — measure token cost of prompt files."""

from __future__ import annotations

from datetime import date
from pathlib import Path


def run_audit_tokens(
    *,
    path: Path = Path("claude/commands/mantle"),
    out: Path | None = None,
    heading: str = "Before",
    encoding: str = "cl100k_base",
    append: bool = False,
) -> None:
    """Audit token cost of Markdown prompt files and write a ranked report.

    Default output: ``.mantle/audits/<YYYY-MM-DD>-token-audit.md``.
    ``--append`` appends an 'After' + 'Delta summary' section to an
    existing report (requires ``--out`` pointing at that report).

    Raises:
        SystemExit: If ``--append`` is given without ``--out``.
    """
    from mantle.core import token_audit

    entries = token_audit.audit_directory(path, encoding)

    if append:
        if out is None:
            print(
                "Error: --append requires --out pointing to an existing report."
            )
            raise SystemExit(1)
        token_audit.append_after_section(out, entries)
        print(f"After section appended to {out}")
        return

    report = token_audit.format_report(entries, heading, encoding)
    report_path = out or (
        Path(".mantle/audits") / f"{date.today().isoformat()}-token-audit.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"Report written to {report_path}")
