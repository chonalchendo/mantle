---
title: Mechanical enforcement of core/ → cli/ import-direction invariant
status: approved
slice:
- tests
- cli
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- DuckDB Best Practices and Optimisations
- DuckLake
- FRED Data Source
- Howard Marks Investment Philosophy
- John Templeton Investment Philosophy
- Mohnish Pabrai Investment Philosophy
- Nick Sleep Investment Philosophy
- OpenRouter LLM Gateway
- Production Project Readiness
- Python 3.14
- Python Project Conventions
- Python package structure
- SQLMesh Best Practices
- Software Design Principles
- Tom Gayner Investment Philosophy
- beautifulsoup4-web-scraping
- claude-sdk-structured-analysis-pipelines
- cyclopts
- dirty-equals
- edgartools
- fastapi
- import-linter
- inline-snapshot
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
- python-314
- streamlit
- streamlit-aggrid
tags:
- type/issue
- status/approved
---

## Parent PRD

product-design.md, system-design.md

## Why

CLAUDE.md and system-design.md both state the core rule: `core/` never imports from `cli/` or `api/`. This is mantle's single load-bearing architectural invariant — everything about the library/delivery split depends on it. Today it's enforced by convention and human review.

As more of mantle is agent-written via `/mantle:build`, convention enforcement will drift. Agents pattern-match local code and replicate whatever they see. One accidental `from mantle.cli` import inside `core/` is all it takes to start normalizing violations. Part 4 of "You are not using AI wrong..." (OpenAI Codex harness) makes the case explicitly: when throughput exceeds human review capacity, invariants must be enforced mechanically, with error messages shaped for agent consumption.

The highest-leverage place to invest mechanical enforcement in this codebase is exactly this rule.

## What to build

A mechanical check that fails any time code under `src/mantle/core/` imports from `mantle.cli` or `mantle.api`. Wired into `just check` so every `mantle:build` gate catches violations before commit. The failure message is structured for agent remediation: the offending file, the forbidden import, the rule being violated, and the fix steps — all in one actionable message the next agent run can consume from tool output.

Shaping should pick between `import-linter` (data-driven contracts, extensible later), a small pytest that uses `ast` to walk `src/mantle/core/`, or a ruff custom rule. Data-driven contracts are preferable because more invariants will likely follow.

### Flow

1. A linter config (likely `importlinter` contracts in `pyproject.toml` or `.importlinter`) declares `mantle.core` forbidden from importing `mantle.cli` or `mantle.api`.
2. `just check` runs the linter alongside ruff/pyright/pytest.
3. On violation, the error message names the file, the import, the rule, and one-line remediation guidance (e.g. "move the helper into core or invert the dependency").
4. A test fixture deliberately introduces a violating import in a scratch module and asserts the linter catches it — the check is itself tested.
5. CONTRIBUTING.md (or a new docs section) names the rule and points to the linter config so humans and agents can discover how to extend it.

## Acceptance criteria

- [ ] `just check` runs a mechanical import-direction check over `src/mantle/core/` and fails on any import from `mantle.cli` or `mantle.api`.
- [ ] The failure message names the offending file, the forbidden import, and includes remediation steps formatted for injection into agent context.
- [ ] A test deliberately introduces a violating import into a sandbox/fixture module and asserts the check catches it (the guard itself is tested).
- [ ] The rule is data-driven (e.g. `import-linter` contracts) so additional architectural invariants can be added later without new infrastructure.
- [ ] CONTRIBUTING.md (or equivalent) documents the rule, points to the check config, and explains how agents/humans extend it.
- [ ] `just check` passes in a clean tree.

## Blocked by

None

## User stories addressed

- As a maintainer, I want the core/→cli/api boundary mechanically enforced so architectural drift is impossible rather than merely discouraged.
- As an agent running `/mantle:build`, I want a linter failure to tell me exactly which file and import are wrong and how to fix them, so I can self-correct in one retry rather than asking a human.
- As a future contributor adding a second invariant (e.g. no-skills-imports-core), I want the rule config to be extensible rather than a bespoke script.