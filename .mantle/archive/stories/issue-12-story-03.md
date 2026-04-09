---
issue: 12
title: Plan-stories command prompt and vault template
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## User Story

As a developer, I want `/mantle:plan-stories` to break each issue into stories that include both implementation tasks and test expectations (TDD approach), sized for a single Claude Code session, so that implementation is predictable and each story is self-contained enough for an AI agent to build independently.

## Approach

Create a static Claude Code command `plan-stories.md` following the pattern of `plan-issues.md` — an interactive session that proposes stories one at a time, waits for approval, and saves via `mantle save-story` (story 2). Also create the `vault-templates/story.md` template. This is story 3 of 3: the user-facing layer that ties together the core module (story 1) and CLI (story 2).

## Implementation

Create the static Claude Code command `plan-stories.md` that guides the interactive story decomposition session, and the Obsidian vault template for stories.

### claude/commands/mantle/plan-stories.md (new file)

Static command prompt following the pattern of `plan-issues.md` and `shape-issue.md`. The AI adopts the persona of a senior engineer who decomposes issues into implementable, session-sized stories with TDD test specifications.

#### Structure

**Step 1 — Check prerequisites**

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell user to run `mantle init`)
- Status is `planning` (the valid state for story planning)
- If status is earlier, tell user the current status and suggest the appropriate next command

**Step 2 — Select issue and load context**

