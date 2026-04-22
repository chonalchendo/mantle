---
issue: 74
title: Audit /mantle:* commands for token-cost conciseness
approaches:
- One-shot script + manual cuts
- mantle audit-tokens CLI command + manual cuts (CHOSEN after pivot)
- Full eval harness (caveman-style)
chosen_approach: mantle audit-tokens CLI command + manual cuts
appetite: medium batch
open_questions:
- None
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-22'
updated: '2026-04-22'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approach history

**Original shape** picked Approach A (one-shot script) on small-batch appetite.
During implementation, two issues surfaced that invalidated the original
choice:

1. **Tokenizer friction** — `anthropic.messages.count_tokens` requires a
   funded Anthropic account, not just an API key. Claude Code's OAuth auth
   doesn't grant API access. Switching to a local tokenizer was necessary.
2. **Architectural miss** — a standalone script under `scripts/` bypasses
   project conventions (cyclopts CLI, tests, core/cli split,
   discoverability via `mantle --help`). For a capability that will almost
   certainly be re-invoked (every prompt edit is a candidate for a delta
   measurement), proper CLI surface pays back the ~50 extra lines of code.

Revised to Approach B with a tiktoken tokenizer. Appetite bumped to medium
batch.

## Approaches Considered (revised)

### Approach A — One-shot script + manual cuts (small batch) — REJECTED

Standalone script under `scripts/` calling `anthropic.messages.count_tokens`.
Rejected post-implementation-start: requires funded Anthropic account;
bypasses project CLI conventions; tool is not discoverable.

### Approach B — `mantle audit-tokens` CLI command + manual cuts (medium batch) — CHOSEN

Proper Mantle subcommand following the core/cli split. Uses
`tiktoken.get_encoding("cl100k_base")` locally — no network, no auth, no
account needed. Community-cited ~97% accuracy against real Claude BPE; for
rank + delta purposes this is effectively exact (a 3% drift on every entry
cannot reorder the top N when the top files are 2-3× bigger than the next).

**Tradeoffs:** more code (~220 lines total vs. ~170 script), but includes
tests, is discoverable, reusable (callable from other mantle commands
later, e.g. a pre-release audit check), and honours the core-never-
imports-cli invariant.

### Approach C — Full eval harness (large batch) — REJECTED

Out of appetite. Would measure *output* token savings via real `claude -p`
runs. Issue body flags as optional follow-up.

## Code Design

### Strategy

Three new files, plus one deletion:

**`src/mantle/core/token_audit.py` (new)** — pure logic, no CLI deps.

```python
@dataclass(frozen=True)
class AuditEntry:
    path: Path
    tokens: int
    percent_of_total: float

def count_tokens_in_file(path: Path, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in a text file using a tiktoken encoding."""

def audit_directory(
    commands_dir: Path,
    encoding_name: str = "cl100k_base",
) -> list[AuditEntry]:
    """Count tokens for every .md in commands_dir. Return sorted desc."""

def format_report(
    entries: list[AuditEntry],
    heading: str = "Before",
    encoding_name: str = "cl100k_base",
) -> str:
    """Render a Markdown ranked table (same format as original script)."""

def append_after_section(
    before_path: Path,
    after_entries: list[AuditEntry],
) -> None:
    """Append 'After' table + 'Delta summary' to an existing report."""
```

**`src/mantle/cli/audit_tokens.py` (new)** — cyclopts wrapper.

Follows the existing CLI command pattern (same shape as other
`src/mantle/cli/*.py` modules). Signature:

```python
def audit_tokens(
    path: Path = Path("claude/commands/mantle"),
    out: Path | None = None,
    heading: str = "Before",
    encoding: str = "cl100k_base",
    append: bool = False,
) -> None:
    """Audit token cost of prompt files and write a ranked report.

    Default writes to `.mantle/audits/<YYYY-MM-DD>-token-audit.md`.
    `--append` appends an 'After' section to an existing report
    (expects `--out` to point at the existing file).
    """
```

Register in whichever cyclopts `App` currently aggregates mantle
subcommands (match existing registration pattern — likely
`src/mantle/cli/__init__.py` or `cli/main.py`; implementer to verify).

**`tests/core/test_token_audit.py` (new)** — covers:
- ranking descending by token count
- percent-of-total sums to 100% (dirty-equals with tolerance)
- report format via `inline_snapshot` against a fixture directory
- `append_after_section` produces exactly the expected delta markdown
- `count_tokens_in_file` on a known-content file returns a stable count

**`scripts/audit_command_tokens.py` (delete)** — superseded.

**`pyproject.toml` (modify)** — add `tiktoken>=0.8` to runtime
dependencies. Tiktoken ships prebuilt wheels for py3.14; single C
extension, ~5MB.

### Fits architecture by

- Honours the `core/` never-imports-`cli/` invariant (core has no cyclopts
  dep; cli imports from core).
- Uses the same cyclopts registration + type-hint-driven arg parsing as
  every other `mantle` subcommand.
- Report location `.mantle/audits/` extends the existing convention
  (`.mantle/scouts/`, `.mantle/learnings/`).
- Tests live in `tests/core/test_token_audit.py`, mirroring the
  `src/mantle/core/token_audit.py` path per CLAUDE.md convention.
- Uses `inline_snapshot` and `dirty-equals` per project test conventions.

### Does not

- Does NOT call the Anthropic API (no network, no auth, no account).
- Does NOT attempt BPE-exact accuracy — tiktoken cl100k_base is
  ~97% accurate against real Claude tokens, accepted as the pragmatic
  proxy. Absolute numbers are approximate; ranks and deltas are
  effectively exact.
- Does NOT run real `claude -p` output measurement (approach C deferred).
- Does NOT auto-rewrite any command file — rewrites are Story 2's manual
  pass with human judgement.
- Does NOT touch Iron Laws, Red Flags tables, or numbered-step structure
  in the rewrites (Story 2 constraint, repeated here for visibility).
- Does NOT modify CLAUDE.md, `.mantle/` memory files, or commands outside
  `claude/commands/mantle/*.md` (issues 79 and 87 cover other areas).

## Story layout

1. **Story 1 (rewritten)** — build `mantle audit-tokens` (core + cli +
   tests + dep + delete old script); generate "Before" report.
2. **Story 2 (updated invocation)** — apply cuts to top 3 commands;
   `mantle audit-tokens --append --out <report>` produces "After" and
   "Delta summary"; finalize report.

## Issue-body amendment (to be applied alongside story 1)

The issue body's "Measurement method" section currently pins
`anthropic.messages.count_tokens`. Amend to:

> - **ac-01, ac-03 (prompt-file token counts)**: use
>   `tiktoken.get_encoding("cl100k_base")` via the `mantle audit-tokens`
>   subcommand. Originally pinned to `anthropic.messages.count_tokens`;
>   switched after discovering Anthropic requires funded-account access
>   for even free endpoints. Tiktoken cl100k_base is the community-
>   standard proxy, ~97% accurate against Claude BPE, with rank and
>   delta effectively exact for an English-prose corpus.

## Open Questions

None.