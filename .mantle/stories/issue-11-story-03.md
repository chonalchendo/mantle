---
issue: 11
title: Plan-issues command prompt and vault template
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Create the static Claude Code command `plan-issues.md` that guides the interactive one-at-a-time issue planning session, and the Obsidian vault template for issues.

### claude/commands/mantle/plan-issues.md (new file)

Static command prompt following the pattern of `shape-issue.md` and `design-product.md`. The AI adopts the persona of a senior product engineer who decomposes work into thin vertical slices.

#### Structure

**Step 1 — Check prerequisites**

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell user to run `mantle init`)
- Status is one of: `system-design`, `adopted`, or `planning` (these are the valid states from which issue planning can proceed)
- If status is earlier (e.g., `idea`, `product-design`), tell user the current status and suggest the appropriate next command

**Step 2 — Load context and define slices**

Read and internalise:
- `.mantle/product-design.md` — the product definition (features, user stories, milestones)
- `.mantle/system-design.md` — the system architecture (modules, API contracts, data model)
- `.mantle/issues/` — any existing issues (to understand what's already planned, dependencies, and numbering)
- `.mantle/bugs/` — any open bugs (surface these as candidates for new issues, per product design requirement)

Check `state.md` for the `slices` field. If slices are already defined, display them:

> **Project slices:** ingestion, transformation, api, storage, tests

If slices are empty (first planning session), propose slices derived from the system design's architecture section. Ask the user to confirm or adjust:

> Based on your system design, I'd propose these architectural slices for vertical planning:
> - **core** — business logic modules
> - **cli** — command-line interface
> - **claude-code** — Claude Code commands and prompts
> - **vault** — Obsidian vault integration
> - **tests** — test suite
>
> Does this match your architecture? Adjust as needed.

After confirmation, save via:

```bash
mantle set-slices --slice "<layer1>" --slice "<layer2>" --slice "<layer3>"
```

Summarise what's already planned:
> **Existing issues:** [count] issues planned. Latest: issue-NN "[title]".
> **Open bugs:** [count] bugs found. [list titles if any]

**Step 3 — Propose issues one at a time**

For each issue, propose:

1. **Title** — concise, action-oriented (e.g., "Context compilation engine + /mantle:status")
2. **Why** — 1-2 sentences explaining the user-facing value and linking to the product/system design motivation. This bridges the gap between design docs and implementation without requiring a round-trip.
3. **Vertical slice** — which of the project's defined slices this issue cuts through. Use the slice names from `state.md` (defined in Step 2).
4. **What to build** — 2-3 paragraph description of the deliverable
5. **Acceptance criteria** — testable checkboxes defining "done". Each criterion should be independently verifiable.
6. **Blocked by** — which existing issues must complete first (by number)
7. **User stories addressed** — which user stories from the product design this issue satisfies

Rules for vertical slices:
- Each issue must deliver something the user can run or test end-to-end. The litmus test: "can a user verify this works?" If the answer is no, the slice isn't vertical enough.
- Slices should trace from user-facing entry point through to the underlying implementation — nothing is developed in isolation.
- Avoid "pure refactoring" or "pure testing" issues — tests belong with the feature they verify.
- Smaller is better. If an issue feels large, suggest splitting it.
- Use the project's defined slices (from `state.md`) as the vocabulary. Every `--slice` value on saved issues should match a defined slice.

Present the proposed issue and **wait for user approval or adjustment**. Do not propose the next issue until the current one is approved.

The user may:
- **Approve** — save the issue and proceed
- **Adjust** — modify the proposal (change title, add/remove criteria, split, merge)
- **Skip** — move to the next issue without saving
- **Stop** — end the planning session

**Step 4 — Save each approved issue**

After user approval, save using the CLI:

```bash
mantle save-issue \
  --title "<issue title>" \
  --slice "<layer1>" --slice "<layer2>" \
  --content "<full issue body including: ## Parent PRD, ## Why, ## What to build, ## Acceptance criteria, ## Blocked by, ## User stories addressed>" \
  --blocked-by <issue_number> \
  --verification "<optional per-issue verification override>"
```

The `--content` body should follow the structure used by existing issues in `.mantle/issues/`:

```markdown
## Parent PRD

product-design.md, system-design.md

## Why

[1-2 sentences: what user-facing value does this deliver and why now? Links the issue to its motivation in the product/system design.]

## What to build

[Description of what this issue delivers...]

## Acceptance criteria

- [ ] First testable criterion
- [ ] Second testable criterion
...

## Blocked by

- Blocked by issue-NN (needs [reason])

## User stories addressed

- User story NN: [description]
```

**Step 5 — Design impact analysis**

After each issue is saved, analyze whether the issue implies changes to `product-design.md` or `system-design.md`. Check for:

- New API surface not documented in system design
- New commands or features not in the product design user stories
- Architectural changes that affect the module structure
- New data models or schema changes

If design impact is detected, prompt the user:

> "This issue touches [specific area]. Consider running `/mantle:revise-system` to update the [section name] section."

or:

> "This issue adds [feature]. Consider running `/mantle:revise-product` to add user stories for [area]."

The command does NOT edit design docs itself — it identifies the impact and defers to the revise commands (one-command-one-job principle).

**Step 6 — Session wrap-up**

When the user stops planning (or all planned work is proposed), summarise:

> **Planning session complete.**
> - Issues planned: [count]
> - Total issues now: [count]
> - Next: run `/mantle:shape-issue` to evaluate approaches for the next issue to implement.

#### Persona

Senior product engineer who thinks in vertical slices. Pragmatic, not theoretical. Pushes for small, testable slices. Challenges proposals that are too broad ("that sounds like two issues") or too narrow ("this doesn't deliver end-to-end value"). Respects the user's domain knowledge.

#### Tone

Collaborative, structured, and efficient. Present one issue at a time with clear formatting. Wait for explicit approval before moving on. Never rush the user through planning.

### vault-templates/issue.md (new file)

Obsidian note template for issues. Used when creating issues directly in the vault (e.g., via Obsidian's template feature).

```yaml
---
title:
status: planned
slice: []
story_count: 0
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

_1-2 sentences: what user-facing value does this deliver and why now?_

## What to build

_Describe what this issue delivers as a vertical slice._

## Acceptance criteria

- [ ] _First testable criterion_
- [ ] _Second testable criterion_

## Blocked by

_List blocking issues or "None"._

## User stories addressed

_Which user stories from the product design does this satisfy?_
```

#### Design decisions

- **Static command, not compiled.** The plan-issues command doesn't need vault state baked in — it reads context dynamically during the session. This matches the system design classification as a static command.
- **One-at-a-time pacing.** The product design explicitly requires issues proposed one at a time with user approval on each. This is enforced by the command prompt structure, not by code.
- **Design impact analysis is advisory.** The command identifies potential design impact but doesn't edit design docs. This respects the one-command-one-job principle and keeps the plan-issues command focused on issue planning.
- **Bug surfacing.** The command reads `.mantle/bugs/` and surfaces open bugs as issue candidates. This implements the product design requirement that `/mantle:plan-issues` surfaces open bugs.
- **Existing issue awareness.** The command reads existing issues to understand numbering, dependencies, and what's already planned. It won't propose duplicate work.
- **Slices defined once, reused everywhere.** The command proposes slices from the system design on first run and persists them to `state.md`. Subsequent runs (and future story planning) reuse the same vocabulary, ensuring consistent naming across all issues.

## Tests

No automated tests for this story. The static command prompt is a markdown file that guides Claude's behaviour — it's verified by manual usage and the acceptance criteria in the parent issue. The vault template is a static file with no logic.

Verification:
- The `plan-issues.md` file exists at `claude/commands/mantle/plan-issues.md`
- The vault template exists at `vault-templates/issue.md`
- The template frontmatter matches the `IssueNote` schema from story 1
- Running `mantle install` copies `plan-issues.md` to `~/.claude/commands/mantle/`
