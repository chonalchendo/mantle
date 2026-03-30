---
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *)
---

Capture implementation learnings after completing an issue, so future planning
benefits from past experience. Help the user think clearly about what happened
and why, then distill actionable recommendations.

## Dynamic Context

- **Current branch**: !`git branch --show-current`
- **Recent commits**: !`git log --oneline -10`

Be reflective, honest, and forward-looking. Ask probing questions. Draw out
specific examples, not vague generalities. Focus on what's useful for next time.

## Step 1 — Check prerequisites

Check whether `.mantle/`, `.mantle/state.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first.
- Read `state.md` and verify status is `verifying`, `reviewing`, or `completed`.
  If not, tell them the current status and that retrospectives run after
  implementation.

## Step 2 — Load context

Read and internalise:
- The shaped issue file from `.mantle/shaped/` for the current issue (if exists)
- Any existing files in `.mantle/learnings/` — past learnings for patterns
- `.mantle/state.md` — to identify the current issue number

If a shaped issue exists, use it as the baseline for reflection — what was
planned vs what actually happened.

If past learnings exist, briefly note recurring themes before starting.

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, ask the user which issue number they want to retrospect on, or
confirm the current issue from state.md.

## Step 3 — Guided reflection

Work through each area interactively. Ask questions, probe for specifics:

### What went well

- What worked as expected or better than expected?
- Any approaches or patterns worth repeating?
- Where did the shaped issue's plan hold up?

### Harder than expected

- What took longer or was more complex than anticipated?
- Where did estimates miss and why?
- Any rabbit holes that weren't anticipated in shaping?

### Wrong assumptions

- What did you believe going in that turned out to be false?
- Any technical assumptions that didn't hold?
- Any user/product assumptions that shifted?

### Recommendations

- What would you do differently next time?
- Any tools, patterns, or approaches to adopt or avoid?
- What should future shaping sessions account for?

## Step 4 — Assess confidence delta

Ask the user: how has your overall confidence in the project changed after this
issue?

- Format: `+N` or `-N` (e.g. `+2` means confidence increased by 2 points,
  `-1` means it decreased by 1)
- This is relative to their confidence before starting the issue
- Help them calibrate: a major success might be +3, a minor adjustment +1,
  a significant setback -2

## Step 5 — Save learning

Compile the structured reflection and save using the CLI:

```bash
mantle save-learning \
  --issue <number> \
  --title "<issue title>" \
  --confidence-delta "<+N or -N>" \
  --content "<structured reflection with all sections>"
```

## Step 6 — Next steps

After a successful save, check `.mantle/issues/` for remaining unimplemented issues before recommending next steps.

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:shape-issue` — recommend when unimplemented issues remain. These learnings will automatically surface in that session to inform planning.
- `/mantle:plan-issues` — recommend when all current issues are done but the project needs more work planned.
- `/mantle:status` — recommend when the user might want to see overall project state before deciding what's next.

**Default:** `/mantle:shape-issue` if unimplemented issues remain.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you observed]
>
> Other options: [brief list of alternatives with one-line descriptions]
