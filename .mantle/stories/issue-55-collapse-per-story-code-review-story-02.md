---
issue: 55
title: Remove per-story code-reviewer from implement.md
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a developer, I want the implementation loop to skip per-story code review so that the build pipeline spends tokens only on the single post-implementation simplify gate.

## Depends On

None — independent. Touches only `claude/commands/mantle/implement.md`; does not depend on story 1.

## Approach

Pure prompt edit. Remove the "Post-implementation review" step (currently sub-step 7 in Step 5) and its "Handling review results" paragraph. Renumber subsequent sub-steps: current 8 → 7, current 9 → 8. Fix any cross-references elsewhere in the file.

## Implementation

### claude/commands/mantle/implement.md (modify)

1. **Delete sub-step 7 entirely** — from the line starting `7. **Post-implementation review**:` through the end of its "Handling review results" bullet list (the line starting `- **Issues found**: ...`). This is the `code-reviewer` agent spawn block and its fix-cycle paragraph.

2. **Renumber sub-steps**: current sub-step 8 (`**Handle outcome**:`) becomes **7**; current sub-step 9 (`**Extract learnings**:`) becomes **8**.

3. **Update cross-references**:
   - In the renumbered sub-step 7 (old 8): change the phrase "Tests pass (and review passed or issues fixed)" to "Tests pass" — there is no review step anymore.
   - Search the whole file for any remaining references to "sub-step 7", "step 7", "post-implementation review", "code-reviewer", or "review agent" and fix or delete them.
   - In the "Wave completion" paragraph (around line 282), the phrase "sub-steps 1-9" becomes "sub-steps 1-8".

4. **Do NOT** change the "Verification Discipline" section, the Iron Laws, the Red Flags table, Step 4 (Select relevant context per story), or Step 6 (Report results). Those are unrelated.

5. **Do NOT** remove the `code-reviewer` agent type from any subagent registry — only stop implement.md from spawning it.

6. After editing, re-read the file top-to-bottom to confirm sub-step numbering is consistent (1, 2, 3, 4, 5, 6, 7, 8 with no gaps) and that no orphan reference to a removed step remains.

#### Design decisions

- **Full removal rather than `allowed-tools` flag**: the step is dead code if the issue's whole premise holds — leaving it behind a flag just re-creates the hidden-complexity problem the brainstorm flagged.
- **Keep `Extract learnings`**: unrelated to code review; still valuable.

## Tests

No production-code tests — this story is a prompt-file edit with no Python code change.

Manual verification (part of verify step, not this story):
- Grep `claude/commands/mantle/implement.md` for `code-reviewer`, `Post-implementation review`, `REVIEW: PASS`, `REVIEW: ISSUES` — all must be absent.
- Grep for `sub-step 7`, `sub-step 8`, `sub-step 9` — `sub-step 9` must be absent; `sub-step 7` and `sub-step 8` must exist and reference the renumbered steps.
- The sub-step numbered list inside Step 5 must run 1→8 with no gaps.

## Out of scope

- Any change to build.md.
- Any change to Python code or the `code-reviewer` agent definition.
- Updating standalone `/mantle:simplify` or `/mantle:verify`.