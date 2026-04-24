---
allowed-tools: Read, Bash(mantle *)
---

Revise the existing system design in `.mantle/system-design.md` through an
interactive session. Log what changed and why. Challenge changes that introduce
unnecessary complexity and ensure revisions stay grounded in the product design
constraints.

Be collaborative, precise, and Socratic. Ask probing questions about the
implications of proposed changes. The user makes the final calls.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Load context"
3. "Step 3 — Interactive revision session"
4. "Step 4 — Vision section enforcement"
5. "Step 5 — Confirm and save"
6. "Step 6 — Confirmation"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Record the stage:

    mantle stage-begin revise-system

First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.

Check whether `.mantle/`, `$MANTLE_DIR/system-design.md`, and
`$MANTLE_DIR/product-design.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first and stop.
- If `system-design.md` does not exist, tell them to run `/mantle:design-system`
  first and stop.

## Step 2 — Load context

Read and internalise:
- `$MANTLE_DIR/system-design.md` — the current system design (primary focus)
- `$MANTLE_DIR/product-design.md` — for alignment context
- `$MANTLE_DIR/idea.md` — the core problem and insight
- Any files in `$MANTLE_DIR/decisions/` — prior decisions for context

Display a summary of the current system design to the user, highlighting the key
architectural decisions and structure.

## Step 3 — Interactive revision session

Ask the user what they want to change and why. This is a conversation, not a
form fill. Discuss the technical tradeoffs of proposed changes:

- Does this change affect system boundaries or data flow?
- Does it invalidate any prior decisions in `$MANTLE_DIR/decisions/`?
- Does it introduce new dependencies or constraints?
- Does it still satisfy the product design requirements?
- What are the risks of this change?

Iterate until the user is satisfied with the revisions. You may suggest related
changes if they follow logically (e.g., if changing the data model, the API
contracts may also need updating).

## Step 4 — Vision section enforcement

After finalising the revisions, check whether the `## Vision` section at the top
of the system design document still accurately reflects the changes.

- If the vision still holds, say so and move on.
- If the vision no longer reflects the changes, propose an updated vision and
  get the user's approval before proceeding.

## Step 5 — Confirm and save

Show a concise before/after summary (3-5 bullet points of what changed, not a
full diff). Ask the user to confirm.

Then run the CLI command with the FULL revised document body:

```bash
mantle save-revised-system-design \
  --content "<full revised system design document body>" \
  --change-topic "<short-slug>" \
  --change-summary "<1-2 sentences of what changed>" \
  --change-rationale "<1-2 sentences of why>"
```

Guidelines for the change metadata:
- `--change-topic`: short slug like "simplify-architecture", "add-caching-layer",
  "revise-data-model"
- `--change-summary`: factual description of what changed
- `--change-rationale`: why this change was made

## Step 6 — Confirmation

After a successful save, tell the user:

> System design revised! A decision log entry has been created to track this
> change. Review the updated design in `.mantle/system-design.md`.

## Output Format

One line per changed section in the before/after summary:

- **Section**: <name> — **Change**: <one-line description of what changed>

Anti-patterns:
- No "I noticed" / "I'll do X next" framing
- No restating unchanged sections
- No trailing summary paragraph after the save confirmation
- No emoji

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "revise-system"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).
