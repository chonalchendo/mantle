---
title: Automated build pipeline — /mantle:build command
status: completed
slice:
- claude-code
- core
story_count: 0
verification: null
blocked_by: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

Mantle's 13-step workflow requires human invocation at every stage. Research on AI workflow orchestration (2026-03-29) and critical thinking analysis confirm that the industry has converged on a three-checkpoint pattern: human input at specification, plan review, and output review — with full automation between. The middle steps (research → plan-issues → shape-issue → plan-stories → implement → verify) are confirmatory, not generative — they add friction without proportional value for most projects.

## What to build

A `/mantle:build` orchestrator command that automates the planning-through-verification pipeline:

1. Reads the current project state and design docs
2. Auto-plans issues from the product/system design (or uses existing issues)
3. Auto-shapes each issue (picks approach based on appetite/risk)
4. Auto-decomposes into stories
5. Implements via story-implementer agents
6. Runs verification
7. Pauses at review for human approval

Individual commands (`/mantle:shape-issue`, `/mantle:plan-stories`, etc.) remain available for fine-grained control.

The command should surface intermediate state so users can inspect progress, but not require confirmation at each step. Think CI/CD pipeline with approval gates, not step-by-step wizard.

Key design decisions informed by research:
- Checkpoints at phase boundaries only (Devin, Copilot Workspace pattern)
- Quality upstream inputs principle — require solid design docs before automation
- Compound failure mitigation — break the chain at plan review, not every step
- Persistent state in `.mantle/` for resumability

## Acceptance criteria

- [ ] `/mantle:build` command exists as a Claude Code slash command
- [ ] Automatically plans issues from design docs if no issues exist
- [ ] Automatically shapes and decomposes existing issues into stories
- [ ] Implements stories via story-implementer agents
- [ ] Runs verification after implementation
- [ ] Pauses at review checkpoint for human approval
- [ ] Surfaces progress at each automated stage (not silent)
- [ ] Individual workflow commands still work independently
- [ ] Handles errors gracefully — stops and reports rather than continuing with bad state

## Blocked by

None — all prerequisite infrastructure exists (shape-issue, plan-stories, implement, verify commands)

## User stories addressed

- As a developer, I want to go from design to reviewed code in a single command so I spend time on decisions, not process