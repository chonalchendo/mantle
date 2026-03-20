---
issue: 24
title: Simplify command (/mantle:simplify)
approaches:
- 'Approach A — Post-Implement Simplification Pass: A /mantle:simplify command that
  sits between /mantle:implement and /mantle:verify. Collects the diff of all story
  commits for an issue, spawns a simplification agent that reviews changed code against
  CLAUDE.md standards and known LLM bloat patterns (unnecessary abstractions, defensive
  over-engineering, duplication, dead code, comment noise). Changes committed separately
  from implementation. Tests run before and after to ensure behavioral equivalence.
  Issue-scoped only.'
- 'Approach B — Simplify as Review Lens: Simplification integrated into /mantle:verify
  as a dedicated phase. No new command — simplification findings reported in the verification
  report as advisory only. Lighter implementation but mixes concerns (functional correctness
  vs code quality) and findings may get ignored.'
- 'Approach C — Standalone Simplify with Per-File Agents: Dedicated /mantle:simplify
  runnable at any point. Spawns per-file simplification agents (like /mantle:implement
  spawns per-story agents). Each file gets focused context: file contents, CLAUDE.md
  standards, LLM bloat checklist. Flexible scope (issue, files, or git status). Misses
  cross-file duplication but produces better per-file results.'
chosen_approach: Hybrid A+C — Issue-scoped pass with standalone flexibility
appetite: medium batch
open_questions:
- Should simplify auto-run after /mantle:implement or require explicit invocation?
- Should the bloat pattern checklist be user-configurable in config.md?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-03-20'
updated: '2026-03-20'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Shaping: Simplify Command (/mantle:simplify)

### Problem

AI-generated code has well-documented characteristic bloat patterns: unnecessary abstractions, defensive over-engineering (excessive try-catch, redundant validation), code duplication (8x increase per GitClear data), unnecessary conditionals, comment noise, and "slop scaffolding" (boilerplate wrapping trivial logic). These patterns accumulate faster than humans catch them in review. A dedicated simplification pass is needed as a quality gate.

### Research Findings

- A 2025 taxonomy paper documents 5 categories, 19 subcategories of LLM code inefficiencies. Most common: General Logic (68.5%), Maintainability (21.14%).
- Industry consensus (CodeScene, SonarQube) places simplification post-implementation, pre-merge as a dedicated pass — not bundled into code review.
- Safe to auto-fix: unnecessary else blocks, unused imports, redundant conditionals, duplicate comments, dead variables. Requires human judgment: removing "unused" functions, interface changes, business logic restructuring, error handling changes.
- Key risk is mis-simplification: code that's shorter but harder to follow. Tests are a prerequisite, not a consequence.
- An existing code-simplifier agent exists in the Claude plugins marketplace but is not Mantle-aware, not language-specific, and not integrated into the story workflow.

### Chosen Approach: Hybrid A+C

Issue-scoped simplification pass with standalone flexibility. Combines the workflow integration of Approach A with the per-file agent focus of Approach C.

**Default mode (issue-scoped)**:
1. User runs `/mantle:simplify 15` (or auto-detects current issue)
2. Command collects git diff for that issue's story commits
3. Identifies changed files from the diff
4. Spawns per-file simplification agents, each with: file contents, CLAUDE.md/project standards, known LLM bloat pattern checklist
5. Tests run after all files processed — failures trigger per-file revert to isolate culprits
6. Surviving changes committed as `refactor(issue-N): simplify implementation`

**Standalone mode**:
- `/mantle:simplify` with no arguments operates on changed files (git status)
- Can also accept explicit file paths
- Works outside the Mantle issue workflow for any project

**Language-agnostic**: No hardcoded language rules. All simplification driven by CLAUDE.md standards and the universal LLM bloat pattern checklist.

**The LLM bloat pattern checklist** (what agents look for):
1. Unnecessary abstractions — helper functions/classes for one-time operations
2. Defensive over-engineering — excessive try-catch, redundant validation of internal data
3. Code duplication — repeated logic within a file
4. Unnecessary conditionals — redundant else blocks, conditions that can't fail
5. Dead code — unused imports, variables, unreachable branches
6. Comment noise — comments restating what code already says
7. Slop scaffolding — boilerplate wrapping trivial logic
8. Over-parameterisation — configuration for things that never vary

**Test safety**: Tests must pass before and after simplification. No changes committed if tests fail.

**Scope boundary**: Per-file simplification only. No cross-file refactoring (that's architectural). No public interface changes. No business logic restructuring.

### Tradeoffs

- **Gain**: Dedicated quality gate for AI bloat. Works within Mantle workflow and standalone. Per-file agents get focused context. Separately committed and revertable. Language-agnostic.
- **Give up**: Cross-file duplication not addressed (biggest LLM pattern by volume). Extra workflow step. Per-file agents can't see the whole picture.

### Rabbit Holes

- Determining which commits belong to an issue (relies on conventional commit messages with issue references)
- Per-file agents missing cross-file patterns — accepted limitation, documented as no-go
- Test suite might not exist for new projects — simplify should warn but not block
- The agent could produce mis-simplifications (shorter but worse) — test gate is the safety net

### No-Gos

- No language-specific rules hardcoded
- No cross-file refactoring or architectural changes
- No public interface modifications
- No changes without test verification (warn if no tests, proceed with caution flag)
- No removal of functions without clear evidence they're unused within the file