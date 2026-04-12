---
date: '2026-04-12'
author: 110059232+chonalchendo@users.noreply.github.com
title: jira-integration-via-hook-seam
verdict: proceed
tags:
- type/brainstorm
---

## Brainstorm Summary

**Idea**: Jira integration — let teammates see what the user is working on via a team Jira board, without double-entering work.
**Problem**: (A) visibility — teammates don't know what's in progress between standups; (B) compliance — manager requires work to be tracked in Jira, causing double-entry today.
**Vision alignment**: Moderate-to-Strong (conditional on staying a one-way export, not PM-workflow).

## Exploration

- **Problem**: A + B. One-way push (mantle → Jira) is enough. No need to read Jira comments back.
- **Granularity**: One Jira ticket per mantle *issue* (coarse — "I'm working on X"). Stories stay internal; team doesn't need slice-level detail.
- **Trigger**: Initially imagined a `/mantle:sync-jira` command, but hook-driven auto-update using the Jira CLI (`acli`) is the preferred mechanism.
- **User context**: User uses the global `.mantle/` pattern (not per-project git-committed), so config and secrets both live locally/privately for them.

## Vision Alignment Analysis

**For**: product-design.md explicitly names a future `/mantle:sync-notion` one-way export for team visibility. Jira-as-export fits that precedent. User memory confirms this is live pain (multi-repo work + Jira board), not speculative.

**Against**: Out of Scope explicitly lists "No PM features" and "No multi-backend support — Obsidian-native by design". Jira-as-PM-workflow (bidirectional sync, comments, assignments) would violate both. A thin one-way adapter does not.

**Overlap**: Issue 42 (report-to-GitHub) is structurally identical — push mantle state to an external tracker. Strong case that they should share a mechanism.

## Challenges Explored

**Devil's advocate — why mantle at all?**: User could write a 30-line bash script in their dotfiles triggered by SessionEnd hook. User's answer ("cool integration, best tools have useful integrations a user can extend") was hand-wavy — but reframed productively: the real argument was for an *extension seam*, not Jira-specific product code. This reframe became the key insight of the session.

**Seam vs. Jira-specific**: The two shapes were laid out plainly (table of tradeoffs). User converged on the seam: mantle exposes lifecycle events, user writes scripts. Mantle never imports a Jira library, never stores a Jira token, never knows Jira exists.

**Auth pre-mortem**: Addressed. Mantle owns no auth — `acli` uses OS keychain; raw curl uses env vars. Mantle's only responsibility is documenting setup in the example script's header comments. Same model as pre-commit framework.

**Config pre-mortem**: Project-scoped config (Jira project key, base URL) needs somewhere to live. Solution: generic `hooks.env:` passthrough in `.mantle/config.yml` — mantle reads keys, exports as env vars, never interprets them. Keeps seam principle intact. Works identically for global or per-project `.mantle/`.

## Approaches Considered

| Approach | Description | Key Trade-off | Appetite |
|---|---|---|---|
| **B1 — Pure hook dispatch** | `.mantle/hooks/on-<event>.sh` convention only. User writes any script. | Simplest; cold-start friction. | Small |
| **B2 — Hook + examples repo** (chosen) | B1 + worked examples (`jira.sh`, `linear.sh`, `slack.sh`) users copy and edit. Plus generic `hooks.env:` config passthrough. | Same code surface, solves cold start. Carries Jira as docs, not core code. | Small |
| **B3 — Hook + typed integration config** | Named `integrations.jira:` config block mantle parses per-tool. | Slippery slope back to Jira-awareness in core. Rejected. | Small-medium |

## Verdict

**Verdict**: proceed
**Reasoning**: The seam reframe turns a vision-tense idea (Jira-specific integration) into a vision-aligned idea (generic extension seam). B2 ships the immediate Jira win, costs mantle ~50 lines of core code, and unlocks Linear/Slack/GitHub for free — issue 42 (report-to-GitHub) should be re-evaluated as a hook example rather than a bespoke command.

**If proceeding**: create an issue for the hook seam. Scope:
- Hook directory convention (`<mantle-dir>/hooks/on-<event>.sh`) resolved via `mantle where` so it works for both global and per-project `.mantle/`.
- Lifecycle events to emit: issue-shaped, issue-implement-start, issue-verify-done, issue-review-approved (plus story-status-changed if cheap).
- Positional args passed to hook: issue id, new status, issue title.
- `hooks.env:` passthrough from config.yml → env vars.
- Examples directory shipped in the package: `jira.sh`, `linear.sh`, `slack.sh`, each with a setup header (install CLI, authenticate, set env).
- README section on hook authoring.

**Open questions for shape-issue**:
- Should hooks run sync (blocking) or async (fire-and-forget)? Blocking = can surface failures; async = don't slow the workflow.
- Fail-open or fail-closed on hook error? Probably fail-open with a warning — a broken Jira hook shouldn't block mantle work.
- Does issue 42 survive as its own issue, or collapse into "provide a github.sh example"? Revisit when this issue is shaped.