---
issue: 28
title: Add-issue slash command — interactive single-issue creation
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer mid-project, I want to add a single validated issue to my backlog without re-running the full plan-issues pipeline, so that brainstorm verdicts flow naturally into actionable issues.

## Depends On

None — independent (no prior stories for this issue).

## Approach

Create `claude/commands/mantle/add-issue.md` following the established prompt command pattern (brainstorm.md, challenge.md). The prompt orchestrates an interactive session that reads existing context, captures issue details conversationally, performs dedup and design-impact checks, then saves via the existing `mantle save-issue` CLI. Also update help.md to list the new command.

## Implementation

### claude/commands/mantle/add-issue.md (new file)

Create a static Claude Code slash command with this structure:

**Frontmatter:**
- `description`: "Use when you want to add a single new issue to an existing project's backlog"
- `allowed-tools`: `Read, Bash(mantle *)`

**Steps (follow brainstorm.md pattern):**

1. **Step 1 — Check prerequisites**
   - Read `.mantle/state.md`, verify status is `planning`
   - If not, tell user current status and suggest next command

2. **Step 2 — Load context**
   - Read `.mantle/issues/` — all existing issues (for numbering, dedup)
   - Read `.mantle/system-design.md` — for architecture checks
   - Read `.mantle/brainstorms/` — for brainstorm file linking
   - Display context: existing issue count, latest issue number, available slices from state.md

3. **Step 3 — Capture the issue (interactive, 3-5 exchanges)**
   - Ask for the idea/feature (one question)
   - Ask for acceptance criteria (suggest 3-5 concrete, testable criteria)
   - Ask for slices touched (present available slices from state.md as options)
   - Ask for dependencies on existing issues (show list of existing issue titles)
   - After each answer, reflect back and confirm

4. **Step 4 — Deduplication check**
   - Compare proposed title and description against all existing issue titles/descriptions
   - If overlap found, flag it: "This overlaps with issue NN: {title}. Proceed anyway, merge, or adjust?"
   - If no overlap, confirm: "No duplicates found."

5. **Step 5 — System design impact check**
   - Compare proposed slices and description against system-design.md
   - If the issue introduces architecture not covered: "This touches {area} which isn't in system-design.md. Consider running /mantle:revise-system after this."
   - If no new architecture: "Fits within current system design."

6. **Step 6 — Save**
   - Compile the issue and save via:
     ```
     mantle save-issue \
       --title "<title>" \
       --slice "<slice1>" --slice "<slice2>" \
       --content "<full issue body with ## Why, ## What to build, ## Acceptance criteria, ## User stories addressed>" \
       --blocked-by <dep1> --blocked-by <dep2>
     ```
   - If a brainstorm file was found matching this idea, include a `## Brainstorm reference` section in the content body referencing the file path

7. **Step 7 — Recommend next step**
   - Default: "/mantle:shape-issue {NN}" — to evaluate approaches before implementation
   - Alternative: "/mantle:plan-stories {NN}" if the issue is simple enough to skip shaping

**Conversation discipline (from brainstorm.md pattern):**
- One question per message
- Prefer multiple choice where applicable (slices, dependencies)
- Reflect back, then confirm before moving on

**Content body format for save-issue:**
```markdown
## Parent PRD

product-design.md, system-design.md

## Why

{user's description of why this is needed}

## What to build

{summary of what the issue delivers}

### Flow

{numbered steps of what the command/feature does}

## Acceptance criteria

- [ ] {criterion 1}
- [ ] {criterion 2}
...

## Brainstorm reference

{path to brainstorm file, if found — otherwise omit this section}

## Blocked by

{list of blocking issues, or "None"}

## User stories addressed

- As a {role}, I want {capability} so that {outcome}
```

### claude/commands/mantle/help.md (modify)

Add the new command under the **Planning** section, after the `/mantle:plan-issues` line:

```
- `/mantle:add-issue` — Add a single new issue to the backlog
```

#### Design decisions

- **Prompt-only, no Python**: The `mantle save-issue` CLI already handles persistence, numbering, and frontmatter. No new core/ or cli/ modules needed.
- **Follows brainstorm.md pattern**: Step-based, TaskCreate for progress tracking, allowed-tools restricted to Read + Bash(mantle *), one question per message.
- **Brainstorm file matching**: Simple title/description substring matching against `.mantle/brainstorms/` filenames and content. No fuzzy matching — exact enough is good enough.
- **Dedup is advisory**: Flags overlap but doesn't block. User decides whether to proceed.
- **System design check is advisory**: Flags drift but doesn't block or auto-update.

## Tests

No tests — this is a static markdown prompt file. The underlying `mantle save-issue` CLI is already tested. The prompt's behaviour is verified by the acceptance criteria in Step 8 (verify).