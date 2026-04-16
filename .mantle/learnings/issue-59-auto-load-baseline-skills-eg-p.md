---
issue: 59
title: Auto-load baseline skills (e.g. python-314) based on project constraints
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-16'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- Two-story decomposition was session-sized: story 1 was a pure module + 14 unit tests, story 2 was the integration + CLI change + docs. Clean dependency line, no blockage between them.
- Shape-issue correctly preferred approach B (new `core/baseline.py`) over an inline helper in `skills.py`. The separation paid off — the pure version-mapping function was trivially unit-testable without any filesystem fixtures.
- The CLI stderr two-group report format ("Baseline skills (always loaded)" / "Issue-matched skills (from body scan)") landed in one shot without needing revisions; matched the issue body's suggested format exactly and satisfies the cli-design-best-practices stdout/stderr contract.
- Soft-failure pattern (`warnings.warn(..., stacklevel=2)` + return empty tuple) copied cleanly from the existing `skills.compile_skills` idiom — new module felt native to the codebase from day one.

## Harder Than Expected

- The refactorer/simplifier pass introduced a name-collision bug by consolidating imports into `from mantle.core import project, skills, state, vault`. Three test files had a pytest fixture literally named `project`, and the fixture's module-level name bound by `@pytest.fixture` shadowed the `project` module import — 123 tests errored with `AttributeError: 'FixtureFunctionDefinition' object has no attribute '_ConfigFrontmatter'`. Had to revert the entire simplify pass and ship pre-simplify state.
- The story-2 story-implementer agent's output got truncated mid-sentence before emitting a proper `STATUS:` code. The orchestrator had to independently verify tests and lint to decide whether to continue. Protocol gap but non-blocking.

## Wrong Assumptions

- Assumed `from __future__ import annotations` was discouraged on Python 3.14+ per the python-project-conventions skill ("No `from __future__ import annotations` on Python 3.12+"). The actual codebase uses it widely in test files to satisfy ruff TC003 (which wants stdlib-only imports like `pathlib.Path` moved into a `TYPE_CHECKING` block). The guide and the ruff config disagree. Matching the codebase beat matching the guide.
- Assumed the refactorer agent could be trusted to do mechanical import consolidation safely. In a project with pytest fixtures that happen to share module names (very common: `project`, `state`, `vault`), consolidating `from mantle.core.skills import X` into `from mantle.core import skills` is a name-collision trap.

## Recommendations

- **Codify module/fixture name-shadowing as a specific simplify-mode red flag.** Before consolidating imports, grep the target file for pytest fixture definitions and local variables matching the candidate module names. If there is a conflict, skip that consolidation — or require the fixture to be renamed explicitly. Add this to `claude/commands/mantle/simplify.md` as an anti-pattern example, grounded in this incident.
- **Keep the revert-on-test-failure behaviour.** It worked exactly as designed — orchestrator ran tests after the refactorer agent returned, caught 123 failures, reverted. That's the safety net doing its job.
- **Clarify the `from __future__ import annotations` rule in CLAUDE.md.** The python-project-conventions skill bans it on 3.12+, but the project uses it in test files for ruff TC003. Either update the skill to exempt TYPE_CHECKING-only tests, or drop the blanket ban. Otherwise future agents will churn this back and forth.
- **Baseline skills approach scales.** When a future issue needs another language/framework baseline (e.g. `pydantic-project-conventions` when Pydantic is detected in imports), extend `_python_baseline_for_version` sibling functions rather than introducing a registry. Single-file growth is cheaper than premature extensibility.