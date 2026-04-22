---
issue: 74
title: Apply cuts to top 3 commands, measure, and finalize report
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a Mantle user paying for tokens on every `/mantle:*` invocation, I want the
top-3 most expensive commands rewritten using Output Format templates and
imperative-fragment prose so that my recurring cost shrinks without losing
workflow guarantees.

## Depends On

Story 1 (produces the audit report with top-3 identified and the reusable
`scripts/audit_command_tokens.py`).

## Approach

Apply the two techniques from caveman scout findings 7 and 8 to the top-3
commands identified in Story 1. Preserve all Iron Laws, Red Flags tables,
numbered-step structure, and any prose that encodes behavioral spec — only
trim prose density. Re-run the Story 1 script to produce an "After" table;
append before/after delta to the report. Spot-check that `/mantle:build`
still reads end-to-end by reading the diff.

## Implementation

### claude/commands/mantle/&lt;top-1&gt;.md, &lt;top-2&gt;.md, &lt;top-3&gt;.md (modify)

Target commands: determined by Story 1's report. Apply both techniques:

**Technique 1 — Output Format template.** Where the command produces output
(verification table, review result, status block, etc.), add an explicit
"Output Format" section with a one-line-per-item template and a short
anti-pattern list (e.g., "no 'I noticed'", "no restating the question"). This
replaces paragraphs of prose guidance with an anchored template.

**Technique 2 — Imperative-fragment rewrite.** Inside numbered steps, tighten
prose:
- "Before starting, you must first read..." → "Read X."
- "If you find that the file does not exist, then you should..." → "If file missing, ..."
- Remove throat-clearing: "Note that...", "It is important to...", "Keep in mind..." — preserve the instruction without the framing.
- Collapse adjacent short sentences when X always pairs with Y.
- Target: 20-30% reduction per command.

**Hard constraints — do NOT remove or reword:**
- Iron Laws sections (exact wording)
- Red Flags tables (structure and rows)
- Numbered-step headings and step names
- Hard-warning thresholds, specific commands, and file paths (e.g., `mantle where`, `$MANTLE_DIR`, `.mantle/issues/issue-{NN}.md`)
- Concrete examples where they illustrate non-obvious patterns
- CLI surface snippets and the exact flags shown

### .mantle/audits/2026-04-22-token-audit.md (modify)

Re-run:

```
uv run python scripts/audit_command_tokens.py \
  --out .mantle/audits/2026-04-22-token-audit.md.new
```

Manually merge the new "Before" numbers into an "After" section of the
existing report:

```markdown
## After

| Rank | Command | Before | After | Saved | % saved |
|------|---------|--------|-------|-------|---------|
| 1    | &lt;top-1&gt;.md | NNNN  | MMMM  | KKK   | YY.Y%   |
| 2    | &lt;top-2&gt;.md | ...    | ...   | ...   | ...     |
| 3    | &lt;top-3&gt;.md | ...    | ...   | ...   | ...     |

## Delta summary

- Top-3 commands: **N tokens saved (X% reduction).**
- Total across all commands: **M tokens saved (Y% reduction).**
- Techniques applied: Output Format templates, imperative-fragment rewrite.
```

Delete the `.new` scratch file after merging.

#### Design decisions

- **Manual merge instead of combined report**: simpler than teaching the
  script a two-mode operation for a one-shot audit.
- **No real `/mantle:build` run for ac-04 check**: would cost real Claude
  tokens. Verify instead by reading each rewritten prompt end-to-end and
  confirming: step count unchanged, Iron Laws intact, every `mantle` CLI
  command preserved, every `$MANTLE_DIR`/`.mantle/` path preserved.
- **Scope cap**: if a command in the top-3 turns out to be mostly short
  capture scaffolding (e.g., `/mantle:bug`, `/mantle:idea`) with no prose
  to cut, skip it and move to the next candidate. Note the skip in the
  report.

## Tests

No pytest tests. Verification:
- Re-run audit script — confirm each rewritten command's token count dropped.
- Read each rewritten prompt end-to-end — confirm step structure, Iron Laws,
  and concrete CLI commands/paths preserved.
- `just check` — confirm lint/format pass (prompts are .md so mostly N/A, but
  catches any accidental src/ damage).