---
description: Use when you want to add a single new issue to an existing project's backlog
allowed-tools: Read, Bash(mantle *)
---

Add a single validated issue to the project backlog without re-running the full
plan-issues pipeline. Ideal for turning a brainstorm verdict into an actionable
issue while context is fresh.

Be collaborative and structured. One question per message. Prefer multiple
choice. Reflect back and confirm before moving on.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Load context"
3. "Step 3 — Capture the issue"
4. "Step 4 — Deduplication check"
5. "Step 5 — System design impact check"
6. "Step 6 — Save"
7. "Step 7 — Recommend next step"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Read `.mantle/state.md` and verify:

- `.mantle/` exists. If not, tell the user to run `mantle init` first.
- Status is `planning`. If not, tell the user the current status and suggest
  the appropriate next command.

## Step 2 — Load context

Read and internalise:

- `.mantle/issues/` — all existing issues (for numbering and deduplication).
  Read all issue files.
- `.mantle/system-design.md` — the system architecture (for architecture
  checks).
- `.mantle/brainstorms/` — past brainstorms (for brainstorm file linking). Read
  all brainstorm files if the directory exists.

Display a context summary:

> **Existing issues**: {count} issues in backlog. Latest: issue-{NN} "{title}".
> **Available slices**: {slices from state.md}
> **Available brainstorms**: {count} ({proceed count} with "proceed" verdict)

## Step 3 — Capture the issue

Interactive conversation. Ask one question per message. 3-5 exchanges total.

1. What's the idea or feature you'd like to add to the backlog? (open-ended)
2. What are the acceptance criteria? Suggest 3-5 concrete, testable criteria.
   Present as a multiple choice starting point the user can refine:
   - Example: "Works end-to-end with a real project"
   - Example: "Handles error case X gracefully"
   - Example: "Covered by tests"
3. Which slices does this touch? Present the available slices from `state.md`
   as a multiple choice list.
4. Does this depend on any existing issues? Show the list of existing issue
   titles with numbers and let the user pick.

After each answer, reflect back what you heard and confirm before proceeding.

### Rules

- **One question per message.** Do not dump multiple questions.
- **Prefer multiple choice** where appropriate.
- **Reflect back and confirm** before moving on.
- Use AskUserQuestion for interactive choices.

## Step 4 — Deduplication check

Compare the proposed title and description against all existing issue
titles and descriptions.

Use `<analysis>` to reason through overlap:

```
<analysis>
- Does the title closely match any existing issue?
- Does the description duplicate work covered by an existing issue?
- Is this a subset or extension of an existing issue?
</analysis>
```

If overlap is found, flag it clearly:

> **Overlap detected**: This idea may overlap with issue-NN "{title}".
> [Brief explanation of the overlap.]
>
> Do you want to (a) proceed anyway, (b) modify the scope to avoid overlap, or
> (c) abandon this issue?

If no overlap, confirm:

> **No duplicates found.** This issue covers new ground.

## Step 5 — System design impact check

Compare the proposed slices and description against `system-design.md`.

Use `<analysis>` to assess impact:

```
<analysis>
- Does this issue introduce architecture not covered in system-design.md?
- Does it add new modules, APIs, or data models?
- Would system-design.md need updating to reflect this issue?
</analysis>
```

If architectural gaps are found, flag them:

> **Architecture note**: This issue introduces {area} not currently described
> in `system-design.md`. Consider running `/mantle:revise-system` to update
> the design before building.

If no gaps, confirm:

> **Architecture check passed.** This issue fits within the existing design.

## Step 6 — Save

Compile the full issue from the conversation and save via the CLI.

If a brainstorm file was found whose title or idea closely matches this issue,
include a `## Brainstorm reference` section with the path.

```bash
mantle save-issue \
  --title "<issue title>" \
  --slice "<slice1>" --slice "<slice2>" \
  --content "<full issue body>" \
  --blocked-by <issue_number>
```

The `--content` body must follow this structure:

```markdown
## Parent PRD

product-design.md, system-design.md

## Why

{user's description of the problem and value}

## What to build

{summary of what the issue delivers}

### Flow

1. {numbered steps describing the user-facing flow}

## Acceptance criteria

- [ ] {criterion}
- [ ] {criterion}

## Brainstorm reference

{path to brainstorm file, e.g. .mantle/brainstorms/brainstorm-YYYY-MM-DD-slug.md — omit this section entirely if no matching brainstorm}

## Blocked by

{blocking issue references, e.g. "- Blocked by issue-NN (needs ...)" — or "None"}

## User stories addressed

- As a {role}, I want {capability} so that {outcome}
```

After saving, confirm the saved file path and issue number.

## Step 7 — Recommend next step

Briefly assess what was captured before recommending next steps:

- Is the issue well-shaped or does it need approach exploration?
- Is it simple enough to go straight to story planning?

**Default recommendation:** `/mantle:shape-issue {NN}` — explore approaches
before decomposing into stories.

**Alternatives:**

- `/mantle:build {NN}` — if the user wants to move fast. Automates shaping,
  story planning, implementation, and verification in one pass.
- `/mantle:plan-stories {NN}` — if the issue is simple and the approach is
  already clear.

Present one clear recommendation with a reason, then mention alternatives
briefly:

> **Recommended next step:** `/mantle:<command> {NN}` — [reason based on
> the issue you just captured]
>
> Other options: [brief list of alternatives with one-line descriptions]

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "add-issue"

Keep the log under ~200 words following the session log format (Summary, What
Was Done, Decisions Made, What's Next, Open Questions).
