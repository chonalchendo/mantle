---
issue: 60
title: Remove Step 5c from plan-stories.md
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a Mantle user planning stories, I want `plan-stories.md` to no longer present skill-loading as context-priming for implementation so that I can trust the workflow documentation matches actual runtime behaviour.

## Depends On

None — independent (single-file edit).

## Approach

Apply the shaped approach (option a): cut Step 5c entirely from `claude/commands/mantle/plan-stories.md`. This is the Claude Code prompt layer only — no Python code, no tests. The redundancy with `implement.md` Step 3's own `update-skills + compile` call is resolved by deleting plan-stories' copy.

## Implementation

### claude/commands/mantle/plan-stories.md (modify)

Two edits:

1. **Remove the TaskCreate entry for Step 5c.** At lines 17-27, the TaskCreate list currently reads:

   ```
   1. "Step 1 — Check prerequisites"
   2. "Step 2 — Select issue and load context"
   3. "Step 3 — Propose stories one at a time"
   4. "Step 4 — Save each approved story"
   5. "Step 5 — Coverage check"
   6. "Step 5b — Story self-review"
   7. "Step 5c — Load relevant skills"
   8. "Step 6 — Session wrap-up"
   ```

   Delete line `7. \"Step 5c — Load relevant skills\"` and renumber the final entry to 7 so the list has seven entries total.

2. **Remove the entire \"Step 5c — Load relevant skills\" section** (lines 233-252 in current file). The next section header `## Step 6 — Session wrap-up` must immediately follow `## Step 5b — Story self-review` (separated by one blank line, keeping existing style).

No other changes. Do NOT touch `implement.md`, `shape-issue.md`, `build.md`, or any Python/test file.

#### Design decisions

- **Cut entirely rather than shrink**: `implement.md` Step 3 already runs `mantle update-skills --issue {NN}` and `mantle compile --issue {NN}` before implementation. Keeping even a one-line call in plan-stories duplicates that work for no benefit.
- **Do not touch status.md.j2 / resume.md.j2**: they are display consumers of `skills_required` and remain unaffected — the list is still populated by shape-issue and implement.
- **No follow-up issue for implement.md**: implement.md does load skills. The \"does implement read skill files?\" internal inconsistency noted during shaping is captured as an open question on the shaped issue, not filed as a blocker.

## Tests

No test changes required. The acceptance criteria mandate `just check` passes, which covers existing lint/type/test suites — verification will run that separately.

### Verification after edit

- Confirm `grep -n \"Step 5c\" claude/commands/mantle/plan-stories.md` returns no matches.
- Confirm the TaskCreate list in plan-stories.md has exactly 7 entries.
- Confirm `just check` passes.