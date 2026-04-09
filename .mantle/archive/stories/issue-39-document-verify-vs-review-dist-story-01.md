---
issue: 39
title: Document verify vs review distinction and add convention check to verify
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer reading verification results, I want to understand what verify checks and what it doesn't, and see convention deviations surfaced early, so I don't skip the review step and fewer issues reach human review.

## Depends On

None — independent (first and only story).

## Approach

Edit verify.md and review.md command prompts directly. Add documentation blocks clarifying the scope of each command. Add a convention check sub-step to verify.md between 'Execute verification' and 'Report results' that reads CLAUDE.md and system-design.md and flags deviations as warnings. No Python code changes needed — this is entirely prompt-layer work.

## Implementation

### claude/commands/mantle/verify.md (modify)

1. **Add scope documentation** after the opening description (before Dynamic Context):

   Add a section titled '## Scope' or integrate into the existing intro text:
   - verify checks **functional correctness** against acceptance criteria
   - verify does NOT check architectural quality, convention adherence, or design consistency
   - For architectural review, use /mantle:review

2. **Add Step 6.5 — Convention Check** between Step 6 (Execute verification) and Step 7 (Report results):

   The convention check step should:
   - Read CLAUDE.md from the project root
   - Read .mantle/system-design.md (the architecture conventions section)
   - Run `mantle collect-issue-files --issue {NN}` to get the list of changed files
   - Read each changed file
   - Compare against conventions from CLAUDE.md and system-design.md
   - Record deviations as warnings (NOT as pass/fail criteria)

3. **Modify Step 7 — Report results** to include a Convention Warnings section:

   After the existing pass/fail table, add:
   ```
   > **Convention Warnings** (informational — not pass/fail):
   > - {warning 1}
   > - {warning 2}
   > (or 'No convention deviations detected')
   ```

   Make clear these do not affect the overall PASSED/FAILED verdict.

### claude/commands/mantle/review.md (modify)

1. **Add scope documentation** after the opening description (before Dynamic Context):

   Add text clarifying:
   - review checks **architectural quality**, convention adherence, and design consistency
   - review is the authoritative quality gate — verification checks functional correctness, review checks everything else
   - The reviewer should look for: convention deviations, architectural consistency, code quality patterns

#### Design decisions

- **Convention check as warnings, not failures**: The issue explicitly requires convention deviations as warnings only. This avoids blocking builds for style issues while still surfacing them early.
- **No Python code**: Convention checking is an AI task (read conventions, compare against code, report deviations). No programmatic parser needed — the AI agent doing verification is well-suited to this kind of review.
- **Step 6.5 naming**: Inserted between existing steps to avoid renumbering all subsequent steps and breaking references in build.md and other orchestrators.

## Tests

No Python tests needed — this is a prompt-only change. The acceptance criteria are verified by:
- Reading verify.md to confirm scope documentation exists
- Reading review.md to confirm scope documentation exists
- Reading verify.md to confirm convention check step exists
- Reading the convention check step to confirm it produces warnings, not pass/fail results