Ask the user which issue to decompose. Then read and internalise:
- `.mantle/issues/issue-<NN>.md` — the selected issue (acceptance criteria, what to build, slice)
- `.mantle/shaped/issue-<NN>-shaped.md` — the shaped issue if it exists (chosen approach, appetite, open questions)
- `.mantle/product-design.md` — for user stories referenced by the issue
- `.mantle/system-design.md` — for module structure, API contracts, data model relevant to the issue's slice
- `.mantle/stories/issue-<NN>-story-*.md` — any existing stories for this issue (to understand what's already decomposed)
- `.mantle/learnings/` — any learnings from previous issues (to avoid repeating mistakes)

Display context summary:
> **Issue {NN}**: {title}
> **Slice**: {slice layers}
> **Shaped**: {Yes — approach: {chosen_approach}, appetite: {appetite} | No — consider running /mantle:shape-issue first}
> **Existing stories**: {count} already planned
> **Acceptance criteria**: {count} criteria to cover

**Step 3 — Propose stories one at a time**

For each story, propose:

1. **Title** — concise, action-oriented (e.g., "Core stories module — StoryNote, save, load, list")
2. **User story** — a one-line user story in the format: *"As a [role], I want [capability] so that [outcome]."* This grounds the implementing agent in who benefits and what the user should experience once the story is built. Derive the role from the parent issue's user stories and the capability from the specific slice this story delivers.
3. **Approach** — 2-3 sentences explaining *how* this story delivers the user story. Which codebase pattern it follows, which modules it builds on, and how it fits into the issue's broader story sequence.
4. **Implementation** — detailed description of what to build, organized by file:
   - Which files to create or modify
   - For each file: what functions, classes, or changes to make
   - Design decisions with rationale
   - Import requirements
5. **Tests** — specific test cases organized by test file:
   - Which test files to create or modify
   - Each test as a one-line description (e.g., "**save_story**: writes file to `.mantle/stories/` directory")
   - Test fixture requirements (tmp_path setup, mocks needed)

Rules for story sizing:
- Each story must be completable in a single Claude Code session (one context window)
- A story should touch 1-3 files in implementation (not counting tests)
- If a story needs to modify more than 3 implementation files, it should be split
- Tests are part of the same story as the code they test — never separate "write tests" stories
- Stories within an issue should build on each other: story 1 provides the foundation, story 2 adds the CLI layer, story 3 adds the command prompt

Rules for story content:
- **## User Story** is a single line: *"As a [role], I want [capability] so that [outcome]."* Derive from the parent issue's user stories. This orients the implementing agent — it knows who benefits and what the experience should be before diving into the how.
- **## Approach** is 2-3 sentences connecting the user story to the implementation strategy. Which pattern does this follow? What does it build on? Where does it fit in the story sequence?
- **## Implementation** must be specific enough that an AI agent can build it without reading the issue or design docs. Include: exact file paths, function signatures, expected behaviour, design decisions, import patterns.
- **## Tests** must list specific test cases, not vague "test that it works" descriptions. Each test targets one behaviour.
- Stories should follow existing codebase patterns (frozen Pydantic models, vault.read_note/write_note, etc.)
- Reference existing modules that the story builds on (e.g., "follows the pattern of `core/shaping.py`")

Present each proposed story and **wait for user approval or adjustment**. Do not propose the next story until the current one is approved.

The user may:
- **Approve** — save the story and proceed
- **Adjust** — modify the proposal (change scope, add/remove tests, split further)
- **Skip** — move to the next story without saving
- **Stop** — end the planning session

**Step 4 — Save each approved story**

After user approval, save using the CLI:

```bash
mantle save-story \
  --issue <issue_number> \
  --title "<story title>" \
  --content "<full story body including: ## Implementation and ## Tests sections>"
```

The `--content` body should follow the structure used by existing stories in `.mantle/stories/`:

```markdown
## User Story

As a [role], I want [capability] so that [outcome].

## Approach

[2-3 sentences: which pattern this follows, what it builds on, where it fits in the story sequence.]

## Implementation

[Detailed implementation description organized by file...]

### path/to/file.py (new file | modify)

[What to create or change...]

#### Design decisions

- **Decision**: Rationale

## Tests

### tests/path/to/test_file.py (new file | modify)

- **test_name**: description of what it tests
- **test_name**: description of what it tests
```

**Step 5 — Coverage check**

After all stories are proposed (or user stops), verify coverage:

1. Check each acceptance criterion from the parent issue — is it covered by at least one story?
2. Check that the issue's full slice is represented (e.g., if slice is `[core, cli, claude-code, tests]`, stories should collectively touch all those layers)
3. If gaps exist, propose additional stories to fill them

Display coverage summary:
> **Acceptance criteria coverage:**
> - [x] Criterion 1 — covered by story 1, 2
> - [x] Criterion 2 — covered by story 3
> - [ ] Criterion 3 — **not covered** (propose additional story?)
>
> **Slice coverage:** core ✓, cli ✓, claude-code ✓, tests ✓

**Step 6 — Session wrap-up**

When the user stops planning, summarise:

> **Story planning complete for issue {NN}.**
> - Stories planned: {count}
> - Acceptance criteria covered: {covered}/{total}
> - Next: run `/mantle:implement --issue {NN}` to start building, or `/mantle:plan-stories` for another issue.

#### Persona

Senior engineer who decomposes work into precise, implementable units. Thinks in terms of "what would a fresh Claude Code session need to know to build this?" Every story is self-contained: it includes all the context needed for implementation. Pushes for specificity — vague stories get challenged.

#### Tone

Structured, precise, and implementation-focused. Each story opens with who benefits and what they experience (user story), then provides the detailed technical specification for how to build it. Wait for explicit approval before moving on.

### vault-templates/story.md (new file)

Obsidian note template for stories. Used when creating stories directly in the vault.

```yaml
---
issue:
title:
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## User Story

_As a [role], I want [capability] so that [outcome]._

## Approach

_How this story delivers the user story. Which pattern it follows, what it builds on._

## Implementation

_Describe what to build, organized by file. Include function signatures, design decisions, and import patterns._

## Tests

_List specific test cases. Each test targets one behaviour._
```

#### Design decisions

- **Static command, not compiled.** The plan-stories command reads context dynamically during the session (issue file, shaped issue, design docs). No vault state needs to be baked in. This matches plan-issues.md.
- **One-at-a-time pacing.** Matches the pattern from plan-issues: propose one story, wait for approval, save, then propose the next. The user maintains control over decomposition granularity.
- **Coverage check at the end.** After all stories are proposed, the command verifies that acceptance criteria and slice layers are covered. This catches gaps before the user starts implementation.
- **Stories include both ## Implementation and ## Tests.** The product design explicitly requires stories to include both implementation tasks and test expectations (TDD approach). Tests are a natural extension of story functionality — never planned separately.
- **Self-contained stories.** Each story must include enough context for a fresh Claude Code session. The implementation section references exact file paths, function signatures, and design decisions. A story should never say "see the system design" — it should include the relevant details inline.
- **Learnings loaded during planning.** The command reads `.mantle/learnings/` to surface past implementation learnings. This implements the feedback loop: retrospective → learnings → future planning.

## Tests

No automated tests for this story. The static command prompt is a markdown file that guides Claude's behaviour — it's verified by manual usage and the acceptance criteria in the parent issue. The vault template is a static file with no logic.

Verification:
- The `plan-stories.md` file exists at `claude/commands/mantle/plan-stories.md`
- The vault template exists at `vault-templates/story.md`
- The template frontmatter matches the `StoryNote` schema from story 1
- Running `mantle install` copies `plan-stories.md` to `~/.claude/commands/mantle/`
