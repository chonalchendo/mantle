---
issue: 89
title: A/B harness for build pipeline (post-hoc comparison)
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-25'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Split from 92 held cleanly.** Carving telemetry-prereq out at shape time (Approach B) meant 89 stayed a small-batch, read-only consumer of existing artefacts. Shape's first-principles arithmetic — "harness vs telemetry are two concerns; bundling violates one-issue-one-job" — held end-to-end. Same scope-split pattern that worked for 75 → 84.
- **Pure-core / thin-CLI structure resisted classitis.** `core/ab_build.py` shipped as frozen pydantic value objects (`ComparisonRow`, `Comparison`, `BuildArtefacts`, `QualityStats`, `CostBreakdown`) plus module-level functions (`compute_cost`, `collect_quality`, `build_comparison`, `render_markdown`) — no `Comparator` class. Matched the `core/telemetry.py` posture. `cli/ab_build.py` is a thin glue layer composing `cli/builds.py` patterns. Import-linter clean.
- **`inline_snapshot` for the renderer landed first-pass.** Story 2 captured two baselines for `render_markdown`; AC-03 sentinel-rejection became a trivial `not in` assert. The pairing of inline_snapshot (capture) + sentinel substring check (shape constraint) is the right pattern for any deterministic-renderer AC.
- **`/mantle:build` ran clean end-to-end.** 3 stories, 6/6 ACs PASS, zero DONE_WITH_CONCERNS. Same pipeline shape that worked for 80/84/90/91 worked here. Single automated session from plan-stories through verify; the only manual touch was a small post-build simplify pass (`refactor: simplify — public read_frontmatter_and_body, module-style imports`).

## Harder Than Expected

- **Issue 92's telemetry contract was structurally complete but data-incomplete.** Shape doc declared "92 delivered the telemetry contract this harness consumes." Three post-approval commits had to follow before the harness produced useful output on real data:
  - `feat(telemetry): persist cost_usd per stage-run in build reports` — cost wasn't being written to build files at all.
  - `feat(telemetry): parse story_id from sub-agent description` — every `story_id` in build-89's own report was `null`, including for sub-agent stages.
  - `feat(issue-89): resolve full Anthropic model ids to tier-keyed prices` — `StoryRun.model` carries full ids (`claude-opus-4-7`); the prices dict keys by tier (`opus`). Direct lookup failed.
- **The harness couldn't be dogfooded on its own build.** With `story_id=null` and no `cost_usd`, a comparison run against build-89 vs any other build would have rendered a near-empty report. The integration gap was invisible to the test suite (handcrafted fixtures all worked) and only surfaced when running the new command against real artefacts.
- **Wall-clock inflation cosmetic but real.** One `implement` run on opus shows 41,692s (~11.5h) — Mac slept overnight mid-build. Pre-existing pattern (memory note `project_build_wall_clock_inflates_on_sleep`); the harness will faithfully report this distortion in any A/B comparison until wall-clock is computed from active-time, not start/finish stamps.

## Wrong Assumptions

- **\"92 verified\" implied 89 could just consume.** Verification meant `just check` passed, not that the harness's actual consumption path produced a useful report on real data. This is the same class of finding as 84-retro (verifier passed `<fill>` skeleton) and 91-retro (\"telemetry fixed\" was only partially true). Shape inherited the assumption and never tested it.
- **Tier-keyed prices would match build data.** Story 1 chose `dict[str, Pricing]` with keys `opus`/`sonnet`/`haiku` because `cost-policy.md` presets use those names. No test exercised the actual `StoryRun.model` strings before the price-resolver gap surfaced post-build.
- **Fixture-passing tests proved the harness was usable.** All unit tests passed against handcrafted `BuildReport`s. The real value of an A/B harness is comparing two real builds; the missing test was a story-3 smoke test that ran the CLI against the latest two real `.mantle/builds/*.md` files and asserted the rendered report contained non-zero cost rows for at least one stage.

## Recommendations

- **Add a real-data smoke test for any consumer of cross-issue telemetry.** When issue N consumes telemetry/state produced by issue M, story acceptance should include one test that reads the most recent real artefact under `.mantle/builds/` (or equivalent) and asserts a non-trivial property of the rendered output (e.g. \"at least one cost row is non-zero\"). This is the harness-self-test pattern from 90 (`tests/parity/test_harness.py`) extended one layer down to data.
- **Promote \"prereq verified ≠ prereq usable\" from a 3rd recurrence to a shape-time check.** When a shape doc says \"issue X is verified, this consumes its output\", the shape step should require one concrete data sample showing the consumption shape (e.g. \"here is the StoryRun.model field from a real build — confirm the price-key strategy matches\"). Catching the tier-vs-fullid mismatch at shape time costs minutes; catching it post-approval cost three follow-up commits.
- **Defer cost lookups through a resolver, not direct dict access.** The fix that landed (`resolve_full_anthropic_model_ids_to_tier_keyed_prices`) is the right shape — a `resolve_price(model_id, prices) -> Pricing` function with explicit fallback rules. Future model additions only touch the resolver, not the prices dict.
- **Track the dogfood smoke test as a baseline-skill expectation.** Issues touching `.mantle/builds/`, `.mantle/stories/`, or other live state should be tagged with a baseline expectation: \"include a test that consumes one real artefact.\" Cheap to add at plan-stories time; would have caught all three post-hoc gaps.