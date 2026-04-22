---
issue: 88
title: 'Audit, trim, and re-measure: vault-wide Output Format sweep + top-3 cuts'
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a maintainer, I want AI outputs to follow a consistent terse pattern across every `/mantle:*` command and the vault's top-3 heaviest skills trimmed so that recurring token cost shrinks without losing capability, with the savings measured and reported.

## Depends On

Story 1 — requires the multi-path audit CLI and per-surface `--append` delta.

## Approach

Three-phase pass: (1) produce the Before audit over commands + skills to establish the baseline report artifact; (2) apply the proven Output Format template to every `/mantle:*` command that emits output and concrete top-3 cuts (commands + skills) using the imperative-fragment rewrite technique from issue 74; (3) re-run the audit with `--append` to produce the After table and Delta summary, then smoke-test `/mantle:build` on a trivial throwaway issue to confirm no behavioural regression.

## Implementation

### Phase 1 — Capture Before state

Run:

```bash
uv run mantle audit-tokens \
  --path claude/commands/mantle \
  --path /Users/conal/test-vault/skills \
  --out .mantle/audits/2026-04-22-vault-audit.md
```

The resulting report is the Before snapshot for ac-04.

Record the top-3 per surface from the ranked tables. Expected candidates based on file size: commands likely `build.md`, `shape-issue.md`, `implement.md` (issue 74 confirmed these); skills likely the largest vault nodes (empirical — read from report).

### Phase 2 — Apply prose edits

#### 2a — Output Format sections on every output-emitting `/mantle:*` command

For each file in `claude/commands/mantle/*.md`, read and decide: does this command instruct Claude to emit a user-facing report, summary, or structured output? If yes, add (or normalise) an `## Output Format` section near the end containing:

- A one-line-per-item template showing the shape of the output (headers, tables, bullets).
- A 3-5 line anti-pattern list — what NOT to include.

Use the Output Format section structure already present in issue-74-era edits as the canonical template — preserve its voice and structure. Do not invent new formatting conventions.

Commands that are pure state-mutation with no user-facing output (e.g., `bug.md`, `idea.md` if they only persist a record) are exempt. Err toward inclusion when in doubt — adding the section costs ~5 lines and clarifies intent.

**Preservation constraints** (Iron Law equivalents for prose edits):

- Preserve Iron Laws, Red Flags tables, numbered-step structure verbatim.
- Preserve CLI invocations (`mantle <cmd>`, shell snippets) byte-for-byte.
- Preserve `$MANTLE_DIR` / `.mantle/` path references.
- Never collapse a numbered step into a bullet — step ordering is semantic.

#### 2b — Top-3 command cuts

On the top-3 commands from Phase 1's report, apply imperative-fragment rewrites targeting ~20% reduction per file (the ratio hit in issue 74). Prioritise:

- Prose → imperative fragments where the instruction is a single action.
- Redundant framing ("Be sure to...", "Make sure that...", "It is important that...") → imperatives.
- Over-specified examples — collapse or remove if the pattern is clear.
- Repeated explanations across sub-steps — consolidate.

Do not touch behavioural logic, flag definitions, or CLI snippets.

#### 2c — Top-3 skill cuts

On the top-3 skill source files (in `/Users/conal/test-vault/skills/*.md`), apply the same imperative-fragment technique. Skills have a frontmatter + body structure — trim the body only. Preserve frontmatter `description`, `when_to_use`, `when_not_to_use`, `triggers` sections if present. Aim for ~20% per file.

After skill edits, re-run `mantle compile --issue 88` so the compiled `.claude/skills/` reflects the trimmed source (smoke-test only; no verification required yet).

### Phase 3 — Measure + smoke-test

Re-run the audit with `--append` over the same paths:

```bash
uv run mantle audit-tokens \
  --path claude/commands/mantle \
  --path /Users/conal/test-vault/skills \
  --out .mantle/audits/2026-04-22-vault-audit.md \
  --append \
  --heading After
```

This appends per-surface After tables and a Delta summary to the same report. Verify the Delta summary shows non-zero savings on both surfaces.

Smoke-test `/mantle:build` by invoking it manually against a trivial throwaway issue (or pick an already-planned small issue and run shape-through-verify). The pipeline must complete without prompt-parsing regressions introduced by the rewrites. Record the build-report path.

## Tests

Prose edits are verified by the measurement artifact (Delta summary) and the build smoke-test rather than by unit tests — there are no new functions or classes to test in this story. The acceptance criteria explicitly verify via `mantle audit-tokens --append` (ac-04) and `/mantle:build` E2E (ac-05).

### tests/test_workflows.py (verify, no change expected)

Run the full test suite after prose edits are done. No prose edit should break a test — if one does, the test was over-fitted to prose wording and must be updated to assert on behaviour instead.

Run `just check` — must pass (ac-06).

## Verification against issue ACs

- ac-01: per-surface ranked report exists in `.mantle/audits/2026-04-22-vault-audit.md`.
- ac-02: top-3 commands + top-3 skills edited (concrete diffs visible in git log for this story's commits).
- ac-03: Output Format section present on every `/mantle:*` command that emits output.
- ac-04: Delta summary in same report via `--append`.
- ac-05: `/mantle:build` smoke-test passes on a throwaway issue.
- ac-06: `just check` passes.