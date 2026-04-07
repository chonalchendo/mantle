---
description: Analyze an external repo through your project's design lens
argument-hint: <repo-url>
allowed-tools: Read, Bash, Agent, Glob, Grep
---

Analyze an external repository by cloning it and examining it through the lens
of your project's architecture, goals, and current backlog. Produce structured
findings and actionable recommendations.

## Iron Laws

These rules are absolute. There are no exceptions.

1. **NO analysis without project context.** Every finding must be evaluated
   against the project's design — not in isolation.
2. **NO skipping the cleanup step.** Always remove the temp clone after
   analysis, even if earlier steps failed.
3. **NO vague recommendations.** Every finding must land in Adopt, Adapt, or
   Skip — no "interesting but unclear" hedging.

### Red Flags — thoughts that mean STOP

| Thought | Reality |
|---------|---------|
| "This pattern is interesting in general" | Interesting to whom? Evaluate it against the project's specific goals. |
| "I'll clean up the clone later" | The clone is temp disk. Clean it up now, before you report. |
| "I can skip the backlog scan" | Backlog implications are a required output section. Read the issues. |

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Parse input and clone repo"
2. "Step 2 — Compile project context"
3. "Step 3 — Run parallel analysis agents"
4. "Step 4 — Synthesise findings"
5. "Step 5 — Save and cleanup"
6. "Step 6 — Report results"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Parse input and clone repo

Extract the repo URL from `$ARGUMENTS`. If no URL was provided, ask the user:

> What is the URL of the repository you want to analyze?

Once you have the URL, clone it into a temp directory with a shallow clone (no
history needed for analysis):

```bash
git clone --depth 1 <url> $(mktemp -d)
```

Capture the path printed to stdout — that is your `<tmpdir>`. Derive
`<repo-name>` from the last segment of the URL (strip `.git` if present).

Confirm the clone succeeded before proceeding. If it fails, report the error
and stop.

## Step 2 — Compile project context

Read the following files to build a project context summary. This context is
the lens through which the external repo will be analyzed — include only what
shapes evaluation.

- `.mantle/product-design.md` — vision, target user, features, differentiators
- `.mantle/system-design.md` — architecture, modules, patterns, conventions
- `.mantle/issues/` — current backlog: read all issue files, extract titles and
  statuses only
- `.mantle/learnings/` — past implementation learnings: read all learning files
- `.claude/skills/*/SKILL.md` — compiled skill summaries: read all that exist

Synthesise into a compact context block (under 500 words) covering:

- **Product vision**: What this project is trying to do and for whom
- **Architecture principles**: How the code is structured and why
- **Current focus**: Active issues and their themes
- **Known patterns**: Conventions and learnings already established
- **Gaps and open questions**: Areas the project hasn't fully resolved yet

This context block will be injected into each analysis agent's prompt.

## Step 3 — Run parallel analysis agents

Spawn 5 Agent subagents simultaneously, each exploring the cloned repo through
a different dimension. Use `subagent_type: "Explore"` for all agents. Launch
all five in the same message (concurrent tool calls).

Each agent must receive:
- The path to the cloned repo (`<tmpdir>`)
- The full compiled project context from Step 2
- Its specific analysis dimension and guiding question (below)
- The output format required (see below)

**Agent 1 — Architecture**

> Analyze the repository at `<tmpdir>` through an architectural lens.
>
> Project context: `<compiled context>`
>
> Examine: module structure, dependency direction, layering patterns,
> separation of concerns, how the codebase is decomposed into packages and
> modules.
>
> Guiding question: What architectural patterns does this repo use that are
> relevant to our system design? What does it do better or differently than us?
>
> For each finding, produce a structured entry:
> - **Pattern name**: short label
> - **What they do**: one sentence describing the pattern
> - **Why it's relevant**: how it connects to our architecture
> - **Recommendation**: Adopt / Adapt / Skip — with a one-sentence rationale

**Agent 2 — Coding patterns**

> Analyze the repository at `<tmpdir>` through a coding patterns lens.
>
> Project context: `<compiled context>`
>
> Examine: naming conventions, error handling strategies, configuration
> management, abstraction styles, how complexity is managed day-to-day.
>
> Guiding question: What coding patterns could we adopt or learn from? What
> patterns do they use that would improve our codebase?
>
> For each finding, produce a structured entry:
> - **Pattern name**: short label
> - **What they do**: one sentence describing the pattern
> - **Why it's relevant**: how it connects to our conventions or gaps
> - **Recommendation**: Adopt / Adapt / Skip — with a one-sentence rationale

**Agent 3 — Testing**

> Analyze the repository at `<tmpdir>` through a testing lens.
>
> Project context: `<compiled context>`
>
> Examine: test framework choice, fixture patterns, test organisation,
> coverage strategy, use of mocks vs integration tests, test naming
> conventions, how edge cases are handled.
>
> Guiding question: What testing strategies does this repo use that we should
> consider adopting or adapting?
>
> For each finding, produce a structured entry:
> - **Pattern name**: short label
> - **What they do**: one sentence describing the pattern
> - **Why it's relevant**: how it connects to our test conventions or gaps
> - **Recommendation**: Adopt / Adapt / Skip — with a one-sentence rationale

