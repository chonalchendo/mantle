---
issue: 84
title: Model-tier config with measured defaults for the build pipeline
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-21'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Scope split from issue 75 held.** The umbrella in 75 was heading for 3-4 weeks against a 1-2 week appetite. Carving 84 down to the dominant lever (per-stage model tier) plus four explicitly deferred follow-ups (AI review+retro merge, prompt pruning, A/B harness, `.mantle/` restructure) shipped in one session. First-principles arithmetic in the shaped doc — 5x cost lever vs 6% prompt-token lever vs 0% restructure — was the right framing. Pattern worth naming and reusing.
- **Preset + overrides won on ergonomics.** The chosen config shape (one knob in `config.md`, preset definitions in `cost-policy.md`, per-stage overrides as escape hatch) let preset improvements propagate without every project re-copying seven lines. Flat per-stage would have violated pull-complexity-downward.
- **`core/project.py` over a new `core/config.py`.** Shaped doc explicitly rejected a shallow split ("would be a shallow split from `core/project.py` — the existing owner") and co-located `StageModels` + `load_model_tier` next to `read_config`. Kept the deep-module pattern and avoided introducing a new module boundary with only two functions in it.
- **Thin CLI wrapper mirrored existing patterns.** `mantle model-tier` in `cli/models.py` is a direct analogue of the other CLI wrappers — no surprises, no cross-layer imports, import-linter clean.

## Harder Than Expected

- **ac-04 couldn't actually complete inside the build.** The acceptance criterion required a before/after measurement from two `/mantle:build` runs. But `/mantle:build` cannot nest another `/mantle:build` inside its own session, so what shipped was a telemetry folder + method doc + pricing-table skeleton with every number literally `<fill>`. The verifier passed the criterion anyway because the file exists.
- **AC text never caught up to the shape decision.** `ac-02` explicitly named `core/config.py` and was never rewritten when shaping landed on `core/project.py` instead. The AC-in-issue-body is frozen at plan-issues time; the shape step updates the shaped doc, not the issue.
- **`FALLBACK_STAGE_MODELS` needed a post-hoc visibility promotion.** Commit `cefb78d` made the constant public and fixed test imports — the internal/public boundary was decided by test access patterns rather than up front. Small, but a sign the story plan didn't call the test surface out.

## Wrong Assumptions

- **Verifier would catch skeleton-vs-measured.** Assumed an AC that says "reports wall-clock seconds and dollar cost" would fail when the file reports `<fill>` in every row. It didn't — the verifier evaluated file presence plus method documentation, not numerical content. This is the single most leveraged finding from this issue.
- **Shape-time rewrites would propagate to AC text.** They don't. The shape step updates the shaped doc; the AC list in the issue body is frozen. Drift is structural unless shape is given explicit authority to rewrite the AC.
- **One build session could measure itself.** The self-referential nature of ac-04 wasn't surfaced at shaping — you need a fresh session after config.md is set up, because the current session runs under the pre-change state.

## Recommendations

- **Measurement ACs need a placeholder check in the verifier.** When an AC contains words like "measured", "reports", "records values for", the verifier should grep the target artifact for `<fill>`, `TBD`, `pending`, `<x>`, `<y>` sentinels and fail if present. This is the highest-leverage fix — it would have flagged ac-04 today.
- **Shape must rewrite divergent ACs.** When shaping reaches a conclusion that contradicts the issue-body AC text (e.g. `core/config.py` → `core/project.py`), the shape step should edit the issue file's AC list, not just the shaped doc. Otherwise reviewers see a mismatched paper trail.
- **Self-referential measurement ACs should split out.** Any AC that requires a fresh `/mantle:build` session to satisfy belongs in a separate follow-up issue, not the issue that implements the config it measures. "Build the lever" and "measure the lever" are two sessions; bundling them forces a skeleton-shaped compromise.
- **Scope-split pattern: verify deferred threads are filed before closing.** The 75 → 84 + four follow-ups split worked. Next time, the approval step should check that each "Deferred to follow-up issues" bullet has a corresponding issue file (or an explicit decision to not file one). Today this is trust-based and easy to drop silently.