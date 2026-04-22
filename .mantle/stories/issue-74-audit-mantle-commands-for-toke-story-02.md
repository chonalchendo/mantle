---
issue: 74
title: Apply cuts to top 3 commands, measure via --append, finalize report
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a Mantle user paying for tokens on every `/mantle:*` invocation, I want the
top-3 most expensive commands rewritten using Output Format templates and
imperative-fragment prose so that my recurring cost shrinks without losing
workflow guarantees.

## Depends On

Story 1 (produces the `mantle audit-tokens` command and the "Before" report
identifying the top 3).

## Approach

Apply the two techniques from caveman scout findings 7 and 8 to the top-3
commands identified in Story 1. Preserve all Iron Laws, Red Flags tables,
numbered-step structure, and any prose that encodes behavioral spec — only
trim prose density. Then invoke `mantle audit-tokens --append` against the
Story 1 report to generate the "After" table and "Delta summary" sections.
Spot-check that `/mantle:build` still reads end-to-end by reading the diff.

## Implementation

### claude/commands/mantle/&lt;top-1&gt;.md, &lt;top-2&gt;.md, &lt;top-3&gt;.md (modify)

Target commands: determined by Story 1's report (the top-3 names written in
`.mantle/audits/2026-04-22-token-audit.md` under "Top 3 candidates for
rewrite"). Apply both techniques:

**Technique 1 — Output Format template.** Where the command produces output
(verification table, review result, status block, etc.), add an explicit
"Output Format" section with a one-line-per-item template and a short
anti-pattern list (e.g., "no 'I noticed'", "no restating the question").
This replaces paragraphs of prose guidance with an anchored template.

**Technique 2 — Imperative-fragment rewrite.** Inside numbered steps,
tighten prose:
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

### .mantle/audits/2026-04-22-token-audit.md (modify via CLI)

Run:

```
uv run mantle audit-tokens \
  --append \
  --path claude/commands/mantle \
  --out .mantle/audits/2026-04-22-token-audit.md
```

The `--append` mode (implemented in Story 1) reads the existing "Before"
table, measures current token counts, and appends:

```markdown
## After

| Rank | Command | Before | After | Saved | % saved |
|------|---------|--------|-------|-------|---------|
| 1    | &lt;top-1&gt;.md | ... | ... | ... | ... |
| 2    | &lt;top-2&gt;.md | ... | ... | ... | ... |
| 3    | &lt;top-3&gt;.md | ... | ... | ... | ... |

## Delta summary

- Top-3 commands: **N tokens saved (X% reduction).**
- Total across all commands: **M tokens saved (Y% reduction).**
- Techniques applied: Output Format templates, imperative-fragment rewrite.
- Tokenizer: tiktoken cl100k_base (~97% Claude BPE proxy; rank/delta
  effectively exact).
```

Manually append the "Techniques applied" and "Tokenizer" lines after the
CLI-generated delta summary (the CLI writes just the tables and numerical
summary; commentary is human-added).

#### Design decisions

- **No real `/mantle:build` run for ac-04 check**: would cost real Claude
  tokens. Verify instead by reading each rewritten prompt end-to-end and
  confirming: step count unchanged, Iron Laws intact, every `mantle` CLI
  command preserved, every `$MANTLE_DIR`/`.mantle/` path preserved.
- **Scope cap**: if a command in the top-3 turns out to be mostly short
  capture scaffolding (e.g., `/mantle:bug`, `/mantle:idea`) with no prose
  to cut, skip it and move to the next candidate. Note the skip in the
  report.

## Tests

No new pytest tests for this story — the rewrites are content edits, not
code. Existing Story 1 tests already cover `mantle audit-tokens`
behaviour. Verification for this story:

- Run `mantle audit-tokens --append` — confirm the After/Delta sections
  appear in the report and each rewritten command's token count dropped.
- Read each rewritten prompt end-to-end — confirm step structure, Iron
  Laws, and concrete CLI commands/paths preserved.
- Run `just check` — lint/format/tests pass.