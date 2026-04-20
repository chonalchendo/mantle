---
issue: 80
title: flip-ac --pass flag errors; verify.md drives users into the broken path
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-20'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **77→80 handoff validated the retrospective→issue pipeline.** Issue 77's "harder than expected" section named the exact cyclopts quirk (`--pass/--fail` negation syntax doesn't work as the skill implies) and named the fix (`negative=` kwarg is first-class). Shaping had clear evidence for picking A over B without any new research. This is working as intended — learnings produced an issue, and the issue closed the loop.
- **`/mantle:build` end-to-end was a clean fit for a small-batch fix.** Single automated pass — shape → plan-stories → implementer (sonnet) → simplifier (refactorer) → verifier — no agent handoff friction, no design judgement required, 4/4 ACs passed on first verify. Rubric-correct: single file, clear spec, no ambiguity.
- **Approach A over B was the right call.** Fixing the CLI binding (consistent help text = documented flag) beats the marginal saving of a docs-only patch. `cli-design-best-practices` skill's "help output should match accepted flags" invariant was the deciding factor. Rejected B because `--help` would still display `--pass` as a flag the user could try.
- **sonnet for implementation matched the rubric.** Single file + clear spec + no design judgement = exactly the single-file-implementer profile. Refactorer then folded the two-line import back to module form per the CLAUDE.md convention; that simplification pass is paying for itself.

## Harder than expected

- **Cyclopts vault skill still encodes the broken `name="--pass/--fail"` form.** The example that produced issue 77's bug is still in the skill. The next author wiring a boolean pair will hit the same trap. This is the single highest-leverage follow-up — fix the example and it stops recurring.
- **CLI-parse coverage gap.** Existing flip-ac tests called `run_flip_ac(...)` directly, bypassing cyclopts entirely. That's why the binding bug slipped past unit tests and was only caught at verify-time during issue 77. Story 1 closed the gap with an in-process `main_module.app("flip-ac ... --pass")` test — worth generalising: any new CLI flag needs at least one test that exercises cyclopts parsing, not just the underlying function.

## Wrong assumptions

- **Assumed `name="--pass/--fail"` was a cyclopts idiom for bool-pair negation.** Cyclopts parses it as two literal aliases `--pass` and `--fail`, and then `--fail` happens to work (literal alias flipping the default) while `--pass` is never bound. The first-class API is `name="--pass", negative="--fail"`. Issue 77's learning had already flagged this — the fix was straightforward once named.

## Recommendations

- **Fix the cyclopts vault skill example.** Replace `Parameter(name="--flag/--no-flag")` with `Parameter(name="--flag", negative="--no-flag")`. One edit prevents the same class of bug reappearing. Candidate follow-up issue or inline `/mantle:add-skill` revision.
- **Add a CLI-parse test when wiring any new flag.** `app("cmd --flag ...")` catches binding bugs that direct-function tests miss. This deserves a convention note — maybe in CLAUDE.md under "Test Conventions" — or at minimum a mention in shaping prose when new flags land.
- **Keep mining retrospectives for follow-up issues.** 77's retrospective produced 80, 81, 82 verbatim. That's the intended flow — do more of it. `/mantle:patterns` across learnings could automate the mining pass.
- **Bundle tier-1 fixes through `/mantle:build`.** Issues 81/82/83 are same-shape small batches (CLI/prompt alignment, tightening verification). Pipe them through `/mantle:build` directly rather than manually shaping each — the rubric fits.

## Notes on process

- The fact that issue 80 was so uneventful is itself signal — the machinery (shaping, build, verify, review, retrospective) handled a genuine bug from detection → fix → archive without a single human-in-the-loop correction. Small confidence +1: the pipeline works for small batches; still unproven at larger appetite.