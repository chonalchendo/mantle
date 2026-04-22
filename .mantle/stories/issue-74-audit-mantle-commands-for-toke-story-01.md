---
issue: 74
title: Build mantle audit-tokens CLI command + initial ranked report
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a Mantle user paying for tokens on every `/mantle:*` invocation, I want a
measurement of each command's token cost via a proper `mantle audit-tokens`
subcommand so that cut decisions are grounded in data AND the measurement
tool is discoverable, tested, and reusable from other mantle commands.

## Depends On

None — independent.

## Approach

Proper mantle subcommand following the core/cli split. Pure logic in
`src/mantle/core/token_audit.py`, cyclopts wrapper in
`src/mantle/cli/audit_tokens.py`, tests in `tests/core/test_token_audit.py`.
Uses `tiktoken.get_encoding("cl100k_base")` — local, no network, no auth;
community-cited ~97% accuracy against Claude BPE (rank/delta effectively
exact). Supersedes the `scripts/audit_command_tokens.py` prototype from the
first shaping attempt; delete that file.

## Implementation

### pyproject.toml (modify)

Add `tiktoken>=0.8` to `[project]` `dependencies`. Tiktoken ships prebuilt
wheels for py3.14 (single C extension, ~5MB). After edit, run
`uv lock && uv sync --group check`.

### src/mantle/core/token_audit.py (new file)

Pure logic, no cyclopts or CLI deps.

```python
"""Token-cost audit of Markdown prompt files using tiktoken."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import tiktoken

DEFAULT_ENCODING = "cl100k_base"

@dataclass(frozen=True)
class AuditEntry:
    """One file's token-count result in an audit."""
    path: Path
    tokens: int
    percent_of_total: float

def count_tokens_in_file(
    path: Path, encoding_name: str = DEFAULT_ENCODING,
) -> int:
    """Return the token count for the file's UTF-8 contents."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(path.read_text(encoding="utf-8")))

def audit_directory(
    commands_dir: Path,
    encoding_name: str = DEFAULT_ENCODING,
) -> list[AuditEntry]:
    """Count tokens for every .md file in commands_dir, sorted desc."""
    paths = sorted(commands_dir.glob("*.md"))
    counts = [(p, count_tokens_in_file(p, encoding_name)) for p in paths]
    total = sum(c for _, c in counts) or 1  # avoid div-by-zero on empty
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
    """Return the full audit report Markdown (heading + table + total + top-3)."""
    # Header: '# Mantle command token audit — <today iso>'
    # Note: 'Measured with tiktoken (encoding: <name>, ~97% Claude BPE proxy).'
    # '## <heading>'
    # '| Rank | Command | Tokens | % of total |' with rows per entry
    # '**Total:** <sum> tokens across <n> commands.'
    # '**Top 3 candidates for rewrite:** <name>.md, <name>.md, <name>.md'

def append_after_section(
    report_path: Path,
    after_entries: list[AuditEntry],
) -> None:
    """Append 'After', 'Delta summary' to an existing Before-only report.

    Parses the existing Before table to compute per-file before→after
    deltas. Appends:
      ## After
      | Rank | Command | Before | After | Saved | % saved |
      ## Delta summary
      - Top-3 commands: N tokens saved (X% reduction).
      - Total: M tokens saved (Y% reduction).
    """
```

**Design decisions:**

- **Dataclass over dict**: gives type checker signal and makes the report-
  formatting function easier to test.
- **`cl100k_base` as default**: community proxy for Claude; swap is one
  argument away if a better encoding appears.
- **Parse Before table to compute delta in `append_after_section`**: keeps
  the "After" invocation stateless from the caller's perspective
  (caller only supplies the current audit; function figures out the
  delta by reading the file). Simpler call site in Story 2.

### src/mantle/cli/audit_tokens.py (new file)

Follow whatever cyclopts pattern other `src/mantle/cli/*.py` files use
(implementer: grep an existing module to confirm — likely a top-level
function decorated by a shared `app` instance, or registered in
`cli/__init__.py`). Command shape:

```python
def audit_tokens(
    *,
    path: Path = Path("claude/commands/mantle"),
    out: Path | None = None,
    heading: str = "Before",
    encoding: str = "cl100k_base",
    append: bool = False,
) -> None:
    """Audit token cost of Markdown prompt files and write a ranked report.

    Default output: `.mantle/audits/<YYYY-MM-DD>-token-audit.md`.
    `--append` appends an 'After' + 'Delta summary' section to an
    existing report (requires `--out` pointing at that report).
    """
    entries = token_audit.audit_directory(path, encoding)
    if append:
        if out is None:
            raise ValueError("--append requires --out pointing to existing report")
        token_audit.append_after_section(out, entries)
        return
    report = token_audit.format_report(entries, heading, encoding)
    report_path = out or (
        Path(".mantle/audits") / f"{date.today().isoformat()}-token-audit.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"Report written to {report_path}")
```

### tests/core/test_token_audit.py (new file)

Covers the core module only (CLI tests live elsewhere if the project has
them; follow existing convention — if there are no CLI tests for other
commands, don't add one here either). Fixture: `tmp_path / "cmds"` with
three small .md files of known content.

- **count_tokens_in_file_encodes_content**: a file with 'hello world'
  returns `len(tiktoken.get_encoding('cl100k_base').encode('hello world'))`.
- **audit_directory_sorts_descending**: three files of different sizes
  come back in descending token order.
- **audit_directory_percents_sum_to_100**: use `dirty_equals.IsFloat(approx=...)`
  or a tolerance assertion (sum of percents ~= 100.0 ±0.01).
- **audit_directory_empty_dir**: empty dir returns `[]` (no div-by-zero).
- **format_report_snapshot**: render a report from a fixed 3-file fixture,
  assert against `inline_snapshot()` — will auto-fill on first run with
  `uv run pytest --inline-snapshot=create`.
- **append_after_section_appends_and_computes_delta**: write a Before-only
  report, call `append_after_section` with reduced counts, assert the
  After+Delta sections match `inline_snapshot()`.

### scripts/audit_command_tokens.py (delete)

`git rm scripts/audit_command_tokens.py`. Superseded by the CLI command.

### .mantle/audits/2026-04-22-token-audit.md (generate)

After implementation, run:

```
uv run mantle audit-tokens \
  --path claude/commands/mantle \
  --out .mantle/audits/2026-04-22-token-audit.md
```

Confirm the ranked table, totals, and top-3 identification. Story 2 will
consume this file.

## Tests

Already enumerated in the Implementation section under
`tests/core/test_token_audit.py`. Additionally, to close the loop:

- Run `uv run pytest tests/core/test_token_audit.py` — all new tests pass.
- Run `just check` — lint, type, import-linter, and full test suite pass.
- Run `uv run mantle audit-tokens --help` — confirm the command registered
  in cyclopts.
- Run the command end-to-end against `claude/commands/mantle/` — confirm
  the report file is created and the top-3 identified.