---
issue: 74
title: Audit /mantle:* commands for token-cost conciseness
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-22'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Issue-body amendment actually happened.** When the tokenizer pivoted (anthropic → tiktoken), the Measurement method section in the issue body was rewritten inline, not just in the shaped doc. Directly inverts issue 84's AC-drift pattern. Worth naming: when shape contradicts a frozen AC, rewrite the issue body, not just the shaped doc.
- **Two mid-build pivots, still shipped in one appetite window.** Tokenizer swap + script→CLI both landed without derailing the slice. Shaped doc was rewritten before Story 1 resumed; that resynchronisation is what kept the pivots cheap.
- **Per-command cuts hit target.** build −19.7%, implement −21.6%, add-skill −21.7% — all in the 20-30% range the shape called. Output Format templates + imperative-fragment rewrite both carried their weight.
- **Simplify pass caught post-implementation complexity.** commit ccb71e8 trimmed audit-tokens after feature-complete but before prompt cuts. The feature-first / simplify-second ordering worked — cleanest module shape only emerged after the behaviour was nailed.

## Harder Than Expected

- **Both pivots had one root cause.** The shape step named a measurement instrument (`anthropic.messages.count_tokens`) that was never smoke-tested from the Claude Code session — OAuth doesn't grant API access, requires a funded account. Discovery happened mid-Story-1. General pattern: measurement-centric issues freeze the instrument in the AC before anyone's confirmed it runs.
- **4.6% total savings feels modest next to 20% per-command.** Top-3 cap is the bottleneck — the long tail of commands absorbs the remaining prose. Not a failure of technique, a failure of scope.

## Wrong Assumptions

- **Original 'small batch' appetite was right for the rejected shape, wrong for the chosen one.** Appetite calibrated for scripts/audit_command_tokens.py; the proper core/ + cli/ + tests version was medium. Appetite must be re-evaluated when shape pivots, not inherited from the pre-pivot frame.
- **Expected redundant *steps*, not just redundant *prose*.** Audit landed purely on prose density. Step-level dedup wasn't where the wins were on the top-3 — but may be elsewhere in the long tail.
- **97% tiktoken accuracy mattered.** It didn't. Rank + delta were always going to dominate; absolute accuracy is second-order for this class of audit.

## Recommendations

- **scripts/ is an anti-pattern for recurring tooling.** If the capability will be re-invoked (and most measurement tools will be), default to core/ + cli/ split from day one. Elevate this from story-1 learning to a shape-time check. (Confirmed with user.)
- **Measurement-centric issues need instrument smoke-test at shape time.** For any issue whose spec names a tokenizer, cost API, cloud measurement endpoint, or external SDK call, verify the instrument actually runs from the Claude Code session context before freezing it in the AC. Two pivots on 74 trace to skipping this.
- **Extend audit to ALL commands + skills in the vault.** Current sweep only covers `claude/commands/mantle/*.md`. File a follow-up issue for a combined commands + skills audit. (User confirmed to file as new issue.)
- **Every /mantle:* command that emits output needs an Output Format section.** Durable output discipline, not just a token-trim technique. AI outputs should follow the same terse pattern across all commands, not just top-3. (User confirmed.)
- **Before/After + Delta-summary is a reusable audit shape.** `mantle audit-tokens --append` is the first instance; pattern generalises to prompt-pruning rounds, schema-migration audits, any 'measure around a discrete intervention' workflow. Worth naming before the next measurement issue.
- **Re-evaluate appetite after shape pivot.** Inherited appetite from pre-pivot framing is a trap (74 was called 'small' for a script, landed as 'medium' for proper CLI). Post-pivot, reprice explicitly.