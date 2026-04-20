---
title: Machine-verifiable acceptance criteria with explicit pass/fail state
status: implementing
slice:
- core
- cli
- claude-code
- tests
story_count: 2
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- DuckLake
- Howard Marks Investment Philosophy
- John Templeton Investment Philosophy
- Lakehouse Architecture
- OpenRouter LLM Gateway
- Python 3.14
- Python package structure
- claude-sdk-structured-analysis-pipelines
- cyclopts
- import-linter
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
- python-314
tags:
- type/issue
- status/implementing
---

## Parent PRD

product-design.md, system-design.md

## Why

Mantle stores issue acceptance criteria as prose checkboxes in the markdown body. `mantle:verify` and `mantle:review` have to infer pass/fail state from the code and narrative, which is the exact "declare victory too early" failure mode documented in Anthropic's Claude Code harness work and OpenAI's Codex harness article. An agent reading a partially-complete issue can observe code-level progress and conclude the issue is done, skipping real end-to-end verification.

The harness-engineering literature (specifically Part 3 of "You are not using AI wrong...") highlights the feature list as a cognitive anchor: a structured file with explicit `passes: true|false` per criterion, which the agent can only flip after evidence-based verification. JSON/structured formats are also noted as harder for agents to tamper with than freeform markdown, which matters for a file we want agents to treat as inviolable.

## What to build

Shift ground truth for acceptance criteria into issue frontmatter as a structured list. Each entry gets `{id, text, passes}`. Markdown checkboxes in the body become a generated view of that list, kept in sync. `mantle:verify` flips `passes` from false to true only after evidence-based verification; `mantle:review` refuses to approve an issue while any AC is still `passes: false` (unless explicitly waived).

### Flow

1. `/mantle:plan-issues` and `/mantle:add-issue` write ACs into issue frontmatter as a list of `{id, text, passes: false}` entries; body markdown is rendered from the list.
2. `/mantle:verify` walks each AC, gathers evidence, and flips `passes` via a `mantle flip-ac` CLI (or equivalent) — never by raw edit. Emits a report of still-false ACs.
3. `/mantle:review` loads the structured list and gates approval on all ACs being `passes: true` (or `waived: true` with a reason).
4. A one-time `mantle migrate-acs` CLI backfills the backlog: parses existing markdown checkboxes, writes them into frontmatter with `passes: false`, regenerates the body view.

## Acceptance criteria

- [ ] Issue frontmatter supports an `acceptance_criteria` list where each entry has `id`, `text`, and `passes: true|false`; Pydantic schema validates it.
- [ ] Markdown AC checkboxes in the issue body are generated from the structured list on save, so the prose stays true to the data.
- [ ] `/mantle:verify` flips `passes` per AC via a dedicated CLI operation (not raw edit) and emits a report of ACs still at `passes: false`.
- [ ] `/mantle:review` refuses to approve an issue unless every AC is `passes: true` or carries an explicit waiver.
- [ ] A one-time `mantle migrate-acs` CLI backfills existing planned/implemented/verified issues from their markdown checkboxes into structured frontmatter.
- [ ] Unit tests cover the Pydantic schema, frontmatter round-trip, migration, body-sync rendering, and the flip-passes CLI behavior.
- [ ] `just check` passes.

## Blocked by

None

## User stories addressed

- As an agent running `mantle:verify`, I want an unambiguous pass/fail field per AC so I cannot conclude an issue is done by inference.
- As a reviewer, I want `mantle:review` to refuse approval until every AC has explicit evidence of passing.
- As a maintainer with a live backlog, I want a migration command so structured ACs apply to existing issues, not just new ones.