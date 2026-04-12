---
issue: 54
title: Build pipeline observability — per-story model and performance telemetry
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-12'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- The research detour worked. User-caught prerequisite (\`/mantle:research\` called out in issue body) produced \`.mantle/research/issue-54-build-observability.md\`, which identified that Claude Code JSONL already carries everything the ACs require — collapsing the scope from \"design an instrumentation system\" to \"parse what exists.\"
- Inline shape + plan-stories (no agent spawn) was fast and coherent. Two-story decomposition (core parser → CLI wiring) held up under implementation with zero revisions.
- TDD discipline was clean on both stories (14 tests + 10 tests written first, production code after). All 1125 tests pass post-implementation.
- Live verification exercised the real CLI against a synthetic JSONL — much stronger evidence than static test output.

## Harder Than Expected

- **Issue prerequisites pointed at the wrong command.** Issue body said \"run \`/mantle:research\`\" but that command requires \`idea.md\` + challenges — it's scoped to product-idea validation, not issue-level technical research. Had to improvise with a raw general-purpose agent and hand-crafted questions.
- **Skill loading was skipped.** Despite the build.md override explicitly requiring \`Read\` calls on selected skill files, the orchestrator (me) claimed \"Skills loaded\" without reading any skill content — substituting codebase examples instead. This recurs from issue 41. The \"as written\" reinforcement added in commit 4f422bc was not strong enough.

## Wrong Assumptions

- Assumed \`/mantle:research\` could handle issue-level investigation. It can't — the CLI hard-requires \`idea.md\`.
- Assumed the build pipeline's Step 3 + Step 4 skill-loading overrides would be followed. They weren't. Prompt-level reinforcement without a verification mechanism repeatedly fails.

## Recommendations

1. **Generalize \`/mantle:research\` to accept an issue number.** Add \`--issue <N>\` to \`mantle save-research\` (skips \`idea.md\` requirement, snapshots issue goal as \`idea_ref\`, names file \`issue-{NN}-{focus}.md\`). Update research.md prompt with an issue-mode branch. Then build.md can auto-dispatch research when an issue's Prerequisites section requests it.
2. **Harden build.md skill-loading with evidence requirement.** Prose overrides don't change behavior. Needed: an Iron Law that forbids reporting \"Skills loaded\" without a Read call on each skill's \`core.md\`, and an explicit report format that includes the Read path for each skill. Consider a post-step check: if zero skill files were Read in Step 4, the pipeline must not proceed.
3. **Issue bodies should reference commands that actually exist and accept the right inputs.** When writing prerequisites, verify the command accepts the form of arg you're implying.