**Agent 4 — CLI design** (only if the repo has a CLI — check for argument
parsing, command entry points, or a `cli/` module before analyzing)

> Analyze the repository at `<tmpdir>` through a CLI design lens.
>
> Project context: `<compiled context>`
>
> Examine: command structure, argument/flag patterns, help text UX, error
> message quality, subcommand organisation, output formatting.
>
> Guiding question: What CLI patterns are better than ours? What would improve
> the user experience of our own CLI?
>
> If the repo has no CLI, respond: "No CLI found — skipping this dimension."
>
> For each finding, produce a structured entry:
> - **Pattern name**: short label
> - **What they do**: one sentence describing the pattern
> - **Why it's relevant**: how it connects to our CLI design
> - **Recommendation**: Adopt / Adapt / Skip — with a one-sentence rationale

**Agent 5 — Domain-specific features**

> Analyze the repository at `<tmpdir>` through a domain lens.
>
> Project context: `<compiled context>`
>
> Examine: domain-specific features, product decisions, and approaches that
> relate directly to our product goals. Let the product vision in the project
> context guide what counts as "domain-relevant."
>
> Guiding question: What domain-specific features or approaches in this repo
> are relevant to our product goals? What have they solved that we haven't yet?
>
> For each finding, produce a structured entry:
> - **Pattern name**: short label
> - **What they do**: one sentence describing the feature or approach
> - **Why it's relevant**: how it connects to our product vision or backlog
> - **Recommendation**: Adopt / Adapt / Skip — with a one-sentence rationale

## Step 4 — Synthesise findings

Once all agents have returned, combine their results into a structured report
using the template below. Drop any dimension where the agent found nothing
relevant or reported the dimension was not applicable.

```markdown
# Scout Report: <repo-name>

**Repository**: <url>
**Analyzed**: <date>
**Project context**: <one-line summary of our product vision>

---

## Executive Summary

[2-4 sentences: what kind of project is this, what is the overall signal
quality (high/medium/low relevance to us), and the single most important
takeaway.]

---

## Findings by Dimension

### Architecture

[Agent 1 findings, formatted as structured entries]

### Coding Patterns

[Agent 2 findings, formatted as structured entries]

### Testing

[Agent 3 findings, formatted as structured entries]

### CLI Design

[Agent 4 findings, or "Not applicable — no CLI found."]

### Domain-Specific Features

[Agent 5 findings, formatted as structured entries]

---

## Actionable Recommendations

### Adopt
> High confidence — bring this in directly with minimal adaptation.

- **<pattern name>** (from <dimension>): <one sentence on what and why>

### Adapt
> Worth doing but needs adjustment for our context.

- **<pattern name>** (from <dimension>): <one sentence on what to change>

### Skip
> Not relevant or not worth the cost for us right now.

- **<pattern name>** (from <dimension>): <one sentence on why we're passing>

---

## Backlog Implications

[2-4 bullet points: findings that suggest new issues, reinforce existing
issues, or challenge current assumptions in the backlog. Reference specific
issue titles by name where relevant.]
```

## Step 5 — Save and cleanup

Save the report by running:

```bash
mantle save-scout \
  --repo-url "<url>" \
  --repo-name "<repo-name>" \
  --dimensions "architecture" \
  --dimensions "patterns" \
  --dimensions "testing" \
  --dimensions "cli-design" \
  --dimensions "domain" \
  --content "<full report>"
```

Then clean up the temp clone:

```bash
rm -rf <tmpdir>
```

Run the cleanup even if the save command fails. Temp disk must be freed.

## Step 6 — Report results

Display the Executive Summary and Actionable Recommendations sections to the
user. Do not re-display the full report — it is saved and accessible via
`mantle save-scout`.

Then briefly assess before recommending next steps:

- Were there high-value Adopt items that could be acted on immediately?
- Did any findings suggest gaps in the current backlog?
- Was the overall signal quality high enough to inform a design revision?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:brainstorm` — recommend when the scout surfaced a strong idea worth
  exploring further before committing to an issue
- `/mantle:add-issue` — recommend when the scout found a concrete, well-defined
  gap that maps directly to work we should do
- `/mantle:revise-system` — recommend when architectural findings suggest our
  system design should be updated
- `/mantle:revise-product` — recommend when domain findings challenge or enrich
  our product vision

**Default:** `/mantle:brainstorm` if findings surfaced new ideas worth exploring.

Present one clear recommendation with a reason, then mention alternatives
briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you
> observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "scout"

Keep the log under ~200 words following the session log format (Summary, What
Was Done, Decisions Made, What's Next, Open Questions).
