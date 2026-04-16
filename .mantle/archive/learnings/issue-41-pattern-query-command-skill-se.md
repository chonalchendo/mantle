---
issue: 41
title: Pattern query command — skill-selection gap in build pipeline
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-12'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Build pipeline ran end-to-end without intervention.** Shape → plan → 2 stories → simplify → verify → approve-all. 3 feat/refactor commits + 2 follow-up fix commits, ~60 min wall-clock.
- **Deterministic design paid off immediately.** `mantle show-patterns` on the real vault produced a useful themed report on first try — no tuning. Confirms "compiled not queried" as the right principle for recurring-pattern surfacing.
- **Simplify caught real bloat.** -76 lines in one quality pass (two dead helpers + redundant `list.clear()` calls). Reinforces the v0.14 single-gate decision.
- **Post-build fixes landed fast and tight.** Empty-trend-table papercut was 15 lines + 3 tests in one commit, bundled with two prompt tweaks.

## Harder than expected

- **Shaping silently skipped skills entirely — the issue-52 fix didn't reach build mode.** `update-skills --issue 41` returned "no new skills" and `compile --issue 41` emitted only Jinja state templates, zero `SKILL.md` files. `build.md` Step 4's override said "read any compiled skills" — vacuous when compile produced nothing. The fallback to shape-issue.md's active selection (issue 52's fix) was never triggered because build-mode overrode that step. For issue 41, at least `cli-design-best-practices`, `cyclopts`, `python-project-conventions`, `pydantic-project-conventions`, `software-design-principles`, and `python-package-structure` were plausibly in scope. The shape was written from code-reading alone.
- **Confidence-trend table was empty on the live run** because `list_issues` excludes `archive/issues/`, and nearly every real issue is archived.
- **Story 1 spec contained an incorrect structural claim** (`IssueNote.number` doesn't exist). Implementer caught it via the "check `core/issues.py`" fallback hint.
- **Simplify refactorer agent had no bash access** — reasoned about test passage rather than running pytest. Orchestrator's own test run caught any risk.

## Wrong assumptions

- **Assumed issue 52's skill-selection fix was active across all shaping entry points.** It was only active in `/mantle:shape-issue` — `/mantle:build` Step 4 had a separate override that silently replaced active selection with a "read compiled skills" instruction.
- **Assumed `mantle compile --issue NN` always populates relevant skills.** For internal-tooling issues it produces nothing because the vault's 38 skills are all domain-specific (data / investment / scraping).
- **Assumed `list_issues` + `load_issue` would surface enough history for confidence trends.** Once archived, issues drop out.
- **Assumed the refactorer agent had bash access.** It didn't.

## Recommendations

### Addressed this session
- **commit 647e9fc** — `core.issues.list_archived_issues` added; `_issue_slice_map` merges live + archive; regex tolerates slug-less archive filenames; live wins on collisions. Confidence-trend table now populates on mature projects.
- **commit 647e9fc** — `plan-stories.md`: verify structural claims about sibling-module public APIs before asserting them in story specs.
- **commit 647e9fc** — `build.md` Step 7: orchestrator must re-run tests after refactorer returns; agent's "tests passed" claim is unverified until confirmed.
- **commit 4f422bc** — `build.md` Step 4: removed the "read any compiled skills" override; now follows `shape-issue.md` Step 2.3 "Load skills" as written (active selection of 2-4 skills from `list-skills`, read each). Restores issue 52's intended flow inside build mode.

### Still open
- **Consider a "mantle core conventions" vault skill** (frozen Pydantic models, section banners, core↔cli boundary, `project.resolve_mantle_dir`, test style with `tmp_path`) so internal-tooling issues have a concrete skill node to select. Right now these conventions are spread across CLAUDE.md + existing modules with no reusable trigger description.
- **Consider separating the two skill operations** in the CLI: `update-skills` detects missing skills to *create* vs a distinct step to *select existing skills to load for this issue*. Right now they're entangled in a way that makes silent no-ops easy.
- **Broaden pattern keyword buckets** once a few more runs surface terms currently landing in `"other"`.
- **`analyze_patterns` could also scan `brainstorms/`** eventually, but learnings + issues cover the ACs today.