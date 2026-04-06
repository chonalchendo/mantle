---
issue: 34
title: Wire auto-transitions into build and implement prompts
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a developer, I want the build pipeline to automatically transition issue status at each phase so that I never need to run manual transition commands during a normal build flow.

## Depends On

Story 1 — needs the `transition-issue-implemented` CLI command and idempotent `transition-issue-implementing`.

## Approach

Update the build.md and implement.md prompt files to call `mantle transition-issue-*` CLI commands at the right lifecycle points. build.md Step 6 start calls `transition-issue-implementing`, Step 6 end calls `transition-issue-implemented`. implement.md also calls `transition-issue-implementing` at start so standalone usage works too.

## Implementation

### claude/commands/mantle/build.md (modify)

In Step 6 (Implement), add at the **start** (before reading implement.md):
```
Run: `mantle transition-issue-implementing --issue {NN}`
```

In Step 6, add at the **end** (after all stories complete successfully):
```
Run: `mantle transition-issue-implemented --issue {NN}`
```

These calls use the CLI commands created in Story 1.

### claude/commands/mantle/implement.md (modify)

In the prerequisites section (Step 1 or Step 2), after confirming the issue exists, add:
```
Run: `mantle transition-issue-implementing --issue {NN}`
```

This is idempotent (Story 1 ensures implementing->implementing is a no-op), so it's safe to call from both build.md and implement.md.

#### Design decisions

- **Idempotent calls**: Both build.md and implement.md call transition-issue-implementing. This is safe because Story 1 makes the transition idempotent. The alternative (only build.md transitions) would leave standalone implement.md usage without auto-transitions.
- **No verify.md changes**: verify.md already calls transition-issue-verified, so no changes needed there.
- **No review.md changes**: review.md already calls transition-issue-approved/implementing, so no changes needed there.

## Tests

### tests/prompts/test_build_prompts.py (new file)

- **test_build_md_contains_transition_implementing**: build.md Step 6 contains the transition-issue-implementing command
- **test_build_md_contains_transition_implemented**: build.md Step 6 contains the transition-issue-implemented command

### tests/prompts/test_implement_prompts.py (new file)

- **test_implement_md_contains_transition_implementing**: implement.md contains the transition-issue-implementing command