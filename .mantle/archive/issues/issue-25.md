---
title: Automated build pipeline — /mantle:build command
status: completed
slice:
- claude-code
- core
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria:
- id: ac-01
  text: '`/mantle:build` command exists as a Claude Code slash command'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Automatically plans issues from design docs if no issues exist
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Automatically shapes and decomposes existing issues into stories
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Implements stories via story-implementer agents
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Runs verification after implementation
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Pauses at review checkpoint for human approval
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: Surfaces progress at each automated stage (not silent)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: Individual workflow commands still work independently
  passes: false
  waived: false
  waiver_reason: null
- id: ac-09
  text: Handles errors gracefully — stops and reports rather than continuing with
    bad state
  passes: false
  waived: false
  waiver_reason: null
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

- [ ] ac-01: `/mantle:build` command exists as a Claude Code slash command
- [ ] ac-02: Automatically plans issues from design docs if no issues exist
- [ ] ac-03: Automatically shapes and decomposes existing issues into stories
- [ ] ac-04: Implements stories via story-implementer agents
- [ ] ac-05: Runs verification after implementation
- [ ] ac-06: Pauses at review checkpoint for human approval
- [ ] ac-07: Surfaces progress at each automated stage (not silent)
- [ ] ac-08: Individual workflow commands still work independently
- [ ] ac-09: Handles errors gracefully — stops and reports rather than continuing with bad state

## Blocked by

None — all prerequisite infrastructure exists (shape-issue, plan-stories, implement, verify commands)

## User stories addressed

- As a developer, I want to go from design to reviewed code in a single command so I spend time on decisions, not process