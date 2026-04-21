---
title: /mantle:compress — input-token compression for .mantle/ memory files and CLAUDE.md
status: planned
slice:
- core
- cli
- claude-code
- tests
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

The caveman scout (`.mantle/scouts/2026-04-21-caveman.md`, finding 10) surfaced input-compression as a lever Mantle currently lacks: every `/mantle:*` invocation re-reads `CLAUDE.md`, `.mantle/state.md`, `product-design.md`, `system-design.md`, and relevant skills. Caveman's compressor cuts ~46% input tokens on prose memory files while preserving structural invariants (headings, code blocks, URLs byte-identical; bullets within ±15%). This stacks multiplicatively with issue 84's model tiering — cutting *what* the model reads on top of *which* model reads it.

Dominantly this is about recurring cost: a one-time compression pass pays back on every subsequent session. Validation matters (silent semantic loss in design docs is worse than the token cost), which is why caveman's `.original.md` backup + structural validator is the right reference pattern rather than a naïve LLM rewrite.

## What to build

1. A `mantle compress <target>` CLI (optionally surfaced as `/mantle:compress`) that compresses a single named memory file in place.
2. A file-type classifier (lifted from caveman-compress's `detect.py` pattern) that classifies file content as prose / code / config so only prose is compressed — YAML frontmatter, code fences, and tool-call syntax stay byte-identical.
3. A structural validator (lifted from caveman-compress's `validate.py` pattern) that asserts invariants are preserved across compression: headings exact, code blocks byte-identical, URLs/file-paths present, bullet counts within ±15%. Validator fails loudly; no silent acceptance.
4. A `.original.md` sibling saved next to every compressed file so the operation is reversible.
5. Before/after token counts recorded in `.mantle/telemetry/` per run, reusing the format introduced by issue 84.

Default targets under consideration: project `CLAUDE.md`, `.mantle/state.md`, `.mantle/product-design.md`, `.mantle/system-design.md`. Compression is opt-in per file, not a batch sweep — these are load-bearing docs and each compression should be reviewed.

## Acceptance criteria

- [ ] ac-01: `mantle compress <target>` exists and compresses a single target file in place, saving the original as `<target>.original.md`.
- [ ] ac-02: A file-type classifier skips code/config blocks so only prose is compressed.
- [ ] ac-03: A post-compression validator asserts structural invariants (headings exact, code blocks/URLs/file-paths byte-identical, bullets within ±15%) and fails loudly if any are violated.
- [ ] ac-04: The tool is exercised on at least one real memory file (e.g. `CLAUDE.md`) with before/after token counts recorded in `.mantle/telemetry/`; applying compression to the rest of the memory surface is left to maintainer discretion post-ship.
- [ ] ac-05: Tests cover the validator (invariant preservation + intentional-failure cases) and the classifier (prose vs code vs config fixtures).
- [ ] ac-06: `just check` passes.

## Blocked by

None. `.mantle/telemetry/` is introduced by issue 84; if 84 hasn't landed when this issue ships, this issue creates the folder.

## User stories addressed

- As a Mantle user paying per input token, I want `.mantle/` memory files compressed once so every subsequent session pays less for the same context.
- As a maintainer worried about silent semantic loss, I want a validator asserting code/URLs/headings survive compression so memory files stay trustworthy.
- As a Mantle user, I want a `.original.md` backup beside every compressed file so I can roll back if the compressed version drops nuance I wanted to keep.

## Source inbox items

- `.mantle/scouts/2026-04-21-caveman.md` (finding 10 — input compression of LLM-facing memory files; findings 3, 4 — structural validator + file-type classifier patterns)