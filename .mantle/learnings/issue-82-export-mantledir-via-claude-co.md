---
issue: 82
title: Export MANTLE_DIR via Claude Code SessionStart hook instead of per-command
  'mantle where'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-21'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Shape doc was single-approach-clear.** B (settings.json static `env`) and C (hookSpecificOutput.additionalContext) were both rejected with one-line reasons — not shell-visible, not per-project. No wasted decision cycles; the chosen `CLAUDE_ENV_FILE` + `${MANTLE_DIR:-$(mantle where)}` fallback was the only viable shape from the start.
- **Story implementation matched the shape doc 1:1.** `printf '%q'` quoting, the `mantle where 2>/dev/null || true` swallow, the two new hook tests, the same-commit prompt-sweep widening — every decision in the shape doc landed verbatim in commit 8b6e739. Tight scope: 5 files, +67/-2, single commit.
- **77 → 81 → 82 retrospective chain confirmed.** Issue 81's retrospective explicitly named 82 as the next same-shape tier-1 fix and predicted it would run clean through `/mantle:build`. Third consecutive build with zero human-in-the-loop corrections — the retrospective-mines-follow-ups pipeline is now well-established at this appetite.
- **Story-level learning captured the prompt-sweep landmine immediately.** The `test_prompt_sweep.py::_assert_includes_resolve_prelude` literal-match across every /mantle:*.md is invisible from reading build.md — it surfaces only when you change a prelude. Saving the learning while the pain was fresh means the next prelude edit won't rediscover it.

## Harder than expected

- **Prompt-sweep coupling was unexpected.** Changing one prelude line in build.md triggered a failing test in `tests/prompts/test_prompt_sweep.py` that had to be widened in the same commit. Not a blocker (the fix is one-line), but it's a test that enforces conformity across all /mantle:* prompts without any visible cross-reference from the prompt itself. Story-level learning now documents it; worth keeping in mind when issuing the broader prelude sweep as a follow-up.
- **Build log artefact didn't capture the run.** `.mantle/builds/build-82-20260421-1513.md` reports "No story runs detected in this build" despite a clean end-to-end story run. This is the second build/observability oddity in two retros (81 flagged migrate-acs re-running on already-migrated issues). Worth investigating collectively as a tier-1 follow-up — the builds directory is a retrospective-grade artefact and should reflect reality.

## Wrong assumptions

- None that cost time. Shape doc's explicit non-goals ("does not migrate every /mantle:* prompt — AC-02 only requires build.md"; "does not introduce a claude-code-hooks vault skill") both held up. The follow-up prelude migration is now mechanically smaller than shape doc implied, because the prompt-sweep test already encodes both accepted forms.

## Recommendations

- **Continue piping tier-1 fixes through `/mantle:build`.** Three consecutive clean runs (80, 81, 82) at the "single seam + test + prompt edit" appetite. This is now the calibrated build rubric. Issue 83 (make-collect-issue-diff-stats source-aware) is the next candidate and fits the same shape.
- **File a follow-up for the broader prelude sweep.** Now that `test_prompt_sweep.py` accepts both forms and the hook is proven, extending `${MANTLE_DIR:-$(mantle where)}` to every other /mantle:*.md prompt is a mechanical multi-file edit. Good `/mantle:build` candidate.
- **File a follow-up for build-log observability.** `.mantle/builds/build-*.md` "No story runs detected" despite successful runs is a trust-eroding artefact. Combined with 81's migrate-acs spinning-wheel, there's a cluster of small .mantle/ backlog-hygiene issues worth batching.
- **Hold off on a `claude-code-hooks` vault skill.** Shape doc's call was right at this scale — one documented pattern, captured inline. If we add a second hook-driven export or ship an install-flow tweak, revisit.

## Notes on process

- Third back-to-back clean small-batch build. The `/mantle:build → /mantle:review → /mantle:retrospective` loop now handles tier-1 fixes as one muscle, with retrospectives reliably seeding the next issue. Confidence +1: the pipeline is dependable for small batches; still unproven at medium/large appetite. The prompt-sweep coupling and the empty build log are both "half-a-rabbit-hole" signals rather than real blockers, but they've accumulated to the point of warranting one .mantle/-hygiene follow-up pass.