Decompose the project's product and system design into thin vertical slice issues,
proposed one at a time with user approval on each. Think in vertical slices. Push
for small, testable slices. Challenge proposals that are too broad ("that sounds
like two issues") or too narrow ("this doesn't deliver end-to-end value"). Respect
the user's domain knowledge.

Be collaborative, structured, and efficient. Present one issue at a time with
clear formatting. Wait for explicit approval before moving on. Never rush the user
through planning.

## Step 1 — Check prerequisites

Read `.mantle/state.md` and verify:

- `.mantle/` exists. If not, tell the user to run `mantle init` first.
- Status is one of: `system-design`, `adopted`, or `planning`. These are the
  valid states from which issue planning can proceed.
- If status is earlier (e.g., `idea`, `product-design`), tell the user the current
  status and suggest the appropriate next command (e.g., `/mantle:design-product`,
  `/mantle:design-system`).

## Step 2 — Load context and define slices

Read and internalise:

- `.mantle/product-design.md` — the product definition (features, user stories,
  milestones)
- `.mantle/system-design.md` — the system architecture (modules, API contracts,
  data model)
- `.mantle/issues/` — any existing issues (to understand what's already planned,
  dependencies, and numbering)
- `.mantle/bugs/` — any open bugs (surface these as candidates for new issues)
- `.mantle/learnings/` — past retrospective learnings (surface recommendations
  as candidates for new issues)

Check `state.md` for the `slices` field. If slices are already defined, display
them:

> **Project slices:** ingestion, transformation, api, storage, tests

If slices are empty (first planning session), propose slices derived from the
system design's architecture section. Ask the user to confirm or adjust:

> Based on your system design, I'd propose these architectural slices for vertical
> planning:
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
> **Learnings with recommendations:** [count] learnings found. [list any that
> suggest new work]

## Step 3 — Propose issues one at a time

When proposing issues, draw from all sources: product/system design features,
open bugs, and retrospective recommendations. If a learning recommendation
maps to a new issue, cite it:

> **Source:** Recommendation from issue {NN} retrospective: "{recommendation}"

For each issue, propose:

1. **Title** — concise, action-oriented (e.g., "Context compilation engine +
   /mantle:status")
2. **Why** — 1-2 sentences explaining the user-facing value and linking to the
   product/system design motivation
3. **Vertical slice** — which of the project's defined slices this issue cuts
   through. Use the slice names from `state.md` (defined in Step 2).
4. **What to build** — 2-3 paragraph description of the deliverable
5. **Acceptance criteria** — testable checkboxes defining "done". Each criterion
   should be independently verifiable.
6. **Blocked by** — which existing issues must complete first (by number)
7. **User stories addressed** — which user stories from the product design this
   issue satisfies

Rules for vertical slices:

- Each issue must deliver something the user can run or test end-to-end. Litmus
  test: "can a user verify this works?" If not, the slice isn't vertical enough.
- Slices should trace from user-facing entry point through to the underlying
  implementation — nothing developed in isolation.
- Avoid "pure refactoring" or "pure testing" issues — tests belong with the
  feature they verify.
- Smaller is better. If an issue feels large, suggest splitting it.
- Use the project's defined slices (from `state.md`) as the vocabulary. Every
  `--slice` value on saved issues should match a defined slice.

Present the proposed issue and **wait for user approval or adjustment**. Do not
propose the next issue until the current one is approved.

After presenting each issue, use AskUserQuestion to let the user choose:
- **Approve** — save the issue and proceed
- **Adjust** — modify the proposal (ask what to change)
- **Skip** — move to the next issue without saving
- **Stop** — end the planning session

## Step 4 — Save each approved issue

After user approval, save using the CLI:

```bash
mantle save-issue \
  --title "<issue title>" \
  --slice "<layer1>" --slice "<layer2>" \
  --content "<full issue body>" \
  --blocked-by <issue_number> \
  --verification "<optional per-issue verification override>"
```

The `--content` body should follow this structure:

```markdown
## Parent PRD

product-design.md, system-design.md

## Why

[1-2 sentences: what user-facing value does this deliver and why now?]

## What to build

[Description of what this issue delivers...]

## Acceptance criteria

- [ ] First testable criterion
- [ ] Second testable criterion

## Blocked by

- Blocked by issue-NN (needs [reason])

## User stories addressed

- User story NN: [description]
```

## Step 5 — Design impact analysis

After each issue is saved, analyze whether the issue implies changes to
`product-design.md` or `system-design.md`. Check for:

- New API surface not documented in system design
- New commands or features not in the product design user stories
- Architectural changes that affect the module structure
- New data models or schema changes

If design impact is detected, prompt the user:

> "This issue touches [specific area]. Consider running `/mantle:revise-system`
> to update the [section name] section."

or:

> "This issue adds [feature]. Consider running `/mantle:revise-product` to add
> user stories for [area]."

The command does NOT edit design docs itself — it identifies the impact and defers
to the revise commands (one-command-one-job principle).

## Step 6 — Session wrap-up

When the user stops planning (or all planned work is proposed), summarise:

> **Planning session complete.**
> - Issues planned: [count this session]
> - Total issues now: [total count]

Then briefly assess before recommending next steps:

- Did any issues imply changes to the product or system design (from Step 5)?
- Are the issues well-defined enough for shaping?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:build` — recommend when the user wants to move fast. Automates shaping, story planning, implementation, and verification in one pass.
- `/mantle:shape-issue` — recommend when the user wants fine-grained control over approach selection before building.
- `/mantle:revise-system` — recommend when issue planning revealed system design gaps that should be addressed before building.
- `/mantle:revise-product` — recommend when issue planning revealed product design gaps.

**Default:** `/mantle:shape-issue` if nothing suggests otherwise.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]
