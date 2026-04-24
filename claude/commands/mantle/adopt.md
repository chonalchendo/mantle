---
allowed-tools: Read, Bash(mantle *), Agent
---

Onboard an existing codebase into Mantle by reverse-engineering structured design
artifacts from the code that already exists. Decompose the system into its
irreducible building blocks before reaching for labels or patterns.

Be respectful of existing choices, curious about intent, and honest about
confidence levels. The goal is to understand and codify, not to redesign. Start
from what must be true, not what's conventional.

## Design Principles

- **First principles, not pattern matching.** Decompose the codebase into
  irreducible building blocks before reaching for architectural labels. Start from
  what must be true, then work upward.
- **Constraints before conventions.** Distinguish hard constraints (the code breaks
  without this) from inherited conventions (this is how it happens to be done).
  Name each explicitly.
- **Extract, don't prescribe.** Codify what exists. The Considerations section is
  clearly separated from factual analysis.
- **Interactive, not dump-and-run.** Present findings incrementally. Let the user
  correct and refine.
- **Honest about confidence.** Mark inferred sections with confidence levels. "I'm
  90% sure this is a REST API" vs "I'm guessing this module handles auth based on
  the name."
- **Respect existing choices.** The user chose their stack for reasons.
  Considerations are framed as options, not criticism.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Concurrent agent analysis"
3. "Step 3 — Interactive synthesis"
4. "Step 4 — Log decisions"
5. "Step 5 — Save adoption"
6. "Step 6 — Next steps"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Record the stage:

    mantle stage-begin adopt

First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.

Check whether `$MANTLE_DIR/` and `$MANTLE_DIR/state.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first.
- If state is not `idea`, tell the user the current status and explain that
  adoption is for freshly-initialized projects.
- If `$MANTLE_DIR/product-design.md` or `$MANTLE_DIR/system-design.md` already
  exists, warn the user that adoption will overwrite them. Ask for confirmation
  before proceeding. If they decline, stop.

## Step 2 — Phase 1: Concurrent agent analysis

Launch two subagents concurrently using the Agent tool:

**Agent 1: Codebase analyst** (subagent_type: "codebase-analyst")

Prompt includes:
- The project directory path for exploration
- Instruction to follow its built-in methodology

**Agent 2: Domain researcher** (subagent_type: "domain-researcher")

Prompt includes:
- Context about what the project appears to be (from directory name, README, or
  initial observation)
- Instruction to follow its built-in methodology

Both agents run in parallel. Wait for both to complete before proceeding.

## Step 3 — Phase 2: Interactive synthesis

Present findings to the user and work through four sections one at a time. Do NOT
dump everything at once — present each section, get user feedback, then move on.

### Section A: Architecture summary

Present the codebase analyst's findings as a first-principles decomposition:

> "I've decomposed your project into its fundamental building blocks — the
> irreducible pieces it depends on. Here's what I found. Please correct anything
> that's wrong or fill in intent that isn't visible in the code."

Start with the building blocks (what are the smallest correct pieces?), then show
how they compose into the architecture. Cover: fundamental constraints, building
blocks, composition, tech stack, dependency graph, test patterns, deployment
approach. For each observation, distinguish hard constraints (the code breaks
without this) from soft conventions (this is how it happens to be done). Mark each
with confidence (high/medium/low).

Let the user correct misconceptions and add context about intent.

### Section B: Product design draft

Synthesise a product design from both agents' findings, working from first
principles:

- **Vision**: Infer from README, docs, and domain research. One sentence connecting
  the fundamental problem to the insight that makes this project's approach
  possible.
- **Principles**: Extract the non-negotiable truths from the codebase — structural
  realities that constrain the solution space, not aspirational goals. What must be
  true for this code to work?
- **Building blocks**: The irreducible primitives the project depends on. Identify
  from module boundaries and key abstractions. These are the atoms — if these are
  right, everything else follows.
- **Prior art**: Note dependencies and ecosystem tools being used. What didn't need
  to be built from scratch?
- **Composition**: Describe how the building blocks assemble into the product.
  Features are an output of composition, not an input.
- **Target users**: Infer from docs, API design, and domain context.
- **Success metrics**: Propose based on what the project measures (tests, CI checks,
  etc.).

Present each field with confidence level. Ask the user to refine.

### Section C: System design draft

Compile a system design document from the codebase analysis, structured around
building blocks rather than generic architecture headings:

- True constraints — what must be true for this system to function
- Building blocks — the irreducible capabilities, with correctness invariants
- How blocks compose — boundaries, data flow, error propagation
- Key technical decisions (with inferred rationale and alternatives)
- API contracts (if applicable)
- Deployment and configuration

Challenge inherited conventions. "That's how it's usually done" is not a rationale
— ask what problem the pattern solves and whether this system has that problem.
Present for user refinement.

### Section D: Considerations

Present optional observations clearly marked as non-prescriptive:

> "These are things I noticed that you might want to consider. They're
> observations, not recommendations — you know your project better than I do."

Categories: architectural patterns that could simplify things, dependencies that
could be consolidated, testing gaps, documentation gaps. Each framed as "you might
consider" not "you should."

The user decides which (if any) to act on. Do NOT automatically turn these into
decisions or actions.

## Step 4 — Log decisions

For each key architectural decision visible in the codebase that was confirmed
during the interactive session, save a decision log entry:

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

Mark the scope as `"adoption"` to distinguish inferred decisions from actively-made
ones. Include confidence levels that reflect whether the rationale was
user-confirmed (higher) or purely inferred (lower).

## Step 5 — Save adoption

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

## Step 6 — Next steps

After a successful save, briefly assess the quality of the generated design artifacts:

- How confident are you in the reverse-engineered product design?
- Does the system design accurately capture the existing architecture?
- Were there areas where you had low confidence or made assumptions?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:plan-issues` — default. Recommend when the design docs are solid and the user is ready to start planning work.
- `/mantle:revise-product` — recommend when the reverse-engineered product design needs refinement (e.g., vision or principles felt uncertain).
- `/mantle:revise-system` — recommend when the system design needs updating (e.g., architecture areas with low confidence).

**Default:** `/mantle:plan-issues` if the designs are solid.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on the adoption session]
>
> Other options: [brief list of alternatives with one-line descriptions]

## Output Format

One line per generated artifact:

- **Product design**: saved — confidence: <high / medium / low>
- **System design**: saved — confidence: <high / medium / low>
- **Decisions logged**: <count>

Anti-patterns:
- No "I noticed" / "I'll do X next" framing
- No restating the full system design document
- No trailing summary paragraph after the save confirmation
- No emoji

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "adopt"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).
