---
issue: 74
title: Audit /mantle:* commands for token-cost conciseness
approaches:
- One-shot script + manual cuts
- Mantle audit-tokens CLI command
- Full eval harness (caveman-style)
chosen_approach: One-shot script + manual cuts
appetite: small batch
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

## Approaches Considered

### Approach A — One-shot script + manual cuts (small batch) — CHOSEN

Write a standalone script `scripts/audit_command_tokens.py` that uses
`anthropic.messages.count_tokens` to count tokens in each
`claude/commands/mantle/*.md`. Output a ranked Markdown report to
`.mantle/audits/2026-04-22-token-audit.md`. Identify top 3 by cost. Apply
Output Format templates + imperative-fragment rewrite (per scout findings
7 and 8 in `.mantle/scouts/2026-04-21-caveman.md`). Re-run the script to
measure before/after savings; append the delta table to the report.
Spot-check behavior by reading rewritten commands end-to-end; run
`just check`.

**Tradeoffs:** cheapest path to all ACs; script is disposable. No
repeatable CLI surface — future audits must re-run the script manually.
**Rabbit holes:** rewriting may drift into Iron Laws / Red Flags prose
that encodes behavioral spec, not noise. Mitigation: "Does not" excludes
Iron Laws.
**No-gos:** no new `mantle` subcommand; no eval harness; no output-token
measurement.

### Approach B — `mantle audit-tokens` CLI command (medium batch)

Same counting logic, but exposed as `mantle audit-tokens` under
`src/mantle/cli/` with a pure helper in `core/`. Repeatable; tested.
Rejected: YAGNI for a one-shot audit. If recurring audits become
needed, file a new issue.

### Approach C — Full eval harness (large batch)

Build `evals/llm_run.py` + `evals/measure.py` per caveman's two-stage
pattern. Measures *output* token savings (the bigger cost axis) via real
`claude -p` baseline/control/rewritten runs. Rejected: out of appetite;
issue body explicitly flags this as optional.

## Rationale for Approach A

Smallest-appetite approach that satisfies every acceptance criterion:
ac-01 (ranked table from script), ac-02 (top-3 rewrites with scout-named
techniques), ac-03 (before/after delta from re-run), ac-04 (spot-check
unchanged behavior), ac-05 (`just check`). Any heavier approach risks
widening scope beyond the investigation's mandate.

## Code Design

### Strategy

- `scripts/audit_command_tokens.py` — standalone script (not under
  `src/mantle/`; this is tooling, not shipped CLI surface). Uses
  `anthropic.Anthropic().messages.count_tokens(model=..., messages=[...])`.
  Reads `claude/commands/mantle/*.md`, writes a ranked Markdown report.
  Report structure:

      # Mantle command token audit (2026-04-22)
      | Rank | Command | Tokens | % of total |
      | Top 3 cuts: {names}
      | Before → After (applied): delta column

- Top-3 rewrites: in-place edits to `claude/commands/mantle/<name>.md`
  applying two techniques from the caveman scout:
    1. Output Format templates (one-line-per-item template + short
       anti-pattern list)
    2. Imperative-fragment rewrite of numbered steps — preserve step
       structure, tighten prose inside each step. Target 20-30%
       per-command reduction.
- Report lives at `.mantle/audits/2026-04-22-token-audit.md`.
- Model for `count_tokens`: `claude-opus-4-7` (matches the default
  orchestrator model; BPE is stable across 4.x variants so the rank
  order is invariant to exact model choice).

### Fits architecture by

- Script under `scripts/` — does not pollute `src/mantle/` with
  one-shot tooling; honours the meta-template carve-out in
  `shape-issue.md` Step 2.3.
- Report lives under `.mantle/audits/` — extends the existing
  naming convention (`.mantle/scouts/`, `.mantle/learnings/`).
- Prompt edits preserve each command's numbered-step structure and
  Iron Laws — only trim prose inside steps.
- `core/` never-imports-from-`cli/` invariant is trivially honoured
  (no `src/` changes).
- Uses Anthropic Python SDK directly; `anthropic` is already a dep of
  the project (per global `claude-api` skill guidance). If not, add
  to a `check` group and document in the script header.

### Does not

- Does NOT add a `mantle audit-tokens` CLI command (YAGNI; approach
  B deferred).
- Does NOT run real `claude -p` output-token eval (approach C
  deferred; issue body flags as optional).
- Does NOT rewrite every command — only top 3 by cost.
- Does NOT change command *behavior* — only prose density.
- Does NOT touch Iron Laws, Red Flags tables, or "Red Flags — thoughts
  that mean STOP" sections in any command (behavioral spec, not noise).
- Does NOT modify CLAUDE.md or `.mantle/` memory files (issues 79
  and 87 cover those).
- Does NOT edit commands where the prose is already the spec
  (e.g., short "Open questions" scaffolds in capture commands like
  `/mantle:bug`, `/mantle:idea` if they land in the top 3 — prefer
  leaving them as-is and moving to the next candidate).

## Open Questions

None — issue body is detailed enough; the scout file encodes both
techniques concretely.