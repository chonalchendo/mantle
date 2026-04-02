---
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *)
---

Break an issue into implementable, session-sized stories with TDD test specifications,
proposed one at a time with user approval on each.

Think in terms of "what would a fresh Claude Code session need to know to build this?"
Every story must be self-contained with all the context needed for implementation. Push
for specificity — challenge vague stories.

Be structured, precise, and implementation-focused. Each story opens with who benefits
and what they experience (user story), then provides the detailed technical specification
for how to build it. Wait for explicit approval before moving on.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Select issue and load context"
3. "Step 3 — Propose stories one at a time"
4. "Step 4 — Save each approved story"
5. "Step 5 — Coverage check"
6. "Step 5b — Story self-review"
7. "Step 5c — Load relevant skills"
8. "Step 6 — Session wrap-up"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Read `.mantle/state.md` and verify:

- `.mantle/` exists. If not, tell the user to run `mantle init` first.
- Status is `planning`. This is the valid state for story planning.
- If status is earlier, tell the user the current status and suggest the appropriate
  next command (e.g., `/mantle:plan-issues`, `/mantle:shape-issue`).

## Step 2 — Select issue and load context

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, ask the user which issue to decompose. Then read and internalise:

- `.mantle/issues/issue-<NN>.md` — the selected issue (acceptance criteria, what to
  build, slice)
- `.mantle/shaped/issue-<NN>-shaped.md` — the shaped issue if it exists (chosen
  approach, appetite, open questions)
- `.mantle/product-design.md` — for user stories referenced by the issue
- `.mantle/system-design.md` — for module structure, API contracts, data model relevant
  to the issue's slice
