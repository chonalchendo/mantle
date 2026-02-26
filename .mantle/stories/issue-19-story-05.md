---
issue: 19
title: Claude adopt command (/mantle:adopt) and help update
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Create the `/mantle:adopt` Claude Code command that orchestrates the full adoption workflow as an interactive session, and update `/mantle:help` to include it.

### claude/commands/mantle/adopt.md

The adopt command guides the user through three phases: concurrent agent analysis, interactive synthesis, and artifact generation. Follows the same interactive-session pattern as `/mantle:design-product` and `/mantle:design-system`.

#### Persona

Adopt the persona of a senior architect who thinks from first principles — decomposing systems into their irreducible building blocks before reaching for labels or patterns. Tone: respectful of existing choices, curious about intent, honest about confidence levels. You're here to understand and codify, not to redesign. Start from what must be true, not what's conventional.

#### Step 1 — Check prerequisites

Check whether `.mantle/` and `.mantle/state.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first.
- If state is not `idea`, tell the user the current status and explain that adoption is for freshly-initialized projects.
- If `.mantle/product-design.md` or `.mantle/system-design.md` already exists, warn the user that adoption will overwrite them. Ask for confirmation before proceeding. If they decline, stop.

#### Step 2 — Phase 1: Concurrent agent analysis

Launch two subagents concurrently using the Task tool:

**Agent 1: Codebase analyst** (subagent_type: "general-purpose")

Prompt includes:
- Instructions to read `claude/agents/codebase-analyst.md` and follow its methodology
- The project directory path for exploration

**Agent 2: Domain researcher** (subagent_type: "general-purpose")

Prompt includes:
- Instructions to read `claude/agents/domain-researcher.md` and follow its methodology
- Context about what the project appears to be (from directory name, README, or initial observation)

Both agents run in parallel. Wait for both to complete before proceeding.

#### Step 3 — Phase 2: Interactive synthesis

Present findings to the user and work through four sections one at a time. Do NOT dump everything at once — present each section, get user feedback, then move on.

**Section A: Architecture summary**

Present the codebase analyst's findings as a first-principles decomposition:

> "I've decomposed your project into its fundamental building blocks — the irreducible pieces it depends on. Here's what I found. Please correct anything that's wrong or fill in intent that isn't visible in the code."

Start with the building blocks (what are the smallest correct pieces?), then show how they compose into the architecture. Cover: fundamental constraints, building blocks, composition, tech stack, dependency graph, test patterns, deployment approach. For each observation, distinguish hard constraints (the code breaks without this) from soft conventions (this is how it happens to be done). Mark each with confidence (high/medium/low).

Let the user correct misconceptions and add context about intent.

**Section B: Product design draft**

Synthesise a product design from both agents' findings, working from first principles:

- **Vision**: Infer from README, docs, and domain research. One sentence connecting the fundamental problem to the insight that makes this project's approach possible.
- **Principles**: Extract the non-negotiable truths from the codebase — structural realities that constrain the solution space, not aspirational goals. What must be true for this code to work?
- **Building blocks**: The irreducible primitives the project depends on. Identify from module boundaries and key abstractions. These are the atoms — if these are right, everything else follows.
- **Prior art**: Note dependencies and ecosystem tools being used. What didn't need to be built from scratch?
- **Composition**: Describe how the building blocks assemble into the product. Features are an output of composition, not an input.
- **Target users**: Infer from docs, API design, and domain context.
- **Success metrics**: Propose based on what the project measures (tests, CI checks, etc.).

Present each field with confidence level. Ask the user to refine.

**Section C: System design draft**

Compile a system design document from the codebase analysis, structured around building blocks rather than generic architecture headings:

- True constraints — what must be true for this system to function
- Building blocks — the irreducible capabilities, with correctness invariants
- How blocks compose — boundaries, data flow, error propagation
- Key technical decisions (with inferred rationale and alternatives)
- API contracts (if applicable)
- Deployment and configuration

Challenge inherited conventions. "That's how it's usually done" is not a rationale — ask what problem the pattern solves and whether this system has that problem. Present for user refinement.

**Section D: Considerations**

Present optional observations clearly marked as non-prescriptive:

> "These are things I noticed that you might want to consider. They're observations, not recommendations — you know your project better than I do."

Categories: architectural patterns that could simplify things, dependencies that could be consolidated, testing gaps, documentation gaps. Each framed as "you might consider" not "you should."

The user decides which (if any) to act on. Do NOT automatically turn these into decisions or actions.

#### Step 4 — Log decisions

For each key architectural decision visible in the codebase that was confirmed during the interactive session, save a decision log entry:

```bash
mantle save-decision \
  --topic "<slugified-topic>" \
  --decision "<what was decided>" \
  --alternatives "<alt 1>" --alternatives "<alt 2>" \
  --rationale "<inferred rationale — confirmed by user>" \
  --reversal-trigger "<what would change this>" \
  --confidence "<N/10>" \
  --reversible "<high|medium|low>" \
  --scope "adoption"
```

Mark the scope as `"adoption"` to distinguish inferred decisions from actively-made ones. Include confidence levels that reflect whether the rationale was user-confirmed (higher) or purely inferred (lower).

#### Step 5 — Save adoption

After the user confirms the product design and system design, save via CLI:

```bash
mantle save-adoption \
  --vision "<vision>" \
  --principles "<p1>" --principles "<p2>" \
  --building-blocks "<b1>" --building-blocks "<b2>" \
  --prior-art "<a1>" --prior-art "<a2>" \
  --composition "<composition>" \
  --target-users "<target_users>" \
  --success-metrics "<m1>" --success-metrics "<m2>" \
  --system-design-content "<full system design markdown>"
```

Add `--overwrite` if the user confirmed overwriting in Step 1.

#### Step 6 — Next steps

After a successful save, tell the user:

> Adoption complete! Your project now has structured design artifacts in `.mantle/`.
>
> Next steps:
> - Run `/mantle:plan-issues` to break down the work into implementable issues
> - Run `/mantle:revise-product` or `/mantle:revise-system` to refine the designs
> - Decision log entries are in `.mantle/decisions/` — review them with `/mantle:status`

#### Design principles

Embed these as guidance in the command prompt:

- **First principles, not pattern matching.** Decompose the codebase into irreducible building blocks before reaching for architectural labels. Start from what must be true, then work upward.
- **Constraints before conventions.** Distinguish hard constraints (the code breaks without this) from inherited conventions (this is how it happens to be done). Name each explicitly.
- **Extract, don't prescribe.** Codify what exists. The Considerations section is clearly separated from factual analysis.
- **Interactive, not dump-and-run.** Present findings incrementally. Let the user correct and refine.
- **Honest about confidence.** Mark inferred sections with confidence levels. "I'm 90% sure this is a REST API" vs "I'm guessing this module handles auth based on the name."
- **Respect existing choices.** The user chose their stack for reasons. Considerations are framed as options, not criticism.

### claude/commands/mantle/help.md (modify)

Add `/mantle:adopt` to the "Idea & Validation" section (or create a new "Setup & Onboarding" section):

```markdown
## Setup & Onboarding
- `/mantle:adopt` — Onboard an existing project into Mantle (reverse-engineer design docs)
```

Place this section before "Idea & Validation" since adoption is an alternative starting point.

## Tests

No automated tests — these are static prompt files. Verified by:

- `claude/commands/mantle/adopt.md` exists and is syntactically valid markdown
- `/mantle:help` mentions `/mantle:adopt`
- After `mantle install`, the command is available in Claude Code
