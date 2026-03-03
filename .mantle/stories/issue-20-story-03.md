---
issue: 20
title: /mantle:bug command prompt, vault template, help update
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Create the static Claude Code command `bug.md` that guides a brief interactive bug capture, the Obsidian vault template, and update help to include the new command.

### claude/commands/mantle/bug.md (new file)

Static command prompt following the pattern of `idea.md`. The AI guides a short, structured bug capture — designed to be fast (30 seconds for a simple bug).

#### Structure

**Step 1 — Check prerequisites**

Run `mantle save-bug --help` to confirm the CLI is available, then check whether `.mantle/bugs/` exists by reading `.mantle/state.md`.

- If `.mantle/` does not exist, tell the user to run `mantle init` first.
- If `.mantle/bugs/` does not exist, tell the user to create it: `mkdir .mantle/bugs/`

**Step 2 — Gather the bug**

Have a brief conversation to capture five things:

1. **What happened?** — One-line summary of the bug. *(one sentence)*
2. **How to reproduce** — Steps or context. If the bug was just encountered in the current session, the AI can infer reproduction steps from the conversation context. *(bullet list or paragraph)*
3. **Expected vs actual** — What should have happened, and what actually happened. *(one sentence each)*
4. **Severity** — The AI suggests a severity based on the description:
   - **blocker** — Cannot proceed with current work, no workaround
   - **high** — Significant impact, workaround exists but is painful
   - **medium** — Noticeable but doesn't block progress
   - **low** — Minor annoyance, cosmetic, or edge case

   Present the suggestion and let the user confirm or adjust.
5. **Related context** — Which issue/story was being worked on (if any), and which files are involved. Both optional.

The capture should be conversational but efficient. Don't force the user through a rigid form — if the user provides most of the information upfront, extract it and confirm rather than asking redundant questions.

**Step 3 — Confirm and save**

Once all fields are gathered, show a summary:

```
Summary:      <summary>
Severity:     <severity>
Description:  <description>
Reproduction: <reproduction>
Expected:     <expected>
Actual:       <actual>
Related issue: <related_issue or "None">
Related files: <files or "None">
```

Ask the user to confirm. Then run:

```bash
mantle save-bug \
  --summary "<summary>" \
  --severity "<severity>" \
  --description "<description>" \
  --reproduction "<reproduction>" \
  --expected "<expected>" \
  --actual "<actual>" \
  --related-issue "<issue>" \
  --related-file "<file1>" --related-file "<file2>"
```

Omit `--related-issue` and `--related-file` if not provided.

**Step 4 — Next steps**

After a successful save, tell the user:

> Bug captured! It will be surfaced next time you run `/mantle:plan-issues`.

If the bug is a blocker, additionally suggest:

> Since this is a **blocker**, consider addressing it in your current work session or running `/mantle:plan-issues` to create an issue for it now.

#### Persona

Helpful and efficient. The goal is speed — capture the bug before context is lost, don't make it feel like filing a Jira ticket. If the user is clearly frustrated by the bug, acknowledge it briefly and move on.

#### Tone

Brief, structured, no-nonsense. Minimise back-and-forth. If the user provides enough information in one message, don't ask clarifying questions — just extract and confirm.

### vault-templates/bug.md (new file)

Obsidian note template for bugs. Used when creating bugs directly in the vault.

```yaml
---
date:
author:
summary:
severity:
status: open
related_issue:
related_files: []
fixed_by:
tags:
  - type/bug
  - severity/medium
  - status/open
---

## Description

_What happened?_

## Reproduction

_Steps or context to reproduce._

## Expected Behaviour

_What should happen._

## Actual Behaviour

_What actually happens._
```

### claude/commands/mantle/help.md (modify)

Add `/mantle:bug` to the Bug Capture section. Insert a new section between Design and Planning:

```markdown
## Bug Capture
- `/mantle:bug` — Quick structured bug capture during any session
```

### Session Logging

The command prompt includes a session logging reminder at the end, following the same pattern as `idea.md`:

```markdown
## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "bug"

Keep the log under ~200 words following the session log format.
```

### Design decisions

- **AI suggests severity.** The AI is well-positioned to assess severity from the description — it can distinguish between "app crashes" (blocker) and "button colour is wrong" (low). The user confirms, keeping humans in control.
- **Context-aware reproduction.** When the bug was just encountered, the AI can infer reproduction steps from the current session rather than asking the user to re-explain. This makes bug capture genuinely fast.
- **Minimal back-and-forth.** Unlike `/mantle:idea` which has four distinct conversational rounds, bug capture aims for 1-2 exchanges. If the user describes the bug well in one message, the AI extracts all fields and jumps straight to confirmation.
- **Blocker escalation.** Blockers get an extra nudge because they need immediate attention. Non-blockers just get the standard "it'll show up in planning" message.
- **Session logging included.** Even bug capture sessions should log what happened. The `--command bug` flag links the session to this workflow.

## Tests

No automated tests for this story. The command prompt and vault template are static markdown files verified by manual usage and the acceptance criteria in the parent issue.

Verification:
- `claude/commands/mantle/bug.md` exists and follows the guided capture flow
- `vault-templates/bug.md` exists and frontmatter matches `BugNote` schema from story 1
- `claude/commands/mantle/help.md` includes `/mantle:bug` in a Bug Capture section
- Running `mantle install` copies `bug.md` to `~/.claude/commands/mantle/`