- `.mantle/stories/issue-<NN>-story-*.md` — any existing stories for this issue (to
  understand what's already decomposed)
- `.mantle/learnings/` — any learnings from previous issues (to avoid repeating
  mistakes)

Display context summary:

> **Issue {NN}**: {title}
> **Slice**: {slice layers}
> **Shaped**: {Yes — approach: {chosen_approach}, appetite: {appetite} | No — consider running /mantle:shape-issue first}
> **Existing stories**: {count} already planned
> **Acceptance criteria**: {count} criteria to cover

## Step 3 — Propose stories one at a time

For each story, propose:

1. **Title** — concise, action-oriented (e.g., "Core stories module — StoryNote, save,
   load, list")
2. **User story** — a one-line user story: *"As a [role], I want [capability] so that
   [outcome]."* This grounds the implementing agent in who benefits and what the user
   should experience once the story is built. Derive the role from the parent issue's
   user stories and the capability from the specific slice this story delivers.
3. **Approach** — 2-3 sentences explaining *how* this story delivers the user story.
   Which codebase pattern it follows, which modules it builds on, and how it fits into
   the issue's broader story sequence.
4. **Implementation** — detailed description of what to build, organized by file:
   - Which files to create or modify
   - For each file: what functions, classes, or changes to make
   - Design decisions with rationale
   - Import requirements
5. **Tests** — specific test cases organized by test file:
   - Which test files to create or modify
   - Each test as a one-line description (e.g., "**save_story**: writes file to
     `.mantle/stories/` directory")
   - Test fixture requirements (tmp_path setup, mocks needed)

Rules for story sizing:

- Each story must be completable in a single Claude Code session (one context window)
- A story should touch 1-3 files in implementation (not counting tests)
- If a story needs to modify more than 3 implementation files, it should be split
- Tests are part of the same story as the code they test — never separate "write tests"
  stories
- Stories within an issue should build on each other: story 1 provides the foundation,
  story 2 adds the next layer, story 3 adds the user-facing layer

Rules for story content:

- **## User Story** is a single line: *"As a [role], I want [capability] so that
  [outcome]."* Derive from the parent issue's user stories. This orients the
  implementing agent — it knows who benefits and what the experience should be before
  diving into the how.
- **## Approach** is 2-3 sentences connecting the user story to the implementation
  strategy. Which pattern does this follow? What does it build on? Where does it fit
  in the story sequence?
- **## Implementation** must be specific enough that an AI agent can build it without
  reading the issue or design docs. Include: exact file paths, function signatures,
  expected behaviour, design decisions, import patterns.
- **## Tests** must list specific test cases, not vague "test that it works"
  descriptions. Each test targets one behaviour.
- Stories should follow existing codebase patterns (discover them by reading existing
  code in the project)
- Reference existing modules that the story builds on (e.g., "follows the pattern of
  `core/shaping.py`")

Present each proposed story and **wait for user approval or adjustment**. Do not
propose the next story until the current one is approved.

After presenting each story, use AskUserQuestion to let the user choose:
- **Approve** — save the story and proceed to the next
- **Adjust** — modify the proposal (ask what to change)
- **Skip** — move to the next story without saving
- **Stop** — end the planning session

## Step 4 — Save each approved story

After user approval, save using the CLI:

```bash
mantle save-story \
  --issue <issue_number> \
  --title "<story title>" \
  --content "<full story body>"
```

The `--content` body should follow this structure:

```markdown
## User Story

As a [role], I want [capability] so that [outcome].

## Approach

[2-3 sentences: which pattern this follows, what it builds on, where it fits in the
story sequence.]

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

## Step 5 — Coverage check

After all stories are proposed (or user stops), verify coverage:

1. Check each acceptance criterion from the parent issue — is it covered by at least
   one story?
2. Check that the issue's full slice is represented (e.g., if slice is
   `[core, cli, claude-code, tests]`, stories should collectively touch all those
   layers)
3. If gaps exist, propose additional stories to fill them

Display coverage summary:

> **Acceptance criteria coverage:**
> - [x] Criterion 1 — covered by story 1, 2
> - [x] Criterion 2 — covered by story 3
> - [ ] Criterion 3 — **not covered** (propose additional story?)
>
> **Slice coverage:** core ✓, cli ✓, claude-code ✓, tests ✓

## Step 5b — Story self-review

Before loading skills, review the full set of stories with fresh eyes:

1. **Placeholder scan** — Any "TBD", "TODO", vague implementation descriptions,
   or test cases that say "test that it works"? Fix them now.
2. **Internal consistency** — Do later stories reference functions, modules, or
   patterns that earlier stories actually create? Does story 3 assume an API
   that story 1 doesn't define?
3. **Naming consistency** — Are function names, class names, and file paths
   consistent across stories? A function called `save_story` in story 1 but
   `write_story` in story 3 is a bug.
4. **Ambiguity check** — Could any implementation description be interpreted two
   different ways by an implementing agent? If so, make the intent explicit.

Fix any issues by updating the saved stories via `mantle save-story --issue <N>
--story <S> --title "<title>" --content "<updated content>" --overwrite`.

## Step 5c — Load relevant skills

After stories are saved, ensure the right vault knowledge is available for
implementation.

1. **Auto-detect existing skills**: Run `mantle update-skills --issue {NN}` to
   scan the issue and stories for vault skill matches.

2. **Identify skill gaps**: Review the technologies and patterns referenced in
   the stories. For any that don't have a matching vault skill, tell the user:

   > **Skill gaps detected:**
   > - {technology} — no vault skill found
   >
   > Consider running `/mantle:add-skill` to create skills for these before
   > implementation. Vault skills give the implementing agent domain-specific
   > knowledge (patterns, conventions, anti-patterns) beyond what's in its
   > training data.

3. Run `mantle compile` to ensure the latest skills are compiled.

## Step 6 — Session wrap-up


When the user stops planning, summarise:

> **Story planning complete for issue {NN}.**
> - Stories planned: {count}
> - Acceptance criteria covered: {covered}/{total}

Then briefly assess before recommending next steps:

- Is acceptance criteria coverage complete?
- Are any stories unclear or underspecified?
- Were coverage gaps identified that need additional stories?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:implement --issue {NN}` — default. Recommend when stories are complete and acceptance criteria coverage is good.
- `/mantle:plan-stories` — recommend when coverage gaps were identified that need additional stories before implementation.

**Default:** `/mantle:implement --issue {NN}` if coverage is complete.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]
