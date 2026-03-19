---
issue: 23
title: Retrospective command prompt with learnings integration
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Create the static Claude Code command `retrospective.md` that guides the interactive retrospective session. The AI adopts a reflective persona and works through structured reflection areas before saving via the CLI.

### `claude/commands/mantle/retrospective.md` (new file)

Static command prompt following the pattern of `shape-issue.md` and `design-product.md`. The AI adopts the persona of a thoughtful engineering lead who values honest reflection.

#### Structure

**Step 1 — Check prerequisites**

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell user to run `mantle init`)
- Status is `verifying`, `reviewing`, or `completed` (if not, tell them the current status and that retrospectives run after implementation)

**Step 2 — Load context**

Read and internalise:
- `.mantle/shaped/` — the shaped issue for the current issue (if exists), as baseline for planned-vs-actual comparison
- `.mantle/learnings/` — past learnings for pattern recognition
- `.mantle/state.md` — to identify the current issue number

If past learnings exist, briefly note recurring themes before starting. Ask the user which issue number to retrospect on, or confirm the current issue from state.md.

**Step 3 — Guided reflection**

Work through four areas interactively with probing questions:

1. **What went well** — what worked as expected or better, patterns worth repeating, where the shaped plan held up
2. **Harder than expected** — what took longer, where estimates missed, unanticipated rabbit holes
3. **Wrong assumptions** — technical or product assumptions that turned out false
4. **Recommendations** — what to do differently, tools/patterns to adopt or avoid, what future shaping should account for

**Step 4 — Assess confidence delta**

Ask the user how their project confidence changed. Format: `+N` or `-N`. Help calibrate: major success might be +3, minor adjustment +1, significant setback -2.

**Step 5 — Save learning**

Compile the structured reflection and save via:

```bash
mantle save-learning \
  --issue <number> \
  --title "<issue title>" \
  --confidence-delta "<+N or -N>" \
  --content "<structured reflection with all sections>"
```

**Step 6 — Next steps**

After a successful save:

> Learning captured! These learnings will automatically surface in future `/mantle:shape-issue` sessions to inform planning.

#### Persona

Thoughtful engineering lead who values honest reflection. Doesn't sugarcoat. Asks probing questions. Draws out specific examples, not vague generalities. Focuses on what's useful for next time. Reflective, honest, and forward-looking.

### Design decisions

- **Static command, not compiled.** The retrospective command reads context dynamically during the session. No vault state needs to be baked in at compile time.
- **Interactive reflection, not questionnaire.** Each area is explored conversationally with follow-up questions, not presented as a form to fill in.
- **Shaped issue as baseline.** If a shaped issue exists for this issue number, it's used to compare planned approach vs actual outcome — surfacing where plans held up and where they didn't.
- **Past learnings for patterns.** Loading previous learnings helps identify recurring themes (e.g. "we always underestimate API integration") that the user might otherwise miss.
- **Four reflection areas match Learning Note schema.** The guided reflection maps directly to the four body sections in the learning note format defined in the system design.

## Tests

No automated tests for this story. The static command prompt is a markdown file that guides Claude's behaviour — it's verified by manual usage and the acceptance criteria in the parent issue.

Verification:
- The `retrospective.md` file exists at `claude/commands/mantle/retrospective.md`
- Running `mantle install` copies it to `~/.claude/commands/mantle/`
- The command references `mantle save-learning` which is registered in story 2
