---
description: Analyze an external repo through your project's design lens
argument-hint: <repo-url>
allowed-tools: Read, Bash, Agent, Glob, Grep
---

Analyze an external repository by cloning it and examining it through the lens
of your project's architecture, goals, and current backlog. Produce structured
findings and actionable recommendations.

## Iron Laws

These rules are absolute. No exceptions.

1. **NO analysis without project context.** Evaluate every finding against the
   project's design — not in isolation.
2. **NO executing code from the cloned repo.** It is untrusted. Only use Read,
   Glob, and Grep. Never run scripts, tests, build commands, or install
   dependencies.
3. **NO skipping the cleanup step.** Always remove the temp clone, even if
   earlier steps failed.
4. **NO vague recommendations.** Every finding must be Adopt, Adapt, or Skip.

### Red Flags — thoughts that mean STOP

| Thought | Reality |
|---------|---------|
| "This pattern is interesting in general" | Evaluate it against the project's specific goals. |
| "Let me run the tests to see if they pass" | Never execute from an untrusted repo. Read test files instead. |
| "I'll install the dependencies to understand the project" | Read requirements/pyproject.toml — never install. |
| "I'll clean up the clone later" | Clean up before you report. |
| "I can skip the backlog scan" | Backlog implications are required. Read the issues. |

Use TaskCreate for each step, TaskUpdate to set `in_progress` / `completed`.

## Step 1 — Parse input and clone repo

Extract the repo URL from `$ARGUMENTS`. If absent, ask:

> What is the URL of the repository you want to analyze?

Clone with a shallow clone:

```bash
git clone --depth 1 <url> $(mktemp -d)
```

Capture `<tmpdir>` from stdout. Derive `<repo-name>` from the last URL segment
(strip `.git`). If clone fails, report the error and stop.

## Step 2 — Compile project context

Record the stage:

    mantle stage-begin scout

    MANTLE_DIR=$(mantle where)

Use `$MANTLE_DIR/...` for all subsequent reads.

Read:
- `$MANTLE_DIR/product-design.md`
- `$MANTLE_DIR/system-design.md`
- `$MANTLE_DIR/issues/` — titles and statuses only
- `$MANTLE_DIR/learnings/`
- `.claude/skills/*/SKILL.md`

Synthesise a context block under 500 words covering: product vision,
architecture principles, current focus, known patterns, and open gaps.
Inject this into each analysis agent's prompt.

## Step 3 — Run parallel analysis agents

Spawn 5 agents simultaneously (`subagent_type: "Explore"`). Launch all five
in the same message. Each agent receives `<tmpdir>`, the compiled project
context, its dimension/guiding question below, the output format, and:

**Read-only constraint:** "Only use Read, Glob, and Grep. Never run, execute,
install, or build anything from the cloned repo."

**Agent 1 — Architecture**

> Analyze `<tmpdir>` through an architectural lens.
> Project context: `<compiled context>`
> Examine: module structure, dependency direction, layering, separation of concerns.
> Guiding question: What architectural patterns are relevant to our system design?
> For each finding: **Pattern name** / **What they do** / **Why it's relevant** / **Adopt/Adapt/Skip**

**Agent 2 — Coding patterns**

> Analyze `<tmpdir>` through a coding patterns lens.
> Project context: `<compiled context>`
> Examine: naming conventions, error handling, configuration, abstraction styles.
> Guiding question: What coding patterns could we adopt?
> For each finding: **Pattern name** / **What they do** / **Why it's relevant** / **Adopt/Adapt/Skip**

**Agent 3 — Testing**

> Analyze `<tmpdir>` through a testing lens.
> Project context: `<compiled context>`
> Examine: test framework, fixture patterns, organisation, mocks vs integration, edge cases.
> Guiding question: What testing strategies should we consider?
> For each finding: **Pattern name** / **What they do** / **Why it's relevant** / **Adopt/Adapt/Skip**

**Agent 4 — CLI design** (only if a CLI exists — check before analyzing)

> Analyze `<tmpdir>` through a CLI design lens.
> Project context: `<compiled context>`
> Examine: command structure, argument patterns, help text UX, error messages, output formatting.
> Guiding question: What CLI patterns would improve our own CLI?
> If no CLI found: "No CLI found — skipping this dimension."
> For each finding: **Pattern name** / **What they do** / **Why it's relevant** / **Adopt/Adapt/Skip**

**Agent 5 — Domain-specific features**

> Analyze `<tmpdir>` through a domain lens.
> Project context: `<compiled context>`
> Examine: domain-specific features and product decisions related to our goals.
> Guiding question: What domain approaches have they solved that we haven't?
> For each finding: **Pattern name** / **What they do** / **Why it's relevant** / **Adopt/Adapt/Skip**

## Step 4 — Synthesise findings

Combine agent results into a structured report. Drop dimensions with no relevant findings.

```markdown
# Scout Report: <repo-name>

**Repository**: <url>
**Analyzed**: <date>
**Project context**: <one-line product vision summary>

---

## Executive Summary

[2-4 sentences: project type, overall signal quality, single most important takeaway.]

---

## Findings by Dimension

### Architecture
[Agent 1 findings]

### Coding Patterns
[Agent 2 findings]

### Testing
[Agent 3 findings]

### CLI Design
[Agent 4 findings, or "Not applicable — no CLI found."]

### Domain-Specific Features
[Agent 5 findings]

---

## Actionable Recommendations

### Adopt
> High confidence — bring in directly.
- **<pattern>** (from <dimension>): <what and why>

### Adapt
> Worth doing with adjustment.
- **<pattern>** (from <dimension>): <what to change>

### Skip
> Not relevant or not worth the cost.
- **<pattern>** (from <dimension>): <why passing>

---

## Backlog Implications

[2-4 bullets: new issues, reinforced issues, or challenged assumptions. Reference issue titles.]
```

## Step 5 — Save and cleanup

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

Then:

```bash
rm -rf <tmpdir>
```

Run cleanup even if save fails.

## Step 6 — Report results

Display the Executive Summary and Actionable Recommendations only. Do not
re-display the full report.

## Output Format

One line per recommendation:

- **Pattern**: <name> (<dimension>) — <one-line rationale>
- **Verdict**: Adopt / Adapt / Skip — <one sentence on why>

Anti-patterns:
- No "I noticed" / "I'll do X next" framing
- No restating the full findings list
- No trailing summary paragraph
- No emoji
- No "interesting" findings without an Adopt/Adapt/Skip verdict

**Valid next commands:**

- `/mantle:brainstorm` — strong idea worth exploring before committing to an issue
- `/mantle:add-issue` — concrete gap that maps directly to work we should do
- `/mantle:revise-system` — architectural findings suggest system design needs updating
- `/mantle:revise-product` — domain findings challenge or enrich product vision

**Default:** `/mantle:brainstorm` if findings surfaced new ideas.

> **Recommended next step:** `/mantle:<command>` — [reason]
>
> Other options: [brief list]

## Session Logging

    mantle save-session --content "<body>" --command "scout"

Under ~200 words: Summary, What Was Done, Decisions Made, What's Next, Open Questions.
