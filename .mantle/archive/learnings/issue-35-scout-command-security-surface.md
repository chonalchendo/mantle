---
issue: 35
title: Scout command — security surface, integration checklist, pattern reuse
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-07'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Build pipeline maturity**: Full automated shape → plan → implement → verify flow ran cleanly with no blocked stories. Pipeline is reliable for pattern-following features.
- **Pattern reuse as template**: Using brainstorm.py as a direct template for scout.py produced clean, consistent code with minimal review issues. The thin-module CRUD pattern (Pydantic model + save/load/list) is a proven, repeatable unit.
- **Verification caught real gaps**: The query.md integration gap and the post-build read-only security constraint were both caught before review — exactly what the multi-step pipeline is for.

## Harder Than Expected

- **Security surface not anticipated**: The read-only constraint on cloned repos (never execute untrusted code) was caught only after implementation, not during shaping or acceptance criteria. Commands that interact with external/untrusted resources need explicit security constraints planned upfront.

## Wrong Assumptions

- **Underestimated security surface**: Assumed cloning + agent analysis was a benign workflow. In reality, handing untrusted repo files to agents creates a code execution risk that needed explicit Iron Law protection.

## Recommendations

1. **Security review for external-resource commands**: Any command that clones, fetches, or processes untrusted content should have an explicit security constraint in its acceptance criteria during issue planning — not as an afterthought.
2. **Cross-cutting integration checklist**: When adding new artifact directories (e.g. `.mantle/scouts/`), check query.md and any other commands that enumerate `.mantle/` content. New directories don't auto-register.
3. **Pattern reuse is a strength**: The brainstorm.py template approach works. For future thin-module features, explicitly reference the template module in the story spec — it accelerates implementation and reduces review issues.