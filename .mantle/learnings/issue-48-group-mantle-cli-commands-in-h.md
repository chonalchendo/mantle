---
issue: 48
title: Group mantle CLI commands in --help with Cyclopts help panels
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-12'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- Cyclopts 'Group(name, sort_key=N)' API was a one-line-per-decorator change — the chosen 'central GROUPS registry' approach held up exactly as shaped. No surprises, no rework.
- Single-story decomposition was correct. Splitting registry-creation from test would have created sequential waves with no independence benefit.
- story-implementer first-attempt DONE. The story spec included the exact file content for 'groups.py', the full taxonomy table, test structure, and gotcha checks (cyclopts version sniff, just check, smoke test) — the agent had no room to guess.
- Skill reading (cyclopts 'Group Validator Example' + '--help testing pattern') directly shaped both the implementation and the test structure. Iron Law #5 (read skills, not skim examples) paid off on a genuinely trivial issue.

## Harder than expected

- Not really. This was the frictionless case and is useful as a calibration data point: trivial issues should feel like this.

## Wrong assumptions

- Issue text said '~48 existing commands'; 'main.py' actually registers 50 (extras: show-patterns, build-start, build-finish, collect-issue-diff-stats). Low cost to reconcile inline during shaping, but on a larger refactor stale counts in acceptance criteria could mislead an agent into an incomplete pass.
- Assumed 'mantle update-skills --issue N' would produce a usable short-list. It picked 'Nick Sleep Investment Philosophy' for a CLI-grouping issue — zero signal. The matcher is currently too fuzzy to rely on; manual selection from 'mantle list-skills' is still the load-bearing step.

## Recommendations

- **Skill auto-matcher has a false-positive problem.** Recurring across issues (the resume hook also mislabelled this project 'mentat'). Worth an issue: tighten the matcher (exact skill-name token match on issue body? exclude investment-philosophy skills when the issue slice doesn't touch analysis modules?). Until then, treat 'update-skills' output as advisory and manually select.
- **Simplification skip threshold counts mechanical edits as logic.** Issue 48 ran simplification for 298 lines-changed — all mechanical 'group=GROUPS[...]' annotations. The refactorer found nothing (correctly). Consider: add a second skip dimension (e.g. 'unique logical statements changed' via tree-sitter / AST diff), or let shaping mark an issue as 'mechanical' to force-skip simplification.
- **Verify acceptance-criteria counts against live code at shape time.** Shaping could run a one-liner grep for '@app.command' and warn when the AC's declared count diverges from reality. Cheap; would have caught the 48-vs-50 drift before the story agent inherited it.
- **Build telemetry silently skipped when CLAUDE_SESSION_ID is unset.** Known gap from issue 54 work; surfaces again here. Already tracked.