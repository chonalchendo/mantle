---
issue: 29
title: Verify prompt — structured first-use, evolution, and build alignment
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want corrections I give during verification to persist so I don't repeat myself every build cycle.

## Depends On

Story 2 — uses the mantle introspect-project CLI command.

## Approach

Update verify.md prompt to use project introspection for first-use, add an evolution step after verification, and update build.md's verify override for non-interactive strategy generation. This is a prompt-only story — no Python code changes.

## Implementation

### claude/commands/mantle/verify.md (modify)

**Step 3 — Load verification strategy** (replace existing first-use flow):

Replace the current first-use flow (lines telling user to 'describe their preferred verification strategy') with:

1. Run `mantle introspect-project` to detect project setup
2. Parse the JSON output to get detected commands
3. Read the stderr output to get the proposed structured strategy
4. Present the proposed strategy to the user:
   > Based on your project setup, I propose this verification strategy:
   > {structured strategy from introspect-project}
   > Would you like to use this, or adjust it?
5. After user confirms (or adjusts), save via:
   ```bash
   mantle save-verification-strategy --strategy "{final strategy}"
   ```

**Add Step 7.5 — Strategy evolution** (new step after Step 7 Report results):

After presenting the verification report, check whether the user corrected or adjusted the verification approach during this session. If so:

1. Summarise what corrections were made
2. Ask: 'Should I update the verification strategy to include these changes?'
3. If confirmed, construct the updated strategy by appending/refining the relevant section
4. Save via `mantle save-verification-strategy --strategy "{updated strategy}"`
5. Report: 'Verification strategy updated.'

Important: existing strategy content is preserved — corrections append or refine sections, never silently overwrite the whole strategy.

### claude/commands/mantle/build.md (modify)

**Step 8 — Verify** (update the build-mode override):

In the verify agent prompt within Step 8, update the override for missing strategy:

Replace: 'If no verification strategy is configured, use a sensible default: run the test suite and check each acceptance criterion against the implementation'

With: 'If no verification strategy is configured, run `mantle introspect-project` to auto-detect project setup, then save the generated strategy via `mantle save-verification-strategy --strategy "{generated strategy}"` before proceeding with verification. This creates a real structured strategy for future runs.'

#### Design decisions

- **Prompt-only story**: No Python code changes — all verification flow logic lives in the prompt, consistent with the project's 'prompt orchestrates, AI implements' principle.
- **Append-only evolution**: Strategy updates refine sections rather than replacing the whole string. This satisfies AC 7 (existing strategies preserved).
- **Build pipeline uses same introspection**: The build.md override calls the same CLI command as verify.md's first-use flow, ensuring consistency (AC 6).

## Tests

No automated tests — this is a prompt-only change. Verification is done by running the verify command and checking that:
1. First-use flow calls introspect-project and proposes a structured strategy
2. Strategy evolution prompts after corrections
3. Build pipeline auto-generates strategy when none exists