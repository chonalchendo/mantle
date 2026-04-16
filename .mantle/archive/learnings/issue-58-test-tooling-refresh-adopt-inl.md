---
issue: 58
title: 'Test-tooling refresh: adopt inline_snapshot and dirty-equals, introduce named
  scenario fixtures'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-16'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- Small-batch pilot scoping held up end-to-end. The add-issue session had pre-scoped this as \"pilot, not sweep\" and that decision propagated cleanly through shape → plan → implement. Single story, single commit, seven ACs — no wasted motion.
- Just-in-time skill creation (inline-snapshot, dirty-equals) gave the implementer concrete patterns — named scenario fixtures, IsPartialDict kwargs form, snapshot-formatter caveat — that shaped the story well. Not generic library docs; skill files encode project-relevant anti-patterns.
- Iron Law #5 (skill evidence requirement) forced actual Read calls on core.md files, measurably improving shape quality.
- Orchestrator caught a silent regression — verified tests before trusting the simplify-agent's changes, which surfaced that it had reverted a validated commit.

## Harder than expected

- Pre-build working-tree cleanup. Session started with 7 dirty files from a prior session (import-module + PEP 758). Had to commit before starting. Friction that the build prompt currently surfaces only as a generic \"warn the user\".
- Simplify agent went out of scope. It reviewed files by git recency, not by issue diff. Reverted a PEP 758 `except X, Y:` → `except (X, Y):` (valid 3.14 syntax it didn't know about), and violated story spec's \"leave other tests untouched\" by importing _write_* helpers from conftest (pytest anti-pattern). Orchestrator caught both; reverted.
- CLAUDE_SESSION_ID silently unset → build-start/finish skipped per-story telemetry. Known gap from issue 54, surfaced here again. Fixed inline via SessionStart hook + file fallback (not part of issue 58).

## Wrong assumptions

- Assumed the refactorer respects issue-scoped simplification. It was told \"use issue-scoped mode with issue number 58\" but its own scope detection isn't tight enough — it reviews by git recency.
- Assumed agents know about Python 3.14 syntax. PEP 758 is recent; the python-314 skill exists in the vault and explicitly says \"Do not flag `except A, B:` as invalid\" — but it wasn't compiled for this issue because the auto-matcher didn't flag it.

## Recommendations

1. Scope simplifier to the issue's actual diff, not its recent git history. Pass the refactorer `git diff --name-only <feat-commit>^..<feat-commit>` and instruct it to touch only those files. Files modified by other commits are out of bounds by construction.
2. Auto-load `python-314` on 3.14+ projects. Cheap insurance against agents \"fixing\" valid syntax. Either extend `mantle update-skills` with a baseline-skills mechanism driven by pyproject.toml's `requires-python`, or have build.md add it post-update-skills.
3. Tighten pre-flight dirty-tree check in /mantle:build. Surface risk when dirty files overlap the issue's slice layers (e.g., tests/ changes when the issue's slice is tests).
4. Session-id fix already shipped — next /mantle:build will capture per-story telemetry via .mantle/.session-id.