---
issue: 74
title: Build audit script and produce initial ranked report
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a Mantle user paying for tokens on every `/mantle:*` invocation, I want a
measurement of each command's token cost so that cut decisions are grounded in
data, not guesses.

## Depends On

None — independent.

## Approach

Standalone one-shot script under `scripts/` (not `src/mantle/`; this is
investigation tooling, not shipped CLI surface). Uses
`anthropic.Anthropic().messages.count_tokens(...)` for real Claude-BPE counts
on each prompt file. Writes a ranked Markdown report to `.mantle/audits/`.
Throwaway — if audits recur, file a new issue for a `mantle audit-tokens` CLI
command (deferred per the shaped issue's Approach B).

## Implementation

### scripts/audit_command_tokens.py (new file)

Header comment: "One-shot audit tool for issue 74. Re-run after rewrites to
measure savings."

Required functions:

```python
def count_file_tokens(client: Anthropic, model: str, path: Path) -> int:
    """Count tokens in a .md file using messages.count_tokens."""
    content = path.read_text(encoding="utf-8")
    response = client.messages.count_tokens(
        model=model,
        messages=[{"role": "user", "content": content}],
    )
    return response.input_tokens

def audit(commands_dir: Path, model: str, client: Anthropic) -> list[tuple[Path, int]]:
    """Count tokens for every .md in commands_dir. Return sorted descending."""

def format_report(results: list[tuple[Path, int]], heading: str) -> str:
    """Return ranked Markdown table with Rank | Command | Tokens | % of total."""

def main() -> None:
    # argparse: --commands-dir, --out, --model
    # Reads commands, counts tokens, writes report.
```

CLI surface:

```
uv run python scripts/audit_command_tokens.py \
  --commands-dir claude/commands/mantle \
  --out .mantle/audits/2026-04-22-token-audit.md \
  --model claude-opus-4-7
```

Report format:

```markdown
# Mantle command token audit — 2026-04-22

Measured with `anthropic.messages.count_tokens` (model: claude-opus-4-7).

## Before

| Rank | Command | Tokens | % of total |
|------|---------|--------|------------|
| 1    | build.md | NNNN  | XX.X%      |
...

**Total:** N tokens across M commands.

**Top 3 candidates for rewrite:** <name>.md, <name>.md, <name>.md
```

Dependency note: `anthropic` may not yet be a dep. Verify via `uv tree | grep
anthropic`. If missing, add via `uv add anthropic` (runtime, not a check-group
dep — the script uses it). Env requires `ANTHROPIC_API_KEY`.

### .mantle/audits/2026-04-22-token-audit.md (new file)

Generated output of the script's first run. Contains only the "Before" section
plus the "Top 3 candidates" line. Story 2 will append "After" and "Delta".

#### Design decisions

- **Script under `scripts/`, not `src/mantle/`**: one-shot investigation; no
  repeatable CLI surface needed.
- **`claude-opus-4-7` as default model**: matches orchestrator default. BPE is
  stable across 4.x so rank order is invariant to exact model choice.
- **Report in `.mantle/audits/`**: parallels `.mantle/scouts/`, `.mantle/learnings/`.
- **No pytest tests**: script is throwaway; verification is running it and
  reading output. `just check` passes because the script is a plain .py that
  doesn't break imports.

## Tests

No pytest tests — script lives outside `src/mantle/`. Verification:
- Run `uv run python scripts/audit_command_tokens.py` — confirm report file created at `.mantle/audits/2026-04-22-token-audit.md`.
- Read report — confirm ranked table, % column sums to ~100%, top 3 identified.
- `just check` — confirm nothing else broke.